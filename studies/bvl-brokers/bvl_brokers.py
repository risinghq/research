"""Market shares and concentration of the BVL's brokerage firms (SABs).

The SMV reports each firm's bought and sold amounts for a day. A firm's share
is its bought plus sold amount over the day's total of both sides, so a firm
on both sides of a trade counts twice. The API's own percentages are not used:
on some days they sum to less than 100.

Concentration is the Herfindahl-Hirschman index (HHI), the sum of squared
shares in percent, from 0 to 10,000. A year's HHI uses the firm's share of the
year's total amount; the daily HHI uses each day's shares.
"""

from pathlib import Path

import figures
import numpy as np
import pandas as pd

from bvl import store, study


# A year enters the figures once the firms' bought amount, and every later
# year's, reaches this share of the quotes' traded amount.
COVERAGE = 0.9


def amounts(db: Path) -> pd.DataFrame:
    """One row per firm and day with a positive amount: date, broker, name, total."""
    rows = store.read(
        db,
        "SELECT date, broker, name, bought + sold AS total FROM broker_amounts "
        "WHERE bought + sold > 0 ORDER BY date, broker",
    )
    rows["date"] = pd.to_datetime(rows["date"])
    return rows


def coverage(db: Path) -> pd.Series:
    """Each year's bought amount over the quotes' traded amount.

    Before 2010 the brokers' amounts cover well under the quotes' total, so
    some firms of those years are missing from the API.
    """
    years = store.read(
        db,
        "SELECT b.year, b.bought / q.amount AS coverage FROM "
        "(SELECT substr(date, 1, 4) AS year, sum(bought) AS bought "
        "FROM broker_amounts GROUP BY 1) AS b JOIN "
        "(SELECT substr(date, 1, 4) AS year, sum(amount) AS amount "
        "FROM quotes GROUP BY 1) AS q USING (year)",
    )
    return years.set_index(years["year"].astype(int))["coverage"].rename_axis("year")


def latest_names(rows: pd.DataFrame) -> pd.Series:
    """Each broker code's name on the last day it traded.

    The API gives a code the same name on every day, today's.
    """
    return rows.groupby("broker")["name"].last()


def hhi(shares: pd.Series) -> float:
    """HHI of shares that sum to 1, on the 0 to 10,000 scale."""
    return float(((shares * 100) ** 2).sum())


def yearly_shares(rows: pd.DataFrame) -> pd.DataFrame:
    """Share of each firm (columns) in each year's total amount (rows)."""
    totals = rows.pivot_table(
        index=rows["date"].dt.year, columns="broker", values="total", aggfunc="sum"
    ).fillna(0.0)
    totals.index.name = "year"
    return totals.div(totals.sum(axis=1), axis=0)


def daily_hhi(rows: pd.DataFrame) -> pd.Series:
    """The HHI of each day's shares."""
    shares = rows["total"] / rows.groupby("date")["total"].transform("sum")
    return ((shares * 100) ** 2).groupby(rows["date"]).sum().rename("hhi")


def concentration_by_year(rows: pd.DataFrame) -> pd.DataFrame:
    """Per year: market days, active firms, HHI, median daily HHI, top-1 and top-3 shares."""
    shares = yearly_shares(rows)
    daily = daily_hhi(rows)
    ranked = -np.sort(-shares.to_numpy(), axis=1)
    return pd.DataFrame(
        {
            "days": rows.groupby(rows["date"].dt.year)["date"].nunique(),
            "firms": (shares > 0).sum(axis=1),
            "hhi": shares.apply(hhi, axis=1),
            "daily_hhi": daily.groupby(pd.DatetimeIndex(daily.index).year).median(),
            "top1": pd.Series(ranked[:, 0], index=shares.index),
            "top3": pd.Series(ranked[:, :3].sum(axis=1), index=shares.index),
        }
    ).rename_axis("year")


def run(db: Path, out: Path) -> dict[str, object]:
    rows = amounts(db)
    names = latest_names(rows)
    by_year = concentration_by_year(rows).join(coverage(db))
    by_year["leader"] = yearly_shares(rows).idxmax(axis=1)
    short = by_year["coverage"] < COVERAGE
    first = (
        int(by_year.index[short].max()) + 1 if short.any() else int(by_year.index[0])
    )
    shown = by_year.loc[first:]
    shares = yearly_shares(rows).loc[first:]
    note = study.SOURCE.replace("BVL daily quotes", "amounts traded by each SAB")
    last_year = int(shares.index.max())

    figures.lines(
        {"yearly shares": shown["hhi"], "median day": shown["daily_hhi"]},
        out / "hhi.png",
        title="Concentration of BVL brokerage, Herfindahl-Hirschman index",
        ylabel="HHI, 0 to 10,000",
        note=note + f" {last_year} is partial.",
    )
    figures.lines(
        {"largest firm": shown["top1"] * 100, "three largest": shown["top3"] * 100},
        out / "top-shares.png",
        title="Share of the amount traded through the largest firms",
        ylabel="% of bought plus sold",
        note=note + " Each year's ranking.",
    )
    figures.lines(
        {"firms": shown["firms"]},
        out / "firms.png",
        title="Brokerage firms with any amount traded in the year",
        ylabel="firms",
        note=note,
    )
    leaders = shares.iloc[-1].nlargest(3)
    figures.lines(
        {f"{names[code]} ({code})": shares[code] * 100 for code in leaders.index},
        out / "leaders.png",
        title=f"Yearly share of the three largest firms in {last_year}",
        ylabel="% of bought plus sold",
        note=note,
    )

    numbers: dict[str, object] = {
        "first_day": rows["date"].min().date().isoformat(),
        "last_day": rows["date"].max().date().isoformat(),
        "market_days": int(rows["date"].nunique()),
        "firms_ever": int(rows["broker"].nunique()),
        "coverage_threshold": COVERAGE,
        "first_covered_year": first,
        "by_year": study.records(by_year.round(4)),
        "shares": {
            str(year): [
                {"broker": code, "name": names[str(code)], "share": round(float(s), 4)}
                for code, s in year_shares[year_shares > 0]
                .sort_values()
                .iloc[::-1]
                .items()
            ]
            for year, year_shares in shares.iterrows()
        },
    }
    study.write_numbers(out, numbers)
    return numbers


if __name__ == "__main__":
    study.main(run, Path(__file__).parent)
