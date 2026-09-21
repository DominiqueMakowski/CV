"""Merge ../publications.bib with content/publications.yml into one rendered file.

    python tools/build_publications.py

Writes content/_publications.generated.yml, which cv.qmd renders and which
nothing should edit by hand: it is rewritten on every build. The two files it is
built from are the ones to edit - facts in the .bib at the repo root, editorial
decisions in content/publications.yml.

The formatting happens here rather than in Typst because it is bibliographic
convention, not layout: which name is bold, how initials are punctuated, where
the ampersand goes. Typst is left with the job it is good at, which is putting
the pieces on the page.
"""

from __future__ import annotations

import io
import os
import sys

import yaml

import bibtex

HERE = os.path.dirname(os.path.abspath(__file__))
CV = os.path.dirname(HERE)
REPO = os.path.dirname(CV)

BIB = os.path.join(REPO, "publications.bib")
CURATION = os.path.join(CV, "content", "publications.yml")
OUT = os.path.join(CV, "content", "_publications.generated.yml")


def render(entry: dict, highlight: bool) -> dict:
    equal = {int(i) for i in entry.get("equal", "").replace(",", " ").split() if i}
    authors = bibtex.format_authors(entry["author"], equal=equal)
    # An author list usually ends in an initial, which already carries the full
    # stop that separates it from the title. Adding another gives "Neves, A..".
    # Trailing bold and shared-authorship marks are stripped before the check,
    # since they sit outside the punctuation.
    if not authors.rstrip("*\\").endswith("."):
        authors += "."
    out = {
        "authors": authors,
        "title": bibtex.escape(entry["title"]),
        "venue": bibtex.venue_of(entry),
        "year": entry.get("year") or entry.get("status", "under review"),
    }
    url = bibtex.link_for(entry)
    if url:
        out["url"] = url
    notes = [n for n in (entry.get("equalnote"), entry.get("note")) if n]
    if notes:
        out["note"] = bibtex.escape("; ".join(notes))
    if highlight:
        out["highlight"] = True
    return out


def main() -> int:
    entries = bibtex.load(BIB)
    with io.open(CURATION, encoding="utf-8") as fh:
        curation = yaml.safe_load(fh)

    highlight = set(curation.get("highlight") or ())
    hidden = {h["key"] for h in (curation.get("hidden") or ())}

    claimed, themes, problems = set(), [], []
    for theme in curation.get("themes") or ():
        rendered = []
        for key in theme.get("keys") or ():
            if key in claimed:
                problems.append(f"{key}: listed in more than one theme")
                continue
            if key not in entries:
                problems.append(f"{key}: no such entry in publications.bib")
                continue
            claimed.add(key)
            rendered.append(render(entries[key], key in highlight))
        # Under review first, then newest first. Two stable passes rather than
        # one clever key: the second groups, the first orders within the group,
        # and entries that tie keep the order the curation file gives them, so a
        # deliberate ordering inside one year survives.
        rendered.sort(key=lambda e: e["year"], reverse=True)
        rendered.sort(key=lambda e: e["year"].isdigit())
        themes.append({"name": theme["name"], "entries": rendered})

    for key in entries:
        if key not in claimed and key not in hidden:
            problems.append(
                f"{key}: in publications.bib but in no theme and not hidden - "
                "add it to content/publications.yml"
            )
    for key in hidden:
        if key not in entries:
            problems.append(f"{key}: hidden, but no such entry in publications.bib")
    for key in highlight:
        if key not in claimed:
            problems.append(f"{key}: highlighted, but not shown in any theme")

    if problems:
        for p in problems:
            print("ERROR " + p, file=sys.stderr)
        return 1

    header = (
        "# GENERATED - do not edit. Rewritten by tools/build_publications.py from\n"
        "# ../../publications.bib (the facts) and content/publications.yml (the\n"
        "# editorial decisions). Edit those.\n"
    )
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header)
        yaml.safe_dump(
            themes, fh, allow_unicode=True, sort_keys=False, width=100_000
        )

    shown = sum(len(t["entries"]) for t in themes)
    print(
        f"wrote content/_publications.generated.yml "
        f"({shown} entries across {len(themes)} themes, {len(hidden)} hidden)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
