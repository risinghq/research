"""The mining, gas and oil canon Peru's public universities receive: how much
they spend and what they spend it on, from MEF's open budget data, tested
against the figures the press has reported since 2013.

`--fetch` rebuilds `canon.csv`, `items.csv`, `projects.csv` and
`universities.csv` from MEF. It streams about 5 GB of zips and takes ten
minutes, so a plain run charts the committed tables.
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
SAN_ANTONIO_ABAD = "511"
DEL_SANTA = "536"
# Pliego 540 is the Asamblea Nacional de Rectores, which SUNEDU replaced in
# 2014; every other pliego from 510 to 583 is a public university.
NOT_A_UNIVERSITY = {"540"}
# The raw-line test MEF's two files share: sector 10, then a pliego from 500.
PREFIX = '"GOBIERNO NACIONAL","10","EDUCACION","5'
# The zip's FUENTE_FINANCIAMIENTO columns hold the rubro; the daily file names
# it in RUBRO.
SPAN_FUNDING = "FUENTE_FINANCIAMIENTO_NOMBRE"
DAILY_FUNDING = "RUBRO_NOMBRE"
# Rubro 18, "CANON Y SOBRECANON, REGALIAS, RENTA DE ADUANAS Y PARTICIPACIONES".
CANON_RUBRO = "CANON"
# Regional governments also passed canon to universities as transfers, booked
# under rubro 13 with a canon resource type. Those rows carry spending only:
# their budget sits on other resource types.
DONATIONS_RUBRO = "DONACIONES"
CANON = "canon"
REGIONAL = "regional transfer"
KEY = ("fund", "year", "pliego", "tipo", "item", "grupo")
MONEY = ("pia", "pim", "devengado")
PROJECT_KEY = ("year", "pliego", "project")
PROJECT = "PROYECTO"
CAPITAL = "2.6"
# MEF's functional groups for research.
RESEARCH = ("INVESTIGACION APLICADA", "INVESTIGACION BASICA")
SHOWN = 20
ITEMS_SHOWN = 10
PROJECTS_SHOWN = 10

# What the press reported, in soles and percent, with the year it covers.
# El Búho, 2014-01-02, from a Contraloría press note on 2013.
BUHO_2013 = {"available": 828_500_000, "pct": 14.1}
# ProActivo, 2015-11-19, crediting El Comercio, on 2014.
COMERCIO_2014 = {"received": 771_000_000, "spent": 216_200_000, "pct": 28.5}
COMERCIO_2014_UNIVERSITIES = {
    DEL_SANTA: {"received_over": 18_000_000, "spent": 14_000},
    SAN_ANTONIO_ABAD: {"received_over": 154_000_000},
    UNMSM: {"received_under": 100_000},
}
# Gestión, 2022-09-28, quoting the SNMPE on 2012-2021.
SNMPE_2012_2021 = {"received": 2_072_000_000, "pct": 39.0}

Budget = dict[tuple[str, ...], dict[str, float]]


def is_university(row: Mapping[str, str]) -> bool:
    code = row["PLIEGO"]
    return "510" <= code <= "599" and code not in NOT_A_UNIVERSITY


def keep(line: str) -> bool:
    return PREFIX in line


def fund(row: Mapping[str, str], funding: str) -> str | None:
    rubro = row[funding].strip()
    if rubro.startswith(CANON_RUBRO):
        return CANON
    if rubro.startswith(DONATIONS_RUBRO) and "CANON" in row["TIPO_RECURSO_NOMBRE"]:
        return REGIONAL
    return None


def item(row: Mapping[str, str]) -> str:
    """The spending item to the subgenérica detail: `2.6.2.2` is non-residential
    buildings."""
    return ".".join(
        row[c]
        for c in ("TIPO_TRANSACCION", "GENERICA", "SUBGENERICA", "SUBGENERICA_DET")
    )


class Tables:
    """What a fetch collects: the canon budget by key, its projects, and the
    names behind the codes."""

    def __init__(self) -> None:
        self.budget: Budget = {}
        self.projects: Budget = {}
        self.project_names: dict[tuple[str, str], str] = {}
        self.items: dict[str, str] = {}
        self.universities: dict[str, str] = {}

    def add(
        self, year: int, row: Mapping[str, str], stages: Mapping[str, float], kind: str
    ) -> None:
        at = (
            kind,
            str(year),
            row["PLIEGO"],
            row["TIPO_ACT_PROY_NOMBRE"].strip(),
            item(row),
            row["GRUPO_FUNCIONAL_NOMBRE"].strip(),
        )
        add(self.budget, at, stages)
        if kind == CANON and row["TIPO_ACT_PROY_NOMBRE"].strip() == PROJECT:
            code = row["PRODUCTO_PROYECTO"]
            add(self.projects, (str(year), row["PLIEGO"], code), stages)
            self.project_names[row["PLIEGO"], code] = row[
                "PRODUCTO_PROYECTO_NOMBRE"
            ].strip()

    def name(self, row: Mapping[str, str]) -> None:
        self.universities[row["PLIEGO"]] = row["PLIEGO_NOMBRE"].strip()
        self.items[item(row)] = row["SUBGENERICA_DET_NOMBRE"].strip()


def add(budget: Budget, at: tuple[str, ...], stages: Mapping[str, float]) -> None:
    sums = budget.setdefault(at, dict.fromkeys(MONEY, 0.0))
    for name in MONEY:
        sums[name] += stages[name.upper()]


def from_spans(rows: Iterable[dict[str, str]], tables: Tables) -> None:
    for row in rows:
        kind = fund(row, SPAN_FUNDING) if is_university(row) else None
        if kind is None:
            continue
        tables.name(row)
        for year, stages in mef.years(row):
            if year < DAILY[-1]:
                tables.add(year, row, stages, kind)


def from_daily(rows: Iterable[dict[str, str]], tables: Tables) -> None:
    for row in rows:
        kind = fund(row, DAILY_FUNDING) if is_university(row) else None
        if kind is None:
            continue
        tables.name(row)
        tables.add(int(row["ANO_EJE"]), row, mef.monthly(row), kind)


def fetch(client: mef.MefClient, out: Path) -> None:
    tables = Tables()
    for span in mef.SPANS:
        from_spans(client.rows(span, keep), tables)
    from_daily(client.daily(DAILY[-1], keep), tables)
    # The daily file holds no day, so its refresh date is the data's date.
    modified = parsedate_to_datetime(client.daily_modified(DAILY[-1]))
    source = {"daily_modified": modified.date().isoformat()}
    (out / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    write_csv(out / "canon.csv", [*KEY, *MONEY], money_rows(tables.budget))
    write_csv(
        out / "projects.csv",
        [*PROJECT_KEY, *MONEY],
        money_rows(tables.projects),
    )
    write_csv(
        out / "project_names.csv",
        ["pliego", "project", "name"],
        [[*k, n] for k, n in sorted(tables.project_names.items())],
    )
    write_csv(out / "items.csv", ["item", "name"], sorted(tables.items.items()))
    write_csv(
        out / "universities.csv",
        ["pliego", "mef_name", "name"],
        [[c, n, short_name(n)] for c, n in sorted(tables.universities.items())],
    )


def money_rows(budget: Budget) -> list[list[str]]:
    return [
        [*k, *(f"{v[m]:.2f}" for m in MONEY)]
        for k, v in sorted(budget.items())
        if any(v.values())
    ]


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


def sentence_case(name: str) -> str:
    return name[:1] + name[1:].lower()


class Table:
    """A money table summed over whichever of its keys a question needs."""

    def __init__(self, rows: Sequence[Mapping[str, str]], key: Sequence[str]) -> None:
        self.rows: list[tuple[dict[str, str], dict[str, float]]] = [
            ({k: r[k] for k in key}, {m: float(r[m]) for m in MONEY}) for r in rows
        ]

    def total(self, money: str, **match: str) -> float:
        return sum(
            sums[money]
            for keys, sums in self.rows
            if all(keys[k] == v for k, v in match.items())
        )

    def by(
        self, field: str, money: str, years: Sequence[str] | None = None, **match: str
    ) -> dict[str, float]:
        found: dict[str, float] = defaultdict(float)
        for keys, sums in self.rows:
            if years is not None and keys["year"] not in years:
                continue
            if all(keys[k] == v for k, v in match.items()):
                found[keys[field]] += sums[money]
        return dict(found)


def millions(soles: float) -> float | None:
    return figures.y_value(soles / 1e6)


def share(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def years(first: int, last: int) -> list[str]:
    return [str(y) for y in range(first, last + 1)]


def canon_chart(table: Table, last: int) -> dict[str, object]:
    def line(label: str, money: str) -> dict[str, object]:
        points: list[dict[str, object]] = []
        for year in years(FIRST, last):
            point: dict[str, object] = {
                "x": year,
                "y": millions(table.total(money, fund=CANON, year=year)),
            }
            if money == "devengado" and year == str(last):
                point["preliminary"] = True
            points.append(point)
        return {"label": label, "points": points}

    return figures.chart(
        "line",
        figures.Style(
            "Public universities' canon budget and spending",
            "Opening budget (PIA), budget after the year's changes (PIM) and "
            f"spending accrued (devengado) from canon and royalties, all public "
            f"universities, current soles; {last} to date",
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


def execution_pct(table: Table, year: str, **match: str) -> float:
    return share(
        table.total("devengado", fund=CANON, year=year, **match),
        table.total("pim", fund=CANON, year=year, **match),
    )


def execution_chart(table: Table, closed: int) -> dict[str, object]:
    return figures.chart(
        "columns",
        figures.Style(
            "How much of their canon universities spend",
            "Canon and royalty spending accrued as a share of the budget after "
            "the year's changes, all public universities",
            SOURCE,
            "%",
        ),
        figures.Axis("year"),
        [
            {
                "label": "Share spent",
                "points": [
                    {"x": y, "y": execution_pct(table, y)} for y in years(FIRST, closed)
                ],
            }
        ],
    )


def universities_chart(
    table: Table, names: Mapping[str, str], year: str
) -> dict[str, object]:
    pim = table.by("pliego", "pim", fund=CANON, year=year)
    spent = table.by("pliego", "devengado", fund=CANON, year=year)
    shown = sorted(pim, key=lambda c: -pim[c])[:SHOWN]
    shown.sort(key=lambda c: -share(spent.get(c, 0.0), pim[c]))
    return figures.chart(
        "bars",
        figures.Style(
            f"How much of their {year} canon universities spent",
            f"Canon and royalty spending accrued in {year} as a share of the "
            f"budget after the year's changes; the {SHOWN} universities with the "
            "largest canon budgets",
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


def ranked(found: Mapping[str, float], n: int) -> list[str]:
    return sorted(found, key=lambda k: -found[k])[:n]


def uses_chart(table: Table, span: Sequence[str]) -> dict[str, object]:
    spent = table.by("grupo", "devengado", span, fund=CANON)
    return figures.chart(
        "bars",
        figures.Style(
            "What universities spend their canon on",
            f"Canon and royalty spending accrued in {span[0]}-{span[-1]} by "
            "MEF's functional group, all public universities, current soles",
            SOURCE,
            UNIT,
        ),
        figures.Axis("category"),
        [
            {
                "label": "Spent",
                "points": [
                    {"x": sentence_case(g), "y": millions(spent[g])}
                    for g in ranked(spent, 8)
                ],
            }
        ],
    )


def items_chart(
    table: Table, items: Mapping[str, str], span: Sequence[str]
) -> dict[str, object]:
    spent = table.by("item", "devengado", span, fund=CANON)
    return figures.chart(
        "bars",
        figures.Style(
            "What universities buy with their canon",
            f"Canon and royalty spending accrued in {span[0]}-{span[-1]} by "
            "spending item, all public universities, current soles",
            SOURCE,
            UNIT,
        ),
        figures.Axis("category"),
        [
            {
                "label": "Spent",
                "points": [
                    {"x": sentence_case(items[i]), "y": millions(spent[i])}
                    for i in ranked(spent, ITEMS_SHOWN)
                ],
            }
        ],
    )


def against_press(table: Table) -> dict[str, object]:
    def year(y: str, **match: str) -> dict[str, float]:
        pim = table.total("pim", fund=CANON, year=y, **match)
        spent = table.total("devengado", fund=CANON, year=y, **match)
        return {"pim": round(pim), "devengado": round(spent), "pct": share(spent, pim)}

    span = years(2012, 2021)
    pim = sum(table.total("pim", fund=CANON, year=y) for y in span)
    spent = sum(table.total("devengado", fund=CANON, year=y) for y in span)
    return {
        "buho_2013": {"claimed": BUHO_2013, "mef": year("2013")},
        "comercio_2014": {"claimed": COMERCIO_2014, "mef": year("2014")},
        "comercio_2014_universities": {
            code: {"claimed": claim, "mef": year("2014", pliego=code)}
            for code, claim in COMERCIO_2014_UNIVERSITIES.items()
        },
        # SNMPE's transfers are not in a budget table; its 39% matches the sum of
        # ten years' spending over the sum of ten years' PIM, which counts every
        # balance carried over again in each year it is carried.
        "snmpe_2012_2021": {
            "claimed": SNMPE_2012_2021,
            "mef_summed": {
                "pim": round(pim),
                "devengado": round(spent),
                "pct": share(spent, pim),
            },
        },
    }


def top_projects(
    projects: Table,
    project_names: Mapping[tuple[str, str], str],
    names: Mapping[str, str],
    span: Sequence[str],
) -> list[dict[str, object]]:
    spent: dict[tuple[str, str], float] = defaultdict(float)
    for keys, sums in projects.rows:
        if keys["year"] in span:
            at = (keys["pliego"], keys["project"])
            spent[at] += sums["devengado"]
    return [
        {
            "university": names[p],
            "project": project_names[p, code],
            "devengado": round(spent[p, code]),
        }
        for p, code in sorted(spent, key=lambda k: -spent[k])[:PROJECTS_SHOWN]
    ]


def run(out: Path) -> dict[str, object]:
    table = Table(read_csv(OUT / "canon.csv"), KEY)
    projects = Table(read_csv(OUT / "projects.csv"), PROJECT_KEY)
    project_names = {
        (r["pliego"], r["project"]): r["name"]
        for r in read_csv(OUT / "project_names.csv")
    }
    items = {r["item"]: r["name"] for r in read_csv(OUT / "items.csv")}
    names = {r["pliego"]: r["name"] for r in read_csv(OUT / "universities.csv")}
    last = DAILY[-1]
    closed = last - 1
    span = years(FIRST, closed)
    charts = {
        "canon": canon_chart(table, last),
        "execution": execution_chart(table, closed),
        "universities": universities_chart(table, names, str(closed)),
        "uses": uses_chart(table, span),
        "items": items_chart(table, items, span),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    source = json.loads((OUT / "source.json").read_text())
    date_readme(out, date.fromisoformat(source["daily_modified"]))
    spent = sum(table.by("year", "devengado", span, fund=CANON).values())
    by_grupo = table.by("grupo", "devengado", span, fund=CANON)
    by_item = table.by("item", "devengado", span, fund=CANON)
    pim = table.by("pliego", "pim", fund=CANON, year=str(closed))
    done = table.by("pliego", "devengado", fund=CANON, year=str(closed))
    result = {
        "canon": {
            y: {m: round(table.total(m, fund=CANON, year=y)) for m in MONEY}
            for y in years(FIRST, last)
        },
        "execution_pct": {y: execution_pct(table, y) for y in span},
        "universities_with_canon": {
            y: len(
                [
                    c
                    for c, v in table.by("pliego", "pim", fund=CANON, year=y).items()
                    if v
                ]
            )
            for y in years(FIRST, last)
        },
        "against_press": against_press(table),
        "spent": {
            "span": f"{span[0]}-{span[-1]}",
            "total": round(spent),
            "capital_pct": share(
                sum(v for i, v in by_item.items() if i.startswith(CAPITAL)), spent
            ),
            "research_pct": share(sum(by_grupo.get(g, 0.0) for g in RESEARCH), spent),
            "by_grupo_pct": {
                g: share(by_grupo[g], spent)
                for g in ranked(by_grupo, len(by_grupo))
                if share(by_grupo[g], spent)
            },
            "by_item_pct": {
                items[i]: share(by_item[i], spent) for i in ranked(by_item, ITEMS_SHOWN)
            },
        },
        "regional_transfers_devengado": {
            y: round(table.total("devengado", fund=REGIONAL, year=y))
            for y in years(FIRST, last)
        },
        f"universities_{closed}": {
            names[c]: {
                "pim": round(pim[c]),
                "unspent": round(pim[c] - done.get(c, 0.0)),
                "pct": share(done.get(c, 0.0), pim[c]),
            }
            for c in ranked(pim, len(pim))
            if pim[c]
        },
        "top_projects": top_projects(projects, project_names, names, span),
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
    parser = argparse.ArgumentParser(description="Chart Peru's university canon.")
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
