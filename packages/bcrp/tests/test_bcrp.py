from datetime import date

import bcrp


def test_period_day_reads_spanish_months_across_the_century() -> None:
    assert bcrp.period_day("02.Ene.97") == date(1997, 1, 2)
    assert bcrp.period_day("30.Set.19") == date(2019, 9, 30)


def test_period_name_reads_months_and_quarters_across_the_century() -> None:
    assert bcrp.period_name("Sep.2026") == "2026-09"
    assert bcrp.period_name("Ago.2026") == "2026-08"
    assert bcrp.period_name("T3.26") == "2026-Q3"
    assert bcrp.period_name("T1.80") == "1980-Q1"


def test_parse_periods_skips_unpublished_periods() -> None:
    body = {
        "periods": [
            {"name": "T2.26", "values": ["17.76"]},
            {"name": "T3.26", "values": ["n.d."]},
        ]
    }
    assert bcrp.parse_periods(body) == [("2026-Q2", 17.76)]
