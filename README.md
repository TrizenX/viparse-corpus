# viparse-corpus

Benchmark corpus and scoring harness for [viparse](https://github.com/TrizenX/viparse) —
how well does a document loader recover Vietnamese diacritics from files written in
pre-Unicode encodings?

**33 documents, 32 transcribed.** 32 TCVN3 and 1 VNI, collected from Vietnamese
government sites via the Internet Archive, every one confirmed legacy-encoded and
carrying a provenance record. First results are in [`RESULTS.md`](RESULTS.md).

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
  synthetic/                              real Vietnamese re-encoded into VNI
ground-truth/                             expected transcript per document
  pending/                                transcripts not yet `ready`, never scored
ground-truth-synthetic/                   expected transcript per generated document
results/                                  versioned results.json
scripts/
  score.py                  the metric (self-tested)
  find_candidates.py        locate legacy-encoded documents in the Wayback Machine
  make_synthetic.py         generate the synthetic subset from `ready` transcripts
  doc_text.py               Word 97 text extraction, independent of viparse
  tcvn3.py / vni.py         conversion tables, derived from the corpus itself
  validate_provenance.py    CI guard: no file without a source
PROVENANCE.md               per-file origin and redistribution basis
SOURCES.md                  where documents come from, and why they are redistributable
METRIC.md                   the metric, written before measuring
```

## Finding documents

Live government portals serve documents **re-published in Unicode** and are useless
here. The legacy encodings survive in archived copies of those sites from before the
migration — see [`SOURCES.md`](SOURCES.md) for the legal basis and the measured
yield.

```bash
python3 scripts/find_candidates.py --domain mof.gov.vn --from 2001 --to 2008
```

Screening is **two-stage**. The font table narrows — a Word 97 file that never declares
`.VnTime` or `VNI-Times` is not a candidate — and the text decides. The font alone is
not enough: the declaration survives conversion to Unicode, so a re-published document
keeps naming `.VnTime` while containing no legacy bytes at all. Screening on the font
alone put 27 already-Unicode files into a 62-file collection before the text stage was
added. The text stage measures high bytes following an ASCII vowel, which separates the
families as well as detecting them: TCVN3 lands at 0.14–0.18, VNI at about 0.56.

## Two subsets, never mixed

**`public-domain`** — real Vietnamese documents whose origin permits redistribution.
The credible core. Every file needs a row in [`PROVENANCE.md`](PROVENANCE.md); CI
fails without one.

**`synthetic`** — real Vietnamese converted *backwards* into a legacy encoding. It
exists because VNI ran out: 28 government domains yielded two VNI documents, and the
diaspora publishers that have more are copyrighted. The source text is the corpus's own
`ready` public-domain transcripts, re-encoded by `scripts/make_synthetic.py` and written
as `.docx` with the run font set to `VNI-Times`, so the detection and extraction layers
are exercised and not just the table.

It is **circular**: generated with the same table it scores against, so a mapping wrong
in both directions scores as correct. What it can honestly show is what an
implementation is *missing* — and that is what it found, viparse at 0.246 on diacritics
with detection working perfectly.

Two things keep it honest. The generator verifies the round trip line by line and drops
what fails, and `scripts/vni.py` refuses to encode a letter it has no observed VNI
sequence for — `ẳ` and `ẵ` appear in no collected document, so lines containing them are
dropped and counted on stderr rather than guessed at.

Reported separately, always. No headline number is drawn from the synthetic set.

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
