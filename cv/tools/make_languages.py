"""Build img/languages/: the four flags, and the Python and R marks.

    python tools/make_languages.py

Not part of build.sh. Like the other make_*_logo.py scripts this runs once and
its output is committed, so a build needs nothing but Quarto and Typst - and,
here, no network.

The flags are drawn rather than downloaded: four rectangles and, for the Union
Flag, the standard saltire construction. That is less code than vendoring four
files, and it is where the old LaTeX CV drew them too (see the `Language` chunk
of ../old_cv/DominiqueMakowski_CV.Rmd, whose colours these are).

Each flag keeps its own proportions - 3:2 for France and Italy, 8:5 for Poland,
2:1 for the Union Flag - because they are drawn to a common *height* in the CV,
not a common width. A Union Flag squashed into a tricolour's box is the sort of
thing a reader notices without being able to say why.

The two marks are the official artwork, fetched from the projects themselves:

  Python  https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg
          The PSF's logo mark. A trademark of the Python Software Foundation,
          used here nominatively, to name the language.
  R       https://www.r-project.org/logo/Rlogo.svg
          (c) 2016 The R Foundation, CC-BY-SA 4.0.
"""

from __future__ import annotations

import io
import os
import sys
import urllib.request

from cvdata import LANGS

# The border that keeps a white flag off a white page. Given per 30 units of
# height so the four come out at the same visual weight once they are drawn to
# a common height. Kept light so the flags still read as flat: with no border
# at all (None), Poland's white half has no edge on a white page. It was
# #9a9a9a at 1.0 before, which read as a frame.
BORDER = "#d4d4d4"
BORDER_PER_30 = 0.8

SOURCES = {
    "python.svg": (
        "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"
    ),
    "r.svg": "https://www.r-project.org/logo/Rlogo.svg",
}


def svg(w: float, h: float, body: str, defs: str = "") -> str:
    """A flag drawn on a light grey mat rather than outlined by a stroke.

    The border was a stroke laid over the artwork, and at a flag's printed size
    it is well under a pixel wide. PDF viewers snap and smooth strokes that thin
    differently at every zoom level, and the edge of the bands underneath showed
    through, so in Acrobat the outline came and went and darkened on the blue
    and red sides. A filled rectangle behind the flag, with the flag inset into
    it, is area rather than line: it renders the same way at every zoom, and no
    band colour reaches past it.
    """
    if BORDER:
        b = h / 30.0 * BORDER_PER_30
        body = (
            f'<rect width="{w:g}" height="{h:g}" fill="{BORDER}"/>'
            f'<g transform="translate({b:g} {b:g}) '
            f'scale({(w - 2 * b) / w:g} {(h - 2 * b) / h:g})">{body}</g>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" '
        f'width="{w:g}" height="{h:g}">'
        f"{defs}{body}</svg>\n"
    )


def vertical(w: float, h: float, colours: tuple[str, ...]) -> str:
    """A flag of vertical bands: France, Italy."""
    band = w / len(colours)
    return svg(
        w,
        h,
        "".join(
            f'<rect x="{i * band:g}" y="0" width="{band:g}" height="{h:g}" '
            f'fill="{c}"/>'
            for i, c in enumerate(colours)
        ),
    )


def horizontal(w: float, h: float, colours: tuple[str, ...]) -> str:
    """A flag of horizontal bands, top first: Poland."""
    band = h / len(colours)
    return svg(
        w,
        h,
        "".join(
            f'<rect x="0" y="{i * band:g}" width="{w:g}" height="{band:g}" '
            f'fill="{c}"/>'
            for i, c in enumerate(colours)
        ),
    )


def union_flag() -> str:
    """The Union Flag, at its own 2:1.

    The saltire is drawn as two stroked diagonals rather than as eight
    polygons, and St Patrick's red is counterchanged by clipping those
    diagonals to opposite quadrants - which is what the clip path's four
    triangles are. Anything outside the field is cut by the viewBox.
    """
    diagonals = '<path d="M0,0 L60,30 M60,0 L0,30"'
    return svg(
        60,
        30,
        f'<rect width="60" height="30" fill="#012169"/>'
        f'{diagonals} stroke="#ffffff" stroke-width="6"/>'
        f'{diagonals} clip-path="url(#counterchange)" stroke="#C8102E" '
        f'stroke-width="4"/>'
        f'<path d="M30,0 v30 M0,15 h60" stroke="#ffffff" stroke-width="10"/>'
        f'<path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>',
        defs=(
            '<clipPath id="counterchange">'
            '<path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/>'
            "</clipPath>"
        ),
    )


FLAGS = {
    # 3:2. The colours are the ones the LaTeX CV used, not the darker official
    # pair, so the two versions of the CV match.
    "french.svg": lambda: vertical(60, 40, ("#0055A4", "#FFFFFF", "#EF4135")),
    "italian.svg": lambda: vertical(60, 40, ("#009246", "#FFFFFF", "#CE2B37")),
    # 8:5, white over crimson.
    "polish.svg": lambda: horizontal(60, 37.5, ("#FFFFFF", "#DC143C")),
    "english.svg": union_flag,
}


def fetch(name: str, url: str) -> None:
    """Vendor one mark, as sent. Re-fetching a file that is already there would
    replace committed artwork with whatever upstream is today, silently."""
    path = os.path.join(LANGS, name)
    if os.path.exists(path):
        print(f"  {name} already vendored - delete it to re-fetch")
        return
    request = urllib.request.Request(url, headers={"User-Agent": "cv-quarto"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read().decode("utf-8")
    io.open(path, "w", encoding="utf-8", newline="\n").write(data)
    print(f"  {name} <- {url} ({len(data) / 1024:.1f} KB)")


def main() -> int:
    os.makedirs(LANGS, exist_ok=True)
    for name, draw in FLAGS.items():
        io.open(os.path.join(LANGS, name), "w", encoding="utf-8", newline="\n").write(
            draw()
        )
        print(f"  {name} drawn")
    for name, url in SOURCES.items():
        fetch(name, url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
