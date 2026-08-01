# Metric definition

Written **before** any number was produced. If this document changes after results
are published, the results are republished with it.

"Diacritic accuracy" is not self-defining. Stated loosely it means whatever a critic
wants it to mean, so it is pinned here.

## Preprocessing, applied to both sides

1. **Unicode NFC.** Both the parser output and the ground truth are normalised to
   NFC before comparison. Without this we would be measuring our own output's
   normalisation form, which is a thing we control, not a thing we are testing.
2. **Whitespace collapsed.** Runs of whitespace → a single space; leading/trailing
   stripped. Line-break placement is a layout question, not an encoding one, and
   penalising it here would conflate two different failures.
3. **Nothing else.** No case folding, no punctuation stripping, no spelling
   correction.

## The three numbers

### 1. `char_accuracy`

Character-level similarity over the whole document, computed from an alignment
(`difflib.SequenceMatcher`) so insertions and deletions are handled rather than
shifting every subsequent character into a mismatch.

```
char_accuracy = matched_chars / len(ground_truth)
```

Broad, easy to reason about, and **not** the headline: a parser that drops all
Vietnamese diacritics still scores well here because base letters survive.

### 2. `diacritic_accuracy` — the headline

Measures only the thing viparse exists to fix.

**Denominator:** every character in the ground truth whose identity depends on a
diacritic — anything that decomposes to a combining mark under NFD, plus `đ`/`Đ`.
Characters carrying no diacritic are excluded entirely.

**Numerator:** those recovered exactly. Both sides are reduced to base letters (NFD,
category `Mn` removed, `đ`→`d`) and aligned; at each diacritic-bearing ground-truth
position the *original* characters are compared.

```
diacritic_accuracy = diacritic-bearing chars recovered exactly / diacritic-bearing chars in ground truth
```

Two decisions worth stating, both of which the first draft of this metric got wrong
and the self-test caught:

- **Non-diacritic characters are excluded.** In a typical Vietnamese sentence only
  ~17% of characters carry a diacritic. Counting the rest — spaces, digits,
  consonants — means they match trivially and bury the signal: a parser that strips
  *every* diacritic still scored **0.83** before this was fixed.
- **The denominator is all diacritic-bearing characters, not only aligned ones.**
  Restricting it to aligned positions would let a parser that dropped half the
  document score on the half it kept.

A parser that emits `Bao cao tai chinh` for `Báo cáo tài chính` now scores **0** here
while scoring 0.83 on `char_accuracy`. That gap is the entire point of the benchmark.

**Raw mojibake does not score 0**, and that is correct rather than a bug: some
characters coincide across encodings. In the reference sample, `ý` maps to itself in
TCVN3, so `quý` survives corruption intact and the untouched text scores 0.125.

Report `char_accuracy` alongside, always. Reporting `diacritic_accuracy` alone would
let a parser that extracted three words perfectly and dropped the rest look flawless.

### 3. `syllable_accuracy`

Whitespace-delimited tokens, exact match after NFC.

```
syllable_accuracy = exactly matching tokens / ground-truth tokens
```

The closest proxy for retrieval behaviour: an embedding model sees tokens, and one
wrong diacritic makes a token a different word.

## Reported alongside, never omitted

- `n_documents`, and the count per encoding
- Which corpus subset — `public-domain` and `synthetic` are **always reported
  separately**. Synthetic files are generated with our own conversion tables, so
  scoring them with our own decoder is circular. They measure self-consistency, not
  real-world correctness, and no headline number is drawn from them.
- Failures: any document a parser errored on, counted, not silently dropped. A parser
  that crashes on hard files and scores 100% on the rest is not a parser that scored
  100%.
- Version of every tool compared, and the date.

## What this metric does not measure

Stated here so nobody has to discover it in a comment thread:

- **Layout and table structure.** Not measured. viparse is expected to be weaker than
  layout-focused tools here.
- **OCR quality on scans**, beyond the diacritics themselves.
- **Speed.** Measured separately if at all; a benchmark that mixes accuracy and
  throughput into one score hides both.
