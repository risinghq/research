"""Peru's private investment from the BCRP's national accounts and business
expectations survey, opening with Gestión's report of 2026-11-21.

BCRP publishes the quarterly growth rate a few weeks after each quarter ends
and revises earlier quarters with each release.
"""

import argparse
import json
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import bcrp
import figures
import replication


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

OUT = Path(__file__).parent
SOURCE = "BCRP, BCRPData"
PRIVATE = "PN02522AQ"
PUBLIC = "PN02523AQ"
# Gross fixed private investment, percent of nominal GDP, quarterly.
PRIVATE_SHARE = "PN02556AQ"
# The survey's three-month investment index by sector; BCRPData has no total.
SECTORS = {
    "PD41404AM": "Mining and hydrocarbons",
    "PD41412AM": "Manufacturing",
    "PD41420AM": "Construction",
    "PD41428AM": "Commerce",
    "PD41436AM": "Services",
}
FIRST = "2000-1"


def points(values: Sequence[tuple[str, float]]) -> list[dict[str, object]]:
    return [{"x": x, "y": figures.y_value(y)} for x, y in values]


def growth_chart(private: Sequence[tuple[str, float]]) -> dict[str, object]:
    return figures.chart(
        "columns",
        figures.Style(
            "Private investment growth in Peru",
            "Gross fixed private investment, real, percent change on the same "
            "quarter a year before",
            SOURCE,
            "%",
            1,
        ),
        figures.Axis("quarter"),
        [{"label": "Latest estimate", "points": points(private)}],
        view="2022-Q1",
    )


def trailing_mean(
    values: Sequence[tuple[str, float]], n: int
) -> list[tuple[str, float]]:
    return [
        (values[i][0], sum(v for _, v in values[i - n + 1 : i + 1]) / n)
        for i in range(n - 1, len(values))
    ]


def share_chart(share: Sequence[tuple[str, float]]) -> dict[str, object]:
    return figures.chart(
        "line",
        figures.Style(
            "Private investment as a share of GDP",
            "Gross fixed private investment over nominal GDP, mean of the last "
            "four quarters",
            SOURCE,
            "%",
            1,
        ),
        figures.Axis("quarter"),
        [{"label": "Share of GDP", "points": points(trailing_mean(share, 4))}],
    )


def expectations_chart(
    sectors: Mapping[str, Sequence[tuple[str, float]]],
) -> dict[str, object]:
    return figures.chart(
        "line",
        figures.Style(
            "Firms' investment plans for the next three months",
            "Index of BCRP's monthly business survey by sector; above 50, more "
            "firms expect to invest more than less",
            SOURCE,
        ),
        figures.Axis("month"),
        [
            {"label": SECTORS[code], "points": points(values)}
            for code, values in sectors.items()
        ],
        view="2022-01",
    )


def highest_since(values: Sequence[tuple[str, float]], quarter: str) -> list[str]:
    """The quarters from 2010 on whose growth beat `quarter`'s."""
    level = dict(values)[quarter]
    return [x for x, y in values if x >= "2010" and y > level]


def date_readme(out: Path, month: str) -> None:
    """Set the README's `data` line to the last day of `month`, the newest
    period any chart shows."""
    readme = out / "README.md"
    if readme.exists():
        day = replication.period_end(month)
        text = readme.read_text(encoding="utf-8")
        readme.write_text(replication.set_data_date(text, day), encoding="utf-8")


def run(client: bcrp.BcrpClient, out: Path) -> dict[str, object]:
    last = "2030-4"
    private = client.periods(PRIVATE, FIRST, last)
    public = client.periods(PUBLIC, FIRST, last)
    share = client.periods(PRIVATE_SHARE, "1990-1", last)
    sectors = {code: client.periods(code, "2013-7", "2030-12") for code in SECTORS}
    charts = {
        "growth": growth_chart(private),
        "share": share_chart(share),
        "expectations": expectations_chart(sectors),
    }
    for name, value in charts.items():
        figures.write(out, name, value)
    date_readme(out, max(values[-1][0] for values in sectors.values()))
    latest = private[-1][0]
    streak = 0
    for _, y in reversed(private):
        if y < 10:
            break
        streak += 1
    result = {
        "latest_quarter": latest,
        "private_growth_pct": {x: round(y, 2) for x, y in private[-8:]},
        "public_growth_pct": {x: round(y, 2) for x, y in public[-8:]},
        "quarters_at_10_pct_or_more_running": streak,
        "beat_2026_q2_since_2010": highest_since(private, "2026-Q2"),
        "share_of_gdp_pct_4q_mean": {
            x: round(y, 2) for x, y in trailing_mean(share, 4)[-1:]
        },
        "share_of_gdp_pct_4q_mean_peak": max(
            ((x, round(y, 2)) for x, y in trailing_mean(share, 4)), key=lambda t: t[1]
        ),
        "expectations_latest": {
            SECTORS[code]: [values[-1][0], round(values[-1][1], 1)]
            for code, values in sectors.items()
        },
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    (out / "numbers.json").write_text(text, encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chart Peru's private investment.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    client = bcrp.BcrpClient()
    try:
        run(client, args.out)
    finally:
        client.close()
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
