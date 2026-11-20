import bvl_liquidity as liquidity
import numpy as np
import pandas as pd
import pytest


def test_time_effects_recover_year_effects_on_an_unbalanced_panel() -> None:
    rng = np.random.default_rng(7)
    year_effect = {2000: 0.0, 2001: 1.0, 2002: -0.5, 2003: 2.0}
    rows = []
    for unit in range(40):
        # Units enter and leave at different years, and each has its own level,
        # as a dollar stock's ratio sits a constant factor from a sol stock's.
        level = rng.normal(0, 3)
        first = int(rng.integers(2000, 2003))
        for year in range(first, int(rng.integers(first + 1, 2004)) + 1):
            for _ in range(3):
                value = level + year_effect[year] + rng.normal(0, 0.01)
                rows.append((unit, year, value))
    frame = pd.DataFrame(rows, columns=["unit", "year", "value"])

    effects = liquidity.time_effects(frame["value"], frame["unit"], frame["year"])

    expected = pd.Series(year_effect)
    expected -= expected.mean()
    assert effects.to_numpy() == pytest.approx(expected.to_numpy(), abs=0.02)
