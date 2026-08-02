#!/usr/bin/env python3
"""Text out of a PowerPoint 97 ``.ppt``, independently of viparse.

viparse reaches a legacy ``.ppt`` through LibreOffice and python-pptx. Screening the
corpus with that same path would make the benchmark a collection of exactly the files
the library already handles — the reason ``doc_text.py`` exists for Word, and the
standard the PDF and RTF stages could not meet.

Following the pointer, not scanning the stream
----------------------------------------------
A ``.ppt`` is saved incrementally: each save appends a new ``Document`` container and
leaves the previous one in place. Scanning the ``PowerPoint Document`` stream for text
therefore returns **every revision** — on the one legacy presentation collected, the
whole slide index appeared twice, and a first attempt produced a transcript at exactly
twice any parser's length with 1021 of 1023 long lines duplicated.

The live revision is found the way PowerPoint finds it:

1. ``Current User`` stream → ``CurrentUserAtom.offsetToCurrentEdit``.
2. That offset holds a ``UserEditAtom``, chained backwards through ``offsetLastEdit``.
3. Each edit carries a ``PersistDirectoryAtom`` mapping persist IDs to stream offsets;
   merged newest-first, the current edit's ``docPersistIdRef`` resolves to the live
   ``Document``.

This is the Word piece table's lesson again: a stale revision is still in the file, and
a reader that scans instead of resolving finds it.

Records inside that container
-----------------------------
An 8-byte header — version/instance, type, length — then the payload. Containers, whose
low nibble of the first field is 0xF, hold other records rather than data, so the walk
descends into them. Text lives in:

* ``TextBytesAtom`` (0x0FA8) — one byte per character, which is where a legacy encoding
  survives. A slide typed in ``.VnTime`` is stored here.
* ``TextCharsAtom`` (0x0FA0) — UTF-16LE, already Unicode.

    python3 scripts/ppt_text.py file.ppt
"""

from __future__ import annotations

import struct
import sys
from collections.abc import Iterator

_TEXT_CHARS_ATOM = 0x0FA0
_TEXT_BYTES_ATOM = 0x0FA8
_USER_EDIT_ATOM = 0x0FF5
_PERSIST_DIRECTORY_ATOM = 0x1772

_HEADER = struct.Struct("<HHI")
_CURRENT_USER = struct.Struct("<III")  # size, headerToken, offsetToCurrentEdit
_USER_EDIT = struct.Struct("<IHBBIII")  # …, offsetLastEdit, offsetPersistDirectory, docId

# PowerPoint writes CR for a paragraph break and 0x0B for a soft line break.
_BREAKS = str.maketrans({"\r": "\n", "\x0b": "\n"})


def _persist_map(data: bytes, offset: int) -> dict[int, int]:
    """Persist ID → stream offset, from one edit's directory."""
    if offset + _HEADER.size > len(data):
        return {}
    _, record_type, length = _HEADER.unpack_from(data, offset)
    if record_type != _PERSIST_DIRECTORY_ATOM:
        return {}
    mapping: dict[int, int] = {}
    position = offset + _HEADER.size
    end = min(position + length, len(data))
    while position + 4 <= end:
        (entry,) = struct.unpack_from("<I", data, position)
        position += 4
        persist_id, count = entry & 0xFFFFF, entry >> 20
        for index in range(count):
            if position + 4 > end:
                break
            (target,) = struct.unpack_from("<I", data, position)
            position += 4
            mapping[persist_id + index] = target
    return mapping


def _live_document(data: bytes, current_user: bytes) -> int | None:
    """Offset of the ``Document`` container belonging to the most recent save."""
    if len(current_user) < _HEADER.size + _CURRENT_USER.size:
        return None
    _, _, offset = _CURRENT_USER.unpack_from(current_user, _HEADER.size)

    mapping: dict[int, int] = {}
    document_id: int | None = None
    seen: set[int] = set()
    while offset and offset not in seen and offset + _HEADER.size <= len(data):
        seen.add(offset)
        _, record_type, _ = _HEADER.unpack_from(data, offset)
        if record_type != _USER_EDIT_ATOM:
            break
        _, _, _, _, last_edit, persist_offset, persist_id = _USER_EDIT.unpack_from(
            data, offset + _HEADER.size
        )
        # Walked newest to oldest, so an older directory must not overwrite a newer
        # entry: setdefault keeps the first — newest — mapping for each persist ID.
        for key, value in _persist_map(data, persist_offset).items():
            mapping.setdefault(key, value)
        if document_id is None:
            document_id = persist_id
        offset = last_edit
    return mapping.get(document_id) if document_id is not None else None


def _records(data: bytes, start: int, end: int) -> Iterator[tuple[int, bytes]]:
    """Yield ``(type, payload)`` for every atom, descending into containers."""
    position = start
    while position + _HEADER.size <= end:
        version_instance, record_type, length = _HEADER.unpack_from(data, position)
        body = position + _HEADER.size
        if length > end - body:
            return
        if version_instance & 0x0F == 0x0F:
            yield from _records(data, body, body + length)
        else:
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
        data = ole.openstream("PowerPoint Document").read()
        current_user = (
            ole.openstream("Current User").read() if ole.exists("Current User") else b""
        )

    start = _live_document(data, current_user)
    if start is None or start + _HEADER.size > len(data):
        # No usable pointer chain. Reading the whole stream would return every saved
        # revision, so return nothing rather than something silently doubled.
        return ""
    _, _, length = _HEADER.unpack_from(data, start)
    body = start + _HEADER.size

    parts: list[str] = []
    for record_type, payload in _records(data, body, min(body + length, len(data))):
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
