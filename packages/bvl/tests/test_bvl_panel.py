import numpy as np
import pandas as pd
import pytest

from bvl import panel


def test_market_level_skips_a_return_that_spans_a_missed_market_day() -> None:
    d = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    quotes = pd.DataFrame(
        {
            "date": [d[0], d[1], d[2], d[2]],
            "prev_date": [pd.NaT, d[0], d[1], d[0]],
            "log_return": [np.nan, 0.01, 0.02, 0.5],
        }
    )

    level = panel.market_log_level(quotes)

    assert level.to_numpy() == pytest.approx([0.0, 0.01, 0.03])


@pytest.mark.parametrize(
    ("ticker", "name", "local"),
    [
        ("ALICORC1", "Alicorp S.A.A.", True),
        ("BACKUSI1", "Union De Cervecerias Peruanas Backus Y Johnston", True),
        ("AMD", "Advanced Micro Devices, Inc.", False),
        ("BAP", "Credicorp Ltd.", False),
        ("FICORPS2", "Coril Renta Prime Soles 2 - Fondo De Inversion", False),
        ("COWZ1", "Pacerus Cashcows100uts Etfacc", False),
        ("SPXS1", "Invesco S&P500 Ucits Etf", False),
    ],
)
def test_local_shares_exclude_foreign_listings_funds_and_etfs(
    ticker: str, name: str, *, local: bool
) -> None:
    assert panel.is_local_share(ticker, name) is local
