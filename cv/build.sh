#!/usr/bin/env bash
# Build every output from content/*.yml. Run from the cv/ directory.
#
#   ./build.sh            PDF + HTML
#   ./build.sh --pdf      PDFs only
set -uo pipefail
cd "$(dirname "$0")"

# Quarto exits non-zero when it cannot delete its scratch directory, which on
# this machine happens whenever Dropbox has the folder open - after the PDF has
# already been written. So judge each step by whether its output was *rewritten*
# rather than by the exit code.
#
# Checking that the file merely exists is not enough: if a PDF viewer holds the
# output open, Windows blocks both the delete and the write, Quarto fails, and
# the stale file from the previous build sits there looking like a success. That
# silently shipped an out-of-date CV once, hence the timestamp check.
render() {
  local out="$1" log before after
  shift
  before=$([[ -f "$out" ]] && stat -c %Y_%s "$out" || echo none)
  log=$(mktemp)
  "$@" >"$log" 2>&1
  after=$([[ -f "$out" ]] && stat -c %Y_%s "$out" || echo none)

  if [[ "$after" == none || "$after" == "$before" ]]; then
    echo "FAILED: $out was not rewritten" >&2
    [[ "$after" == "$before" ]] && echo "  (the file on disk is unchanged - is it open in a viewer?)" >&2
    tail -25 "$log" >&2
    rm -f "$log"
    return 1
  fi
  rm -f "$log"
}

# Redrawn before validation, which checks the file exists, and before the PDF,
# which embeds it. Keeps the plot from drifting from the numbers it is drawn
# from.
echo "==> img/impact.svg"
python tools/make_impact.py || exit 1

# Rebuilt before validation for the same reason as the plot above: the
# generated file is what both the PDF and the HTML read, and regenerating it
# here means the .bib and the curation file cannot drift out of the CV without
# the build saying so.
echo "==> content/_publications.generated.yml"
python tools/build_publications.py || exit 1

# The CV embeds the logos as PNGs rendered from the SVG sources; only the stale
# ones are redrawn, so an edited SVG cannot silently fall out of the PDF.
echo "==> img/logos/*.png"
python tools/rasterize_logos.py || exit 1

echo "==> validating content"
python tools/validate.py || exit 1

echo "==> cv.pdf"
render cv.pdf quarto render cv.qmd || exit 1

if [[ "${1:-}" != "--pdf" ]]; then
  echo "==> cv.html"
  python tools/build_html.py || exit 1
fi

# Quarto leaves this behind when its own cleanup is blocked.
rmdir cv_files 2>/dev/null || true

echo
for f in cv.pdf cv.html; do
  [[ -f "$f" ]] && printf '  %-18s %5.0f KB\n' "$f" "$(($(wc -c <"$f") / 1024))"
done
exit 0
