---
summary: Peru's cajas municipales earned S/ 1,124.5 million from January to September 2026, 93% more than a year before and almost four times their best year before 2025; every figure in Gestión's article of 2026-11-20 matches the SBS's workbooks.
topic: peru-microfinance
status: finished
published: 2026-11-21
data: 2026-09-30
---

# The profits of Peru's microfinance firms

On 2026-11-20 Gestión reported that
[cajas municipales and rurales earned twice as much as a year before](https://gestion.pe/economia/empresas/cajas-municipales-y-rurales-ganan-el-doble-que-hace-un-ano-cuales-son-las-5-mas-rentables-noticia/),
with data from the Superintendencia de Banca, Seguros y AFP (SBS) to September.
The article has no table and names five cajas as the most profitable without a
figure or the measure it ranks them by. This study reads the SBS's monthly
workbooks for September of every year from 2010, for the four systems the
article covers: cajas municipales, cajas rurales, empresas financieras and
empresas de crédito.

- The cajas municipales earned S/ 1,124.5 million from January to September
  2026, up 93.1% on 2025, as Gestión reported. All eleven earned more, and
  ten raised their return on equity; CMAC Del Santa's fell. Their best
  January to September before 2025 was S/ 304.7 million, in 2019.
- The system's return on equity, 24.1%, is the highest of any September since
  2010. The previous high was 16.3%, in 2012.
- The cajas rurales earned S/ 17.7 million, up from S/ 7.9 million. They lost
  money in nine of the eleven Septembers from 2014 to 2024.
- The empresas financieras earned S/ 158.5 million, 16.3% less, and the
  empresas de crédito S/ 91.0 million, 52.4% more. Every figure and return on
  equity the article quotes matches the workbooks at the precision it gives.
- The five cajas Gestión names, CMCP Lima, Piura, Huancayo, Cusco and
  Arequipa in that order, are the five with the highest return on equity, in
  that order. By profit, CMCP Lima earned S/ 20.3 million and ranks seventh
  of eleven.

## Profits

![Microfinance profits, January to September](https://research.rising.sh/peru-microfinance-profits/profits.svg)

Net profit is the year to date, so each point is January to September of its
year, in current soles. The pandemic years show as the drop of 2020 and 2021:
the cajas municipales lost S/ 14.6 million in 2021 and the financieras lost
money in both years.

## Return on equity

![Return on equity by firm](https://research.rising.sh/peru-microfinance-profits/roe.svg)

Return on equity is the SBS's net profit over average equity, annualised. The
red tick marks September 2025. Gestión wrote 36.8% for Financiera Qapaq,
18.8% for Mitsui Auto Finance, 18.1% for Financiera Proempresa, 26.7% for
Santander Consumo, 13.5% for Vívela, 13.3% for Total Servicios Financieros
and about 8% for CRAC Incasur and CRAC Cencosud Scotia. The workbooks give
36.79, 18.76, 18.07, 26.68, 13.47, 13.30, 7.89 and 7.82.

InFinance XP lost S/ 3.8 million from January to September 2026, yet shows a
return on equity of 0.93%. The SBS annualises profit as the last twelve
months, October 2025 to September 2026, so a loss this year can sit beside a
positive return.

## Arrears

![Loans in arrears by firm](https://research.rising.sh/peru-microfinance-profits/arrears.svg)

Arrears are loans past due or in court collection over direct loans, the
SBS's "morosidad". They rose at three cajas municipales, Del Santa, Maynas and
Paita, and fell at the other eight and at every caja rural, financiera and
empresa de crédito, as the article reported.

## Which firms count

Gestión counted 24 of 26 firms earning more. The workbooks give the same
count once two firms drop out:

- **CRAC del Centro** reports zero in every column of September 2026. The
  SBS keeps a column of zeros for a firm that stopped reporting, so the study
  reads it as absent.
- **Financiera Efectiva** appears in September 2025 and not in 2026.

The two firms whose profit fell are InFinance XP and Vívela.

## Limits

- **Current soles.** Profits are not adjusted for inflation.
- **Year to date.** September's figures cover nine months. A full year's
  profit is in December's workbooks, which this study does not read.
- **Firms change.** The SBS approved Financiera Oh!'s new name, InFinance XP,
  in
  [Resolución SBS 00332-2026](https://busquedas.elperuano.pe/dispositivo/NL/2485493-1)
  of 2026-02-03; the study joins the two names. It does not join firms that
  merged, and the system totals include whichever firms reported that year.
  The empresas de crédito were called EDPYMEs until 2021; the SBS kept the
  same reports.
- **Solidaridad.** The EDPYME Solidaridad has no profit column after 2016,
  and its indicators are zero from 2017, so it is absent from those years.

## Data

The SBS publishes one workbook per system, report and month at
[intranet2.sbs.gob.pe/estadistica/financiera](https://intranet2.sbs.gob.pe/estadistica/financiera/).
The study reads the balance and income statement workbook and the indicators
workbook for September of each year:

| System | Statements | Indicators |
| --- | --- | --- |
| Cajas municipales | C-1101 | C-1301 |
| Cajas rurales | C-2101 | C-2301 |
| Empresas financieras | B-3101 | B-3301 |
| Empresas de crédito | C-4103 | C-4301 |

The workbooks were read on 2026-11-21.

## Reproduce

[`entities.csv`](entities.csv) holds net profit in thousands of soles, return
on equity and arrears, one row per system, year and firm, with `Total` for the
system. [`peru_microfinance_profits.py`](peru_microfinance_profits.py) charts
it and writes [`numbers.json`](numbers.json), which lists every firm under
`by_firm` and the firms of one year only under `gone` and `new`. The SBS answers scripts with a challenge
page, so the workbooks come through a browser;
[docs/sbs.md](../../docs/sbs.md) gives the steps. `--raw DIR` rebuilds
`entities.csv` from the 136 workbooks saved in DIR.

```bash
mise run install
uv run studies/peru-microfinance-profits/peru_microfinance_profits.py
uv run studies/peru-microfinance-profits/peru_microfinance_profits.py --raw DIR
```
