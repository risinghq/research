---
summary: Peru's cajas municipales earned S/ 1,124.5 million from January to September 2026, 93% more than a year before and almost four times their best year before 2025. Their return on equity, 24.1%, is the highest of any September since 2010.
topic: peru-microfinance
status: finished
published: 2026-11-21
data: 2026-09-30
---

# The profits of Peru's microfinance firms

The Superintendencia de Banca, Seguros y AFP (SBS) supervises four systems of
microfinance firms: the cajas municipales, savings banks owned by
municipalities; the cajas rurales; the empresas financieras; and the empresas
de crédito. Each month it publishes every firm's balance sheet, income
statement and indicators. On 2026-11-20
[Gestión](https://gestion.pe/economia/empresas/cajas-municipales-y-rurales-ganan-el-doble-que-hace-un-ano-cuales-son-las-5-mas-rentables-noticia/)
reported that the cajas earned twice as much as a year before.

- The cajas municipales earned S/ 1,124.5 million from January to September
  2026, up 93.1% on 2025. Their best January to September before 2025 was
  S/ 304.7 million, in 2019. All eleven earned more, and ten raised their
  return on equity; CMAC Del Santa's fell.
- The system's return on equity, 24.1%, is the highest of any September since
  2010. The previous high was 16.3%, in 2012.
- The cajas rurales earned S/ 17.7 million, up from S/ 7.9 million. They lost
  money in nine of the eleven Septembers from 2014 to 2024.
- The empresas financieras earned S/ 158.5 million, 16.3% less, and the
  empresas de crédito S/ 91.0 million, 52.4% more.
- Of the 26 firms that reported in both Septembers, 24 earned more. InFinance
  XP and Vívela earned less.

## Profits

![Microfinance profits, January to September](https://research.rising.sh/peru-microfinance-profits/profits.svg)

Net profit is the year to date, so each point is January to September of its
year, in current soles. The pandemic shows as the drop of 2020 and 2021: the
cajas municipales lost S/ 14.6 million in 2021, and the financieras lost money
in both years.

## Return on equity

![Return on equity by firm](https://research.rising.sh/peru-microfinance-profits/roe.svg)

Return on equity is the SBS's net profit over average equity, annualised. The
red tick marks September 2025.

The five cajas municipales with the highest return are CMCP Lima (30.6%),
Piura (30.1%), Huancayo (29.2%), Cusco (25.8%) and Arequipa (23.1%). CMCP Lima
is the smallest of the five: it earned S/ 20.3 million and ranks seventh of
eleven by profit. The highest return in each other system is Financiera
Qapaq's, 36.8%, among the financieras; Santander Consumo's, 26.7%, among the
empresas de crédito; and CRAC Incasur's, 7.9%, among the cajas rurales.

InFinance XP lost S/ 3.8 million from January to September 2026, yet shows a
return on equity of 0.93%. The SBS annualises profit as the last twelve
months, October 2025 to September 2026, so a loss this year can sit beside a
positive return.

## Arrears

![Loans in arrears by firm](https://research.rising.sh/peru-microfinance-profits/arrears.svg)

Arrears are loans past due or in court collection over direct loans, the
SBS's "morosidad". They rose at three cajas municipales, Del Santa, Maynas and
Paita, and fell at the other eight and at every caja rural, financiera and
empresa de crédito.

## Limits

- **Current soles.** Profits are not adjusted for inflation.
- **Year to date.** September's figures cover nine months. A full year's
  profit is in December's workbooks, which are not read here.
- **Firms that stopped reporting.** CRAC del Centro reports zero in every
  column of September 2026, the SBS's mark for a firm that stopped reporting,
  and Financiera Efectiva is absent from 2026. Neither counts among the 26.
  The EDPYME Solidaridad has no profit column after 2016 and zero indicators
  from 2017, so it is absent from those years.
- **Firms change.** The SBS approved Financiera Oh!'s new name, InFinance XP,
  in
  [Resolución SBS 00332-2026](https://busquedas.elperuano.pe/dispositivo/NL/2485493-1)
  of 2026-02-03, and the two names are joined. Firms that merged are not
  joined, and the system totals include whichever firms reported that year.
  The empresas de crédito were called EDPYMEs until 2021; the SBS kept the
  same reports.

## Data

The SBS publishes one workbook per system, report and month at
[intranet2.sbs.gob.pe/estadistica/financiera](https://intranet2.sbs.gob.pe/estadistica/financiera/).
The figures come from the balance and income statement workbook and the
indicators workbook for September of each year from 2010:

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
`by_firm` and the firms of one year only under `gone` and `new`. The SBS
answers scripts with a challenge page, so the workbooks come through a
browser; [docs/sbs.md](../../docs/sbs.md) gives the steps. `--raw DIR`
rebuilds `entities.csv` from the 136 workbooks saved in DIR.

```bash
mise run install
uv run studies/peru-microfinance-profits/peru_microfinance_profits.py
uv run studies/peru-microfinance-profits/peru_microfinance_profits.py --raw DIR
```
