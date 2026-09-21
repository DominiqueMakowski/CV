"""Draw the Research Impact plot from content/impact.yml.

    python tools/make_impact.py        # -> img/impact.svg

A port of `plot_impact()` from the LaTeX CV's functions.R, which faceted
publications and citations from one ggplot. Two differences, both deliberate:

- Per year, not cumulative. The original plotted a running total, which only
  ever goes up and so says the same thing whatever the underlying year was
  like. Per-year bars show the shape of the record, which is the interesting
  part: the citation column roughly doubles every two years.
- The part-year bar is drawn faded and labelled. A snapshot taken in June makes
  the current year look like a collapse, and a reader who does not know the
  snapshot date has no way to tell that from a real one.

Text is converted to paths, so the file renders identically in Typst and in a
browser without either needing the font. The numbers are all repeated in the
bullets beneath the plot, so nothing is only in the picture.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from matplotlib import font_manager

from cvdata import ROOT, load

# The same fonts the PDF is set in, so the plot is not the one thing on the page
# in a different typeface. They are bundled, so this does not depend on what is
# installed.
for _f in glob.glob(os.path.join(ROOT, "fonts", "SourceSans3-*")):
    font_manager.fontManager.addfont(_f)

ACCENT = "#1976d2"
# The accent mixed 35% into white, rather than the accent at 35% alpha: alpha
# survives into the SVG as a compositing rule, and Typst and the browser do not
# resolve it the same way against a transparent background.
ACCENT_FADED = "#aecfef"
GRAY = "#8a8a8a"

# Mid-grey text and a transparent background, because the page behind this is
# white in the PDF and either white or near-black in the browser.
matplotlib.rcParams.update({
    "svg.fonttype": "path",
    "font.family": "sans-serif",
    "font.sans-serif": ["Source Sans 3", "Source Sans Pro", "DejaVu Sans"],
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "savefig.facecolor": "none",
})


def panel(ax, years, values, title, total, partial):
    colours = [ACCENT_FADED if y == partial else ACCENT for y in years]
    ax.bar(years, values, width=0.68, color=colours, linewidth=0)

    ax.set_title(
        f"{title}   {total:,}",
        loc="left", pad=6, fontsize=7.5, color=GRAY,
    )
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#d8d8d8")
    ax.tick_params(axis="x", length=0, pad=3, labelsize=6.2, colors=GRAY)
    ax.tick_params(axis="y", length=0, labelsize=6.2, colors=GRAY)
    ax.set_xticks(years)
    ax.set_xticklabels([f"'{str(y)[2:]}" for y in years])
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.margins(x=0.03)


def build(out: str | None = None) -> str:
    data = load("content/impact.yml")
    rows = data.get("history", [])
    totals = data.get("totals", {})
    partial = data.get("partial-year")

    fig, axes = plt.subplots(1, 2, figsize=(6.4, 1.7))
    for ax, key, title in (
        (axes[0], "publications", "PUBLICATIONS"),
        (axes[1], "citations", "CITATIONS"),
    ):
        pts = [(r["year"], r[key]) for r in rows if r.get(key) is not None]
        panel(ax, [y for y, _ in pts], [v for _, v in pts], title,
              totals.get(key, sum(v for _, v in pts)), partial)

    if partial:
        axes[1].annotate(
            f"'{str(partial)[2:]} part year",
            xy=(0.995, -0.30), xycoords="axes fraction",
            ha="right", va="top", fontsize=5.8, color=GRAY,
        )

    fig.tight_layout(pad=0.2, w_pad=2.5)
    out = out or os.path.join(ROOT, data.get("figure", "img/impact.svg"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", help="output file (default: the figure in impact.yml)")
    out = build(ap.parse_args().out)
    print(f"wrote {os.path.relpath(out, ROOT)} ({os.path.getsize(out) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
