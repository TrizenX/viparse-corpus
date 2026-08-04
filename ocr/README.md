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

## Results — viparse 0.1.25 + Tesseract 5.5.3, `vie`

| render | documents | char | **diacritic** | syllable |
| --- | ---: | ---: | ---: | ---: |
| clean, all | 96 | 0.874 | **0.933** | 0.872 |
| clean, prose only | 65 | 0.926 | **0.967** | 0.938 |
| degraded, all | 96 | 0.749 | **0.816** | 0.748 |
| degraded, prose only | 65 | 0.856 | **0.898** | 0.866 |

For comparison, the same metric on the same documents through the **conversion** path —
legacy bytes, no OCR — is **0.982**.

**OCR is the weakest part of viparse, by a wide margin, and 0.967 is its ceiling.** That
figure comes from a perfectly rendered page with no skew, no sensor noise, no paper
texture and no bleed-through, in a font Tesseract finds easy. A real scan will do worse
than 0.967; the degraded row suggests roughly how much, and it is not a substitute for
measuring real scans.

## Why two subsets

31 of the 96 transcripts are spreadsheets — tab-separated tables. This renderer wraps text
to a column width, so a tabular row becomes a run-on line and the layout is destroyed
*before Tesseract sees it*. Those documents score 0.714 against 0.914 for `.doc` and 0.999
for `.pdf`, and that gap measures the renderer, not the OCR.

| source format | n | diacritic (mean) |
| --- | ---: | ---: |
| `.pdf` | 5 | 0.999 |
| `.rtf` | 11 | 0.991 |
| `.doc` | 48 | 0.914 |
| `.ppt` | 1 | 0.895 |
| `.xls` | 31 | **0.714** |

So both figures are published: the whole corpus, and the 65 documents this renderer can
actually draw. The cut is `>80%` of non-blank lines containing a tab.

**That threshold was chosen after seeing the scores**, which is worth saying rather than
hiding. What makes it defensible is that it lands in an empty part of the distribution —
31 documents sit above 0.8 and 5 sit between 0.2 and 0.8 — and that both numbers are here
either way.

## What OCR actually gets wrong

Almost entirely **tone marks**, in both directions:

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

## Caveats

- **A rendered page is not a scan.** Stated again because it is the whole limitation.
- **Three pages per document.** 56 of 96 transcripts are longer and were truncated to
  exactly the rendered text, so the score compares like with like. 243 pages per variant.
- **One font, one engine, one language model.** Arial Unicode, Tesseract 5.5.3, `vie`.
  Nothing here says how a different font or a newer model would score.
- **No real scanned Vietnamese document has been measured at all.** That still needs one,
  and it is the thing that would make this number mean what people will assume it means.
