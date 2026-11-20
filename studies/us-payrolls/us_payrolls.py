"""The monthly change in U.S. nonfarm payrolls, rebuilt from the BLS series that
Axios charted on 2026-11-06.

The change in a month is the seasonally adjusted level less the month before,
in jobs; BLS publishes the level in thousands. Each jobs report revises the
two months before it, and the annual benchmark in February revises years, so
a rerun can differ from the post in months it already showed.
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
    name="payrolls",
    kind="columns",
    title="Change in U.S. nonfarm payrolls",
    subtitle="Monthly, seasonally adjusted",
    unit="jobs",
    decimals=0,
    source="BLS, Current Employment Statistics, series CES0000000001.",
    ylabel="Thousands of jobs",
    scale=1000,
)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    # December of the year before gives the first year's January change.
    found = client.series([bls.PAYROLLS], FIRST_YEAR - 1, today.year)[bls.PAYROLLS]
    jobs = replication.changes(
        replication.levels(found), 1, lambda now, before: round((now - before) * 1000)
    )
    points = [p for p in jobs if p.period >= f"{FIRST_YEAR}-01"]
    return replication.publish(out, CHART, points, replication.read_original(OUT))


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
