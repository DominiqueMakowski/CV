"""Build img/logos/universite-paris.svg: monogram in maroon, name in black.

The asset copied from the lab website is the reversed lockup - a solid maroon
square with the monogram and name knocked out in white. On a white page that
square reads as a heavy block rather than a logo, so this rebuilds it the way
the university sets it on light backgrounds: no panel, monogram in the brand
maroon, name in black underneath.

It also updates the name. The source asset still says "Universite de Paris";
the institution has been Universite Paris Cite since 2022, which is what
PROFILE.md records.

    python tools/make_paris_logo.py

The name is set in Roboto rather than the university's own typeface, so this is
a close reconstruction, not official artwork. Same caveat as tools/make_ntu_logo.py.
"""

from __future__ import annotations

import io
import os
import re
import sys

import pymupdf

from cvdata import LOGOS, ROOT

MAROON = (0x8B / 255, 0x15 / 255, 0x38 / 255)
BLACK = (0, 0, 0)

W, H = 300.0, 268.0
MARK_TOP, MARK_H = 8.0, 182.0
NAME = "Université Paris Cité"
NAME_BASELINE, NAME_TARGET_W = 246.0, 232.0

# The reversed lockup as supplied, kept as the source this is built from.
SOURCE = os.path.join(LOGOS, "universite-paris-panel.svg")
OUT = os.path.join(LOGOS, "universite-paris.svg")
OUT_MARK = os.path.join(LOGOS, "universite-paris-mark.svg")
FONT_PATH = os.path.join(ROOT, "fonts", "Roboto-Regular.ttf")

# Path index 2 in the source file is the monogram on its own; 0 is the maroon
# panel, 1 and 3 are edge slivers, 4 is the old wordmark.
MONOGRAM_PATH = 2


def monogram_pdf(src: str) -> pymupdf.Document:
    """The monogram alone, recoloured maroon, as a one-page PDF."""
    s = io.open(src, encoding="utf-8").read()
    paths = [m.group(0) for m in re.finditer(r"<path[^>]*?(?:/>|>)", s, re.S)]
    mark = re.sub(r"fill:#[0-9a-fA-F]{6}", "fill:#8b1538", paths[MONOGRAM_PATH])
    frag = s[: s.index("<path")] + mark + "</g></g></svg>"

    tmp = os.path.join(LOGOS, "_monogram.tmp.svg")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(frag)
    try:
        return pymupdf.open("pdf", pymupdf.open(tmp).convert_to_pdf())
    finally:
        os.remove(tmp)


def main() -> int:
    mark = monogram_pdf(SOURCE)

    # The monogram sits in a 300x300 canvas with a lot of air; find its real box.
    page = mark[0]
    box = None
    for d in page.get_drawings():
        box = d["rect"] if box is None else (box | d["rect"])
    if box is None or box.is_empty:
        print("could not find the monogram artwork", file=sys.stderr)
        return 1

    font = pymupdf.Font(fontfile=FONT_PATH)
    size = 100.0 * NAME_TARGET_W / font.text_length(NAME, 100.0)

    doc = pymupdf.open()
    out_page = doc.new_page(width=W, height=H)
    out_page.insert_font(fontname="RR", fontfile=FONT_PATH)

    mw = MARK_H * box.width / box.height
    out_page.show_pdf_page(
        pymupdf.Rect((W - mw) / 2, MARK_TOP, (W + mw) / 2, MARK_TOP + MARK_H),
        mark,
        0,
        clip=box,
    )

    tw = font.text_length(NAME, size)
    out_page.insert_text(
        ((W - tw) / 2, NAME_BASELINE), NAME, fontname="RR", fontsize=size, color=BLACK
    )

    svg = out_page.get_svg_image(text_as_path=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(svg)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) / 1024:.0f} KB)")

    # Monogram on its own, for sections whose logos are too small for the name
    # to be legible - it would render as a grey smear rather than words.
    mark_doc = pymupdf.open()
    mark_page = mark_doc.new_page(width=box.width, height=box.height)
    mark_page.show_pdf_page(mark_page.rect, mark, 0, clip=box)
    io.open(OUT_MARK, "w", encoding="utf-8", newline="\n").write(
        mark_page.get_svg_image(text_as_path=True)
    )
    print(
        f"wrote {os.path.relpath(OUT_MARK, ROOT)}"
        f" ({os.path.getsize(OUT_MARK) / 1024:.0f} KB)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
