from datetime import date
from pathlib import Path

import httpx2
import nahb
import pytest


FIXTURES = Path(__file__).parent / "fixtures"
TABLE_2 = (
    "https://www.nahb.org/-/media/NAHB/news-and-economics/docs/housing-economics/"
    "hmi/2026-11/t2-national-hmi-history-202611.xls"
    "?rev=7d3ee4092c5e4a138b0bd90ade05c83b&hash=FCD8B1ED5E31ADB32A98AA27C4BD00E0"
)


def test_the_history_follows_the_page_link_to_every_released_month() -> None:
    asked = []

    def answer(request: httpx2.Request) -> httpx2.Response:
        asked.append(str(request.url))
        if request.url.path.endswith(".xls"):
            name = "t2-national-hmi-history-202611.xls"
            return httpx2.Response(200, content=(FIXTURES / name).read_bytes())
        return httpx2.Response(200, content=(FIXTURES / "hmi.html").read_bytes())

    client = nahb.NahbClient(transport=httpx2.MockTransport(answer))
    history = client.history()

    assert asked == [nahb.HMI_PAGE, TABLE_2]
    # January 1985 to November 2026; December 2026 is not released yet.
    assert len(history) == 41 * 12 + 11
    first, last = history[0], history[-1]
    assert (first.day, first.value) == (date(1985, 1, 1), 50)
    assert (last.day, last.value) == (date(2026, 11, 1), 25)
    assert [o.day for o in history] == sorted(o.day for o in history)


def test_a_page_without_the_table_link_raises() -> None:
    with pytest.raises(nahb.NahbError, match="no Table 2"):
        nahb.table_link("<a href='/t1-hmi-and-components-202611.xls'>Table 1</a>")
