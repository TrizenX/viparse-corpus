#!/usr/bin/env python3
"""Render the ground-truth transcripts to page images, so OCR can finally be scored.

Why this shape
--------------
OCR is the one capability viparse advertises with no number behind it: every test in the
library mocks Tesseract, and no scanned document exists in any published benchmark. The
obstacle was never the metric — it was that scoring OCR needs a page image whose correct
text is already known, and the corpus holds documents, not scans.

It does, however, hold **96 hand-written transcripts**. Rendering one back to a page image
gives exactly the missing pair: an image, and the text that is on it, at no cost in new
transcription. The renderer shares no code with viparse or with Tesseract, so nothing here
can agree with itself.

What this is not
----------------
**A rendered page is not a scan.** It has perfect contrast, no skew, no sensor noise, no
paper texture, no bleed-through from the reverse side, and a font Tesseract finds easy.
The number it produces is a **ceiling**: a real scan of the same document will do worse,
and how much worse is not measured here.

That is why ``--degrade`` exists — rotation, noise, blur and JPEG artefacts, applied on
top. It is closer to a scan and still not one. Both numbers should be published together,
because the gap between them says more than either alone.

Pages per document are capped (``--max-pages``) and **the transcript is truncated to
exactly the text that was rendered**, so the score compares like with like rather than
punishing the parser for pages that were never drawn. The cap is written into the manifest
and printed, because a benchmark that quietly measures a third of a document reads as
though it measured all of it.

    python3 scripts/make_ocr_bench.py --truth ground-truth/ --out ocr/clean/
    python3 scripts/make_ocr_bench.py --truth ground-truth/ --out ocr/degraded/ --degrade
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
import textwrap
from pathlib import Path

# 300 dpi A4 — the resolution a document scanner is normally set to.
_PAGE = (2480, 3508)
_MARGIN = 236
_FONT_PX = 44
_LINE_SPACING = 1.5

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _font(size: int):  # noqa: ANN202 - PIL type, imported lazily
    from PIL import ImageFont

    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    print(
        "no Unicode TTF found; every diacritic would render as a box. Looked in:\n  "
        + "\n  ".join(FONT_CANDIDATES),
        file=sys.stderr,
    )
    raise SystemExit(2)


#: A transcript with more than this fraction of tabbed lines is a table, not prose, and
#: this renderer cannot draw it. It wraps text to a column width, so a tab-separated row
#: becomes a run-on line, the layout is destroyed before Tesseract sees it, and the score
#: measures the renderer rather than the OCR.
#:
#: The threshold was chosen after seeing the scores, which is worth saying out loud. What
#: makes it defensible is that it sits in an empty part of the distribution — 31 documents
#: are above 0.8 and score 0.714, five sit between 0.2 and 0.8 and score 0.97, and the cut
#: does not have to land on any of them. Both figures are published either way.
TABULAR_LINE_RATIO = 0.8


def is_tabular(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    return sum(1 for line in lines if "\t" in line) / len(lines) > TABULAR_LINE_RATIO


def _wrap(text: str, columns: int) -> list[str]:
    """Wrap to a fixed column count, keeping blank lines so paragraphs stay apart."""
    lines: list[str] = []
    for source_line in text.splitlines():
        if not source_line.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(source_line, width=columns) or [""])
    return lines


def _degrade(image, seed: int):  # noqa: ANN001, ANN202 - PIL types
    """Rotation, noise, blur and JPEG artefacts — closer to a scan, still not one."""
    from PIL import Image, ImageFilter

    rng = random.Random(seed)
    image = image.rotate(rng.uniform(-0.6, 0.6), resample=Image.BICUBIC, fillcolor="white")
    image = image.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.4, 0.9)))

    pixels = image.load()
    width, height = image.size
    # Sparse salt-and-pepper rather than per-pixel noise: cheap, and closer to the dust
    # and speckle a real scanner picks up than uniform grain would be.
    for _ in range((width * height) // 400):
        x, y = rng.randrange(width), rng.randrange(height)
        pixels[x, y] = 0 if rng.random() < 0.5 else 255

    buffer = io.BytesIO()
    image.convert("L").save(buffer, format="JPEG", quality=rng.randint(45, 65))
    buffer.seek(0)
    return Image.open(buffer).copy()


def render(text: str, max_pages: int, degrade: bool, seed: int) -> tuple[list, str]:
    """Page images plus the text that actually fitted on them."""
    from PIL import Image, ImageDraw

    font = _font(_FONT_PX)
    line_height = int(_FONT_PX * _LINE_SPACING)
    usable_width = _PAGE[0] - 2 * _MARGIN
    lines_per_page = (_PAGE[1] - 2 * _MARGIN) // line_height
    # Measure with a representative Vietnamese string rather than assuming a width: tone
    # marks and đ/ơ/ư are wider than ASCII, and guessing here would overflow the margin.
    sample = "ăâđêôơư nghiệp quốc tế xã hội chủ nghĩa Việt Nam"
    average_char = font.getlength(sample) / len(sample)
    columns = max(20, int(usable_width / average_char))

    lines = _wrap(text, columns)
    pages, drawn = [], []
    for start in range(0, len(lines), lines_per_page):
        if len(pages) >= max_pages:
            break
        chunk = lines[start : start + lines_per_page]
        page = Image.new("RGB", _PAGE, "white")
        draw = ImageDraw.Draw(page)
        for index, line in enumerate(chunk):
            draw.text((_MARGIN, _MARGIN + index * line_height), line, fill="black", font=font)
        pages.append(_degrade(page, seed + len(pages)) if degrade else page.convert("L"))
        drawn.extend(chunk)
    return pages, "\n".join(drawn)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--truth", type=Path, required=True, help="directory of transcripts")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-pages", type=int, default=3, help="pages rendered per document")
    ap.add_argument("--degrade", action="store_true", help="rotation, noise, blur, JPEG")
    ap.add_argument("--limit", type=int, help="stop after N documents (says so if it does)")
    ap.add_argument(
        "--skip-tabular",
        action="store_true",
        help="omit transcripts that are mostly tab-separated tables; see TABULAR_LINE_RATIO",
    )
    args = ap.parse_args()

    images = args.out / "images"
    truth = args.out / "truth"
    images.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)

    transcripts = sorted(args.truth.glob("*.txt"))
    selected = transcripts[: args.limit] if args.limit else transcripts
    manifest = {
        "max_pages": args.max_pages,
        "degraded": args.degrade,
        "documents_available": len(transcripts),
        "documents_rendered": len(selected),
    }

    truncated = 0
    total_pages = 0
    skipped_tabular: list[str] = []
    for index, path in enumerate(selected):
        text = path.read_text(encoding="utf-8")
        if args.skip_tabular and is_tabular(text):
            skipped_tabular.append(path.stem)
            continue
        pages, rendered = render(text, args.max_pages, args.degrade, seed=index * 97)
        if not pages:
            continue
        # Multi-page TIFF: one file per document, which also exercises the frame walking
        # the engine does for a digitised archive.
        pages[0].save(
            images / f"{path.stem}.tif",
            format="TIFF",
            save_all=len(pages) > 1,
            append_images=pages[1:],
        )
        (truth / f"{path.stem}.txt").write_text(rendered, encoding="utf-8")
        total_pages += len(pages)
        if len(rendered) < len(text.rstrip()):
            truncated += 1

    manifest["pages_rendered"] = total_pages
    manifest["documents_truncated"] = truncated
    manifest["skipped_tabular"] = skipped_tabular
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    kind = "degraded" if args.degrade else "clean"
    print(f"  {kind}: {len(selected)} document(s), {total_pages} page(s) -> {images}")
    if truncated:
        # Not a footnote. Two thirds of these documents are longer than what was drawn,
        # and a reader who does not know that will read the score as covering all of them.
        print(
            f"  CAPPED: {truncated} of {len(selected)} document(s) are longer than "
            f"{args.max_pages} page(s); their transcripts were truncated to match."
        )
    if skipped_tabular:
        print(
            f"  SKIPPED: {len(skipped_tabular)} tabular transcript(s) this renderer cannot "
            f"draw (>{TABULAR_LINE_RATIO:.0%} of lines contain a tab)."
        )
    if args.limit and args.limit < len(transcripts):
        print(f"  LIMITED: {args.limit} of {len(transcripts)} documents rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
