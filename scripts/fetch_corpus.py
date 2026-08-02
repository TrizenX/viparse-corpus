#!/usr/bin/env python3
"""Download screened documents into the corpus and write their provenance rows.

Collection and transcription are deliberately separate steps. This does the part a
machine can do — fetch, classify, record where each file came from — and marks every
row `pending-transcript`, because the part a machine cannot do is produce a correct
Unicode reading of the text.

    python3 scripts/fetch_corpus.py --domains mof.gov.vn sbv.gov.vn --limit 20
    python3 scripts/fetch_corpus.py --domains-file domains.txt --dry-run

Each row is appended to PROVENANCE.md **as its file lands**, not in one write at the
end. An interrupted run must not leave documents on disk with no record of where they
came from — that is precisely the state `validate_provenance.py` exists to catch, and
a collector that creates it is worse than useless.

Files already listed are skipped, so the script can be re-run to top the corpus up or
to resume after an interruption.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from find_candidates import (  # noqa: E402
    KINDS,
    WAYBACK,
    classify,
    declared_fonts,
    fetch,
    list_archived,
)

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "PROVENANCE.md"
CORPUS = ROOT / "corpus" / "public-domain"

SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(url: str, timestamp: str, kind: str = "doc") -> str:
    """A filename that survives every filesystem and reads the same everywhere.

    Archived URLs are percent-encoded and often carry spaces and Vietnamese
    diacritics; leaving those in makes the corpus awkward to work with and the
    provenance table hard to read.

    The extension comes from the screened kind. Some sources serve documents through a script
    (`download.php?file=...`) or with a numeric suffix, and naming a Word document
    `.772` or `.download` misleads every tool that looks at it. The mimetype filter
    upstream already established what these are.
    """
    parsed = urllib.parse.urlparse(url)
    # A download script hides the real name in the query string.
    query = urllib.parse.parse_qs(parsed.query)
    candidate = ""
    for key in ("file", "filename", "name"):
        if query.get(key):
            candidate = query[key][0]
            break
    if not candidate:
        candidate = parsed.path.rsplit("/", 1)[-1]

    raw = urllib.parse.unquote(candidate)
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    # Strip whatever extension the source used, in any case — the kind decides the one
    # that goes back on. Matching only `.doc` produced `2003-A06.rtf.rtf` the first time
    # this ran over a format other than Word; a hand-written list of the others then
    # produced `...ppt.ppt` the first time it ran over PowerPoint. Built from KINDS so
    # the next format cannot repeat it.
    known = "|".join(sorted({k[1].lstrip(".") for k in KINDS.values()} | {"docx", "xlsx", "pptx"}))
    raw = re.sub(rf"\.({known})$", "", raw, flags=re.IGNORECASE)
    stem = SAFE.sub("-", raw).strip("-")[:48] or KINDS[kind][1].lstrip(".")
    name = f"{timestamp[:4]}-{stem}{KINDS[kind][1]}"
    # Transcripts are keyed on the *stem*, so two formats sharing a source name would
    # share a ground-truth file. `download.doc` and `download.xls` from different
    # ministries in the same year did exactly that — the .xls was matched against the
    # .doc's transcript and the validator caught it.
    if any(
        (CORPUS / family / f"{timestamp[:4]}-{stem}{other[1]}").exists()
        for other in KINDS.values()
        if other[1] != KINDS[kind][1]
        for family in ("tcvn3", "vni", "viscii", "vps")
    ):
        name = f"{timestamp[:4]}-{stem}-{KINDS[kind][1].lstrip('.')}{KINDS[kind][1]}"
    return name


def existing_rows() -> set[str]:
    if not PROVENANCE.exists():
        return set()
    text = PROVENANCE.read_text(encoding="utf-8")
    start = text.find("## Files")
    if start < 0:
        return set()
    names = set()
    for line in text[start:].splitlines():
        if line.strip().startswith("|"):
            first = line.strip().strip("|").split("|")[0].strip().strip("`")
            if first and first != "file" and not set(first) <= set("-: "):
                names.add(first)
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domains", nargs="*", default=[])
    ap.add_argument("--domains-file", type=Path)
    ap.add_argument("--from", dest="year_from", type=int, default=2000)
    ap.add_argument("--to", dest="year_to", type=int, default=2009)
    ap.add_argument("--limit", type=int, default=12, help="candidates screened per domain")
    ap.add_argument("--kind", choices=sorted(KINDS), default="doc")
    ap.add_argument(
        "--max-bytes",
        type=int,
        default=0,
        help="skip anything larger; 0 means no limit. A 1.3 MB statistics table is a "
        "real legacy document and useless as corpus material, because ground truth for "
        "it cannot be transcribed by hand.",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    domains = list(args.domains)
    if args.domains_file:
        domains += [
            ln.strip()
            for ln in args.domains_file.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
    if not domains:
        print("give --domains or --domains-file", file=sys.stderr)
        return 2

    already = existing_rows()
    counts: dict[str, int] = {}
    written = 0

    def record(row: str) -> None:
        """Append one row immediately, so disk and record never diverge."""
        text = PROVENANCE.read_text(encoding="utf-8").rstrip("\n")
        PROVENANCE.write_text(text + "\n" + row + "\n", encoding="utf-8")

    for domain in domains:
        candidates = list_archived(
            domain, args.year_from, args.year_to, args.limit, args.kind
        )
        print(f"  {domain}: screening {len(candidates)}", file=sys.stderr)

        for ts, url in candidates:
            try:
                data = fetch(WAYBACK.format(ts=ts, url=url), timeout=45)
            except Exception:
                continue

            if args.max_bytes and len(data) > args.max_bytes:
                continue

            encoding = classify(declared_fonts(data, args.kind), data, args.kind)
            if not encoding:
                continue

            name = safe_name(url, ts, args.kind)
            if name in already:
                continue
            already.add(name)
            counts[encoding] = counts.get(encoding, 0) + 1

            retrieved = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
            publisher = domain.split(".")[0]
            row = (
                f"| `{name}` | {url} | {retrieved} | {publisher} | public-domain-law "
                f"| {encoding} | pending-transcript | PII review not done |"
            )

            if not args.dry_run:
                # Record first, then write the file. If this is interrupted the worst
                # case is a row with no file, which the validator reports and a
                # re-run repairs — the reverse leaves an untraceable document.
                record(row)
                target = CORPUS / encoding
                target.mkdir(parents=True, exist_ok=True)
                (target / name).write_bytes(data)

            written += 1
            print(f"    {encoding:6} {name}", file=sys.stderr)

    if not written:
        print("\n  nothing new", file=sys.stderr)
        return 0

    total = sum(counts.values())
    breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"\n  {total} new document(s): {breakdown}", file=sys.stderr)
    print("  Every row is `pending-transcript` with PII review outstanding.", file=sys.stderr)
    print("  Neither is optional before a document is marked `ready`.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
