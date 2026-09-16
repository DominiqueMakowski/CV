# Refresh the bibliometrics in content/impact.yml from Google Scholar.
#
#   Rscript tools/refresh_scholar.R
#
# Needs R and the scholar package (install.packages("scholar")). This is the
# only part of the build that does, which is why it is a separate manual step
# rather than something `build.sh` runs: the figures change a few times a year,
# and Scholar rate-limits hard enough that an automated fetch would be a
# liability in a build that otherwise needs nothing but Quarto, Typst and
# Python.
#
# Ported from the LaTeX CV's make_data_impact.R. That version saved an .Rdata
# blob, which meant the numbers on the CV lived in a binary file that only R
# could open. This one prints YAML to paste into content/impact.yml, so they
# stay readable, diffable and checkable by tools/validate.py.
#
# Afterwards: paste the block below `history:`, update `totals` and `source`,
# move `partial-year` to the current year, and run
# `python tools/make_impact.py` (or just `./build.sh`) to redraw.

library(scholar)

ID <- "bg0BZ-QAAAAJ"

profile <- scholar::get_profile(ID)
history <- scholar::get_citation_history(ID)
pubs <- scholar::get_publications(ID, flush = TRUE)

pub_years <- table(pubs$year[!is.na(pubs$year) & pubs$year > 1950])
cite_years <- setNames(history$cites, history$year)
years <- sort(union(as.integer(names(pub_years)), as.integer(names(cite_years))))

cat("# totals:\n")
cat(sprintf("#   publications: %d\n", nrow(pubs)))
cat(sprintf("#   citations: %d\n", profile$total_cites))
cat(sprintf("# h-index %d, i10-index %d\n", profile$h_index, profile$i10_index))
cat(sprintf("# source: \"Google Scholar, %s\"\n\n", format(Sys.Date(), "%B %Y")))

cat("history:\n")
for (y in years) {
  cat(sprintf("  - year: %d\n", y))
  p <- pub_years[as.character(y)]
  if (!is.na(p)) cat(sprintf("    publications: %d\n", p))
  c_ <- cite_years[as.character(y)]
  if (!is.na(c_)) cat(sprintf("    citations: %d\n", c_))
}

# Scholar reports some publications without a year, so the publications column
# does not add up to the total; that is why `totals` is given rather than summed.
missing <- sum(is.na(pubs$year) | pubs$year <= 1950)
if (missing > 0) cat(sprintf("\n# %d publication(s) have no year and are not in the plot.\n", missing))
