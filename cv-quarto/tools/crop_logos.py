"""Tighten the viewBox of img/logos/*.svg to the artwork it actually contains.

Brand SVGs usually ship with clear space baked into the canvas. Inside a fixed
logo slot that padding is dead area: the mark renders smaller than its
neighbours and sits off-centre against the text. Cropping the viewBox to the
drawn bounds makes every logo fill its slot the same way, without touching the
artwork.

    python tools/crop_logos.py           # report what would change
    python tools/crop_logos.py --apply   # rewrite the files

The originals are copies of the lab website's assets
(RealityBending.github.io/people/dominique-makowski/assets/), so re-copying from
there undoes this.
"""

from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys

import pymupdf

from cvdata import LOGOS

# A hair of breathing room so anti-aliasing and stroke ends are not clipped.
PAD = 0.01  # fraction of the larger dimension

VIEWBOX_RE = re.compile(r'viewBox\s*=\s*"([^"]+)"')
SIZE_RE = re.compile(r'\s(width|height)\s*=\s*"[^"]*"')


def content_bounds(path: str) -> pymupdf.Rect | None:
    page = pymupdf.open(path)[0]
    rect = None
    for d in page.get_drawings():
        rect = d["rect"] if rect is None else (rect | d["rect"])
    # Images and text inside the SVG are not drawings; fall back to everything.
    for block in page.get_text("dict")["blocks"]:
        r = pymupdf.Rect(block["bbox"])
        rect = r if rect is None else (rect | r)
    return rect


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="rewrite the files")
    args = ap.parse_args()

    changed = 0
    for path in sorted(glob.glob(os.path.join(LOGOS, "*.svg"))):
        name = os.path.basename(path)
        src = io.open(path, encoding="utf-8").read()
        m = VIEWBOX_RE.search(src)
        if not m:
            print(f"  {name:24s} no viewBox, skipped")
            continue

        page = pymupdf.open(path)[0].rect
        box = content_bounds(path)
        if box is None or box.is_empty:
            print(f"  {name:24s} no content found, skipped")
            continue

        pad = PAD * max(box.width, box.height)
        x0, y0 = max(0.0, box.x0 - pad), max(0.0, box.y0 - pad)
        x1 = min(page.width, box.x1 + pad)
        y1 = min(page.height, box.y1 + pad)
        gain = (page.width * page.height) / max(1e-9, (x1 - x0) * (y1 - y0))

        if gain < 1.02:
            print(f"  {name:24s} already tight")
            continue

        new = f'viewBox="{x0:.2f} {y0:.2f} {x1 - x0:.2f} {y1 - y0:.2f}"'
        print(f"  {name:24s} {m.group(0)[:38]:40s} -> {new}   (+{(gain - 1) * 100:.0f}% area)")

        if args.apply:
            out = src[: m.start()] + new + src[m.end() :]
            # A stale width/height would fight the new viewBox.
            head_end = out.find(">", out.find("<svg"))
            out = out[:head_end].replace(" width=", " data-width=").replace(
                " height=", " data-height="
            ) + out[head_end:]
            io.open(path, "w", encoding="utf-8", newline="\n").write(out)
        changed += 1

    if not args.apply and changed:
        print(f"\n{changed} file(s) would change. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
