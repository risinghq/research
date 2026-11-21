"""Fetch the OpenAlex counts the study reads: `output.csv`, `groups.csv`,
`journals.csv`, `journal-years.csv`, `venues.csv`, `citing.csv` and
`articles-by-year.csv`.

OpenAlex works are CC0. Without an API key the requests share a daily budget
of 1,000 calls per address; a full fetch makes about 280. OpenAlex
updates continuously, so a later fetch gives slightly different counts.
"""

import argparse
import csv
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx2


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

OUT = Path(__file__).parent
BASE_URL = "https://api.openalex.org"
WINDOW = "2021-2024"
# OpenAlex dates about a thousand back-issue articles of UNMSM's own journals
# to 2014, which makes that year twice its neighbours for Peru as a whole.
YEARS = range(2015, 2026)
CORE = ",primary_location.source.is_core:true"
PERU = "authorships.institutions.country_code:PE"
# `cites:` takes at most 100 ids, so each sample is one request.
SAMPLE = 100
SEEDS = (1, 2, 3)
CITED = 10
VENUES = 20
JOURNALS = 10
FOLLOWED = ("UCV", "UNMSM", "PUCP", "UPCH", "Científica")

MEASURES = {
    "articles": "",
    "core": CORE,
    "top10": ",citation_normalized_percentile.is_in_top_10_percent:true",
}


class OpenAlex:
    def __init__(self, *, transport: httpx2.BaseTransport | None = None) -> None:
        self._http = httpx2.Client(base_url=BASE_URL, timeout=60, transport=transport)

    def close(self) -> None:
        self._http.close()

    def get(self, path: str, **params: str | int) -> dict[str, Any]:
        response = self._http.get(path, params=params)
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body

    def count(self, filters: str) -> int:
        body = self.get("/works", filter=filters, per_page=1, select="id")
        return int(body["meta"]["count"])

    def groups(self, filters: str, by: str) -> dict[str, int]:
        """Counts per group, keyed by the group's short OpenAlex id or value.
        OpenAlex returns at most the 200 largest groups."""
        body = self.get("/works", filter=filters, group_by=by)
        return {
            g["key"].rsplit("/", 1)[-1]: int(g["count"])
            for g in body["group_by"]
            if g["key"]
        }

    def sample(self, filters: str, size: int, seed: int) -> list[str]:
        body = self.get(
            "/works", filter=filters, sample=size, seed=seed, per_page=size, select="id"
        )
        return [w["id"].rsplit("/", 1)[-1] for w in body["results"]]

    def source(self, source: str) -> dict[str, Any]:
        return self.get(
            f"/sources/{source}", select="display_name,is_core,country_code"
        )


def read_universities(path: Path) -> list[dict[str, str]]:
    """The universities in SUNEDU's register that have an OpenAlex record."""
    with path.open(encoding="utf-8", newline="") as file:
        return [row for row in csv.DictReader(file) if row["openalex"]]


def articles(institutions: str, years: str) -> str:
    return (
        f"authorships.institutions.lineage:{institutions},"
        f"publication_year:{years},type:article"
    )


def output(
    client: OpenAlex, universities: Sequence[Mapping[str, str]]
) -> list[dict[str, object]]:
    """Each university's 2021 to 2024 articles and their subsets.

    One grouped request per measure returns the 200 largest institutions on
    Peruvian articles, foreign co-authors' included, so a small university can
    be missing from it. A missing university is counted on its own for
    articles and core articles; its top-10% count is left empty to stay inside
    the daily budget.
    """
    peru = f"{PERU},type:article,publication_year:{WINDOW}"
    grouped = {
        k: client.groups(peru + f, "authorships.institutions.lineage")
        for k, f in MEASURES.items()
    }
    rows: list[dict[str, object]] = []
    for u in universities:
        row: dict[str, object] = {"code": u["code"]}
        for k, f in MEASURES.items():
            if u["openalex"] in grouped[k]:
                row[k] = grouped[k][u["openalex"]]
            elif k in {"articles", "core"}:
                row[k] = client.count(articles(u["openalex"], WINDOW) + f)
            else:
                row[k] = ""
        rows.append(row)
    return rows


def group_of(university: Mapping[str, str]) -> str:
    if university["licence"] == "denied":
        return "denied"
    return university["management"]


def groups(
    client: OpenAlex, universities: Sequence[Mapping[str, str]]
) -> list[dict[str, object]]:
    """Articles a year by public, licensed private and denied universities,
    and by every Peruvian institution. An article shared by two universities of
    a group counts once for it."""
    span = f"{YEARS[0]}-{YEARS[-1]}"
    filters = {
        name: articles(
            "|".join(u["openalex"] for u in universities if group_of(u) == name), span
        )
        for name in ("public", "private", "denied")
    } | {"Peru": f"{PERU},type:article,publication_year:{span}"}
    rows: list[dict[str, object]] = []
    for name, base in filters.items():
        every = client.groups(base, "publication_year")
        core = client.groups(base + CORE, "publication_year")
        rows += [
            {
                "group": name,
                "year": year,
                "articles": every.get(str(year), 0),
                "core": core.get(str(year), 0),
            }
            for year in YEARS
        ]
    return rows


def journals(client: OpenAlex) -> list[dict[str, object]]:
    """The journals with most 2021 to 2024 Peruvian articles, with every
    article each published in those years."""
    peru = f"{PERU},type:article,publication_year:{WINDOW}"
    top = client.groups(
        peru + ",primary_location.source.type:journal", "primary_location.source.id"
    )
    rows: list[dict[str, object]] = []
    for source, count in list(top.items())[:JOURNALS]:
        info = client.source(source)
        total = client.count(
            f"primary_location.source.id:{source},type:article,publication_year:{WINDOW}"
        )
        rows.append(
            {
                "source": source,
                "journal": info["display_name"],
                "country": info["country_code"] or "",
                "core": info["is_core"],
                "peru": count,
                "articles": total,
            }
        )
    return rows


def journal_years(client: OpenAlex, sources: Sequence[str]) -> list[dict[str, object]]:
    """Articles a year in each journal, and those with a Peruvian author."""
    rows: list[dict[str, object]] = []
    span = f"{YEARS[0]}-{YEARS[-1]}"
    for source in sources:
        base = (
            f"primary_location.source.id:{source},type:article,publication_year:{span}"
        )
        every = client.groups(base, "publication_year")
        peru = client.groups(base + f",{PERU}", "publication_year")
        rows += [
            {
                "source": source,
                "year": year,
                "articles": every.get(str(year), 0),
                "peru": peru.get(str(year), 0),
            }
            for year in YEARS
        ]
    return rows


def venues(
    client: OpenAlex, universities: Sequence[Mapping[str, str]]
) -> list[dict[str, object]]:
    """Of each university's 2021 to 2024 articles, those in the five journals
    it published in most."""
    rows: list[dict[str, object]] = []
    for u in universities:
        top = client.groups(
            articles(u["openalex"], WINDOW) + ",primary_location.source.type:journal",
            "primary_location.source.id",
        )
        rows.append({"code": u["code"], "top5": sum(list(top.values())[:5])})
    return rows


def citing(
    client: OpenAlex, universities: Sequence[Mapping[str, str]]
) -> list[dict[str, object]]:
    """Who cites a random sample of each university's articles, one row per
    seed."""
    rows: list[dict[str, object]] = []
    for u in universities:
        institution = u["openalex"]
        for seed in SEEDS:
            ids = client.sample(articles(institution, WINDOW), SAMPLE, seed)
            cites = "cites:" + "|".join(ids)
            rows.append(
                {
                    "code": u["code"],
                    "seed": seed,
                    "sampled": len(ids),
                    "citing": client.count(cites),
                    "core": client.count(cites + CORE),
                    "dissertation": client.count(cites + ",type:dissertation"),
                    "same": client.count(
                        cites + f",authorships.institutions.lineage:{institution}"
                    ),
                }
            )
    return rows


def by_year(
    client: OpenAlex, universities: Sequence[Mapping[str, str]]
) -> list[dict[str, object]]:
    span = f"{YEARS[0]}-{YEARS[-1]}"
    rows: list[dict[str, object]] = []
    for u in universities:
        every = client.groups(articles(u["openalex"], span), "publication_year")
        core = client.groups(articles(u["openalex"], span) + CORE, "publication_year")
        rows += [
            {
                "code": u["code"],
                "year": year,
                "articles": every.get(str(year), 0),
                "core": core.get(str(year), 0),
            }
            for year in YEARS
        ]
    return rows


def largest(
    universities: Sequence[Mapping[str, str]],
    counts: Sequence[Mapping[str, object]],
    n: int,
) -> list[Mapping[str, str]]:
    size = {row["code"]: int(row["articles"]) for row in counts}  # type: ignore[call-overload]
    return sorted(universities, key=lambda u: -size[u["code"]])[:n]


def write(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fetch the study's OpenAlex counts.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    universities = read_universities(OUT / "universities.csv")
    client = OpenAlex()
    try:
        counts = output(client, universities)
        write(args.out / "output.csv", counts)
        write(args.out / "groups.csv", groups(client, universities))
        top = journals(client)
        write(args.out / "journals.csv", top)
        write(
            args.out / "journal-years.csv",
            journal_years(client, [str(row["source"]) for row in top[:3]]),
        )
        write(
            args.out / "venues.csv",
            venues(client, largest(universities, counts, VENUES)),
        )
        write(
            args.out / "citing.csv",
            citing(client, largest(universities, counts, CITED)),
        )
        followed = [u for u in universities if u["short"] in FOLLOWED]
        write(args.out / "articles-by-year.csv", by_year(client, followed))
    finally:
        client.close()
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
