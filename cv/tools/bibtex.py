"""A small BibTeX reader, and the citation formatting the CV needs.

Deliberately not a dependency. The rest of this build needs nothing but Quarto,
Typst and Python, and adding `bibtexparser` for one file would be the first
thing to break on a fresh machine. What is here handles the subset
../../publications.bib actually uses - braced fields, nested braces, UTF-8 - and
raises on anything it does not understand rather than guessing.
"""

from __future__ import annotations

import io
import re

# LaTeX-isms that survive in a hand-written .bib. Applied to every field value.
TEX = [
    (r"\&", "&"),
    (r"\%", "%"),
    (r"\_", "_"),
    ("---", "—"),
    ("--", "–"),
    ("``", "“"),
    ("''", "”"),
    ("~", " "),
]

# Characters Typst reads as markup. Escaped in every value before any of our own
# markup goes on, so a title containing one renders as itself. `*` is left
# alone: it never appears in a source field, and we emit it ourselves for bold
# and for shared-authorship marks.
TYPST_SPECIAL = "#@$\\_<>"

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.S)


def _fields(body: str) -> dict:
    """Split an entry body into fields, respecting nested braces."""
    out, i, n = {}, 0, len(body)
    while i < n:
        m = re.compile(r"\s*(\w+)\s*=\s*").match(body, i)
        if not m:
            break
        name, i = m.group(1).lower(), m.end()
        if body[i] == "{":
            depth, start = 0, i
            while i < n:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            value, i = body[start + 1 : i], i + 1
        elif body[i] == '"':
            j = body.index('"', i + 1)
            value, i = body[i + 1 : j], j + 1
        else:
            m2 = re.compile(r"[^,}]*").match(body, i)
            value, i = m2.group(0).strip(), m2.end()
        out[name] = " ".join(value.split())
        m3 = re.compile(r"\s*,\s*").match(body, i)
        i = m3.end() if m3 else n
    return out


def load(path: str) -> dict:
    """Parse a .bib into {cite key: {field: value}}, with `type` and `key`."""
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    # Strip whole-line % comments; they are documentation, not data.
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))

    entries, seen = {}, set()
    for m in ENTRY_RE.finditer(text):
        kind, key = m.group(1).lower(), m.group(2)
        if key in seen:
            raise ValueError(f"duplicate cite key in {path}: {key}")
        seen.add(key)
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        fields = _fields(text[m.end() : i - 1])
        for a, b in TEX:
            fields = {k: v.replace(a, b) for k, v in fields.items()}
        fields["type"], fields["key"] = kind, key
        entries[key] = fields
    return entries


# --- formatting -------------------------------------------------------------


def escape(s: str) -> str:
    for c in TYPST_SPECIAL:
        s = s.replace(c, "\\" + c)
    return s


def initials(given: str) -> str:
    """`Dominique` -> `D.`; `S. H. Annabel` -> `S. H. A.`; `Jean-Charles` -> `J.-C.`"""
    parts = []
    for tok in given.split():
        if tok.endswith("."):
            parts.append(tok)
        elif "-" in tok:
            parts.append("-".join(p[0] + "." for p in tok.split("-") if p))
        else:
            parts.append(tok[0] + ".")
    return " ".join(parts)


def split_authors(field: str) -> list:
    """`Last, First and Last, First` -> [(last, given), ...]."""
    out = []
    for name in re.split(r"\s+and\s+", field):
        name = name.strip()
        if "," in name:
            last, given = name.split(",", 1)
        else:  # `Given Last`, which this .bib does not use but which is legal
            bits = name.rsplit(" ", 1)
            last, given = (bits[1], bits[0]) if len(bits) == 2 else (name, "")
        out.append((last.strip(), given.strip()))
    return out


def format_authors(field: str, equal=(), me: str = "Makowski") -> str:
    """APA-ish author list, with the CV's own name in bold.

    `equal` is 1-based author positions sharing first or last authorship; they
    get an asterisk, as in the printed CV. The asterisk is emitted escaped,
    because Typst would otherwise read it as the start of bold text.
    """
    names, parts = split_authors(field), []
    for i, (last, given) in enumerate(names, start=1):
        text = escape(last) + (", " + escape(initials(given)) if given else "")
        # Bold the CV's owner, and only him: `Makowski, Anna Christina` is a
        # different person and a real co-author.
        #
        # One asterisk, not two. This is Typst markup, not Markdown: `*x*` is
        # bold and `**x**` is an empty bold followed by the text, which Typst
        # warns about and renders unbolded.
        if last == me and given.startswith("Dominique"):
            text = "*" + text + "*"
        if i in equal:
            text += "\\*"
        parts.append(text)
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] + ", & " + parts[1]
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def link_for(entry: dict):
    if entry.get("doi"):
        return "https://doi.org/" + entry["doi"]
    return entry.get("url") or None


def venue_of(entry: dict) -> str:
    """The italicised source, plus volume/issue/pages, as one markup string."""
    if entry["type"] == "incollection":
        out = "In _" + escape(entry.get("booktitle", "")) + "_"
        if entry.get("publisher"):
            out += ". " + escape(entry["publisher"])
        return out
    out = "_" + escape(entry.get("journal", "")) + "_"
    if entry.get("volume"):
        out += ", _" + escape(entry["volume"]) + "_"
        if entry.get("number"):
            out += "(" + escape(entry["number"]) + ")"
    if entry.get("pages"):
        out += ", " + escape(entry["pages"])
    return out
