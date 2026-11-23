---
summary: The year-over-year change in the U.S. Producer Price Index for final demand, rebuilt from the BLS series behind an Axios chart and rerun after every PPI release.
topic: us-economy
status: live
published: 2026-11-20
data: 2026-10-31
replicates: https://www.axios.com/2026/11/13/freight-inflation-supply-chain-iran
original: High transportation costs drive wholesale prices
author: Courtenay Brown
outlet: Axios
posted: 2026-11-13
---

# Year-over-year change in the Producer Price Index

On 2026-11-13 Axios charted the year-over-year change in the U.S. Producer
Price Index for final demand from November 2010 to October 2026. The chart
below rebuilds it from the series it was drawn from, Bureau of Labor
Statistics (BLS) series `WPSFD4`, final demand, seasonally adjusted. The data
is public domain and comes from the BLS Public Data API.

![Year-over-year change in the Producer Price Index, monthly](https://research.rising.sh/us-ppi/ppi.svg)

Each point is a month's index over the same month a year before, as a percent
change. The chart gains each new month and every revision the day BLS
publishes it.

## What differs from the original

- **Source.** The original credits BLS through FRED, whose series
  `PPIFIS_PC1` is the same change computed from the same index. This chart
  reads the index from BLS.
- **Seasonal adjustment.** BLS headlines the change of the index that is not
  seasonally adjusted, `WPUFD4`. The original, and this chart, use the
  seasonally adjusted index, so the latest figure can differ from the one in
  the BLS release by a tenth or two.
- **Revisions.** BLS marks the four latest months preliminary and revises them,
  and it revises the seasonal factors of the last five years each February.
  The original keeps the numbers of 2026-11-13. This chart shows the latest
  figures, marks the preliminary months and draws the original's line beside
  its own.

## Checked against the original

The post's chart publishes the values it plots. On 2026-11-20 the BLS index
gave the same change, at the original's precision, for all 192
months, from November 2010 to October 2026.

## Reproduce

[`us_ppi.py`](us_ppi.py) fetches the series from its start in November 2009
and writes the chart file [`ppi.json`](ppi.json) and
[`numbers.json`](numbers.json). Its `revised_since_post` lists every month that
changed since the post. The rerun workflow runs the script every weekday.

```bash
mise run install
uv run studies/us-ppi/us_ppi.py
```

The script needs no key. Set `BLS_API_KEY` to a BLS registration key to raise
the daily request limit.
