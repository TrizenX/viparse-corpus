# Where the documents come from

Verified 2026-08-01. Every claim here was checked by fetching, not assumed.

## The legal basis

Vietnamese IP law puts legal and administrative documents **outside copyright by
statute**, not merely by age.

> Điều 15. Các đối tượng không thuộc phạm vi bảo hộ quyền tác giả
> — Văn bản quy phạm pháp luật, văn bản hành chính, văn bản khác thuộc lĩnh vực tư
> pháp và bản dịch chính thức của văn bản đó.

"Văn bản hành chính" covers documents of state bodies, political organisations,
socio-political organisations and units of the armed forces.

This is a stronger basis than public-domain-by-age, and it is why quyết định, thông
tư, nghị định and công văn can go in the corpus and be redistributed. Provenance
basis for these: `public-domain-law`.

It does **not** cover everything on a government website — third-party reports,
photographs and commissioned studies hosted there keep their own rights. Basis is
recorded per file, not per site.

## The finding that made the corpus possible

Live portals are useless as source material. `vbpl.vn`, `congbao.chinhphu.vn` and
`vanban.chinhphu.vn` have all been rebuilt, and they serve documents **re-published
in Unicode** — correct text, no encoding artefacts, nothing to test against.

The legacy encodings survive in **archived copies of those sites from before the
migration**. The Wayback Machine holds `.doc` files from `.gov.vn` domains going back
to the early 2000s, in the era when TCVN3 and VNI were how Vietnamese was written.

Measured on `mof.gov.vn`, 2001–2006:

```
$ python3 scripts/find_candidates.py --domain mof.gov.vn --from 2001 --to 2006 --limit 14

  tcvn3  02144qd.doc     .VnTime, .VnTimeH
  tcvn3  0328NDCP.doc    .VnTime, .VnTimeH
  tcvn3  0112qd.DOC      .VnArial, .VnArialH, .VnAvantH
  ...
  8/14 legacy-encoded (0 download failures)
```

A confirmed sample — Ministry of Finance decision, November 2002, read as Latin-1:

```
bé tµi chÝnh          céng hoµ x· héi chñ nghÜa ViÖt nam
Hµ néi, ngµy 22 th¸ng 11 n¨m 2002
quyÕt ®Þnh cña bé tr­ëng bé tµi chÝnh
vÒ viÖc söa ®æi møc thuÕ suÊt cña mét sè mÆt hµng trong
```

## How screening works — corrected 2026-08-01

The first version of this screen used the **font table alone**, on the reasoning that
a file declaring `.VnTime` is legacy-encoded by construction.

**That was wrong, and it cost 28 of 62 collected documents.** The font declaration
survives conversion: when a document's text is migrated to Unicode, the legacy font
often stays in its table. Screening on that signal alone had a **44% false-positive
rate** — 27 files were already Unicode and one was empty.

Screening is now two stages, and both are needed:

1. **Font table** narrows the candidates — it says which encoding the document was
   authored in.
2. **The extracted text decides** — a file counts as legacy only when its characters
   are Latin-1 byte values rather than Vietnamese Unicode.

Stage 2 needs a working `.doc` extractor, which is `scripts/doc_text.py` — written
here rather than borrowed from viparse, because a corpus screened by the library
under test would be a corpus of exactly the files that library already handles.

## Ground truth

Also produced independently of viparse, for the same reason: a transcript generated
by the tool being measured would score 100% against itself and mean nothing.

`scripts/tcvn3.py` holds a TCVN3 → Unicode table derived from the corpus itself, by
aligning byte sequences against the fixed phrases Vietnamese legal documents always
carry — "Cộng hoà xã hội chủ nghĩa Việt Nam", "Căn cứ Nghị định số", "Độc lập - Tự
do - Hạnh phúc" — and extended until no Latin-1 byte was left unmapped across all 31
TCVN3 files.

A first draft of that table guessed at four bytes to make the unmapped count reach
zero. All four guesses were wrong: `¡ ¢ £ ¤` are **Ă Â Ê Ô**, not accented lowercase.
They sit in a block, `A1–A7`, holding the uppercase base vowels, with `A8–AE` holding
the lowercase ones — a structure invisible to anyone filling gaps to make a number
look tidy. Every entry is now backed by a context quotation.

### The one thing still unresolved

TCVN3 has **no uppercase accented letters**. An uppercase heading is typed with
uppercase ASCII and the same accented bytes as lowercase, and `.VnTimeH` draws them
uppercase. Byte-level conversion therefore produces `TOàN` for `TOÀN`.

Where the ASCII in a line is uppercase, this is unambiguous and repaired. Where a
heading was typed entirely in lowercase ASCII and left to the font, it is not
recoverable from the bytes — and those lines stay lowercase.

Measured exposure across the ten transcripts: **24 of 593 lines (4.0%), 1.9% of
characters.** Concentrated in document letterheads and titles.

Fixing it properly means parsing the character-property runs to find which text is
set in `.VnTimeH`. Until then the ten transcripts are marked `ready` with this
caveat recorded per file, because a transcript that is 98% right and honest about the
other 2% is more useful than no transcript.

## Measured yield, 2026-08-01

Twelve domains screened, 139 candidates fetched, **61 confirmed legacy-encoded (44%)**.

| Domain | Checked | Hits | Encodings |
| --- | ---: | ---: | --- |
| `mof.gov.vn` | 14 | 8 | tcvn3 |
| `sbv.gov.vn` | 11 | 7 | tcvn3 |
| `moit.gov.vn` | 12 | 6 | tcvn3, vni |
| `mpi.gov.vn` | 11 | 6 | tcvn3 |
| `mard.gov.vn` | 12 | 5 | tcvn3 |
| `molisa.gov.vn` | 12 | 5 | tcvn3 |
| `most.gov.vn` | 10 | 5 | tcvn3 |
| `hochiminhcity.gov.vn` | 12 | **8** | tcvn3, vni |
| `cantho.gov.vn` | 10 | 4 | tcvn3 |
| `danang.gov.vn` | 12 | 3 | tcvn3 |
| `binhduong.gov.vn` | 12 | 3 | tcvn3, vni |
| `dongnai.gov.vn` | 11 | 1 | tcvn3 |

That already exceeds the ≥50-document target in the plan, and only ~12 candidates
per domain were screened — raising `--limit` will find more.

## Second sweep, 2026-08-01 — hunting VNI specifically

22 more domains: every Mekong Delta and southeast province not already screened, two
Ho Chi Minh City agencies, and four overseas missions.

| Domain | Checked | Hits | Encodings |
| --- | ---: | ---: | --- |
| `soctrang.gov.vn` | 24 | 20 | tcvn3 |
| `binhthuan.gov.vn` | 24 | 5 | tcvn3 |
| `camau.gov.vn` | 14 | 2 | **vni** |
| `angiang.gov.vn` | 24 | 2 | tcvn3 |
| `binhphuoc.gov.vn` | 24 | 1 | **vni** |
| `banqlkcn.baria-vungtau.gov.vn` | 25 | 1 | **vni** |
| `longan.gov.vn` | 24 | 1 | tcvn3 |
| `hepza.gov.vn` | 7 | 1 | tcvn3 |
| `vietnamembassy-usa.org` | 13 | 1 | tcvn3 |
| `tiengiang`, `bentre`, `vinhlong`, `dongthap`, `baclieu`, `travinh`, `tayninh`, `khanhhoa`, `itpc.hochiminhcity`, `vietnamconsulate-sf` | 11–25 each | 0 | — |
| `kiengiang.gov.vn`, `vietnamembassy-japan.org`, `vietnamembassy-france.org` | — | — | no archived `.doc` at all |

**Four VNI candidates, two usable.** One was already in the corpus
(`camau/quydinhkiemtra02`). One was a district phone directory carrying home and mobile
numbers against named individuals — excluded under the PII rule in `PROVENANCE.md`,
which is worth stating plainly: it was one of only four VNI candidates from a 22-domain
sweep, and the rule still applied. A benchmark that relaxes its own rule when material
is scarce has no rule.

The VNI subset therefore goes **2 → 4** documents.

### Overseas missions did not work

The reasoning was that embassy and consulate sites are state bodies, so Article 15
still covers their documents, but were built by contractors abroad — the population
that used VNI. Three of the four have no archived `.doc` files at all, and the fourth
yielded one TCVN3 file. The hypothesis was reasonable and it was wrong.

### 30 TCVN3 documents found and left on the table

This sweep was for VNI, so the TCVN3 hits — 20 from Sóc Trăng alone — were screened but
not fetched. They are available whenever the TCVN3 subset needs deepening; it is
already at 42 documents and 0.987, so it does not.

**Encoding distribution is badly skewed: tcvn3 = 58, vni = 3.** That matches history
— TCVN3 dominated in government and in the north — but it means a benchmark built on
this set measures TCVN3 recovery and little else. The three VNI hits came from
`hochiminhcity.gov.vn`, `binhduong.gov.vn` and `moit.gov.vn`, so southern portals are
the right place to look for more.

**VISCII and VPS: nothing — but that is not a measurement.** An earlier version of this
file reported "No VISCII or VPS found at all" as though 28 domains had been searched and
come back empty. They had not been searched. See
[the screen cannot find them](#the-screen-cannot-find-viscii-or-vps) below.

## Sources, by usefulness

| Source | Yield | Notes |
| --- | --- | --- |
| **Wayback: `.gov.vn` `.doc`, 2000–2009** | **44% across 12 domains** | The primary source. Ministry sites hosted flat directories of legal documents |
| Southern provincial portals | Best VNI odds | `hochiminhcity.gov.vn` gave the highest single yield, 8/12 |
| `vbpl.vn` scanned originals | Medium, **OCR path only** | "Văn bản gốc" pages hold scans of pre-2000 documents. No encoding to recover — a different axis |
| `congbao.chinhphu.vn` | **None** | Serves modern `.docx`/`.pdf`, Unicode |
| `vanban.chinhphu.vn`, live `vbpl.vn` | **None** | Rebuilt as SPAs, Unicode throughout |
| Diaspora / overseas publishing | Untested, and copyrighted | The likeliest home of VISCII and VPS. Article 15 does not reach it |
| Overseas missions (`vietnamembassy-*.org`) | **None** | State bodies, so Article 15 applies, and built by contractors abroad — but three of four have no archived `.doc` at all |

### The screen cannot find VISCII or VPS

Recorded because "we looked and found none" and "we never looked" read identically in a
results table, and this file printed the first when the second was true.

**The regex is blind.** `find_candidates.py` narrows on font names:

```
LEGACY_FONT = r"\.Vn[A-Za-z]+|VNI-[A-Za-z]+|VPS[A-Za-z]+|ABC[A-Za-z]*"
```

There is no VISCII pattern at all, and `ENCODING_OF` has no `viscii` key. `VPS[A-Za-z]+`
requires a letter immediately after `VPS`, so `VPSTimes` matches and **`VPS Times` — with
the space real font names carry — does not.**

**The format is wrong, which matters more.** TCVN3 and VNI are *font hacks*: ordinary
bytes rendered as Vietnamese by a special font, so the font name is a signal sitting in
the Word file. VISCII is not — it is a character set (RFC 1456) declared as
`charset=VISCII` in email, Usenet and HTML. There is no font name to find, because there
is no font trick. Screening archived `.doc` files for font declarations therefore cannot
locate VISCII however many domains it covers.

**A Word 97 `.doc` cannot even hold them.** VISCII puts 6 letters and VPS 14 in the C0
control range, which Word reserves for structural markers — `0x02` is a footnote
reference, `0x1E` a non-breaking hyphen, `0x13`–`0x15` field delimiters. Patching those
bytes into a real corpus document and re-extracting confirms it: `0x02` and `0x1E` do not
survive, because Word never meant them as text.

So the honest statement is: **no VISCII or VPS document has been looked for.** Finding
them means searching Wayback for HTML declaring `charset=viscii`, not `.doc` files — and
the licensing problem is then the real obstacle, since VISCII was overwhelmingly a
diaspora encoding and Article 15 does not cover that material.

### One caution about the numbers above

The first run of this screen used six parallel workers and reported **0 hits from
`mard.gov.vn`** — the archive was rate-limiting, and a wall of download failures is
indistinguishable from an empty archive. Re-run sequentially, the same domain gave
5/12.

`fetch()` now retries with backoff and paces itself. If a domain reports zero, check
the failure count before believing it.

## Workflow

Collect — screens, downloads, and writes each provenance row as its file lands:

```bash
python3 scripts/fetch_corpus.py --domains-file domains.txt --limit 14
```

Every row is written `pending-transcript` with PII review outstanding. Neither is
optional before a document is marked `ready` and enters the scored set.

Then, per file:

1. Confirm it is a legal or administrative document — not a third-party report
2. PII review per `PROVENANCE.md`
3. Add a row to `PROVENANCE.md` with basis `public-domain-law`, source URL and
   retrieval date
4. Produce the ground-truth transcript
5. `python3 scripts/validate_provenance.py` before committing

Step 4 is the real cost. Screening is cheap and automated; a correct Unicode
transcript is manual. Scope the real-document set small and deep rather than large
and shallow.

## Overseas publishing — searched 2026-08-01, and why nothing came from it

Government sources are exhausted for VNI: 28 Vietnamese domains produced 2 usable VNI
documents against 43 TCVN3. The encoding was common in the south and in the diaspora,
but the bodies that published to the web ran TCVN3.

So the diaspora was searched. VNI is there:

| Source | .doc archived | Legacy | Notes |
| --- | ---: | ---: | --- |
| `thuvienhoasen.org` | 60 | **2 VNI**, 2 TCVN3 | Names files by encoding — `-vni.doc`, `-tcvn.doc`. Seven more found by that filename pattern alone |
| `buddhismtoday.com` | 72 | 0 | Already Unicode |
| `quangduc.com` | 2 | 1 TCVN3 | |
| `oc.ca.gov`, `sccgov.org` | 111 | 0 | US counties with large Vietnamese populations; their Vietnamese material is not archived `.doc` |
| `nguoi-viet.com`, `vietbao.com` | 0 | — | Newspapers published HTML, not documents |

**The blocker is not supply, it is licence.** Article 15 of the Vietnamese IP law
places *legal and administrative* documents outside copyright, and that is the entire
basis on which this corpus can be published. It does not reach a Buddhist library's
translations, which belong to their translators. No licence statement was found on
`thuvienhoasen.org` or its archived pages.

So these documents are **not** in the corpus, and should not be added without
permission. Three ways forward, in order of preference:

1. **Ask.** Buddhist publishing has a strong free-distribution tradition (*ấn tống*),
   and a request naming the purpose — measuring how well software recovers Vietnamese
   from a dead encoding — is likely to be received well. `thuvienhoasen.org` labels its
   own files by encoding, which suggests people there who would understand the problem.
2. **Synthetic VNI**, generated and labelled as such. It cannot be a headline number —
   see `corpus.md` on circularity — but it can carry a table far enough to be worth
   contributing.
3. **Keep looking** in Vietnamese-language material published by US state and local
   government, which is public record. Two counties were checked and had none archived
   as `.doc`; more exist.

## Beyond `.doc`, 2026-08-02

The corpus was `.doc` only, which hid a class of problem: `.doc` reaches viparse's DOCX
engine through LibreOffice, so that one path was thoroughly covered while PDF, RTF and
XLS had no real-document coverage at all.

`find_candidates.py` and `fetch_corpus.py` now take `--kind`. Reconnaissance across the
domains already screened:

| kind | archived | declaring a legacy font |
| --- | ---: | ---: |
| `rtf` | 36 | **23** |
| `pdf` | 48 | 14 |
| `xls` | 56 | 4 |

Collected: **21 RTF** and **7 PDF**, all TCVN3, all `pending-transcript`.

### `.xls` is screened font-only, so it is not collected

A font-only screen measured a 44% false-positive rate on `.doc`. Shipping one for `.xls`
would put known-bad candidates in the corpus, and this repo has no independent `.xls`
reader to run the deciding text stage with. Left uncollected rather than collected
badly — 4 candidates is not worth the exception.

### PDFs are capped by size, and the reason is the transcript

`--max-bytes` exists because `moit.gov.vn` serves 1.3 MB monthly industrial statistics
tables. They are real legacy documents and useless here: ground truth for a table that
size cannot be produced by hand, and a benchmark entry without ground truth is storage,
not evidence.

## What is still missing

- **VISCII and VPS samples — never searched for.** 34 government domains produced only
  TCVN3 and VNI, but the screen cannot detect either encoding: it narrows on Word font
  declarations, and VISCII is a charset with no font to declare. The right search is
  Wayback HTML with `charset=viscii`, and the obstacle there is licensing, not
  discovery.
- **More VNI.** Three is not enough to say anything about VNI recovery. Southern
  provincial portals are the source that worked.
- **Ground truth for anything.** No transcripts exist yet.
- **Scanned originals** for the OCR axis.
