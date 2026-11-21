"""Fetch the OpenAlex counts the study reads into `openalex.csv`,
`citing.csv` and `articles-by-year.csv`.

OpenAlex works are CC0. Without an API key the requests share a small daily
budget per address; a full fetch costs about $0.02 of it. OpenAlex updates
continuously, so a later fetch gives slightly different counts.
"""

import argparse
import csv
import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx2


if TYPE_CHECKING:
    from collections.abc import Sequence

OUT = Path(__file__).parent
BASE_URL = "https://api.openalex.org"
WINDOW = "2021-2024"
# OpenAlex dates about a thousand back-issue articles of UNMSM's own journals
# to 2014, which makes that year four times its neighbours.
YEARS = range(2015, 2026)
SAMPLE = 200
SEED = 7
CORE = ",primary_location.source.is_core:true"

# OpenAlex institution ids. `lineage` counts a university's child institutions
# with it.
UNIVERSITIES = {
    "PUCP": "I65285256",
    "UPCH": "I197097402",
    "UNMSM": "I192513696",
    "Científica": "I263512288",
    "UPC": "I1311157440",
    "UNALM": "I79080234",
    "UPN": "I42923333",
    "Pacífico": "I919628346",
    "ULima": "I192703252",
    "USMP": "I224954996",
    "UNTRM": "I3133295647",
    "UTP": "I4210148428",
    "UCV": "I2802656227",
    "USIL": "I271457894",
}

MEASURES = {
    "articles": "",
    "core": CORE,
    "international": ",countries_distinct_count:>1",
    "top10": ",citation_normalized_percentile.is_in_top_10_percent:true",
}


class OpenAlex:
    def __init__(self, *, transport: httpx2.BaseTransport | None = None) -> None:
        self._http = httpx2.Client(base_url=BASE_URL, timeout=60, transport=transport)

    def close(self) -> None:
        self._http.close()

    def works(self, **params: str | int) -> dict[str, Any]:
        response = self._http.get("/works", params=params)
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body

    def count(self, filters: str) -> int:
        return int(self.works(filter=filters, per_page=1, select="id")["meta"]["count"])

    def groups(self, filters: str, by: str) -> dict[str, int]:
        body = self.works(filter=filters, group_by=by)
        return {g["key"]: int(g["count"]) for g in body["group_by"]}

    def sample(self, filters: str, size: int, seed: int) -> list[str]:
        body = self.works(
            filter=filters, sample=size, seed=seed, per_page=size, select="id"
        )
        return [w["id"].rsplit("/", 1)[-1] for w in body["results"]]


def articles(institution: str, years: str) -> str:
    return (
        f"authorships.institutions.lineage:{institution},"
        f"publication_year:{years},type:article"
    )


def measures(client: OpenAlex) -> list[dict[str, object]]:
    return [
        {"university": name}
        | {k: client.count(articles(i, WINDOW) + f) for k, f in MEASURES.items()}
        for name, i in UNIVERSITIES.items()
    ]


def citing(client: OpenAlex) -> list[dict[str, object]]:
    """Who cites a random sample of each university's articles.

    `cites:` takes at most 100 ids, so the sample is split. A work that cites
    articles in both halves counts twice; with 200 articles that is rare.
    """
    rows: list[dict[str, object]] = []
    for name, institution in UNIVERSITIES.items():
        ids = client.sample(articles(institution, WINDOW), SAMPLE, SEED)
        counts = dict.fromkeys(("citing", "core", "dissertation", "same"), 0)
        for start in range(0, len(ids), 100):
            cites = "cites:" + "|".join(ids[start : start + 100])
            counts["citing"] += client.count(cites)
            counts["core"] += client.count(cites + CORE)
            counts["dissertation"] += client.count(cites + ",type:dissertation")
            counts["same"] += client.count(
                cites + f",authorships.institutions.lineage:{institution}"
            )
        rows.append({"university": name, "sampled": len(ids)} | counts)
    return rows


def by_year(client: OpenAlex) -> list[dict[str, object]]:
    span = f"{YEARS[0]}-{YEARS[-1]}"
    rows: list[dict[str, object]] = []
    for name, institution in UNIVERSITIES.items():
        every = client.groups(articles(institution, span), "publication_year")
        core = client.groups(articles(institution, span) + CORE, "publication_year")
        rows += [
            {
                "university": name,
                "year": year,
                "articles": every.get(str(year), 0),
                "core": core.get(str(year), 0),
            }
            for year in YEARS
        ]
    return rows


def write(path: Path, rows: Sequence[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fetch the study's OpenAlex counts.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    client = OpenAlex()
    try:
        write(args.out / "openalex.csv", measures(client))
        write(args.out / "citing.csv", citing(client))
        write(args.out / "articles-by-year.csv", by_year(client))
    finally:
        client.close()
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
