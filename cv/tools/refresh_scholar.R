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
# Author position is ported from get_stats() in the same CV's functions.R, with
# one change. That version patched the finished counts by hand for particular
# papers; this one reads shared first authorship from ../publications.bib
# (`equal = {1,2}`), so a new co-first paper is counted without editing this
# script. Only shared *first* authorship moves a paper, as it did there.
#
# Run from cv/, as above: the .bib is found relative to it.
#
# Afterwards: paste the block below `history:`, update `totals` and `source`,
# move `partial-year` to the current year, put the author-position line into
# the h-index note under `notes`, and run `python tools/make_impact.py` (or just
# `./build.sh`) to redraw. Then update PROFILE.md > Impact > Bibliometrics.

library(scholar)

ID <- "bg0BZ-QAAAAJ"
BIB <- "../publications.bib"

# Title words, for matching a Scholar title to a .bib one. Accents, case,
# punctuation and brace-protected capitals all differ between the two.
title_words <- function(s) {
  s <- iconv(tolower(s), "UTF-8", "ASCII//TRANSLIT")
  strsplit(trimws(gsub("[^a-z0-9]+", " ", s)), " +")[[1]]
}

# One braced field of a .bib entry, respecting nested braces; NA if absent.
bib_field <- function(entry, name) {
  m <- regexpr(paste0("\\b", name, "\\s*=\\s*\\{"), entry, perl = TRUE)
  if (m < 0) return(NA_character_)
  chars <- strsplit(substring(entry, m + attr(m, "match.length")), "")[[1]]
  end <- which(cumsum((chars == "{") - (chars == "}")) < 0)[1]
  gsub("\\s+", " ", paste(chars[seq_len(end - 1)], collapse = ""))
}

# The .bib entries where I share first authorship: their title words.
read_cofirst <- function(path) {
  text <- readLines(path, encoding = "UTF-8", warn = FALSE)
  text <- paste(text[!grepl("^\\s*%", text)], collapse = "\n")
  out <- list()
  for (entry in strsplit(text, "\n(?=@)", perl = TRUE)[[1]]) {
    equal <- bib_field(entry, "equal")
    if (is.na(equal)) next
    equal <- as.integer(strsplit(equal, "[, ]+")[[1]])
    authors <- trimws(strsplit(bib_field(entry, "author"), " and ", fixed = TRUE)[[1]])
    me <- which(startsWith(authors, "Makowski, D"))
    if (1 %in% equal && length(me) == 1 && me %in% equal) {
      out[[length(out) + 1]] <- title_words(bib_field(entry, "title"))
    }
  }
  out
}

# Where I sit in one Scholar author list: first, second, last or other. Second
# is tested before last, so a two-author paper counts as second, never senior.
# NA if I am not in the list at all.
#
# That default can be wrong: on a two-author paper with a student or junior
# first author, second is the senior position. No such paper exists yet - the
# two-author papers so far are with Serge Nicolas, where second is right - so
# there is no exception mechanism. The script lists every two-author paper it
# counts as second, so check that list at each refresh.
author_position <- function(authors) {
  a <- trimws(tolower(strsplit(authors, ",", fixed = TRUE)[[1]]))
  k <- which(grepl("^d(ominique)?\\.? ?makowski$", a))[1]
  if (is.na(k)) return(NA_character_)
  if (k == 1) "first" else if (k == 2) "second" else if (k == length(a)) "last" else "other"
}

# Positions for every publication, with co-first papers moved to first. A
# Scholar title matches a .bib one when it holds nearly all of its words.
count_positions <- function(pubs, cofirst) {
  pos <- vapply(pubs$author, author_position, character(1), USE.NAMES = FALSE)
  for (i in which(!is.na(pos))) {
    words <- title_words(pubs$title[i])
    if (any(vapply(cofirst, function(b) mean(b %in% words) >= 0.9, logical(1)))) {
      pos[i] <- "first"
    }
  }
  pos
}

# Read the .bib first, so that running from the wrong folder fails before
# spending any requests on Scholar.
if (!file.exists(BIB)) stop("run from cv/: ", BIB, " not found")
cofirst <- read_cofirst(BIB)

profile <- scholar::get_profile(ID)
history <- scholar::get_citation_history(ID)
pubs <- scholar::get_publications(ID, flush = TRUE)

# get_publications() truncates long author lists, so author position needs the
# complete one: one request per publication, which makes this the slow part.
pubs$author <- vapply(pubs$pubid, function(p) {
  scholar::get_complete_authors(ID, p, delay = 0.4)
}, character(1), USE.NAMES = FALSE)

pub_years <- table(pubs$year[!is.na(pubs$year) & pubs$year > 1950])
cite_years <- setNames(history$cites, history$year)
years <- sort(union(as.integer(names(pub_years)), as.integer(names(cite_years))))

pos <- count_positions(pubs, cofirst)
n <- table(factor(pos, levels = c("first", "second", "last", "other")))

cat("# totals:\n")
cat(sprintf("#   publications: %d\n", nrow(pubs)))
cat(sprintf("#   citations: %d\n", profile$total_cites))
cat(sprintf("# h-index %d, i10-index %d\n", profile$h_index, profile$i10_index))
cat(sprintf("# author position: %d first, %d second, %d last (senior), %d other\n",
            n[["first"]], n[["second"]], n[["last"]], n[["other"]]))
cat(sprintf("# notes: \"%d of %d publications as first (%d) or senior (%d) author\"\n",
            n[["first"]] + n[["last"]], nrow(pubs), n[["first"]], n[["last"]]))
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

# Two-author papers counted as second, for the check described at
# author_position().
two <- pubs$title[which(pos == "second" & lengths(strsplit(pubs$author, ",", fixed = TRUE)) == 2)]
if (length(two) > 0) {
  cat(sprintf("\n# Counted as second, not senior - check each is right (%d):\n", length(two)))
  cat(sprintf("#   %s\n", two), sep = "")
}

# A publication I cannot be found in is left out of every author-position count.
absent <- pubs$title[is.na(pos)]
if (length(absent) > 0) {
  cat(sprintf("\n# Not found in the author list of %d publication(s), so not counted:\n", length(absent)))
  cat(sprintf("#   %s\n", absent), sep = "")
}
