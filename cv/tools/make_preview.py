"""Draw img/preview.png: the first three pages of cv.pdf, side by side.

The repository README shows it as the picture of the CV, so it goes stale
whenever the layout changes. Not part of the build - it needs PyMuPDF and
Pillow, which the build does not - so run it by hand after a rebuild that moves
things:

    python tools/make_preview.py
"""

from __future__ import annotations

import os

import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "cv.pdf")
OUT = os.path.join(ROOT, "img", "preview.png")

PAGES = 3
HEIGHT = 1287  # px per page; about 110 dpi on A4
GAP = 15  # px of white between pages


def main() -> None:
    doc = pymupdf.open(PDF)
    shots = []
    for page in list(doc)[:PAGES]:
        zoom = HEIGHT / page.rect.height
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        shots.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    width = sum(s.width for s in shots) + GAP * (len(shots) - 1)
    sheet = Image.new("RGB", (width, HEIGHT), "white")
    x = 0
    for s in shots:
        sheet.paste(s, (x, 0))
        x += s.width + GAP
    sheet.save(OUT, optimize=True)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({width} x {HEIGHT})")


if __name__ == "__main__":
    main()
