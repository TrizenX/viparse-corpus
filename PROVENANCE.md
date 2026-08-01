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
| `status` | `pending-transcript` or `ready` — see below |
| `notes` | PII review outcome, anything unusual |

## Status

A document is collected long before it can be scored, so the two are tracked apart.

- **`pending-transcript`** — in the corpus, provenance recorded, but no ground-truth
  transcript and no PII review yet. It is **not** scored.
- **`ready`** — transcript exists in `ground-truth/`, PII reviewed. CI fails if a
  `ready` document has no transcript, or if a transcript exists for a document still
  marked pending.

Collection is automatable and cheap; transcription is manual and slow. Requiring both
at once would have pushed collection out of version control, which is where the
provenance record needs to live.

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

| file | source | retrieved | publisher | basis | encoding | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `2002-0112qd.doc` | http://www.mof.gov.vn:80/vanban/2001/0112qd.DOC | 2002-07-26 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2003-02120.doc` | http://www.mof.gov.vn:80/vb_phapquy/02120.doc | 2003-03-19 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2003-02144qd.doc` | http://www.mof.gov.vn:80/vb_phapquy/02144qd.doc | 2003-03-08 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-0328NDCP.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/0328NDCP.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B6.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/B6.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B8.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/B8.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2005-nghiencuu_2004_07_21_110129.doc` | http://www.sbv.gov.vn:80/Tintuc/CLPTNH/nguyendailai/Tin/nghiencuu_2004_07_21_110129.doc?tin=33 | 2005-10-18 | sbv | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2005-nghiencuu_2005_09_15_090641.doc` | http://www.sbv.gov.vn:80/Tintuc/CLPTNH/nguyendailai/Tin/nghiencuu_2005_09_15_090641.doc?tin=99 | 2005-12-21 | sbv | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-1113C_Michele_Debonneuil-_Phattrien_congnghe.doc` | http://www.mpi.gov.vn:80/bangbieu/1113C_Michele_Debonneuil-_Phattrien_congnghe.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-13D56_Le_Quang_Thung-phatbieu.doc` | http://www.mpi.gov.vn:80/bangbieu/13D56_Le_Quang_Thung-phatbieu.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-19Z9A_Luat_hop_tac_xasuadoi.doc` | http://www.mpi.gov.vn:80/bangbieu/19Z9A_Luat_hop_tac_xasuadoi.doc | 2004-01-06 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2006-1A79E_Phuluc_TT03-DKKD.doc` | http://www.mpi.gov.vn:80/Bangbieu/1A79E_Phuluc_TT03-DKKD.doc | 2006-09-02 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2005-1DCA4_3b.doc` | http://www.mpi.gov.vn:80/bangbieu/1DCA4_3b.doc | 2005-05-01 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-1E849_Tran_Du_Lich.doc` | http://www.mpi.gov.vn:80/bangbieu/1E849_Tran_Du_Lich.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-1ED4D_Francois_Godement-Thoikyquado.doc` | http://www.mpi.gov.vn:80/bangbieu/1ED4D_Francois_Godement-Thoikyquado.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | pending-transcript | mixed Vietnamese/French; whole-document TCVN3 conversion corrupts the French (Franỗois for François). Needs per-run conversion |
| `2004-1F7ZB_EtudeBinh_vn.doc` | http://www.mpi.gov.vn:80/Bangbieu/1F7ZB_EtudeBinh_vn.doc | 2004-11-28 | mpi | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-NghiDinh114_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh114_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-NghiDinh115_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh115_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-NghiDinh116_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh116_2003.doc | 2004-02-04 | mard | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-NghiDinh117_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh117_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-NghiDinh29_1998.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh29_1998.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2006-Hamau1BK1995.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/Hamau1BK1995.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2006-HHamau3-1995.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/HHamau3-1995.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2006-huong-dan-ghi-phieu.doc` | http://www.molisa.gov.vn:80/qppl/data/anhtl/huong%20dan%20ghi%20phieu.doc | 2006-07-21 | molisa | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B1-1-DONTC.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-1-DONTC | 2004-07-10 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B1-2-TMDA.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-2-TMDA | 2004-07-10 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B1-3-LLTC.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-3-LLTC | 2004-07-10 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-B1-4-LLCN.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-4-LLCN | 2004-07-10 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-HDTMDT.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/HDTMDT | 2004-07-10 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-13-t-Phuluc3.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2004/13-t-Phuluc3.doc | 2004-06-23 | most | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2005-QD-256.doc` | http://www.cantho.gov.vn:80/files/van%20ban%20%20cua%20tpct/QD%20256.doc | 2005-11-06 | cantho | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2004-TT1691998.doc` | http://www.binhduong.gov.vn:80/cucthue/Chinhsach/Noidung_chinhsach/Khong%20theo%20luat%20dtu/TT1691998.doc | 2004-06-20 | binhduong | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2003-TT132001.doc` | http://www.binhduong.gov.vn:80/cucthue/Chinhsach/Noidung_chinhsach/Luat%20dau%20tu/TT132001.doc | 2003-11-25 | binhduong | public-domain-law | tcvn3 | ready | transcript from scripts/tcvn3.py, read through; heading case in all-lowercase-ASCII lines unverified |
| `2009-download.doc` | http://www.dongnai.gov.vn:80/cong-dan/Administrative%20Procedure/20081113.749/20081202.354/20081202.166/download | 2009-03-27 | dongnai | public-domain-law | vni | ready | transcript from scripts/vni.py, read through; heading case in all-lowercase-ASCII lines unverified |
