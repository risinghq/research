"""Writes the files a replication publishes: the chart file research.rising.sh
draws, `numbers.json`, the PNG figure and the README's `data` date.
docs/replications.md defines the chart file and `original.csv`.

A period is `YYYY-MM` for a month or `YYYY-Qn` for a quarter.
"""

import csv
import json
import re

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Protocol

import figures
import pandas as pd


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from datetime import date
    from pathlib import Path

_DATA_LINE = re.compile(r"^data: .*$", re.MULTILINE)
_FIELD = re.compile(r"^([a-z]+): (.+)$", re.MULTILINE)
_QUARTER = re.compile(r"^(\d{4})-Q([1-4])$")


class Observation(Protocol):
    """A source's value for the month or quarter that starts on `day`."""

    @property
    def day(self) -> date: ...
    @property
    def value(self) -> float: ...
    @property
    def preliminary(self) -> bool: ...


@dataclass(frozen=True)
class Point:
    """A period's value; None when the source published none for it."""

    period: str
    value: float | None
    preliminary: bool = False


@dataclass(frozen=True)
class Original:
    """The values a post published, by period, and who published them when."""

    outlet: str
    posted: str
    values: Mapping[str, float]


@dataclass(frozen=True)
class Chart:
    """How a replication's series is drawn.

    `name` is the file stem of the chart file and the figure. `ylabel` and
    `scale` apply only to the PNG, which divides each value by `scale`.
    """

    name: str
    kind: Literal["columns", "line"]
    title: str
    subtitle: str
    unit: str
    decimals: int
    source: str
    ylabel: str
    scale: float = 1


def period(day: date, *, quarterly: bool = False) -> str:
    if quarterly:
        return f"{day.year}-Q{(day.month - 1) // 3 + 1}"
    return day.strftime("%Y-%m")


def _pandas_period(value: str) -> pd.Period:
    quarter = _QUARTER.match(value)
    if quarter:
        return pd.Period(f"{quarter[1]}Q{quarter[2]}", freq="Q")
    return pd.Period(value, freq="M")


def period_end(value: str) -> date:
    end: date = _pandas_period(value).end_time.date()
    return end


def levels(
    observations: Sequence[Observation], *, quarterly: bool = False
) -> list[Point]:
    """One point for every period from the first observation to the last, oldest
    first, with None for a period the source left out."""
    by_period = {period(o.day, quarterly=quarterly): o for o in observations}
    first, last = min(by_period), max(by_period)
    span = pd.period_range(_pandas_period(first), _pandas_period(last))
    points = []
    for step in span:
        key = period(step.start_time.date(), quarterly=quarterly)
        found = by_period.get(key)
        points.append(
            Point(key, None)
            if found is None
            else Point(key, found.value, found.preliminary)
        )
    return points


def changes(
    points: Sequence[Point], lag: int, how: Callable[[float, float], float]
) -> list[Point]:
    """`how(now, before)` for each point against the one `lag` periods before it,
    from the `lag`-th point on. None when either value is missing; preliminary
    when either is."""
    result = []
    for before, now in zip(points, points[lag:], strict=False):
        value = (
            None
            if now.value is None or before.value is None
            else how(now.value, before.value)
        )
        result.append(Point(now.period, value, now.preliminary or before.preliminary))
    return result


def _number(text: str) -> float:
    return int(text) if text.lstrip("-").isdigit() else float(text)


def read_original(study: Path) -> Original:
    """The original of the study folder `study`: the outlet and posted date from
    its README front matter, and its values from `original.csv`."""
    readme = (study / "README.md").read_text(encoding="utf-8")
    front = dict(_FIELD.findall(readme.split("\n---\n", 1)[0]))
    with (study / "original.csv").open(encoding="utf-8", newline="") as file:
        values = {row["period"]: _number(row["value"]) for row in csv.DictReader(file)}
    return Original(front["outlet"], front["posted"], values)


def revised(posted: float, now: float | None) -> bool:
    """Whether `now` differs from `posted` at the precision `posted` was published."""
    if now is None:
        return True
    exponent = Decimal(repr(posted)).normalize().as_tuple().exponent
    places = max(0, -int(exponent))
    return round(now, places) != posted


def numbers(points: Sequence[Point], original: Original) -> dict[str, object]:
    """The latest value, the preliminary periods, and each posted period then and now."""
    now = {point.period: point.value for point in points}
    compared = [
        {"period": key, "posted": value, "now": now.get(key)}
        for key, value in original.values.items()
    ]
    return {
        "latest": asdict(points[-1]),
        "preliminary": [point.period for point in points if point.preliminary],
        "revised_since_post": [
            row
            for row, posted in zip(compared, original.values.values(), strict=True)
            if revised(posted, now.get(str(row["period"])))
        ],
        "against_original": compared,
    }


def chart_file(
    chart: Chart, points: Sequence[Point], original: Original
) -> dict[str, object]:
    """The chart file, opening on the post's first period."""
    return {
        "kind": chart.kind,
        "title": chart.title,
        "subtitle": chart.subtitle,
        "unit": chart.unit,
        "decimals": chart.decimals,
        "source": chart.source,
        "view": min(original.values),
        "points": [asdict(point) for point in points],
        "compare": {
            "label": f"{original.outlet}, {original.posted}",
            "points": [
                {"period": key, "value": value}
                for key, value in original.values.items()
            ],
        },
    }


def set_data_date(readme: str, day: date) -> str:
    return _DATA_LINE.sub(f"data: {day.isoformat()}", readme, count=1)


def _label(value: pd.Period) -> str:
    if value.freqstr.startswith("Q"):
        return f"Q{value.quarter} {value.strftime('%y')}"
    return value.strftime("%b %y")


def _draw(chart: Chart, points: Sequence[Point], path: Path) -> None:
    """The figure over the post's periods, for GitHub and as the site's fallback."""
    periods = [_pandas_period(point.period) for point in points]
    values = [
        float("nan") if point.value is None else point.value / chart.scale
        for point in points
    ]
    note = f"Source: {chart.source}"
    if chart.kind == "columns":
        figures.bars(
            pd.Series(values, index=[_label(p) for p in periods]),
            path,
            title=chart.title,
            ylabel=chart.ylabel,
            note=note,
        )
    else:
        days = pd.DatetimeIndex([p.start_time for p in periods])
        figures.lines(
            {chart.title: pd.Series(values, index=days)},
            path,
            title=chart.title,
            ylabel=chart.ylabel,
            note=note,
        )


def publish(
    out: Path, chart: Chart, points: Sequence[Point], original: Original
) -> dict[str, object]:
    """Write the chart file, `numbers.json` and the figure, date the README, and
    return the numbers."""
    shown = [point for point in points if point.period >= min(original.values)]
    result = numbers(points, original)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "numbers.json", result)
    _write_json(out / f"{chart.name}.json", chart_file(chart, points, original))
    _draw(chart, shown, out / f"{chart.name}.png")
    readme = out / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        day = period_end(points[-1].period)
        readme.write_text(set_data_date(text, day), encoding="utf-8")
    return result


def _write_json(path: Path, value: object) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
