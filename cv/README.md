# cv — Quarto + Typst

The CV. Quarto + Typst, replacing the R Markdown + `vitae` + LaTeX pipeline that
used to live in `../old_cv/`. Every section of the old Rmd is ported, including
the publication list and the additional training, so nothing here depends on
that folder; it is kept only in git history.

## Build

```bash
./build.sh
```

Validates the content, then produces two files from it:

| Output | What it is |
| --- | --- |
| `cv.pdf` | The CV. |
| `cv.html` | Web version, with schema.org JSON-LD. |

A third, `cv-accessible.pdf`, appears if a standalone Typst 0.14+ is on PATH
(`winget install --id Typst.Typst`) - same document, tagged and PDF/UA-1
validated. See the caveat below for why that is not the default.

For the PDF alone, `./build.sh --pdf`. For one render on its own,
`quarto render cv.qmd`. About a second, against ~40 s for the LaTeX build, and
no TeX installation.

`build.sh` judges each step by whether its output appeared rather than by the
exit code: Quarto exits non-zero when Dropbox holds its scratch directory open,
which happens on this machine *after* the PDF is already written.

## Layout

| Path | What it is |
| --- | --- |
| `cv.qmd` | The document: YAML metadata (header fields) + section structure. |
| `content/*.yml` | The content. One file per section. See `content/README.md`. |
| `typst-template.typ` | The look: page setup, header, section headings, entry layout. |
| `typst-show.typ` | Three lines of glue binding the qmd's YAML to the template. |
| `_quarto.yml` | Project-level format options, so `quarto render` needs no flags. |
| `build.sh` | Builds everything, in the right order. |
| `tools/validate.py` | Content checks. Run before every build. |
| `content/publications.yml` | Which theme each publication sits in, and what is hidden or highlighted. The citations themselves are `../publications.bib`. |
| `content/_publications.generated.yml` | Built from those two. Never edited by hand. |
| `tools/build_publications.py` | Merges the bibliography with the curation, and formats the citations. |
| `tools/bibtex.py` | A small BibTeX reader, so the build keeps needing nothing but Quarto, Typst and Python. |
| `tools/build_html.py` | The web version. |
| `tools/cvdata.py` | Shared loading, so the tools cannot disagree about the content. |
| `fonts/` | Roboto, Source Sans 3, FontAwesome — vendored so the build is self-contained. |
| `img/logos/` | Institution logos, as SVG (see caveat below). |
| `img/languages/` | The four flags and the Python and R marks, for the Languages section. |
| `tools/crop_logos.py` | Tightens logo viewBoxes to the artwork they contain. |
| `tools/make_ntu_logo.py` | Rebuilds `ntu-full.svg` (crest + wordmark). |
| `tools/make_paris_logo.py` | Rebuilds `universite-paris.svg` from the panel version. |
| `tools/make_impact.py` | Draws the Impact plot from `content/impact.yml`. Run by the build. |
| `tools/refresh_scholar.R`, `tools/refresh_downloads.py` | Print fresh bibliometrics and download figures to paste into `content/impact.yml`. Run by hand; they need the network. |
| `tools/make_languages.py` | Draws the four flags; vendors the Python and R marks. |

The split that matters: **content is YAML, layout is Typst, and they never mix.**
In the Rmd, an entry was an R `tibble()` with LaTeX macros inside double-escaped
strings; here it is six plain keys. That is the change that makes the content
editable without knowing anything about the renderer.

Adding a section is: write `content/<section>.yml`, then add to `cv.qmd`

````markdown
# Education

```{=typst}
#cv-entries(yaml("content/education.yml"))
```
````

Headings stay real markdown headings, so they remain semantic in the output
rather than being styled text. `tools/validate.py` discovers sections by reading
`cv.qmd`, so there is no manifest to keep in step.

## Validation

```bash
python tools/validate.py
```

The renderer fails quietly - a mistyped key is dropped, an unbalanced bracket
swallows the rest of a sentence, a missing logo leaves a blank slot - and all of
those produce a PDF that looks fine until someone reads it closely. The
validator turns them into errors, and it catches the unbalanced parenthesis that
sat in the NTU entry of the LaTeX CV unnoticed.

## Two caveats from Typst's version

Quarto 1.8.25 bundles **Typst 0.13**, not 0.14. Two consequences:

1. **Logos are SVG, not PDF.** Native PDF images landed in Typst 0.14. This is
   no longer a real constraint: `img/logos/*.svg` are the original vector
   sources copied from the lab website
   (`RealityBending.github.io/people/dominique-makowski/assets/`), so they are
   cleaner than the PDFs the LaTeX build used, not a lossy conversion of them.
   `sussex-brighton.svg` is the variant with
   "Brighton" under the wordmark, unused for now.

2. **No tagged PDF or PDF/UA-1.** Those are 0.14 features, and they were a
   large part of the reason for moving off LaTeX. The escape hatch is already
   wired up: `keep-typ: true` leaves the generated `cv.typ` in place, so a
   standalone Typst 0.14 can compile the same file with the accessibility
   checks turned on:

   ```bash
   typst compile --font-path fonts --pdf-standard ua-1 cv.typ
   ```

   That command is **untested** — it needs a standalone `typst` 0.14 on PATH,
   which this machine does not have yet.

## Machine readability

Checked against the requirements in `../AGENTS.md`:

```bash
python -c "import pypdf; print(pypdf.PdfReader('cv.pdf').pages[0].extract_text())"
```

Extraction order is correct, entries come out as coherent blocks, and nothing
essential is image-only. Two improvements over the LaTeX build:

- **Document metadata now exists.** The LaTeX PDF carried only `/Creator` and
  `/Producer`; this one carries `/Title`, `/Author` and `/Keywords`, the last
  from the `keywords:` list in `cv.qmd` — recruiter-facing search terms, so
  worth curating.
- **The PDF has a foldable outline.** Typst turns every `#` heading into a PDF
  bookmark, so the sidebar in any viewer gives a collapsible tree of sections.
  This comes for free and gets more useful as sections are added.
- **Small caps no longer corrupt the text.** LaTeX extracted the institution line
  as `SCHOOL OF PSYCHOLOGY, UNiVERSiTY OF SUSSEX` — real small-cap glyphs, with
  lowercase `i` surviving as literal `i`. Typst extracts it as
  `School of Psychology, University of Sussex`. Same appearance, but a parser
  now reads the actual words.
