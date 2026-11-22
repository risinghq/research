import io
import zipfile

import httpx2
import mef
import pytest


# One span file's columns, cut to the identifiers a test reads.
HEADER = ",".join(
    f'"{name}"'
    for name in [
        "SECTOR",
        "PLIEGO",
        "PLIEGO_NOMBRE",
        *(f"{stage}_{year}" for year in (2025, 2026) for stage in mef.STAGES),
    ]
)


def row(sector: str, pliego: str, name: str, values: list[str]) -> str:
    return ",".join(f'"{v}"' for v in [sector, pliego, name, *values])


def span_zip(text: str, method: int = zipfile.ZIP_DEFLATED) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=method) as archive:
        archive.writestr("comparativo.csv", text.encode("utf-8-sig"))
    return buffer.getvalue()


def client_for(body: bytes) -> mef.MefClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path.endswith("comparativo_gastos_2022_2026.zip")
        return httpx2.Response(200, content=body)

    return mef.MefClient(transport=httpx2.MockTransport(handler))


def test_rows_streams_the_zip_and_keeps_matching_lines() -> None:
    values = [str(n) for n in range(14)]
    text = "\r\n".join(
        [
            HEADER,
            row("11", "011", "M. DE SALUD", values),
            row("10", "510", "U.N. MAYOR DE SAN MARCOS", values),
            row("10", "517", "U.N. DEL CENTRO DEL PERÚ", ["1.5", *values[1:]]),
        ]
    )
    client = client_for(span_zip(text))
    kept = list(client.rows((2022, 2026), lambda line: line.startswith('"10"')))
    client.close()
    assert [r["PLIEGO_NOMBRE"] for r in kept] == [
        "U.N. MAYOR DE SAN MARCOS",
        "U.N. DEL CENTRO DEL PERÚ",
    ]
    by_year = dict(mef.years(kept[1]))
    assert by_year[2025]["PIA"] == 1.5
    assert by_year[2026]["DEVENGADO"] == 12.0


def test_rows_rejects_a_zip_that_is_not_deflated() -> None:
    client = client_for(span_zip(HEADER, zipfile.ZIP_STORED))
    with pytest.raises(ValueError, match="method 0"):
        list(client.rows((2022, 2026), lambda line: True))
    client.close()


def test_daily_reads_the_zipped_csv_by_month() -> None:
    header = ",".join(
        f'"{n}"'
        for n in ["ANO_EJE", "MES_EJE", "PLIEGO", *(f"MONTO_{s}" for s in mef.STAGES)]
    )
    text = "\n".join(
        [
            header,
            '"2026","1","510","100","120","","","","10","5"',
            '"2026","2","011","1","1","1","1","1","1","1"',
        ]
    )
    body = span_zip(text)

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path.endswith("2026-Gasto-Diario.zip")
        return httpx2.Response(200, content=body)

    client = mef.MefClient(transport=httpx2.MockTransport(handler))
    kept = list(client.daily(2026, lambda line: '"510"' in line))
    client.close()
    assert [r["MES_EJE"] for r in kept] == ["1"]
    stages = mef.monthly(kept[0])
    assert (stages["PIA"], stages["CERTIFICADO"], stages["DEVENGADO"]) == (100, 0, 10)


def test_revenue_reads_the_daily_revenue_file_without_a_bom() -> None:
    header = ",".join(
        f'"{n}"'
        for n in ["ANO_DOC", "PLIEGO", *(f"MONTO_{s}" for s in mef.REVENUE_STAGES)]
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        text = "\n".join([header, '"2026","511","","20.5","7"'])
        archive.writestr("ingreso.csv", text.encode("utf-8"))
    body = buffer.getvalue()

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path.endswith("2026-Ingreso-Diario.zip")
        return httpx2.Response(200, content=body)

    client = mef.MefClient(transport=httpx2.MockTransport(handler))
    kept = list(client.revenue(2026, lambda line: True))
    client.close()
    assert [r["ANO_DOC"] for r in kept] == ["2026"]
    assert mef.collected(kept[0]) == {"PIA": 0.0, "PIM": 20.5, "RECAUDADO": 7.0}
