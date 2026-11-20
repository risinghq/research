import json

from datetime import date
from pathlib import Path

import bls
import httpx2
import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def test_a_fetch_splits_years_into_windows_and_merges_them_oldest_first() -> None:
    asked = []

    def answer(request: httpx2.Request) -> httpx2.Response:
        payload = json.loads(request.content)
        asked.append((payload["startyear"], payload["endyear"]))
        if payload["startyear"] == "2025":
            content = (FIXTURES / "payrolls.json").read_bytes()
            return httpx2.Response(200, content=content)
        empty = {"seriesID": bls.PAYROLLS, "data": []}
        body = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [empty]}}
        return httpx2.Response(200, json=body)

    client = bls.BlsClient(transport=httpx2.MockTransport(answer))
    payrolls = client.series([bls.PAYROLLS], 2005, 2026)[bls.PAYROLLS]

    assert asked == [("2005", "2014"), ("2015", "2024"), ("2025", "2026")]
    assert len(payrolls) == 22
    first = payrolls[0]
    assert (first.day, first.value, first.preliminary) == (
        date(2025, 1, 1),
        158268.0,
        False,
    )
    assert [o.preliminary for o in payrolls[20:22]] == [True, True]


def test_quarters_start_their_first_month_and_annual_periods_are_dropped() -> None:
    assert bls.period_day("2026", "Q03") == date(2026, 7, 1)
    assert bls.period_day("2026", "M13") is None
    assert bls.period_day("2026", "Q05") is None


def test_a_refused_request_raises_the_api_message() -> None:
    body = {"status": "REQUEST_NOT_PROCESSED", "message": ["daily threshold"]}
    with pytest.raises(bls.BlsError, match="daily threshold"):
        bls.parse_series(body)
