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
| `2003-IAP-cua-BTC-2002_e.doc` | http://www.mof.gov.vn:80/apec/IAP%20cua%20BTC%202002_e.doc | 2003-12-29 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-IAP-cua-BTC-2000-V.doc` | http://www.mof.gov.vn:80/apec/viet/IAP%20cua%20BTC%202000%20V.doc | 2004-08-08 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2002-0112qd.doc` | http://www.mof.gov.vn:80/vanban/2001/0112qd.DOC | 2002-07-26 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2003-02120.doc` | http://www.mof.gov.vn:80/vb_phapquy/02120.doc | 2003-03-19 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2003-02144qd.doc` | http://www.mof.gov.vn:80/vb_phapquy/02144qd.doc | 2003-03-08 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-0328NDCP.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/0328NDCP.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B6.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/B6.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B8.doc` | http://www.mof.gov.vn:80/wsold/hethong_vb/dvtaichinh/B8.doc | 2004-09-04 | mof | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2005-nghiencuu_2004_07_21_110129.doc` | http://www.sbv.gov.vn:80/Tintuc/CLPTNH/nguyendailai/Tin/nghiencuu_2004_07_21_110129.doc?tin=33 | 2005-10-18 | sbv | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2005-nghiencuu_2005_04_13_113329.doc` | http://www.sbv.gov.vn:80/Tintuc/CLPTNH/nguyendailai/Tin/nghiencuu_2005_04_13_113329.doc?tin=63 | 2005-10-18 | sbv | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2005-nghiencuu_2005_09_15_090641.doc` | http://www.sbv.gov.vn:80/Tintuc/CLPTNH/nguyendailai/Tin/nghiencuu_2005_09_15_090641.doc?tin=99 | 2005-12-21 | sbv | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-nghiencuu_2006_05_19_110850.Web.doc` | http://www.sbv.gov.vn/Tintuc/CSTT/cstt01/Tin/nghiencuu_2006_05_19_110850.Web.doc?tin=210 | 2006-10-05 | sbv | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-nghiencuu_2006_07_10_153423.doc` | http://www.sbv.gov.vn:80/Tintuc/CSTT/cstt01/Tin/nghiencuu_2006_07_10_153423.doc? | 2006-11-05 | sbv | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-BAO-CAO-TONG-KET-NAM-2008-CHINH-THUC.doc` | http://www1.moit.gov.vn:80/tttm/Admin/UploadFile/BAO%20CAO%20TONG%20KET%20NAM%202008%20(CHINH%20THUC).doc | 2009-03-06 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-BC-9T-WEB.doc` | http://www1.moit.gov.vn:80/tttm/Admin/UploadFile/BC%209T-WEB.doc | 2009-03-20 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-Bao-cao-hoat-dong-nganh-cong-thuong-6-thang-2009.doc` | http://www.moit.gov.vn:80/vsi_portlets/UserFiles/Docman/Upload/Bao%20cao%20hoat%20dong%20nganh%20cong%20thuong%206%20thang%202009-chinh%20thuc.doc | 2009-06-11 | moit | public-domain-law | vni | pending-transcript | PII review not done |
| `2009-Quy-dinh-nhap-khau-Braxin.doc` | http://www.moit.gov.vn:80/vsi_portlets/UserFiles/Docman/Upload/Quy%20dinh%20nhap%20khau%20Braxin.doc | 2009-12-11 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-Mauthuyetminhdetai2010KHCN.doc` | http://www.moit.gov.vn:80/vsi_portlets/UserFiles/File/Mauthuyetminhdetai2010KHCN.doc | 2009-08-16 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-phuluc3.doc` | http://moit.gov.vn:80/vsi_portlets/UserFiles/File/phuluc3.doc | 2009-02-19 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-CV-2499-2005-TC.doc` | http://www.moit.gov.vn:80/vsi_portlets/UserFiles/LegalText/Upload/CV%202499-2005-TC.DOC | 2009-04-08 | moit | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-1113C_Michele_Debonneuil-_Phattrien_congnghe.doc` | http://www.mpi.gov.vn:80/bangbieu/1113C_Michele_Debonneuil-_Phattrien_congnghe.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-13D56_Le_Quang_Thung-phatbieu.doc` | http://www.mpi.gov.vn:80/bangbieu/13D56_Le_Quang_Thung-phatbieu.doc | 2004-04-19 | mpi | public-domain-law | vni | pending-transcript | PII review not done |
| `2004-19Z9A_Luat_hop_tac_xasuadoi.doc` | http://www.mpi.gov.vn:80/bangbieu/19Z9A_Luat_hop_tac_xasuadoi.doc | 2004-01-06 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-1A79E_Phuluc_TT03-DKKD.doc` | http://www.mpi.gov.vn:80/Bangbieu/1A79E_Phuluc_TT03-DKKD.doc | 2006-09-02 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2005-1DCA4_3b.doc` | http://www.mpi.gov.vn:80/bangbieu/1DCA4_3b.doc | 2005-05-01 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-1E849_Tran_Du_Lich.doc` | http://www.mpi.gov.vn:80/bangbieu/1E849_Tran_Du_Lich.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-1ED4D_Francois_Godement-Thoikyquado.doc` | http://www.mpi.gov.vn:80/bangbieu/1ED4D_Francois_Godement-Thoikyquado.doc | 2004-04-19 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-1F7ZB_EtudeBinh_vn.doc` | http://www.mpi.gov.vn:80/Bangbieu/1F7ZB_EtudeBinh_vn.doc | 2004-11-28 | mpi | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-NghiDinh114_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh114_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-NghiDinh115_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh115_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-NghiDinh116_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh116_2003.doc | 2004-02-04 | mard | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-NghiDinh117_2003.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh117_2003.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-NghiDinh29_1998.doc` | http://www.mard.gov.vn:80/CCHC/ThiCCHC/NghiDinh29_1998.doc | 2004-02-05 | mard | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-93CP-1.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/93CP%5B1%5D.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-94CP-1.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/94CP%5B1%5D.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-Hamau1BK1995.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/Hamau1BK1995.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-HHamau3-1995.doc` | http://www.molisa.gov.vn/qppl/data/anhtl/HHamau3-1995.doc | 2006-10-03 | molisa | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-huong-dan-ghi-phieu.doc` | http://www.molisa.gov.vn:80/qppl/data/anhtl/huong%20dan%20ghi%20phieu.doc | 2006-07-21 | molisa | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-hoso.doc` | http://www.most.gov.vn:80/b_hoat_dong_khcn/d_thamdinh_danhgia/Folder.2004-07-07.5545/hoso | 2006-04-11 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B1-1-DONTC.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-1-DONTC | 2004-07-10 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B1-2-TMDA.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-2-TMDA | 2004-07-10 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B1-3-LLTC.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-3-LLTC | 2004-07-10 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-B1-4-LLCN.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/B1-4-LLCN | 2004-07-10 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-HDTMDT.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2003/HDTMDT | 2004-07-10 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-13-t-Phuluc3.doc` | http://www.most.gov.vn:80/b_vbpq/a_van_ban_phap_qui/b_vbpq_bkhcn/a_nam_2004/13-t-Phuluc3.doc | 2004-06-23 | most | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2006-Technical-Financial-File-V.doc` | http://www.cantho.gov.vn:80/files/Technical%20Financial%20File-V.doc | 2006-01-13 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2005-QD-256.doc` | http://www.cantho.gov.vn:80/files/van%20ban%20%20cua%20tpct/QD%20256.doc | 2005-11-06 | cantho | public-domain-law | vni | pending-transcript | PII review not done |
| `2009-ATT7QC6I.doc` | http://www.cantho.gov.vn:80/vbpq/Files/ATT7QC6I.doc | 2009-12-29 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2007-ATTDCL1A.doc` | http://www.cantho.gov.vn:80/vbpq/Files/ATTDCL1A.doc | 2007-04-10 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-ATTDDROE.doc` | http://www.cantho.gov.vn:80/vbpq/Files/ATTDDROE.doc | 2009-12-30 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-ATTXHSH5.doc` | http://www.cantho.gov.vn:80/vbpq/Files/ATTXHSH5.doc | 2009-12-30 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-Ban-hanh-Quy-che-dau-gia-quyen-su-dung-dat-CV-25.doc` | http://www.cantho.gov.vn:80/vbpq/Files/Ban%20hanh%20Quy%20che%20dau%20gia%20quyen%20su%20dung%20dat%20CV%2025.doc | 2009-03-06 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-Chi-thi-trien-khai-thi-hanh-Luat-Dat-dai.doc` | http://www.cantho.gov.vn:80/vbpq/Files/Chi%20thi%20trien%20khai%20thi%20hanh%20Luat%20Dat%20dai%20.doc | 2009-12-30 | cantho | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-CB15307-QD-7346CB.doc` | http://danang.gov.vn:80/congbao/uploads/CB15307-QD%207346CB.doc | 2009-02-19 | danang | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-CB21315-QD-44.doc` | http://danang.gov.vn:80/congbao/uploads/CB21315-QD%2044.doc | 2009-02-19 | danang | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-CB24353-NQ68.doc` | http://danang.gov.vn:80/congbao/uploads/CB24353-NQ68.doc | 2009-02-19 | danang | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2004-TT1691998.doc` | http://www.binhduong.gov.vn:80/cucthue/Chinhsach/Noidung_chinhsach/Khong%20theo%20luat%20dtu/TT1691998.doc | 2004-06-20 | binhduong | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2003-TT132001.doc` | http://www.binhduong.gov.vn:80/cucthue/Chinhsach/Noidung_chinhsach/Luat%20dau%20tu/TT132001.doc | 2003-11-25 | binhduong | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2003-Thong-tu-116.doc` | http://www.binhduong.gov.vn:80/cucthue/Chinhsach/Noidung_chinhsach/Thue%20GTGT/Thong%20tu%20116.doc | 2003-11-25 | binhduong | public-domain-law | vni | pending-transcript | PII review not done |
| `2009-20081117.772.doc` | http://www.dongnai.gov.vn:80/cong-dan/Administrative%20Procedure/20081113.749/20081117.018/20081117.772 | 2009-04-04 | dongnai | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-20081202.073.doc` | http://www.dongnai.gov.vn:80/cong-dan/Administrative%20Procedure/20081113.749/20081202.175/20081202.073 | 2009-04-04 | dongnai | public-domain-law | tcvn3 | pending-transcript | PII review not done |
| `2009-download.doc` | http://www.dongnai.gov.vn:80/cong-dan/Administrative%20Procedure/20081113.749/20081202.354/20081202.166/download | 2009-03-27 | dongnai | public-domain-law | vni | pending-transcript | PII review not done |
