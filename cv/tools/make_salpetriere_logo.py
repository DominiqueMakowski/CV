"""Build img/logos/salpetriere.svg (+ -full.svg) from raw-salpetriere.webp.

The only asset available for the Pitie-Salpetriere is a 1080 px raster: one flat
navy on transparency, no official SVG. Embedding a bitmap in the CV would show
- the logo slot is vector everywhere else, and the PDF scales - so this
revectorises it.

A plain trace of the whole bitmap is not good enough. The artwork is mostly
axis-aligned rectangles a few pixels thick (the hatching, the windows, the
string courses), and at that size the raster's antialiasing leaves every edge
slightly crooked; potrace reproduces the crookedness faithfully, so thin rules
come out wavy and window tops tilted. Instead each connected component is
measured and matched against the shape it obviously is:

  rectangle  -> <rect>, sized from the alphas as an area (a pixel's alpha is
                how much of it the shape covers, so a row of alphas sums to the
                shape's width however its edges fall between pixels)
  arch       -> rectangle with a semicircular head, radius = half the width
  rule       -> <rect>, measured where the solid forms stop covering it
  the rest   -> potrace (the dome, the cupola, the roof band: large smooth
                forms, where a traced outline is both faithful and clean)

Nothing is idealised beyond that: every coordinate is measured off the raster,
so the output matches the original to a fraction of a pixel rather than being a
redrawing from the eye. Whatever a fitted shape does not account for stays in
the mask and is traced with the form it belongs to, so a misfit would show up
as a seam rather than as missing artwork.

    python tools/make_salpetriere_logo.py

Requires potracer (pip install potracer). The run prints how far the result is
from the raster, as a share of its ink: about 4%, which is what it costs to
have crisp edges where a raster downsampled to 1080 px has soft ones. Compared
row by row, the outlines agree to a fraction of a pixel.

Two files, as for NTU: the building alone, which is what a logo slot the size of
the CV's can show, and the full lockup with the name under it.
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

SRC = os.path.join(LOGOS, "raw-salpetriere.webp")
OUT_MARK = os.path.join(LOGOS, "salpetriere.svg")
OUT_FULL = os.path.join(LOGOS, "salpetriere-full.svg")

NAVY = "#233f7c"
TARGET = 400.0  # longest side of the output viewBox

# The building ends at the rule under the facade; the name sits below it.
MARK_BOTTOM = 800

# Right edge of the hatching. A band of rows inked here is one of its rules.
HATCH_X = 870

# A rule is at most this thick, so anything thicker is the artwork itself and
# must not be mistaken for one.
RULE_MAX_H = 10

# Vertical run length that separates a rule from the solid forms it crosses.
THIN = 9

# How closely a fitted rectangle or arch has to match the pixels to be accepted.
ARCH_IOU = 0.98

# A rule is at least this many pixels across in both directions; a two-pixel
# rectangular sliver is a corner of something larger, not a bar of its own.
RULE_MIN_DIM = 4

# Components this thin or this small are antialiasing residue - a half-covered
# row left over where a rule was lifted out - not artwork.
MIN_DIM, MIN_AREA = 2, 12

# Subsamples per pixel side when judging a curved candidate shape.
SUBSAMPLE = 4

# How far the antialiased fringe of an edge reaches, in pixels. Measurements
# include it; the raster was downsampled, so an edge fades over 2-3 pixels.
FRINGE = 3


# --- measuring ------------------------------------------------------------


def vertical_run(mask: np.ndarray) -> np.ndarray:
    """For each inked pixel, the height of the column segment it sits in."""
    up = np.zeros(mask.shape, np.int32)
    down = np.zeros(mask.shape, np.int32)
    for y in range(mask.shape[0]):
        up[y] = np.where(mask[y], (up[y - 1] if y else 0) + 1, 0)
    for y in range(mask.shape[0] - 1, -1, -1):
        down[y] = np.where(mask[y], (down[y + 1] if y < mask.shape[0] - 1 else 0) + 1, 0)
    return np.where(mask, up + down - 1, 0)


def run_start(row: np.ndarray, x: int) -> int:
    """Left end of the inked run in `row` that contains column x."""
    s = x
    while s and row[s - 1]:
        s -= 1
    return s


def bands(column: np.ndarray) -> list[tuple[int, int]]:
    """Maximal runs of True in a boolean column, as (first, last) rows."""
    out, start = [], None
    for y, v in enumerate(column):
        if v and start is None:
            start = y
        elif not v and start is not None:
            out.append((start, y - 1))
            start = None
    if start is not None:
        out.append((start, len(column) - 1))
    return out


def plateau(profile: np.ndarray) -> float:
    """The level a blurred rectangle's row (or column) sums settle at."""
    top = profile[profile >= 0.97 * profile.max()]
    return float(np.median(top))


def fit_rect(alpha: np.ndarray) -> tuple[float, float, float, float]:
    """Subpixel (x0, y0, x1, y1) of the rectangle these alphas describe.

    A pixel's alpha is how much of it the artwork covers, so the alphas are an
    area measure. Summing along a row of a rectangle therefore gives its width
    wherever the row is inside it, and summing down a column its height; the
    centroid gives the centre. This needs the antialiased fringe as well as the
    solid pixels - measuring a thresholded shape alone loses the half-pixel at
    each edge - and it has to be area rather than spread, because the raster
    was downsampled and a blurred edge is wider than the edge it came from.
    """
    ys, xs = np.nonzero(alpha)
    w = alpha[ys, xs]
    total = w.sum()
    cx = ((xs + 0.5) * w).sum() / total
    cy = ((ys + 0.5) * w).sum() / total
    width = plateau(alpha.sum(axis=1))
    height = plateau(alpha.sum(axis=0))
    return cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2


def iou(model: np.ndarray, mask: np.ndarray) -> float:
    return float((model & mask).sum()) / float((model | mask).sum())


def hatch_rules(alpha: np.ndarray, ink: np.ndarray, runs: np.ndarray) -> list[dict]:
    """The horizontal rules, as subpixel rectangles.

    The hatching runs behind the dome, so a rule's left end is wherever the
    solid artwork stops covering it. Taking the innermost of its rows' run
    starts keeps the rectangle inside the inked area: the sliver it gives up
    stays in the mask and is drawn with the form it belongs to.
    """
    out = []
    for y0, y1 in bands(ink[:, HATCH_X]):
        if y1 - y0 + 1 > RULE_MAX_H:  # the roof band crosses the hatching too
            continue
        rows = slice(y0, y1 + 1)
        core = [y for y in range(y0, y1 + 1) if alpha[y, HATCH_X] >= 0.9]
        left = max(run_start(ink[y], HATCH_X) for y in core)

        # Thickness and centre off the alpha profile, in a column where the
        # rule is the only thing present. The window has to clear the whole
        # antialiased fringe or the rule comes out too thin.
        top, bottom = y0 - FRINGE, y1 + 1 + FRINGE
        profile = alpha[top:bottom, HATCH_X]
        ys = np.arange(top, bottom) + 0.5
        thick = float(profile.sum())
        centre = float((ys * profile).sum()) / thick

        # Same idea horizontally: coverage per column, summed, is the length.
        cover = alpha[top:bottom, 850:910].sum(axis=0) / thick
        right = 850.0 + float(cover.sum())
        if alpha[rows, left - 1].max() < 0.05:  # left end out in the open
            fringe = alpha[top:bottom, left - FRINGE : left + 1].sum(axis=0) / thick
            left += 1 - float(fringe.sum())

        out.append(
            dict(
                x0=float(left),
                y0=centre - thick / 2,
                x1=right,
                y1=centre + thick / 2,
                rows=(y0, y1),
                cut=int(np.ceil(left)),
            )
        )
    return out


# --- shapes ---------------------------------------------------------------


def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Canvas:
    """Source pixels to viewBox units."""

    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self.x0, self.y0 = x0, y0
        self.scale = TARGET / max(x1 - x0, y1 - y0)
        self.width = (x1 - x0) * self.scale
        self.height = (y1 - y0) * self.scale

    def x(self, v: float) -> float:
        return (v - self.x0) * self.scale

    def y(self, v: float) -> float:
        return (v - self.y0) * self.scale

    def d(self, v: float) -> float:
        return v * self.scale


def svg_rect(c: Canvas, x0: float, y0: float, x1: float, y1: float) -> str:
    return (
        f'<rect x="{fmt(c.x(x0))}" y="{fmt(c.y(y0))}"'
        f' width="{fmt(c.d(x1 - x0))}" height="{fmt(c.d(y1 - y0))}"/>'
    )


def arch_model(alpha: np.ndarray) -> tuple[float, float, float, float] | None:
    """Fit a rectangle with a semicircular head; (x0, y0, x1, y1) or None.

    The flanks give the width, so the head's radius is half of it. Height comes
    from the columns down the middle, which run the full shape: their alpha sums
    to the height and its centroid sits halfway down it.
    """
    rowsum = alpha.sum(axis=1)
    if not rowsum.any():
        return None
    width = plateau(rowsum)
    flank = np.nonzero(rowsum >= 0.98 * width)[0]
    if len(flank) < 4 or width < 4:
        return None
    x0, _, x1, _ = fit_rect(alpha[flank[0] : flank[-1] + 1])
    radius = (x1 - x0) / 2

    middle = alpha[:, int(round((x0 + x1) / 2 - 1)) : int(round((x0 + x1) / 2 + 2))]
    ys = np.arange(alpha.shape[0])[:, None] + 0.5
    height = middle.sum(axis=0).mean()
    centre = float((ys * middle).sum() / middle.sum())
    top, bottom = centre - height / 2, centre + height / 2
    if height <= radius or radius < 2:
        return None
    return x0, top, x1, bottom


def looks_rect(mask: np.ndarray) -> bool:
    """Is this thresholded component a filled rectangle?

    Judged on whole pixels, not on the subpixel fit: a rule five pixels thick
    sits half a pixel proud of its own inked rows, and comparing it with its
    own fit would turn that half pixel into a whole row of disagreement.
    """
    ys, xs = np.nonzero(mask)
    mask = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    height, width = mask.shape

    def inner(counts: np.ndarray) -> np.ndarray:
        """Drop the first and last, which are the partly covered edges."""
        return counts[1:-1] if len(counts) > 2 else counts

    return bool(
        (inner(mask.sum(axis=1)) >= width - 1).all()
        and (inner(mask.sum(axis=0)) >= height - 1).all()
    )


def rect_cover(shape: tuple[int, int], box: tuple[float, float, float, float]) -> np.ndarray:
    """Per-pixel coverage of an axis-aligned rectangle."""
    x0, y0, x1, y1 = box
    xs = np.arange(shape[1])
    ys = np.arange(shape[0])
    return np.outer(
        np.clip(np.minimum(y1, ys + 1) - np.maximum(y0, ys), 0, 1),
        np.clip(np.minimum(x1, xs + 1) - np.maximum(x0, xs), 0, 1),
    )


def arch_cover(shape: tuple[int, int], box: tuple[float, float, float, float]) -> np.ndarray:
    """Same for a rectangle with a semicircular head, by supersampling."""
    x0, y0, x1, y1 = box
    radius = (x1 - x0) / 2
    cx, cy = (x0 + x1) / 2, y0 + radius
    step = 1.0 / SUBSAMPLE
    offsets = (np.arange(SUBSAMPLE) + 0.5) * step
    ys = (np.arange(shape[0])[:, None] + offsets).ravel()
    xs = (np.arange(shape[1])[:, None] + offsets).ravel()
    gx, gy = np.meshgrid(xs, ys)
    body = (gx >= x0) & (gx <= x1) & (gy >= cy) & (gy <= y1)
    head = ((gx - cx) ** 2 + (gy - cy) ** 2 <= radius**2) & (gy < cy)
    fine = (body | head).astype(np.float32)
    return fine.reshape(shape[0], SUBSAMPLE, shape[1], SUBSAMPLE).mean(axis=(1, 3))


def svg_arch(c: Canvas, box: tuple[float, float, float, float]) -> str:
    x0, y0, x1, y1 = box
    r = c.d((x1 - x0) / 2)
    return (
        f'<path d="M{fmt(c.x(x0))} {fmt(c.y(y1))}'
        f"V{fmt(c.y(y0) + r)}"
        f"A{fmt(r)} {fmt(r)} 0 0 1 {fmt(c.x(x1))} {fmt(c.y(y0) + r)}"
        f"V{fmt(c.y(y1))}Z\"/>"
    )


def trace(mask: np.ndarray, c: Canvas, ox: int, oy: int) -> str:
    """potrace outline of a component, as an SVG path."""
    path = potrace.Bitmap(~np.pad(mask, 1)).trace(turdsize=2, opttolerance=0.2)

    def point(p) -> tuple[str, str]:
        return fmt(c.x(ox - 1 + p.x)), fmt(c.y(oy - 1 + p.y))

    d = []
    for curve in path:
        x, y = point(curve.start_point)
        d.append(f"M{x} {y}")
        for seg in curve:
            if seg.is_corner:
                cx, cy = point(seg.c)
                ex, ey = point(seg.end_point)
                d.append(f"L{cx} {cy}L{ex} {ey}")
            else:
                a1, b1 = point(seg.c1)
                a2, b2 = point(seg.c2)
                ex, ey = point(seg.end_point)
                d.append(f"C{a1} {b1} {a2} {b2} {ex} {ey}")
        d.append("Z")
    return f'<path d="{"".join(d)}"/>'


# --- assembly -------------------------------------------------------------


def components(mask: np.ndarray, alpha: np.ndarray, ink: np.ndarray):
    """Each component of `mask`, with its alphas and the fringe around them.

    Unclaimed pixels next to a component are its antialiased fringe and belong
    in its measurements; a neighbour's own pixels do not.
    """
    labels, _ = ndimage.label(mask, structure=np.ones((3, 3)))
    for index, box in enumerate(ndimage.find_objects(labels), 1):
        if min(labels[box].shape) < MIN_DIM or (labels[box] == index).sum() < MIN_AREA:
            continue
        rows = slice(max(0, box[0].start - FRINGE), box[0].stop + FRINGE)
        cols = slice(max(0, box[1].start - FRINGE), box[1].stop + FRINGE)
        shape = labels[rows, cols] == index
        patch = np.where(shape | ~ink[rows, cols], alpha[rows, cols], 0.0)
        patch[~ndimage.binary_dilation(shape, iterations=FRINGE)] = 0.0
        yield shape, patch, cols.start, rows.start


def decompose(alpha: np.ndarray, top: int, bottom: int) -> tuple[list, tuple]:
    """Shapes for rows [top, bottom), as (kind, payload) plus the ink bounds."""
    ink = alpha > 0.5
    shapes: list[tuple] = []

    rest = ink.copy()
    rest[:top] = False
    rest[bottom:] = False

    # The hatching first: its rules run behind the dome and the roof, so they
    # have to be measured before anything is labelled. Each rule gives up the
    # pixels its rectangle does not cover - the sliver where the dome's edge
    # slants across it - and those stay in the mask, to be drawn with the dome.
    if top == 0:
        runs = vertical_run(ink)
        for rule in hatch_rules(alpha, ink, runs):
            box = (rule["x0"], rule["y0"], rule["x1"], rule["y1"])
            shapes.append(("rect", box))
            y0, y1 = rule["rows"]
            x0, x1 = int(box[0]), int(np.ceil(box[2]))
            covered = np.zeros((y1 + 1 - y0, ink.shape[1]), bool)
            covered[:, x0 : x1 + 1] = (
                rect_cover(
                    (y1 + 1 - y0, x1 + 1 - x0),
                    (box[0] - x0, box[1] - y0, box[2] - x0, box[3] - y0),
                )
                > 0.5
            )
            rest[y0 : y1 + 1] &= ~((runs[y0 : y1 + 1] <= THIN) & covered)

    # Then the rules across the facade, which are clear of the solid forms
    # except where one runs into an arch: a thin bar joined to a solid form -
    # the plinth ears either side of each arch - is a bar, not part of it.
    runs = vertical_run(rest)
    thin = rest & (runs <= THIN)
    for shape, patch, ox, oy in components(thin, alpha, ink):
        ys, xs = np.nonzero(shape)
        if min(np.ptp(ys), np.ptp(xs)) + 1 < RULE_MIN_DIM or not looks_rect(shape):
            continue
        x0, y0, x1, y1 = fit_rect(patch)
        shapes.append(("rect", (x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
        rest[oy : oy + shape.shape[0], ox : ox + shape.shape[1]] &= ~shape

    for shape, patch, ox, oy in components(rest, alpha, ink):
        if looks_rect(shape):
            x0, y0, x1, y1 = fit_rect(patch)
            shapes.append(("rect", (x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
            continue

        arch = arch_model(patch)
        if arch and iou(arch_cover(shape.shape, arch) > 0.5, shape) >= ARCH_IOU:
            shapes.append(
                ("arch", (arch[0] + ox, arch[1] + oy, arch[2] + ox, arch[3] + oy))
            )
            continue

        shapes.append(("trace", (shape, ox, oy)))

    ys, xs = np.nonzero(ink[top:bottom])
    bounds = (
        float(xs.min()),
        float(ys.min() + top),
        float(xs.max() + 1),
        float(ys.max() + 1 + top),
    )
    return shapes, bounds


def render(shapes: list[tuple], bounds: tuple) -> str:
    c = Canvas(*bounds)
    body = []
    for kind, payload in shapes:
        if kind == "rect":
            body.append(svg_rect(c, *payload))
        elif kind == "arch":
            body.append(svg_arch(c, payload))
        else:
            body.append(trace(payload[0], c, payload[1], payload[2]))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {fmt(c.width)} {fmt(c.height)}">'
        f'<g fill="{NAVY}">' + "".join(body) + "</g></svg>\n"
    )


def fidelity(svg_path: str, alpha: np.ndarray, bounds: tuple) -> float:
    """How far the rebuilt SVG is from the raster, as a fraction of its ink.

    Rendered back at the raster's own scale and compared as coverage rather
    than as thresholded pixels: a shape measured to half a pixel is right even
    though thresholding puts a whole row on one side or the other.
    """
    x0, y0, x1, y1 = (int(round(v)) for v in bounds)
    page = pymupdf.open("pdf", pymupdf.open(svg_path).convert_to_pdf())[0]
    zoom = pymupdf.Matrix((x1 - x0) / page.rect.width, (y1 - y0) / page.rect.height)
    pix = page.get_pixmap(matrix=zoom, alpha=True)
    got = (
        np.frombuffer(pix.samples, np.uint8)
        .reshape(pix.height, pix.width, pix.n)[..., -1]
        .astype(np.float32)
        / 255.0
    )
    want = alpha[y0:y1, x0:x1]
    h, w = min(got.shape[0], want.shape[0]), min(got.shape[1], want.shape[1])
    got, want = got[:h, :w], want[:h, :w]
    return float(np.abs(got - want).sum() / want.sum())


def main() -> int:
    alpha = np.array(Image.open(SRC))[..., 3].astype(np.float32) / 255.0

    mark, mark_box = decompose(alpha, 0, MARK_BOTTOM)
    word, word_box = decompose(alpha, MARK_BOTTOM, alpha.shape[0])
    full_box = (
        min(mark_box[0], word_box[0]),
        mark_box[1],
        max(mark_box[2], word_box[2]),
        word_box[3],
    )

    for path, shapes, box in (
        (OUT_MARK, mark, mark_box),
        (OUT_FULL, mark + word, full_box),
    ):
        svg = render(shapes, box)
        io.open(path, "w", encoding="utf-8", newline="\n").write(svg)
        print(
            f"wrote {os.path.relpath(path, ROOT)}"
            f" ({len(svg) / 1024:.1f} KB, {len(shapes)} shapes,"
            f" {fidelity(path, alpha, box) * 100:.2f}% off the raster)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
