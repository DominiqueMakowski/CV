// ---------------------------------------------------------------------------
// The look. A Typst port of the awesome-cv / vitae design used by
// ../DominiqueMakowski_CV.Rmd. Colours, sizes and metrics were measured off the
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
        columns: (1fr, auto),
        column-gutter: 10pt,
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
        columns: (1fr, auto),
        column-gutter: 10pt,
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
      // left edge rather than the two the LaTeX version had.
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
// The source line is not optional and `validate.py` enforces it. Citation
// counts are stale the week after they are taken, and an undated one is exactly
// what a reader is entitled to be suspicious of.
#let cv-stats(data) = block(width: 100%, above: 10pt, below: 0pt)[
  #let notes = data.at("notes", default: ())
  #let source = data.at("source", default: none)
  #let figure-path = data.at("figure", default: none)
  #grid(
    columns: (logo-slot, 1fr),
    [],
    [
      #if figure-path != none [
        // Every figure in the plot is repeated in the bullets underneath, so
        // the alt text can say what it shows rather than read it out.
        #image(
          figure-path,
          width: 100%,
          alt: "Bar charts of publications and of citations per year, both "
            + "rising steeply from 2019.",
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
        columns: (card-logo-width + card-logo-gap, 1fr),
        align: (left + top, left + top),
        box(width: card-logo-width, height: card-logo-width)[
          #if logo != none and logo != "" [
            #align(center + horizon, image(
              logo,
              width: 100%,
              height: 100%,
              fit: "contain",
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
  row-gap: 13pt,
)

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
#let cv-topics(data, row-gap: 6pt, group-gap: 13pt) = {
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

// Convening and curriculum on the left, supervision and examining on the right.
#let cv-roles(
  items,
  headings: ("Convening and Curriculum", "Supervision and Examining"),
) = cv-columns(items, kinds: ("convening", "supervision"), headings: headings)

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
  languages: none,
  about: none,
) = {
  let email = unescape(email)
  let www = unescape(www)
  let github = unescape(github)
  let orcid = unescape(orcid)
  let scholar = unescape(scholar)
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
      github,
      "https://github.com/" + github,
    ))
  }
  // The two identifiers a hiring panel or a screening system will actually
  // follow, on a row of their own: five items do not fit on one line beside
  // the photo, and a row that wraps leaves one of them orphaned. The ORCID is
  // shown as the bare identifier, which is how it is quoted; the Scholar
  // profile is shown by name, since its id means nothing.
  let identifiers = ()
  if orcid != "" {
    identifiers.push(contact-item(fa-orcid, orcid, "https://orcid.org/" + orcid))
  }
  if scholar != "" {
    identifiers.push(contact-item(
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

      #v(-4pt)
      #if position != none [
        #text(size: 7.6pt, fill: accent, smallcaps(position))
        #v(-3pt)
      ]
      #if address != none [
        #text(
          font: head-font,
          size: 8pt,
          style: "italic",
          fill: text-light,
          address,
        )
        #v(-2pt)
      ]
      #contacts.join(separator)
      #if identifiers.len() > 0 [
        #v(-2pt)
        #identifiers.join(separator)
      ]

      // One line, in the same small caps as the position: a fact about the
      // person rather than a section's worth of content.
      #if languages != none [
        #v(1pt)
        #text(size: 6.8pt, fill: text-gray, smallcaps[Languages: #languages])
      ]

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
  languages: none,
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
    languages: languages,
    about: about,
  )

  doc
}
