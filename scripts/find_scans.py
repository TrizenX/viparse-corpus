#!/usr/bin/env python3
"""Screen candidate PDFs for the one property that matters here: no text layer.

The OCR benchmark measures rendered transcripts, and says four times over that a rendered
page is not a scan. Closing that gap needs real scans — and "looks scanned" is not a
property a search engine can filter on, so candidates have to be fetched and examined.

The test is deliberately narrow. A PDF is a **scan** when its pages carry images and
essentially no extractable text; it is **digital** the moment a text layer appears. A
document that is mostly text with a signature image is not a scan and is rejected, because
OCR would never be the right way to read it.

Borderline results are reported as ``mixed`` rather than forced either way: some archives
publish a digital first page in front of scanned content, and quietly counting those as
scans would put documents in the corpus that OCR is not actually being tested on.

    python3 scripts/find_scans.py --urls candidates.txt --out scans/
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

#: Extractable characters per page below which a page counts as having no text layer.
#: Not zero: a scanned page often carries a stray header, a page number stamped by the
#: scanning software, or an OCR layer covering the letterhead alone.
_TEXT_PER_PAGE_FLOOR = 40

#: A scan is images. A digital PDF with a logo has one image on the first page and none
#: after, so the test is the *fraction* of pages carrying one.
_IMAGE_PAGE_RATIO = 0.6

_UA = "Mozilla/5.0 (compatible; viparse-corpus/1.0; +https://github.com/TrizenX/viparse-corpus)"


@dataclass(frozen=True, slots=True)
class Verdict:
    url: str
    kind: str  # scan | digital | mixed | unreadable | unfetched
    pages: int = 0
    chars_per_page: float = 0.0
    image_pages: float = 0.0
    detail: str = ""


def fetch(url: str, destination: Path) -> bool:
    """Download ``url``. Returns False on any failure rather than raising.

    A candidate list is mostly dead links; one 404 must not end the sweep.
    """
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "180", "-A", _UA, "-o", str(destination), url],
            capture_output=True,
            timeout=240,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0 and destination.exists() and destination.stat().st_size > 1024


def classify(path: Path) -> Verdict:
    """Decide whether a downloaded file is a scanned PDF."""
    import pdfplumber

    if path.read_bytes()[:5] != b"%PDF-":
        # Portals routinely answer a .pdf URL with an HTML interstitial.
        return Verdict("", "unreadable", detail="not a PDF (probably an HTML page)")

    try:
        with pdfplumber.open(str(path)) as pdf:
            pages = len(pdf.pages)
            if not pages:
                return Verdict("", "unreadable", detail="no pages")
            sample = pdf.pages[: min(pages, 12)]
            chars = sum(len((page.extract_text() or "").strip()) for page in sample)
            with_images = sum(1 for page in sample if page.images)
            per_page = chars / len(sample)
            image_ratio = with_images / len(sample)
    except Exception as exc:  # noqa: BLE001 - any parse failure is just a rejection
        return Verdict("", "unreadable", detail=f"{type(exc).__name__}: {exc}")

    if per_page < _TEXT_PER_PAGE_FLOOR and image_ratio >= _IMAGE_PAGE_RATIO:
        kind = "scan"
    elif per_page >= _TEXT_PER_PAGE_FLOOR and image_ratio < _IMAGE_PAGE_RATIO:
        kind = "digital"
    else:
        kind = "mixed"
    return Verdict("", kind, pages, round(per_page, 1), round(image_ratio, 2))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls", type=Path, required=True, help="one candidate URL per line")
    ap.add_argument("--out", type=Path, required=True, help="where scans are kept")
    args = ap.parse_args()

    urls = [
        line.strip()
        for line in args.urls.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not urls:
        print("no candidate URLs", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    staging = args.out / ".staging"
    staging.mkdir(exist_ok=True)

    counts: dict[str, int] = {}
    for url in urls:
        temporary = staging / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".pdf")
        if not fetch(url, temporary):
            verdict = Verdict(url, "unfetched")
        else:
            verdict = dataclasses.replace(classify(temporary), url=url)
        counts[verdict.kind] = counts.get(verdict.kind, 0) + 1

        if verdict.kind == "scan":
            kept = args.out / (url.rsplit("/", 1)[-1].split("?")[0] or "scan.pdf")
            temporary.replace(kept)
            print(
                f"  SCAN     {kept.name}  {verdict.pages}p  "
                f"{verdict.chars_per_page} chars/page  {verdict.image_pages:.0%} image pages"
            )
        else:
            temporary.unlink(missing_ok=True)
            print(f"  {verdict.kind:9} {url[:90]}  {verdict.detail}")

    print("\n  " + ", ".join(f"{kind}={n}" for kind, n in sorted(counts.items())))
    if not counts.get("scan"):
        # Said out loud: a sweep that finds nothing looks identical to a sweep that never
        # ran, and this project has already been bitten by exactly that.
        print("  no scans found in this batch — the candidate list needs different sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
