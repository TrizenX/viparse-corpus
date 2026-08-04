#!/usr/bin/env python3
"""Produce the `--pred` directory `score.py` scores, by running viparse over the corpus.

Until now this step lived in whatever shell history produced a given results file. That
is the one part of the benchmark a stranger could not reproduce: the corpus is public,
the metric is public, the results are public, and the command in between was not. A
number nobody else can regenerate is a claim, not evidence.

    pip install "viparse[all]"
    python3 scripts/run_viparse.py --corpus corpus/public-domain --out out/
    python3 scripts/score.py --pred out/ --truth ground-truth/ \\
        --subset public-domain --tool viparse --tool-version 0.1.23 \\
        --out results/viparse-0.1.23-full-corpus.json

One prediction per source file, named by stem so it lines up with the transcript of the
same name. Output is plain text rather than Markdown: the transcripts are plain text,
and scoring Markdown against them would measure table syntax rather than diacritics.

A file that raises is **skipped, loudly**. It then has no prediction, and `score.py`
counts the missing transcript as a failure — which is the intended path. Writing an
empty prediction instead would score the document as zero without ever saying a parser
had crashed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKIP_SUFFIXES = {".md", ".gitkeep"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True, help="directory of source documents")
    ap.add_argument("--out", type=Path, required=True, help="directory to write predictions into")
    ap.add_argument(
        "--encoding",
        default="auto",
        help="passed to viparse.load; 'auto' enables content detection (default)",
    )
    args = ap.parse_args()

    try:
        import viparse
    except ImportError:
        print('viparse is required: pip install "viparse[all]"', file=sys.stderr)
        return 2

    sources = sorted(
        p
        for p in args.corpus.rglob("*")
        if p.is_file() and p.suffix.lower() not in SKIP_SUFFIXES and not p.name.startswith(".")
    )
    if not sources:
        print(f"no documents under {args.corpus}", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, []
    for source in sources:
        try:
            docs = viparse.load(str(source), output="text", encoding=args.encoding)
        except Exception as exc:  # noqa: BLE001 - any parser failure is a benchmark failure
            skipped.append(f"{source.name}: {type(exc).__name__}: {exc}")
            continue
        text = "\n".join(d.text for d in docs)
        (args.out / f"{source.stem}.txt").write_text(text, encoding="utf-8")
        written += 1

    print(f"viparse {viparse.__version__}: wrote {written} prediction(s) to {args.out}")
    for line in skipped:
        print(f"  FAILED {line}", file=sys.stderr)
    if skipped:
        print(f"{len(skipped)} document(s) failed and will score as failures", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
