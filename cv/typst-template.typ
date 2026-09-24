// ---------------------------------------------------------------------------
// The look. A Typst port of the awesome-cv / vitae design used by
// ../old_cv/DominiqueMakowski_CV.Rmd. Colours, sizes and metrics were measured off the
// LaTeX-rendered PDF so the two can be compared side by side.
//
// Nothing in this file is content: it defines the `cv` document template and
// the `cv-entry` / `cv-entries` helpers that the body of cv.qmd calls.
// ---------------------------------------------------------------------------

#let accent = rgb("#1976d2")
#let text-dark = rgb("#333333")
#let text-body = rgb("#414141")
#let text-gray = rgb("#5d5d5d")
#let text-light = rgb("#999999")

#let body-font = "Source Sans 3"
#let head-font = "Roboto"

// The logo gutter. Every logo is drawn at the full gutter width, so height
// follows from its proportions: wide wordmarks come out short, tall crests
// come out tall. The text column keeps a single left edge down the whole page
// either way.
#let logo-width = 44pt
#let logo-gap = 12pt
#let logo-slot = logo-width + logo-gap

// The location/date gutter on the right of an entry. Fixed rather than `auto`
// so that the bullets can reserve it too: sized to the content it holds, the
// column moves with every entry and there is no edge for the bullets to stop
// at, so they run the full width and slide under the dates above them. Set
// just wide enough for the widest value either row carries - "2023 - Present"
// at 44.1pt - so the headings look the same as they did when the column was
// measured from them.
#let meta-width = 46pt
#let meta-gap = 10pt
#let meta-slot = meta-width + meta-gap

// FontAwesome 4 private-use codepoints, same glyphs the LaTeX build uses.
#let fa-envelope = "\u{f0e0}"
#let fa-home = "\u{f015}"
#let fa-github = "\u{f092}"
// ORCID has no glyph in FontAwesome 4; the id badge is the nearest thing to
// what it is, a persistent researcher identifier.
#let fa-orcid = "\u{f2c1}"
#let fa-scholar = "\u{f19d}"

// --- content helpers -------------------------------------------------------

// Flatten content back to a plain string (used to split section titles).
#let plain(c) = {
  if type(c) == str { c } else if type(c) != content { str(c) } else if c
    .has("text") { c.text } else if c.has("children") {
    c.children.map(plain).join("")
  } else if c.has("body") { plain(c.body) } else { "" }
}

// YAML strings are Typst markup, with one convenience: markdown-style
// [label](url) is rewritten to a real link first. See content/README.md.
#let md(s) = {
  if s == none { return [] }
  if type(s) != str { return s }
  eval(
    s.replace(
      regex("\\[([^\\]]*)\\]\\(([^)]+)\\)"),
      m => "#link(\"" + m.captures.at(1) + "\")[" + m.captures.at(0) + "]",
    ),
    mode: "markup",
  )
}

// Pandoc escapes Typst-significant characters (@, _, #) when it substitutes a
// metadata value into a string context. Strings we use as URLs or verbatim
// labels have to be unescaped again.
#let unescape(s) = {
  if type(s) != str { return s }
  s.replace(regex("\\\\(.)"), m => m.captures.at(0))
}

// --- entries ---------------------------------------------------------------

// One experience/education entry: an optional logo spanning two header lines,
// title + location on the first, organisation + date on the second, then
// bullet points that run the full text width (as in the original).
#let cv-entry(
  title: none,
  location: none,
  org: none,
  date: none,
  logo: none,
  details: (),
  size: logo-width,
  logo-h: auto,
  logo-y: top,
) = block(breakable: false, width: 100%, above: 13pt, below: 0pt)[
  #grid(
    // The gutter is the same width in every section, so the text column has one
    // left edge down the whole page. A section with smaller logos keeps that
    // edge and closes the gap by pushing its logos right, against the text,
    // rather than leaving them stranded at the margin.
    columns: (logo-slot, 1fr),
    align: (left + logo-y, left + top),
    // Missing logo files still reserve the slot, so titles stay aligned.
    //
    // `logo-h` fixes the height of that slot. Without it the row is as tall as
    // whichever is taller, the logo or the text, and since a logo's height
    // follows from its proportions, a section of two-line entries ends up with
    // uneven gaps: a tall crest pushes its own row open and a wide wordmark
    // does not. Pinning the height makes every row in such a section the same,
    // whatever shape the marks are. Sections whose entries carry bullets are
    // text-driven already and leave it unset.
    box(width: logo-width, height: logo-h)[
      #if logo != none and logo != "" [
        #align(
          right + logo-y,
          image(logo, width: size, height: logo-h, fit: "contain"),
        )
      ]
    ],
    [
      #grid(
        columns: (1fr, meta-width),
        column-gutter: meta-gap,
        // The column is wider than what it holds now that it is fixed, so the
        // alignment has to say what `auto` used to say by itself: stay against
        // the right margin.
        align: (left, right),
        {
          set par(justify: false)
          text(size: 10pt, weight: "bold", fill: text-body, md(title))
        },
        text(
          size: 9pt,
          weight: "light",
          style: "italic",
          fill: accent,
          md(location),
        ),
      )
      #v(4pt, weak: true)
      #grid(
        columns: (1fr, meta-width),
        column-gutter: meta-gap,
        align: (left, right),
        {
          set par(justify: false)
          text(size: 8pt, fill: text-gray, smallcaps(md(org)))
        },
        text(
          size: 8pt,
          weight: "light",
          style: "italic",
          fill: text-gray,
          md(date),
        ),
      )
      #v(5pt, weak: true)
      // Bullets sit in the same column as the headings, so each entry has one
      // left edge rather than the two the LaTeX version had. They stop at the
      // headings' right edge too: run to the full width they read as a block of
      // text with the dates floating over it, and the eye has to work out which
      // of the two it is following.
      #block(width: 100% - meta-slot)[
        #{
          set par(leading: 0.45em, spacing: 0.45em)
          for d in details {
            grid(
              columns: (8.5pt, 1fr),
              text(size: 9pt, weight: "light", fill: text-dark)[•],
              text(size: 9pt, weight: "light", fill: text-body, md(d)),
            )
          }
        }
      ]
    ],
  )
]

// Render a whole section from a loaded YAML list.
//
// `size` sets the logo width for the whole section, and `logo-h` the height of
// the slot it sits in. A section whose entries carry no bullets - Education,
// say - wants both: the marks have to be small enough not to tower over two
// lines of text, and the slot has to be a fixed height or the rows come out
// unevenly spaced. The gutter itself never changes, so sections stay aligned
// with each other.
//
// `logo-y` is `top` (the logo sits against the title it labels) or `horizon`
// (centred on the entry). Centring only works where entries are short and of
// even height: on a five-line entry the logo drifts to the middle and loses its
// connection to the organisation name.
#let cv-entries(
  entries,
  logo-dir: "img/logos/",
  size: logo-width,
  logo-h: auto,
  logo-y: top,
) = {
  for e in entries {
    cv-entry(
      title: e.at("title", default: none),
      location: e.at("location", default: none),
      org: e.at("org", default: none),
      date: e.at("date", default: none),
      logo: if e.at("logo", default: none) in (none, "") { none } else {
        logo-dir + e.logo
      },
      details: e.at("details", default: ()),
      size: size,
      logo-h: logo-h,
      logo-y: logo-y,
    )
  }
}

// --- figures ------------------------------------------------------------

// The bibliometrics: a plot of publications and citations per year, then the
// things a plot cannot say, then where the numbers came from and when.
//
// Indented into the same text column as the entries above it, so the page has
// one left edge.
//
// The source line is optional, and drawn only when content/impact.yml has one.
#let cv-stats(data) = block(width: 100%, above: 10pt, below: 0pt)[
  #let notes = data.at("notes", default: ())
  #let source = data.at("source", default: none)
  #let figure-path = data.at("figure", default: none)
  #grid(
    columns: (logo-slot, 1fr),
    [],
    [
      #if figure-path != none [
        // The bullets underneath interpret the plot rather than repeat it,
        // so the alt text is what says what it shows.
        #image(
          figure-path,
          width: 100%,
          alt: "Two charts, per year and not cumulative: publications as bars "
            + "with citations as a line, both rising steeply from 2019; and "
            + "software downloads per year for easystats and NeuroKit, on a log "
            + "scale.",
        )
      ]
      #if notes.len() > 0 [
        #v(9pt, weak: true)
        #{
          set par(leading: 0.45em, spacing: 0.45em)
          for n in notes {
            grid(
              columns: (8.5pt, 1fr),
              text(size: 9pt, weight: "light", fill: text-dark)[•],
              text(size: 9pt, weight: "light", fill: text-body, md(n)),
            )
          }
        }
      ]
      #if source != none [
        #v(7pt, weak: true)
        #text(size: 6.8pt, fill: text-light, smallcaps(md(source)))
      ]
    ],
  )
]

// --- cards -----------------------------------------------------------------

// Two labelled columns of short cards. Used twice: for grants and awards, and
// for software and measures. Both are sets of things that pair off naturally,
// and where an item is worth three lines rather than an entry - putting a grant
// on the page at the same size as a job overstates it.
//
// A card repeats the rhythm of `cv-entry` at a smaller size: a name with its
// figure on a baseline, a small-caps line under it, then a description. So the
// two treatments read as one document.

// Big enough that a hex sticker reads as a mark rather than a smudge. The width
// comes straight out of the text column beside it, so the descriptions are cut
// to match - see the note in content/software.yml.
#let card-logo-width = 46pt
#let card-logo-gap = 10pt

#let cv-card(
  name: "",
  url: none,
  meta: none,
  reach: none,
  description: none,
  logo: none,
  slot: false,
  slot-w: card-logo-width,
  frame: false,
) = {
  // The name is a link but is not painted like one: with a figure in the accent
  // colour on the same line, two blues compete and neither reads. Dark for what
  // it is, accent for how much.
  let head = [
    #grid(
      columns: (1fr, auto),
      column-gutter: 6pt,
      align: (left + top, right + top),
      {
        set par(justify: false, leading: 0.4em)
        show link: set text(fill: text-body)
        text(size: 9.5pt, weight: "bold", fill: text-body)[
          #if url != none { link(url)[#md(name)] } else { md(name) }
        ]
      },
      text(size: 7.5pt, weight: "bold", fill: accent, md(reach)),
    )
    #if meta != none [
      #v(2.5pt, weak: true)
      #block(width: 100%)[
        #set par(justify: false, leading: 0.4em)
        #text(size: 7pt, fill: text-gray, smallcaps(md(meta)))
      ]
    ]
    // Left-ragged, unlike the rest of the document: justifying 8pt text in a
    // column this narrow opens rivers wide enough to see across the page.
    #if description != none [
      #v(3.5pt, weak: true)
      #block(width: 100%)[
        #set par(justify: false, leading: 0.42em)
        #text(size: 8pt, weight: "light", fill: text-gray, md(description))
      ]
    ]
  ]

  block(breakable: false, width: 100%, above: 0pt, below: 0pt)[
    #if not slot [
      #head
    ] else [
      // Every mark gets the same square, whatever its proportions, and is
      // centred in it. That is the only way a wordmark, a hex sticker and a
      // figure lifted from a paper sit on one grid without one of them
      // dominating the column.
      //
      // A card with no mark yet still reserves the square, so that one
      // placeholder does not step the whole column left.
      #grid(
        columns: (slot-w + card-logo-gap, 1fr),
        align: (left + top, left + top),
        box(width: slot-w, height: slot-w)[
          #if logo != none and logo != "" [
            // A picture is framed and a mark is not. A logo is drawn to sit on
            // the page by itself; a photograph or a painting has an edge, and
            // without a rule around it the white of the artwork runs into the
            // white of the page and the picture looks like a printing fault.
            #align(center + horizon, box(
              stroke: if frame { 0.5pt + rgb("#dddddd") } else { none },
              radius: if frame { 2pt } else { 0pt },
              clip: frame,
              image(logo, width: 100%, height: 100%, fit: "contain"),
            ))
          ]
        ],
        head,
      )
    ]
  ]
}

// The rule under a column's name.
#let cv-band-label(title, above: 0pt) = block(
  breakable: false,
  width: 100%,
  above: above,
  below: 0pt,
)[
  #heading(level: 2, outlined: true, md(title))
]

// Two columns of cards, split by `kind`, each under its own label.
#let cv-columns(
  items,
  kinds: (),
  headings: (),
  logo-dir: none,
  gutter: 26pt,
  row-gap: 11pt,
  breakable: false,
) = {
  let column(title, group) = [
    #cv-band-label(title)
    #v(9pt, weak: true)
    #{
      // Each card is unbreakable already; the label above the column is sticky
      // (see the level-2 heading rule), so a page break can fall between cards
      // but never between a label and its first card.
      let cells = group.map(i => cv-card(
        name: i.at("name", default: ""),
        url: i.at("url", default: none),
        meta: i.at("meta", default: none),
        reach: i.at("reach", default: none),
        description: i.at("description", default: none),
        logo: if logo-dir == none or i.at("logo", default: none) in (none, "") {
          none
        } else { logo-dir + i.logo },
        slot: logo-dir != none,
      ))
      grid(columns: (1fr,), row-gutter: row-gap, ..cells)
    }
  ]

  // A grid row breaks wherever the page ends, including straight after the
  // column labels, and the sticky heading above cannot see that. Every card
  // section is well under a page, so the default is to move the section whole;
  // a section that ever outgrows a page passes `breakable: true`.
  block(breakable: breakable, width: 100%, above: 14pt, below: 0pt)[
    #grid(
      columns: (1fr, 1fr),
      column-gutter: gutter,
      align: (left + top, left + top),
      ..kinds
        .zip(headings)
        .map(((k, h)) => column(h, items.filter(i => i.at(
          "kind",
          default: kinds.at(0),
        ) == k))),
    )
  ]
}

// Grants on the left, awards on the right. Neither carries a mark: a funder's
// logo is advertising for the funder, and an award has no mark to carry.
#let cv-awards(items, headings: ("Grants", "Awards")) = cv-columns(
  items,
  kinds: ("grant", "award"),
  headings: headings,
)

// What is run for the School and the University on the left; the journals on
// the right.
#let cv-service(
  items,
  headings: ("School and University", "Editorial and Peer Review"),
) = cv-columns(items, kinds: ("leadership", "editorial"), headings: headings)

// Public engagement and outreach on the left; paid and invited work for
// organisations outside the university on the right. The outward-facing
// counterpart of `cv-service`, which is deliberately institutional.
#let cv-engagement(
  items,
  headings: ("Public Engagement and Outreach", "Knowledge Exchange and Consultancy"),
) = cv-columns(items, kinds: ("outreach", "exchange"), headings: headings)

// Talks given by invitation on the left; talks and posters taken to conferences
// on the right. The split is who chose the speaker. An invitation is evidence
// that somebody wanted this particular person in the room; a conference slot is
// evidence that the work passed review. They are different claims, and a single
// chronological list makes neither.
#let cv-talks(
  items,
  headings: ("Invited Talks and Seminars", "Conference Presentations"),
) = cv-columns(items, kinds: ("invited", "conference"), headings: headings)

// Software on the left, the measures and paradigms on the right. These do carry
// their marks: this is the one section where a reader gains something from
// seeing the thing itself rather than only its name.
#let cv-tools(
  items,
  logo-dir: "img/tools/",
  headings: ("Software", "Measures and Paradigms"),
) = cv-columns(
  items,
  kinds: ("software", "measure"),
  headings: headings,
  logo-dir: logo-dir,
  row-gap: 10pt,
)

// The things made outside the job, shown rather than described. One band
// across the page rather than two labelled columns: "Art" over one card and
// "Games" over another labelled two items as though they were two categories,
// and a category of one is a list with a title. One label, one row, and the
// cards say what they each are.
//
// The picture slot is half as wide again as a software mark, because these are
// pictures and not logos - a hex sticker survives being 46pt across, a painting
// does not - and framed, so that an image on a pale ground has an edge.
#let cv-projects(
  items,
  logo-dir: "img/projects/",
  heading: "Science Adjacent Projects",
  gutter: 26pt,
  row-gap: 11pt,
  slot-w: 66pt,
  above: 14pt,
) = block(breakable: false, width: 100%, above: above, below: 0pt)[
  #cv-band-label(heading)
  #v(9pt, weak: true)
  #grid(
    columns: (1fr, 1fr),
    column-gutter: gutter,
    row-gutter: row-gap,
    align: (left + top, left + top),
    ..items.map(i => cv-card(
      name: i.at("name", default: ""),
      url: i.at("url", default: none),
      meta: i.at("meta", default: none),
      reach: i.at("reach", default: none),
      description: i.at("description", default: none),
      logo: if i.at("logo", default: none) in (none, "") { none } else {
        logo-dir + i.logo
      },
      slot: true,
      slot-w: slot-w,
      frame: true,
    )),
  )
]

// --- topics ----------------------------------------------------------------

// A teaching area: what it is and at what level on the left, the topics inside
// it on the right.
//
// A list of modules says what was timetabled; it does not say what a person can
// teach, which is the question a department is actually asking. Grouping by area
// answers that in one screenful, and putting the level beside the area - in the
// accent, so it reads before the prose does - answers the other half of it.
// Three columns, not two with the level tucked under the area: on its own the
// level column is a rail of accent down the section, and the answer to "at what
// level" is legible before any of the prose is.
// Both columns are set just wide enough for their widest entry - measured off
// the rendered PDF at 107pt for "Rehabilitation and Practice" and 48pt for
// "MSc · PhD · BSc" - so the space they were holding goes to the topics. A
// longer name than those simply wraps, which is why these are not exact.
#let topic-area-width = 110pt
#let topic-level-width = 50pt

#let cv-topic(
  area: "",
  level: none,
  topics: none,
  where: none,
  above: 9pt,
) = block(
  breakable: false,
  width: 100%,
  above: above,
  below: 0pt,
)[
  #grid(
    columns: (topic-area-width, topic-level-width, 1fr),
    column-gutter: 10pt,
    align: (left + top, left + top, left + top),
    {
      set par(justify: false, leading: 0.4em)
      text(size: 9pt, weight: "bold", fill: text-body, md(area))
    },
    {
      set par(justify: false, leading: 0.4em)
      text(size: 7pt, weight: "bold", fill: accent, smallcaps(md(level)))
    },
    {
      set par(justify: false, leading: 0.45em)
      text(size: 8.5pt, weight: "light", fill: text-gray, md(topics))
      // Where and when it was actually taught, and for how long. Small, because
      // it is corroboration rather than content - but present, because an
      // unsourced list of what somebody can teach is only a claim.
      if where != none {
        v(2.5pt, weak: true)
        block(width: 100%, text(
          size: 6.8pt,
          fill: text-light,
          smallcaps(md(where)),
        ))
      }
    },
  )
]

// Rows carry a `group`, and a new one opens a labelled band. The groups are the
// overarching areas a department organises its teaching into; the rows inside
// are what can actually be covered, and at what level.
//
// Nested rather than flattened to three lines. Collapsing the rows into their
// groups would take the level column with it - every group would aggregate to
// "MSc · PhD · BSc" and the one thing the column is there to say, that the
// current teaching is postgraduate, would be the first thing lost.
// The gaps are a point tighter than they look like they want to be, and the
// section is the better for it: the table is nine rows of three columns, and
// at 6pt the rows read as nine separate things rather than as three bands.
// It also buys the page enough that Software follows Teaching onto it.
#let cv-topics(data, row-gap: 5pt, group-gap: 11pt) = {
  let lead = data.at("lead", default: none)
  let items = data.at("areas", default: ())

  if lead != none {
    block(width: 100%, above: 10pt, below: 0pt)[
      #set par(justify: true, leading: 0.5em)
      #text(size: 8.5pt, style: "italic", fill: text-body, md(lead))
    ]
  }

  let current = none
  for (n, i) in items.enumerate() {
    let g = i.at("group", default: none)
    if g != current {
      current = g
      if g != none {
        cv-band-label(g, above: if n == 0 { 13pt } else { group-gap })
      }
    }
    cv-topic(
      area: i.at("area", default: ""),
      level: i.at("level", default: none),
      topics: i.at("topics", default: none),
      where: i.at("where", default: none),
      above: row-gap,
    )
  }
}

// What is designed and taught on the left, who is supervised and examined on
// the right. "Design and Delivery" rather than "Convening and Curriculum":
// the column holds a programme, a convened module and a run of invited
// workshops, and only the first two are convening.
#let cv-roles(
  items,
  headings: ("Design and Delivery", "Supervision and Examining"),
) = cv-columns(
  items,
  kinds: ("convening", "supervision"),
  headings: headings,
  row-gap: 10pt,
)

// --- languages -------------------------------------------------------------

// Marks are drawn to a common height, never a common width, so each keeps its
// own proportions: the Union Flag is twice as wide as it is tall and a
// tricolour is half again, and forcing them into one box is the sort of thing
// a reader notices without being able to say why. The slot is a fixed height
// so that the names underneath sit on one line across both columns whatever
// shape the marks above them are.
// Drawn small: the strip has to close the first page under the clinical
// entries, and every point the marks give back is a point the sections above
// it do not have to lose. A flag this size still reads at arm's length -
// they are the most recognisable marks on the page - and what is left over
// once the group labels are gone goes back into them rather than into air.
#let lang-slot = 22pt
#let lang-flag-h = 19pt
#let lang-mark-h = 21pt

// One tile: the mark, the language under it, the level under that. The same
// three sizes as a card's name and `meta`, so the strip reads as part of the
// document rather than as a panel dropped into it.
#let cv-lang(name: "", level: none, logo: none, height: lang-flag-h) = block(
  breakable: false,
  width: 100%,
)[
  #set align(center)
  #box(width: 100%, height: lang-slot)[
    #if logo != none and logo != "" [
      #align(center + horizon, image(logo, height: height, fit: "contain"))
    ]
  ]
  #v(3pt, weak: true)
  #block(width: 100%)[
    #set par(justify: false, leading: 0.4em)
    #text(size: 8pt, weight: "bold", fill: text-body, md(name))
  ]
  // The level is set like an entry's date - italic, light, grey - rather than
  // in the small caps a card's `meta` line uses. Both say the same thing about
  // the line ("this qualifies the name above it"), but small caps at this size
  // hold the eye as long as the name does, and six tiles of that read as
  // twelve things rather than six.
  #if level != none [
    #v(1.5pt, weak: true)
    #block(width: 100%)[
      #set par(justify: false, leading: 0.4em)
      #text(
        size: 7pt,
        weight: "light",
        style: "italic",
        fill: text-gray,
        md(level),
      )
    ]
  ]
]

// One row of tiles, all six of them, with a wide gap where the groups meet.
//
// Labelled columns ("Spoken", "Programming") is what every other two-column
// section does, but here the labels were saying what the tiles already say: a
// flag is spoken and the R and Python marks are not. Dropping them takes a
// ruled line and two rows of small caps out of the strip, which is how it
// closes the first page.
//
// The break between the groups is a gap rather than a label, then: tiles of
// one nature sit at one pitch, and the two natures sit further apart than any
// two tiles ever do. The tiles themselves share one width across the whole
// row, so a flag is never drawn larger than a mark or the other way round.
//
// A flag is a solid block of colour and a mark is an outline, so the marks are
// drawn a little taller; at the same height they read as the smaller of the
// two.
#let cv-languages(
  items,
  logo-dir: "img/languages/",
  kinds: ("spoken", "code"),
  heights: (lang-flag-h, lang-mark-h),
  tile-gutter: 9pt,
  group-gap: 90pt,
  above: 15pt,
) = {
  let group(kind) = items.filter(i => i.at("kind", default: kinds.at(0)) == kind)
  // An empty group would otherwise claim a gap of its own.
  let present = kinds.zip(heights).filter(((k, y)) => group(k).len() > 0)

  let cols = ()
  let cells = ()
  for (n, (kind, height)) in present.enumerate() {
    if n > 0 {
      cols.push(group-gap)
      cells.push([])
    }
    for i in group(kind) {
      cols.push(1fr)
      cells.push(cv-lang(
        name: i.at("name", default: ""),
        level: i.at("level", default: none),
        logo: if i.at("logo", default: none) in (none, "") { none } else {
          logo-dir + i.logo
        },
        height: height,
      ))
    }
  }

  block(breakable: false, width: 100%, above: above, below: 0pt)[
    #grid(
      columns: cols,
      column-gutter: tile-gutter,
      align: top,
      ..cells,
    )
  ]
}

// --- header ----------------------------------------------------------------

#let contact-item(icon, label, url) = {
  let label = unescape(label)
  let url = unescape(url)
  box[
    #text(font: "FontAwesome", size: 6.8pt, fill: accent, icon)
    #h(1.5pt)
    #link(url)[#text(font: head-font, size: 6.8pt, fill: accent, label)]
  ]
}

#let cv-header(
  name: "",
  surname: "",
  position: none,
  address: none,
  photo: none,
  email: "",
  www: "",
  github: "",
  orcid: "",
  scholar: "",
  about: none,
) = {
  let email = unescape(email)
  let www = unescape(www)
  let github = unescape(github)
  let orcid = unescape(orcid)
  let scholar = unescape(scholar)
  // One row, in the order a reader would use them: how to reach him, then
  // where the work is.
  //
  // Each item is labelled by what it is rather than by its identifier. A
  // username and a Scholar profile id are strings only the link needs; "GitHub"
  // and "Google Scholar" say where the link goes, which is the only thing the
  // line has room to say. The address and the ORCID are the exceptions, and for
  // the same reason in reverse: those *are* quoted verbatim, one typed into a
  // browser and one cited in a form.
  let contacts = ()
  if email != "" {
    contacts.push(contact-item(fa-envelope, email, "mailto:" + email))
  }
  if www != "" {
    contacts.push(contact-item(fa-home, www, "https://" + www))
  }
  if github != "" {
    contacts.push(contact-item(
      fa-github,
      "GitHub",
      "https://github.com/" + github,
    ))
  }
  if orcid != "" {
    contacts.push(contact-item(fa-orcid, orcid, "https://orcid.org/" + orcid))
  }
  if scholar != "" {
    contacts.push(contact-item(
      fa-scholar,
      "Google Scholar",
      "https://scholar.google.com/citations?user=" + scholar,
    ))
  }
  let separator = text(font: head-font, size: 6.8pt, fill: text-dark)[
    #h(4pt) | #h(4pt)
  ]

  grid(
    columns: (104pt, 1fr),
    column-gutter: 20.7pt,
    align: (left + top, left + top),
    if photo != none and photo != "" {
      box(
        width: 104pt,
        height: 104pt,
        radius: 50%,
        clip: true,
        stroke: 0.8pt + rgb("#cccccc"),
        image(photo, width: 100%, height: 100%, fit: "cover"),
      )
    } else { none },
    [
      #set align(center)
      #text(font: head-font, size: 32pt, weight: 100, fill: text-gray, name)#h(
        9pt,
      )#text(font: head-font, size: 32pt, weight: "bold", fill: text-dark, surname)

      // The 32pt name sets its own line with room to spare above and below;
      // -4pt took all of that out and closed the gap to nothing, so the post
      // read as part of the name rather than as a line under it.
      #v(-1pt)
      // The post and where it is held are one line, not two. Set as the title
      // in the accent above the address, the post read as a label for the name
      // - a rank, coloured like the links - rather than as the answer to what
      // he does and where, which is the same sentence and belongs in the same
      // breath: "Assistant Professor in Psychology, University of Sussex".
      #let where = {
        let parts = (position, address).filter(p => (
          p != none and plain(p).trim() != ""
        ))
        if parts.len() > 0 { parts.join([, ]) }
      }
      #if where != none [
        #text(
          font: head-font,
          size: 8pt,
          style: "italic",
          fill: text-light,
          where,
        )
        #v(-2pt)
      ]
      #contacts.join(separator)

      // The summary shares the column with the name block, so it runs alongside
      // the photo rather than being pushed below it.
      #if about != none [
        #v(9pt)
        #set align(left)
        #set text(size: 9pt, style: "italic", fill: text-body)
        #set par(justify: true, leading: 0.5em)
        #about
      ]
    ],
  )
}

// --- document --------------------------------------------------------------

#let cv(
  name: "",
  surname: "",
  position: none,
  address: none,
  photo: none,
  email: "",
  www: "",
  github: "",
  orcid: "",
  scholar: "",
  about: none,
  date: none,
  keywords: (),
  doc,
) = {
  set document(
    title: name + " " + surname + " - Curriculum Vitae",
    author: name + " " + surname,
    keywords: keywords,
  )

  set page(
    paper: "a4",
    margin: (left: 1.4cm, right: 1.4cm, top: 0.8cm, bottom: 1.8cm),
    footer: context {
      // Not on the first page. The footer is there so that a loose sheet from
      // the middle of the CV says whose it is and how much of it is missing;
      // the first page has the name at 32pt and a photograph, so a line
      // repeating it underneath only spends space the page has better uses
      // for - the languages strip that closes it.
      if counter(page).get().first() > 1 {
        set text(size: 8pt, fill: text-light)
        grid(
          columns: (1fr, auto, 1fr),
          align: (left, center, right),
          smallcaps(if date != none { date } else { "" }),
          smallcaps[#name #surname · Curriculum Vitae],
          smallcaps[
            #counter(page).display() of #context counter(page).final().first()
          ],
        )
      }
    },
  )

  set text(font: body-font, size: 9pt, fill: text-body, lang: "en", region: "GB")
  set par(justify: true, leading: 0.55em)
  show link: set text(fill: accent)

  // Sub-section labels. A real heading rather than styled text, so that it
  // lands in the PDF outline and the tag tree; `cv-band-label` is the only
  // thing that emits one, and the rule under it is the whole of its look.
  // Both heading levels are sticky: a heading that ends a page while its
  // section starts the next is the first thing a reader notices and the last
  // thing a diff of the content would reveal.
  show heading.where(level: 2): it => block(
    width: 100%,
    above: 0pt,
    below: 0pt,
    sticky: true,
  )[
    #text(size: 7.5pt, fill: text-light, smallcaps(it.body))
    #v(3pt, weak: true)
    #line(length: 100%, stroke: 0.5pt + rgb("#e6e6e6"))
  ]

  // Section headings: first three characters in the accent colour, then a rule.
  show heading.where(level: 1): it => {
    let t = plain(it.body)
    let cut = calc.min(3, t.len())
    block(above: 18pt, below: 8pt, width: 100%, sticky: true)[
      #grid(
        columns: (auto, 1fr),
        column-gutter: 8pt,
        align: (left + bottom, left + bottom),
        text(size: 16pt, weight: "bold")[
          #text(fill: accent, t.slice(0, cut))#text(
            fill: text-dark,
            t.slice(cut),
          )
        ],
        box(inset: (bottom: 4pt), line(length: 100%, stroke: 0.5pt + rgb(
          "#aaaaaa",
        ))),
      )
    ]
  }

  cv-header(
    name: name,
    surname: surname,
    position: position,
    address: address,
    photo: photo,
    email: email,
    www: www,
    github: github,
    orcid: orcid,
    scholar: scholar,
    about: about,
  )

  doc
}

// --- publications -----------------------------------------------------------

// The publication list, as themed blocks. Fed from
// content/_publications.generated.yml, which tools/build_publications.py writes
// from ../publications.bib and content/publications.yml - facts and editorial
// decisions respectively. Nothing about a citation is decided here: the
// authors, title and venue arrive already formatted, because which name is
// bold and where the ampersand goes is bibliographic convention rather than
// layout.
//
// Indented into the same text column as every other section, so the page keeps
// one left edge. The year sits in the same right-hand gutter the entries use
// for their dates, which is what lets a reader scan the list by date without
// reading it.
#let cv-publication(entry, highlight-colour: accent) = block(
  breakable: false,
  width: 100%,
  above: 7pt,
  below: 0pt,
)[
  #grid(
    columns: (1fr, meta-width),
    column-gutter: meta-gap,
    align: (left, right),
    {
      set par(justify: false, leading: 0.45em)
      // The marker sits in the gutter rather than in the text, so a highlighted
      // entry lines up with the others instead of being pushed right.
      place(
        dx: -9pt,
        dy: 2.5pt,
        if entry.at("highlight", default: false) {
          circle(radius: 1.6pt, fill: highlight-colour)
        },
      )
      let title = md(entry.at("title", default: ""))
      // Assembled in code rather than in a markup block: a line break inside
      // markup is a space, which would put one before every full stop.
      text(
        size: 8pt,
        weight: "light",
        fill: text-body,
        {
          // The author list arrives already punctuated: it normally ends in an
          // initial's full stop, and build_publications.py adds one when it
          // does not.
          md(entry.at("authors", default: ""))
          " "
          if entry.at("url", default: none) != none {
            link(entry.url, text(fill: accent, title))
          } else { title }
          ". "
          md(entry.at("venue", default: ""))
          "."
          if entry.at("note", default: none) != none {
            text(fill: text-light, style: "italic", { " (" + entry.note + ")" })
          }
        },
      )
    },
    text(size: 8pt, weight: "light", style: "italic", fill: text-gray)[
      #entry.at("year", default: "")
    ],
  )
]

#let cv-publications(themes) = {
  for (i, theme) in themes.enumerate() {
    block(breakable: false, width: 100%, above: if i == 0 { 10pt } else { 14pt }, below: 0pt)[
      #grid(
        columns: (logo-slot, 1fr),
        [],
        text(
          size: 9pt,
          weight: "bold",
          fill: accent,
          font: head-font,
          // `upper`, not `smallcaps`: Roboto's small-cap glyphs are drawn as
          // full capitals anyway, and they extract as mixed case with some
          // letters lost ("otheR", "Reality PeRcePtion"), which is exactly
          // what an ATS or a screening model reads.
          upper(md(theme.name)),
        ),
      )
    ]
    block(width: 100%, above: 2pt, below: 0pt)[
      #grid(
        columns: (logo-slot, 1fr),
        [],
        {
          for e in theme.at("entries", default: ()) {
            cv-publication(e)
          }
        },
      )
    ]
  }
}
