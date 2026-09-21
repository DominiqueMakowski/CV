"""Shared loading of the CV's content: the qmd front matter and content/*.yml.

Both tools/validate.py and tools/build_html.py read the CV through here, so the
YAML files stay the single source for every output.
"""

from __future__ import annotations

import io
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
LOGOS = os.path.join(ROOT, "img", "logos")
LANGS = os.path.join(ROOT, "img", "languages")

# Keys an entry in a content/*.yml file may carry. Anything else is a typo, and
# a typo'd key fails silently in the renderer, so validate.py rejects it.
# `tooltip` is plain text shown on hover in the web version only; the PDF has
# no equivalent and ignores it.
ENTRY_KEYS = {"title", "location", "org", "date", "logo", "details", "tooltip"}

# Same, for one card of a `cv-tools` or `cv-awards` section.
CARD_KEYS = {"name", "url", "logo", "description", "meta", "reach", "kind"}

# The `kind` values each of those sections splits its two columns on.
CARD_KINDS = {
    "tools": ("software", "measure"),
    "awards": ("grant", "award"),
    "roles": ("convening", "supervision"),
    "service": ("leadership", "editorial"),
    "engagement": ("outreach", "exchange"),
    "talks": ("invited", "conference"),
    # One band rather than two columns, so there is a single kind and no card
    # ever names it.
    "projects": ("project",),
}

# Keys one tile of a `cv-languages` section may carry, and the two groups it
# splits them into: what is spoken, and what is programmed in.
LANG_KEYS = {"name", "level", "logo", "kind"}
LANG_KINDS = ("spoken", "code")

# Keys one theme of a `cv-publications` section may carry, and one rendered
# citation within it. Both belong to content/_publications.generated.yml, which
# tools/build_publications.py writes - nothing hand-edits them, but validating
# them still catches a formatter change that quietly drops a field.
PUB_THEME_KEYS = {"name", "entries"}
PUB_KEYS = {"authors", "title", "venue", "year", "url", "note", "highlight"}

# Keys one row of a `cv-topics` section may carry.
TOPIC_KEYS = {"group", "area", "level", "topics", "where"}

# The top level of a `cv-topics` file, which is a mapping rather than a list.
TOPICS_KEYS = {"lead", "areas"}

# Same, for one year of a `cv-stats` file's history.
STAT_KEYS = {"year", "publications", "citations"}

# The top level of a `cv-stats` file, which is a mapping rather than a list.
STATS_KEYS = {"figure", "totals", "history", "partial-year", "notes", "source"}

TOOLS = os.path.join(ROOT, "img", "tools")
PROJECTS = os.path.join(ROOT, "img", "projects")

# Where a card section's `logo` is looked up. Cards in the sections not listed
# here carry no picture, and are checked against img/tools/ so that a stray one
# is still caught.
CARD_LOGOS = {"projects": PROJECTS}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def front_matter(path: str | None = None) -> dict:
    """The YAML block at the top of cv.qmd."""
    path = path or os.path.join(ROOT, "cv.qmd")
    text = io.open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        raise ValueError(f"{path} has no YAML front matter")
    _, block, _ = text.split("---", 2)
    return yaml.safe_load(block)


# A section is a level-1 heading followed by the renderer call under it. The
# call may be wrapped across lines - some of them take several arguments - so
# this matches over the whole document rather than line by line. Matching per
# line silently dropped a section the day one of the calls grew a second
# argument and got reformatted, which is the kind of failure this module exists
# to prevent.
SECTION_RE = re.compile(
    r"^\#\s+(?P<heading>.+?)\s*$"
    r"|cv-(?P<kind>entries|tools|stats|awards|roles|topics|service"
    r"|engagement|talks|languages|projects|publications)"
    r'\(\s*yaml\(\s*"(?P<path>[^"]+)"\s*\)',
    re.MULTILINE,
)


def sections(path: str | None = None) -> list[tuple[str, str, str]]:
    """Section headings of cv.qmd, each with the YAML it renders and how.

    Returns (heading, yaml path, kind) where kind is the renderer called:
    "entries", "tools", "awards", "roles", "topics", "languages" or "stats".
    A heading may have more than one call under it, and then appears once per
    call. Reads the document rather than a separate manifest, so adding a
    section in one place is enough.
    """
    path = path or os.path.join(ROOT, "cv.qmd")
    text = io.open(path, encoding="utf-8").read()
    _, _, body = text.split("---", 2)
    out, heading = [], None
    for m in SECTION_RE.finditer(body):
        if m.group("heading") is not None:
            heading = m.group("heading")
        elif heading:
            out.append((heading, m.group("path"), m.group("kind")))
    return out


def load(relpath: str):
    """A content file's YAML, given a path relative to the project root."""
    with io.open(os.path.join(ROOT, relpath), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_entries(relpath: str) -> list[dict]:
    """Entries from a content file. A `cv-stats` file is a mapping, not a list;
    read that one with `load`."""
    return load(relpath) or []
