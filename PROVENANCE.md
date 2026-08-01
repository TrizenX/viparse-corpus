# Provenance

Every file in `corpus/` has a row here. No row → CI fails → it is not in the corpus.

This exists because the corpus is only useful if it can be published, and it can only
be published if every file's origin and redistribution basis is known. Reconstructing
that after the fact is impossible.

## Columns

| Column | |
| --- | --- |
| `file` | Path under `corpus/` |
| `source` | URL it came from, or how it was generated |
| `retrieved` | ISO date |
| `publisher` | Issuing body, or `synthetic` |
| `basis` | Why it is redistributable — see below |
| `encoding` | Detected legacy encoding |
| `notes` | PII review outcome, anything unusual |

## Redistribution bases

- `public-domain-law` — Vietnamese legal document; published for public dissemination
- `public-domain-gov` — official gazette or ministry publication
- `cc-*` — carries an explicit Creative Commons licence, named
- `synthetic` — generated here from clean Unicode text; no third-party rights
- `donated` — contributed with written permission; permission recorded in `donations/`

Anything not on this list does not go in. **Documents encountered through employment
are never eligible**, regardless of how well they demonstrate the problem.

## PII

Every real document is reviewed before it is committed. Names of signing officials in
their official capacity may stay — they are already public record. Personal ID
numbers, addresses, phone numbers, salaries and handwritten signatures are redacted,
and the redaction is noted.

If a document cannot be redacted without destroying the encoding artefacts it was
collected for, it does not go in the public corpus.

## Files

| file | source | retrieved | publisher | basis | encoding | notes |
| --- | --- | --- | --- | --- | --- | --- |
