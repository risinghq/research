"""Reads the NAHB/Wells Fargo Housing Market Index (HMI) from NAHB's site.

The HMI is a monthly survey of single-family homebuilders, released for the
current month around its middle at 10:00 Eastern. A reading above 50 means
more builders see conditions as good than poor. NAHB's HMI page links
"Table 2: National HMI - History", an .xls with a row per year from 1985 and
a column per month, seasonally adjusted. Each release moves the table to a new
URL, so the client reads the link from the page. NAHB allows reuse of the
series with credit to the NAHB/Wells Fargo Housing Market Index.
"""

import html
import io
import re

from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin

import httpx2
import pandas as pd


HMI_PAGE = (
    "https://www.nahb.org/news-and-economics/housing-economics/indices/"
    "housing-market-index"
)
_TABLE_2 = re.compile(r'href="([^"]*t2-national-hmi-history-\d{6}\.xls[^"]*)"')
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
_MONTHS += ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass(frozen=True)
class Observation:
    """A month's index; `day` is the first of the month. NAHB marks no value as
    preliminary."""

    day: date
    value: float
    preliminary: bool = False


class NahbError(Exception):
    """NAHB's page or table is not in the shape this module reads."""


def table_link(page: str) -> str:
    """The absolute URL of Table 2 in the HTML of the HMI page."""
    found = _TABLE_2.search(page)
    if found is None:
        raise NahbError("the HMI page links no Table 2 history")
    return urljoin(HMI_PAGE, html.unescape(found[1]))


def parse_history(content: bytes) -> list[Observation]:
    """Each month's index in Table 2, oldest first, without the months not yet
    released."""
    sheet = pd.read_excel(io.BytesIO(content), header=None, engine="calamine")
    header = sheet.index[sheet.iloc[:, 1:13].eq(_MONTHS).all(axis=1)]
    if header.empty:
        raise NahbError("Table 2 has no row of month names")
    observations = []
    for _, row in sheet.loc[header[0] + 1 :].iterrows():
        year = row.iloc[0]
        if not isinstance(year, float | int) or pd.isna(year):
            continue
        for month, value in enumerate(row.iloc[1:13], start=1):
            if isinstance(value, float | int) and not pd.isna(value):
                day = date(int(year), month, 1)
                observations.append(Observation(day, float(value)))
    return observations


class NahbClient:
    def __init__(self, *, transport: httpx2.BaseTransport | None = None) -> None:
        self._http = httpx2.Client(
            timeout=60, follow_redirects=True, transport=transport
        )

    def close(self) -> None:
        self._http.close()

    def history(self) -> list[Observation]:
        """The HMI from January 1985 to the latest release."""
        page = self._get(HMI_PAGE).text
        return parse_history(self._get(table_link(page)).content)

    def _get(self, url: str) -> httpx2.Response:
        response = self._http.get(url)
        response.raise_for_status()
        return response
