# content/

One YAML file per CV section. Each file is a list of entries; each entry is a
flat map of fields. No renderer syntax, no escaping rules beyond the ones below.

## Entry fields

| Field | Renders as |
| --- | --- |
| `title` | First line, left, bold. The position or qualification. |
| `location` | First line, right, blue italic. |
| `org` | Second line, left, small caps grey. The institution. |
| `date` | Second line, right, grey italic. |
| `logo` | File in `img/logos/`. Omit or leave empty to reserve the slot blank. |
| `details` | Bullet points, full text width. |
| `tooltip` | Plain text shown on hover over the title, **in the web version only**. A PDF has no hover, so the field is ignored there; anything that must reach a print reader goes in `details`. No links or emphasis: it lands in an HTML attribute. Used for the PhD thesis title. |

All fields are optional. Entries appear in file order; keep newest first, and
bullets most-important-first.

## Card files

Six files are rendered as two labelled columns of short cards rather than as
entries, and take their own fields. A card is worth three lines; an entry is
worth as much page as a job, which overstates a grant and understates nothing.

Which column a card lands in is its `kind`:

| File | Left column | Right column |
| --- | --- | --- |
| `grants-awards.yml` | `grant` (the default) | `award` |
| `teaching-roles.yml` | `convening` (the default) | `supervision` |
| `software.yml` | `software` (the default) | `measure` |
| `service.yml` | `leadership` (the default) | `editorial` |
| `engagement.yml` | `outreach` (the default) | `exchange` |
| `talks.yml` | `invited` (the default) | `conference` |

`talks.yml` splits on who chose the speaker: an invitation is evidence that
somebody wanted this particular person, a conference slot is evidence that the
work passed review. It is also the one card file that is deliberately a
*selection*. `PROFILE.md` holds all fifty-five presentations; this file holds
four talks and three summary cards, because a full chronological list would run
a page and a half and would weigh a French student poster the same as a chaired
international symposium. The counts on the summary cards count only what was
presented in person - see the header of the file for what that drops.

`service.yml` and `engagement.yml` split one subject between them: what is run
*for* the institution (committees, schemes, seminar series, journals) stays in
service; what faces *outward* (public debate, media, symposia, paid work for
organisations outside the university) goes in engagement. The invited doctoral
teaching is in neither - it is a card in `teaching-roles.yml`.

A grant is named for its project, not its scheme. "Behavioural and Communication
Science Programme" tells a reader nothing about the research; the scheme belongs
with the funder in `meta`.

| Field | Renders as |
| --- | --- |
| `name` | Card heading, bold. Linked to `url` if there is one, but not coloured: the accent is spoken for by `reach`. |
| `url` | Where the name points. Repository, documentation site, DOI or award page. |
| `meta` | Line under the name, small caps grey. Funder, role and dates; or language, role and dates. |
| `reach` | The figure in the corner, accent bold. An amount for a grant, a year for an award or a role, downloads or stars for a package. One per card. |
| `description` | The rest: the project a grant paid for, what an award was for, what a package does. |
| `logo` | File in `img/tools/`, drawn in a fixed square. Only `software.yml` uses marks; a funder's logo is advertising for the funder, and an award has no mark to carry. |
| `kind` | Which column, per the table above. |

Every field except `name` is optional, so a card can be a placeholder - a name
and `meta: "In development"` - until there is something to point at.

Two things to watch:

- Keep a description to about four lines in its column, roughly 160 characters.
- A card name has to fit beside its figure and cannot be hyphenated. One long
  unbroken word will run under the figure; move the detail into `meta` instead.

## teaching-areas.yml

A mapping, and a table rather than a list of cards.

| Key | Renders as |
| --- | --- |
| `lead` | The italic paragraph under the section heading: how long the teaching has run, at what level, and how the table is organised. |
| `areas` | The rows, below. |

| Row field | Renders as |
| --- | --- |
| `group` | Opens a labelled band when it changes. The overarching area a department organises its teaching around. |
| `area` | Left column, bold. |
| `level` | Middle column, accent small caps. `MSc · PhD`, and so on. |
| `topics` | Right column. Semicolon-separated, about 150 characters - two lines. |
| `where` | Small caps under the topics: institution, hours, dates. |

Three decisions are baked into this shape.

**Grouped, not listed module by module.** A module list says what happened to be
timetabled; what a department wants to know is what someone can cover, and where
they would sit. The groups answer the second question, the rows the first.

**The group names are the target department's own.** For the Oxford application
they are taken from the Experimental Psychology job description
(`applications/Jobs/2026_oxford/description.pdf`): *Individual Differences and
Clinical Psychology* is the name of their second-year paper, and the one area
the description names twice as core tutorial teaching; *Cognition* and
*Psychobiology* are two of the three sections of their first-year Introduction
to Psychology paper. The third section, Perception, is not claimed, because it
has not been taught. For another department these revert to generic names -
"Neuroscience and Cognition", "Clinical Neuropsychology" - without touching the
rows underneath.

**Nested, not flattened to three lines.** Collapsing the rows into their groups
would take the level column with it: every group would aggregate to
`MSc · PhD · BSc`, and the one thing that column exists to say - that the current
teaching is postgraduate - is the first thing that would be lost. Rows run
postgraduate-first inside each group for the same reason.

**`where` is not decoration.** An unsourced list of what somebody can teach is
only a claim. Hours are the "equivalent TD" figures from the Paris teaching
service, recorded per course unit in `PROFILE.md` > Academic Teaching; the Sussex
modules are ongoing and carry dates only. The line also does honest work the
prose cannot: it shows at a glance that the clinical teaching is from the Paris
post and not current.

## languages.yml

A list of tiles: a mark, a language, a level. `kind` picks the group.

| Field | Renders as |
| --- | --- |
| `name` | Under the mark, bold. |
| `level` | Under the name, small caps grey. |
| `logo` | File in `img/languages/`. **Required** - unlike an entry's logo, this one is the whole tile. |
| `kind` | `spoken` (the default), first in the row; or `code`, after the gap. |

The section sits after Clinical Practice rather than at the end, because it is
the only one short enough to close the first page; the tiles are sized to the
space the entries above them leave, so the marks here are smaller than the
logos everywhere else. See the note in `../cv.qmd`.

All six tiles are one row, and the break between the two groups is a wide gap
rather than a pair of labels: a flag says "spoken" and the R and Python marks
say what they are, so labelling them spent two rows of the page on nothing. A
tile is the same width throughout - four flags squeezed into half the page
beside two logos at twice the size would say something about the two that is
not meant.

The spoken levels are the ones in `../PROFILE.md` > Languages. The two code
levels are on the same scale as the spoken ones on purpose: the tiles sit in
one strip, and a language is a language.

`tools/make_languages.py` rebuilds `img/languages/`. It draws the flags (the
colours are the ones the LaTeX CV used) and fetches the two marks from the
projects themselves; its output is committed, so a build needs no network.
Marks are drawn to a common *height*, never a common width, so each keeps its
own proportions - a Union Flag is twice as wide as it is tall.

## impact.yml

A mapping, and the only content file with a picture attached.

| Key | Renders as |
| --- | --- |
| `figure` | The plot, drawn from `history` by `tools/make_impact.py`. |
| `totals` | `publications` and `citations`, used to label the panels. |
| `history` | One row per year: `year`, `publications`, `citations`. Either count may be missing. Years must be in order. |
| `partial-year` | The year the snapshot cuts through. Drawn faded and labelled. |
| `notes` | Bullets under the plot, for what a plot cannot say - the h-index, author positions, the Wikipedia articles. |
| `source` | Small caps grey, under the notes. **Required** - `validate.py` rejects the file without it. |

`totals` is given rather than summed, because the columns do not add up to it:
Scholar reports two publications without a year, and citations only from 2019.

The plot shows **per year, not cumulative**. A running total only ever goes up,
so it says the same thing whatever the underlying year was like; per-year bars
show the shape of the record, which is the interesting part. The part-year bar
is faded and labelled for the same reason - a snapshot taken in June makes the
current year look like a collapse, and nothing else on the page would tell a
reader otherwise.

Everything in the plot is repeated in the bullets underneath, so nothing lives
only in the picture.

To refresh: `Rscript tools/refresh_scholar.R` prints a new `history` block (it
needs R and the `scholar` package, and is the only part of this repo that does),
then `./build.sh` redraws the figure. The source date moves with the numbers.

Run `python tools/validate.py` after editing. It rejects unknown keys, missing
logo files, unbalanced brackets and unescaped special characters - all of which
otherwise render into a PDF that looks fine and reads wrong.

## Markup in text fields

Text fields take **Typst markup**, which for ordinary prose means: type the
prose. Three things are worth knowing.

- **Links** use markdown syntax and are rewritten for you:
  `[Reality Bending Lab](https://realitybending.github.io/)`.
- `*bold*` and `_italic_` work (note: Typst uses single asterisks for bold,
  not double).
- `#`, `$`, `@` and `<` are special. A literal one needs a backslash: `\#`.
  This mostly matters for hashtags and prices.

Long bullets are easiest to read as folded scalars:

```yaml
    - >-
      Text that wraps across several lines in the file
      but renders as one paragraph.
```

Quotation marks are curled automatically, so type `"like this"`.

## Two files that are not like the others

`publications.yml` carries no content at all, only cite keys. The citations live
in `../../publications.bib`, at the repo root beside `PROFILE.md`, because they
are ground truth rather than a rendering choice and other projects draw on them.
This file says which theme each key sits in, in what order, what is highlighted
and what is deliberately withheld. `tools/build_publications.py` merges the two
into `_publications.generated.yml`, which is what `cv.qmd` actually renders.

Never edit `_publications.generated.yml`: every build overwrites it. A key that
matches nothing in the bibliography, and a bibliography entry that no theme
claims, both fail `tools/validate.py` — so a new paper cannot be added to the
bibliography and quietly left off the CV.

`training.yml` is rendered by `cv-topics`, the same renderer as
`teaching-areas.yml`, because the shape is identical: rows banded by a group,
each with a short label and a line of provenance. The one oddity is that its
`level` column holds a year rather than a level. Reusing the renderer is why the
section needed no new code, no new validation and no new HTML.
