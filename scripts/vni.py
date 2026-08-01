#!/usr/bin/env python3
"""A VNI → Unicode table, built independently of viparse.

VNI is not TCVN3's shape. TCVN3 replaces a vowel with one high byte (``lËp`` → lập);
VNI keeps the ASCII vowel and appends a modifier that encodes the diacritic and the
tone together (``laäp`` → lập). So the table is keyed on two-character sequences.

.. warning::
   **Derived from a single document.** Only one VNI file has been collected so far, so
   this covers the sequences that appear in it and is extended by the systematic
   structure of the encoding rather than by observation. It is good enough to produce
   one transcript, which is read before being marked ``ready``.

   It is **not** suitable for contributing upstream. Doing that would repeat the
   mistake the TCVN3 table already made once — filling gaps by inference to make a
   count look complete. More VNI source documents first.

    python3 scripts/vni.py file.doc
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_text import extract  # noqa: E402

# Modifier → (diacritic added to the base, tone). Uppercase text uses uppercase
# modifiers with an uppercase base — `OÄ` is Ộ — so both cases are listed.
_TONES = {"ù": "\u0301", "ø": "\u0300", "û": "\u0309", "õ": "\u0303", "ï": "\u0323"}
_MODIFIERS: dict[str, tuple[str, str]] = {
    **{m: ("", t) for m, t in _TONES.items()},
    **{m.upper(): ("", t) for m, t in _TONES.items()},
    "â": ("\u0302", ""), "ê": ("\u0306", ""),
    "Â": ("\u0302", ""), "Ê": ("\u0306", ""),
    "á": ("\u0302", "\u0301"), "à": ("\u0302", "\u0300"),
    "å": ("\u0302", "\u0309"), "ã": ("\u0302", "\u0303"), "ä": ("\u0302", "\u0323"),
    "Á": ("\u0302", "\u0301"), "À": ("\u0302", "\u0300"),
    "Å": ("\u0302", "\u0309"), "Ã": ("\u0302", "\u0303"), "Ä": ("\u0302", "\u0323"),
    # Breve family. `ë` is breve+*nặng*, read off `hoaëc` (hoặc) and `ñaëc` (đặc) in the
    # collected VNI documents — an earlier draft had it as breve+ngã, which is what a
    # first pass writes when it fills the row by symmetry instead of by observation.
    # ẳ and ẵ are deliberately absent: no VNI document collected so far contains either,
    # and guessing them is how the TCVN3 table got four entries wrong.
    "é": ("\u0306", "\u0301"), "è": ("\u0306", "\u0300"), "ë": ("\u0306", "\u0323"),
    "É": ("\u0306", "\u0301"), "È": ("\u0306", "\u0300"), "Ë": ("\u0306", "\u0323"),
}

# Base characters, mapped to the Unicode letter they stand for before a modifier is
# applied. ô and ö are VNI letters in their own right (ơ, ư) and take tones like any
# other vowel — `Töï` is Tự — so they belong here, not among the standalone letters.
_BASES = {
    **{c: c for c in "aeiouyAEIOUY"},
    "ô": "\u01a1", "Ô": "\u01a0",  # ơ Ơ
    "ö": "\u01b0", "Ö": "\u01af",  # ư Ư
}

# Letters that never take a following modifier.
#
# VNI parks the i-family letters that Latin-1 lacks at o-family positions, which makes
# this section easy to get backwards — a first pass mapped ì→ỉ and í→ĩ, when those two
# are already the letters they look like (`cheát vì` is chết vì, `Chi phí` is chi phí).
# Each entry below is quoted from the corpus.
_SOLO = {
    "ñ": "đ", "Ñ": "Đ",              # Ñoäc laäp → Độc lập
    "ò": "\u1ecb", "Ò": "\u1eca",     # ñôn vò → đơn vị;  ÑÒNH KYØ → ĐỊNH KỲ
    "æ": "\u1ec9", "Æ": "\u1ec8",     # nghæ maát söùc → nghỉ mất sức;  CHÆ TIEÂU → CHỈ TIÊU
    "ó": "\u0129", "Ó": "\u0128",     # NGHÓA → NGHĨA (uppercase observed; lowercase by symmetry)
}


def _compose(base: str, diacritic: str, tone: str) -> str | None:
    composed = unicodedata.normalize("NFC", base + diacritic + tone)
    # A sequence that does not compose to a single Vietnamese letter is not a real
    # pairing — refuse it rather than emit a base with dangling combining marks.
    return composed if len(composed) == 1 else None


def convert(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if ch in _BASES and nxt in _MODIFIERS:
            diacritic, tone = _MODIFIERS[nxt]
            base = _BASES[ch]
            # ơ and ư already carry their horn; a circumflex or breve on top is not a
            # Vietnamese letter, so such a pairing is not a real one.
            if base in "\u01a1\u01a0\u01b0\u01af" and diacritic:
                pass
            else:
                composed = _compose(base, diacritic, tone)
                if composed:
                    out.append(composed)
                    i += 2
                    continue

        if ch in _SOLO:
            out.append(_SOLO[ch])
            i += 1
            continue

        if ch in _BASES and _BASES[ch] != ch:
            out.append(_BASES[ch])
            i += 1
            continue

        out.append(ch)
        i += 1

    return unicodedata.normalize("NFC", "".join(out))


# Vietnamese letters that legitimately live in the Latin-1 supplement; they are output,
# not residue. Flagging them was the same mistake this file's TCVN3 sibling made once.
_VALID_LATIN1_VN = set("ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúý")


def _build_encoder() -> dict[str, str]:
    """Unicode → VNI surface, inverted from the decoding table.

    Built by inversion rather than typed out, so the two directions cannot drift apart:
    a synthetic document that decodes back to something other than its source would
    measure the generator, not the parser.
    """
    table: dict[str, str] = {}

    # Standalone forms first. Real VNI documents write ị as `ò`, ỉ as `æ` and ĩ as `ó`,
    # not as i plus a tone; generating the composed form would produce text that decodes
    # correctly but does not look like anything a VNI document contains, and so would
    # not exercise the same paths in a parser.
    for surface, letter in _SOLO.items():
        table.setdefault(letter, surface)

    for base_ch, base_letter in _BASES.items():
        for modifier, (diacritic, tone) in _MODIFIERS.items():
            if base_letter in "\u01a1\u01a0\u01b0\u01af" and diacritic:
                continue
            # Uppercase text uses uppercase modifiers — `ÑAÊNG`, not `ÑAêNG`.
            if base_ch.isupper() != modifier.isupper() and modifier.isalpha():
                continue
            composed = _compose(base_letter, diacritic, tone)
            if composed and composed not in table:
                table[composed] = base_ch + modifier
    # A base that VNI writes with a bare letter needs no sequence at all.
    for base_ch, base_letter in _BASES.items():
        if base_letter != base_ch:
            table.setdefault(base_letter, base_ch)
    return table


_ENCODER = _build_encoder()


class Unencodable(ValueError):
    """A Vietnamese letter with no verified VNI sequence."""


def encode(text: str) -> str:
    """Unicode Vietnamese → VNI surface bytes. The inverse of :func:`convert`.

    Raises :class:`Unencodable` rather than passing a letter through untouched. A
    synthetic document containing a Unicode ``ẳ`` in the middle of VNI text is not a VNI
    document, and scoring a parser against one would report a table gap that is really
    a generator gap.
    """
    normalised = unicodedata.normalize("NFC", text)
    out = []
    for ch in normalised:
        if ch in _ENCODER:
            out.append(_ENCODER[ch])
        elif ch.isalpha() and ord(ch) > 127:
            raise Unencodable(ch)
        else:
            out.append(ch)
    return "".join(out)


def unmapped(text: str) -> set[str]:
    converted = convert(text)
    return {
        c for c in converted if 0xA0 < ord(c) < 0x100 and c not in _VALID_LATIN1_VN
    }


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
