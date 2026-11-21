from typing import TYPE_CHECKING

import openpyxl
import pytest
import sbs


if TYPE_CHECKING:
    from pathlib import Path


def workbook(path: Path, sheets: dict[str, list[list[object]]]) -> Path:
    book = openpyxl.Workbook()
    book.remove(book.active)  # type: ignore[arg-type]
    for title, rows in sheets.items():
        sheet = book.create_sheet(title)
        for row in rows:
            sheet.append(row)
    # The SBS names Excel 2007 workbooks `.XLS` too.
    book.save(path)
    return path


def test_file_path_uses_the_sbs_month_folder_and_code() -> None:
    assert sbs.file_path("C-1101", 2026, 9) == (
        "/estadistica/financiera/2026/Setiembre/C-1101-se2026.XLS"
    )
    assert sbs.file_name("B-3301", 2013, 1) == "B-3301-en2013.XLS"


def test_net_profit_reads_each_total_column_of_the_income_statement(
    tmp_path: Path,
) -> None:
    balance: list[list[object]] = [
        [None, "Balance General"],
        [None, "Resultado Neto del Ejercicio", 1.0, 2.0, 3.0],
    ]
    lima = "Caja Municipal de Crédito Popular Lima**"
    income: list[list[object]] = [
        [None, "Estado de Ganancias y Pérdidas"],
        [None, None, "CMAC\n Piura 1/", None, None, lima, None, None, "TOTAL CM"],
        [None, None, *["MN", "ME", "TOTAL"] * 3],
        [None, "INGRESOS FINANCIEROS", 10.0, 1.0, 11.0, 5.0, 0.0, 5.0, 15.0, 1.0, 16.0],
        [None, "RESULTADO NETO DEL EJERCICIO", 4, 0.5, 4.5, -1, 0, -1, 3, 0.5, 3.5],
    ]
    path = workbook(tmp_path / "C-1101-se2026.XLS", {"bg": balance, "gyp": income})

    found = sbs.net_profit(list(sbs.grids(path)))

    assert found == {"CMAC Piura": 4.5, "CMCP Lima": -1.0, "TOTAL CM": 3.5}


def test_net_profit_refuses_a_workbook_without_an_income_statement(
    tmp_path: Path,
) -> None:
    path = workbook(tmp_path / "x.XLS", {"bg": [["Activo", 1.0]]})
    with pytest.raises(ValueError, match="net profit"):
        sbs.net_profit(list(sbs.grids(path)))


def test_indicator_reads_both_halves_of_a_split_table(tmp_path: Path) -> None:
    rows: list[list[object]] = [
        ["Indicadores Financieros por Caja"],
        [None, "CMAC Arequipa", "CMAC Cusco 2/", None, "CMAC Tacna", "TOTAL CM"],
        ["SOLVENCIA", None, None, None, None, None],
        [
            "Utilidad Neta Anualizada sobre Patrimonio Promedio",
            23.1,
            25.77,
            "Utilidad Neta Anualizada sobre Patrimonio Promedio",
            9.5,
            20.0,
        ],
        [
            "Créditos Atrasados (criterio SBS) / Créditos Directos",
            4.0,
            3.5,
            None,
            6.0,
            4.4,
        ],
    ]
    path = workbook(tmp_path / "C-1301-se2026.XLS", {"ind": rows})
    sheets = list(sbs.grids(path))

    assert sbs.indicator(sheets, sbs.ROE) == {
        "CMAC Arequipa": 23.1,
        "CMAC Cusco": 25.77,
        "CMAC Tacna": 9.5,
        "TOTAL CM": 20.0,
    }
    assert sbs.indicator(sheets, sbs.ARREARS)["CMAC Tacna"] == 6.0
    with pytest.raises(ValueError, match="indicator"):
        sbs.indicator(sheets, ("LIQUIDEZ",))


@pytest.mark.parametrize(
    ("name", "aggregate"),
    [
        ("TOTAL CMAC", True),
        ("Total Empresas Financieras", True),
        ("TOTAL EMPRESAS DE CRÉDITOS", True),
        ("TOTAL Servicios Financieros", False),
        ("CMAC Piura", False),
    ],
)
def test_is_aggregate_tells_system_sums_from_firms(name: str, aggregate: bool) -> None:
    assert sbs.is_aggregate(name) is aggregate
