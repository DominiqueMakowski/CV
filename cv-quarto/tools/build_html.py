"""Build the web version of the CV from the same YAML the PDF uses.

    python tools/build_html.py    # -> cv.html

Deliberately separate from `quarto render`: doing this as a second Quarto format
would put a Python/Jupyter dependency in front of the PDF build, and keeping
that build to "Quarto + Typst, nothing else" is worth more than sharing one
document. The content is shared, which is the part that matters; only the
layout is written twice, and HTML and print need different layouts anyway.

The page carries schema.org/Person JSON-LD, so search engines and agents get the
structured record rather than having to read the layout.
"""

from __future__ import annotations

import argparse
import html
import io
import json
import os
import re
import sys
from datetime import date

from cvdata import CARD_KINDS, LINK_RE, ROOT, front_matter, load, load_entries, sections

ACCENT = "#1976d2"


# --- markup ----------------------------------------------------------------

ESCAPED = re.compile(r"\\(.)")


def to_html(s: str, strong: str = "*") -> str:
    """Convert a content string to HTML.

    `strong` is the emphasis character: content/*.yml uses Typst's single
    asterisk, while cv.qmd's `aboutme` is markdown and uses a double one.
    """
    # Protect backslash escapes before anything else looks at the string.
    holes: list[str] = []

    def stash(m: re.Match) -> str:
        holes.append(m.group(1))
        return f"\x00{len(holes) - 1}\x00"

    s = ESCAPED.sub(stash, s)
    s = html.escape(s, quote=False)

    s = LINK_RE.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        s,
    )
    bold = re.escape(strong)
    s = re.sub(rf"{bold}([^*]+?){bold}", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w/])_([^_]+?)_(?!\w)", r"<em>\1</em>", s)

    return re.sub(r"\x00(\d+)\x00", lambda m: html.escape(holes[int(m.group(1))]), s)


def plain(s: str) -> str:
    """Strip markup and collapse whitespace, for JSON-LD and meta tags."""
    s = ESCAPED.sub(r"\1", s)
    s = LINK_RE.sub(r"\1", s)
    return re.sub(r"\s+", " ", re.sub(r"[*_]", "", s)).strip()


# --- page ------------------------------------------------------------------

CSS = """
:root {
  --accent: __ACCENT__; --dark: #333; --body: #414141;
  --gray: #5d5d5d; --light: #999; --rule: #e2e2e2; --bg: #fff;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --dark: #f0f0f0; --body: #d8d8d8; --gray: #b0b0b0; --light: #8a8a8a;
    --rule: #3a3a3a; --bg: #16181c; --accent: #6ab3ff;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--body);
  font-family: "Source Sans 3", system-ui, -apple-system, sans-serif;
  font-size: 17px; line-height: 1.55;
  -webkit-text-size-adjust: 100%;
}
.wrap { max-width: 46rem; margin: 0 auto; padding: 3rem 16px 5rem; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header { display: flex; gap: 1.75rem; align-items: flex-start; margin-bottom: 2.5rem; }
header img {
  width: 132px; height: 132px; border-radius: 50%; object-fit: cover;
  flex-shrink: 0; border: 1px solid var(--rule);
}
h1 {
  font-family: Roboto, system-ui, sans-serif; font-weight: 300;
  font-size: clamp(2rem, 7vw, 3rem); margin: 0; color: var(--gray);
  line-height: 1.05; letter-spacing: -0.01em;
}
h1 strong { font-weight: 700; color: var(--dark); }
.role {
  color: var(--accent); font-variant: small-caps; letter-spacing: .06em;
  font-size: .95rem; margin: .35rem 0 0;
}
.where { color: var(--light); font-style: italic; font-size: .95rem; margin: .1rem 0 0; }
.langs { color: var(--gray); font-variant: small-caps; letter-spacing: .04em; font-size: .85rem; margin: .5rem 0 0; }
.contacts { margin: .6rem 0 0; font-size: .9rem; display: flex; flex-wrap: wrap; gap: .35rem 1rem; }
.about { font-style: italic; margin: 1.1rem 0 0; }

h2 {
  font-size: 1.5rem; font-weight: 700; color: var(--dark);
  margin: 2.75rem 0 .5rem; display: flex; align-items: center; gap: .75rem;
}
h2 .t { white-space: nowrap; }
h2 .lead { color: var(--accent); }
h2::after { content: ""; flex: 1; height: 1px; background: var(--rule); }

.entry { display: grid; grid-template-columns: 3.2rem 1fr; gap: 0 1.1rem; margin-top: 1.6rem; }
.entry .logo { display: flex; align-items: flex-start; justify-content: center; padding-top: .15rem; }
.entry .logo img { width: 100%; height: auto; }
.entry .head { min-width: 0; }
.line { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }
.title { font-weight: 700; color: var(--dark); }
/* An entry with more to say on hover. The dotted rule is the only hint a
   reader gets that there is something there, so it is not optional. */
.title[title] { text-decoration: underline dotted var(--light); text-underline-offset: .2em; cursor: help; }
.loc { color: var(--accent); font-style: italic; font-size: .9rem; white-space: nowrap; }
.org { color: var(--gray); font-variant: small-caps; letter-spacing: .03em; font-size: .95rem; }
.date { color: var(--gray); font-style: italic; font-size: .85rem; white-space: nowrap; }
.entry ul { grid-column: 2; margin: .5rem 0 0; padding-left: 1.1rem; }
.entry li { margin: .2rem 0; }

/* Two labelled columns of short cards, used by Grants and Awards and by
   Software and Tools. The mark column only exists where a section has marks;
   a card with no mark yet still reserves it, so one placeholder does not step
   the whole column left. */
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 0 2rem; align-items: start; }
.cards > section > h3 {
  font-size: .8rem; font-weight: 400; color: var(--light);
  font-variant: small-caps; letter-spacing: .06em;
  margin: 1.4rem 0 0; padding-bottom: .3rem; border-bottom: 1px solid var(--rule);
}
.card { margin-top: 1.1rem; }
.cards.marks .card { display: grid; grid-template-columns: 2.6rem 1fr; gap: 0 .7rem; }
.card .mark { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; }
.card .mark img { max-width: 100%; max-height: 100%; }
.card .line { align-items: baseline; gap: .6rem; }
.card .name { font-weight: 700; color: var(--dark); }
/* The name is a link but is not painted like one: with a figure in the accent
   colour on the same line, two blues compete and neither reads. */
.card .name a { color: inherit; }
.card .reach { color: var(--accent); font-size: .78rem; font-weight: 700; white-space: nowrap; }
.card .meta {
  color: var(--gray); font-variant: small-caps; letter-spacing: .03em;
  font-size: .8rem; margin: .1rem 0 0;
}
.card p.desc { margin: .3rem 0 0; font-size: .87rem; color: var(--gray); }
@media (max-width: 640px) { .cards { grid-template-columns: 1fr; } }

/* Teaching areas: what, at what level, and the topics inside it. Three columns
   so the level reads as a rail down the section rather than as prose. */
.intro { font-style: italic; margin: .8rem 0 0; }
.topics { display: grid; grid-template-columns: 9.5rem 4.25rem 1fr; gap: .9rem 1rem; margin-top: 1rem; }
.topics > h3 {
  grid-column: 1 / -1; font-size: .8rem; font-weight: 400; color: var(--light);
  font-variant: small-caps; letter-spacing: .06em;
  margin: .8rem 0 0; padding-bottom: .3rem; border-bottom: 1px solid var(--rule);
}
.topics > h3:first-child { margin-top: .3rem; }
.topics .area { font-weight: 700; color: var(--dark); }
.topics .level {
  color: var(--accent); font-weight: 700; font-variant: small-caps;
  letter-spacing: .04em; font-size: .8rem;
}
.topics .what { color: var(--gray); font-size: .92rem; }
/* Where and when it was taught. Corroboration rather than content, so it is
   small - but present, because an unsourced list of what somebody can teach is
   only a claim. */
.topics .where {
  display: block; margin-top: .15rem; color: var(--light);
  font-variant: small-caps; letter-spacing: .05em; font-size: .78rem;
}
@media (max-width: 640px) {
  .topics { grid-template-columns: 1fr; gap: .1rem; }
  .topics > h3 { margin-top: 1.4rem; }
  .topics .what { margin-bottom: .9rem; }
}

/* The bibliometrics plot. Its own SVG is transparent and drawn in mid grey and
   the accent, so it sits on either the light or the dark page without a second
   copy. */
.stats { display: grid; grid-template-columns: 3.2rem 1fr; gap: 0 1.1rem; margin-top: 1.2rem; }
.stats > * { grid-column: 2; }
.stats .plot { width: 100%; height: auto; }
.stats ul { margin: 1rem 0 0; padding-left: 1.1rem; }
.stats li { margin: .2rem 0; }
.stats .source {
  margin: .6rem 0 0; color: var(--light);
  font-variant: small-caps; letter-spacing: .06em; font-size: .75rem;
}

footer { margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--rule);
  color: var(--light); font-size: .85rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem; }

@media (max-width: 640px) {
  header { flex-direction: column; align-items: center; text-align: center; }
  .contacts { justify-content: center; }
  .about { text-align: left; }
  .line { flex-direction: column; gap: 0; }
  .loc, .date { white-space: normal; }
  .entry { grid-template-columns: 1fr; }
  .entry .logo { justify-content: flex-start; margin-bottom: .3rem; }
  .stats { grid-template-columns: 1fr; }
  .stats > * { grid-column: 1; }
}
"""


def render_entry(e: dict) -> str:
    """One entry row: mark, title and location, organisation and date, then
    bullets."""
    logo = e.get("logo")
    logo_html = (
        f'<div class="logo"><img src="img/logos/{logo}" alt=""></div>'
        if logo
        else '<div class="logo"></div>'
    )
    bullets = "".join(f"<li>{to_html(d)}</li>" for d in e.get("details", []))
    tip = e.get("tooltip")
    tip_attr = f' title="{html.escape(plain(tip), quote=True)}"' if tip else ""
    return (
        f'<article class="entry">{logo_html}<div class="head">'
        f'<div class="line"><span class="title"{tip_attr}>{to_html(e.get("title", ""))}</span>'
        f'<span class="loc">{to_html(e.get("location", "") or "")}</span></div>'
        f'<div class="line"><span class="org">{to_html(e.get("org", "") or "")}</span>'
        f'<span class="date">{to_html(e.get("date", "") or "")}</span></div>'
        f"</div>{f'<ul>{bullets}</ul>' if bullets else ''}</article>"
    )


def render_stats(data: dict) -> str:
    """The bibliometrics: the plot, then the notes, then the source.

    The source is required (validate.py enforces it): an undated citation count
    is exactly what a reader is entitled to be suspicious of.
    """
    figure = data.get("figure")
    # Every figure in the plot is repeated in the bullets underneath, so the alt
    # text can say what it shows rather than read it out.
    img = (
        f'<img class="plot" src="{html.escape(figure, quote=True)}" alt="Bar charts'
        " of publications and of citations per year, both rising steeply from"
        ' 2019.">'
        if figure
        else ""
    )
    notes = "".join(f"<li>{to_html(n)}</li>" for n in data.get("notes", []) or [])
    source = data.get("source")
    source_html = f'<p class="source">{to_html(source)}</p>' if source else ""
    return (
        f'<section class="stats">{img}'
        f"{f'<ul>{notes}</ul>' if notes else ''}"
        f"{source_html}</section>"
    )


# Column labels for the two card sections, in the order their kinds appear in
# CARD_KINDS. `logo_dir` is None for a section whose cards carry no marks.
CARD_HEADINGS = {
    "awards": (("Grants", "Awards"), None),
    "roles": (("Convening and Curriculum", "Supervision and Examining"), None),
    "service": (("School and University", "Editorial and Peer Review"), None),
    "engagement": (
        ("Public Engagement and Outreach", "Knowledge Exchange and Consultancy"),
        None,
    ),
    "tools": (("Software", "Measures and Paradigms"), "img/tools"),
}


def render_topics(data: dict) -> str:
    """The teaching areas table: a lead sentence, then area, level and topics,
    banded by the overarching group each area belongs to."""
    out, group = [], None
    for t in data.get("areas", []):
        g = t.get("group")
        if g != group:
            group = g
            if g:
                out.append(f"<h3>{html.escape(g)}</h3>")
        where = t.get("where")
        out.append(
            f'<div class="area">{to_html(t.get("area", ""))}</div>'
            f'<div class="level">{to_html(t.get("level", "") or "")}</div>'
            f'<div class="what">{to_html(t.get("topics", "") or "")}'
            f'{f'<span class="where">{to_html(where)}</span>' if where else ""}</div>'
        )
    lead = data.get("lead")
    lead_html = f'<p class="intro">{to_html(lead)}</p>' if lead else ""
    return f'{lead_html}<section class="topics">{"".join(out)}</section>'



def render_cards(items: list[dict], kind: str) -> str:
    """A card section: two labelled columns, split on each item's `kind`."""
    headings, logo_dir = CARD_HEADINGS[kind]
    kinds = CARD_KINDS[kind]

    def card(t: dict) -> str:
        name = html.escape(t.get("name", ""))
        url = t.get("url")
        label = f'<a href="{html.escape(url, quote=True)}">{name}</a>' if url else name
        reach, meta, desc = t.get("reach"), t.get("meta"), t.get("description")
        logo = t.get("logo")
        mark = ""
        if logo_dir:
            img = f'<img src="{logo_dir}/{logo}" alt="">' if logo else ""
            mark = f'<div class="mark">{img}</div>'
        return (
            f'<article class="card">{mark}<div>'
            f'<div class="line"><span class="name">{label}</span>'
            f'{f'<span class="reach">{to_html(reach)}</span>' if reach else ""}</div>'
            f'{f'<p class="meta">{to_html(meta)}</p>' if meta else ""}'
            f'{f'<p class="desc">{to_html(desc)}</p>' if desc else ""}'
            f"</div></article>"
        )

    cols = "".join(
        f"<section><h3>{html.escape(title)}</h3>"
        f'{"".join(card(t) for t in items if t.get("kind", kinds[0]) == k)}</section>'
        for title, k in zip(headings, kinds)
    )
    return f'<div class="cards{" marks" if logo_dir else ""}">{cols}</div>'


def build() -> str:
    meta = front_matter()
    name, surname = meta.get("name", ""), meta.get("surname", "")
    full_name = f"{name} {surname}".strip()
    www, email = meta.get("www", ""), meta.get("email", "")
    github = meta.get("github", "")
    orcid, scholar = meta.get("orcid", ""), meta.get("scholar", "")
    orcid_url = f"https://orcid.org/{orcid}" if orcid else None
    scholar_url = (
        f"https://scholar.google.com/citations?user={scholar}" if scholar else None
    )
    languages = meta.get("languages")

    contacts = []
    if email:
        contacts.append(f'<a href="mailto:{email}">{email}</a>')
    if www:
        contacts.append(f'<a href="https://{www}">{www}</a>')
    if github:
        contacts.append(f'<a href="https://github.com/{github}">github.com/{github}</a>')
    if orcid_url:
        contacts.append(f'<a href="{orcid_url}">orcid.org/{orcid}</a>')
    if scholar_url:
        contacts.append(f'<a href="{scholar_url}">Google Scholar</a>')

    body: list[str] = []
    jsonld_roles = []
    seen: set[str] = set()

    for heading, relpath, kind in sections():
        # These two are mappings rather than lists of entries.
        mapping = kind in ("stats", "topics")
        entries = load(relpath) if mapping else load_entries(relpath)
        if not entries:
            continue
        # A heading may carry more than one renderer call - Teaching has two -
        # and sections() reports it once per call. Write it out only the first
        # time, or the page grows a duplicate <h2> mid-section.
        if heading not in seen:
            seen.add(heading)
            lead, rest = heading[:3], heading[3:]
            body.append(
                f'<h2 id="{heading.lower().replace(" ", "-")}">'
                f'<span class="t"><span class="lead">{html.escape(lead)}</span>'
                f"{html.escape(rest)}</span></h2>"
            )

        if kind == "topics":
            body.append(render_topics(entries))
            continue

        if kind == "stats":
            body.append(render_stats(entries))
            continue

        if kind in CARD_HEADINGS:
            body.append(render_cards(entries, kind))
            continue

        for e in entries:
            body.append(render_entry(e))

            # A role is something held at a place, so `location` is what marks
            # one. It keeps grants and packages - which have a figure in that
            # corner, or nothing - out of the structured record.
            if e.get("org") and e.get("location"):
                jsonld_roles.append(
                    {
                        "@type": "OrganizationRole",
                        "roleName": plain(e.get("title", "")),
                        "startDate": plain(e.get("date", "") or ""),
                        "memberOf": {"@type": "Organization", "name": plain(e["org"])},
                    }
                )

    about = meta.get("aboutme", "").strip()
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": full_name,
        "givenName": name,
        "familyName": surname,
        "jobTitle": meta.get("position", ""),
        "description": plain(about),
        "email": f"mailto:{email}" if email else None,
        "url": f"https://{www}" if www else None,
        "image": meta.get("profilepic"),
        "knowsAbout": meta.get("keywords", []),
        "sameAs": [
            u
            for u in (
                f"https://github.com/{github}" if github else None,
                orcid_url,
                scholar_url,
            )
            if u
        ],
        "knowsLanguage": [
            re.sub(r"\s*\(.*\)$", "", part).strip()
            for part in (languages or "").split("·")
            if part.strip()
        ],
        "hasOccupation": jsonld_roles,
    }
    jsonld = {k: v for k, v in jsonld.items() if v}

    stamp = date.today().strftime("%B %Y")
    title = f"{full_name} - Curriculum Vitae"
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(plain(about)[:300])}">
<meta name="author" content="{html.escape(full_name)}">
<meta name="keywords" content="{html.escape(', '.join(meta.get('keywords', [])))}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:type" content="profile">
<meta property="og:description" content="{html.escape(plain(about)[:300])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;700&family=Source+Sans+3:ital,wght@0,300;0,400;0,700;1,300;1,400;1,700&display=swap" rel="stylesheet">
<style>{CSS.replace("__ACCENT__", ACCENT)}</style>
<script type="application/ld+json">
{json.dumps(jsonld, indent=2, ensure_ascii=False)}
</script>
</head>
<body>
<div class="wrap">
<header>
  <img src="{meta.get("profilepic", "")}" alt="Portrait of {html.escape(full_name)}">
  <div>
    <h1>{html.escape(name)} <strong>{html.escape(surname)}</strong></h1>
    <p class="role">{html.escape(meta.get("position", ""))}</p>
    <p class="where">{html.escape(meta.get("address", ""))}</p>
    <div class="contacts">{"".join(f"<span>{c}</span>" for c in contacts)}</div>
    {f'<p class="langs">Languages: {html.escape(languages)}</p>' if languages else ""}
    <p class="about">{to_html(about, strong="**")}</p>
  </div>
</header>
{chr(10).join(body)}
<footer>
  <span>{html.escape(full_name)} &middot; Curriculum Vitae &middot; {stamp}</span>
  <span><a href="cv.pdf">Download as PDF</a></span>
</footer>
</div>
</body>
</html>
"""


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()

    out = os.path.join(ROOT, "cv.html")
    io.open(out, "w", encoding="utf-8", newline="\n").write(build())
    print(f"wrote {os.path.relpath(out, ROOT)} ({os.path.getsize(out) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
