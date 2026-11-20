---
summary: The monthly change in the U.S. Consumer Price Index, rebuilt from the BLS series behind an Axios chart and rerun after every CPI release.
topic: us-economy
status: live
published: 2026-11-20
data: 2026-10-31
replicates: https://www.axios.com/2026/11/10/cpi-october-inflation-fed
original: Price pressures persisted in October
author: Courtenay Brown
outlet: Axios
posted: 2026-11-10
---

# Change in the Consumer Price Index

On 2026-11-10 Axios charted the monthly change in the U.S. Consumer Price Index
from January to October 2026, the day the Bureau of Labor Statistics (BLS)
released the October index. This study rebuilds that chart from the BLS series
it was drawn from, series `CUSR0000SA0`, all items for all urban consumers,
U.S. city average, seasonally adjusted. The data is public domain and comes
from the BLS Public Data API.

![Change in the Consumer Price Index, monthly](https://research.rising.sh/us-cpi/cpi.svg)

Each bar is a month's index over the month before, as a percent change. The
chart gains each new month the day BLS publishes it.

## What differs from the original

- **Months.** The original shows January to October 2026. This chart opens on
  the same months and reaches back to January 2000.
- **October 2025.** BLS collected no prices in October 2025, during the lapse
  in appropriations, so the series has no index for that month. October and
  November 2025 have no monthly change, and the chart leaves them empty.
- **Revisions.** BLS revises the seasonal factors of the last five years with
  each January index, published in February. The original keeps the numbers
  of 2026-11-10. This chart shows the latest figures and draws the original's
  beside them.

## Checked against the original

The post's chart publishes the values it plots. On 2026-11-20 the BLS series gave the same change for January to September 2026 to five
decimals. For October the original shows 0.4%, the figure BLS rounded in its
release, and the index gives 0.35%, which rounds to the same 0.4%.

## Reproduce

[`us_cpi.py`](us_cpi.py) fetches the series from 1999 and writes the chart file
[`cpi.json`](cpi.json) and [`numbers.json`](numbers.json). Its
`revised_since_post` lists every month that changed at the original's one
decimal. The rerun workflow runs the script every weekday.

```bash
mise run install
uv run studies/us-cpi/us_cpi.py
```

The script needs no key. Set `BLS_API_KEY` to a BLS registration key to raise
the daily request limit.
