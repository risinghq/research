"""Reader for the monthly workbooks of Peru's Superintendencia de Banca, Seguros
y AFP (SBS): each financial firm's statements and indicators, one column per
entity.

The SBS publishes one workbook per system, report and month at
`intranet2.sbs.gob.pe/estadistica/financiera/`, from 2000 on. The site sits
behind Incapsula, which answers a script with a challenge page, so the files
come through a real browser: open any page of `intranet2.sbs.gob.pe` and fetch
`file_path(...)` from it. docs/sbs.md gives the steps.

Every file is named `.XLS`, but some are Excel 2007 workbooks, so `grid` reads
a file by its first bytes. Within a report the sheet layout holds across
years; only the labels and the column of labels move:

- The income statement gives each entity three columns, MN (soles), ME
  (foreign currency) and TOTAL, under the entity's name, in thousands of
  soles. Net profit is "UTILIDAD (PÉRDIDA) NETA" to 2012 and "RESULTADO NETO
  DEL EJERCICIO" from 2013, when the SBS adopted its new accounting manual.
- The indicators sheet gives each entity one column, in percent. Wide systems
  split the table in two halves side by side, each with its own label column.
- Figures are year to date: September's net profit is January to September.
"""

import re
import unicodedata

from dataclasses import dataclass
from typing import TYPE_CHECKING

import openpyxl
import xlrd


if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path
    from typing import BinaryIO

HOST = "https://intranet2.sbs.gob.pe"
_ZIP = b"PK\x03\x04"
MONTHS = (
    ("Enero", "en"),
    ("Febrero", "fe"),
    ("Marzo", "ma"),
    ("Abril", "ab"),
    ("Mayo", "my"),
    ("Junio", "jn"),
    ("Julio", "jl"),
    ("Agosto", "ag"),
    ("Setiembre", "se"),
    ("Octubre", "oc"),
    ("Noviembre", "no"),
    ("Diciembre", "di"),
)
NET_PROFIT = ("UTILIDAD (PERDIDA) NETA", "RESULTADO NETO DEL EJERCICIO")
# Net profit over average equity, annualised. The cajas' sheets say "Utilidad
# Neta Anualizada sobre Patrimonio Promedio", the financieras' "Utilidad
# Anualizada / Patrimonio Promedio".
ROE = ("UTILIDAD NETA ANUALIZADA SOBRE PATRIMONIO PROMEDIO", "UTILIDAD ANUALIZADA /")
# Arrears over direct loans, the SBS's "morosidad". A sheet also lists the
# soles and dollar ratios on their own, as "Créditos Atrasados MN ...". Sheets
# say "(criterio SBS)" from 2015, and "Cartera Atrasada" to 2012.
ARREARS = (
    "CREDITOS ATRASADOS (CRITERIO SBS)",
    "CREDITOS ATRASADOS / CREDITOS DIRECTOS",
    "CARTERA ATRASADA / CREDITOS DIRECTOS",
)

# The income statements name some firms otherwise than the indicators sheets
# of the same month, 2010 to 2026.
SPELLINGS = {
    "Caja Municipal de Crédito Popular Lima": "CMCP Lima",
    "CRAC Censosud Scotia": "CRAC Cencosud Scotia",
    "CRAC Libertadores de Ayacucho": "CRAC Libertadores Ayacucho",
}

Cell = str | float | None
Grid = list[list[Cell]]


@dataclass(frozen=True)
class System:
    """A group of firms the SBS reports together. `statements` is the code of
    the balance sheet and income statement workbook, `indicators` the code of
    the financial indicators one."""

    name: str
    statements: str
    indicators: str


SYSTEMS = {
    "cajas_municipales": System("Cajas municipales", "C-1101", "C-1301"),
    "cajas_rurales": System("Cajas rurales", "C-2101", "C-2301"),
    "financieras": System("Empresas financieras", "B-3101", "B-3301"),
    "empresas_de_credito": System("Empresas de crédito", "C-4103", "C-4301"),
}


def file_path(code: str, year: int, month: int) -> str:
    """The path of a report's workbook on `HOST`, such as
    `/estadistica/financiera/2026/Setiembre/C-1101-se2026.XLS`."""
    folder, short = MONTHS[month - 1]
    return f"/estadistica/financiera/{year}/{folder}/{code}-{short}{year}.XLS"


def file_name(code: str, year: int, month: int) -> str:
    return file_path(code, year, month).rsplit("/", 1)[1]


def grids(path: Path) -> Iterator[tuple[str, Grid]]:
    """Each sheet of a workbook as its name and rows. An Excel 2007 file starts
    as a zip does; the older format is an OLE file. openpyxl refuses a path
    that ends in `.xls`, so it gets an open file."""
    with path.open("rb") as file:
        if file.read(4) == _ZIP:
            file.seek(0)
            yield from _xlsx(file)
            return
    yield from _xls(path)


def _xlsx(file: BinaryIO) -> Iterator[tuple[str, Grid]]:
    book = openpyxl.load_workbook(file, read_only=True, data_only=True)
    try:
        for sheet in book.worksheets:
            rows = sheet.iter_rows(values_only=True)
            yield sheet.title, [[_cell(c) for c in row] for row in rows]
    finally:
        book.close()


def _xls(path: Path) -> Iterator[tuple[str, Grid]]:
    book = xlrd.open_workbook(str(path), on_demand=True)
    try:
        for sheet in book.sheets():
            rows = (sheet.row_values(r) for r in range(sheet.nrows))
            yield sheet.name, [[_cell(c) for c in row] for row in rows]
    finally:
        book.release_resources()


def _cell(value: object) -> Cell:
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        return float(value)
    return str(value)


def label(value: Cell) -> str:
    """A label as upper case ASCII with single spaces, so "UTILIDAD ( PÉRDIDA )
    NETA" and "Utilidad (Pérdida) Neta" read the same."""
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text).strip().upper()
    return re.sub(r"\(\s*", "(", re.sub(r"\s*\)", ")", text))


def entity(value: str) -> str:
    """An entity's name with its line breaks, footnote marks and doubled spaces
    removed, in the spelling the indicators sheet uses: "CMAC Piura 1/",
    "CMAC Piura***" and "CMAC\\n Piura" all read "CMAC Piura"."""
    text = re.sub(r"(\s*\d+/|\*+)+$", "", value.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return SPELLINGS.get(text, text)


def is_aggregate(name: str) -> bool:
    """Whether a column sums a system or part of one, such as "TOTAL CMAC".
    "TOTAL Servicios Financieros" is a firm, so the test is on the words
    after "TOTAL"."""
    words = label(name).split()
    return bool(words) and words[0] == "TOTAL" and words[1:2] != ["SERVICIOS"]


def _matches(value: Cell, prefixes: Sequence[str]) -> bool:
    text = label(value)
    return any(text.startswith(p) for p in prefixes)


def net_profit(sheets: Sequence[tuple[str, Grid]]) -> dict[str, float]:
    """Each entity's year-to-date net profit, in thousands of soles, from a
    statements workbook. The income statement is the sheet whose rows carry a
    net profit label; the balance sheet's equity line is in mixed case."""
    for _, grid in sheets:
        found = _income(grid)
        if found:
            return found
    raise ValueError("no sheet carries a net profit row")


def _income(grid: Grid) -> dict[str, float]:
    row = next((r for r in grid if any(_upper(c, NET_PROFIT) for c in r[:3])), None)
    if row is None:
        return {}
    totals = next(
        (i for i, r in enumerate(grid) if sum(label(c) == "TOTAL" for c in r) > 1),
        None,
    )
    if totals is None or totals == 0:
        raise ValueError("income statement has no MN, ME, TOTAL header")
    names = grid[totals - 1]
    result = {}
    for col, cell in enumerate(grid[totals]):
        if label(cell) != "TOTAL":
            continue
        name = next(
            (names[c] for c in range(col, max(col - 3, -1), -1) if _text(names, c)),
            None,
        )
        if name is None:
            raise ValueError(f"no entity name above the TOTAL in column {col}")
        result[entity(str(name))] = _number(row, col)
    return result


def _upper(value: Cell, prefixes: Sequence[str]) -> bool:
    # The income statement writes its lines in capitals; the balance sheet
    # repeats net profit as "Resultado Neto del Ejercicio".
    return (
        isinstance(value, str) and value.strip().isupper() and _matches(value, prefixes)
    )


def indicator(
    sheets: Sequence[tuple[str, Grid]], prefixes: Sequence[str]
) -> dict[str, float]:
    """Each entity's value of the indicator whose label starts with one of
    `prefixes`, in percent, from an indicators workbook. Entity names sit in
    the first row above the data that names several columns."""
    for _, grid in sheets:
        row = next((r for r in grid if r and _matches(r[0], prefixes)), None)
        if row is None:
            continue
        names = next(r for r in grid if sum(_text(r, c) for c in range(1, len(r))) > 1)
        return {
            entity(str(names[c])): _number(row, c)
            for c in range(1, len(names))
            if _text(names, c) and isinstance(_at(row, c), float)
        }
    raise ValueError(f"no sheet carries an indicator starting {prefixes[0]}")


def _at(row: Sequence[Cell], col: int) -> Cell:
    return row[col] if col < len(row) else None


def _text(row: Sequence[Cell], col: int) -> bool:
    value = _at(row, col)
    return isinstance(value, str) and bool(value.strip())


def _number(row: Sequence[Cell], col: int) -> float:
    value = _at(row, col)
    if not isinstance(value, float):
        raise ValueError(f"column {col} holds {value!r}, not a number")
    return value
