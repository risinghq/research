---
summary: Peru's private investment grew more than 10% a year for five straight quarters to September 2026, from a low base; firms' plans for the next three months cooled, and construction's turned negative.
topic: peru-economy
status: live
published: 2026-11-21
data: 2026-10-31
---

# Peru's private investment

Gross fixed private investment is what firms and households spend on
buildings, machinery and equipment. The Banco Central de Reserva del Perú
(BCRP) publishes it each quarter in the national accounts, and each month it
asks firms how much they plan to invest. Every series below comes from
BCRPData with its code. On 2026-11-21
[Gestión](https://gestion.pe/economia/inversion-privada-crece-por-quinto-trimestre-a-doble-digito-pero-esta-vez-a-menor-ritmo-noticia/)
reported the fifth quarter of double-digit growth.

- Private investment grew 13.6% in the third quarter of 2026 on a year
  before, after 17.8% in the second. It has grown 10% or more for five
  straight quarters.
- Since 2010 only the quarters of 2010 and the 2021 rebound from the pandemic
  grew faster than the second quarter of 2026.
- The growth starts from a low base. Over the last four quarters private
  investment was 16.9% of GDP, under the 17.6% of 2019 and the 20.9% peak of
  2013.
- In October, firms in mining, manufacturing, commerce and services still
  planned to invest more in the next three months. Construction firms, at
  47.4, planned to invest less.

## Growth

![Private investment growth in Peru](https://research.rising.sh/peru-private-investment/growth.svg)

Each bar is the real change in private investment on the same quarter a year
before, series `PN02522AQ`. BCRP revises earlier quarters with each release,
and the chart shows its latest estimate.

Public investment, series `PN02523AQ`, fell 0.2% in the first quarter of 2026
and 2.5% in the second, and grew 4.2% in the third.

## A low base

![Private investment as a share of GDP](https://research.rising.sh/peru-private-investment/share.svg)

Growth rates compare each quarter with a year before, so they say nothing of
the level. Private investment's share of nominal GDP, series `PN02556AQ`,
fell from 20.9% in the year to September 2013 to 16.9% in 2017, rebounded to
20.1% in 2021 and fell back to 16.6% in 2025. Five quarters of fast growth
have lifted it only to 16.9%.

## Plans for the next three months

![Firms' investment plans for the next three months](https://research.rising.sh/peru-private-investment/expectations.svg)

BCRP's monthly business survey asks firms whether they expect to invest more,
the same or less in the next three months. An index above 50 means more firms
expect to invest more than less. BCRPData publishes the index by sector:

| Sector | Series | July 2026 | October 2026 |
| ------ | ------ | --------- | ------------ |
| Mining and hydrocarbons | `PD41404AM` | 50.0 | 58.7 |
| Manufacturing | `PD41412AM` | 57.1 | 54.1 |
| Construction | `PD41420AM` | 53.6 | 47.4 |
| Commerce | `PD41428AM` | 62.1 | 56.3 |
| Services | `PD41436AM` | 62.7 | 55.7 |

Four sectors fell from July to October. Mining rose. Construction is the only
sector below 50.

## Limits

- **Revisions.** BCRP revises the national accounts with each release, so a
  quarter's growth can change after it is first published.
- **Survey.** The expectations index counts firms, not money: a large miner
  and a small shop weigh the same. It covers the firms BCRP surveys, not all
  firms.
- **Share of GDP.** The chart averages four quarterly shares, which differs
  slightly from the share of yearly totals.

## Reproduce

Every series comes from [BCRPData](https://estadisticas.bcrp.gob.pe), whose
API needs no key. [`peru_private_investment.py`](peru_private_investment.py)
fetches them, writes every chart and [`numbers.json`](numbers.json), and sets
the `data` date. The rerun workflow runs it each weekday.

```bash
mise run install
uv run studies/peru-private-investment/peru_private_investment.py
```
