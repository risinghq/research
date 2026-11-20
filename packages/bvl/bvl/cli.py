"""The `bvl` command: fill the panel from the SMV and BCRP APIs."""

import argparse
import logging

from contextlib import closing
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import bcrp
import smv

from bvl import fetch, store, study


if TYPE_CHECKING:
    from collections.abc import Sequence

DEFAULT_CACHE = Path.home() / ".cache" / "bvl" / "smv"
# Datasets the SMV answers one market day per request: table and fill.
DAILY_FILLS = {
    "indices": ("index_levels", fetch.fill_index_levels),
    "brokers": ("broker_amounts", fetch.fill_broker_amounts),
}
# The first day each API query answers.
QUOTES_START = date(1996, 1, 1)
EVENTS_START = date(2010, 1, 1)
STATEMENTS_START = date(2002, 1, 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bvl", description="Lima Stock Exchange data from the SMV open API."
    )
    parser.add_argument("--db", type=Path, default=study.DEFAULT_DB)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("-v", "--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    fill = commands.add_parser("fetch", help="fill the panel from the SMV or BCRP API")
    fill.add_argument(
        "dataset",
        choices=["quotes", "events", "statements", "holders", *DAILY_FILLS, "bcrp"],
    )
    fill.add_argument("--start", type=date.fromisoformat)
    fill.add_argument("--end", type=date.fromisoformat, default=date.today())
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(message)s",
    )
    _fetch(args)


def _fetch(args: argparse.Namespace) -> None:
    if args.dataset == "bcrp":
        _fetch_bcrp(args)
        return
    today = date.today()
    client = smv.SmvClient(args.cache)
    with closing(store.connect(args.db)) as connection:
        if args.dataset == "quotes":
            start = args.start or QUOTES_START
            fetch.fill_quotes(client, connection, start, args.end, today)
        elif args.dataset == "events":
            start = args.start or EVENTS_START
            fetch.fill_events(client, connection, start, args.end, today)
        elif args.dataset == "statements":
            start = args.start or STATEMENTS_START
            fetch.fill_statements(client, connection, start, args.end, today)
        elif args.dataset == "holders":
            fetch.fill_holders(client, connection, today)
        else:
            table, fill = DAILY_FILLS[args.dataset]
            days = [
                date.fromisoformat(d) for d in fetch.missing_days(connection, table)
            ]
            if args.start is not None:
                days = [d for d in days if d >= args.start]
            fill(client, connection, days, today)
    client.close()


def _fetch_bcrp(args: argparse.Namespace) -> None:
    client = bcrp.BcrpClient()
    with closing(store.connect(args.db)) as connection:
        fetch.fill_bcrp(client, connection, args.start or QUOTES_START, args.end)
    client.close()
