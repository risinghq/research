"""How liquid the BVL has been since 1996, in measures that need no currency.

The API reports a traded amount without its currency, and BVL stocks trade in
soles or US dollars, so totals across stocks are not comparable. Each measure
here compares a stock only with itself or counts days and stocks:

- coverage: the share of market days a stock traded, between its first and
  last trade;
- active stocks: how many local stocks traded in a year;
- illiquidity: the Amihud ratio |return| / amount, averaged per stock and
  month. A currency multiplies a stock's ratio by a constant, so a stock fixed
  effect removes it; the yearly effects that remain trace the market.
"""

from pathlib import Path

import figures
import numpy as np
import pandas as pd

from bvl import panel, study
from bvl.study import SOURCE


# MSCI's review of Peru's Emerging Markets status, from its press releases.
MSCI_MARKS = {
    "2015-08-03": "MSCI consults on Frontier",
    "2015-09-30": "Peru kept, on review",
    "2016-06-14": "Peru stays Emerging",
}


def coverage_by_year(quotes: pd.DataFrame) -> pd.DataFrame:
    """Per year: active stocks, and the median and spread of their coverage."""
    days = panel.market_days(quotes)
    spans = quotes.groupby("ticker")["date"].agg(first="min", last="max")
    stock_years = (
        quotes.assign(year=quotes["date"].dt.year)
        .groupby(["ticker", "year"])
        .size()
        .rename("traded")
        .reset_index()
        .join(spans, on="ticker")
    )
    year = stock_years["year"].astype(str)
    lower = np.maximum(stock_years["first"], pd.to_datetime(year + "-01-01"))
    upper = np.minimum(stock_years["last"], pd.to_datetime(year + "-12-31"))
    possible = days.searchsorted(upper, side="right") - days.searchsorted(lower)
    stock_years["coverage"] = stock_years["traded"] / possible
    coverage = stock_years.groupby("year")["coverage"]
    return pd.DataFrame(
        {
            "stocks": coverage.size(),
            "median_coverage": coverage.median(),
            "daily_share": coverage.agg(lambda c: (c >= 0.8).mean()),
            "rare_share": coverage.agg(lambda c: (c < 0.2).mean()),
        }
    )


def time_effects(
    values: pd.Series, units: pd.Series, periods: pd.Series, iterations: int = 200
) -> pd.Series:
    """Period effects of `values` net of a unit effect, by alternating projections.

    Solves the two-way fixed effects model value = unit + period + error on an
    unbalanced panel. The effects are centred on their mean.
    """
    period_effect = pd.Series(0.0, index=pd.unique(periods))
    for _ in range(iterations):
        unit_effect = (values - periods.map(period_effect)).groupby(units).mean()
        updated = (values - units.map(unit_effect)).groupby(periods).mean()
        change = float((updated - period_effect.reindex(updated.index)).abs().max())
        period_effect = updated
        if change < 1e-10:
            break
    return (period_effect - period_effect.mean()).sort_index()


def illiquidity_by_year(amihud: pd.DataFrame) -> pd.Series:
    """Yearly log illiquidity relative to the mean year, net of stock effects."""
    years = amihud["month"].dt.year.rename("year")
    return time_effects(np.log(amihud["amihud"]), amihud["ticker"], years)


def msci_shift(monthly: pd.Series) -> dict[str, float]:
    """Mean monthly illiquidity in the year before the consultation and after."""
    before = monthly.loc["2014-08":"2015-07"].mean()
    during = monthly.loc["2015-08":"2016-06"].mean()
    after = monthly.loc["2016-07":"2017-06"].mean()
    return {
        "before_2014_08_to_2015_07": round(float(before), 3),
        "review_2015_08_to_2016_06": round(float(during), 3),
        "after_2016_07_to_2017_06": round(float(after), 3),
    }


def run(db: Path, out: Path) -> dict[str, object]:
    quotes = panel.local_quotes(db)
    coverage = coverage_by_year(quotes)
    amihud = panel.monthly_amihud(quotes)
    yearly = illiquidity_by_year(amihud)
    monthly = time_effects(np.log(amihud["amihud"]), amihud["ticker"], amihud["month"])
    monthly.index = pd.PeriodIndex(monthly.index).to_timestamp()
    complete = coverage.loc[coverage.index < pd.Timestamp.today().year]

    year, month = figures.Axis("year"), figures.Axis("month")
    figures.lines(
        out,
        "active-stocks",
        {"Local stocks that traded": complete["stocks"]},
        figures.Style(
            "Local stocks with at least one trade, per year",
            "Stocks",
            SOURCE,
            unit="stocks",
        ),
        year,
    )
    figures.lines(
        out,
        "coverage",
        {
            "Traded on 80% or more of days": complete["daily_share"] * 100,
            "Traded on under 20% of days": complete["rare_share"] * 100,
        },
        figures.Style(
            "How often a listed local stock trades",
            "Percent of active stocks. Coverage counts the days between a stock's"
            " first and last trade.",
            SOURCE,
            unit="%",
            decimals=1,
        ),
        year,
    )
    illiquidity = (
        "Log illiquidity against the mean month. Higher means the same amount"
        " traded moves the price more."
    )
    figures.lines(
        out,
        "illiquidity",
        {
            "Monthly": monthly,
            "12-month mean": monthly.rolling(12, min_periods=6).mean(),
        },
        figures.Style(
            "Price impact of trading (Amihud), net of each stock's own level",
            illiquidity,
            SOURCE,
            decimals=2,
        ),
        month,
        span=("2015-08-03", "2016-06-14", "MSCI review"),
    )

    window = monthly.loc["2014-01":"2017-12"]
    figures.lines(
        out,
        "illiquidity-msci",
        {"Monthly": window},
        figures.Style(
            "Illiquidity around MSCI's 2015-16 review of Peru",
            illiquidity,
            SOURCE,
            decimals=2,
        ),
        month,
        marks=MSCI_MARKS,
    )

    numbers: dict[str, object] = {
        "first_day": quotes["date"].min().date().isoformat(),
        "last_day": quotes["date"].max().date().isoformat(),
        "local_tickers": int(quotes["ticker"].nunique()),
        "stock_months": len(amihud),
        "coverage_by_year": study.records(complete.round(3)),
        "illiquidity_by_year": study.records(yearly.round(3).rename("effect")),
        "msci": msci_shift(monthly),
    }
    study.write_numbers(out, numbers)
    return numbers


if __name__ == "__main__":
    study.main(run, Path(__file__).parent)
