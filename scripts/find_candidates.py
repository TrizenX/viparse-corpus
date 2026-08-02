#!/usr/bin/env python3
"""Find legacy-encoded Vietnamese .doc files in the Wayback Machine.

Live government portals have been rebuilt and their documents re-published as
Unicode, so they are useless as corpus material. The legacy encodings survive in
archived copies of those sites from before the migration.

Screening is in two stages, and **both are needed**.

A font declaration alone is not proof. `.VnTime` survives conversion: a document
whose text was migrated to Unicode often keeps the legacy font in its table, and
screening on that signal alone gave a 44% false-positive rate over 62 files — 27
of them were already Unicode.

So the font table narrows the candidates, and the **text itself decides**. A file
counts as legacy only when its extracted characters are Latin-1 byte values rather
than Vietnamese Unicode.

    python3 scripts/find_candidates.py --domain mof.gov.vn --from 2001 --to 2008
    python3 scripts/find_candidates.py --domain mof.gov.vn --download out/

Requires `olefile` (`pip install olefile`).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_text import extract  # noqa: E402

CDX = "http://web.archive.org/cdx/search/cdx"
WAYBACK = "http://web.archive.org/web/{ts}id_/{url}"

# Families that exist only in the pre-Unicode Vietnamese world. A document
# declaring one of these is legacy-encoded; nothing else needs to be inferred.
LEGACY_FONT = re.compile(r"\.Vn[A-Za-z]+|VNI-[A-Za-z]+|VPS[A-Za-z]+|ABC[A-Za-z]*")

ENCODING_OF = {".vn": "tcvn3", "vni": "vni", "vps": "vps", "abc": "tcvn3"}


def fetch(url: str, timeout: int = 60, attempts: int = 3) -> bytes:
    """Fetch with backoff. The Wayback Machine rate-limits, and a burst of
    parallel requests comes back as a wall of failures that looks like the
    archive holding nothing — it measured 0 hits from a domain whose documents
    were there all along."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "viparse-corpus/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 — any transport failure is retryable here
            last = e
            if attempt < attempts - 1:
                time.sleep(2 * (attempt + 1))
    raise last if last else RuntimeError("fetch failed")


# Formats worth screening, and the archive mimetype that finds them. `.doc` was the
# whole corpus for a long time, which hid a class of bug: `.doc` reaches viparse's DOCX
# engine through LibreOffice, so that one path was well covered and PDF, RTF and XLS had
# no real-document coverage at all. The first PDF screened turned up a defect.
KINDS = {
    "doc": ("application/msword", ".doc"),
    "pdf": ("application/pdf", ".pdf"),
    "rtf": ("application/rtf", ".rtf"),
    "xls": ("application/vnd.ms-excel", ".xls"),
}

# Legacy Vietnamese font families, as they appear in each container. `.doc` and `.xls`
# hide them in OLE2 streams; a PDF names them in /BaseFont, often behind a six-letter
# subset tag; RTF spells them out in the font table. One pattern covers all four because
# the names are the same names.
_FONT_BYTES = re.compile(
    rb"\.Vn[A-Za-z]+|VNI-[A-Za-z]+|VPS[A-Za-z]+|ABC[A-Za-z]*|VNS[A-Za-z0-9]+"
)


def list_archived(
    domain: str, year_from: int, year_to: int, limit: int, kind: str = "doc"
) -> list[tuple[str, str]]:
    params = urllib.parse.urlencode(
        {
            "url": domain,
            "matchType": "domain",
            "filter": f"mimetype:{KINDS[kind][0]}",
            "from": year_from,
            "to": year_to,
            "limit": limit,
            "collapse": "urlkey",
            "fl": "timestamp,original",
            "output": "text",
        }
    )
    try:
        body = fetch(f"{CDX}?{params}").decode("utf-8", errors="replace")
    except Exception as e:
        print(f"CDX query failed: {e}", file=sys.stderr)
        return []
    rows = []
    for line in body.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def declared_fonts(data: bytes, kind: str) -> set[str]:
    """Legacy font names the container declares, whatever the container is.

    OLE2 (`.doc`, `.xls`) needs the streams walked; PDF and RTF are byte-scannable, and
    a plain scan is deliberate — a PDF font name sits in `/BaseFont`, sometimes as
    `ABCDEF+.VnTime`, and RTF writes its font table as text. Neither needs parsing to be
    *narrowed*, and narrowing is all the font stage is for. The text decides.
    """
    if kind in ("doc", "xls"):
        return legacy_fonts(data)
    return {match.decode("latin-1") for match in _FONT_BYTES.findall(data)}


def legacy_fonts(data: bytes) -> set[str]:
    """Font names declared anywhere in the OLE2 container."""
    try:
        import olefile
    except ImportError:
        print("olefile is required: pip install olefile", file=sys.stderr)
        raise SystemExit(2)

    import io

    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
    except Exception:
        return set()

    found: set[str] = set()
    for entry in ole.listdir():
        try:
            raw = ole.openstream(entry).read()
        except Exception:
            continue
        # Font names appear UTF-16LE in the table stream and Latin-1 elsewhere
        # depending on the writer; check both rather than assume.
        for dec in ("utf-16-le", "latin-1"):
            found |= set(LEGACY_FONT.findall(raw.decode(dec, errors="ignore")))
    return found


# Vietnamese letters that exist only in Unicode; they cannot appear in a legacy
# byte stream, so seeing them means the text was already converted.
UNICODE_VN = set("ăâđêôơưĂÂĐÊÔƠƯ") | {chr(c) for c in range(0x1EA0, 0x1EFA)}
# Latin-1 range where the legacy encodings park their Vietnamese letters.
LEGACY_BYTES = {chr(c) for c in range(0xA1, 0x100)}


def text_is_legacy(data: bytes) -> bool | None:
    """Decide from the text, not the font table. None when there is too little to tell."""
    import io
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".doc", delete=True) as tmp:
            tmp.write(data)
            tmp.flush()
            text = extract(tmp.name)
    except Exception:
        return None

    unicode_hits = sum(1 for c in text if c in UNICODE_VN)
    legacy_hits = sum(1 for c in text if c in LEGACY_BYTES)
    if unicode_hits == 0 and legacy_hits < 20:
        return None
    return legacy_hits > unicode_hits


# VNI keeps the ASCII vowel and appends a tone character (``laäp`` → lập); TCVN3
# replaces the vowel outright with a single high byte (``lËp`` → lập). So the share of
# high bytes that sit immediately after an ASCII vowel separates them: measured across
# the corpus, TCVN3 documents land at 0.14–0.18 and VNI at 0.56.
_VOWELS = set("aeiouyAEIOUY")
_VNI_THRESHOLD = 0.35


def text_family(text: str) -> str | None:
    """Which legacy encoding the *text* is in, or None when there is too little to tell."""
    high = after_vowel = 0
    for i, ch in enumerate(text):
        if 0xA0 < ord(ch) < 0x100:
            high += 1
            if i and text[i - 1] in _VOWELS:
                after_vowel += 1
    if high < 50:
        return None
    return "vni" if after_vowel / high > _VNI_THRESHOLD else "tcvn3"


def container_text(data: bytes, kind: str) -> str | None:
    """The document's text, extracted the way that container needs.

    ``.doc`` uses this repo's own piece-table reader, written independently of viparse so
    the corpus is not screened by the library under test. PDF and RTF use pdfplumber and
    striprtf, the same libraries viparse uses — writing a second PDF text extractor to
    avoid that would be a project, not a precaution, and the independence that matters is
    of the *conversion table* and the *ground truth*, both of which stay separate. Every
    transcript is still read before it is marked `ready`.
    """
    import tempfile

    suffix = KINDS[kind][1]
    try:
        if kind == "doc":
            with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                tmp.write(data)
                tmp.flush()
                return extract(tmp.name)
        if kind == "rtf":
            from striprtf.striprtf import rtf_to_text

            return rtf_to_text(data.decode("latin-1", errors="replace"), errors="ignore")
        if kind == "pdf":
            import pdfplumber

            with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                tmp.write(data)
                tmp.flush()
                with pdfplumber.open(tmp.name) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return None
    # `.xls` has no text stage here. A font-only screen was measured at a 44% false
    # positive rate on `.doc`, so shipping one for `.xls` would put known-bad candidates
    # in the corpus. Screening it needs a reader this repo does not have yet.
    return None


def classify(fonts: set[str], data: bytes | None = None, kind: str = "doc") -> str | None:
    """Legacy encoding name, or None.

    The font table narrows the candidates and the text decides. Font alone is not
    enough twice over: a declaration survives conversion to Unicode, and a document
    that declares *both* ``.VnTime`` and ``VNI-Times`` — many do — would otherwise be
    classified by whichever name a set iteration happened to yield first. Two documents
    were filed as VNI that way and are TCVN3.
    """
    families = {ENCODING_OF[f[:3].lower()] for f in fonts if f[:3].lower() in ENCODING_OF}
    if not families:
        return None
    if data is None:
        return sorted(families)[0]

    text = container_text(data, kind)
    if text is None:
        return None

    # The byte-level legacy test reads the raw container, which only means anything when
    # the text sits in it as bytes. A PDF stores glyph codes and an RTF escapes its high
    # bytes, so for those the extracted text is the only evidence there is.
    if kind == "doc" and text_is_legacy(data) is not True:
        return None
    from_text = text_family(text)
    if from_text is None:
        return None

    # The positional heuristic is a fast filter, not a verdict — it filed a Lâm Đồng
    # TCVN3 document as VNI. Confirm by converting with both tables and keeping the one
    # that leaves fewer characters unconverted: a table applied to the wrong encoding
    # cannot consume its bytes, so the residue counts separate them decisively (9
    # against 42 on that document).
    try:
        import tcvn3 as tcvn3_table
        import vni as vni_table
    except ImportError:
        return from_text

    residue = {
        "tcvn3": len(tcvn3_table.unmapped(text)),
        "vni": len(vni_table.unmapped(text)),
    }
    best = min(residue, key=lambda k: residue[k])
    return best if residue[best] != residue["tcvn3" if best == "vni" else "vni"] else from_text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", required=True, help="e.g. mof.gov.vn")
    ap.add_argument("--kind", choices=sorted(KINDS), default="doc")
    ap.add_argument("--from", dest="year_from", type=int, default=2000)
    ap.add_argument("--to", dest="year_to", type=int, default=2009)
    ap.add_argument("--limit", type=int, default=50, help="candidates to screen")
    ap.add_argument("--download", type=Path, help="save confirmed hits here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = list_archived(args.domain, args.year_from, args.year_to, args.limit, args.kind)
    if not rows:
        print(
            f"no archived {KINDS[args.kind][1]} files found for that domain and range",
            file=sys.stderr,
        )
        return 1

    print(f"screening {len(rows)} candidate(s) from {args.domain} "
          f"({args.year_from}–{args.year_to})\n", file=sys.stderr)

    hits, checked, failed = [], 0, 0
    for ts, url in rows:
        try:
            data = fetch(WAYBACK.format(ts=ts, url=url), timeout=45)
        except Exception:
            failed += 1
            continue
        checked += 1
        time.sleep(0.5)  # stay under the archive's rate limit

        fonts = declared_fonts(data, args.kind)
        encoding = classify(fonts, data, args.kind)
        if not encoding:
            continue

        name = url.rsplit("/", 1)[-1].split("?")[0] or f"{ts}{KINDS[args.kind][1]}"
        hit = {
            "file": name,
            "source": url,
            "wayback": WAYBACK.format(ts=ts, url=url),
            "retrieved": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
            "encoding": encoding,
            "fonts": sorted(fonts)[:6],
            "bytes": len(data),
        }
        hits.append(hit)
        if not args.json:
            print(f"  {encoding:6} {name:32} {', '.join(sorted(fonts)[:3])}")

        if args.download:
            args.download.mkdir(parents=True, exist_ok=True)
            (args.download / name).write_bytes(data)

    rate = f"{len(hits)}/{checked}" if checked else "0/0"
    if args.json:
        print(json.dumps({"domain": args.domain, "checked": checked,
                          "failed": failed, "hits": hits}, indent=2, ensure_ascii=False))
    else:
        print(f"\n  {rate} legacy-encoded ({failed} download failures)", file=sys.stderr)
        if hits:
            print("  Add each to PROVENANCE.md with basis `public-domain-law` "
                  "before committing it.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
