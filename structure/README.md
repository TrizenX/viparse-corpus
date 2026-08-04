# Structure benchmark — ordinary Unicode documents

Everything else in this repository measures **legacy-encoded** documents. That is the
moat and the right thing to measure, but it says nothing about what viparse does with an
ordinary Unicode `.docx` or PDF — which is most of what anyone will actually feed it.

On 2026-08-04 that gap was closed by spot-checking rather than measuring, and twenty
minutes of it found three defects. "Probably fine" stopped being a defensible answer, so
this exists.

## What it measures

Four numbers per document, each a counting argument against labels planted in the file,
not a comparison against a transcript.

| | |
| --- | --- |
| `order` | Of consecutive labelled paragraphs, how many came back in the right order. **The headline.** |
| `completeness` | How many labelled paragraphs came back at all. |
| `headings` | How many known section titles came back *as headings* rather than as paragraphs. |
| `table` | Whether every data row survived, and whether each chunk carrying rows also carries the header. |

`order` and `completeness` are kept apart on purpose. Dropping content and reordering it
are different defects with different causes, and one blended score would hide either.

`headings` looks like a cosmetic detail and is not. Section-aware chunking runs on
headings; with none, every chunk's `section` metadata is empty and chunking degrades to
splitting on size.

## Why this one is not circular

The headline accuracy figure in [`RESULTS.md`](../RESULTS.md) is circular, and that file
says so twice: the transcripts and the conversion tables were derived from the same
documents, so it measures self-consistency as much as correctness.

This benchmark cannot be, and the reason is structural rather than a matter of care. It
never compares against a transcript. It plants labels — numbered paragraphs, named
headings, a table with a known header — and counts whether they come back in the right
order, at the right level, attached to the right things. The generator shares no code
with the parser, and `Đoạn số 07` cannot be talked into looking correct. **Nothing here
improves by editing the ground truth**, because the ground truth is arithmetic.

Its weakness is the opposite one, and it is real: **these documents are generated, not
found.** A generator emits clean, well-formed files, so this measures the parser against
the easy half of the world. It is a floor, not a ceiling — a defect it finds is real, a
defect it misses proves nothing.

## Running it

```bash
pip install "viparse[all]" python-docx openpyxl python-pptx reportlab

python3 scripts/make_structure_bench.py --out structure/documents/
python3 scripts/score_structure.py --documents structure/documents/ \
    --out structure/results/viparse-0.1.24.json
```

The documents are regenerated rather than committed: they are a few hundred lines of
deterministic output from a script that is itself the specification. The PDFs need a
Unicode TTF on the system, because reportlab's built-in fonts have no Vietnamese
repertoire and would silently emit boxes for every diacritic.

## Results — viparse 0.1.24

| document | order | completeness | headings | table |
| --- | ---: | ---: | ---: | --- |
| `structured.docx` | **1.000** | 1.000 | **1.000** | ok |
| `structured.xlsx` | **1.000** | 1.000 | **1.000** | ok |
| `structured.pptx` | **1.000** | 1.000 | **1.000** | ok |
| `one_column.pdf` | **1.000** | 1.000 | **0.000** | ok |
| `two_column.pdf` | **0.600** | 1.000 | **0.000** | ok |
| `three_column.pdf` | **0.657** | 1.000 | **0.000** | ok |

Nothing is ever lost — `completeness` is 1.000 everywhere, in every version measured.
Both remaining failures are failures of *arrangement*, which is the harder kind to
notice: the text is all there, fluent, and wrong.

### What the two zero columns mean

**A PDF has no headings.** viparse does not infer them from font size, so every title in
a PDF arrives as an ordinary paragraph and every chunk from a PDF carries an empty
`section`. Section-aware chunking works on `.docx`, `.xlsx` and `.pptx`; on PDF it is
splitting on size.

**A multi-column PDF is read across the page, not down the columns.** Paragraph 1 is
followed by paragraph 19. Recovering the columns means detecting them, which is layout
analysis — the thing viparse deliberately does not do, and the [whitespace table
detection experiment](../RESULTS.md) is what that road costs when guessed at: 0.991 to
0.493. For multi-column PDFs, use a layout-aware loader and pass its output through
`viparse.fix()`.

## What it found

Three defects, all of them in code that had been shipped and none of them visible in the
text output:

**PowerPoint titles were never headings** (since 0.1.19). `shape is slide.shapes.title`
never matched, because python-pptx builds a fresh proxy on every access —
`slide.shapes.title is slide.shapes.title` is itself `False`. The title was always
present and in the right place, just unmarked, so no presentation ever had a section to
chunk on. `headings` for `.pptx`: 0.000 → 1.000.

**A table split across chunks lost its header.** The header row stayed with the previous
chunk, so the continuation was `Tăng trưởng GDP  5,66%  6,42%` with nothing saying which
quarter was which. Retrieval surfaces such a chunk alone, and it looks usable.

**A table split across PDF pages lost its header too**, for a different reason: it came
back as two blocks and the second one had no header row at all. Now rejoined, under
narrow conditions — the continuation must open its page, start near the top, follow a
table, and match its column count.

The first version of this benchmark reported "table: ok" for every document, because its
table had four rows and always fit in one chunk. A benchmark whose fixture cannot
reproduce the defect is a benchmark that certifies it.
