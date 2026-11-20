# research

Rising's studies on open data. Each study is a folder under
[`studies/`](studies) with its question, its report, the numbers it cites and
its figures. Shared data clients live under [`packages/`](packages).

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

- [Change in U.S. nonfarm payrolls](studies/us-payrolls/README.md), after
  Axios, from the BLS.

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
`mise run check` runs the lint, type checks and tests that CI runs.
