"""Check content/*.yml before rendering.

The renderer fails quietly: a mistyped key is dropped, an unbalanced bracket
swallows the rest of a sentence, a missing logo leaves a blank slot. All of
those produce a PDF that looks fine until someone reads it closely. This script
turns them into errors.

    python tools/validate.py

Exits non-zero if anything is wrong, so it can gate a build or a commit hook.
"""

from __future__ import annotations

import os
import subprocess
import sys

from cvdata import (
    CARD_KEYS,
    CARD_KINDS,
    CARD_LOGOS,
    ENTRY_KEYS,
    LANG_KEYS,
    LANG_KINDS,
    LANGS,
    LINK_RE,
    LOGOS,
    PUB_KEYS,
    PUB_THEME_KEYS,
    ROOT,
    STAT_KEYS,
    STATS_KEYS,
    TOPIC_KEYS,
    TOPICS_KEYS,
    TOOLS,
    load,
    load_entries,
    sections,
)

# Characters Typst reads as markup when a YAML string is evaluated. A literal
# one has to be backslash-escaped in the YAML.
TYPST_SPECIAL = "#$@<"

problems: list[str] = []


def err(where: str, msg: str) -> None:
    problems.append(f"{where}: {msg}")


def check_markup(where: str, s: str) -> None:
    """Catch the markup mistakes that survive rendering as damaged prose."""
    if s.count("(") != s.count(")"):
        err(where, f"unbalanced parentheses in {s[:60]!r}...")
    if s.count("[") != s.count("]"):
        err(where, f"unbalanced square brackets in {s[:60]!r}...")

    # A '[' that is not part of a [label](url) pair is almost always a typo.
    stripped = LINK_RE.sub("", s)
    if "](" in stripped:
        err(where, "malformed link: '](' outside a [label](url) pair")

    for ch in TYPST_SPECIAL:
        for i, c in enumerate(s):
            if c == ch and (i == 0 or s[i - 1] != "\\"):
                err(where, f"unescaped {ch!r} - write a backslash before it")
                break

    for _, url in LINK_RE.findall(s):
        if not url.startswith(("http://", "https://", "mailto:")):
            err(where, f"link target {url!r} is not an absolute URL")


def check_entry(
    where: str, e: dict, logo_dir: str = LOGOS, extra: set[str] = frozenset()
) -> None:
    if not isinstance(e, dict):
        err(where, f"expected a mapping, got {type(e).__name__}")
        return

    known = ENTRY_KEYS | set(extra)
    for key in set(e) - known:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(known))})")

    if not e.get("title"):
        err(where, "no title")

    logo = e.get("logo")
    if logo and not os.path.exists(os.path.join(logo_dir, logo)):
        err(where, f"logo {logo!r} not found in {os.path.basename(logo_dir)}/")

    details = e.get("details", [])
    if not isinstance(details, list):
        err(where, "'details' must be a list of bullets")
        details = []

    for field in ("title", "location", "org", "date"):
        if e.get(field) is not None:
            if not isinstance(e[field], str):
                err(where, f"{field!r} must be text")
            else:
                check_markup(f"{where} [{field}]", e[field])

    # Plain text, not markup: it lands in an HTML attribute, where a link or
    # emphasis would come out as literal brackets and asterisks.
    tip = e.get("tooltip")
    if tip is not None:
        if not isinstance(tip, str):
            err(where, "'tooltip' must be text")
        elif any(ch in tip for ch in "*[]_"):
            err(where, "'tooltip' is plain text - no links or emphasis")

    for i, d in enumerate(details, 1):
        if not isinstance(d, str):
            err(where, f"bullet {i} must be text, got {type(d).__name__}")
        else:
            check_markup(f"{where} [bullet {i}]", d)


def check_card(
    where: str, t: dict, kinds: tuple[str, ...], logo_dir: str = TOOLS
) -> None:
    if not isinstance(t, dict):
        err(where, f"expected a mapping, got {type(t).__name__}")
        return

    for key in set(t) - CARD_KEYS:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(CARD_KEYS))})")

    if not t.get("name"):
        err(where, "no name")

    # The card lands in whichever column its kind names, so a typo here silently
    # drops the item out of the section.
    kind = t.get("kind", kinds[0])
    if kind not in kinds:
        err(where, f"kind must be one of {', '.join(map(repr, kinds))}, got {kind!r}")

    logo = t.get("logo")
    if logo and not os.path.exists(os.path.join(logo_dir, logo)):
        err(where, f"logo {logo!r} not found in {os.path.basename(logo_dir)}/")

    url = t.get("url")
    if url and not str(url).startswith(("http://", "https://")):
        err(where, f"url {url!r} is not absolute")

    for field in ("name", "description", "meta", "reach"):
        if t.get(field) is not None:
            if not isinstance(t[field], str):
                err(where, f"{field!r} must be text")
            else:
                check_markup(f"{where} [{field}]", t[field])


def check_language(where: str, t: dict) -> None:
    if not isinstance(t, dict):
        err(where, f"expected a mapping, got {type(t).__name__}")
        return

    for key in set(t) - LANG_KEYS:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(LANG_KEYS))})")

    if not t.get("name"):
        err(where, "no name")

    # A typo here silently moves the tile into the other column.
    kind = t.get("kind", LANG_KINDS[0])
    if kind not in LANG_KINDS:
        err(
            where,
            f"kind must be one of {', '.join(map(repr, LANG_KINDS))}, got {kind!r}",
        )

    # Unlike an entry's logo, this one is the whole tile: a missing file leaves
    # a name and a level floating over nothing.
    logo = t.get("logo")
    if not logo:
        err(where, "no logo - run tools/make_languages.py")
    elif not os.path.exists(os.path.join(LANGS, logo)):
        err(where, f"logo {logo!r} not found in img/languages/")

    for field in ("name", "level"):
        if t.get(field) is not None:
            if not isinstance(t[field], str):
                err(where, f"{field!r} must be text")
            else:
                check_markup(f"{where} [{field}]", t[field])


def check_topic(where: str, t: dict) -> None:
    if not isinstance(t, dict):
        err(where, f"expected a mapping, got {type(t).__name__}")
        return

    for key in set(t) - TOPIC_KEYS:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(TOPIC_KEYS))})")

    if not t.get("area"):
        err(where, "no area")

    for field in ("group", "area", "level", "topics", "where"):
        if t.get(field) is not None:
            if not isinstance(t[field], str):
                err(where, f"{field!r} must be text")
            else:
                check_markup(f"{where} [{field}]", t[field])


def check_topics(where: str, data) -> None:
    if not isinstance(data, dict):
        err(where, f"top level must be a mapping, got {type(data).__name__}")
        return

    for key in set(data) - TOPICS_KEYS:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(TOPICS_KEYS))})")

    if data.get("lead") is not None:
        if not isinstance(data["lead"], str):
            err(where, "'lead' must be text")
        else:
            check_markup(f"{where} [lead]", data["lead"])

    areas = data.get("areas", [])
    if not isinstance(areas, list) or not areas:
        err(where, "'areas' must be a non-empty list of rows")
        return
    for i, t in enumerate(areas, 1):
        label = t.get("area", f"row {i}") if isinstance(t, dict) else f"row {i}"
        check_topic(f"{where} > {label}", t)


def check_stats(where: str, data) -> None:
    if not isinstance(data, dict):
        err(where, f"top level must be a mapping, got {type(data).__name__}")
        return

    for key in set(data) - STATS_KEYS:
        err(where, f"unknown key {key!r} (known: {', '.join(sorted(STATS_KEYS))})")

    figure = data.get("figure")
    if figure and not os.path.exists(os.path.join(ROOT, figure)):
        err(where, f"figure {figure!r} does not exist - run tools/make_impact.py")

    history = data.get("history", [])
    if not isinstance(history, list) or not history:
        err(where, "'history' must be a non-empty list of years")
        history = []
    years = []
    for i, row in enumerate(history, 1):
        at = f"{where} [year {i}]"
        if not isinstance(row, dict):
            err(at, f"expected a mapping, got {type(row).__name__}")
            continue
        for key in set(row) - STAT_KEYS:
            err(at, f"unknown key {key!r} (known: {', '.join(sorted(STAT_KEYS))})")
        for field in STAT_KEYS:
            if row.get(field) is not None and not isinstance(row[field], int):
                err(at, f"{field!r} must be a whole number")
        if "year" not in row:
            err(at, "no year")
        else:
            years.append(row["year"])
    # Out-of-order years would draw a plot whose bars are not in time order.
    if years != sorted(years):
        err(where, "history years are out of order")

    partial = data.get("partial-year")
    if partial is not None and partial not in years:
        err(where, f"partial-year {partial!r} is not one of the history years")

    for key, value in (data.get("totals") or {}).items():
        if key not in ("publications", "citations"):
            err(where, f"unknown total {key!r}")
        elif not isinstance(value, int):
            err(where, f"total {key!r} must be a whole number")

    # The figures go stale, and an undated citation count is the thing a reader
    # is entitled to be suspicious of. See content/README.md.
    if not data.get("source"):
        err(where, "no 'source' - date the snapshot these figures come from")

    for i, n in enumerate(data.get("notes", []) or [], 1):
        if not isinstance(n, str):
            err(where, f"note {i} must be text, got {type(n).__name__}")
        else:
            check_markup(f"{where} [note {i}]", n)


def check_publications(where: str, themes) -> None:
    """The generated publication list, and the two files it comes from.

    The generated file is rebuilt before every render, so what this really
    guards is the pair behind it: that every cite key resolves, that no entry in
    publications.bib is silently absent from the CV, and that the formatter is
    still emitting the fields the template reads. build_publications.py reports
    the first two itself and exits non-zero; running it from here means a plain
    `validate.py` catches them too, rather than only a full build.
    """
    if not isinstance(themes, list):
        err(where, "top level must be a list of themes")
        return
    if not themes:
        err(where, "no themes - did build_publications.py run?")
    for i, theme in enumerate(themes, 1):
        label = theme.get("name") if isinstance(theme, dict) else None
        at = f"{where} > {label or f'theme {i}'}"
        if not isinstance(theme, dict):
            err(at, "theme must be a mapping")
            continue
        for k in set(theme) - PUB_THEME_KEYS:
            err(at, f"unknown key {k!r}")
        if not theme.get("name"):
            err(at, "theme has no name")
        entries = theme.get("entries") or []
        if not entries:
            err(at, "theme has no entries")
        for e in entries:
            cite = (e.get("title") or "?")[:40] if isinstance(e, dict) else "?"
            at2 = f"{at} > {cite}"
            if not isinstance(e, dict):
                err(at2, "entry must be a mapping")
                continue
            for k in set(e) - PUB_KEYS:
                err(at2, f"unknown key {k!r}")
            for k in ("authors", "title", "venue", "year"):
                if not e.get(k):
                    err(at2, f"missing {k}")

    # Re-run the generator in check mode: it is the thing that knows whether
    # publications.bib and content/publications.yml still agree.
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "build_publications.py")],
        capture_output=True,
        text=True,
    )
    if proc.returncode:
        for line in proc.stderr.splitlines():
            if line.strip():
                err("publications.bib / content/publications.yml", line.replace("ERROR ", ""))


def main() -> int:
    found = sections()
    if not found:
        err("cv.qmd", "no sections found - is the cv-entries call intact?")

    for heading, relpath, kind in found:
        path = os.path.join(ROOT, relpath)
        if not os.path.exists(path):
            err(f"{heading}", f"{relpath} does not exist")
            continue
        if kind == "stats":
            check_stats(relpath, load(relpath))
            continue

        if kind == "topics":
            check_topics(relpath, load(relpath))
            continue

        if kind == "publications":
            check_publications(relpath, load(relpath))
            continue

        entries = load_entries(relpath)
        if not isinstance(entries, list):
            err(relpath, "top level must be a list of entries")
            continue
        for i, e in enumerate(entries, 1):
            label = f"item {i}"
            if isinstance(e, dict):
                label = e.get("title") or e.get("name") or label
            where = f"{relpath} > {label}"
            if kind == "entries":
                check_entry(where, e)
            elif kind == "languages":
                check_language(where, e)
            else:
                check_card(
                    where, e, CARD_KINDS[kind], CARD_LOGOS.get(kind, TOOLS)
                )

    if problems:
        print(f"{len(problems)} problem(s):\n", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # A publications file is a list of themes, so counting it like the others
    # would report 5 where the CV shows sixty-odd citations.
    n = 0
    for _, relpath, k in found:
        if k in ("stats", "topics"):
            continue
        if k == "publications":
            n += sum(len(t.get("entries") or ()) for t in load_entries(relpath))
        else:
            n += len(load_entries(relpath))
    print(f"OK - {n} entries across {len(found)} section(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
