# viparse-corpus

Benchmark corpus and scoring harness for [viparse](https://github.com/TrizenX/viparse) —
how well does a document loader recover Vietnamese diacritics from files written in
pre-Unicode encodings?

**Status: scaffolding.** The metric and the harness exist and are tested; the corpus
is empty. Numbers land with viparse v0.2.

## Why this is a separate repo

The benchmark is only worth anything if a reader can re-run it. That requires
publishing the documents, which requires their licensing and PII status to be settled
per file — a different problem, with a different licence and a different size profile,
from a Python library. Keeping it here lets the library stay small and lets the corpus
carry its own terms.

## What is measured

Three numbers, defined in [`METRIC.md`](METRIC.md) **before** any result was produced:

| | |
| --- | --- |
| `char_accuracy` | Character similarity overall. Broad, and deliberately not the headline |
| `diacritic_accuracy` | **The headline.** Of the ground truth's diacritic-bearing characters, how many came back exactly right |
| `syllable_accuracy` | Whitespace tokens matching exactly — the closest proxy for retrieval behaviour |

The separation matters: a parser that turns `Báo cáo tài chính` into
`Bao cao tai chinh` scores **0.83** on `char_accuracy` and **0.00** on
`diacritic_accuracy`. That gap is the whole reason this benchmark exists, and the
self-test asserts it stays open.

## Running it

Stdlib only — nothing to install, so anyone can check the numbers.

```bash
python3 scripts/score.py --self-test --pred . --truth . --subset public-domain

python3 scripts/score.py \
  --pred out/ --truth ground-truth/ \
  --subset public-domain --tool viparse --tool-version 0.2.0 \
  --out results/viparse-public-domain.json
```

`--pred` holds one `.txt` per document, named to match the ground truth. A missing
prediction counts as a **failure**, not an absence — a parser that crashes on hard
files does not get to score only the easy ones.

## Layout

```
corpus/
  public-domain/{tcvn3,vni,viscii,vps}/   real documents, redistributable
  synthetic/                              generated from clean Unicode
ground-truth/                             expected transcript per document
results/                                  versioned results.json
scripts/
  score.py                  the metric (self-tested)
  validate_provenance.py    CI guard: no file without a source
PROVENANCE.md               per-file origin and redistribution basis
METRIC.md                   the metric, written before measuring
```

## Two subsets, never mixed

**`public-domain`** — real Vietnamese documents whose origin permits redistribution.
The credible core. Every file needs a row in [`PROVENANCE.md`](PROVENANCE.md); CI
fails without one.

**`synthetic`** — clean Unicode converted *backwards* into legacy encodings. Unlimited
volume, perfect ground truth, and **circular**: generated with the same conversion
tables viparse decodes with, so it demonstrates self-consistency rather than
real-world correctness.

Reported separately, always. No headline number is drawn from the synthetic set. The
circularity is reducible — generate with published third-party tables where they
exist — but not removable, so it is disclosed instead.

## What this does not measure

Said here so nobody has to find out in a comment thread: layout and table structure,
OCR quality beyond diacritics, and speed. viparse is expected to be **weaker than
layout-focused tools** on the first of those.

## Contributing documents

Read [`PROVENANCE.md`](PROVENANCE.md) first. A document is eligible only with a clear
redistribution basis and a PII review. **Documents encountered through employment are
never eligible**, however well they demonstrate the problem.

## Licence

Harness and scripts: [MIT](LICENSE). Corpus documents carry their own terms, recorded
per file in `PROVENANCE.md`.
