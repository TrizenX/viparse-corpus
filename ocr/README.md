# OCR benchmark — the first number viparse has ever had for OCR

`viparse[ocr]` was advertised in six places and measured in none. Every OCR test in the
library mocks Tesseract, no scanned document existed in any published benchmark, and the
engine had never been executed against a real Tesseract in this project. This closes that.

## How it works

Scoring OCR needs a page image whose correct text is already known. The corpus has no
scans — but it has **96 hand-written transcripts**, and rendering one back to a page image
produces exactly the missing pair at no cost in new transcription.

```bash
brew install tesseract tesseract-lang        # or the tesseract-ocr-vie system package
pip install "viparse[all]"

python3 scripts/make_ocr_bench.py --truth ground-truth/ --out ocr/clean/
python3 scripts/make_ocr_bench.py --truth ground-truth/ --out ocr/degraded/ --degrade

python3 scripts/run_viparse.py --corpus ocr/clean/images --out ocr/clean/pred
python3 scripts/score.py --pred ocr/clean/pred --truth ocr/clean/truth \
    --subset ocr-render --tool viparse+tesseract --tool-version 0.1.25
```

The renderer shares no code with viparse or with Tesseract, so nothing here can agree with
itself. Each document is a multi-page TIFF, which also exercises the frame walking the
engine does for a digitised archive.

## Results — viparse 0.1.26 + Tesseract 5.5.3, `vie`

| subject | documents | char | **diacritic** | syllable |
| --- | ---: | ---: | ---: | ---: |
| **real scans** | **3** | **0.983** | **0.973** | **0.955** |
| rendered clean, all | 96 | 0.952 | 0.990 | 0.949 |
| rendered clean, prose only | 65 | 0.951 | 0.992 | 0.951 |
| rendered degraded, all | 96 | 0.947 | 0.986 | 0.944 |
| rendered degraded, prose only | 65 | 0.949 | 0.991 | 0.947 |

For comparison, the same metric on the same documents through the **conversion** path —
legacy bytes, no OCR — is **0.986**.

The real-scan row is the one that means what people assume the others mean. Three
documents is not a benchmark; it is a floor under the claim that the rendered figures are
not fantasy, and the gap between 0.973 and 0.990 is roughly what a real page costs.

| document | char | diacritic |
| --- | ---: | ---: |
| `2005-mpi-qd837` | 0.991 | 0.988 |
| `2005-mpi-tt01-ptbv` | 0.981 | 0.983 |
| `2015-molisa-ttr-nd51` | 0.979 | 0.954 |

> **Every figure published here on the morning of 2026-08-04 was wrong**, and by a lot —
> 0.933 where the truth is 0.990. The cause was a defect in `score.py`, not in OCR, and it
> is described in [the correction below](#the-numbers-published-this-morning-were-wrong).
> The superseded results files are kept, marked with a `superseded` field.

## The two subsets no longer differ, and that is also the bug

The original split — all 96 documents against the 65 that are prose — existed because
spreadsheets scored 0.714 while `.pdf` scored 0.999, and the renderer was blamed for
flattening tab-separated tables into run-on lines.

With the metric fixed, `all` scores 0.990 and `prose only` 0.992. The renderer was not the
problem. Tabular transcripts segment very differently from OCR output, so they were the
documents the pairing defect hit hardest, and the entire justification for splitting them
out was an artifact of it.

Both subsets are still published, now for a duller reason: they agree.

## What OCR actually gets wrong

Almost entirely **tone marks**, in both directions. The counts below are from `difflib`
over flattened text and are independent of the scoring defect, so the *taxonomy* stands
even though the rates it was used to explain were overstated:

| | count | |
| --- | ---: | --- |
| `i` → `ỉ` | 93 | a hook invented where there is none |
| `ề` → `ê` | 39 | tone dropped from an already-circumflexed vowel |
| `ầ` → `â` | 14 | the same |
| `I` → `l` / `\|` | 19 | capital I, the classic |
| `ồ` → `ô` | 7 | the same |

This is the sharpest possible statement of the problem: the errors land precisely on the
marks the whole product exists to preserve. `Báo cáo tài chính quý II` came back as
`Báo cáo tài chính quý lI` on the very first run.

Note the asymmetry — Tesseract *invents* a hook on bare `i` far more often than it drops
one, and *drops* the tone from `ê`, `â`, `ồ` rather than inventing it. A post-OCR
correction pass has an obvious shape, and is not attempted here.

## A post-OCR repair layer: built, measured, not shipped

The error table above suggests an obvious fix, and it does not work. Recording why, because
the reasoning looks sound right up until it meets the data.

**The rule.** A Vietnamese syllable carries at most one tone mark — grave, acute, hook,
tilde, dot below — and `ă â ê ô ơ ư đ` are letter forms, not tones. So `tỉếng` is not a
rare word; it is orthographically impossible, and no lexicon is needed to know that. When
two tones appear and exactly one of the vowels also carries a circumflex/breve/horn, that
vowel is the nucleus, so the tone on the plain vowel is the intruder: `tỉếng` → `tiếng`.

This mattered because the alternative was a dictionary, and a dictionary built from this
corpus would make the measurement circular. The constraint comes from the writing system
instead.

**Result, on a 50/50 split fixed before anything was scored:**

| split | before | after | |
| --- | ---: | ---: | ---: |
| clean, dev | 0.96696 | 0.96693 | −0.00003 |
| clean, held-out | 0.96738 | 0.96435 | **−0.00303** |
| degraded, dev | 0.87771 | 0.87765 | −0.00006 |
| degraded, held-out | 0.91611 | 0.91582 | −0.00029 |

Worse everywhere. Two independent reasons, either of which is fatal.

**The premise is false in OCR output.** The rule assumes a token is a syllable. OCR drops
spaces, so tokens are routinely two words joined — `hướngchính`, `nướcngoài`, `lạichặt`,
`mạnhđề`. Each word has its own legitimate tone; the rule reads the pair as an impossible
syllable and deletes a **correct** tone. Every change it made on the held-out set was of
this kind.

**The error it targets does not occur.** Of 36,910 word tokens in the predictions, **4**
carry two or more tone marks — 0.01% — and only 2 are short enough to be a single syllable.
All 4 are joined words. The largest real error class is `chi` → `chỉ`, 26 occurrences: a
single tone *added*, where both the correct and the incorrect form are ordinary Vietnamese
words. No spelling rule can separate them.

**What this says about the general problem.** Every large error class here produces a
*legal* result: `chi`/`chỉ`, `ề`/`ê`, `ầ`/`â`. Orthography cannot rank legal alternatives;
that needs context, which means a language model, which means a corpus — and a corpus that
is not this one, or the measurement eats itself again.

The rule was correct about Vietnamese and wrong about the data. That is the whole lesson,
and it is why the code is not in the library.

## The numbers published this morning were wrong

`score.py` splits both texts into segments on sentence punctuation, aligns the segment
lists, and then — for a region where they differ — used to pair the two sides
**positionally**, padding the shorter with empty strings.

That breaks the moment the two sides segment differently, and they do: segmentation
depends on punctuation the parser may have misread. On the real scan `2005-mpi-qd837`, OCR
lost a single `:` in `Số : 837`. Every following segment shifted by one, the title block
was compared against an unrelated paragraph, and one 284-character segment was scored
against `""`.

- Raw similarity of the two texts, whitespace flattened: **0.9904**
- Reported by the metric: **0.578**

The fix joins each changed region and compares it as one pair, with a size cap so the
baseline row — mojibake that shares almost nothing with the truth — cannot fall back into
the O(n²) alignment this file was already written to avoid. `--self-test` now carries a
case built from that exact scan: a lost `:` must not cost more than 5% of char accuracy.

What moved:

| | before | after |
| --- | ---: | ---: |
| viparse, legacy corpus | 0.982 | **0.986** |
| baseline, no conversion | 0.019 | **0.019** |
| OCR, rendered clean, all | 0.933 | **0.990** |
| OCR, rendered degraded, all | 0.816 | **0.986** |

The baseline did not move, which is the reassuring part: the floor was never in question,
so the gap the product is about is intact. Everything else was understated, OCR worst of
all — the more a prediction's punctuation differs from the truth's, the harder the defect
hit it, and OCR misreads punctuation more than any other path.

The lesson is the one this repository keeps relearning, pointed at itself this time: a
measurement that has never been checked against a simpler measurement of the same thing is
not evidence. One `difflib.SequenceMatcher` ratio, computed in three lines, would have
caught this at any point in the last four days.

## Caveats

- **A rendered page is not a scan.** Stated again because it is the whole limitation.
- **Three pages per document.** 56 of 96 transcripts are longer and were truncated to
  exactly the rendered text, so the score compares like with like. 243 pages per variant.
- **One font, one engine, one language model.** Arial Unicode, Tesseract 5.5.3, `vie`.
  Nothing here says how a different font or a newer model would score.
- **Three real scans is not a benchmark.** They exist to bound the rendered figures rather
  than to stand on their own. All three are single pages, hand-transcribed from the image
  *before* OCR was run on them.
- **Both transcripts were made by reading the scan.** That is the same method the rest of
  the corpus uses, and it carries the same risk: a transcription error is indistinguishable
  from an OCR success.
- **Twenty-five scans have been found; twenty-two are unused.** Most were rejected for
  personal data — names, addresses, company emails and phone numbers in correspondence,
  licence registers and tender awards. The corpus has excluded documents on that basis
  before. The rest are collected and untranscribed, which is the real bottleneck:
  screening 2,300 candidate URLs is a background job, and reading a page is not.

- **The automated PII screen is a first pass, not a filter.** It looks for `Ông`/`Bà`
  followed by a name, email addresses and phone numbers. It cleared a tender award whose
  only personal name sat in the signature block, with no honorific in front of it — caught
  by eye, not by the regex. Every document that reaches a transcript is read in full
  first, and that is what the screen is for: reducing how many need reading, not deciding.
