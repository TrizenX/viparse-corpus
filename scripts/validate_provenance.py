#!/usr/bin/env python3
"""Every corpus document must have a provenance entry; scored ones also need a transcript.

Provenance is a hard requirement, because the failure it guards against is silent: a
file lands in the corpus without a recorded source, nobody notices, and the corpus
stops being publishable — at which point the benchmark stops being checkable.

Ground truth is required only once a document is marked `ready`. Transcribing is slow
manual work, and a rule that blocked a document from being collected until it was
also transcribed would just push collection out of version control.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS, TRUTH, PROVENANCE = ROOT / "corpus", ROOT / "ground-truth", ROOT / "PROVENANCE.md"
SYNTHETIC_TRUTH = ROOT / "ground-truth-synthetic"


def truth_dir(path: Path) -> Path:
    """The transcript directory for a corpus file.

    The two subsets keep separate transcripts so that neither scoring run can pick up
    the other's by globbing. Checking only `ground-truth/` would report every synthetic
    document as `ready but no ground truth`.
    """
    return SYNTHETIC_TRUTH if "synthetic" in path.parts else TRUTH

REQUIRED_COLUMNS = ["file", "source", "retrieved", "publisher", "basis"]


def documented_rows() -> dict[str, dict[str, str]]:
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

    header: list[str] = []
    rows: dict[str, dict[str, str]] = {}
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("#"):  # next section — stop
            break
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        if cells[0] == "file":
            header = cells
            continue
        if set(cells[0]) <= set("-: "):
            continue
        rows[cells[0].strip("`")] = dict(zip(header, cells)) if header else {}
    return rows


def main() -> int:
    corpus_files = sorted(
        p for p in CORPUS.rglob("*") if p.is_file() and p.name != ".gitkeep"
    )
    documented = documented_rows()
    problems: list[str] = []
    ready = pending = 0

    for path in corpus_files:
        rel = path.relative_to(ROOT).as_posix()
        row = documented.get(path.name) or documented.get(rel)
        if row is None:
            problems.append(f"no provenance entry: {rel}")
            continue

        status = (row.get("status") or "").strip()
        has_truth = (truth_dir(path) / f"{path.stem}.txt").exists()

        if status == "ready":
            ready += 1
            if not has_truth:
                problems.append(
                    f"marked ready but no ground truth: {rel} "
                    f"(expected {truth_dir(path).name}/{path.stem}.txt)"
                )
        else:
            pending += 1
            if has_truth:
                problems.append(
                    f"has ground truth but not marked ready: {rel} "
                    f"(set status to `ready` in PROVENANCE.md)"
                )

    names = {p.name for p in corpus_files} | {
        p.relative_to(ROOT).as_posix() for p in corpus_files
    }
    problems += [
        f"provenance entry with no file: {name}"
        for name in sorted(set(documented) - names)
    ]

    if problems:
        print(f"{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"ok — {len(corpus_files)} document(s): {ready} ready, {pending} awaiting transcript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
