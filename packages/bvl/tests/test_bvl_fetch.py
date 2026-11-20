from contextlib import closing
from datetime import date
from pathlib import Path

import bcrp
import httpx2
import smv

from bvl import fetch, store


PACKAGES = Path(__file__).parents[2]
SMV_ANSWERS = PACKAGES / "smv" / "tests" / "fixtures"
BCRP_ANSWERS = PACKAGES / "bcrp" / "tests" / "fixtures"


def test_fill_bcrp_stores_each_series_without_unpublished_days(tmp_path: Path) -> None:
    requests: list[httpx2.Request] = []

    def answer(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, content=(BCRP_ANSWERS / "bcrp.json").read_bytes())

    client = bcrp.BcrpClient(transport=httpx2.MockTransport(answer))
    db = tmp_path / "bvl.sqlite"
    with closing(store.connect(db)) as connection:
        fetch.fill_bcrp(client, connection, date(2026, 11, 10), date(2026, 11, 16))
    rows = store.read(db, "SELECT * FROM bcrp_series WHERE code = 'PD04638PD'")

    assert requests[0].url.path.endswith("/PD04638PD/json/2026-11-10/2026-11-16")
    assert len(requests) == len(bcrp.SERIES)
    # The fixture's 13 and 16 Nov read "n.d.".
    assert list(rows["date"]) == ["2026-11-10", "2026-11-11", "2026-11-12"]
    assert rows["value"].iloc[-1] == 3.40585714285714


def test_fill_broker_amounts_stamps_each_row_with_its_day(tmp_path: Path) -> None:
    def answer(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=(SMV_ANSWERS / "brokers.json").read_bytes())

    client = smv.SmvClient(None, transport=httpx2.MockTransport(answer))
    db = tmp_path / "bvl.sqlite"
    with closing(store.connect(db)) as connection:
        fetch.fill_broker_amounts(
            client, connection, [date(2025, 1, 6)], date(2026, 1, 1)
        )
    rows = store.read(db, "SELECT * FROM broker_amounts ORDER BY broker")

    assert list(rows["broker"]) == ["CRE", "GCO", "ITG"]
    assert set(rows["date"]) == {"2025-01-06"}
    assert rows["sold"].iloc[2] == 6944573.36


def test_fill_statements_skips_a_quarter_that_has_not_ended(tmp_path: Path) -> None:
    asked: list[tuple[str, str]] = []

    def answer(request: httpx2.Request) -> httpx2.Response:
        asked.append((request.url.params["sPeriodo"], request.url.params["sTipoInf"]))
        return httpx2.Response(
            200, content=(SMV_ANSWERS / "statements.json").read_bytes()
        )

    client = smv.SmvClient(None, transport=httpx2.MockTransport(answer))
    with closing(store.connect(tmp_path / "bvl.sqlite")) as connection:
        fetch.fill_statements(
            client, connection, date(2025, 1, 1), date(2025, 12, 31), date(2025, 8, 1)
        )
    assert asked == [("1", "I"), ("1", "C"), ("2", "I"), ("2", "C")]
