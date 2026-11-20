from datetime import date

import bcrp


def test_period_day_reads_spanish_months_across_the_century() -> None:
    assert bcrp.period_day("02.Ene.97") == date(1997, 1, 2)
    assert bcrp.period_day("30.Set.19") == date(2019, 9, 30)
