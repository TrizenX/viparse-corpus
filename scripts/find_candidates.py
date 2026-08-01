#!/usr/bin/env python3
"""Find legacy-encoded Vietnamese .doc files in the Wayback Machine.

Live government portals have been rebuilt and their documents re-published as
Unicode, so they are useless as corpus material. The legacy encodings survive in
archived copies of those sites from before the migration.

Screening is by **font table**, not by guessing at the text. A Word 97 document
that declares `.VnTime` or `VNI-Times` is TCVN3/VNI by construction — the bytes
only render as Vietnamese with that font applied. Reading the text and looking
for suspicious characters would be a heuristic; this is a fact stated by the file.

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


def classify(fonts: set[str]) -> str | None:
    for font in fonts:
        key = font[:3].lower()
        if key in ENCODING_OF:
            return ENCODING_OF[key]
    return None


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
        encoding = classify(fonts)
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
