#!/usr/bin/env python3
"""Scoring for the viparse benchmark. Implements METRIC.md exactly.

Pure stdlib on purpose: anyone must be able to re-run this against the published
corpus without installing anything, or the numbers are not checkable.

    python3 scripts/score.py --pred out/ --truth ground-truth/ --subset public-domain
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path

_ALL_WS = re.compile(r"\s+")
# Segment boundaries for chunking. Deliberately punctuation, not line breaks: where a
# tool puts its newlines is a layout choice and must not affect the score, but the
# comparison still has to run on pieces small enough to be quadratic in.
_SEGMENT = re.compile(r"(?<=[.;:!?])\s+")

# đ/Đ carry no combining mark, so NFD leaves them untouched; they are still the
# same base letter as d/D for alignment purposes.
_DSTROKE = str.maketrans({"đ": "d", "Đ": "D"})


def normalise(text: str) -> str:
    """NFC, all whitespace collapsed to single spaces. METRIC.md §Preprocessing."""
    return _ALL_WS.sub(" ", unicodedata.normalize("NFC", text)).strip()


def base_letters(text: str) -> str:
    """Strip diacritics, leaving the letter underneath."""
    decomposed = unicodedata.normalize("NFD", text.translate(_DSTROKE))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def is_diacritic_bearing(ch: str) -> bool:
    """True for a Vietnamese letter whose identity depends on a diacritic."""
    if ch in "\u0111\u0110":  # đ Đ — no combining mark, still diacritic-bearing
        return True
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", ch))


@dataclass
class Score:
    document: str
    char_accuracy: float
    diacritic_accuracy: float | None
    syllable_accuracy: float
    truth_chars: int
    diacritic_positions: int


def _aligned_line_pairs(pred: str, truth: str) -> list[tuple[str, str]]:
    """Pair up segments, then compare within a pair.

    A single global alignment is O(n²) and does not survive real documents: the largest
    file in the corpus is 145k characters, which is ~21 billion comparisons and does not
    finish. Aligning *segments* first is cheap, and the character alignment then runs on
    pieces small enough to be instant — 0.3s for that file instead of never.

    Segments are split on sentence punctuation rather than on newlines. Splitting on
    newlines was tried and is wrong: it made line-break placement affect the score, and
    two tools that agree on every letter but disagree on where paragraphs break would be
    scored as different.
    """
    truth_lines, pred_lines = _SEGMENT.split(truth), _SEGMENT.split(pred)
    matcher = SequenceMatcher(None, truth_lines, pred_lines, autojunk=False)

    pairs: list[tuple[str, str]] = []
    for tag, t1, t2, p1, p2 in matcher.get_opcodes():
        if tag == "equal":
            pairs += [(pred_lines[p1 + k], truth_lines[t1 + k]) for k in range(t2 - t1)]
        else:
            # A changed region: pair line-for-line as far as both sides go, and pair the
            # remainder against nothing so deletions and insertions still count.
            changed_t, changed_p = truth_lines[t1:t2], pred_lines[p1:p2]
            for k in range(max(len(changed_t), len(changed_p))):
                pairs.append((
                    changed_p[k] if k < len(changed_p) else "",
                    changed_t[k] if k < len(changed_t) else "",
                ))
    return pairs


def char_accuracy(pairs: list[tuple[str, str]], truth_len: int) -> float:
    if not truth_len:
        return 1.0 if not any(p for p, _ in pairs) else 0.0
    matched = 0
    for p_line, t_line in pairs:
        if p_line == t_line:  # the common case; no alignment needed
            matched += len(t_line)
        else:
            matched += sum(
                b.size
                for b in SequenceMatcher(None, t_line, p_line, autojunk=False).get_matching_blocks()
            )
    return matched / truth_len


def diacritic_accuracy(pairs: list[tuple[str, str]]) -> tuple[float | None, int]:
    """Fraction of the ground truth's diacritic-bearing characters recovered exactly.

    The denominator is **every** diacritic-bearing character in the ground truth, not
    only those that aligned. Restricting it to aligned positions would let a parser
    that dropped half the document score on the half it kept.

    Characters carrying no diacritic are excluded entirely: they match trivially, and
    including them buries the signal — in a typical Vietnamese sentence only ~17% of
    characters carry a diacritic, so a parser that strips every one of them would
    still score above 0.8.
    """
    total = correct = 0
    for pred_line, truth_line in pairs:
        if pred_line == truth_line:
            n = sum(1 for c in truth_line if is_diacritic_bearing(c))
            total += n
            correct += n
            continue
        matcher = SequenceMatcher(
            None, base_letters(truth_line), base_letters(pred_line), autojunk=False
        )
        aligned_at: dict[int, int] = {}
        for block in matcher.get_matching_blocks():
            for offset in range(block.size):
                aligned_at[block.a + offset] = block.b + offset

        for t_i, t_ch in enumerate(truth_line):
            if not is_diacritic_bearing(t_ch):
                continue
            total += 1
            p_i = aligned_at.get(t_i)
            if p_i is not None and p_i < len(pred_line) and pred_line[p_i] == t_ch:
                correct += 1

    return (correct / total if total else None), total


def syllable_accuracy(pairs: list[tuple[str, str]], truth_tokens: int) -> float:
    """Whitespace tokens matching exactly, compared within aligned lines.

    Per line for the same reason as the other two: a global token alignment on a
    170k-character document is ~25,000 tokens, and quadratic on that does not finish.
    This was the last of the three still doing it globally, and it was the one that
    hung the full-corpus run.
    """
    if not truth_tokens:
        return 1.0
    matched = 0
    for pred_line, truth_line in pairs:
        t_tokens = truth_line.split()
        if not t_tokens:
            continue
        if pred_line == truth_line:
            matched += len(t_tokens)
            continue
        matched += sum(
            b.size
            for b in SequenceMatcher(
                None, t_tokens, pred_line.split(), autojunk=False
            ).get_matching_blocks()
        )
    return matched / truth_tokens


def score_pair(name: str, pred_raw: str, truth_raw: str) -> Score:
    pred, truth = normalise(pred_raw), normalise(truth_raw)
    # Aligned once and shared: the three metrics each used to recompute it, which
    # tripled the cost of the most expensive step for no reason.
    pairs = _aligned_line_pairs(pred, truth)
    dia, aligned = diacritic_accuracy(pairs)
    return Score(
        document=name,
        char_accuracy=round(char_accuracy(pairs, len(truth)), 6),
        diacritic_accuracy=round(dia, 6) if dia is not None else None,
        syllable_accuracy=round(syllable_accuracy(pairs, len(truth.split())), 6),
        truth_chars=len(truth),
        diacritic_positions=aligned,
    )


def aggregate(scores: list[Score], failures: list[str]) -> dict:
    """Weight by document length, so one short file cannot swing the headline."""
    total = sum(s.truth_chars for s in scores) or 1
    dia_scores = [s for s in scores if s.diacritic_accuracy is not None]
    dia_total = sum(s.diacritic_positions for s in dia_scores) or 1

    return {
        "n_documents": len(scores),
        "n_failures": len(failures),
        "failures": failures,
        "char_accuracy": round(sum(s.char_accuracy * s.truth_chars for s in scores) / total, 6),
        "diacritic_accuracy": (
            round(sum(s.diacritic_accuracy * s.diacritic_positions for s in dia_scores) / dia_total, 6)
            if dia_scores
            else None
        ),
        "syllable_accuracy": round(sum(s.syllable_accuracy * s.truth_chars for s in scores) / total, 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pred", type=Path, required=True, help="directory of parser output, one .txt per document")
    ap.add_argument("--truth", type=Path, required=True, help="directory of ground-truth transcripts")
    ap.add_argument("--subset", required=True, choices=["public-domain", "synthetic"])
    ap.add_argument("--tool", default="viparse")
    ap.add_argument("--tool-version", default="")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true", help="run the built-in check and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    truths = sorted(args.truth.glob("*.txt"))
    if not truths:
        print(f"no ground truth in {args.truth}", file=sys.stderr)
        return 1

    scores: list[Score] = []
    failures: list[str] = []
    for truth_file in truths:
        pred_file = args.pred / truth_file.name
        if not pred_file.exists():
            # A missing prediction is a failure, not an absence. Dropping it would
            # let a parser that crashes on hard files score perfectly on easy ones.
            failures.append(truth_file.stem)
            continue
        scores.append(
            score_pair(
                truth_file.stem,
                pred_file.read_text(encoding="utf-8"),
                truth_file.read_text(encoding="utf-8"),
            )
        )

    report = {
        "tool": args.tool,
        "tool_version": args.tool_version,
        "subset": args.subset,
        "metric_version": "1",
        "summary": aggregate(scores, failures),
        "documents": [asdict(s) for s in scores],
    }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def self_test() -> int:
    """Check the metric against a real TCVN3 sample before it is trusted on a corpus."""
    garbled = "B\u00b8o c\u00b8o t\u00b5i ch\u00ddnh qu\u00fd II n\u00a8m 2026 c\u00f1a c\u00abng ty."
    correct = "B\u00e1o c\u00e1o t\u00e0i ch\u00ednh qu\u00fd II n\u0103m 2026 c\u1ee7a c\u00f4ng ty."
    stripped = "Bao cao tai chinh quy II nam 2026 cua cong ty."

    ok = True

    def check(label: str, pred: str, lo: float, hi: float) -> None:
        nonlocal ok
        s = score_pair(label, pred, correct)
        d = s.diacritic_accuracy
        good = d is not None and lo <= d <= hi
        print(
            f"  {label:20} char={s.char_accuracy:.3f} diacritic={d:.3f} "
            f"syllable={s.syllable_accuracy:.3f}  {'ok' if good else 'FAIL'}"
        )
        if not good:
            print(f"    expected diacritic_accuracy in [{lo}, {hi}]", file=sys.stderr)
            ok = False

    check("perfect", correct, 1.0, 1.0)
    check("diacritics dropped", stripped, 0.0, 0.0)
    # Not 0: `\u00fd` maps to itself in TCVN3, so `qu\u00fd` survives the corruption
    # intact. Raw mojibake scoring slightly above zero is correct, and worth knowing
    # before someone reads a low-but-nonzero baseline as a bug.
    check("raw mojibake", garbled, 0.0, 0.2)

    # The property the whole metric exists for: stripping diacritics must look fine
    # on char_accuracy and score zero here. If that gap closes, the metric is broken.
    s = score_pair("gap", stripped, correct)
    if not (s.char_accuracy > 0.8 and s.diacritic_accuracy == 0.0):
        print("    FAIL: metric no longer separates base letters from diacritics", file=sys.stderr)
        ok = False
    else:
        print(f"  separation          char={s.char_accuracy:.3f} vs diacritic=0.000  ok")

    print("  self-test:", "pass" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
