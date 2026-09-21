"""Build img/logos/ntu-full.svg: the NTU crest with the wordmark beneath it.

The asset copied from the lab website is the crest alone. This composes the
full vertical lockup - crest, three lines of wordmark, red rule, SINGAPORE -
to match NTU's published logo.

    python tools/make_ntu_logo.py

The wordmark is set in Roboto Bold, NOT NTU's own typeface, so this is a close
reconstruction rather than the official artwork. At the ~38 pt the CV renders
logos at, the difference is invisible; if the CV is ever used somewhere the
logo appears large, replace this with the official SVG.

Text is flattened to paths, so nothing depends on fonts being available to
whatever renders the SVG.
"""

from __future__ import annotations

import io
import os
import sys

import pymupdf

from cvdata import LOGOS, ROOT

NAVY = (0x16 / 255, 0x2C / 255, 0x53 / 255)
RED = (0xE0 / 255, 0x19 / 255, 0x32 / 255)

W = H = 600.0
CREST_TOP, CREST_H = 18.0, 272.0
LINES = ("NANYANG", "TECHNOLOGICAL", "UNIVERSITY")
LINE_BASELINES = (372.0, 432.0, 492.0)
WORDMARK_TARGET_W = 392.0  # width of the longest line, tuned to the crest
RULE_Y, RULE_H = 522.0, 4.5
SINGAPORE_BASELINE, SINGAPORE_TRACKING = 580.0, 12.0
SINGAPORE_SCALE = 0.70      # relative to the wordmark size

FONT_PATH = os.path.join(ROOT, "fonts", "Roboto-Bold.ttf")


def main() -> int:
    font = pymupdf.Font(fontfile=FONT_PATH)

    # Scale the type so the longest line spans WORDMARK_TARGET_W.
    probe = 100.0
    size = probe * WORDMARK_TARGET_W / font.text_length(max(LINES, key=len), probe)

    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    page.insert_font(fontname="RB", fontfile=FONT_PATH)

    # Crest, centred, scaled to CREST_H.
    crest = pymupdf.open(os.path.join(LOGOS, "ntu.svg"))
    crest_pdf = pymupdf.open("pdf", crest.convert_to_pdf())
    src = crest_pdf[0].rect
    cw = CREST_H * src.width / src.height
    page.show_pdf_page(
        pymupdf.Rect((W - cw) / 2, CREST_TOP, (W + cw) / 2, CREST_TOP + CREST_H),
        crest_pdf,
        0,
    )

    for line, baseline in zip(LINES, LINE_BASELINES):
        w = font.text_length(line, size)
        page.insert_text(
            ((W - w) / 2, baseline), line, fontname="RB", fontsize=size, color=NAVY
        )

    page.draw_rect(
        pymupdf.Rect((W - WORDMARK_TARGET_W) / 2, RULE_Y,
                     (W + WORDMARK_TARGET_W) / 2, RULE_Y + RULE_H),
        color=None,
        fill=RED,
    )

    # SINGAPORE is letterspaced, so place each glyph.
    s_size = size * SINGAPORE_SCALE
    glyphs = [(c, font.text_length(c, s_size)) for c in "SINGAPORE"]
    total = sum(w for _, w in glyphs) + SINGAPORE_TRACKING * (len(glyphs) - 1)
    x = (W - total) / 2
    for ch, w in glyphs:
        page.insert_text(
            (x, SINGAPORE_BASELINE), ch, fontname="RB", fontsize=s_size, color=RED
        )
        x += w + SINGAPORE_TRACKING

    out = os.path.join(LOGOS, "ntu-full.svg")
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        page.get_svg_image(text_as_path=True)
    )
    print(f"wrote {os.path.relpath(out, ROOT)} ({os.path.getsize(out) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
