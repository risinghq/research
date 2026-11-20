"""The quarterly change in U.S. labor productivity, rebuilt from the BLS series
that Axios charted on 2026-11-05.

BLS publishes the change itself: output per hour in the nonfarm business
sector against the quarter before, at an annual rate. Each release revises
earlier quarters, so a rerun can differ from the post in quarters it already
showed.
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
    name="productivity",
    kind="columns",
    title="Change in U.S. output per hour of labor",
    subtitle="Quarterly, annual rate, nonfarm business sector",
    unit="%",
    decimals=1,
    source="BLS, Productivity and Costs, series PRS85006092.",
    ylabel="Percent change at an annual rate",
)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    found = client.series([bls.PRODUCTIVITY], FIRST_YEAR, today.year)
    points = replication.levels(found[bls.PRODUCTIVITY], quarterly=True)
    return replication.publish(out, CHART, points, replication.read_original(OUT))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the productivity chart.")
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
