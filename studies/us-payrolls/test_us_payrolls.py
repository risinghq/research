import json

from datetime import date
from pathlib import Path

import bls
import httpx2
import us_payrolls


FIXTURE = Path(__file__).parents[2] / "packages" / "bls" / "tests" / "fixtures"


def _client(revise: dict[str, str] | None = None) -> bls.BlsClient:
    """A client answering the 2025-26 payrolls fixture, with `revise` overriding
    a month's level by its `YYYY-Mnn` key."""
    body = json.loads((FIXTURE / "payrolls.json").read_text(encoding="utf-8"))
    for row in body["Results"]["series"][0]["data"]:
        row["value"] = (revise or {}).get(
            f"{row['year']}-{row['period']}", row["value"]
        )

    def answer(request: httpx2.Request) -> httpx2.Response:
        if json.loads(request.content)["endyear"] == "2026":
            return httpx2.Response(200, json=body)
        empty = {"seriesID": bls.PAYROLLS, "data": []}
        return httpx2.Response(
            200, json={"status": "REQUEST_SUCCEEDED", "Results": {"series": [empty]}}
        )

    return bls.BlsClient(transport=httpx2.MockTransport(answer))


def test_a_rerun_matches_every_posted_month_and_dates_the_readme(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("---\ndata: 2026-09-30\n---\n", "utf-8")

    numbers = us_payrolls.run(_client(), tmp_path, date(2026, 11, 20))

    assert numbers["revised_since_post"] == []
    assert numbers["latest"] == {
        "period": "2026-10",
        "value": 165000,
        "preliminary": True,
    }
    assert "data: 2026-10-31" in (tmp_path / "README.md").read_text("utf-8")
    chart = json.loads((tmp_path / "payrolls.json").read_text("utf-8"))
    assert chart["view"] == "2026-01"
    assert chart["points"][0]["period"] == "2025-02"


def test_a_revised_month_is_listed_with_the_posted_and_current_change(
    tmp_path: Path,
) -> None:
    # September 159128 + 5 lifts September's change by 5,000 and cuts October's.
    numbers = us_payrolls.run(
        _client({"2026-M09": "159133"}), tmp_path, date(2026, 11, 20)
    )

    assert numbers["revised_since_post"] == [
        {"period": "2026-09", "posted": 60000, "now": 65000},
        {"period": "2026-10", "posted": 165000, "now": 160000},
    ]
