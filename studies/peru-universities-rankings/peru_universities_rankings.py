"""Measure the research record of the universities in SUNEDU's register from
OpenAlex, and set the global rankings' first places in Peru beside it.

`universities.csv` is SUNEDU's register with each university's OpenAlex id.
`ranks.csv`, `leiden.csv` and `staff.csv` were read by hand from each source's
own pages. `openalex.py` fetches the OpenAlex files; this script reads no
network.
"""

import argparse
import csv
import json
import sys

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import figures


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

OUT = Path(__file__).parent
OPENALEX = "OpenAlex, fetched 2026-11-21 (CC0)"
REGISTER = f"{OPENALEX}; SUNEDU register (ODC-BY)"
SJR = f"{OPENALEX}; SCImago Journal Rank"
# An article whose journal SJR does not list in the article's year, or whose
# journal has no ISSN in OpenAlex.
UNLISTED = "not in SJR"
# Full journal names overflow the legend.
JOURNALS = {
    "Ciencia Latina Revista Científica Multidisciplinar": "Ciencia Latina (Paraguay)",
    "Revista de Climatología": "Revista de Climatología (Spain)",
    "Horizontes Revista de Investigación en Ciencias de la Educación": (
        "Horizontes (Bolivia)"
    ),
}
LEIDEN = "OpenAlex, fetched 2026-11-21; CWTS Leiden Ranking Open Edition 2026"
STAFF = "OpenAlex, fetched 2026-11-21; THE World University Rankings 2027 data, with permission"
WINDOW = "2021 to 2024"
GROUPS = {
    "public": "Public",
    "private": "Private, licensed",
    "denied": "Licence denied",
}
FOLLOWED = ("UCV", "UNMSM", "PUCP", "UPCH", "Científica")
SHOWN = 20


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def share(part: float, whole: float) -> float:
    return round(100 * part / whole, 1)


def label(university: Mapping[str, str]) -> str:
    if not university["short"]:
        message = f"{university['name']} is charted but has no short name"
        raise ValueError(message)
    return university["short"]


def bars(
    style: figures.Style, values: Mapping[str, float], series: str
) -> dict[str, object]:
    points = [{"x": name, "y": y} for name, y in values.items()]
    return figures.chart(
        "bars", style, figures.Axis("category"), [{"label": series, "points": points}]
    )


def group_of(university: Mapping[str, str]) -> str:
    return "denied" if university["licence"] == "denied" else university["management"]


def descending(values: Mapping[str, float]) -> dict[str, float]:
    return dict(sorted(values.items(), key=lambda kv: -kv[1]))


class Record:
    """The OpenAlex counts of every university with an OpenAlex record."""

    def __init__(self, folder: Path) -> None:
        self.universities = {
            u["code"]: u for u in read_csv(folder / "universities.csv")
        }
        self.output = {
            row["code"]: {k: int(v) for k, v in row.items() if k != "code" and v}
            for row in read_csv(folder / "output.csv")
        }

    def largest(self, n: int, measure: str = "articles") -> list[str]:
        return sorted(self.output, key=lambda c: -self.output[c][measure])[:n]

    def short(self, code: str) -> str:
        return label(self.universities[code])


def concentration_chart(record: Record) -> dict[str, object]:
    top = record.largest(15, "core")
    return bars(
        figures.Style(
            "Articles in core journals",
            f"Journal articles {WINDOW}; the 15 universities with most",
            REGISTER,
            "",
        ),
        {record.short(c): record.output[c]["core"] for c in top},
        "Core articles",
    )


def core_share_chart(record: Record) -> dict[str, object]:
    top = record.largest(SHOWN)
    values = {
        record.short(c): share(record.output[c]["core"], record.output[c]["articles"])
        for c in top
    }
    return bars(
        figures.Style(
            "Share of articles in core journals",
            f"The {SHOWN} universities with most journal articles, {WINDOW}",
            OPENALEX,
            "%",
        ),
        descending(values),
        "Share in core journals",
    )


def venues_chart(
    record: Record, venues: Sequence[Mapping[str, str]]
) -> dict[str, object]:
    values = {
        record.short(row["code"]): share(
            int(row["top5"]), record.output[row["code"]]["articles"]
        )
        for row in venues
    }
    return bars(
        figures.Style(
            "Articles in the university's five most-used journals",
            f"Share of journal articles, {WINDOW}; the {SHOWN} universities with most",
            OPENALEX,
            "%",
        ),
        descending(values),
        "Share in five journals",
    )


def per_staff(record: Record, staff: Sequence[Mapping[str, str]]) -> dict[str, float]:
    """Core articles in the window per academic staff member, with staff taken
    as THE's student count over its students per staff."""
    by_short = {
        u["short"]: code for code, u in record.universities.items() if u["short"]
    }
    return descending(
        {
            row["university"]: round(
                record.output[by_short[row["university"]]]["core"]
                / (int(row["students"]) / float(row["students_per_staff"])),
                2,
            )
            for row in staff
        }
    )


def staff_chart(values: Mapping[str, float]) -> dict[str, object]:
    return bars(
        figures.Style(
            "Core articles per academic staff member",
            f"Core-journal articles {WINDOW} over staff in THE's 2027 data",
            STAFF,
            "",
            2,
        ),
        values,
        "Core articles per staff",
    )


def group_lines(
    rows: Sequence[Mapping[str, str]], column: str, title: str
) -> dict[str, object]:
    series = [
        {
            "label": name,
            "points": [
                {"x": row["year"], "y": int(row[column])}
                for row in rows
                if row["group"] == key
            ],
        }
        for key, name in GROUPS.items()
    ]
    return figures.chart(
        "line",
        figures.Style(
            title,
            "Articles with an author at a university of the group; 2025 still filling",
            REGISTER,
            "articles",
        ),
        figures.Axis("year"),
        series,
    )


def journals_chart(
    journals: Sequence[Mapping[str, str]], years: Sequence[Mapping[str, str]]
) -> dict[str, object]:
    names = {row["source"]: row["journal"] for row in journals}
    series = [
        {
            "label": JOURNALS.get(names[source], names[source]),
            "points": [
                {"x": row["year"], "y": int(row["peru"])}
                for row in years
                if row["source"] == source
            ],
        }
        for source in dict.fromkeys(row["source"] for row in years)
    ]
    return figures.chart(
        "line",
        figures.Style(
            "Peruvian articles in three foreign journals",
            f"Articles a year with a Peruvian author, in the three journals with most "
            f"of them in {WINDOW}; none is core",
            OPENALEX,
            "articles",
        ),
        figures.Axis("year"),
        series,
    )


def citing_shares(
    record: Record, rows: Sequence[Mapping[str, str]]
) -> dict[str, dict[str, object]]:
    """Per university, the share of works citing its sampled articles in core
    journals, theses and by the same university: pooled over the seeds, with
    the lowest and highest single seed."""
    by: defaultdict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by[row["code"]].append(row)
    result: dict[str, dict[str, object]] = {}
    for code, seeds in by.items():
        entry: dict[str, object] = {"samples": len(seeds)}
        for key in ("core", "dissertation", "same"):
            each = [share(int(s[key]), int(s["citing"])) for s in seeds]
            pooled = share(
                sum(int(s[key]) for s in seeds), sum(int(s["citing"]) for s in seeds)
            )
            entry[key] = {"pct": pooled, "low": min(each), "high": max(each)}
        result[record.short(code)] = entry
    return result


def citing_chart(shares: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    core = {name: entry["core"] for name, entry in shares.items()}
    order = sorted(core, key=lambda n: -core[n]["pct"])  # type: ignore[index]
    points = [
        {
            "x": name,
            "y": core[name]["pct"],  # type: ignore[index]
            "low": core[name]["low"],  # type: ignore[index]
            "high": core[name]["high"],  # type: ignore[index]
        }
        for name in order
    ]
    return figures.chart(
        "bars",
        figures.Style(
            "Citations that come from core journals",
            "Works citing three random samples of 100 articles each, 2021 to 2024; "
            "whiskers span the samples",
            OPENALEX,
            "%",
        ),
        figures.Axis("category"),
        [{"label": "Share of citing works", "points": points}],
    )


def top10_chart(
    record: Record, leiden: Mapping[str, Mapping[str, str]]
) -> dict[str, object]:
    by_short = {
        u["short"]: code for code, u in record.universities.items() if u["short"]
    }
    every = descending(
        {
            name: share(
                record.output[by_short[name]]["top10"],
                record.output[by_short[name]]["articles"],
            )
            for name in leiden
        }
    )
    core = [{"x": name, "y": float(row["pp_top10"])} for name, row in leiden.items()]
    return figures.chart(
        "bars",
        figures.Style(
            "Articles among the world's 10% most cited",
            f"{WINDOW}; OpenAlex counts every article and citing work, Leiden "
            "core articles, core citations and fractional authorship",
            LEIDEN,
            "%",
            1,
        ),
        figures.Axis("category"),
        [
            {
                "label": "OpenAlex, every article",
                "points": [{"x": k, "y": v} for k, v in every.items()],
            }
        ],
        compare={"label": "Leiden Ranking", "points": core},
    )


def followed_chart(
    record: Record, rows: Sequence[Mapping[str, str]]
) -> dict[str, object]:
    code = {record.short(c): c for c in {row["code"] for row in rows}}
    series = [
        {
            "label": name,
            "points": [
                {"x": row["year"], "y": int(row["articles"])}
                for row in rows
                if row["code"] == code[name]
            ],
        }
        for name in FOLLOWED
    ]
    return figures.chart(
        "line",
        figures.Style(
            "Journal articles a year",
            "The five universities with most articles; 2025 still filling",
            OPENALEX,
            "articles",
        ),
        figures.Axis("year"),
        series,
    )


@dataclass(frozen=True)
class Article:
    year: str
    universities: tuple[str, ...]
    sjr: str
    lists: frozenset[str]


class Grades:
    """Every 2021 to 2024 Peruvian article with the SJR quartile of its journal
    in the article's year and the national lists OpenAlex records for it."""

    def __init__(self, folder: Path) -> None:
        quartile = {
            (row["source"], row["year"]): row["quartile"]
            for row in read_csv(folder / "sjr.csv")
        }
        lists = {
            row["source"]: frozenset(row["lists"].split())
            for row in read_csv(folder / "sources.csv")
        }
        self.articles = [
            Article(
                row["year"],
                tuple(row["universities"].split()),
                # SJR prints "-" for a journal it lists without a quartile.
                quartile.get((row["source"], row["year"]), UNLISTED).replace(
                    "-", "no quartile"
                ),
                lists.get(row["source"], frozenset()),
            )
            for row in read_csv(folder / "articles.csv")
        ]

    def of(self, code: str) -> list[Article]:
        return [a for a in self.articles if code in a.universities]

    def largest(self, n: int) -> list[str]:
        counts = Counter(c for a in self.articles for c in a.universities)
        return [code for code, _ in counts.most_common(n)]


def top_quartiles(articles: Sequence[Article]) -> float:
    return share(sum(a.sjr in {"Q1", "Q2"} for a in articles), len(articles))


def unlisted(articles: Sequence[Article]) -> float:
    return share(sum(a.sjr == UNLISTED for a in articles), len(articles))


def grade_mix(articles: Sequence[Article]) -> dict[str, object]:
    sjr = Counter(a.sjr for a in articles)
    outside = [a for a in articles if a.sjr == UNLISTED]
    ungraded = [a for a in outside if not {"norway-1", "norway-2"} & a.lists]
    return {
        "articles": len(articles),
        "sjr_pct": {k: share(n, len(articles)) for k, n in sorted(sjr.items())},
        "neither_sjr_nor_norway_pct": share(len(ungraded), len(articles)),
        "not_in_sjr_in_scielo_pct": share(
            sum("scielo" in a.lists for a in outside), len(outside)
        ),
    }


def grades_summary(record: Record, grades: Grades) -> dict[str, object]:
    def in_group(key: str) -> list[Article]:
        return [
            a
            for a in grades.articles
            if any(group_of(record.universities[c]) == key for c in a.universities)
        ]

    return {
        "Peru": grade_mix(grades.articles),
        "groups": {name: grade_mix(in_group(key)) for key, name in GROUPS.items()},
        "universities": {
            record.short(c): grade_mix(grades.of(c)) for c in grades.largest(SHOWN)
        },
        "not_in_sjr_pct_by_year": {
            year: unlisted([a for a in grades.articles if a.year == year])
            for year in sorted({a.year for a in grades.articles})
        },
    }


def grade_chart(
    record: Record,
    grades: Grades,
    measure: Callable[[Sequence[Article]], float],
    style: figures.Style,
    series: str,
) -> dict[str, object]:
    values = {record.short(c): measure(grades.of(c)) for c in grades.largest(SHOWN)}
    return bars(style, descending(values), series)


def graded_years_chart(rows: Sequence[Mapping[str, str]]) -> dict[str, object]:
    columns = {"norway_1_or_2": "Level 1 or 2", "norway_2": "Level 2"}
    return figures.chart(
        "line",
        figures.Style(
            "Peruvian articles in graded journals",
            "Share of journal articles with a Peruvian author, by the journal's "
            "level in the Norwegian register as OpenAlex lists it today",
            f"{OPENALEX}; Norwegian Register for Scientific Journals",
            "%",
        ),
        figures.Axis("year"),
        [
            {
                "label": label,
                "points": [
                    {"x": row["year"], "y": share(int(row[key]), int(row["articles"]))}
                    for row in rows
                ],
            }
            for key, label in columns.items()
        ],
    )


def leaders(ranks: Sequence[Mapping[str, str]]) -> dict[str, list[str]]:
    """Each ranking's first place in Peru; a tie lists every university."""
    result: dict[str, list[str]] = {}
    for rank in ranks:
        if rank["peru_rank"] == "1":
            result.setdefault(rank["ranking"], []).append(rank["university"])
    return result


def summary(record: Record, groups: Sequence[Mapping[str, str]]) -> dict[str, object]:
    out, unis = record.output, record.universities
    core = sorted((row["core"] for row in out.values()), reverse=True)
    total = sum(core)
    by_group: Counter[str] = Counter()
    by_lima: Counter[bool] = Counter()
    for code, row in out.items():
        u = unis[code]
        by_group[group_of(u)] += row["core"]
        by_lima[u["department"] == "Lima"] += row["core"]
    year = {(row["group"], row["year"]): row for row in groups}
    return {
        "register": len(unis),
        "with_openalex": len(out),
        "without_openalex": dict(
            Counter(u["licence"] for u in unis.values() if not u["openalex"])
        ),
        "core_summed": total,
        "top10_universities_core_pct": share(sum(core[:10]), total),
        "under_10_core": sum(1 for c in core if c < 10),
        "core_pct_by_group": {g: share(n, total) for g, n in by_group.items()},
        "lima_core_pct": share(by_lima[True], total),
        "growth_2015_2024": {
            g: {
                m: [int(year[g, "2015"][m]), int(year[g, "2024"][m])]
                for m in ("articles", "core")
            }
            for g in (*GROUPS, "Peru")
        },
    }


def run(out: Path) -> dict[str, object]:
    record = Record(OUT)
    groups = read_csv(OUT / "groups.csv")
    journals = read_csv(OUT / "journals.csv")
    venues = read_csv(OUT / "venues.csv")
    leiden = {row.pop("university"): row for row in read_csv(OUT / "leiden.csv")}
    staff = per_staff(record, read_csv(OUT / "staff.csv"))
    citing = citing_shares(record, read_csv(OUT / "citing.csv"))
    grades = Grades(OUT)
    by_year = read_csv(OUT / "grades-by-year.csv")
    charts = {
        "top-quartiles": grade_chart(
            record,
            grades,
            top_quartiles,
            figures.Style(
                "Articles in top-quartile journals",
                f"Share in journals SJR ranks Q1 or Q2 in the article's year, "
                f"{WINDOW}; the {SHOWN} universities with most",
                SJR,
                "%",
            ),
            "Share in Q1 or Q2",
        ),
        "not-in-sjr": grade_chart(
            record,
            grades,
            unlisted,
            figures.Style(
                "Articles in journals SJR does not list",
                f"Share in journals outside SJR in the article's year, {WINDOW}; "
                f"the {SHOWN} universities with most",
                SJR,
                "%",
            ),
            "Share not in SJR",
        ),
        "graded-years": graded_years_chart(by_year),
        "concentration": concentration_chart(record),
        "growth": group_lines(groups, "core", "Articles a year in core journals"),
        "growth-all": group_lines(groups, "articles", "Journal articles a year"),
        "core-share": core_share_chart(record),
        "venues": venues_chart(record, venues),
        "journals": journals_chart(journals, read_csv(OUT / "journal-years.csv")),
        "per-staff": staff_chart(staff),
        "top10": top10_chart(record, leiden),
        "citing": citing_chart(citing),
        "articles": followed_chart(record, read_csv(OUT / "articles-by-year.csv")),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    result = summary(record, groups) | {
        "universities": {
            record.short(c): {
                "articles": record.output[c]["articles"],
                "core_pct": share(
                    record.output[c]["core"], record.output[c]["articles"]
                ),
            }
            for c in record.largest(SHOWN)
        },
        "venues_top5_pct": charts["venues"]["series"][0]["points"],  # type: ignore[index]
        "journals": journals,
        "core_per_staff": staff,
        "citing": citing,
        "leiden": {n: float(row["pp_top10"]) for n, row in leiden.items()},
        "grades": grades_summary(record, grades) | {"norway_by_year": by_year},
        "leaders": leaders(read_csv(OUT / "ranks.csv")),
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    (out / "numbers.json").write_text(text, encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Measure Peru's university research.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    run(args.out)
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
