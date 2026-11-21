<a href="https://rising.sh"><picture><source media="(prefers-color-scheme: dark)" srcset="https://rising.sh/brand/rising-sh-dark.svg"><img alt="rising.sh" src="https://rising.sh/brand/rising-sh-light.svg" height="28"></picture></a>

# research

Studies on open data by rising.sh. Each study is a folder under
[`studies/`](studies) with its question, its report, the numbers it cites and
its chart files, which [docs/charts.md](docs/charts.md) describes. Shared data
clients live under [`packages/`](packages).

## Studies

The Lima Stock Exchange (BVL), on the SMV's open data and the central bank's
series:

- [BVL liquidity since 1996](studies/bvl-liquidity/README.md), and the MSCI
  review of 2015-16.
- [Do BVL prices move before a material event is filed?](studies/bvl-disclosure/README.md)
- [How the BVL and the sol take Peru's political shocks](studies/bvl-politics/README.md)
- [How concentrated is BVL brokerage?](studies/bvl-brokers/README.md)
- [When BVL issuers file their quarterly results, and how prices take them](studies/bvl-earnings/README.md)
- [Who holds BVL issuers, and does a concentrated register trade less?](studies/bvl-ownership/README.md)

[docs/bvl.md](docs/bvl.md) describes the data and the `bvl` command.

Replications rebuild a published chart from its public data and rerun it as
the data updates; [docs/replications.md](docs/replications.md) describes them:

All six rebuild Axios charts, five from BLS series and one from NAHB's
Housing Market Index:

- [Change in U.S. nonfarm payrolls](studies/us-payrolls/README.md)
- [Change in the Consumer Price Index](studies/us-cpi/README.md)
- [Year-over-year change in the Producer Price Index](studies/us-ppi/README.md)
- [Change in U.S. output per hour of labor](studies/us-productivity/README.md)
- [Ground beef price per pound](studies/us-beef-prices/README.md)
- [U.S. homebuilder sentiment index](studies/us-homebuilder-sentiment/README.md)

## Run a study

You need [mise](https://mise.jdx.dev/), which installs the pinned Python and uv:

```bash
mise run install
uv run bvl fetch quotes
uv run studies/bvl-liquidity/bvl_liquidity.py
```

A study reads `data/`, which is not committed, and rewrites its folder. Its
README lists the fetches it needs. Each README opens with front matter that the
research.rising.sh site reads: a one-line `summary`, the `topic`, a `status` of
`live` or `finished`, the `published` date and the `data` date the numbers run
to. A replication adds the keys that name its original.

A README ends with a `## Reproduce` section that names the script, its output
files and the commands that rerun it. The text above that section is for
readers and names no files, commands or pipeline. The site shows the text above
`## Reproduce`, links the study's folder for the rest, and fails its build on a
README without the section.

`mise run check` runs the lint, type checks and tests that CI runs.
