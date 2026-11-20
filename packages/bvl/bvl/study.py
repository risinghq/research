"""The command line and the numbers file that every BVL study shares.

A study's README cites its `numbers.json`, so a rerun on a newer panel updates
the evidence and leaves the prose to be checked against it.
"""

import argparse
import json
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

DEFAULT_DB = Path("data/bvl.sqlite")
SOURCE = "Source: SMV open data API (mvnet.smv.gob.pe), BVL daily quotes."


def records(frame: pd.DataFrame | pd.Series) -> list[dict[str, object]]:
    table = frame.to_frame() if isinstance(frame, pd.Series) else frame
    rows: list[dict[str, object]] = json.loads(
        table.reset_index().to_json(orient="records")
    )
    return rows


def write_numbers(out: Path, numbers: dict[str, object]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(numbers, indent=2, ensure_ascii=False) + "\n"
    (out / "numbers.json").write_text(text, encoding="utf-8")


def main(
    run: Callable[[Path, Path], object],
    out: Path,
    argv: Sequence[str] | None = None,
) -> None:
    """Run a study on the panel and write its outputs to `out` unless told otherwise."""
    parser = argparse.ArgumentParser(description="Run a study on the filled panel.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=out)
    args = parser.parse_args(argv)
    run(args.db, args.out)
    sys.stdout.write(f"wrote {args.out}\n")
