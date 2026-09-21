"""Build img/logos/porte-verte.svg from the hospital's logo and its own mark.

img/logos/raw-porte-verte.jpg is a 512 px screenshot of the Hopital La Porte
Verte lockup: the name over two lines in an orange-to-purple wash, and under it
the univi mark with SANTE beside it. It is cropped tight enough to cut the
circumflex off "Hopital", the last "e" off "Verte", the left of the mark and
the foot of its swoosh, so it cannot simply be traced - the missing pieces have
to be put back.

Almost none of it needs tracing anyway, because the parts are separately
available:

  the name    is live text on the hospital's own site. Its stylesheet sets
              .header-baseline in noto-sans over a 90-degree gradient from
              #e84e1c to #931c80, clipped to the text - which is exactly the
              wash in the screenshot, endpoints and all. So the two lines are
              set in Noto Sans and painted with that gradient rather than
              traced. The screenshot is Regular, not the site's 600: its stems
              measure 6.7-7.2 px where Regular gives 6.8-6.9 and Medium 8.2

  the mark    is served whole and unclipped as global-logo-color.png, kept here
              as img/logos/raw-univi-mark.png at 705 px with an alpha channel.
              Seven components, each traced from that alpha

  SANTE       is the one thing with no source. It is set in Barlow Semi
              Condensed, the closest of the faces to hand; the real one is a
              DIN, which is not free to redistribute. Tracing it instead was
              tried and thrown away: three-pixel strokes in a JPEG come out of
              potrace with bent stems and a lumpy A

Everything is then placed where the screenshot has it. The name comes out at an
em of 74.0 px, letters a point apart and word spaces stretched from 19.2 px to
26.3 - the liberties the lockup takes with the font's own metrics, and the
reason the second line runs wider than Noto Sans would set it. The mark's scale
and position come from its two dots, whose centres are 107 px apart in the
screenshot and 264 px apart in the PNG.

The mark's colour is not one gradient but seven. Fitting a linear ramp to each
component separately leaves a residual of 0.3-1.2% of its variance, so each
piece really does carry its own, as Illustrator artwork with a gradient applied
per object does; one ramp across the whole mark leaves 59%. Each
component therefore gets its own linearGradient, with the axis and the two end
colours measured off the PNG.

    python tools/make_porte_verte_logo.py

Requires potracer (pip install potracer). The run prints how much of the
screenshot the result covers, as intersection over union of the two ink masks
at the screenshot's own size, counting only what the screenshot does not crop.
"""

from __future__ import annotations

import io
import os
import sys

import numpy as np
import potrace
import pymupdf
from PIL import Image
from scipy import ndimage

from cvdata import LOGOS, ROOT
from svgtext import fmt, set_line

SHOT = os.path.join(LOGOS, "raw-porte-verte.jpg")
MARK = os.path.join(LOGOS, "raw-univi-mark.png")
OUT = os.path.join(LOGOS, "porte-verte.svg")

WARM, COOL = "#e84e1c", "#931c80"  # the two ends of the house gradient
PURPLE = "#931c80"  # SANTE, which is flat
TARGET = 400.0  # longest side of the output viewBox


# --- the lockup, in the screenshot's own pixels ---------------------------

# The name: Noto Sans Regular. The em comes from the cap height, measured as
# the coverage down a column of a flat stem - 52.8 px on the "L", the "H" and
# the "P" alike, and Noto Sans puts its caps at 0.714 em. Spacing is then a
# least-squares fit of the letters' left edges, which is what pins it: em and
# tracking trade off almost exactly if both are free, so the em has to be
# fixed first. Residual 1.7 px over nineteen letters on a 512 px screenshot.
NAME_FONT = "NotoSans-Regular.subset.ttf"
NAME_EM = 52.8 / 0.714
NAME_TRACKING = 1.043
NAME_WORD_EXTRA = 6.076  # so a space runs 26.3 px against the font's own 19.2
NAME_LEFT = -8.18  # the pen; the screenshot crops a shade into the "H" and "L"
NAME_BASELINES = (59.23, 136.44)
NAME_LINES = ("Hôpital", "La Porte Verte")

# SANTE: Barlow Semi Condensed Regular, fitted the same way. Its letters are
# spaced well apart, so the tracking is part of the measurement.
SANTE_FONT = "BarlowSemiCondensed-Regular.subset.ttf"
SANTE_EM, SANTE_TRACKING = 45.25, 4.23
SANTE_LEFT, SANTE_BASELINE = 274.62, 248.71

# The mark, from its two dots: 107.0 px between centres here against 264.0 in
# the PNG, the first dot's left edge at 128.0 against 320.0.
MARK_SCALE = 107.0 / 264.0
MARK_X = 128.0 - 320.0 * MARK_SCALE
MARK_Y = 166.0  # the dots' tops, which are the top of the PNG

# Ink threshold, as a share of full coverage, for the closing comparison.
INK = 0.3


# --- the mark -------------------------------------------------------------


def trace(mask: np.ndarray, ox: int, oy: int) -> str:
    """potrace outline of one component of the mark, as path data."""
    path = potrace.Bitmap(~np.pad(mask, 1)).trace(turdsize=2, opttolerance=0.2)

    def point(p) -> str:
        return f"{ox - 1 + p.x:.2f} {oy - 1 + p.y:.2f}"

    d = []
    for curve in path:
        d.append("M" + point(curve.start_point))
        for seg in curve:
            if seg.is_corner:
                d.append("L" + point(seg.c) + "L" + point(seg.end_point))
            else:
                d.append(
                    "C" + point(seg.c1) + " " + point(seg.c2) + " " + point(seg.end_point)
                )
        d.append("Z")
    return "".join(d)


def gradient(rgb: np.ndarray, mask: np.ndarray) -> tuple[tuple[float, float, float, float], str, str]:
    """The linear gradient this component is painted with.

    Colour over a linear gradient is an affine function of position, so the
    axis is the direction in which a straight-line fit explains the most of the
    colour, found by sweeping it a degree at a time. The endpoints are then the
    extremes of the ink projected onto that axis, and the colours are what the
    fit gives there - read off the fit rather than off the corner pixels, which
    are half-covered and would come out pale.
    """
    ys, xs = np.nonzero(mask)
    rgb = rgb[mask].astype(np.float64)

    best = None
    for degrees in np.arange(-90.0, 90.0, 1.0):
        radians = np.radians(degrees)
        t = xs * np.cos(radians) + ys * np.sin(radians)
        residual = 0.0
        for c in range(3):
            fit = np.polyval(np.polyfit(t, rgb[:, c], 1), t)
            residual += (rgb[:, c] - fit).var() / max(rgb[:, c].var(), 1e-9)
        if best is None or residual < best[0]:
            best = (residual, degrees)

    radians = np.radians(best[1])
    t = xs * np.cos(radians) + ys * np.sin(radians)
    lo, hi = float(t.min()), float(t.max())
    ends = []
    for at in (lo, hi):
        ends.append(
            "#%02x%02x%02x"
            % tuple(
                int(round(min(255.0, max(0.0, np.polyval(np.polyfit(t, rgb[:, c], 1), at)))))
                for c in range(3)
            )
        )
    # Put the endpoints on the axis through the ink's centre.
    cx, cy = xs.mean(), ys.mean()
    mid = cx * np.cos(radians) + cy * np.sin(radians)
    axis = (
        cx + (lo - mid) * np.cos(radians),
        cy + (lo - mid) * np.sin(radians),
        cx + (hi - mid) * np.cos(radians),
        cy + (hi - mid) * np.sin(radians),
    )
    return axis, ends[0], ends[1]


def build_mark() -> tuple[str, str]:
    """The mark as (gradient definitions, drawing), in the PNG's own pixels."""
    png = np.asarray(Image.open(MARK).convert("RGBA"))
    alpha = png[..., 3] > 200
    labels, count = ndimage.label(alpha)

    defs, body = [], []
    for i in range(1, count + 1):
        mask = labels == i
        if mask.sum() < 200:
            continue
        ys, xs = np.nonzero(mask)
        crop = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        (x1, y1, x2, y2), warm, cool = gradient(png[..., :3], mask)
        name = f"u{i}"
        defs.append(
            f'<linearGradient id="{name}" gradientUnits="userSpaceOnUse"'
            f' x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}">'
            f'<stop offset="0" stop-color="{warm}"/>'
            f'<stop offset="1" stop-color="{cool}"/></linearGradient>'
        )
        body.append(f'<path fill="url(#{name})" d="{trace(crop, xs.min(), ys.min())}"/>')
    return "".join(defs), "".join(body)


# --- assembly -------------------------------------------------------------


def build() -> tuple[str, tuple[float, float, float]]:
    parts, defs = [], []

    # The name, on one gradient spanning the block, as the site's CSS does it.
    # The gradient's ends are given in the space the lines are drawn in - the
    # one inside their own translate - so that both lines, which sit in
    # separate groups at the same x, share one ramp across the whole block.
    lines, extent = [], []
    for text, baseline in zip(NAME_LINES, NAME_BASELINES):
        d, left, right = set_line(
            NAME_FONT, text, NAME_EM, NAME_TRACKING, NAME_WORD_EXTRA
        )
        lines.append((d, baseline))
        extent.append((left, right))
    x0 = min(a for a, _ in extent)
    x1 = max(b for _, b in extent)
    defs.append(
        f'<linearGradient id="name" gradientUnits="userSpaceOnUse"'
        f' x1="{fmt(x0)}" y1="0" x2="{fmt(x1)}" y2="0">'
        f'<stop offset="0" stop-color="{WARM}"/>'
        f'<stop offset="1" stop-color="{COOL}"/></linearGradient>'
    )
    for d, baseline in lines:
        parts.append(
            f'<g fill="url(#name)" transform="translate({fmt(NAME_LEFT)},{fmt(baseline)})">'
            f"{d}</g>"
        )

    mark_defs, mark_body = build_mark()
    defs.append(mark_defs)
    parts.append(
        f'<g transform="translate({fmt(MARK_X)},{fmt(MARK_Y)})'
        f' scale({MARK_SCALE:.6f})">{mark_body}</g>'
    )

    sante, sante_left, _ = set_line(
        SANTE_FONT, "SANTÉ", SANTE_EM, tracking=SANTE_TRACKING
    )
    parts.append(
        f'<g fill="{PURPLE}" transform="translate({fmt(SANTE_LEFT - sante_left)},'
        f'{fmt(SANTE_BASELINE)})">{sante}</g>'
    )

    body = f"<defs>{''.join(defs)}</defs>" + "".join(parts)
    return frame(body)


def frame(body: str) -> tuple[str, tuple[float, float, float]]:
    """Wrap the drawing in a viewBox that just contains it.

    Its own extent is what counts, not the screenshot's: the screenshot cuts
    the circumflex, the last "e", the left of the mark and the foot of the
    swoosh, and all four are back. Returns the SVG and where its top left sits
    in the screenshot, which is what the closing comparison needs.
    """
    # A generous window around the screenshot's own 512 x 312, rendered only
    # for its alpha - this renderer ignores the gradients, which does not
    # matter when all that is wanted is where the ink reaches.
    probe = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-40 -40 700 440">{body}</svg>'
    page = pymupdf.open(
        "pdf", pymupdf.open(stream=probe.encode(), filetype="svg").convert_to_pdf()
    )[0]
    zoom = 4.0
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    ink = (
        np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., -1]
        > 8
    )
    ys, xs = np.nonzero(ink)
    x0, y0 = -40 + xs.min() / zoom, -40 + ys.min() / zoom
    x1, y1 = -40 + (xs.max() + 1) / zoom, -40 + (ys.max() + 1) / zoom
    scale = TARGET / max(x1 - x0, y1 - y0)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {fmt((x1 - x0) * scale)} {fmt((y1 - y0) * scale)}">'
        f'<g transform="scale({fmt(scale)}) translate({fmt(-x0)},{fmt(-y0)})">'
        f"{body}</g></svg>\n"
    )
    return svg, (x0, y0, scale)


def coverage(rgb: np.ndarray) -> np.ndarray:
    """How far each pixel is from white, as a share of its own colour's."""
    return (1.0 - rgb / 255.0).max(axis=2)


def agreement(path: str, placement: tuple[float, float, float]) -> float:
    """How much of the screenshot the result covers, intersection over union.

    Rendered back at the screenshot's own scale and laid over it at the place
    the drawing was built from, so the pieces the screenshot crops fall outside
    the window rather than counting as misses. Slid by up to three pixels
    first: the screenshot is a JPEG and its thin strokes carry a pixel of
    fringe.
    """
    want = coverage(np.asarray(Image.open(SHOT).convert("RGB")).astype(np.float32)) > INK
    height, width = want.shape

    x0, y0, scale = placement
    page = pymupdf.open("pdf", pymupdf.open(path).convert_to_pdf())[0]
    zoom = 1.0 / scale
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    got = (
        coverage(
            np.frombuffer(pix.samples, np.uint8)
            .reshape(pix.height, pix.width, pix.n)[..., :3]
            .astype(np.float32)
        )
        > INK
    )

    best = 0.0
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            canvas = np.zeros_like(want)
            oy, ox = int(round(y0)) + dy, int(round(x0)) + dx
            src = got[max(0, -oy) :, max(0, -ox) :]
            rows = min(src.shape[0], height - max(oy, 0))
            cols = min(src.shape[1], width - max(ox, 0))
            if rows <= 0 or cols <= 0:
                continue
            canvas[max(oy, 0) : max(oy, 0) + rows, max(ox, 0) : max(ox, 0) + cols] = src[
                :rows, :cols
            ]
            best = max(best, float((canvas & want).sum()) / float((canvas | want).sum()))
    return best


def main() -> int:
    svg, placement = build()
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(svg)
    print(
        f"wrote {os.path.relpath(OUT, ROOT)}"
        f" ({len(svg) / 1024:.1f} KB, {svg.count('<path')} paths,"
        f" {svg.count('<linearGradient')} gradients,"
        f" {agreement(OUT, placement):.2f} overlap with the screenshot)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
