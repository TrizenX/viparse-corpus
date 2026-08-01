#!/usr/bin/env python3
"""Extract the text of a Word 97 .doc, independently of viparse.

Independence is the point. Ground truth generated with the library under test would
make the benchmark circular — viparse would score 100% against its own output and the
number would mean nothing. So this reads the binary format directly and knows nothing
about viparse.

Word 97 stores text in pieces described by a piece table in the Table stream. Each
piece is either UTF-16 or 8-bit cp1252, flagged per piece. Reading the whole span as
one encoding silently drops characters — "đăng ký" comes back as "ng ký" — which is
the failure this file exists to avoid.

    python3 scripts/doc_text.py file.doc
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import olefile


def extract(path: str | Path) -> str:
    ole = olefile.OleFileIO(str(path))
    wd = ole.openstream("WordDocument").read()

    # FIB flags: bit 9 of the field at 0x0A selects which table stream is live.
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    table_name = "1Table" if (flags & 0x0200) else "0Table"
    if not ole.exists(table_name):
        table_name = "0Table" if table_name == "1Table" else "1Table"
    table = ole.openstream(table_name).read()

    fc_clx, lcb_clx = struct.unpack_from("<II", wd, 0x01A2)
    clx = table[fc_clx : fc_clx + lcb_clx]

    # The CLX is a run of property blobs (0x01) followed by the piece table (0x02).
    pos = 0
    piece_table = b""
    while pos < len(clx):
        kind = clx[pos]
        if kind == 0x01:
            size = struct.unpack_from("<H", clx, pos + 1)[0]
            pos += 3 + size
        elif kind == 0x02:
            size = struct.unpack_from("<I", clx, pos + 1)[0]
            piece_table = clx[pos + 5 : pos + 5 + size]
            break
        else:
            break

    if not piece_table:
        raise ValueError("no piece table")

    # n+1 character positions, then n 8-byte descriptors.
    n = (len(piece_table) - 4) // 12
    cps = list(struct.unpack_from(f"<{n + 1}I", piece_table, 0))

    out: list[str] = []
    for i in range(n):
        pcd = 4 * (n + 1) + 8 * i
        fc = struct.unpack_from("<I", piece_table, pcd + 2)[0]
        # Bit 30 set means the piece is 8-bit cp1252 and fc must be halved.
        compressed = bool(fc & 0x40000000)
        offset = (fc & 0x3FFFFFFF) // 2 if compressed else (fc & 0x3FFFFFFF)
        length = cps[i + 1] - cps[i]

        if compressed:
            chunk = wd[offset : offset + length]
            out.append(chunk.decode("cp1252", errors="replace"))
        else:
            chunk = wd[offset : offset + length * 2]
            out.append(chunk.decode("utf-16-le", errors="replace"))

    text = "".join(out)
    # Word's in-band control characters: field marks, cell/row ends, page breaks.
    for ch, repl in (
        ("\r", "\n"), ("\x07", "\n"), ("\x0b", "\n"), ("\x0c", "\n"),
        ("\x13", ""), ("\x14", ""), ("\x15", ""), ("\x01", ""), ("\x02", ""),
        ("\x08", ""), ("\x1e", "-"), ("\xa0", " "),
    ):
        text = text.replace(ch, repl)
    return text


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    print(extract(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
