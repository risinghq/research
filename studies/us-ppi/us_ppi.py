"""The year-over-year change in the U.S. Producer Price Index for final demand,
rebuilt from the BLS series that Axios charted on 2026-11-13.

The change in a month is the seasonally adjusted index over the same month a
year before, in percent, as Axios computed it from FRED's copy of the series.
BLS marks the last four months preliminary and revises them, and it revises
the seasonal factors of the last five years each February.
"""

import argparse
import os
import sys

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import bls
import replication


if TYPE_CHECKING:
    from collections.abc import Sequence

OUT = Path(__file__).parent
# The final demand index starts in November 2009.
FIRST_YEAR = 2009
CHART = replication.Chart(
    name="ppi",
    kind="line",
    title="Year-over-year change in the Producer Price Index",
    subtitle="Monthly, seasonally adjusted, final demand",
    unit="%",
    decimals=1,
    source="BLS, Producer Price Index, series WPSFD4.",
    ylabel="Percent change from a year before",
)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    found = client.series([bls.PPI], FIRST_YEAR, today.year)[bls.PPI]
    points = replication.changes(
        replication.levels(found),
        12,
        lambda now, before: round((now / before - 1) * 100, 5),
    )
    return replication.publish(out, CHART, points, replication.read_original(OUT))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the PPI chart.")
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
