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

`cv.pdf` is tagged and PDF/UA-1 (`pdf-standard: ua-1` in `cv.qmd`). The UA-1
compile *refuses* to build if, say, an image loses its alt text, so it doubles
as the accessibility check: `build.sh` then reports that `cv.pdf` was not
rewritten.

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
| `img/logos/` | Institution logos: SVG sources, and the PNGs rendered from them that the CV embeds (see caveat below). |
| `tools/rasterize_logos.py` | Renders `img/logos/*.svg` to PNG. Run by the build; only stale PNGs are redrawn. |
| `img/languages/` | The four flags and the Python and R marks, for the Languages section. |
| `img/tools/`, `img/projects/` | The software marks, and the pictures for Science Adjacent Projects. |
| `img/preview.png` | The first three pages side by side, shown in the repository README. |
| `tools/crop_logos.py` | Tightens logo viewBoxes to the artwork they contain. |
| `tools/make_ntu_logo.py` | Rebuilds `ntu-full.svg` (crest + wordmark). |
| `tools/make_paris_logo.py` | Rebuilds `universite-paris.svg` from the panel version. |
| `tools/make_ghu_logo.py`, `tools/make_salpetriere_logo.py`, `tools/make_porte_verte_logo.py` | Rebuild the three hospital logos (`sainte-anne2.svg`, `salpetriere.svg`, `porte-verte.svg`) from the raw assets beside them. |
| `tools/svgtext.py`, `tools/fonts/` | Set a line of type as SVG paths, for the logo text no institution publishes as vectors; the subset fonts it uses. |
| `tools/make_preview.py` | Redraws `img/preview.png` from `cv.pdf`. Not run by the build (it needs PyMuPDF and Pillow); run it by hand after a layout change. |
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

## Typst version

Quarto 1.8 bundled Typst 0.13; Quarto 1.9 bundles 0.14, which writes tagged
PDF and takes `pdf-standard`, so the accessible PDF is the only PDF - headings,
paragraphs, links and figures in a structure tree, `/Lang en-GB`, PDF/UA-1
declared in the metadata. `keep-typ: true` still leaves the generated `cv.typ`
in place, which is useful for reading the error when a compile fails.

Logos are SVG: `img/logos/*.svg` are the original vector sources copied from
the lab website (`RealityBending.github.io/people/dominique-makowski/assets/`),
cleaner than the PDFs the LaTeX build used. `sussex-brighton.svg` is the
variant with "Brighton" under the wordmark.

The CV embeds PNGs rendered from them, not the SVGs themselves. Several logos
are traced artwork made of many abutting paths, and PDF viewers anti-alias each
path separately, so at some zoom levels seams and ragged edges showed between
shapes. `tools/rasterize_logos.py` renders each SVG through Typst at 1,200 px on
the long side (about 2,000 ppi at the size the CV prints them), which has no
seams and stays sharp well past any normal zoom. Edit the SVG, never the PNG;
the build redraws the PNG. The flags and the software marks are simple shapes
and stay SVG.

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

Accessibility and ATS rules the template now enforces:

- **Every image is either described or marked decorative.** Logos, flags and
  the contact icons sit next to the name they stand for, so they are tagged as
  artifacts (`pdf.artifact`) and skipped. The photo, the impact plot and the
  project pictures carry alt text - the last from `alt:` in `projects.yml`.
  The build fails on a figure with neither.
- **No hyphenation.** A word broken across lines extracts as two fragments
  (`disor- ders`), which literal keyword matching misses. Only real compounds
  (`ageing-related`) still break at their hyphen.
- **Identifiers are in the text, not only behind links.** The GitHub address
  is spelled out in the header. The ORCID is an iD mark beside the
  Publications heading, linked to the record and with the iD as its alt text
  (the header has no room for it); it and the Scholar profile id are the only
  identifiers that are link-only.
- The contact icons still appear as four private-use characters to extractors
  that ignore tagging (pypdf does); tag-aware readers skip them.
