"""Draw the Impact plot from content/impact.yml.

    python tools/make_impact.py        # -> img/impact.svg

Two panels. The left is a port of `plot_impact()` from the LaTeX CV's
functions.R, which faceted publications and citations from one ggplot; here
they share one panel, publications as bars and citations as a line on its own
axis. The right is software downloads, one line per package family.

Deliberate choices, all of them about not misleading:

- Per year, not cumulative. The original plotted a running total, which only
  ever goes up and so says the same thing whatever the underlying year was
  like. Because every series here rises anyway, the plot is easy to misread as
  a running total, so both titles say "per year" and the caption under the
  plot says "not cumulative" in so many words.
- Two y-axes on the left panel, which is normally a mistake: where the two
  scales happen to line up is arbitrary, so the chart can be made to say
  anything about how the two relate. It is kept because publications and
  citations are the pair a reader wants side by side, and made safer by
  aligning the gridlines to round numbers on both scales, colouring each
  axis's ticks like its series, and naming both series in a legend with their
  totals.
- A log scale on the right. easystats has ten times NeuroKit's downloads, and
  on a linear axis NeuroKit would be a flat line along the bottom. The ticks
  say 10k / 100k / 1M / 10M, and the title says "log scale".
- The part year is drawn faded (bars) and dashed (lines). A snapshot taken
  mid-year makes the current year look like a collapse, and a reader who does
  not know the snapshot date has no way to tell that from a real one.

Text is converted to paths, so the file renders identically in Typst and in a
browser without either needing the font. The bullets beneath the plot interpret
it rather than repeat it, so the figure's alt text (in typst-template.typ and
build_html.py) is what describes it to a reader who cannot see it.
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
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

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
# The second and third series hues. Blue, orange and this green were checked
# together with the dataviz palette validator (all pairs, colour-blind safe).
# The green is under 3:1 against white, which is why its line is labelled
# directly rather than left to a legend.
ORANGE = "#eb6834"
GREEN = "#1baf7a"
GRAY = "#8a8a8a"
INK = "#555555"
GRID = "#e6e6e6"

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

TITLE = dict(loc="left", pad=14, fontsize=7.5, color=GRAY)
MARKER = dict(marker="o", markersize=3.6, markeredgecolor="white", markeredgewidth=0.7)


def frame(ax, years):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#d8d8d8")
    ax.tick_params(axis="x", length=0, pad=3, labelsize=6.2, colors=GRAY)
    ax.tick_params(axis="y", length=0, labelsize=6.2, colors=GRAY)
    ax.set_xticks(years)
    ax.set_xticklabels([f"'{str(y)[2:]}" for y in years])
    ax.grid(axis="y", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def line(ax, years, values, colour, partial):
    """A line with ringed markers. The step into the part year is dashed and its
    point hollow, so the part year reads as unfinished rather than as a fall."""
    full = [(y, v) for y, v in zip(years, values) if y != partial]
    ax.plot([y for y, _ in full], [v for _, v in full], color=colour,
            linewidth=1.5, solid_capstyle="round", zorder=3, **MARKER)
    if partial in years:
        i = years.index(partial)
        if i > 0:
            ax.plot(years[i - 1:i + 1], values[i - 1:i + 1], color=colour,
                    linewidth=1.2, linestyle=(0, (2, 1.6)), zorder=3)
        ax.plot([partial], [values[i]], linestyle="none", marker="o",
                markersize=3.6, markerfacecolor="white", markeredgecolor=colour,
                markeredgewidth=1.0, zorder=4)


def scholar_panel(ax, rows, totals, partial):
    pub = [(r["year"], r["publications"]) for r in rows if r.get("publications") is not None]
    cit = [(r["year"], r["citations"]) for r in rows if r.get("citations") is not None]
    years = [y for y, _ in pub]

    ax.bar(years, [v for _, v in pub], width=0.62, linewidth=0,
           color=[ACCENT_FADED if y == partial else ACCENT for y in years])
    frame(ax, years)
    ax.margins(x=0.03)
    ax.tick_params(axis="y", colors=ACCENT)

    twin = ax.twinx()
    line(twin, [y for y, _ in cit], [v for _, v in cit], ORANGE, partial)
    for side in ("top", "right", "left", "bottom"):
        twin.spines[side].set_visible(False)
    twin.tick_params(axis="y", length=0, labelsize=6.2, colors=ORANGE, pad=2)

    # The two scales are aligned so that every gridline is a round number on
    # both: 5 publications and 2,500 citations sit on the same line.
    pub_step, cit_step = 5, 2500
    top = max(max(v for _, v in pub) / pub_step, max(v for _, v in cit) / cit_step) * 1.08
    ax.set_ylim(0, top * pub_step)
    twin.set_ylim(0, top * cit_step)
    ax.set_yticks(range(0, int(top) * pub_step + 1, pub_step))
    ticks = list(range(0, int(top) * cit_step + 1, cit_step))
    twin.set_yticks(ticks)
    twin.set_yticklabels([f"{t / 1000:g}k" if t else "0" for t in ticks])

    ax.set_title("PUBLICATIONS AND CITATIONS PER YEAR", **TITLE)
    handles = [
        Patch(color=ACCENT, label=f"Publications ({totals.get('publications', 0):,} total)"),
        Line2D([], [], color=ORANGE, linewidth=1.5,
               label=f"Citations ({totals.get('citations', 0):,} total)", **MARKER),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.01, 1.0),
              ncol=2, frameon=False, fontsize=6.0, labelcolor=GRAY,
              handlelength=1.4, handleheight=0.7, columnspacing=1.2,
              handletextpad=0.5, borderaxespad=0, borderpad=0)


def downloads_panel(ax, software, partial):
    years = sorted({r["year"] for p in software for r in p["history"]})
    frame(ax, years)
    ax.set_yscale("log")
    ax.minorticks_off()
    ax.set_yticks([1e4, 1e5, 1e6, 1e7])
    ax.set_yticklabels(["10k", "100k", "1M", "10M"])
    ax.set_ylim(8e3, 2.2e7)
    # Room on the right for the labels at the end of each line, and the grid and
    # baseline stopped short of it so that no rule runs through a label.
    lo, hi = years[0] - 0.4, years[-1] + 0.4
    ax.set_xlim(lo, years[-1] + 2.7)
    ax.grid(False)
    ax.hlines([1e4, 1e5, 1e6, 1e7], lo, hi, color=GRID, linewidth=0.5, zorder=0)
    ax.spines["bottom"].set_bounds(lo, hi)

    for pkg, colour in zip(software, (ACCENT, GREEN, ORANGE)):
        ys = [r["year"] for r in pkg["history"]]
        vs = [r["downloads"] for r in pkg["history"]]
        line(ax, ys, vs, colour, partial)
        detail = f"{sum(vs) / 1e6:.1f}M total"
        if pkg.get("stars"):
            detail += f" · {pkg['stars']:,} stars"
        # Name and figures in text ink beside the end of the line, never in the
        # series colour: the line beside them carries the identity.
        ax.annotate(pkg["name"], xy=(ys[-1], vs[-1]), xytext=(6, 1),
                    textcoords="offset points", va="bottom", fontsize=6.4,
                    color=INK, fontweight="bold")
        ax.annotate(detail, xy=(ys[-1], vs[-1]), xytext=(6, -1),
                    textcoords="offset points", va="top", fontsize=5.8, color=GRAY)

    ax.set_title("SOFTWARE DOWNLOADS PER YEAR  ·  LOG SCALE", **TITLE)


def build(out: str | None = None) -> str:
    data = load("content/impact.yml")
    rows = data.get("history", [])
    totals = data.get("totals", {})
    partial = data.get("partial-year")
    software = data.get("software") or []

    fig, axes = plt.subplots(
        1, 2 if software else 1, figsize=(6.4, 1.95), squeeze=False,
        gridspec_kw={"width_ratios": [1.1, 1]} if software else None,
    )
    axes = axes[0]
    scholar_panel(axes[0], rows, totals, partial)
    if software:
        downloads_panel(axes[1], software, partial)
    fig.tight_layout(pad=0.2, w_pad=3.2)

    caption = "Per calendar year, not cumulative."
    if partial:
        caption += f" Faded bar and dashed lines: {partial} so far."
    axes[0].annotate(caption, xy=(0, -0.2), xycoords="axes fraction",
                     ha="left", va="top", fontsize=5.8, color=GRAY)

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
