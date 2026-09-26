"""Render img/logos/*.svg to transparent PNGs beside them, for the CV to embed.

The SVGs stay the source; the PNGs are what content/*.yml points at. Several
logos are traced artwork - hundreds of small abutting paths - and PDF viewers
anti-alias each path on its own, so at some zoom levels hairline seams and
ragged edges show between shapes. A raster has no seams. At 1,200 px on the
long side a 44pt logo is embedded at roughly 2,000 ppi, well past what print
or any ordinary on-screen zoom can resolve.

Rendering goes through Typst (the copy bundled with Quarto), the same SVG
engine the PDF is built with, so the PNG is drawn the way the SVG was.

    python tools/rasterize_logos.py          # render missing or stale PNGs
    python tools/rasterize_logos.py --force  # re-render all of them

`raw-*` files are upstream material for the make_*_logo.py scripts, not logos
the CV uses, and are skipped.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from cvdata import LOGOS

LONG_SIDE_PX = 1200
PPI = 1200  # the page is sized so that LONG_SIDE_PX / PPI inches is the long side

TEMPLATE = """#let img = image("{svg}")
#set page(width: auto, height: auto, margin: 0pt, fill: none)
#context {{
  let s = measure(img)
  let k = {side}in / calc.max(s.width, s.height)
  image("{svg}", width: s.width * k, height: s.height * k)
}}
"""


def typst() -> list[str]:
    if shutil.which("typst"):
        return ["typst"]
    if shutil.which("quarto"):
        return ["quarto", "typst"]
    sys.exit("neither typst nor quarto is on PATH")


def render(svg: str, png: str, cmd: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "logo.svg")
        shutil.copyfile(svg, src)
        doc = os.path.join(tmp, "logo.typ")
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write(TEMPLATE.format(svg="logo.svg", side=LONG_SIDE_PX / PPI))
        out = os.path.join(tmp, "logo.png")
        subprocess.run(
            cmd + ["compile", "--ppi", str(PPI), doc, out],
            check=True, capture_output=True, text=True,
        )
        shutil.move(out, png)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cmd = typst()
    for svg in sorted(glob.glob(os.path.join(LOGOS, "*.svg"))):
        name = os.path.basename(svg)
        if name.startswith("raw-"):
            continue
        png = svg[:-4] + ".png"
        if not args.force and os.path.exists(png) and os.path.getmtime(png) >= os.path.getmtime(svg):
            continue
        try:
            render(svg, png, cmd)
        except subprocess.CalledProcessError as e:
            print(f"{name}: {e.stderr.strip()}", file=sys.stderr)
            return 1
        print(f"{name} -> {os.path.basename(png)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
