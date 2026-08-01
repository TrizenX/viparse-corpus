#!/usr/bin/env python3
"""Convert a document that changes legacy encoding partway through.

One document in the corpus, `2004-duanLD9820` from Lâm Đồng, is TCVN3 and VNI in the
same file — the plan was assembled from sections written on different machines, and
whoever merged them kept each section's bytes. A single table cannot read it: applying
TCVN3 throughout turns `Thường vụ Bộ Chính trị` into `Thửụứng vuù Boọ Chớnh trũ`.

Deciding per line
-----------------
Two signals, because neither is enough alone.

**Residue** — characters still in Latin-1 after conversion. TCVN3's bytes (``¸ ¹ ª «``)
are absent from the VNI table, so TCVN3 text converted as VNI leaves a great deal
behind. Useless in the other direction: TCVN3's table covers nearly the whole Latin-1
range, so VNI text converted as TCVN3 leaves almost nothing — it just produces nonsense.

**Invalid vowel clusters** — a bare vowel followed by an accented one. VNI writes `Caùc`,
which TCVN3 reads as `Caúc`, and `aú` is not a Vietnamese vowel cluster. This catches
exactly the case residue misses.

The cluster count is used *comparatively*, never against a threshold. The pattern also
matches `yê`, `iê`, `uô` and `ươ`, which are ordinary Vietnamese — so a correct reading
scores 2 or 3 on a long line, and only the difference between the two readings means
anything.

Only lines with *no* diacritic at all, or where the two readings score identically,
inherit the previous decision — an encoding change happens at a section boundary rather
than mid-sentence, so inheriting is right when there is nothing to go on.

The threshold for "enough to judge" is one high byte, not five. Five was the first
guess, and it left `UBND TØnh` and `M¸y chñ CSDL &` — short TCVN3 captions sitting
inside a VNI section — inheriting VNI and coming out as `UBND TØnh` unconverted. The
scores separate cleanly even on a single byte: 0 against 3, 1 against 6.

    python3 scripts/mixed.py file.doc
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tcvn3 as tcvn3_table  # noqa: E402
import vni as vni_table  # noqa: E402
from doc_text import extract  # noqa: E402

_ACCENTED = (
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộ"
    "ơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
)
_INVALID_CLUSTER = re.compile(f"[aeiouyAEIOUY][{_ACCENTED}]")
_MIN_HIGH_BYTES = 1


def _residue(text: str) -> int:
    return sum(
        1
        for ch in text
        if 0xA0 < ord(ch) < 0x100 and ch not in vni_table._VALID_LATIN1_VN
    )


def _score(converted: str) -> int:
    """Lower is a better reading. Residue dominates; clusters break the tie."""
    return _residue(converted) * 3 + len(_INVALID_CLUSTER.findall(converted))


def classify_line(line: str) -> str | None:
    """``"tcvn3"``, ``"vni"``, or None when the line carries no evidence."""
    if sum(1 for ch in line if 0xA0 < ord(ch) < 0x100) < _MIN_HIGH_BYTES:
        return None
    as_tcvn3 = _score(tcvn3_table.convert(line))
    as_vni = _score(vni_table.convert(line))
    if as_tcvn3 == as_vni:
        return None
    return "vni" if as_vni < as_tcvn3 else "tcvn3"


_TOKEN_MARGIN = 2


def _convert_by_token(line: str, start: str) -> str:
    """Re-read a line token by token, for the few lines that change encoding mid-line.

    Only used as a fallback, and only with a margin, because a token is short evidence:
    `diÖn` carries one high byte and scores 1 either way, so an unguarded token pass
    flips it to VNI and turns `diện rộng` into `diƯn réng` — trading four wrong
    characters for a dozen.
    """
    current = start
    out: list[str] = []
    for token in re.split(r"(\s+)", line):
        if token.strip() and any(0xA0 < ord(ch) < 0x100 for ch in token):
            as_tcvn3 = _score(tcvn3_table.convert(token))
            as_vni = _score(vni_table.convert(token))
            if abs(as_tcvn3 - as_vni) >= _TOKEN_MARGIN:
                current = "vni" if as_vni < as_tcvn3 else "tcvn3"
        out.append((vni_table if current == "vni" else tcvn3_table).convert(token))
    return "".join(out)


def convert(text: str) -> tuple[str, dict[str, int]]:
    """Convert line by line, carrying the last decision across undecidable lines.

    A line that still holds Latin-1 after conversion is direct evidence the line-level
    decision was wrong somewhere in it, so those lines — and only those — get a second
    pass at token granularity. The result is kept only if it actually leaves less behind.
    """
    out: list[str] = []
    counts = {"tcvn3": 0, "vni": 0, "inherited": 0, "by_token": 0}
    current = "tcvn3"
    for line in text.split("\n"):
        decided = classify_line(line)
        if decided is None:
            counts["inherited"] += 1
        else:
            current = decided
            counts[current] += 1
        converted = (vni_table if current == "vni" else tcvn3_table).convert(line)
        if _residue(converted):
            retry = _convert_by_token(line, current)
            if _residue(retry) < _residue(converted):
                converted = retry
                counts["by_token"] += 1
        out.append(converted)
    return "\n".join(out), counts


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    text, counts = convert(extract(sys.argv[1]))
    print(
        f"  lines: tcvn3={counts['tcvn3']} vni={counts['vni']} "
        f"inherited={counts['inherited']} by_token={counts['by_token']}",
        file=sys.stderr,
    )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
