"""The monthly change in the U.S. Consumer Price Index, rebuilt from the BLS
series that Axios charted on 2026-11-10.

The change in a month is the seasonally adjusted index over the month before,
in percent. BLS revises the seasonal factors of the last five years each
February, so a rerun can differ from the post in months it already showed.
BLS collected no prices in October 2025, a lapse in appropriations, so October
and November 2025 have no monthly change.
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
FIRST_YEAR = 2000
CHART = replication.Chart(
    name="cpi",
    kind="columns",
    title="Change in the Consumer Price Index",
    subtitle="Monthly, seasonally adjusted, all items",
    unit="%",
    decimals=1,
    source="BLS, Consumer Price Index, series CUSR0000SA0.",
    ylabel="Percent change from the month before",
)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    # December of the year before gives the first year's January change.
    found = client.series([bls.CPI], FIRST_YEAR - 1, today.year)[bls.CPI]
    monthly = replication.changes(
        replication.levels(found),
        1,
        lambda now, before: round((now / before - 1) * 100, 5),
    )
    points = [p for p in monthly if p.period >= f"{FIRST_YEAR}-01"]
    return replication.publish(out, CHART, points, replication.read_original(OUT))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the CPI chart.")
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
