---
summary: How U.S. homebuilders rate the market for new single-family homes, rebuilt from the NAHB/Wells Fargo index behind an Axios chart and rerun after every monthly release.
topic: us-economy
status: live
published: 2026-11-20
data: 2026-11-30
replicates: https://www.axios.com/2026/11/18/homebuilders-construction-housing-market-october
original: Homebuilder warning: Construction rebounds, but building plans plunge
author: Courtenay Brown
outlet: Axios
posted: 2026-11-18
---

# U.S. homebuilder sentiment index

On 2026-11-18 Axios charted the NAHB/Wells Fargo Housing Market Index from
January 2000 to November 2026. The chart below rebuilds it from the index's
history, which the National Association of Home Builders (NAHB) publishes on
its [Housing Market Index page](https://www.nahb.org/news-and-economics/housing-economics/indices/housing-market-index).
NAHB allows its use here with credit: the data is the NAHB/Wells Fargo Housing
Market Index.

Each month NAHB asks single-family homebuilders to rate current sales, sales
expected over the next six months, and the traffic of prospective buyers. The
index combines the three answers and is seasonally adjusted. A reading above
50 means more builders see conditions as good than poor.

![U.S. homebuilder sentiment index, monthly](https://research.rising.sh/us-homebuilder-sentiment/hmi.svg)

The index fell to 25 in November 2026, from 29 in October and 38 a year
earlier. It was last that low in April 2012, at 24. Since January 2000 it has
ranged from 8 in January 2009 to 90 in November 2020. The chart gains each new
month the day NAHB releases it, around the middle of the month.

## What differs from the original

- **Months.** The original shows January 2000 to November 2026. This chart
  opens on the same months, reaches back to January 1985, where NAHB's table
  starts, and adds the months NAHB has released since the post.
- **Recessions.** The original shades the recessions. This chart does not.
- **Revisions.** NAHB revises past months when it updates the seasonal
  adjustment. The chart shows the values as NAHB publishes them now.

## Checked against the original

The post's chart carries the values it plots. On 2026-11-20 NAHB's table gave
the same value for each of its 323 months, from January 2000 to November 2026.

## Reproduce

[`us_homebuilder_sentiment.py`](us_homebuilder_sentiment.py) reads the link to
"Table 2: National HMI – History" from NAHB's page, downloads the table and
writes the chart file [`hmi.json`](hmi.json) and
[`numbers.json`](numbers.json). [`original.csv`](original.csv) holds the
values the Axios chart plots. The rerun workflow runs the script every
weekday.

```bash
mise run install
uv run studies/us-homebuilder-sentiment/us_homebuilder_sentiment.py
```
