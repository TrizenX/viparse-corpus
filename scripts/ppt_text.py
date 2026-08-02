#!/usr/bin/env python3
"""Text out of a PowerPoint 97 ``.ppt``, independently of viparse.

viparse reaches a legacy ``.ppt`` through LibreOffice and python-pptx. Screening the
corpus with that same path would mean the benchmark is a collection of exactly the files
the library already handles — the reason ``doc_text.py`` exists for Word, and the
standard the PDF and RTF stages could not meet.

A ``.ppt`` is an OLE2 container whose ``PowerPoint Document`` stream is a flat sequence
of records: an 8-byte header (version/instance, type, length) then the payload. Text
lives in two of them, and the distinction is the whole point here:

* ``TextCharsAtom`` (0x0FA0) — UTF-16LE, already Unicode.
* ``TextBytesAtom`` (0x0FA8) — one byte per character, which is where a legacy encoding
  survives. A slide typed in ``.VnTime`` is stored here.

Container records — those whose low nibble of the first field is 0xF — hold other
records rather than data, so the walk descends into them instead of skipping their
length. Missing that reads the file as a single opaque blob and finds nothing.

.. warning::
   **Not yet correct enough for ground truth.** PowerPoint keeps slide text in more than
   one place, and this reader still returns some of it twice: on the one legacy ``.ppt``
   collected it produces 97,359 characters where a parser produces 85,410, with 578
   duplicated lines. The text it returns is right; there is too much of it.

   Reading only ``TextBytesAtom`` inside ``SlideListWithText`` removed most of the
   duplication but not all — the index appears to carry a second copy for some shapes.
   Until that is understood the document it was built for stays ``pending-transcript``,
   because a transcript that repeats lines charges the repetition to whatever is
   measured against it.

   The record walk is also not fully trustworthy: scanning the stream for
   ``TextCharsAtom`` matched 760 records, most of them arbitrary bytes rather than text.
   ``TextBytesAtom`` — the one that matters for a legacy file — is clean.

    python3 scripts/ppt_text.py file.ppt
"""

from __future__ import annotations

import struct
import sys

_TEXT_CHARS_ATOM = 0x0FA0
_TEXT_BYTES_ATOM = 0x0FA8

# PowerPoint stores slide text *twice*: once per shape, inside the drawing records, and
# once flattened into a document-level index. Reading the stream for text atoms without
# caring where they sit therefore returns every line two or four times — measured on the
# one legacy .ppt collected, 1021 of 1023 long lines were duplicates, and the transcript
# came out at exactly twice the length of any parser's output.
#
# The index is the complete copy — 124 atoms against the drawing records' 16 in that
# file, because a shape whose text lives in the outline stores only a reference. So the
# walk reads the index and nothing else.
_SLIDE_LIST_WITH_TEXT = 0x0FF0
_HEADER = struct.Struct("<HHI")

# PowerPoint writes CR for a paragraph break and 0x0B for a soft line break.
_BREAKS = str.maketrans({"\r": "\n", "\x0b": "\n"})


def _records(data: bytes, start: int, end: int, *, inside_index: bool):
    """Yield ``(type, payload)`` for text atoms in the slide-text index only."""
    position = start
    while position + _HEADER.size <= end:
        version_instance, record_type, length = _HEADER.unpack_from(data, position)
        body = position + _HEADER.size
        if length > end - body:
            return
        if version_instance & 0x0F == 0x0F:
            yield from _records(
                data,
                body,
                body + length,
                inside_index=inside_index or record_type == _SLIDE_LIST_WITH_TEXT,
            )
        elif inside_index:
            yield record_type, data[body : body + length]
        position = body + length


def extract(path: str) -> str:
    """Slide text in stream order, legacy bytes preserved as Latin-1 characters."""
    try:
        import olefile
    except ImportError:  # pragma: no cover - screening dependency
        print("olefile is required: pip install olefile", file=sys.stderr)
        raise SystemExit(2) from None

    with olefile.OleFileIO(path) as ole:
        if not ole.exists("PowerPoint Document"):
            return ""
        stream = ole.openstream("PowerPoint Document").read()

    parts: list[str] = []
    for record_type, payload in _records(stream, 0, len(stream), inside_index=False):
        if record_type == _TEXT_BYTES_ATOM:
            # One byte per character. Decoding as Latin-1 keeps every byte intact, which
            # is what a legacy table needs to read afterwards — decoding as anything
            # else would resolve the very bytes the corpus exists to preserve.
            parts.append(payload.decode("latin-1"))
        elif record_type == _TEXT_CHARS_ATOM:
            parts.append(payload.decode("utf-16-le", errors="replace"))
    return "\n".join(parts).translate(_BREAKS)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    print(extract(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
