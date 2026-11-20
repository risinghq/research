import json

from typing import TYPE_CHECKING

import figures
import pandas as pd
import pytest


if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("value", "kind", "expected"),
    [
        (2014, "year", "2014"),
        (pd.Timestamp("2014-09-30"), "quarter", "2014-Q3"),
        (pd.Period("2014-09", freq="M"), "month", "2014-09"),
        ("2014-09-03", "day", "2014-09-03"),
        (-3, "number", -3),
        (0.5, "number", 0.5),
        ("state", "category", "state"),
    ],
)
def test_an_x_value_takes_the_chart_file_format_of_its_axis(
    value: object, kind: figures.XKind, expected: object
) -> None:
    assert figures.x_value(value, kind) == expected


def test_a_line_chart_writes_gaps_as_null_and_snaps_marks_to_the_axis(
    tmp_path: Path,
) -> None:
    months = pd.date_range("2015-06-01", periods=4, freq="MS")
    values = pd.Series([1.0, float("nan"), 2.123456789, 3.0], months)

    path = figures.lines(
        tmp_path,
        "monthly",
        {"Monthly": values},
        figures.Style("Title", "Subtitle", "Source."),
        figures.Axis("month"),
        marks={"2015-07-15": "mid July"},
        span=("2015-06-03", "2015-09-30", "review"),
    )

    chart = json.loads(path.read_text("utf-8"))
    assert chart["x"] == {"kind": "period"}
    assert chart["series"][0]["points"][1:3] == [
        {"x": "2015-07", "y": None},
        {"x": "2015-08", "y": 2.12346},
    ]
    # A mark inside a month lands on that month, the axis's own x.
    assert chart["marks"] == [{"x": "2015-07", "label": "mid July"}]
    assert chart["span"] == {"from": "2015-06", "to": "2015-09", "label": "review"}
    with pytest.raises(ValueError, match="after the last x"):
        figures.snap("2016-01-01", ["2015-06", "2015-09"], "month")
