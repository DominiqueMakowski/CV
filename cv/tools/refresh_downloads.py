"""Print a fresh `software:` block for content/impact.yml.

    python tools/refresh_downloads.py

The software counterpart of refresh_scholar.R, and run by hand for the same
reason: it needs the network, and a build that needs nothing but Quarto, Typst
and Python should not start depending on three web services. It prints YAML to
paste over the `software:` block, rather than writing the file, so the numbers
go through a diff and PROFILE.md > Impact before they reach the CV.

No account or key is needed for any of the three sources:

- CRAN downloads per year, from cranlogs (https://cranlogs.r-pkg.org). These
  are the RStudio/Posit mirror only, so they undercount CRAN as a whole.
- PyPI downloads per year, from ClickHouse's public copy of the PyPI download
  logs (the dataset behind https://clickpy.clickhouse.com). These are raw
  counts, mirrors and CI included, the same basis as Google's BigQuery table.
- Stars, from the GitHub API. Current totals only: listing *when* each star
  was given now needs a signed-in request, and the public GitHub events archive
  that would otherwise answer it thins out from mid-2025.

Afterwards: paste the block, move `partial-year` if the year has turned, put
the month in `source`, and run ./build.sh to redraw.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.parse
import urllib.request

EASYSTATS = ("insight", "datawizard", "parameters", "effectsize", "performance",
             "bayestestR", "correlation", "modelbased", "see", "report")

# `start` drops a first year that is only a release month or two: NeuroKit2
# reached PyPI on 29 October 2019, and two months drawn as a year would put a
# cliff at the start of the line that says nothing about use.
PACKAGES = [
    {"name": "easystats", "registry": "CRAN", "packages": EASYSTATS, "start": 2019,
     "repos": ["easystats/easystats"] + [f"easystats/{p}" for p in EASYSTATS]},
    {"name": "NeuroKit", "registry": "PyPI", "packages": ("neurokit2",), "start": 2020,
     "repos": ["neuropsychology/NeuroKit"]},
]

UA = {"User-Agent": "cv-refresh-downloads"}


def get(url: str, data: bytes | None = None):
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=120) as r:
        return r.read()


def cran(packages, year: int, today: dt.date) -> int:
    end = min(dt.date(year, 12, 31), today - dt.timedelta(days=1))
    url = (f"https://cranlogs.r-pkg.org/downloads/total/{year}-01-01:{end}/"
           + ",".join(packages))
    return sum(p["downloads"] for p in json.loads(get(url)))


def pypi(packages) -> dict[int, int]:
    names = ",".join(f"'{p}'" for p in packages)
    q = (f"SELECT toYear(date) AS y, sum(count) FROM pypi.pypi_downloads_per_day "
         f"WHERE project IN ({names}) GROUP BY y ORDER BY y FORMAT JSONCompact")
    rows = json.loads(get("https://sql-clickhouse.clickhouse.com/?user=demo", q.encode()))["data"]
    return {int(y): int(n) for y, n in rows}


def stars(repos) -> int:
    return sum(json.loads(get(f"https://api.github.com/repos/{r}"))["stargazers_count"]
               for r in repos)


def main() -> int:
    today = dt.date.today()
    print(f"# Fetched {today}. Paste over the `software:` block in content/impact.yml.")
    print("software:")
    for pkg in PACKAGES:
        years = range(pkg["start"], today.year + 1)
        if pkg["registry"] == "CRAN":
            counts = {y: cran(pkg["packages"], y, today) for y in years}
        else:
            got = pypi(pkg["packages"])
            counts = {y: got.get(y, 0) for y in years}
        print(f'  - name: "{pkg["name"]}"')
        print(f'    registry: "{pkg["registry"]}"')
        print(f'    stars: {stars(pkg["repos"])}')
        print("    history:")
        for y, n in counts.items():
            print(f"      - {{year: {y}, downloads: {n}}}")
        print(f"    # total {sum(counts.values()):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
