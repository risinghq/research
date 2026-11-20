from dataclasses import dataclass
from datetime import date

import pytest
import replication


@dataclass(frozen=True)
class _Obs:
    day: date
    value: float
    preliminary: bool = False


def test_a_missing_month_leaves_a_gap_in_both_changes_that_span_it() -> None:
    # BLS published no index for October 2025.
    found = [
        _Obs(date(2025, 9, 1), 100.0),
        _Obs(date(2025, 11, 1), 102.0),
        _Obs(date(2025, 12, 1), 103.02, preliminary=True),
    ]

    points = replication.changes(
        replication.levels(found), 1, lambda now, before: now - before
    )

    assert [(p.period, p.value) for p in points] == [
        ("2025-10", None),
        ("2025-11", None),
        ("2025-12", pytest.approx(1.02)),
    ]
    assert points[-1].preliminary


def test_quarterly_observations_become_quarter_periods() -> None:
    found = [_Obs(date(2025, 10, 1), 1.2), _Obs(date(2026, 4, 1), 2.1)]

    points = replication.levels(found, quarterly=True)

    assert [(p.period, p.value) for p in points] == [
        ("2025-Q4", 1.2),
        ("2026-Q1", None),
        ("2026-Q2", 2.1),
    ]
    assert replication.period_end("2026-Q2") == date(2026, 6, 30)


@pytest.mark.parametrize(
    ("posted", "now", "expected"),
    [
        pytest.param(0.4, 0.35028, False, id="same at the posted decimal"),
        pytest.param(0.4, 0.34, True, id="changed at the posted decimal"),
        pytest.param(165000, 165000.0, False, id="whole number unchanged"),
        pytest.param(165000, 160000.0, True, id="whole number changed"),
        pytest.param(2.59481, 2.59482, True, id="five decimals changed"),
        pytest.param(0.4, None, True, id="no value now"),
    ],
)
def test_a_value_is_revised_only_when_it_differs_at_the_posted_precision(
    posted: float, now: float | None, expected: bool
) -> None:
    assert replication.revised(posted, now) is expected
