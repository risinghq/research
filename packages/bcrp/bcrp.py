"""Client for the BCRP statistics API at `estadisticas.bcrp.gob.pe`.

The API needs no key and answers a whole daily series from 1996 in one request.
Each period is named `DD.Mon.YY` with a Spanish month abbreviation (`Set` is
September), and a day without a value reads `n.d.`.
"""

from datetime import date
from typing import TYPE_CHECKING, Any

import httpx2


if TYPE_CHECKING:
    from collections.abc import Mapping

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"
# BCRP's firewall answers 403 to httpx2's default user agent (2026-11-21).
USER_AGENT = "risinghq-research (+https://github.com/risinghq/research)"
SOL = "PD04638PD"
COPPER = "PD04701XD"
# The daily series the studies read, by BCRP code.
SERIES = {
    SOL: "interbank exchange rate, soles per US dollar, sell",
    COPPER: "copper, London, US cents per pound",
}
_MONTHS = {
    "Ene": 1,
    "Feb": 2,
    "Mar": 3,
    "Abr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Ago": 8,
    "Set": 9,
    # Monthly series name September `Sep`; daily ones use `Set`.
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dic": 12,
}


def period_day(name: str) -> date:
    """`02.Ene.97` as 1997-01-02. Series start in the 1990s, so `9x` is 199x."""
    day, month, year = name.split(".")
    two = int(year)
    return date(1900 + two if two >= 90 else 2000 + two, _MONTHS[month], int(day))


def period_name(name: str) -> str:
    """A monthly `Oct.2026` as `2026-10`, a quarterly `T3.26` as `2026-Q3`.
    Quarterly years have two digits, and series start in the 1980s."""
    if name.startswith("T") and name[1:2].isdigit():
        quarter, year = name[1:].split(".")
        century = "19" if int(year) >= 80 else "20"
        return f"{century}{year}-Q{quarter}"
    month, year = name.split(".")
    return f"{year}-{_MONTHS[month]:02}"


def parse_periods(body: Mapping[str, Any]) -> list[tuple[str, float]]:
    """The named values of a one-series monthly or quarterly answer, without
    the periods marked `n.d.`."""
    return [
        (period_name(p["name"]), float(p["values"][0]))
        for p in body["periods"]
        if p["values"][0] != "n.d."
    ]


def parse_series(body: Mapping[str, Any]) -> list[tuple[date, float]]:
    """The dated values of a one-series answer, without the `n.d.` days."""
    values = []
    for period in body["periods"]:
        value = period["values"][0]
        if value != "n.d.":
            values.append((period_day(period["name"]), float(value)))
    return values


class BcrpClient:
    def __init__(self, *, transport: httpx2.BaseTransport | None = None) -> None:
        self._http = httpx2.Client(
            base_url=BASE_URL,
            timeout=120,
            transport=transport,
            headers={"User-Agent": USER_AGENT},
        )

    def close(self) -> None:
        self._http.close()

    def series(self, code: str, start: date, end: date) -> list[tuple[date, float]]:
        response = self._http.get(f"{code}/json/{start.isoformat()}/{end.isoformat()}")
        response.raise_for_status()
        return parse_series(response.json())

    def periods(self, code: str, start: str, end: str) -> list[tuple[str, float]]:
        """A monthly or quarterly series. BCRP takes `start` and `end` as
        `YYYY-M` for a month and `YYYY-Q` for a quarter."""
        response = self._http.get(f"{code}/json/{start}/{end}")
        response.raise_for_status()
        return parse_periods(response.json())
