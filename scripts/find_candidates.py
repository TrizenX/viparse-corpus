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


def list_archived(domain: str, year_from: int, year_to: int, limit: int) -> list[tuple[str, str]]:
    params = urllib.parse.urlencode(
        {
            "url": domain,
            "matchType": "domain",
            "filter": "mimetype:application/msword",
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


def classify(fonts: set[str], data: bytes | None = None) -> str | None:
    """Legacy encoding name, or None.

    `fonts` says which legacy encoding the document was authored in; `data`, when
    given, says whether the text is still in it.
    """
    family = None
    for font in fonts:
        key = font[:3].lower()
        if key in ENCODING_OF:
            family = ENCODING_OF[key]
            break
    if family is None:
        return None
    if data is not None and text_is_legacy(data) is not True:
        return None
    return family


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", required=True, help="e.g. mof.gov.vn")
    ap.add_argument("--from", dest="year_from", type=int, default=2000)
    ap.add_argument("--to", dest="year_to", type=int, default=2009)
    ap.add_argument("--limit", type=int, default=50, help="candidates to screen")
    ap.add_argument("--download", type=Path, help="save confirmed hits here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = list_archived(args.domain, args.year_from, args.year_to, args.limit)
    if not rows:
        print("no archived .doc files found for that domain and range", file=sys.stderr)
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

        fonts = legacy_fonts(data)
        encoding = classify(fonts, data)
        if not encoding:
            continue

        name = url.rsplit("/", 1)[-1].split("?")[0] or f"{ts}.doc"
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
