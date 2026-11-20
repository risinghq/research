---
summary: The quarterly change in U.S. labor productivity, rebuilt from the BLS series behind an Axios chart and rerun after every productivity release.
topic: us-economy
status: live
published: 2026-11-20
data: 2026-09-30
replicates: https://www.axios.com/2026/11/05/labor-output-productivity-ai
original: Strong Q3 labor output shows a productivity surge
author: Neil Irwin
outlet: Axios
posted: 2026-11-05
---

# Change in U.S. output per hour of labor

On 2026-11-05 Axios charted the quarterly change in U.S. labor productivity
from the third quarter of 2024 to the third quarter of 2026, the day the
Bureau of Labor Statistics (BLS) released its third-quarter estimate. This
study rebuilds that chart from the BLS series it was drawn from, series
`PRS85006092`, output per hour in the nonfarm business sector, percent change
from the quarter before at an annual rate. The data is public domain and comes
from the BLS Public Data API.

![Change in U.S. output per hour of labor, quarterly](https://research.rising.sh/us-productivity/productivity.svg)

The chart shows the change as BLS publishes it and gains each new quarter and
every revision the day BLS publishes it.

## What differs from the original

- **Quarters.** The original shows the third quarter of 2024 to the third
  quarter of 2026. This chart opens on the same quarters and reaches back to
  2000.
- **Revisions.** Each release revises earlier quarters, and the revised
  estimate of a quarter follows about a month after the first. The original
  keeps the numbers of 2026-11-05. This chart shows the latest estimate and
  draws the original's numbers beside it.

## Checked against the original

The post's chart publishes the values it plots. On 2026-11-20 the BLS series
gave the same change, to the tenth, for each of its nine quarters.

## Reproduce

[`us_productivity.py`](us_productivity.py) fetches the series from 2000 and
writes the chart file [`productivity.json`](productivity.json) and
[`numbers.json`](numbers.json). Its `revised_since_post` lists every quarter
that changed since the post. The rerun workflow runs the script every weekday.

```bash
mise run install
uv run studies/us-productivity/us_productivity.py
```

The script needs no key. Set `BLS_API_KEY` to a BLS registration key to raise
the daily request limit.
