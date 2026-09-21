# Figure scripts

Two standalone R scripts, kept out of the CV build. They came from the retired
`old_cv/` pipeline, where they were run by hand and their PNGs pasted into the
repo README. Nothing in `cv/` depends on them, and `cv/build.sh` does not call
them — they are here because the figures are worth being able to remake.

Both use paths relative to this folder, so run them from here:

```bash
cd scripts && Rscript make_data_coauthors.R
```

| Script                   | Reads                                    | Writes                          |
|--------------------------|------------------------------------------|---------------------------------|
| `make_data_coauthors.R`  | Google Scholar; `data/data_network.csv`  | `img/collaboration_network.png` |
| `make_data_wordcloud.R`  | publication PDFs; `img/brain.png` (mask) | `img/wordcloud.png`             |

The committed PNGs in `img/` are the last outputs from the old pipeline, so the
figures survive even if a script cannot be re-run.

## Co-author network

Scrapes the co-author lists of the Google Scholar profile, one hop out, into
`data/data_network.csv` (2,615 edges as committed), then draws it with `igraph`
/ `ggraph`. The scrape is slow and rate-limited; the committed CSV lets you
redraw without re-scraping — comment out the scraping block and start from the
`read.csv` on line 93.

Two caveats inherited from the source data:

- Scholar only lists co-authors who have a Scholar profile **and** whom you have
  manually accepted on your own profile (the `+` button under "Co-authors"), so
  the network is an undercount rather than a census.
- Line 111 writes a `data_graph.json` to an absolute path inside the lab website
  repo (`RealityBendingLab/RealityBending.github.io/WIP/collaborations/`), for an
  interactive version of the same graph. Edit or drop that line — it will fail
  if the path is not there.

Needs: `dplyr`, `stringr`, `scholar`, `igraph`, `ggraph`, `see`, `tidygraph`,
`jsonlite`.

## Wordcloud

Extracts the text of every publication PDF with `pdftools`, counts terms with
`tm` after a hand-written list of merges and corrections (`replace_and_add`,
which fixes ligature damage such as `ction` → `fiction`), and renders the cloud
into the silhouette of `img/brain.png`.

**The input path is stale.** Line 32 points at
`C:/Dropbox/PERSO/website/content/publication`, which is where the personal
website kept per-paper folders of PDFs. Repoint it at whatever holds the PDFs
now before running, and expect the merge list to need extending as new terms
appear.

Needs: `dplyr`, `ggplot2`, `pdftools`, `tm`, `png`, and a wordcloud geom
(`ggwordcloud`).
