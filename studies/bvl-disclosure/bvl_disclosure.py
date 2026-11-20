"""Do BVL prices and traded amounts move before a material event is filed?

Each event is measured against placebo days of the same stock with
`bvl.eventstudy`. The events are SMV material-event filings, grouped from the
API's rows with a coarse topic.

The SMV changed its list of event kinds over the years: 2010 labels carry no
number and later ones do (`14. DISTRIBUCIÓN ...`), and some were reworded.
A topic is found by keywords in the unaccented label, so both spellings land
in the same topic. A filing that reports several kinds gets every matching
topic.
"""

import re

from pathlib import Path
from typing import Any

import figures
import numpy as np
import pandas as pd

from bvl import eventstudy, issuers, panel, store, study
from bvl.study import SOURCE


# Quotes this long before the first event give it a full baseline.
QUOTES_FROM = "2008-01-01"
SEED = 20261114
# (measure, statistic, label) compared between events and placebo days.
MEASURES = (
    ("abs_car_pre5", "mean", "|abnormal return|, days -5 to -1"),
    ("abs_car_pre1", "mean", "|abnormal return|, day -1"),
    ("abs_car_event", "mean", "|abnormal return|, days 0 to 1"),
    ("signed_pre5", "mean", "days -5 to -1 return in the direction of days 0 to 1"),
    ("signed_pre1", "mean", "day -1 return in the direction of days 0 to 1"),
    ("log_volume_pre5", "mean", "log(1 + amount / baseline), days -5 to -1"),
    ("log_volume_event", "mean", "log(1 + amount / baseline), days 0 to 1"),
    ("traded_pre5", "mean", "share of days -5 to -1 with a trade"),
    ("traded_event", "mean", "share of days 0 to 1 with a trade"),
)
# Measures repeated per topic, period and decision-to-filing gap.
FOCUS = ("abs_car_event", "signed_pre5", "log_volume_pre5")
PERIODS = {"2010-14": (2010, 2014), "2015-19": (2015, 2019), "2020-26": (2020, 2026)}
GAPS = {
    "same day": (0, 0),
    "next day": (1, 1),
    "2 to 7 days": (2, 7),
    "8+ days": (8, 10_000),
}
PROFILE_SPAN = (-10, 10)
# A group with fewer events gets a count and no estimates.
MIN_EVENTS = 30
# Topic -> keywords. The first topic whose keyword appears in a label wins.
TOPICS: dict[str, tuple[str, ...]] = {
    "results": ("INFORMACION FINANCIERA", "ESTADOS FINANCIEROS", "MEMORIA ANUAL"),
    "dividends": ("UTILIDADES", "DIVIDENDO", "FECHA DE REGISTRO"),
    "capital": (
        "CAPITAL",
        "FUSION",
        "ESCISION",
        "REORGANIZACION",
        "ADQUISICION",
        "ENAJENACION",
        "INVERSION O DESINVERSION",
    ),
    "debt": ("COLOCACION DE VALORES", "CLASIFICACION DE RIESGO", "REP.DE OBLIG"),
    "legal": ("SANCIONADOR", "DEMANDA", "JUDICIAL"),
    "governance": (
        "DIRECTORES",
        "GERENTES",
        "JUNTA",
        "ESTATUTO",
        "AUDITORIA",
        "COMITE",
        "GRUPO ECONOMICO",
    ),
    "news": ("PRENSA", "MEDIOS", "ANALISTAS"),
    "other": ("OTRAS CIRCUNSTANCIAS", "OTROS"),
}


def topic(kind: str) -> str:
    """The topic of one event-kind label, or `unclassified`."""
    label = re.sub(r"^\d+\.\s*", "", issuers.ascii_upper(kind))
    for name, keywords in TOPICS.items():
        if any(keyword in label for keyword in keywords):
            return name
    return "unclassified"


def load(db: Path) -> pd.DataFrame:
    """One row per filing: ruc, company, filed_at, agreed_on and its topics."""
    rows = store.read(
        db, "SELECT filing, ruc, company, kind, agreed_on, filed_at FROM events"
    )
    rows["topic"] = rows["kind"].map(topic)
    filings = rows.groupby("filing").agg(
        ruc=("ruc", "first"),
        company=("company", "first"),
        filed_at=("filed_at", "first"),
        agreed_on=("agreed_on", "min"),
        topics=("topic", lambda t: frozenset(t)),
    )
    filings["filed_at"] = pd.to_datetime(filings["filed_at"])
    filings["agreed_on"] = pd.to_datetime(filings["agreed_on"])
    return filings.reset_index()


def run(db: Path, out: Path) -> dict[str, object]:
    rng = np.random.default_rng(SEED)
    quotes = panel.local_quotes(db)
    quotes = quotes[quotes["date"] >= QUOTES_FROM]
    grid = eventstudy.build_grid(quotes, panel.market_log_level(quotes))
    filings = load(db)
    sample, filing_days = event_sample(grid, quotes, filings)
    placebos = eventstudy.placebo_days(grid, sample, filing_days, rng)

    actual = with_signed(
        eventstudy.measure(grid, sample["column"].to_numpy(), sample["day0"].to_numpy())
    ).set_index(sample.index)
    placebo = with_signed(
        eventstudy.measure(
            grid, placebos["column"].to_numpy(), placebos["day0"].to_numpy()
        )
    ).set_index(pd.Index(placebos["event"]))
    clusters = sample["day0"]

    def compare(rows: pd.Index, measures: tuple[str, ...]) -> dict[str, Any]:
        kept = placebo[placebo.index.isin(rows)]
        result: dict[str, Any] = {"events": len(rows)}
        if len(rows) < MIN_EVENTS:
            return result
        for name, statistic, _ in MEASURES:
            if name not in measures:
                continue
            point, low, high = eventstudy.excess(
                actual.loc[rows, name], kept[name], clusters.loc[rows], statistic, rng
            )
            result[name] = {
                "events": round(_stat(actual.loc[rows, name], statistic), 5),
                "placebo": round(_stat(kept[name], statistic), 5),
                "excess": round(point, 5),
                "low": round(low, 5),
                "high": round(high, 5),
            }
        return result

    every = tuple(name for name, _, _ in MEASURES)
    overall = compare(sample.index, every)
    by_topic = {
        name: compare(
            sample.index[sample["topics"].map(lambda t, n=name: n in t)], FOCUS
        )
        for name in TOPICS
    }
    year = sample["filed_at"].dt.year
    by_period = {
        name: compare(sample.index[year.between(a, b)], FOCUS)
        for name, (a, b) in PERIODS.items()
    }
    gap = (sample["filed_at"].dt.normalize() - sample["agreed_on"]).dt.days
    by_gap = {
        name: compare(sample.index[gap.between(a, b)], FOCUS)
        for name, (a, b) in GAPS.items()
    }
    shares = gap_shares(gap, year)

    _figures(grid, sample, placebos, by_topic, shares, out)
    numbers: dict[str, object] = {
        "filings": len(filings),
        "filings_in_events": int(sample["filings"].sum()),
        "events": len(sample),
        "issuers": int(sample["ruc"].nunique()),
        "tickers": int(sample["ticker"].nunique()),
        "first_event": sample["filed_at"].min().date().isoformat(),
        "last_event": sample["filed_at"].max().date().isoformat(),
        "placebo_days": len(placebos),
        "measures": {name: label for name, _, label in MEASURES},
        "overall": overall,
        "by_topic": by_topic,
        "by_period": by_period,
        "by_gap": by_gap,
        "gap_shares_by_year": study.records(shares.round(3)),
    }
    study.write_numbers(out, numbers)
    return numbers


def event_sample(
    grid: eventstudy.Grid, quotes: pd.DataFrame, filings: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Clean events, one per stock and day 0, and every issuer filing day per ticker.

    Filings that share an issuer's day 0 merge into one event with every
    topic among them. A filing after the last market day is dropped.
    """
    names = quotes.sort_values("date", ascending=False).drop_duplicates(
        ["ticker", "name"]
    )[["ticker", "name"]]
    links = issuers.link(names, filings.drop_duplicates("ruc")[["ruc", "company"]])
    linked = filings.merge(links[["ticker", "ruc"]], on="ruc")
    linked["day0"] = eventstudy.day_zero(linked["filed_at"], grid.days)
    linked = linked[linked["day0"] < len(grid.days)]
    picked = eventstudy.most_traded(
        grid, linked.rename(columns={"filing": "event"})[["event", "ticker", "day0"]]
    ).rename(columns={"event": "filing"})
    chosen = filings.merge(picked, on="filing")
    filing_days = {
        str(ticker): np.unique(days.to_numpy())
        for ticker, days in linked.groupby("ticker")["day0"]
    }
    merged = chosen.groupby(["ticker", "day0"], as_index=False).agg(
        ruc=("ruc", "first"),
        column=("column", "first"),
        filed_at=("filed_at", "min"),
        agreed_on=("agreed_on", "min"),
        filings=("filing", "size"),
        topics=("topics", lambda t: frozenset().union(*t)),
    )
    return merged[eventstudy.clean(merged)].reset_index(drop=True), filing_days


def with_signed(measures: pd.DataFrame) -> pd.DataFrame:
    """Add |CAR|, pre-event returns signed by the day 0 to 1 reaction, and log volume.

    The amount ratio is zero on most days of a thin stock and very large on a
    few, so its log(1 + ratio) is averaged instead.

    A leak moves the price before the filing in the direction the filing then
    moves it, so the signed return is positive on average; on a placebo day it
    is the plain autocorrelation of returns.
    """
    direction = np.sign(measures["car_event"])
    return measures.assign(
        abs_car_pre5=measures["car_pre5"].abs(),
        abs_car_pre1=measures["car_pre1"].abs(),
        abs_car_event=measures["car_event"].abs(),
        signed_pre5=measures["car_pre5"] * direction,
        signed_pre1=measures["car_pre1"] * direction,
        log_volume_pre5=np.log1p(measures["volume_pre5"]),
        log_volume_event=np.log1p(measures["volume_event"]),
    )


def _stat(values: pd.Series, statistic: str) -> float:
    return float(values.median() if statistic == "median" else values.mean())


def gap_shares(gap: pd.Series, year: pd.Series) -> pd.DataFrame:
    """Per year, the share of events in each decision-to-filing gap."""
    known = gap.notna() & (gap >= 0)
    label = pd.Series(pd.NA, index=gap.index, dtype="object")
    for name, (a, b) in GAPS.items():
        label[gap.between(a, b)] = name
    table = pd.crosstab(year[known].rename("year"), label[known], normalize="index")
    return table.reindex(columns=list(GAPS), fill_value=0.0)


def _figures(
    grid: eventstudy.Grid,
    sample: pd.DataFrame,
    placebos: pd.DataFrame,
    by_topic: dict[str, dict[str, Any]],
    shares: pd.DataFrame,
    out: Path,
) -> None:
    source = SOURCE.removesuffix(".") + ", SMV material-event filings from 2010."
    day = figures.Axis("number", label="Day", decimals=0)
    event_returns, event_amount, event_traded = eventstudy.profile(
        grid, sample["column"].to_numpy(), sample["day0"].to_numpy(), PROFILE_SPAN
    )
    placebo_returns, placebo_amount, placebo_traded = eventstudy.profile(
        grid, placebos["column"].to_numpy(), placebos["day0"].to_numpy(), PROFILE_SPAN
    )
    offsets = pd.Index(range(PROFILE_SPAN[0], PROFILE_SPAN[1] + 1), name="day")
    figures.lines(
        out,
        "abs-return-profile",
        {
            "Filing": pd.Series(
                np.nanmean(np.abs(event_returns), axis=0) * 100, offsets
            ),
            "Placebo day": pd.Series(
                np.nanmean(np.abs(placebo_returns), axis=0) * 100, offsets
            ),
        },
        figures.Style(
            "Size of the daily abnormal move around a material-event filing",
            "Mean absolute abnormal return. Day 0 is the first market day on or"
            " after the filing date.",
            source,
            unit="%",
            decimals=2,
        ),
        day,
    )
    figures.lines(
        out,
        "traded-profile",
        {
            "Filing": pd.Series(np.nanmean(event_traded, axis=0) * 100, offsets),
            "Placebo day": pd.Series(np.nanmean(placebo_traded, axis=0) * 100, offsets),
        },
        figures.Style(
            "Share of stocks that trade on each day around a filing",
            "Percent of events with a trade",
            source,
            unit="%",
            decimals=1,
        ),
        day,
    )
    figures.lines(
        out,
        "amount-profile",
        {
            "Filing": pd.Series(np.nanmean(np.log1p(event_amount), axis=0), offsets),
            "Placebo day": pd.Series(
                np.nanmean(np.log1p(placebo_amount), axis=0), offsets
            ),
        },
        figures.Style(
            "Traded amount around a filing, against the stock's own baseline",
            "Mean log(1 + amount / baseline). The baseline is the mean daily"
            " amount over days -250 to -30.",
            source,
            decimals=2,
        ),
        day,
    )
    signed = {
        name: result["signed_pre5"]
        for name, result in by_topic.items()
        if isinstance(result.get("signed_pre5"), dict)
    }
    excess = pd.Series({t: v["excess"] * 100 for t, v in signed.items()})
    figures.bars(
        out,
        "pre-run-up-by-topic",
        excess,
        figures.Style(
            "Pre-filing move in the direction of the reaction, over placebo",
            "Excess signed return over days -5 to -1, with the 95% bootstrap"
            " interval clustered by day 0",
            source,
            unit="%",
            decimals=2,
        ),
        low=pd.Series({t: v["low"] * 100 for t, v in signed.items()}),
        high=pd.Series({t: v["high"] * 100 for t, v in signed.items()}),
    )
    figures.lines(
        out,
        "filing-gap",
        {name.capitalize(): shares[name] * 100 for name in ("same day", "next day")},
        figures.Style(
            "When the decision behind a filing was taken",
            "Percent of events by the gap from the agreement date to the filing date",
            source,
            unit="%",
            decimals=1,
        ),
        figures.Axis("year"),
    )


if __name__ == "__main__":
    study.main(run, Path(__file__).parent)
