"""The monthly change in U.S. nonfarm payrolls, rebuilt from the BLS series that
Axios charted on 2026-11-06.

The change in a month is the seasonally adjusted level less the month before,
in jobs; BLS publishes the level in thousands. Each jobs report revises the
two months before it, and the annual benchmark in February revises years, so
a rerun can differ from the post in months it already showed.
"""

import argparse
import itertools
import json
import os
import re
import sys

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import bls
import figures
import pandas as pd


if TYPE_CHECKING:
    from collections.abc import Sequence

OUT = Path(__file__).parent
FIRST_YEAR = 2000
SOURCE = "Source: BLS, Current Employment Statistics, series CES0000000001."
POSTED = "2026-11-06"
# The post's chart data, in thousands of jobs, as Axios published it.
ORIGINAL = {
    "2026-01": 160,
    "2026-02": -156,
    "2026-03": 214,
    "2026-04": 148,
    "2026-05": 63,
    "2026-06": 31,
    "2026-07": -10,
    "2026-08": 186,
    "2026-09": 60,
    "2026-10": 165,
}
_DATA_LINE = re.compile(r"^data: .*$", re.MULTILINE)


def changes(levels: Sequence[bls.Observation]) -> list[dict[str, object]]:
    """Each month's change in jobs from the month before, from the second month on."""
    return [
        {
            "period": now.day.strftime("%Y-%m"),
            "value": round((now.value - before.value) * 1000),
            "preliminary": now.preliminary,
        }
        for before, now in itertools.pairwise(levels)
    ]


def against_original(points: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    """The post's months with the value then and the value now, in jobs."""
    now = {point["period"]: point["value"] for point in points}
    return [
        {
            "period": period,
            "posted": thousands * 1000,
            "now": now.get(period),
        }
        for period, thousands in ORIGINAL.items()
    ]


def chart(points: Sequence[dict[str, object]]) -> dict[str, object]:
    """The chart file the site draws, opening on the post's first month."""
    return {
        "kind": "columns",
        "title": "Change in U.S. nonfarm payrolls",
        "subtitle": "Monthly, seasonally adjusted",
        "unit": "jobs",
        "source": SOURCE.removeprefix("Source: "),
        "view": min(ORIGINAL),
        "points": list(points),
        "compare": {
            "label": f"Axios, {POSTED}",
            "points": [
                {"period": period, "value": thousands * 1000}
                for period, thousands in ORIGINAL.items()
            ],
        },
    }


def month_end(period: str) -> date:
    first = pd.Period(period, freq="M")
    return first.end_time.date()


def set_data_date(readme: str, day: date) -> str:
    return _DATA_LINE.sub(f"data: {day.isoformat()}", readme, count=1)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    # December of the year before gives the first year's January change.
    levels = client.series([bls.PAYROLLS], FIRST_YEAR - 1, today.year)[bls.PAYROLLS]
    points = changes(levels)
    view = [point for point in points if str(point["period"]) >= min(ORIGINAL)]
    latest = points[-1]
    compared = against_original(points)
    numbers: dict[str, object] = {
        "latest": latest,
        "preliminary": [p["period"] for p in points if p["preliminary"]],
        "revised_since_post": [c for c in compared if c["posted"] != c["now"]],
        "against_original": compared,
    }

    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "numbers.json", numbers)
    _write_json(out / "payrolls.json", chart(points))
    figures.bars(
        pd.Series(
            [int(str(p["value"])) / 1000 for p in view],
            index=[pd.Period(str(p["period"])).strftime("%b %y") for p in view],
        ),
        out / "payrolls.png",
        title="Change in U.S. nonfarm payrolls, monthly",
        ylabel="Thousands of jobs",
        note=SOURCE,
    )
    readme = out / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        day = month_end(str(latest["period"]))
        readme.write_text(set_data_date(text, day), encoding="utf-8")
    return numbers


def _write_json(path: Path, value: object) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the payrolls chart.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    client = bls.BlsClient(os.environ.get("BLS_API_KEY") or None)
    try:
        run(client, args.out, date.today())
    finally:
        client.close()
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
