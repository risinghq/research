"""How many global rankings place each Peruvian university first in Peru, in
Peru's top three, or anywhere, counted from the ranks in `ranks.csv`, beside the
counts Percy Mayta-Tristán posted on 2026-11-18.

`ranks.csv` was read by hand from each ranking's own pages, so the script reads
no network. Universities that share a rank in Peru share its `peru_rank`.
"""

import argparse
import csv
import json
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import figures


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

OUT = Path(__file__).parent
POSTED = "Mayta-Tristán, 2026-11-18"
SOURCE = (
    "Rankings and editions in the study's README; "
    "QS data: Source: QS Quacquarelli Symonds (www.qs.com). With permission."
)


@dataclass(frozen=True)
class Rank:
    ranking: str
    university: str
    peru_rank: int


@dataclass(frozen=True)
class Measure:
    key: str
    title: str
    subtitle: str
    counts: Callable[[int], bool]


MEASURES = (
    Measure(
        "leader",
        "Rankings that place the university first in Peru",
        "Global rankings, latest edition on 2026-11-18; ties share a place",
        lambda rank: rank == 1,
    ),
    Measure(
        "top3",
        "Rankings that place the university in Peru's top three",
        "Global rankings, latest edition on 2026-11-18; ties share a place",
        lambda rank: rank <= 3,
    ),
    Measure(
        "present",
        "Rankings that include the university",
        "Global rankings, latest edition on 2026-11-18",
        lambda _rank: True,
    ),
)


def read_ranks(path: Path) -> list[Rank]:
    with path.open(encoding="utf-8", newline="") as file:
        return [
            Rank(row["ranking"], row["university"], int(row["peru_rank"]))
            for row in csv.DictReader(file)
        ]


def read_original(path: Path) -> dict[str, dict[str, int]]:
    """The posted table: each university's count for each measure."""
    with path.open(encoding="utf-8", newline="") as file:
        return {
            row["university"]: {m.key: int(row[m.key]) for m in MEASURES}
            for row in csv.DictReader(file)
        }


def count(
    ranks: Sequence[Rank], universities: Sequence[str]
) -> dict[str, dict[str, int]]:
    """For each university, how many rankings meet each measure."""
    return {
        university: {
            m.key: sum(
                1
                for rank in ranks
                if rank.university == university and m.counts(rank.peru_rank)
            )
            for m in MEASURES
        }
        for university in universities
    }


def leaders_outside(ranks: Sequence[Rank], universities: Sequence[str]) -> list[str]:
    """The rankings whose first place in Peru is a university the post left out."""
    return sorted(
        f"{rank.ranking}: {rank.university}"
        for rank in ranks
        if rank.peru_rank == 1 and rank.university not in universities
    )


def chart(
    measure: Measure,
    now: Mapping[str, Mapping[str, int]],
    posted: Mapping[str, Mapping[str, int]],
) -> dict[str, object]:
    def points(table: Mapping[str, Mapping[str, int]]) -> list[dict[str, object]]:
        return [{"x": name, "y": row[measure.key]} for name, row in table.items()]

    return figures.chart(
        "bars",
        figures.Style(measure.title, measure.subtitle, SOURCE, "", 0),
        figures.Axis("category"),
        [{"label": "This study", "points": points(now)}],
        compare={"label": POSTED, "points": points(posted)},
    )


def numbers(
    ranks: Sequence[Rank],
    now: Mapping[str, Mapping[str, int]],
    posted: Mapping[str, Mapping[str, int]],
) -> dict[str, object]:
    compared = [
        {
            "university": university,
            "measure": m.key,
            "posted": row[m.key],
            "now": now[university][m.key],
        }
        for university, row in posted.items()
        for m in MEASURES
    ]
    return {
        "rankings": len({rank.ranking for rank in ranks}),
        "leaders_outside_post": leaders_outside(ranks, list(posted)),
        "differs_from_post": [row for row in compared if row["posted"] != row["now"]],
        "against_original": compared,
    }


def run(out: Path) -> dict[str, object]:
    ranks = read_ranks(OUT / "ranks.csv")
    posted = read_original(OUT / "original.csv")
    now = count(ranks, list(posted))
    for measure in MEASURES:
        figures.write(out, measure.key, chart(measure, now, posted))
    result = numbers(ranks, now, posted)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    (out / "numbers.json").write_text(text, encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Count the rankings per university.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    run(args.out)
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
