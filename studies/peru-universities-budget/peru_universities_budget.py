"""The budgets of Peru's public universities and how much of them they spend,
from MEF's open budget data, opening with San Marcos' report of its 2026 cut.

`--fetch` rebuilds `budget.csv`, `monthly.csv` and `universities.csv` from MEF.
It streams about 5 GB of zips and takes ten minutes, so a plain run charts
the committed tables.
"""

import argparse
import csv
import json
import sys

from collections import defaultdict
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import TYPE_CHECKING

import figures
import mef
import replication


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

OUT = Path(__file__).parent
SOURCE = "MEF, Datos Abiertos: Comparación de Presupuesto y Ejecución de Gasto"
UNIT = "million soles"
FIRST = 2012
# Years the daily file holds; the zip's 2026 columns repeat 2025.
DAILY = (2025, 2026)
UNMSM = "510"
# Pliego 540 is the Asamblea Nacional de Rectores, which SUNEDU replaced in
# 2014; every other pliego from 510 to 583 is a public university.
NOT_A_UNIVERSITY = {"540"}
# The raw-line test MEF's two files share: sector 10, then a pliego from 500.
PREFIX = '"GOBIERNO NACIONAL","10","EDUCACION","5'
KEY = ("year", "pliego", "rubro", "generica", "tipo")
# The funding a row names. The zip's FUENTE_FINANCIAMIENTO columns hold the
# rubro, the finer split (code 18, canon and royalties), while the daily file
# names the fuente (5, recursos determinados) and the rubro apart. The rubro
# is the one both carry.
SPAN_FUNDING = "FUENTE_FINANCIAMIENTO_NOMBRE"
DAILY_FUNDING = "RUBRO_NOMBRE"
MONEY = ("pia", "pim", "certificado", "devengado")
CAPITAL = "2.6"
GOODS = "2.3"
ORDINARY = "RECURSOS ORDINARIOS"
SHOWN = 20
# The cut San Marcos' communiqué gave for 2026 against 2025, as Infobae
# reported it on 2025-12-11, in soles.
COMMUNIQUE = {"total": 17_296_489, GOODS: 13_484_620, CAPITAL: 3_811_869}
# The cut in ordinary resources for all public universities the rectors gave.
RECTORS_ORDINARY_CUT = 288_000_000

Budget = dict[tuple[str, ...], dict[str, float]]


def is_university(row: Mapping[str, str]) -> bool:
    code = row["PLIEGO"]
    return "510" <= code <= "599" and code not in NOT_A_UNIVERSITY


def keep(line: str) -> bool:
    return PREFIX in line


def key(year: int, row: Mapping[str, str], funding: str) -> tuple[str, ...]:
    return (
        str(year),
        row["PLIEGO"],
        row[funding].strip(),
        f"{row['TIPO_TRANSACCION']}.{row['GENERICA']}",
        row["TIPO_ACT_PROY_NOMBRE"].strip(),
    )


def add(budget: Budget, at: tuple[str, ...], stages: Mapping[str, float]) -> None:
    sums = budget.setdefault(at, dict.fromkeys(MONEY, 0.0))
    for name in MONEY:
        sums[name] += stages[name.upper()]


def from_spans(rows: Iterable[dict[str, str]], budget: Budget) -> dict[str, str]:
    """Add the zip rows' closed years to `budget`; return each pliego's name."""
    names: dict[str, str] = {}
    for row in rows:
        if not is_university(row):
            continue
        names[row["PLIEGO"]] = row["PLIEGO_NOMBRE"].strip()
        for year, stages in mef.years(row):
            if year < DAILY[-1]:
                add(budget, key(year, row, SPAN_FUNDING), stages)
    return names


def from_daily(
    rows: Iterable[dict[str, str]],
    budget: Budget,
    monthly: dict[tuple[str, str, str], float],
    *,
    annual: bool,
) -> dict[str, str]:
    """Add a daily file's months to `monthly`, and its year to `budget` when
    `annual`; return each pliego's name."""
    names: dict[str, str] = {}
    for row in rows:
        if not is_university(row):
            continue
        names[row["PLIEGO"]] = row["PLIEGO_NOMBRE"].strip()
        stages = mef.monthly(row)
        at = (row["ANO_EJE"], f"{int(row['MES_EJE']):02d}", row["PLIEGO"])
        monthly[at] = monthly.get(at, 0.0) + stages["DEVENGADO"]
        if annual:
            add(budget, key(int(row["ANO_EJE"]), row, DAILY_FUNDING), stages)
    return names


def fetch(client: mef.MefClient, out: Path) -> None:
    budget: Budget = {}
    monthly: dict[tuple[str, str, str], float] = {}
    names: dict[str, str] = {}
    for span in mef.SPANS:
        names |= from_spans(client.rows(span, keep), budget)
    for year in DAILY:
        rows = client.daily(year, keep)
        names |= from_daily(rows, budget, monthly, annual=year == DAILY[-1])
    # The daily file holds no day, so its refresh date is the data's date.
    modified = parsedate_to_datetime(client.daily_modified(DAILY[-1]))
    source = {"daily_modified": modified.date().isoformat()}
    (out / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    write_csv(
        out / "budget.csv",
        [*KEY, *MONEY],
        [[*k, *(f"{v[m]:.2f}" for m in MONEY)] for k, v in sorted(budget.items())],
    )
    write_csv(
        out / "monthly.csv",
        ["year", "month", "pliego", "devengado"],
        [[*k, f"{v:.2f}"] for k, v in sorted(monthly.items())],
    )
    write_csv(
        out / "universities.csv",
        ["pliego", "mef_name", "name"],
        [[c, n, short_name(n)] for c, n in sorted(names.items())],
    )


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


SMALL_WORDS = {"de", "del", "la", "y", "el", "los", "las"}


def short_name(mef_name: str) -> str:
    """MEF's upper-case pliego name as a label: `U.N. MAYOR DE SAN MARCOS` reads
    `UN Mayor de San Marcos`."""
    words = mef_name.replace("U. N.", "U.N.").split()
    rest = words[1:] if words[0] == "U.N." else words
    shown = [w.lower() if w.lower() in SMALL_WORDS else w.capitalize() for w in rest]
    return " ".join(["UN", *shown] if words[0] == "U.N." else shown)


class Table:
    """budget.csv summed over whichever of its keys a question needs."""

    def __init__(self, rows: Sequence[Mapping[str, str]]) -> None:
        self.rows = [
            {**{k: r[k] for k in KEY}, **{m: float(r[m]) for m in MONEY}} for r in rows
        ]

    def total(self, money: str, **match: str) -> float:
        return sum(
            r[money]  # type: ignore[misc]
            for r in self.rows
            if all(r[k] == v for k, v in match.items())
        )

    def by(self, field: str, money: str, **match: str) -> dict[str, float]:
        sums: dict[str, float] = defaultdict(float)
        for r in self.rows:
            if all(r[k] == v for k, v in match.items()):
                sums[str(r[field])] += r[money]  # type: ignore[operator]
        return dict(sums)


def millions(soles: float) -> float | None:
    return figures.y_value(soles / 1e6)


def share(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def years(last: int) -> list[str]:
    return [str(y) for y in range(FIRST, last + 1)]


def unmsm_chart(table: Table, last: int, month: str) -> dict[str, object]:
    def line(label: str, money: str) -> dict[str, object]:
        points: list[dict[str, object]] = []
        for year in years(last):
            point: dict[str, object] = {
                "x": year,
                "y": millions(table.total(money, year=year, pliego=UNMSM)),
            }
            if money == "devengado" and year == str(last):
                point["preliminary"] = True
            points.append(point)
        return {"label": label, "points": points}

    return figures.chart(
        "line",
        figures.Style(
            "San Marcos' budget and spending",
            f"Opening budget (PIA), budget after the year's changes (PIM) and "
            f"spending accrued (devengado), current soles; {last} to {month}",
            SOURCE,
            UNIT,
        ),
        figures.Axis("year"),
        [
            line("Opening budget", "pia"),
            line("Budget after changes", "pim"),
            line("Spent", "devengado"),
        ],
    )


def largest(table: Table, year: str, n: int, **match: str) -> list[str]:
    pim = table.by("pliego", "pim", year=year, **match)
    return sorted(pim, key=lambda c: -pim[c])[:n]


def execution_chart(
    table: Table, names: Mapping[str, str], year: str, title: str, **match: str
) -> dict[str, object]:
    pim = table.by("pliego", "pim", year=year, **match)
    spent = table.by("pliego", "devengado", year=year, **match)
    shown = largest(table, year, SHOWN, **match)
    shown.sort(key=lambda c: -share(spent.get(c, 0.0), pim[c]))
    what = "investment budget" if match else "budget"
    return figures.chart(
        "bars",
        figures.Style(
            title,
            f"Spending accrued in {year} as a share of the {what} after the "
            f"year's changes; the {SHOWN} public universities with the largest",
            SOURCE,
            "%",
        ),
        figures.Axis("category"),
        [
            {
                "label": "Share spent",
                "points": [
                    {"x": names[c], "y": share(spent.get(c, 0.0), pim[c])}
                    for c in shown
                ],
            }
        ],
    )


def funding_chart(table: Table, last: int) -> dict[str, object]:
    found = table.by("rubro", "pim", pliego=UNMSM)
    rubros = sorted(found, key=lambda r: -found[r])
    return figures.chart(
        "line",
        figures.Style(
            "Where San Marcos' budget comes from",
            "Budget after the year's changes (PIM) by funding source, current soles",
            SOURCE,
            UNIT,
        ),
        figures.Axis("year"),
        [
            {
                "label": rubro.capitalize(),
                "points": [
                    {
                        "x": y,
                        "y": millions(
                            table.total("pim", year=y, pliego=UNMSM, rubro=rubro)
                        ),
                    }
                    for y in years(last)
                ],
            }
            for rubro in rubros
        ],
    )


def ordinary_chart(table: Table, last: int) -> dict[str, object]:
    return figures.chart(
        "columns",
        figures.Style(
            "Public universities' opening budget from ordinary resources",
            "Opening budget (PIA) funded by the Treasury, all public "
            "universities, current soles",
            SOURCE,
            UNIT,
        ),
        figures.Axis("year"),
        [
            {
                "label": "Ordinary resources",
                "points": [
                    {"x": y, "y": millions(table.total("pia", year=y, rubro=ORDINARY))}
                    for y in years(last)
                ],
            }
        ],
    )


def cumulative(
    monthly: Sequence[Mapping[str, str]], year: str, pliego: str
) -> list[float]:
    by_month = {
        r["month"]: float(r["devengado"])
        for r in monthly
        if r["year"] == year and r["pliego"] == pliego
    }
    sums: list[float] = []
    running = 0.0
    for month in range(1, 13):
        running += by_month.get(f"{month:02d}", 0.0)
        sums.append(running)
    return sums


MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def pace_chart(
    table: Table, monthly: Sequence[Mapping[str, str]], last_month: int
) -> dict[str, object]:
    series = []
    for year in (str(y) for y in DAILY):
        pim = table.total("pim", year=year, pliego=UNMSM)
        open_year = year == str(DAILY[-1])
        months = last_month if open_year else 12
        sums = cumulative(monthly, year, UNMSM)
        points: list[dict[str, object]] = []
        for m in range(12):
            point: dict[str, object] = {
                "x": MONTHS[m],
                "y": share(sums[m], pim) if m < months else None,
            }
            if open_year and m == months - 1:
                point["preliminary"] = True
            points.append(point)
        series.append({"label": year, "points": points})
    return figures.chart(
        "line",
        figures.Style(
            "How fast San Marcos spends its budget",
            "Spending accrued since January as a share of the year's budget "
            "after changes (PIM)",
            SOURCE,
            "%",
        ),
        figures.Axis("category"),
        series,
    )


def last_month(monthly: Sequence[Mapping[str, str]]) -> int:
    """The open year's latest month with spending. The daily file adds each
    day as it comes, so this month is still partial."""
    year = str(DAILY[-1])
    return max(
        int(r["month"]) for r in monthly if r["year"] == year and float(r["devengado"])
    )


def against_communique(table: Table, last: int) -> dict[str, object]:
    def cut(**match: str) -> float:
        before = table.total("pia", year=str(last - 1), pliego=UNMSM, **match)
        now = table.total("pia", year=str(last), pliego=UNMSM, **match)
        return round(before - now)

    return {
        "total": {"communique": COMMUNIQUE["total"], "mef_pia": cut()},
        "goods_and_services": {
            "communique": COMMUNIQUE[GOODS],
            "mef_pia": cut(generica=GOODS),
        },
        "capital": {
            "communique": COMMUNIQUE[CAPITAL],
            "mef_pia": cut(generica=CAPITAL),
        },
    }


def run(out: Path) -> dict[str, object]:
    table = Table(read_csv(OUT / "budget.csv"))
    monthly = read_csv(OUT / "monthly.csv")
    names = {r["pliego"]: r["name"] for r in read_csv(OUT / "universities.csv")}
    last = DAILY[-1]
    closed = str(last - 1)
    month = last_month(monthly)
    through = f"{MONTHS[month - 1]} {last}"
    charts = {
        "unmsm": unmsm_chart(table, last, through),
        "execution": execution_chart(
            table,
            names,
            closed,
            f"How much of their {closed} budget universities spent",
        ),
        "investment": execution_chart(
            table,
            names,
            closed,
            f"How much of their {closed} investment budget universities spent",
            generica=CAPITAL,
        ),
        "funding": funding_chart(table, last),
        "ordinary": ordinary_chart(table, last),
        "pace": pace_chart(table, monthly, month),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    source = json.loads((OUT / "source.json").read_text())
    date_readme(out, date.fromisoformat(source["daily_modified"]))
    pim = table.by("pliego", "pim", year=closed)
    spent = table.by("pliego", "devengado", year=closed)
    cap_pim = table.by("pliego", "pim", year=closed, generica=CAPITAL)
    cap_spent = table.by("pliego", "devengado", year=closed, generica=CAPITAL)
    ordinary = {
        y: round(table.total("pia", year=y, rubro=ORDINARY)) for y in years(last)
    }
    result = {
        "latest_month": f"{last}-{month:02d}",
        "universities": len([c for c in pim if pim[c]]),
        "unmsm": {
            y: {m: round(table.total(m, year=y, pliego=UNMSM)) for m in MONEY}
            for y in years(last)
        },
        "unmsm_against_communique": against_communique(table, last),
        "ordinary_pia_all": ordinary,
        "ordinary_pia_cut_vs_rectors": {
            "rectors": RECTORS_ORDINARY_CUT,
            "mef_pia": ordinary[str(last - 1)] - ordinary[str(last)],
        },
        "all_execution_pct": {
            y: share(table.total("devengado", year=y), table.total("pim", year=y))
            for y in years(last - 1)
        },
        "all_capital_execution_pct": {
            y: share(
                table.total("devengado", year=y, generica=CAPITAL),
                table.total("pim", year=y, generica=CAPITAL),
            )
            for y in years(last - 1)
        },
        "execution_pct": {
            names[c]: share(spent.get(c, 0.0), pim[c])
            for c in sorted(pim, key=lambda c: -pim[c])
            if pim[c]
        },
        "capital_execution_pct": {
            names[c]: {
                "pim": round(cap_pim[c]),
                "pct": share(cap_spent.get(c, 0.0), cap_pim[c]),
            }
            for c in sorted(cap_pim, key=lambda c: -cap_pim[c])
            if cap_pim[c]
        },
        # The daily file and the zip both hold 2025; their spending must agree.
        "daily_against_zip_devengado": {
            "daily": round(
                sum(float(r["devengado"]) for r in monthly if r["year"] == closed)
            ),
            "zip": round(table.total("devengado", year=closed)),
        },
        "unmsm_pace_through": MONTHS[month - 2],
        "unmsm_pace_pct": {
            str(y): share(
                cumulative(monthly, str(y), UNMSM)[month - 2],
                table.total("pim", year=str(y), pliego=UNMSM),
            )
            for y in DAILY
        },
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    (out / "numbers.json").write_text(text, encoding="utf-8")
    return result


def date_readme(out: Path, day: date) -> None:
    readme = out / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        readme.write_text(replication.set_data_date(text, day), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chart Peru's university budgets.")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--fetch", action="store_true", help="rebuild the tables from MEF"
    )
    args = parser.parse_args(argv)
    if args.fetch:
        client = mef.MefClient()
        try:
            fetch(client, OUT)
        finally:
            client.close()
    run(args.out)
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
