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
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

#: Extractable characters per page below which a page counts as having no text layer.
#: Not zero: a scanned page often carries a stray header, a page number stamped by the
#: scanning software, or an OCR layer covering the letterhead alone.
_TEXT_PER_PAGE_FLOOR = 40

#: A scan is images. A digital PDF with a logo has one image on the first page and none
#: after, so the test is the *fraction* of pages carrying one.
_IMAGE_PAGE_RATIO = 0.6

#: Pages examined before deciding. Opening every page of a 300-page PDF to answer "is
#: this a scan" is wasteful, but a sample is a cap and a cap that is not reported reads as
#: a whole-document verdict. When it applies, the verdict says so.
_SAMPLE_PAGES = 12

_UA = "Mozilla/5.0 (compatible; viparse-corpus/1.0; +https://github.com/TrizenX/viparse-corpus)"


@dataclass(frozen=True, slots=True)
class Verdict:
    url: str
    kind: str  # scan | digital | mixed | unreadable | unfetched | throttled
    pages: int = 0
    chars_per_page: float = 0.0
    image_pages: float = 0.0
    detail: str = ""


def fetch(url: str, destination: Path, attempts: int = 3) -> str:
    """Download ``url``, retrying. Returns ``"ok"``, ``"throttled"`` or ``"unfetched"``.

    The three-way answer is the point. A candidate list is mostly dead links, and one 404
    must not end a sweep — but the Wayback Machine answers a burst with **HTTP 429**, and
    a throttled request is indistinguishable from a missing document unless someone looks
    at the status code.

    That distinction is not pedantry. `find_candidates.py` carries the scar in its own
    docstring: a wall of throttled requests once read as "the archive holds nothing" for a
    domain whose documents were there all along. Collapsing 429 into "unfetched" here
    would reproduce it in a script whose entire output is a count.

    The size floor stays as a second guard: a throttle page is a couple of hundred bytes
    of HTML, and parsing one as a PDF is how a sweep invents results.
    """
    last = "unfetched"
    for attempt in range(attempts):
        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "180", "-A", _UA,
                 "-w", "%{http_code}", "-o", str(destination), url],
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
            status = (result.stdout or "").strip()[-3:]
            if result.returncode == 0 and status == "200":
                if destination.exists() and destination.stat().st_size > 1024:
                    return "ok"
            elif status == "429":
                last = "throttled"
        except subprocess.TimeoutExpired:
            pass
        if attempt < attempts - 1:
            time.sleep(2 * (attempt + 1))
    return last


def screen(url: str, staging: Path) -> tuple[str, Verdict, Path | None]:
    """Fetch and classify one URL, in that order, in one place.

    Deliberately one function rather than a download phase followed by a scan of the
    download directory. The ad-hoc version of this was two phases with a
    ``glob("*.pdf")`` between them, which silently skipped every file saved as ``.PDF`` —
    seven of fourteen in one batch. A pipeline with no intermediate listing cannot lose
    files to a pattern.
    """
    temporary = staging / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".pdf")
    status = fetch(url, temporary)
    if status != "ok":
        temporary.unlink(missing_ok=True)
        return url, Verdict(url, status), None
    verdict = dataclasses.replace(classify(temporary), url=url)
    if verdict.kind == "scan":
        return url, verdict, temporary
    temporary.unlink(missing_ok=True)
    return url, verdict, None


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
            sample = pdf.pages[:_SAMPLE_PAGES]
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
    sampled = "" if pages <= _SAMPLE_PAGES else f"decided on the first {_SAMPLE_PAGES} of {pages} pages"
    return Verdict("", kind, pages, round(per_page, 1), round(image_ratio, 2), sampled)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls", type=Path, required=True, help="one candidate URL per line")
    ap.add_argument("--out", type=Path, required=True, help="where scans are kept")
    ap.add_argument(
        "--workers",
        type=int,
        default=6,
        help=(
            "parallel fetches (default 6). Raising this does not go faster past a point — "
            "the archive throttles, and a throttled request looks exactly like a missing "
            "document. Twelve workers over 700 URLs returned 69 files."
        ),
    )
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
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for url, verdict, kept_path in pool.map(lambda u: screen(u, staging), urls):
            counts[verdict.kind] = counts.get(verdict.kind, 0) + 1
            if kept_path is not None:
                name = url.rsplit("/", 1)[-1].split("?")[0] or "scan.pdf"
                if not name.lower().endswith(".pdf"):
                    # Archive URLs routinely end in a UUID with no extension. Named here
                    # rather than left to a later directory walk to guess at.
                    name += ".pdf"
                kept = args.out / name
                kept_path.replace(kept)
                note = f"  [{verdict.detail}]" if verdict.detail else ""
                print(
                    f"  SCAN     {kept.name}  {verdict.pages}p  "
                    f"{verdict.chars_per_page} chars/page  {verdict.image_pages:.0%} image pages{note}"
                )
            else:
                print(f"  {verdict.kind:9} {url[:90]}  {verdict.detail}")

    print("\n  " + ", ".join(f"{kind}={n}" for kind, n in sorted(counts.items())))
    throttled = counts.get("throttled", 0)
    unfetched = counts.get("unfetched", 0)
    if throttled:
        # The strongest statement this script can make, and it must outrank the counts
        # above it: a throttled sweep has not measured anything.
        print(
            f"\n  THROTTLED: the archive returned HTTP 429 for {throttled} of {len(urls)} "
            f"URL(s) ({throttled / len(urls):.0%}).\n"
            "  This run did not screen them. The counts above are not evidence about what\n"
            "  the archive holds — wait, lower --workers, and run it again."
        )
    if unfetched:
        share = unfetched / len(urls)
        print(
            f"  {unfetched} of {len(urls)} ({share:.0%}) never downloaded after retries — "
            "dead links, or transport failures. These were not screened either."
        )
    if not counts.get("scan") and not throttled and not unfetched:
        # Only claimed when every candidate was actually examined. A sweep that finds
        # nothing looks identical to a sweep that never ran, and this project has already
        # been bitten by exactly that.
        print("  no scans found in this batch — the candidate list needs different sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
