"""When BVL issuers file their quarterly statements, and how prices take the news.

The limits come from article 7 of Resolución CONASEV 103-99-EF/94.10 as
amended by Resolución SMV 013-2014-SMV/01, in force from 1 July 2014: 30 days
after the quarter for individual statements and 45 for consolidated ones, 45
and 60 days for the fourth quarter. The SMV's own calendars read the first two
counts as months: a 30-day limit is the last day of the month after the
quarter and a 45-day one the 15th of the second month. The 60-day limit is 60
calendar days, 1 March or 29 February in a leap year. A limit on a closed day
moves to the next business day.

Earnings news is the change in quarterly net income from the same quarter a
year before, over the year-earlier total assets. It needs no forecast, which
the BVL lacks for most issuers, but it also counts a change the market
expected as news.
"""

from pathlib import Path
from typing import Any

import figures
import numpy as np
import pandas as pd

from bvl import eventstudy, issuers, panel, store, study


STATEMENTS_SOURCE = "Source: SMV open data API, quarterly statements."
EVENTS_SOURCE = "Source: SMV open data API, quarterly statements and BVL quotes."
SEED = 20261114
# How far before and after the filing the reaction profile runs, in market days.
SPAN = (-5, 60)
WINDOWS = {"pre": (-5, -1), "reaction": (0, 1), "drift": (2, 60)}
PERIODS = {
    "2002-09": (2002, 2009),
    "2010-14": (2010, 2014),
    "2015-19": (2015, 2019),
    "2020-26": (2020, 2026),
}
# Days from the due day shown in the filing-day histogram.
DUE_OFFSETS = range(-20, 11)
# A group with fewer events gets a count and no estimates.
MIN_EVENTS = 30
RULE_FROM = pd.Timestamp("2014-07-01")
ISSUER = "EMPRESAS EMISORAS"

# Peru's national holidays as (month, day, first year). Holy Thursday and Good
# Friday are left out: they fall by 23 April at the latest, never near a limit.
HOLIDAYS = [
    (1, 1, 0), (5, 1, 0), (6, 7, 2022), (6, 29, 0), (7, 23, 2024), (7, 28, 0),
    (7, 29, 0), (8, 6, 2024), (8, 30, 0), (10, 8, 0), (11, 1, 0), (12, 8, 0),
    (12, 9, 2024), (12, 25, 0),
]  # fmt: skip

# Public-sector non-working days that moved a filing limit: DS 019-2011-PCM,
# DS 002-2019-PCM and DS 033-2022-PCM. DS 161-2021-PCM also closed 2 November
# 2021, but the SMV's 2021 calendar kept that day as a limit, so it stays open.
CLOSED = pd.to_datetime(["2011-05-02", "2011-10-31", "2019-10-31", "2022-10-31"])


def load(db: Path) -> pd.DataFrame:
    rows = store.read(db, "SELECT * FROM statements WHERE filed_on IS NOT NULL")
    rows["filed_on"] = pd.to_datetime(rows["filed_on"])
    first = pd.to_datetime(
        pd.DataFrame({"year": rows["year"], "month": rows["quarter"] * 3, "day": 1})
    )
    rows["quarter_end"] = first + pd.offsets.MonthEnd(0)
    rows["consolidated"] = rows["consolidated"].astype(bool)
    return rows


def limit(
    quarter_end: pd.Timestamp, *, fourth: bool, consolidated: bool
) -> pd.Timestamp:
    """The calendar limit for one statement, before a closed day moves it."""
    if consolidated and fourth:
        return quarter_end + pd.Timedelta(days=60)
    if consolidated or fourth:
        return (quarter_end + pd.offsets.MonthBegin(2)).replace(day=15)
    return quarter_end + pd.offsets.MonthEnd(1)


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Weekdays from `start` to `end` that are neither a holiday nor CLOSED."""
    days = pd.bdate_range(start, end)
    holiday = pd.Series(
        [(day.month, day.day) for day in days], index=days, dtype=object
    ).map(
        {(month, day): first for month, day, first in HOLIDAYS},
    )
    closed = (holiday <= days.year).to_numpy() | days.isin(CLOSED)
    return days[~closed]


def due(statements: pd.DataFrame) -> pd.Series:
    """Each statement's limit moved to the first business day on or after it."""
    limits = pd.DatetimeIndex(
        [
            limit(end, fourth=quarter == 4, consolidated=consolidated)
            for end, quarter, consolidated in zip(
                statements["quarter_end"],
                statements["quarter"],
                statements["consolidated"],
                strict=True,
            )
        ]
    )
    days = business_days(limits.min(), limits.max() + pd.Timedelta(days=14))
    return pd.Series(days[days.searchsorted(limits)], index=statements.index)


def timing(statements: pd.DataFrame) -> pd.DataFrame:
    """Add each statement's lag in days, its due day and whether it beat it."""
    due_on = due(statements)
    return statements.assign(
        lag=(statements["filed_on"] - statements["quarter_end"]).dt.days,
        due_on=due_on,
        on_due_day=statements["filed_on"] == due_on,
        late=statements["filed_on"] > due_on,
    )


def news(statements: pd.DataFrame) -> pd.Series:
    """Change in net income from the same quarter a year before, over its assets.

    A filer that changed its reporting currency in between gets no value, and
    neither does one with no positive year-earlier assets.
    """
    keys = ["rpj", "consolidated", "quarter"]
    earlier = statements[[*keys, "year", "currency", "net_income", "assets"]].copy()
    earlier["year"] += 1
    paired = statements[[*keys, "year", "currency", "net_income"]].merge(
        earlier, on=[*keys, "year"], how="left", suffixes=("", "_before")
    )
    usable = (paired["currency"] == paired["currency_before"]) & (paired["assets"] > 0)
    change = (paired["net_income"] - paired["net_income_before"]) / paired["assets"]
    return pd.Series(np.where(usable, change, np.nan), index=statements.index)


def car(
    grid: eventstudy.Grid, columns: np.ndarray, day0: np.ndarray, span: tuple[int, int]
) -> np.ndarray:
    """Cumulative abnormal return over `span`, NaN for an event that cannot be
    measured. A day whose price is unknown adds nothing."""
    returns, _, _ = eventstudy.profile(grid, columns, day0, span)
    measured = ~np.isnan(returns).all(axis=1)
    return np.where(measured, np.nansum(returns, axis=1), np.nan)


def run(db: Path, out: Path) -> dict[str, object]:
    rng = np.random.default_rng(SEED)
    quotes = panel.local_quotes(db)
    days = panel.market_days(quotes)
    statements = load(db)
    links = statement_links(quotes, statements)
    statements["traded_share"] = statements["ruc"].isin(links["ruc"])
    # A quarter counts once every limit has passed in the panel.
    complete = statements["quarter_end"] + pd.offsets.MonthEnd(3) < days[-1]
    timed = timing(statements[complete])
    individual = timed[~timed["consolidated"] & (timed["company_type"] == ISSUER)]

    by_quarter = timing_by_quarter(individual)
    ruled = individual[individual["filed_on"] >= RULE_FROM]
    offsets = (ruled["filed_on"] - ruled["due_on"]).dt.days
    shares = offsets.value_counts(normalize=True).reindex(DUE_OFFSETS, fill_value=0.0)
    by_traded = {
        "traded share": timing_summary(ruled[ruled["traded_share"]]),
        "no traded share": timing_summary(ruled[~ruled["traded_share"]]),
    }

    grid = eventstudy.build_grid(quotes, panel.market_log_level(quotes))
    sample = event_sample(grid, statements, links)
    reaction = reactions(sample, rng)
    _figures(grid, by_quarter, shares, sample, out)

    numbers: dict[str, object] = {
        "statements": len(statements),
        "filers": int(statements["rpj"].nunique()),
        "first_quarter": str(statements["quarter_end"].min().to_period("Q")),
        "last_quarter": str(timed["quarter_end"].max().to_period("Q")),
        "issuer_statements": len(individual),
        "issuers": int(individual["rpj"].nunique()),
        "rule_from": RULE_FROM.date().isoformat(),
        "since_rule": timing_summary(ruled),
        "since_rule_by_traded": by_traded,
        "by_quarter": study.records(
            by_quarter.round(3)
            .set_axis(pd.DatetimeIndex(by_quarter.index).to_period("Q").astype(str))
            .rename_axis("quarter")
        ),
        "filed_vs_due_day": {str(k): round(float(v), 4) for k, v in shares.items()},
        "events": len(sample),
        "event_issuers": int(sample["ruc"].nunique()),
        "event_tickers": int(sample["ticker"].nunique()),
        "first_event": sample["filed_on"].min().date().isoformat(),
        "last_event": sample["filed_on"].max().date().isoformat(),
        "windows": {k: list(v) for k, v in WINDOWS.items()},
        "reaction": reaction,
    }
    study.write_numbers(out, numbers)
    return numbers


def statement_links(quotes: pd.DataFrame, statements: pd.DataFrame) -> pd.DataFrame:
    names = quotes.sort_values("date", ascending=False).drop_duplicates(
        ["ticker", "name"]
    )[["ticker", "name"]]
    filers = statements.sort_values("filed_on", ascending=False).drop_duplicates("ruc")
    return issuers.link(names, filers[["ruc", "company"]])


def timing_summary(rows: pd.DataFrame) -> dict[str, object]:
    return {
        "statements": len(rows),
        "median_lag": float(rows["lag"].median()),
        "on_due_day": round(float(rows["on_due_day"].mean()), 4),
        "late": round(float(rows["late"].mean()), 4),
        "late_over_30_days": round(
            float((rows["filed_on"] - rows["due_on"]).dt.days.gt(30).mean()), 4
        ),
    }


def timing_by_quarter(rows: pd.DataFrame) -> pd.DataFrame:
    """Per fiscal quarter: statements, median lag and the share on and after the due day."""
    grouped = rows.groupby("quarter_end")
    return pd.DataFrame(
        {
            "statements": grouped.size(),
            "median_lag": grouped["lag"].median(),
            "on_due_day": grouped["on_due_day"].mean(),
            "late": grouped["late"].mean(),
        }
    )


def event_sample(
    grid: eventstudy.Grid, statements: pd.DataFrame, links: pd.DataFrame
) -> pd.DataFrame:
    """Individual statements of share issuers with earnings news, on their busiest
    ticker, each with its day 0 and cumulative abnormal return in every window."""
    individual = statements[~statements["consolidated"]].reset_index(drop=True)
    individual["news"] = news(individual)
    rows = individual.dropna(subset=["news"]).merge(links[["ticker", "ruc"]], on="ruc")
    rows["day0"] = eventstudy.day_zero(rows["filed_on"], grid.days)
    rows = rows[rows["day0"] < len(grid.days)]
    rows["event"] = rows["rpj"] + " " + rows["quarter_end"].dt.date.astype(str)
    picked = eventstudy.most_traded(grid, rows[["event", "ticker", "day0"]])
    sample = (
        rows.drop(columns=["ticker"])
        .drop_duplicates("event")
        .merge(picked[["event", "ticker", "column"]], on="event")
    )
    for name, span in WINDOWS.items():
        sample[f"car_{name}"] = car(
            grid, sample["column"].to_numpy(), sample["day0"].to_numpy(), span
        )
    sample = sample.dropna(subset=["car_reaction"]).reset_index(drop=True)
    sample["tercile"] = pd.qcut(sample["news"], 3, labels=["bad", "middle", "good"])
    return sample


def reactions(sample: pd.DataFrame, rng: np.random.Generator) -> dict[str, object]:
    """Mean CAR of good-news less bad-news events in each window, by tercile and
    by sign, with a bootstrap that resamples day 0."""

    def gap(rows: pd.DataFrame, good: pd.Series, bad: pd.Series) -> dict[str, Any]:
        result: dict[str, Any] = {"good": int(good.sum()), "bad": int(bad.sum())}
        if min(good.sum(), bad.sum()) < MIN_EVENTS:
            return result
        for name in WINDOWS:
            column = rows[f"car_{name}"]
            point, low, high = eventstudy.excess(
                column[good], column[bad], rows["day0"], "mean", rng
            )
            result[name] = {
                "good": round(float(column[good].mean()), 5),
                "bad": round(float(column[bad].mean()), 5),
                "difference": round(point, 5),
                "low": round(low, 5),
                "high": round(high, 5),
            }
        return result

    def split(rows: pd.DataFrame) -> dict[str, Any]:
        return {
            "terciles": gap(rows, rows["tercile"] == "good", rows["tercile"] == "bad"),
            "sign": gap(rows, rows["news"] > 0, rows["news"] < 0),
        }

    year = sample["filed_on"].dt.year
    return {
        "overall": split(sample),
        "by_period": {
            name: split(sample[year.between(a, b)]) for name, (a, b) in PERIODS.items()
        },
    }


def _figures(
    grid: eventstudy.Grid,
    by_quarter: pd.DataFrame,
    shares: pd.Series,
    sample: pd.DataFrame,
    out: Path,
) -> None:
    note = STATEMENTS_SOURCE + " Individual statements of issuers."
    rule = {RULE_FROM.date().isoformat(): "SMV 013-2014 in force"}
    figures.lines(
        {"median days after quarter end": by_quarter["median_lag"]},
        out / "lag.png",
        title="How long issuers take to file a quarterly statement",
        ylabel="days",
        note=note + " One point per fiscal quarter, by quarter end.",
        marks=rule,
    )
    figures.lines(
        {
            "filed on the due day": by_quarter["on_due_day"] * 100,
            "filed after it": by_quarter["late"] * 100,
        },
        out / "due-day.png",
        title="Share of statements filed on the due day and after it",
        ylabel="% of statements",
        note=note + " Due day: the SMV limit moved past closed days.",
        marks=rule,
    )
    figures.bars(
        shares * 100,
        out / "filing-day.png",
        title="Filing day against the due day, since July 2014",
        ylabel="% of statements",
        note=note + " 0 is the due day.",
    )
    returns, _, _ = eventstudy.profile(
        grid, sample["column"].to_numpy(), sample["day0"].to_numpy(), SPAN
    )
    offsets = pd.Index(range(SPAN[0], SPAN[1] + 1), name="day")
    figures.lines(
        {
            f"{name} news": pd.Series(
                np.nancumsum(
                    np.nanmean(returns[(sample["tercile"] == name).to_numpy()], axis=0)
                )
                * 100,
                offsets,
            )
            for name in ("good", "middle", "bad")
        },
        out / "drift.png",
        title="Mean cumulative abnormal return around a quarterly filing",
        ylabel="cumulative %, from the close of day -6",
        note=EVENTS_SOURCE + " Terciles of the change in net income from a year"
        " before, over assets.",
    )


if __name__ == "__main__":
    study.main(run, Path(__file__).parent)
