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

## Sources, by usefulness

| Source | Yield | Notes |
| --- | --- | --- |
| **Wayback: `.gov.vn` `.doc`, 2000–2008** | **High** — 8/14 on the first domain tried | The primary source. Ministry sites hosted flat directories of legal documents; `mof.gov.vn/vb_phapquy/` is one |
| Wayback: provincial portals | Untested | `*.gov.vn` covers them; provincial sites migrated later, so the legacy window may run further |
| `vbpl.vn` scanned originals | Medium, **OCR path only** | "Văn bản gốc" pages hold scans of pre-2000 documents. No encoding to recover — these test OCR, a different axis |
| `congbao.chinhphu.vn` | **None** | Serves modern `.docx`/`.pdf`, Unicode |
| `vanban.chinhphu.vn`, live `vbpl.vn` | **None** | Rebuilt as SPAs, Unicode throughout |
| Provincial công báo (e.g. Quảng Ngãi) | Untested | Some older portals may not have migrated |

Domains worth screening next: `mard.gov.vn`, `most.gov.vn`, `moit.gov.vn`,
`molisa.gov.vn`, `mpi.gov.vn`, `sbv.gov.vn`, plus provincial `*.gov.vn`.

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

- **VNI, VISCII and VPS samples.** Everything confirmed so far is TCVN3, which
  matches its historical dominance in the north and in government use. VNI was more
  common in the south and in overseas publishing — screen southern provincial
  portals and diaspora sites for it.
- **Ground truth for anything.** No transcripts exist yet.
- **Scanned originals** for the OCR axis.
