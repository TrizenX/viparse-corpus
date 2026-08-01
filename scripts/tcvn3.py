#!/usr/bin/env python3
"""A TCVN3 → Unicode table, built independently of viparse.

Ground truth generated with the library under test would make the benchmark
circular: viparse would score 100% against its own output and the number would
mean nothing. So this table was derived from the corpus itself, by aligning the
byte sequences against the fixed phrases that Vietnamese legal documents always
contain — "Cộng hoà xã hội chủ nghĩa Việt Nam", "Độc lập - Tự do - Hạnh phúc",
"Căn cứ Nghị định số", "Quyết định của Bộ trưởng" — and then extended until no
Latin-1 byte was left unmapped across all 31 TCVN3 documents.

It is a transcription aid, not an authority. Every transcript it produces is read
before being marked `ready`.

    python3 scripts/tcvn3.py file.doc
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_text import extract  # noqa: E402

# Lowercase, and the uppercase forms that share a byte in the .VnTimeH font.
TABLE = {
    # A1–A7 are the uppercase base vowels, A8–AE their lowercase counterparts.
    # This structure is why a first pass that guessed at A1–A4 was wrong in every
    # case: they are Ă Â Ê Ô, not accented lowercase.
    "¡": "Ă", "¢": "Â", "£": "Ê", "¤": "Ô", "¥": "Ơ", "¦": "Ư", "§": "Đ",
    "¨": "ă", "©": "â", "ª": "ê", "«": "ô", "¬": "ơ", "\xad": "ư", "®": "đ",

    "µ": "à", "¸": "á", "¶": "ả", "·": "ã", "¹": "ạ",
    "»": "ằ", "¾": "ắ", "¼": "ẳ", "½": "ẵ", "Æ": "ặ",
    "Ç": "ầ", "Ê": "ấ", "È": "ẩ", "É": "ẫ", "Ë": "ậ",
    "Ì": "è", "Ð": "é", "Î": "ẻ", "Ï": "ẽ", "Ñ": "ẹ",
    "Ò": "ề", "Õ": "ế", "Ó": "ể", "Ô": "ễ", "Ö": "ệ",
    "×": "ì", "Ý": "í", "Ø": "ỉ", "Ü": "ĩ", "Þ": "ị",
    "ß": "ò", "ã": "ó", "á": "ỏ", "â": "õ", "ä": "ọ",
    "å": "ồ", "è": "ố", "æ": "ổ", "ç": "ỗ", "é": "ộ",
    "ê": "ờ", "í": "ớ", "ë": "ở", "ì": "ỡ", "î": "ợ",
    "ï": "ù", "ó": "ú", "ñ": "ủ", "ò": "ũ", "ô": "ụ",
    "õ": "ừ", "ø": "ứ", "ö": "ử", "÷": "ữ", "ù": "ự",
    "ú": "ỳ", "ý": "ý", "û": "ỷ", "ü": "ỹ", "þ": "ỵ",
}
# Known limitation. TCVN3 encodes uppercase Vietnamese with the *same bytes* as
# lowercase and distinguishes them by font (.VnTime vs .VnTimeH). A byte-level table
# cannot recover case, so headings set in .VnTimeH come back lowercase. Every
# transcript is read and its case corrected before being marked `ready` — which is
# why these are transcripts rather than conversions.


def _fix_uppercase_runs(text: str) -> str:
    """Restore case inside .VnTimeH runs.

    TCVN3 has no uppercase accented letters: an uppercase heading is typed with
    uppercase ASCII and the *same* accented bytes as lowercase, and the .VnTimeH
    font draws them uppercase. Converting byte-by-byte therefore yields "TOàN" for
    "TOÀN" and "ĐĂNG Ký" for "ĐĂNG KÝ".

    The decision is per line, not per word. A word like "Bé" ("Bộ") has exactly one
    ASCII letter and it is uppercase, so a per-word rule turns ordinary capitalised
    prose into shouting: "của Bé trưởng" became "của BỘ trưởng". A line is judged
    uppercase only when it has several ASCII letters and they are all uppercase.

    Lines with no uppercase ASCII at all are left alone. They may be genuinely
    lowercase, or a heading whose typist relied on the font — that call belongs to
    the reader who marks the transcript `ready`.
    """
    out = []
    for line in text.split("\n"):
        ascii_letters = [c for c in line if c.isascii() and c.isalpha()]
        if len(ascii_letters) >= 3 and all(c.isupper() for c in ascii_letters):
            out.append(line.upper())
        else:
            out.append(line)
    return "\n".join(out)


def convert(text: str) -> str:
    """Apply the table, restore uppercase runs, normalise to NFC."""
    mapped = "".join(TABLE.get(c, c) for c in text)
    return unicodedata.normalize("NFC", _fix_uppercase_runs(mapped))


def unmapped(text: str) -> set[str]:
    """Latin-1 characters the table does not cover — these are the gaps."""
    return {c for c in text if 0xA0 < ord(c) < 0x100 and c not in TABLE}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    raw = extract(sys.argv[1])
    gaps = unmapped(raw)
    if gaps:
        print(f"unmapped: {sorted(gaps)}", file=sys.stderr)
    print(convert(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
