"""Set a line of type as SVG path data.

Two of the logos in img/logos/ carry a line of text that the institution does
not publish as vector artwork, so it has to be set here. Flattening it to paths
means the SVG does not depend on a font being installed wherever it is rendered
- Typst, a browser, or Quarto's HTML - which is the same bargain the NTU and
Paris logos make.

The subset fonts in tools/fonts/ hold only the glyphs those two lines need.
"""

from __future__ import annotations

import os

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def fmt(v: float) -> str:
    out = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if out in ("-0", "") else out


def set_line(
    font_file: str,
    text: str,
    em: float,
    tracking: float = 0.0,
    word_extra: float = 0.0,
) -> tuple[str, float, float]:
    """`text` as path data, its baseline on y=0 and its pen starting at x=0.

    Returns the data and the left and right edges of the ink, which is what a
    logo is aligned by - the sidebearing is a typesetting convenience and has
    nothing to do with where the letters look like they start.

    `tracking` is added after every glyph and `word_extra` after every space,
    both in the same units as `em`, because the two lines this sets are both
    spaced more loosely than the font sets them.

    The em scale and the pen position are folded into the coordinates rather
    than left on the glyphs as transforms. A transform on the element would
    also apply to any gradient the caller paints it with - the name on the
    Porte Verte logo is one gradient across two lines - and each letter would
    get its own copy of the ramp, in glyph units.
    """
    font = TTFont(os.path.join(FONTS, font_file))
    glyphs = font.getGlyphSet()
    names = font["cmap"].getBestCmap()
    scale = em / font["head"].unitsPerEm

    out: list[str] = []
    pen_x, left, right = 0.0, None, None
    for ch in text:
        name = names[ord(ch)]
        # Two decimals: at the sizes these lines are set, that is a hundredth
        # of a pixel, and the default seventeen digits triples the file.
        path = SVGPathPen(glyphs, ntos=lambda v: fmt(round(v, 2)))
        glyphs[name].draw(TransformPen(path, (scale, 0, 0, -scale, pen_x, 0)))
        d = path.getCommands()
        if d:
            out.append(f'<path d="{d}"/>')
            bounds = BoundsPen(glyphs)
            glyphs[name].draw(bounds)
            if bounds.bounds:
                lo = pen_x + bounds.bounds[0] * scale
                hi = pen_x + bounds.bounds[2] * scale
                left = lo if left is None else min(left, lo)
                right = hi if right is None else max(right, hi)
        pen_x += glyphs[name].width * scale + tracking
        if ch == " ":
            pen_x += word_extra
    return "".join(out), left, right
