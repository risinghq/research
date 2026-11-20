"""Writes the chart files research.rising.sh draws, one JSON file per figure.
docs/charts.md defines the format.

The site draws each chart on the study page and as a static SVG, so a study
writes data and labels here, never pixels.
"""

import json
import math

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pandas as pd


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

XKind = Literal["year", "quarter", "month", "day", "number", "category"]
Kind = Literal["line", "columns", "bars", "scatter"]
_PERIODS = ("year", "quarter", "month", "day")


@dataclass(frozen=True)
class Style:
    """The words and number format of a chart. `unit` is `%`, `$`, empty, or a
    word written after the value."""

    title: str
    subtitle: str
    source: str
    unit: str = ""
    decimals: int = 0


@dataclass(frozen=True)
class Axis:
    """The x axis. `label`, `unit` and `decimals` describe a number axis."""

    kind: XKind
    label: str = ""
    unit: str = ""
    decimals: int = 0

    def as_json(self) -> dict[str, object]:
        if self.kind in _PERIODS:
            return {"kind": "period"}
        if self.kind == "category":
            return {"kind": "category"}
        return {
            "kind": "number",
            "label": self.label,
            "unit": self.unit,
            "decimals": self.decimals,
        }


def x_value(value: object, kind: XKind) -> str | float:
    """`value` as the chart file's x: `YYYY`, `YYYY-Qn`, `YYYY-MM` or
    `YYYY-MM-DD` for a period, a number, or a category's name."""
    if kind == "number":
        number = float(value)  # type: ignore[arg-type]
        return int(number) if number.is_integer() else number
    if kind == "category":
        return str(value)
    if kind == "year" and isinstance(value, int | str) and str(value).isdigit():
        return str(value)
    stamp = value.start_time if isinstance(value, pd.Period) else pd.Timestamp(value)  # type: ignore[arg-type]
    if kind == "year":
        return str(stamp.year)
    if kind == "quarter":
        return f"{stamp.year}-Q{stamp.quarter}"
    if kind == "month":
        return stamp.strftime("%Y-%m")
    return stamp.strftime("%Y-%m-%d")


def y_value(value: object) -> float | None:
    """`value` to six significant digits, or None for a missing value."""
    number = float(value)  # type: ignore[arg-type]
    if math.isnan(number):
        return None
    return float(f"{number:.6g}")


def snap(when: str, xs: Sequence[object], kind: XKind) -> object:
    """The first x on the axis at or after the date `when`."""
    target = x_value(when, kind)
    for x in xs:
        if str(x) >= str(target):
            return x
    message = f"{when} is after the last x, {xs[-1]}"
    raise ValueError(message)


def chart(
    kind: Kind,
    style: Style,
    axis: Axis,
    series: Sequence[Mapping[str, object]],
    *,
    view: str | None = None,
    compare: Mapping[str, object] | None = None,
    marks: Sequence[Mapping[str, object]] = (),
    span: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """The chart file from parts already in its format."""
    result: dict[str, object] = {
        "kind": kind,
        "title": style.title,
        "subtitle": style.subtitle,
        "source": style.source,
        "unit": style.unit,
        "decimals": style.decimals,
        "x": axis.as_json(),
        "series": list(series),
    }
    if view is not None:
        result["view"] = view
    if compare is not None:
        result["compare"] = compare
    if marks:
        result["marks"] = list(marks)
    if span is not None:
        result["span"] = span
    return result


def write(out: Path, name: str, value: Mapping[str, object]) -> Path:
    """Write `value` as `out/name.json`."""
    path = out / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=1, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def _points(values: pd.Series, kind: XKind) -> list[dict[str, object]]:
    return [
        {"x": x_value(x, kind), "y": y_value(y)}
        for x, y in zip(values.index, values.to_numpy(), strict=True)
    ]


def lines(
    out: Path,
    name: str,
    series: Mapping[str, pd.Series],
    style: Style,
    axis: Axis,
    *,
    marks: Mapping[str, str] | None = None,
    span: tuple[str, str, str] | None = None,
) -> Path:
    """One line per series over a shared x axis. `marks` maps a date to a label
    drawn as a vertical line; `span` is a (start, end, label) shaded band. Both
    snap to the first x on or after their date. Every series shares one x."""
    points = {label: _points(values, axis.kind) for label, values in series.items()}
    xs = [point["x"] for point in next(iter(points.values()))]
    for label, each in points.items():
        if [point["x"] for point in each] != xs:
            message = f"{label} does not share the x of the first series"
            raise ValueError(message)
    drawn = [{"label": label, "points": each} for label, each in points.items()]
    return write(
        out,
        name,
        chart(
            "line",
            style,
            axis,
            drawn,
            marks=[
                {"x": snap(when, xs, axis.kind), "label": label}
                for when, label in (marks or {}).items()
            ],
            span=None
            if span is None
            else {
                "from": snap(span[0], xs, axis.kind),
                "to": snap(span[1], xs, axis.kind),
                "label": span[2],
            },
        ),
    )


def columns(out: Path, name: str, values: pd.Series, style: Style, axis: Axis) -> Path:
    """Vertical bars along an ordered x axis."""
    drawn = [{"label": style.title, "points": _points(values, axis.kind)}]
    return write(out, name, chart("columns", style, axis, drawn))


def bars(
    out: Path,
    name: str,
    values: pd.Series,
    style: Style,
    *,
    low: pd.Series | None = None,
    high: pd.Series | None = None,
) -> Path:
    """Horizontal bars, one per category in `values`' order, with optional
    whiskers from `low` to `high`."""
    points = _points(values, "category")
    if low is not None and high is not None:
        for point, a, b in zip(points, low.to_numpy(), high.to_numpy(), strict=True):
            point["low"], point["high"] = y_value(a), y_value(b)
    drawn = [{"label": style.title, "points": points}]
    return write(out, name, chart("bars", style, Axis("category"), drawn))


def scatter(
    out: Path,
    name: str,
    x: pd.Series,
    y: pd.Series,
    style: Style,
    axis: Axis,
    *,
    size: pd.Series | None = None,
) -> Path:
    """One point per row, named by the index; `size` scales each point's area."""
    points: list[dict[str, object]] = []
    for row, (key, a, b) in enumerate(
        zip(x.index, x.to_numpy(), y.to_numpy(), strict=True)
    ):
        point: dict[str, object] = {"x": y_value(a), "y": y_value(b), "name": str(key)}
        if size is not None:
            point["size"] = y_value(size.iloc[row])
        points.append(point)
    drawn = [{"label": style.title, "points": points}]
    return write(out, name, chart("scatter", style, axis, drawn))
