"""Client for the Bureau of Labor Statistics Public Data API v2 at `api.bls.gov`.

Without a key the API answers at most 25 series and 10 years per request and
25 requests a day for each address. A registration key raises that to 50
series, 20 years and 500 requests. A period is `M01` to `M12` for a month,
`M13` for an annual average, or `Q01` to `Q04` for a quarter (`Q05` is the
annual one). A value of `-` means no value, and the footnote code `P` marks a
preliminary value.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

import httpx2


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

BASE_URL = "https://api.bls.gov/publicAPI/v2/"
PAYROLLS = "CES0000000001"
# The series the studies read, by BLS id.
SERIES = {
    PAYROLLS: "total nonfarm employment, seasonally adjusted, thousands",
}
YEARS_PER_REQUEST = {False: 10, True: 20}


@dataclass(frozen=True)
class Observation:
    """One period's value; `day` is the first day of the month or quarter."""

    day: date
    value: float
    preliminary: bool


class BlsError(Exception):
    """The API answered without processing the request, as on a daily limit."""


def period_day(year: str, period: str) -> date | None:
    """The first day of `M01` to `M12` or `Q01` to `Q04`; None for an annual period."""
    number = int(period[1:])
    if period.startswith("M") and number <= 12:
        return date(int(year), number, 1)
    if period.startswith("Q") and number <= 4:
        return date(int(year), 3 * number - 2, 1)
    return None


def parse_series(body: Mapping[str, Any]) -> dict[str, list[Observation]]:
    """Each series' observations, oldest first, without annual or empty periods."""
    if body["status"] != "REQUEST_SUCCEEDED":
        raise BlsError("; ".join(body["message"]) or body["status"])
    parsed = {}
    for series in body["Results"]["series"]:
        observations = []
        for row in series["data"]:
            day = period_day(row["year"], row["period"])
            if day is None or row["value"] == "-":
                continue
            codes = {note.get("code") for note in row["footnotes"]}
            observations.append(Observation(day, float(row["value"]), "P" in codes))
        parsed[series["seriesID"]] = sorted(observations, key=lambda o: o.day)
    return parsed


def windows(start: int, end: int, span: int) -> list[tuple[int, int]]:
    """Consecutive year ranges of at most `span` years covering `start` to `end`."""
    return [
        (first, min(first + span - 1, end)) for first in range(start, end + 1, span)
    ]


class BlsClient:
    def __init__(
        self, key: str | None = None, *, transport: httpx2.BaseTransport | None = None
    ) -> None:
        self._key = key
        self._http = httpx2.Client(base_url=BASE_URL, timeout=60, transport=transport)

    def close(self) -> None:
        self._http.close()

    def series(
        self, ids: Sequence[str], start: int, end: int
    ) -> dict[str, list[Observation]]:
        """Every observation of `ids` from January of `start` to the end of `end`."""
        merged: dict[str, list[Observation]] = {code: [] for code in ids}
        for first, last in windows(
            start, end, YEARS_PER_REQUEST[self._key is not None]
        ):
            for code, observations in self._request(ids, first, last).items():
                merged[code].extend(observations)
        return merged

    def _request(
        self, ids: Sequence[str], start: int, end: int
    ) -> dict[str, list[Observation]]:
        payload: dict[str, object] = {
            "seriesid": list(ids),
            "startyear": str(start),
            "endyear": str(end),
        }
        if self._key is not None:
            payload["registrationkey"] = self._key
        response = self._http.post("timeseries/data/", json=payload)
        response.raise_for_status()
        return parse_series(response.json())
