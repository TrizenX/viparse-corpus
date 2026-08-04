#!/usr/bin/env python3
"""Score viparse against the structure benchmark: order, completeness, headings, tables.

Four numbers per document, all of them counting arguments against labels planted by
``make_structure_bench.py`` rather than comparisons against a transcript.

``order``
    Of the consecutive pairs of labelled paragraphs, how many came back in the right
    order. **This is the headline.** A multi-column PDF read line-by-line across the page
    interleaves the columns, and the resulting text is fluent, complete, and wrong — the
    hardest kind of failure to notice, and the one that quietly ruins retrieval.

``completeness``
    How many labelled paragraphs came back at all. Kept separate from ``order`` because
    dropping content and reordering it are different defects with different causes, and a
    single blended score would hide either one.

``headings``
    How many known section titles came back as *headings* rather than as ordinary
    paragraphs. This is what section-aware chunking runs on: with no headings, a chunk's
    ``section`` metadata is empty and chunking degrades to splitting on size.

``table``
    Whether every data row survived, and whether each chunk carrying rows also carries
    the header. A retrieved chunk of bare numbers with no column names is worse than a
    missing chunk: it looks usable.

    python3 scripts/score_structure.py --documents structure/documents/ \\
        --out structure/results/viparse-0.1.24.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LABEL = re.compile(r"Đoạn số (\d+)")


def _ratio(good: int, total: int) -> float:
    """A score with no total is 1.0 — nothing was asked, so nothing was missed."""
    return 1.0 if total == 0 else round(good / total, 4)


def score_order(labels: list[int]) -> float:
    if len(labels) < 2:
        return 1.0
    ascending = sum(1 for a, b in zip(labels, labels[1:], strict=False) if b > a)
    return _ratio(ascending, len(labels) - 1)


HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)


def score_headings(markdown: str, expected: list[str]) -> tuple[float, list[str]]:
    """Headings are read out of the Markdown, not out of the block tree.

    Deliberately: the block tree is internal, and what decides whether section-aware
    chunking has anything to work with is what actually reaches the caller. If a title
    is a heading internally but renders as a paragraph, that is still a defect.
    """
    found = set(HEADING.findall(markdown))
    missing = [title for title in expected if title not in found]
    return _ratio(len(expected) - len(missing), len(expected)), missing


def score_table(chunks: list[object], table: list[list[str]]) -> dict:
    """Rows recovered, and whether any chunk carries rows without the header."""
    header_cells = table[0]
    data_rows = table[1:]

    def cells_present(text: str, cells: list[str]) -> bool:
        return all(cell in text for cell in cells)

    joined = "\n".join(c.text for c in chunks)
    recovered = sum(1 for row in data_rows if cells_present(joined, row))

    orphaned = 0
    carrying = 0
    for chunk in chunks:
        rows_here = sum(1 for row in data_rows if cells_present(chunk.text, row))
        if not rows_here:
            continue
        carrying += 1
        if not cells_present(chunk.text, header_cells):
            orphaned += 1
    return {
        "rows_recovered": _ratio(recovered, len(data_rows)),
        "chunks_with_rows": carrying,
        "chunks_missing_header": orphaned,
        "header_always_present": orphaned == 0,
    }


def score_document(path: Path, spec: dict) -> dict:
    import viparse
    from viparse.chunk import ChunkOptions

    document = viparse.load(
        str(path), output="markdown", chunk=ChunkOptions(max_tokens=64, overlap_tokens=0)
    )[0]
    labels = [int(m) for m in LABEL.findall(document.text)]
    heading_score, missing = score_headings(document.text, spec["headings"])

    return {
        "document": path.name,
        "order": score_order(labels),
        "completeness": _ratio(len(set(labels)), spec["paragraphs"]),
        "headings": heading_score,
        "headings_missing": missing,
        "table": score_table(document.chunks, spec["table"]),
        "labels_read": labels,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--documents", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    try:
        import viparse
    except ImportError:
        print('viparse is required: pip install "viparse[all]"', file=__import__("sys").stderr)
        return 2

    manifest = json.loads((args.documents / "manifest.json").read_text(encoding="utf-8"))
    present = [(n, s) for n, s in manifest.items() if (args.documents / n).exists()]
    missing = [n for n in manifest if not (args.documents / n).exists()]
    if missing:
        # Said out loud, not skipped quietly. The first run of this script scored five
        # documents and printed a clean table; the sixth had never been written to disk
        # because the generator forgot to save it, and nothing anywhere said so.
        print(
            f"  MISSING from {args.documents}: {', '.join(missing)}"
            "\n  These are in the manifest and were not scored.\n"
        )
    results = [score_document(args.documents / name, spec) for name, spec in present]

    def mean(key: str) -> float:
        return round(sum(r[key] for r in results) / len(results), 4) if results else 0.0

    payload = {
        "tool": "viparse",
        "tool_version": viparse.__version__,
        "subset": "structure",
        "metric_version": "1",
        "summary": {
            "n_documents": len(results),
            "not_scored": missing,
            "order": mean("order"),
            "completeness": mean("completeness"),
            "headings": mean("headings"),
            "documents_with_orphaned_table_rows": sum(
                1 for r in results if not r["table"]["header_always_present"]
            ),
        },
        "documents": results,
    }

    print(f"\n  viparse {viparse.__version__} — structure benchmark\n")
    print(f"  {'document':22} {'order':>7} {'complete':>9} {'headings':>9}  table")
    for r in results:
        table = r["table"]
        note = "ok" if table["header_always_present"] else f"{table['chunks_missing_header']} orphaned"
        print(
            f"  {r['document']:22} {r['order']:>7.3f} {r['completeness']:>9.3f}"
            f" {r['headings']:>9.3f}  rows {table['rows_recovered']:.2f}, {note}"
        )
    s = payload["summary"]
    print(f"\n  mean   order {s['order']}   completeness {s['completeness']}   headings {s['headings']}\n")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
