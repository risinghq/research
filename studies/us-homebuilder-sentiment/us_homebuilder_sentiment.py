"""The NAHB/Wells Fargo Housing Market Index, rebuilt from NAHB's history table
that Axios charted on 2026-11-18.

The index is seasonally adjusted, and NAHB revises past months when it
re-estimates the seasonal factors.
"""

import argparse
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import nahb
import replication


if TYPE_CHECKING:
    from collections.abc import Sequence

OUT = Path(__file__).parent
CHART = replication.Chart(
    name="hmi",
    kind="line",
    title="U.S. homebuilder sentiment index",
    subtitle="Monthly survey of single-family homebuilders, seasonally adjusted",
    unit="",
    decimals=0,
    source="NAHB/Wells Fargo Housing Market Index, used with permission.",
)


def run(client: nahb.NahbClient, out: Path) -> dict[str, object]:
    points = replication.levels(client.history())
    return replication.publish(out, CHART, points, replication.read_original(OUT))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild the homebuilder chart.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    client = nahb.NahbClient()
    try:
        run(client, args.out)
    finally:
        client.close()
    sys.stdout.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
