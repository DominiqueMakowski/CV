# Institution logos

Logos shown next to each entry of the *Education* section of the CV. Only
that section uses them; the *Experience* entries are plain text.

## How it works

Each Education entry carries a `logo` column holding the **file name only**
(the `img/logos/` prefix is added by the `add_logos()` helper defined in the
setup chunk of `DominiqueMakowski_CV.Rmd`):

```r
tibble(
  what = "Doctor of Philosophy (PhD) - Psychology",
  when = "2014 - 18",
  with = "Université de Paris",
  where = "France",
  logo = "universite-paris.pdf",
  details = "..."
)
```

Just before `vitae::detailed_entries()`, the chunk runs:

```r
data <- add_logos(data, data$logo)
```

which prefixes the title line (`what`) with `\cvlogo{img/logos/<file>}` and
indents the institution line (`with`) by the same width, so the logo sits to
the left of both header lines and spans their full height.

If a file is missing (or `logo` is `NA`), the slot is left empty but still
reserved, so every entry in the section keeps the same left edge. **Nothing
breaks if a logo file is absent** — the CV simply builds without that logo.

## Files

`raw/` holds the original SVGs, copied from the lab website
(`RealityBending.github.io/people/dominique-makowski/assets`). The PDFs next
to them are vector conversions made with `pymupdf` (see below), so they stay
sharp at any zoom.

| PDF                      | Raw SVG                    | Institution                           | Used in   |
|--------------------------|----------------------------|---------------------------------------|-----------|
| `universite-paris.pdf`   | `org-uniparis.svg`         | Université de Paris                   | Education |
| `aftcc.pdf`              | `org-aftcc.svg`            | French Association for CBT (AFTCC)    | Education |
| `sussex.pdf`             | `org-sussex.svg`           | University of Sussex (full lockup)    | —         |
| `ntu.pdf`                | `org-ntu.svg`              | Nanyang Technological University      | —         |
| `sainte-anne.pdf`        | `sainte-anne-Hospital.svg` | Centre hospitalier Sainte-Anne        | —         |
| `ngh.pdf`                | `org-ngh.svg`              | National Guild of Hypnotists          | —         |

To use one of the unused files, add a `logo = "<file>"` column to the
relevant entry and call `add_logos()` before `detailed_entries()` in that
chunk, as the Education chunk does.

## Image requirements

- **PDF (vector) is preferred**; PNG with a transparent or white background
  also works.
- Logos are scaled to fit a box of `\cvlogoheight` × `\cvlogowidth`
  (7.5 mm × 9 mm by default) and centred in it, aspect ratio preserved. The
  height matches the two header lines of an entry (title + institution).
  Square marks use the full height; wide wordmarks are limited by the width.
- For PNG, around 300–500 px on the long side is plenty.
- Crop away surrounding whitespace before adding a file, otherwise the logo
  will look smaller than the others.

To change the size for the whole CV, edit the three `\newlength` lines in the
`header-includes:` block of `DominiqueMakowski_CV.Rmd`.

## Converting more SVGs

```python
import pymupdf
doc = pymupdf.open("raw/logo.svg")
open("logo.pdf", "wb").write(doc.convert_to_pdf())
```

Note: ImageMagick's SVG delegate (`magick::image_read`) renders these
particular files with badly wrong colours — the NTU crest came out magenta
instead of blue and gold. Use MuPDF (above) or `rsvg` instead.
