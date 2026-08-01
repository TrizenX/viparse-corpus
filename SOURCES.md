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

## How screening works

By **font table**, not by inspecting the text. A Word 97 file that declares
`.VnTime` or `VNI-Times` is legacy-encoded *by construction* — those bytes only
render as Vietnamese with that font applied. Reading the text and looking for
suspicious characters would be a heuristic that a Spanish or Portuguese document
could trip; the font declaration is a fact the file states about itself.

This is deliberately the same signal `viparse`'s own detector treats as primary, so
a document that lands in the corpus is one the library should get right — and if it
does not, that is a real failure rather than an argument about the corpus.

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

**Encoding distribution is badly skewed: tcvn3 = 58, vni = 3.** That matches history
— TCVN3 dominated in government and in the north — but it means a benchmark built on
this set measures TCVN3 recovery and little else. The three VNI hits came from
`hochiminhcity.gov.vn`, `binhduong.gov.vn` and `moit.gov.vn`, so southern portals are
the right place to look for more. **No VISCII or VPS found at all.** Those may need
diaspora publishing sites rather than government ones.

## Sources, by usefulness

| Source | Yield | Notes |
| --- | --- | --- |
| **Wayback: `.gov.vn` `.doc`, 2000–2009** | **44% across 12 domains** | The primary source. Ministry sites hosted flat directories of legal documents |
| Southern provincial portals | Best VNI odds | `hochiminhcity.gov.vn` gave the highest single yield, 8/12 |
| `vbpl.vn` scanned originals | Medium, **OCR path only** | "Văn bản gốc" pages hold scans of pre-2000 documents. No encoding to recover — a different axis |
| `congbao.chinhphu.vn` | **None** | Serves modern `.docx`/`.pdf`, Unicode |
| `vanban.chinhphu.vn`, live `vbpl.vn` | **None** | Rebuilt as SPAs, Unicode throughout |
| Diaspora / overseas publishing | Untested | The likeliest home of VISCII and VPS |

### One caution about the numbers above

The first run of this screen used six parallel workers and reported **0 hits from
`mard.gov.vn`** — the archive was rate-limiting, and a wall of download failures is
indistinguishable from an empty archive. Re-run sequentially, the same domain gave
5/12.

`fetch()` now retries with backoff and paces itself. If a domain reports zero, check
the failure count before believing it.

## Workflow

```bash
python3 scripts/find_candidates.py --domain mof.gov.vn --from 2001 --to 2008 \
  --download corpus/public-domain/tcvn3/
```

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

## What is still missing

- **VISCII and VPS samples — none found.** Twelve government domains produced 58
  TCVN3 and 3 VNI and nothing else. These two probably do not live on government
  sites at all; diaspora publishing is the place to look.
- **More VNI.** Three is not enough to say anything about VNI recovery. Southern
  provincial portals are the source that worked.
- **Ground truth for anything.** No transcripts exist yet.
- **Scanned originals** for the OCR axis.
