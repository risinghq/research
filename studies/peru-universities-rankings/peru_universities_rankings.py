"""Count how many global rankings place each Peruvian university first in Peru,
in Peru's top three, or anywhere, beside the counts Percy Mayta-Tristán posted
on 2026-11-18, and set the rankings beside what OpenAlex and the Leiden Ranking
show of each university's articles.

`ranks.csv` and `leiden.csv` were read by hand from each ranking's own pages.
`openalex.py` fetches the OpenAlex files; this script reads no network.
Universities that share a rank in Peru share its `peru_rank`.
"""

import argparse
import csv
import json
import sys

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import figures


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

OUT = Path(__file__).parent
POSTED = "Mayta-Tristán, 2026-11-18"
RANKS_SOURCE = (
    "Rankings and editions in the study's README; "
    "QS data: Source: QS Quacquarelli Symonds (www.qs.com). With permission; "
    "Times Higher Education rankings with permission"
)
OPENALEX_SOURCE = "OpenAlex, fetched 2026-11-21 (CC0)"
LEIDEN_SOURCE = "OpenAlex, fetched 2026-11-21; CWTS Leiden Ranking Open Edition 2026"
# The universities the yearly charts follow: the five with most articles.
FOLLOWED = ("UCV", "UNMSM", "PUCP", "UPCH", "Científica")


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_ranks(path: Path) -> list[Rank]:
    return [
        Rank(row["ranking"], row["university"], int(row["peru_rank"]))
        for row in read_csv(path)
    ]


def read_table(path: Path) -> dict[str, dict[str, float]]:
    """A CSV keyed by its `university` column, every other column a number."""
    return {
        row.pop("university"): {k: float(v) for k, v in row.items()}
        for row in read_csv(path)
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


def leaders(ranks: Sequence[Rank]) -> dict[str, list[str]]:
    """Each ranking's first place in Peru; a tie lists every university."""
    result: dict[str, list[str]] = {}
    for rank in ranks:
        if rank.peru_rank == 1:
            result.setdefault(rank.ranking, []).append(rank.university)
    return result


def share(part: float, whole: float) -> float:
    return round(100 * part / whole, 1)


def output_shares(table: Mapping[str, Mapping[str, float]]) -> dict[str, object]:
    """Each university's articles and the share of them in each subset."""
    return {
        name: {
            "articles": int(row["articles"]),
            "core_pct": share(row["core"], row["articles"]),
            "international_pct": share(row["international"], row["articles"]),
            "top10_pct": share(row["top10"], row["articles"]),
        }
        for name, row in table.items()
    }


def citing_shares(table: Mapping[str, Mapping[str, float]]) -> dict[str, object]:
    """Of the works citing each university's sampled articles, the share in core
    journals, the share that are theses and the share by the same university."""
    return {
        name: {
            "sampled": int(row["sampled"]),
            "citing": int(row["citing"]),
            "core_pct": share(row["core"], row["citing"]),
            "dissertation_pct": share(row["dissertation"], row["citing"]),
            "same_university_pct": share(row["same"], row["citing"]),
        }
        for name, row in table.items()
    }


def bars(
    title: str,
    subtitle: str,
    source: str,
    values: Mapping[str, float],
    *,
    unit: str = "",
    decimals: int = 0,
    label: str = "This study",
    compare: Mapping[str, object] | None = None,
) -> dict[str, object]:
    points = [{"x": name, "y": y} for name, y in values.items()]
    return figures.chart(
        "bars",
        figures.Style(title, subtitle, source, unit, decimals),
        figures.Axis("category"),
        [{"label": label, "points": points}],
        compare=compare,
    )


def ranking_chart(
    measure: Measure,
    now: Mapping[str, Mapping[str, int]],
    posted: Mapping[str, Mapping[str, int]],
) -> dict[str, object]:
    def column(table: Mapping[str, Mapping[str, int]]) -> dict[str, float]:
        return {name: row[measure.key] for name, row in table.items()}

    posted_points = [{"x": k, "y": v} for k, v in column(posted).items()]
    return bars(
        measure.title,
        measure.subtitle,
        RANKS_SOURCE,
        column(now),
        compare={"label": POSTED, "points": posted_points},
    )


def core_chart(table: Mapping[str, Mapping[str, float]]) -> dict[str, object]:
    values = {name: share(row["core"], row["articles"]) for name, row in table.items()}
    return bars(
        "Articles in core journals",
        "Share of each university's 2021 to 2024 journal articles",
        OPENALEX_SOURCE,
        dict(sorted(values.items(), key=lambda kv: -kv[1])),
        unit="%",
        label="Share of articles",
    )


def top10_chart(
    openalex: Mapping[str, Mapping[str, float]],
    leiden: Mapping[str, Mapping[str, float]],
) -> dict[str, object]:
    every = {
        name: share(openalex[name]["top10"], openalex[name]["articles"])
        for name in sorted(leiden, key=lambda n: -leiden[n]["pp_top10"])
    }
    core = [{"x": name, "y": row["pp_top10"]} for name, row in leiden.items()]
    return bars(
        "Articles among the world's 10% most cited",
        "2021 to 2024; bars count every citing work, ticks count core journals only",
        LEIDEN_SOURCE,
        every,
        unit="%",
        decimals=1,
        label="OpenAlex, every citing work",
        compare={"label": "Leiden Ranking, core only", "points": core},
    )


def citing_chart(citing: Mapping[str, Mapping[str, float]]) -> dict[str, object]:
    values = {name: share(row["core"], row["citing"]) for name, row in citing.items()}
    ordered = dict(sorted(values.items(), key=lambda kv: -kv[1]))
    return bars(
        "Citations that come from core journals",
        "Works citing a random 200 of each university's 2021 to 2024 articles",
        OPENALEX_SOURCE,
        ordered,
        unit="%",
        label="Share of citing works",
    )


def yearly_chart(
    rows: Sequence[Mapping[str, str]], column: str, title: str, subtitle: str
) -> dict[str, object]:
    series = [
        {
            "label": name,
            "points": [
                {"x": row["year"], "y": int(row[column])}
                for row in rows
                if row["university"] == name
            ],
        }
        for name in FOLLOWED
    ]
    return figures.chart(
        "line",
        figures.Style(title, subtitle, OPENALEX_SOURCE, "articles", 0),
        figures.Axis("year"),
        series,
    )


def numbers(
    ranks: Sequence[Rank],
    now: Mapping[str, Mapping[str, int]],
    posted: Mapping[str, Mapping[str, int]],
    openalex: Mapping[str, Mapping[str, float]],
    citing: Mapping[str, Mapping[str, float]],
    leiden: Mapping[str, Mapping[str, float]],
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
    first = leaders(ranks)
    return {
        "rankings": len({rank.ranking for rank in ranks}),
        "leaders": first,
        "leader_counts": dict(Counter(u for names in first.values() for u in names)),
        "leaders_outside_post": sorted(
            f"{ranking}: {name}"
            for ranking, names in first.items()
            for name in names
            if name not in posted
        ),
        "differs_from_post": [row for row in compared if row["posted"] != row["now"]],
        "against_original": compared,
        "openalex": output_shares(openalex),
        "citing": citing_shares(citing),
        "leiden": {
            name: {"p": int(row["p"]), "pp_top10": row["pp_top10"]}
            for name, row in leiden.items()
        },
    }


def run(out: Path) -> dict[str, object]:
    ranks = read_ranks(OUT / "ranks.csv")
    posted = {
        name: {k: int(v) for k, v in row.items()}
        for name, row in read_table(OUT / "original.csv").items()
    }
    openalex = read_table(OUT / "openalex.csv")
    citing = read_table(OUT / "citing.csv")
    leiden = read_table(OUT / "leiden.csv")
    yearly = read_csv(OUT / "articles-by-year.csv")
    now = count(ranks, list(posted))
    charts = {m.key: ranking_chart(m, now, posted) for m in MEASURES} | {
        "core-share": core_chart(openalex),
        "top10": top10_chart(openalex, leiden),
        "citing": citing_chart(citing),
        "articles": yearly_chart(
            yearly,
            "articles",
            "Journal articles a year",
            "Articles with an author at the university, by year published",
        ),
        "core-articles": yearly_chart(
            yearly,
            "core",
            "Journal articles a year in core journals",
            "Core journals as OpenAlex marks them, the set the Leiden Ranking counts",
        ),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    result = numbers(ranks, now, posted, openalex, citing, leiden)
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
