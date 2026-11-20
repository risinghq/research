---
summary: The monthly change in U.S. nonfarm payrolls, rebuilt from the BLS series behind an Axios chart and rerun after every jobs report.
topic: us-economy
status: live
published: 2026-11-20
data: 2026-10-31
replicates: https://www.axios.com/2026/11/06/october-2026-jobs-report-unemployment-165000
original: U.S. labor market zooms ahead with 165,000 jobs added in October
author: Courtenay Brown
outlet: Axios
posted: 2026-11-06
---

# Change in U.S. nonfarm payrolls

On 2026-11-06 Axios charted the monthly change in U.S. nonfarm payrolls from
January to October 2026, the day the Bureau of Labor Statistics (BLS) released
the October jobs report. This study rebuilds that chart from the BLS series it
was drawn from, series `CES0000000001`, total nonfarm employment, seasonally
adjusted. The data is public domain and comes from the BLS Public Data API.

![Change in U.S. nonfarm payrolls, monthly](https://research.rising.sh/us-payrolls/payrolls.svg)

Each bar is a month's level less the month before. The chart gains each new
month and every revision the day BLS publishes it.

## What differs from the original

- **Months.** The original shows January to October 2026. This chart opens on
  the same months and reaches back to January 2000.
- **Revisions.** Each jobs report revises the two months before it, and the
  annual benchmark, published with the January report, revises the past years.
  The original keeps the numbers of 2026-11-06. This chart shows the latest
  estimate and draws the original's numbers beside it.
- **Preliminary months.** BLS marks the two latest months preliminary; the
  chart marks them too.

## Checked against the original

The post's chart publishes the values it plots. On 2026-11-20 the BLS series
gave the same change, to the thousand, for each of its ten months:
from 160,000 in January and −156,000 in February to 165,000 in October.

## Reproduce

[`us_payrolls.py`](us_payrolls.py) fetches the series from 1999 and writes the
chart file [`payrolls.json`](payrolls.json) and
[`numbers.json`](numbers.json). Its `revised_since_post` lists every month that
changed since the post. The rerun workflow runs the script every weekday.

```bash
mise run install
uv run studies/us-payrolls/us_payrolls.py
```

The script needs no key. Set `BLS_API_KEY` to a BLS registration key to raise
the daily request limit.
