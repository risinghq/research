"""Write `sjr.csv`: the SJR best quartile of each journal in `sources.csv`, for
each year from 2021 to 2024.

SCImago's yearly lists sit behind a browser check, so they were saved by hand
from https://www.scimagojr.com/journalrank.php?out=xls&year=YEAR into one
folder as `sjr-YEAR.csv`. SCImago builds them from Scopus and asks to be cited
as the source. Only the journals that Peruvian articles appear in are kept.
"""

import argparse
import csv
import sys

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

OUT = Path(__file__).parent
YEARS = range(2021, 2025)


def bare(issn: str) -> str:
    return issn.replace("-", "").strip().upper()


def read_quartiles(path: Path) -> dict[str, str]:
    """Each ISSN in one year's list, with its best quartile; `-` when the
    journal is in Scopus without a quartile that year."""
    quartiles: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file, delimiter=";"):
            for issn in row["Issn"].split(","):
                if bare(issn):
                    quartiles[bare(issn)] = row["SJR Best Quartile"]
    return quartiles


def match(
    sources: Iterable[Mapping[str, str]], quartiles: Mapping[int, Mapping[str, str]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in sources:
        issns = [bare(i) for i in source["issn"].split()]
        for year, listed in quartiles.items():
            found = next((listed[i] for i in issns if i in listed), None)
            if found is not None:
                rows.append(
                    {"source": source["source"], "year": year, "quartile": found}
                )
    return rows


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Match Peru's journals to SJR.")
    parser.add_argument("lists", type=Path, help="folder with sjr-YEAR.csv files")
    args = parser.parse_args(argv)
    with (OUT / "sources.csv").open(encoding="utf-8", newline="") as file:
        sources = list(csv.DictReader(file))
    quartiles = {y: read_quartiles(args.lists / f"sjr-{y}.csv") for y in YEARS}
    rows = match(sources, quartiles)
    with (OUT / "sjr.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=["source", "year", "quartile"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    sys.stdout.write(f"matched {len({r['source'] for r in rows})} journals\n")


if __name__ == "__main__":
    main()
