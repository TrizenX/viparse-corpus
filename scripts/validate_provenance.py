#!/usr/bin/env python3
"""Every corpus document must have a provenance entry and a ground-truth transcript.

Enforced in CI, because the failure this guards against is silent: a file lands in
the corpus without a recorded source, nobody notices, and the corpus stops being
publishable — at which point the benchmark stops being checkable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS, TRUTH, PROVENANCE = ROOT / "corpus", ROOT / "ground-truth", ROOT / "PROVENANCE.md"

REQUIRED_COLUMNS = ["file", "source", "retrieved", "publisher", "basis"]


def documented_files() -> set[str]:
    """Filenames in the table under `## Files`.

    Scoped to that section on purpose: PROVENANCE.md also contains explanatory
    tables, and parsing every table in the file makes column headers look like
    undocumented corpus entries.
    """
    if not PROVENANCE.exists():
        return set()

    lines = PROVENANCE.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "## files")
    except StopIteration:
        return set()

    found = set()
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("#"):  # next section — stop
            break
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or cells[0] in ("file", "") or set(cells[0]) <= set("-: "):
            continue
        found.add(cells[0].strip("`"))
    return found


def main() -> int:
    corpus_files = sorted(
        p for p in CORPUS.rglob("*") if p.is_file() and p.name != ".gitkeep"
    )
    documented = documented_files()
    problems: list[str] = []

    for path in corpus_files:
        rel = path.relative_to(ROOT).as_posix()
        if path.name not in documented and rel not in documented:
            problems.append(f"no provenance entry: {rel}")
        if not (TRUTH / f"{path.stem}.txt").exists():
            problems.append(f"no ground truth: {rel} (expected ground-truth/{path.stem}.txt)")

    orphans = documented - {p.name for p in corpus_files} - {
        p.relative_to(ROOT).as_posix() for p in corpus_files
    }
    problems += [f"provenance entry with no file: {name}" for name in sorted(orphans)]

    if problems:
        print(f"{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"ok — {len(corpus_files)} document(s), all with provenance and ground truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
