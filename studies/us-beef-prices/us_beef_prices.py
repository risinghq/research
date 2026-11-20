"""The average U.S. price of a pound of ground beef, rebuilt from the BLS series
that Axios charted on 2026-11-07.

BLS publishes the average price itself, not seasonally adjusted, and does not
revise it. It collected no prices in October 2025, a lapse in
appropriations, so that month has no value.
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
# The series starts in January 1984.
FIRST_YEAR = 1984
CHART = replication.Chart(
    name="beef",
    kind="line",
    title="Ground beef price per pound",
    subtitle="Monthly, 100% beef, U.S. city average",
    unit="$",
    decimals=2,
    source="BLS, Average Price Data, series APU0000703112.",
)


def run(client: bls.BlsClient, out: Path, today: date) -> dict[str, object]:
    found = client.series([bls.GROUND_BEEF], FIRST_YEAR, today.year)
    points = replication.levels(found[bls.GROUND_BEEF])
    return replication.publish(out, CHART, points, replication.read_original(OUT))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the ground beef chart.")
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
