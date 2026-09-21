"""Build img/logos/sainte-anne2.svg from the GHU's own vector artwork.

img/logos/raw-sainte-anne2.jpg is a 200 px avatar of the current Sainte-Anne
logo: the GHU Paris mark stacked over the name, with the site line under it.
It is clipped at the top (the crown of the canopy) and at the bottom (the
baseline of "Sainte-Anne"), and its strapline is ten pixels tall, so tracing it
would give mush.

The GHU publishes the same artwork as a vector - img/logos/raw-ghu-footer.svg,
the horizontal lockup from the foot of ghu-paris.fr - so nothing here is
traced. That file is drawn for a dark footer: 42 dots in the house colours,
plus one white path carrying the swoosh and all three lines of the name. The
path splits at its movetos into 43 subpaths, which sort by position into the
swoosh and the three lines, and each group is then placed on its own. The path
data itself is copied across character for character: the dots are a few
percent off being true circles and are left that way, because the source is
already vector and rounding it off would add error where there was none.

Only the arrangement changes, and it is measured rather than guessed. The
stacked lockup exists as a 425 px PNG (fr.wikipedia.org, "Ght paris psychiatrie
& neurosciences.png"), cropped flush on every side but clean in between, and
the avatar has margins left and right but not top and bottom. So the vertical
spacings are fitted to the PNG and the horizontal ones to the avatar, each
where it is not clipped, by sliding the real artwork over the reference and
maximising overlap. What comes out:

  - the three lines keep the sizes, tracking and left edges they have in the
    footer file; only the leading changes, the strapline pulling up under GHU
    PARIS from 30.0 units of baseline pitch to 21.3 (the gap between the two
    strapline lines, one typeset pair, is unchanged)
  - the mark is set to the width of GHU PARIS, aligned with its left edge.
    Fitting its scale freely gives 1.7245 against the PNG and 1.7500 against
    the avatar; equal widths means 1.7375, between the two and within the
    measurement error of both, so the rule is used rather than either figure
  - the mark's lowest dot sits 32.3 units above the GHU PARIS baseline - 32.31
    measured on the PNG, 32.1 on the avatar

Colours are read off the GHU's own header PNG, which is the logo on white:
navy #004f8b for the swoosh and GHU PARIS, grey #8b8d8e for the strapline, and
the five dot colours, which match the ones already in the footer file.

One line is not official artwork. "Sainte-Anne" appears only in the avatar,
eleven pixels tall and cut off by the bottom edge, and the GHU serves no vector
of it. It is set in Noto Sans SemiBold - the best of the faces tried against
those eleven pixels, and within a pixel of the measured width - at the size and
position fitted to the avatar. Everything above it is the GHU's own.

    python tools/make_ghu_logo.py

Requires svgpathtools (pip install svgpathtools), for measuring where a subpath
sits without rendering it. The run prints how far the result overlaps the avatar, as intersection over
union of the two ink masks at the avatar's own 155 px. About 0.75, which is
what a sharp drawing scores against a 200 px JPEG whose dots are three pixels
across: sweeping the scale shows the peak within 1.3% of the size used here.
"""

from __future__ import annotations

import io
import os
import re
import sys

import numpy as np
import pymupdf
from PIL import Image
from svgpathtools import parse_path

from cvdata import LOGOS, ROOT
from svgtext import fmt, set_line

SRC = os.path.join(LOGOS, "raw-ghu-footer.svg")
AVATAR = os.path.join(LOGOS, "raw-sainte-anne2.jpg")
FONT = "NotoSans-SemiBold.subset.ttf"
OUT = os.path.join(LOGOS, "sainte-anne2.svg")

NAVY = "#004f8b"
GREY = "#8b8d8e"
TARGET = 400.0  # longest side of the output viewBox


# --- the source file ------------------------------------------------------

# Where the four parts of the white path sit in it. The swoosh is the only
# subpath left of the name; the three lines then separate by height.
SWOOSH_X = 100.0
GHU_BOTTOM, PSY_BOTTOM = 30.0, 56.0

# Baselines of the three lines in the footer file, taken as the foot of the
# letters that end flat (the round ones overshoot, the ampersand rises).
BASE = {"ghu": 22.2, "psy": 52.2, "neuro": 71.8}


# --- the stacked arrangement, in footer units -----------------------------

# Baseline pitch. The first is measured on the stacked PNG; the second is the
# footer file's own, which the fit reproduces to within a pixel.
GHU_TO_PSY, PSY_TO_NEURO = 21.26, 19.60

# The mark is as wide as GHU PARIS and shares its left edge; its lowest dot
# sits this far above the GHU PARIS baseline.
MARK_LIFT = 32.31

# "Sainte-Anne", fitted to the avatar and converted to footer units at the
# avatar's own scale of 0.920 px per unit: 14.00 px of em, its left edge 1.00
# px right of GHU PARIS's, its baseline 52.37 px below the GHU PARIS baseline.
ANNE_EM = 14.00 / 0.920
ANNE_X = 1.00 / 0.920
ANNE_BASE = 52.37 / 0.920


# --- reading the source ---------------------------------------------------

CMD = re.compile(r"([MmZzLlHhVvCcSsQqTtAa])([^MmZzLlHhVvCcSsQqTtAa]*)")
NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")

# How many numbers each path command takes per repeat.
ARITY = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}


def split_subpaths(d: str) -> list[str]:
    """The path's subpaths, each starting with an absolute moveto.

    The source mixes absolute and relative commands, so a subpath opened with
    a relative `m` only makes sense after the ones before it. Everything after
    that first moveto is self-contained, so it is carried over verbatim and
    only the moveto is rewritten - which keeps the artwork byte for byte what
    the GHU drew, rather than a re-serialisation of it.
    """
    out: list[str] = []
    x = y = sx = sy = 0.0
    for cmd, args in CMD.findall(d):
        low = cmd.lower()
        rel = cmd.islower()
        nums = [float(v) for v in NUM.findall(args)]
        step = ARITY[low]

        if low == "m":
            mx, my = (x + nums[0], y + nums[1]) if rel else (nums[0], nums[1])
            # everything after the first coordinate pair is an implicit lineto
            tail = NUM.findall(args)[2:]
            piece = f"M{fmt(mx)},{fmt(my)}"
            if tail:
                piece += ("l" if rel else "L") + ",".join(tail)
            out.append(piece)
            x, y = mx, my
            for i in range(2, len(nums), 2):
                x, y = (x + nums[i], y + nums[i + 1]) if rel else (nums[i], nums[i + 1])
            sx, sy = mx, my
            continue

        out[-1] += cmd + args
        if low == "z":
            x, y = sx, sy
        else:
            for i in range(0, len(nums), step):
                chunk = nums[i : i + step]
                if low == "h":
                    x = x + chunk[0] if rel else chunk[0]
                elif low == "v":
                    y = y + chunk[0] if rel else chunk[0]
                else:
                    ex, ey = chunk[-2], chunk[-1]
                    x, y = (x + ex, y + ey) if rel else (ex, ey)
    return out


def bbox(pieces: list[str]) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of these subpaths, via a render-free path parse."""
    boxes = [parse_path(p).bbox() for p in pieces]
    return (
        min(b[0] for b in boxes),
        min(b[2] for b in boxes),
        max(b[1] for b in boxes),
        max(b[3] for b in boxes),
    )


def read_source() -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """The white path's four groups, and the dots as (path data, colour)."""
    svg = io.open(SRC, encoding="utf-8").read()
    paths = re.findall(r'<path d="([^"]*)" fill="([^"]*)"/>', svg)
    white = [(d, f) for d, f in paths if f == "#fff"]
    dots = [(d, f) for d, f in paths if f != "#fff"]
    if len(white) != 1:
        raise SystemExit(f"{SRC}: expected one white path, found {len(white)}")

    groups: dict[str, list[str]] = {"swoosh": [], "ghu": [], "psy": [], "neuro": []}
    for piece in split_subpaths(white[0][0]):
        if re.fullmatch(r"M[-\d.,]+[Zz]?", piece):
            continue  # the source holds one moveto that draws nothing
        x0, y0, x1, y1 = bbox([piece])
        if x0 < SWOOSH_X:
            groups["swoosh"].append(piece)
        elif y1 < GHU_BOTTOM:
            groups["ghu"].append(piece)
        elif y1 < PSY_BOTTOM:
            groups["psy"].append(piece)
        else:
            groups["neuro"].append(piece)
    return groups, dots


# --- assembly -------------------------------------------------------------


def group(body: str, fill: str, tx: float, ty: float) -> str:
    move = f' transform="translate({fmt(tx)},{fmt(ty)})"' if (tx or ty) else ""
    return f'<g fill="{fill}"{move}>{body}</g>'


def build() -> str:
    groups, dots = read_source()
    gx0, _, gx1, _ = bbox(groups["ghu"])
    ghu_w = gx1 - gx0
    mx0, my0, mx1, my1 = bbox(groups["swoosh"] + [d for d, _ in dots])
    mark_s = ghu_w / (mx1 - mx0)

    # Place everything in footer units, GHU PARIS's baseline-left as the origin.
    px0 = bbox(groups["psy"])[0]
    lines = [
        ("ghu", NAVY, 0.0, 0.0),
        ("psy", GREY, px0 - gx0, GHU_TO_PSY),
        ("neuro", GREY, px0 - gx0, GHU_TO_PSY + PSY_TO_NEURO),
    ]
    parts = []
    for name, fill, dx, dy in lines:
        # One path per line, not one per subpath: a letter's counter is a
        # subpath wound against its outline, and it only knocks a hole in it
        # while the two share a path element.
        body = f'<path d="{"".join(groups[name])}"/>'
        parts.append(group(body, fill, dx - gx0, dy - BASE[name]))

    by_colour: dict[str, list[str]] = {}
    for d, colour in dots:
        by_colour.setdefault(colour, []).append(d)
    mark = f'<path fill="{NAVY}" d="{groups["swoosh"][0]}"/>'
    for colour, ds in by_colour.items():
        mark += f'<g fill="{colour}">' + "".join(f'<path d="{d}"/>' for d in ds) + "</g>"
    parts.append(
        f'<g transform="translate({fmt(-mx0 * mark_s)},'
        f'{fmt(-MARK_LIFT - my1 * mark_s)}) scale({fmt(mark_s)})">{mark}</g>'
    )

    anne, anne_left, _ = set_line(FONT, "Sainte-Anne", ANNE_EM)
    parts.append(group(anne, NAVY, ANNE_X - anne_left, ANNE_BASE))

    # The drawing now runs from the top of the mark to the Sainte-Anne baseline.
    x0, y0 = 0.0, -MARK_LIFT - (my1 - my0) * mark_s
    x1, y1 = ghu_w, ANNE_BASE
    scale = TARGET / max(x1 - x0, y1 - y0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {fmt((x1 - x0) * scale)} {fmt((y1 - y0) * scale)}">'
        f'<g transform="scale({fmt(scale)}) translate({fmt(-x0)},{fmt(-y0)})">'
        + "".join(parts)
        + "</g></svg>\n"
    )


def coverage(rgb: np.ndarray) -> np.ndarray:
    """How far each pixel is from white, as a share of its own colour's.

    The artwork is coloured, so ink cannot be read off one channel: a yellow
    dot is white in red and green. Taking the largest per-channel shortfall
    gives 1 inside any of the colours and 0 on the paper, which is what has to
    be compared.
    """
    return (1.0 - rgb / 255.0).max(axis=2)


INK = 0.3  # a pixel counts as inked once it is this far from white


def agreement(path: str) -> float:
    """How much of the avatar the result covers, as intersection over union.

    Rendered back at the avatar's own scale - 155 px across the logo box, laid
    on white - and compared over the avatar's own window, so the crown of the
    canopy that the avatar cuts off is left out rather than counted as a miss.
    The two are slid over each other by up to three pixels first, because the
    avatar is a small JPEG and its edges are soft.

    Ink is compared as a mask rather than as coverage: the avatar's colours are
    washed out by the JPEG - its yellow reads a fifth short of #ffc900 - so
    comparing coverage would charge that to the geometry. Expect about 0.75.
    Every dot here is three or four pixels across at this scale, so most of
    what is left is the width of one soft edge.
    """
    want = coverage(np.asarray(Image.open(AVATAR).convert("RGB")).astype(np.float32)) > INK
    height, width = want.shape

    page = pymupdf.open("pdf", pymupdf.open(path).convert_to_pdf())[0]
    zoom = (177.0 - 22.0) / page.rect.width
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
            # the drawing's bottom left meets the avatar's (22, 200)
            top, left = 200 + dy - got.shape[0], 22 + dx
            src = got[max(0, -top) :, : width - left]
            rows = min(src.shape[0], height - max(top, 0))
            canvas[max(top, 0) : max(top, 0) + rows, left : left + src.shape[1]] = src[:rows]
            best = max(best, float((canvas & want).sum()) / float((canvas | want).sum()))
    return best


def main() -> int:
    svg = build()
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(svg)
    print(
        f"wrote {os.path.relpath(OUT, ROOT)}"
        f" ({len(svg) / 1024:.1f} KB, {svg.count('<path')} paths,"
        f" {agreement(OUT):.2f} overlap with the avatar)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
