"""The profits, returns on equity and arrears of Peru's microfinance firms,
from the SBS's monthly workbooks, testing Gestión's article of 2026-11-20 on
the cajas' profits to September.

`--raw DIR` rebuilds `entities.csv` from SBS workbooks saved in DIR under
their SBS names, any extension. The SBS answers scripts with a challenge
page, so docs/sbs.md gives the browser steps that fetch them; a plain run
charts the committed table.
"""

import argparse
import csv
import json
import sys

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import figures
import replication
import sbs


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

OUT = Path(__file__).parent
SOURCE = "SBS, Estadísticas del Sistema Financiero"
FIRST = 2010
LAST = 2026
# September: the month Gestión's article reports.
MONTH = 9
FIELDS = ("net_profit", "roe", "arrears")
TOTAL = "Total"
# The SBS approved Financiera Oh!'s new name in Resolución SBS 00332-2026 of
# 2026-02-03, so its 2025 rows and InFinance XP's 2026 rows are one firm.
RENAMES = {"Financiera Oh!": "InFinance XP"}
# The day the SBS's September 2026 workbooks were read.
READ = date(2026, 11, 21)
# Gestión's figures, 2026-11-20, in millions of soles, percent and firms.
GESTION: dict[str, object] = {
    "cajas_municipales": {"profit": 1124.5, "growth_pct": 93.1, "firms_up": 11},
    "cajas_rurales": {"profit": 17.7, "firms_up": 4},
    "financieras": {"profit": 158.5, "growth_pct": -16, "firms_up": 5},
    "empresas_de_credito": {"profit": 91, "growth_pct": 52, "firms_up": 4},
    "firms_up": 24,
    "firms": 26,
    "roe_pct": {
        "Financiera Qapaq": 36.8,
        "Mitsui Auto Finance": 18.8,
        "Financiera Proempresa": 18.1,
        "Santander Consumo": 26.7,
        "Vívela": 13.5,
        "TOTAL Servicios Financieros": 13.3,
    },
}
# The five cajas municipales the article calls the most profitable, in its
# order, without a figure or a measure.
GESTION_TOP_CAJAS = (
    "CMCP Lima",
    "CMAC Piura",
    "CMAC Huancayo",
    "CMAC Cusco",
    "CMAC Arequipa",
)

Rows = list[dict[str, str]]


def workbook(raw: Path, code: str, year: int) -> list[tuple[str, sbs.Grid]]:
    stem = sbs.file_name(code, year, MONTH).rsplit(".", 1)[0].lower()
    path = next(p for p in raw.iterdir() if p.stem.lower() == stem)
    return list(sbs.grids(path))


def firms(values: Mapping[str, float]) -> dict[str, float]:
    """A sheet's firms under their current names, and the system's total as
    `TOTAL`. A sheet's last aggregate column sums the whole system; the ones
    before it sum part of it, such as the cajas municipales without Lima."""
    aggregates = [n for n in values if sbs.is_aggregate(n)]
    found = {RENAMES.get(n, n): v for n, v in values.items() if n not in aggregates}
    found[TOTAL] = values[aggregates[-1]]
    return found


def read_raw(raw: Path) -> Rows:
    rows: Rows = []
    for key, system in sbs.SYSTEMS.items():
        for year in range(FIRST, LAST + 1):
            statements = workbook(raw, system.statements, year)
            indicators = workbook(raw, system.indicators, year)
            columns = {
                "net_profit": firms(sbs.net_profit(statements)),
                "roe": firms(sbs.indicator(indicators, sbs.ROE)),
                "arrears": firms(sbs.indicator(indicators, sbs.ARREARS)),
            }
            names = sorted({n for c in columns.values() for n in c})
            for name in names:
                values = [columns[f].get(name) for f in FIELDS]
                # A firm that stopped reporting keeps a column of zeros:
                # CRAC del Centro in 2026, Solidaridad's indicators from 2017.
                if not any(values):
                    continue
                rows.append(
                    {
                        "system": key,
                        "year": str(year),
                        "name": name,
                        **{
                            f: "" if v is None else f"{v:.2f}"
                            for f, v in zip(FIELDS, values, strict=True)
                        },
                    }
                )
    return rows


def write_csv(path: Path, rows: Rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, ["system", "year", "name", *FIELDS], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> Rows:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


class Table:
    """entities.csv by system, year and firm."""

    def __init__(self, rows: Iterable[Mapping[str, str]]) -> None:
        self.cells: dict[tuple[str, int, str], dict[str, float | None]] = {
            (r["system"], int(r["year"]), r["name"]): {
                f: float(r[f]) if r[f] else None for f in FIELDS
            }
            for r in rows
        }

    def value(self, system: str, year: int, name: str, field: str) -> float | None:
        return self.cells.get((system, year, name), {}).get(field)

    def firms(self, system: str, year: int, field: str) -> dict[str, float]:
        return {
            n: v
            for (s, y, n), c in self.cells.items()
            if s == system and y == year and n != TOTAL and (v := c[field]) is not None
        }


def millions(thousands: float | None) -> float | None:
    return None if thousands is None else figures.y_value(thousands / 1000)


def growth(now: float, before: float) -> float:
    return round(100 * (now / before - 1), 1)


def compared(table: Table) -> dict[str, dict[str, object]]:
    """Each firm reporting a profit in September of both years: its profit,
    return on equity and arrears then and now."""
    result: dict[str, dict[str, object]] = {}
    for key in sbs.SYSTEMS:
        now = table.firms(key, LAST, "net_profit")
        before = table.firms(key, LAST - 1, "net_profit")
        for name in sorted(now):
            if name not in before:
                continue
            result[name] = {
                "system": key,
                **{
                    f"{field}_{year}": table.value(key, year, name, field)
                    for field in FIELDS
                    for year in (LAST - 1, LAST)
                },
            }
    return result


def changed(table: Table, firms: Mapping[str, object], year: int) -> list[str]:
    return sorted(
        n
        for key in sbs.SYSTEMS
        for n in table.firms(key, year, "net_profit")
        if n not in firms
    )


def rising(firms: Mapping[str, Mapping[str, object]], field: str) -> list[str]:
    def up(f: Mapping[str, object]) -> bool:
        now, before = f[f"{field}_{LAST}"], f[f"{field}_{LAST - 1}"]
        return isinstance(now, float) and isinstance(before, float) and now > before

    return sorted(n for n, f in firms.items() if up(f))


def profits_chart(table: Table) -> dict[str, object]:
    return figures.chart(
        "line",
        figures.Style(
            "Microfinance profits, January to September",
            "Net profit from January to September of each year, by system, "
            "current soles",
            SOURCE,
            "million soles",
            1,
        ),
        figures.Axis("year"),
        [
            {
                "label": system.name,
                "points": [
                    {
                        "x": str(y),
                        "y": millions(table.value(key, y, TOTAL, "net_profit")),
                    }
                    for y in range(FIRST, LAST + 1)
                ],
            }
            for key, system in sbs.SYSTEMS.items()
        ],
    )


def firms_chart(
    firms: Mapping[str, Mapping[str, object]], field: str, style: figures.Style
) -> dict[str, object]:
    """Each firm's September value in `LAST`, largest first, with `LAST - 1`'s
    value as the compared tick."""
    now = {n: f[f"{field}_{LAST}"] for n, f in firms.items()}
    shown = sorted(
        (n for n, v in now.items() if isinstance(v, float)),
        key=lambda n: -float(now[n]),  # type: ignore[arg-type]
    )
    return figures.chart(
        "bars",
        style,
        figures.Axis("category"),
        [
            {
                "label": f"September {LAST}",
                "points": [{"x": n, "y": now[n]} for n in shown],
            }
        ],
        compare={
            "label": f"September {LAST - 1}",
            "points": [{"x": n, "y": firms[n][f"{field}_{LAST - 1}"]} for n in shown],
        },
    )


def run(out: Path) -> dict[str, object]:
    table = Table(read_csv(OUT / "entities.csv"))
    firms = compared(table)
    charts = {
        "profits": profits_chart(table),
        "roe": firms_chart(
            firms,
            "roe",
            figures.Style(
                "Return on equity by firm",
                f"Net profit over average equity, annualised, September {LAST}; "
                f"the tick marks September {LAST - 1}",
                SOURCE,
                "%",
                1,
            ),
        ),
        "arrears": firms_chart(
            firms,
            "arrears",
            figures.Style(
                "Loans in arrears by firm",
                f"Loans past due or in court collection over direct loans, "
                f"September {LAST}; the tick marks September {LAST - 1}",
                SOURCE,
                "%",
                1,
            ),
        ),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    date_readme(out, date(LAST, MONTH, 30))
    systems = {}
    for key in sbs.SYSTEMS:
        now = table.value(key, LAST, TOTAL, "net_profit")
        before = table.value(key, LAST - 1, TOTAL, "net_profit")
        members = {n: f for n, f in firms.items() if f["system"] == key}
        systems[key] = {
            "profit_millions": {
                str(LAST - 1): millions(before),
                str(LAST): millions(now),
            },
            "growth_pct": growth(now, before) if now and before else None,
            "roe_pct": {
                str(y): table.value(key, y, TOTAL, "roe") for y in (LAST - 1, LAST)
            },
            "arrears_pct": {
                str(y): table.value(key, y, TOTAL, "arrears") for y in (LAST - 1, LAST)
            },
            "firms": len(members),
            "profit_up": rising(members, "net_profit"),
            "roe_up": rising(members, "roe"),
            "arrears_up": rising(members, "arrears"),
        }
    cajas = table.firms("cajas_municipales", LAST, "roe")
    result = {
        "month": f"{LAST}-{MONTH:02d}",
        "read": READ.isoformat(),
        "gestion": GESTION,
        "systems": systems,
        "firms": len(firms),
        "firms_profit_up": len(rising(firms, "net_profit")),
        # Firms with a profit in one of the two years only.
        "gone": changed(table, firms, LAST - 1),
        "new": changed(table, firms, LAST),
        "cajas_by_roe": sorted(cajas, key=lambda n: -cajas[n])[
            : len(GESTION_TOP_CAJAS)
        ],
        "gestion_top_cajas": list(GESTION_TOP_CAJAS),
        "by_firm": firms,
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
    parser = argparse.ArgumentParser(description="Chart Peru's microfinance profits.")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--raw", type=Path, help="rebuild entities.csv from SBS workbooks in RAW"
    )
    args = parser.parse_args(argv)
    if args.raw:
        write_csv(OUT / "entities.csv", read_raw(args.raw))
    run(args.out)
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
