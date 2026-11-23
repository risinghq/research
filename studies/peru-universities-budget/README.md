---
summary: San Marcos' 2026 opening budget cut goods and services by S/ 13.5 million and investment by S/ 3.8 million, as it said, but pay rose more, so its total rose S/ 6.5 million. Public universities lost S/ 298 million of Treasury funding, and in 2025 they spent 90% of their budgets, the most since 2012.
topic: peru-universities
status: live
published: 2026-11-21
data: 2026-11-20
---

# The budgets of Peru's public universities

On 2025-12-11 the Universidad Nacional Mayor de San Marcos declared itself in
emergency over budget cuts, as
[Infobae](https://www.infobae.com/peru/2025/12/11/unmsm-se-declara-en-emergencia-por-recortes-de-presupuesto-que-superan-s-100-millones-y-alerta-impacto-en-calidad-educativa-e-investigacion/)
and
[América TV](https://www.americatv.com.pe/noticias/actualidad/unmsm-se-declara-emergencia-recorte-s100-millones-n513827)
reported from its communiqué. On 2026-11-19
[La República](https://larepublica.pe/sociedad/2026/11/19/san-marcos-denuncia-recorte-presupuestal-y-anuncia-marcha-hacia-el-congreso-este-24-de-noviembre-1043119)
reported a march to Congress on 2026-11-24 over the same cuts. The budget
data the Ministerio de Economía y Finanzas (MEF) publishes check the
communiqué's figures and set San Marcos beside the country's other public
universities.

- San Marcos' communiqué said its 2026 budget was S/ 17,296,489 below 2025's:
  S/ 13,484,620 less for goods and services and S/ 3,811,869 less for capital
  spending. MEF's opening budgets (PIA) match both cuts to the sol. The
  S/ 17.3 million is their sum, not the change in the total. Pay rose
  S/ 19.4 million and pensions S/ 4.0 million, so San Marcos' opening budget
  rose S/ 6.5 million, to S/ 677.7 million.
- The rectors said ordinary resources, the Treasury's share, fell S/ 288
  million for public universities. MEF's opening budgets show a fall of
  S/ 297.9 million, from S/ 4,997 million in 2025 to S/ 4,699 million.
- Public universities spent 90.1% of their budget after changes (PIM) in
  2025, the most since 2012, when they spent 70.1%. They spent 75.1% of their
  investment budget. San Marcos spent 94.7% and 76.7%.
- Through October 2026 San Marcos had spent 72.6% of its budget after
  changes, against 72.7% through October 2025.

None of the reports cited here alleges misuse of funds. The figures show how
much was budgeted and how much was spent, not what the money bought.

## San Marcos

![San Marcos' budget and spending](https://research.rising.sh/peru-universities-budget/unmsm.svg)

The opening budget (PIA) is the one Congress approves in December. The budget
after changes (PIM) adds the transfers and credits of the year. San Marcos'
PIA grew from S/ 361 million in 2012 to S/ 678 million in 2026, in current
soles. Its largest step was 2024, when the PIA rose 23%.

The communiqué also said S/ 40 million allotted under Ley 32185 arrived as
S/ 12,840,828, that S/ 72,983,846 assigned for 2025 was never transferred, and
that a S/ 45,824,674 research centre got no funding. A transfer that never
arrived never enters the PIM, and the data names no project as promised, so
these three figures cannot be checked.

| Spending group | PIA 2025 | PIA 2026 | Change |
| -------------- | -------: | -------: | -----: |
| 2.1 Personnel and social obligations | 355.8 | 375.2 | +19.4 |
| 2.2 Pensions and social benefits | 42.2 | 46.2 | +4.0 |
| 2.3 Goods and services | 193.6 | 180.1 | −13.5 |
| 2.5 Other spending | 25.9 | 26.3 | +0.4 |
| 2.6 Non-financial assets (investment) | 53.9 | 50.1 | −3.8 |
| Total | 671.3 | 677.7 | +6.5 |

Million soles. MEF codes each line by its spending group (genérica).

![Where San Marcos' budget comes from](https://research.rising.sh/peru-universities-budget/funding.svg)

## All public universities

![Public universities' opening budget from ordinary resources](https://research.rising.sh/peru-universities-budget/ordinary.svg)

Ordinary resources are the Treasury's money. Their opening budget for public
universities rose from S/ 1,732 million in 2012 to S/ 5,096 million in 2024.
It fell in 2025 and again in 2026.

![How much of their 2025 budget universities spent](https://research.rising.sh/peru-universities-budget/execution.svg)

![How much of their 2025 investment budget universities spent](https://research.rising.sh/peru-universities-budget/investment.svg)

Investment is where universities leave money unspent. Of the twenty largest
investment budgets in 2025, the Universidad Nacional de San Antonio Abad del
Cusco had the largest, S/ 139.9 million, and spent 56.4% of it. The
Universidad Nacional Toribio Rodríguez de Mendoza de Amazonas spent all of
S/ 97.4 million. [`numbers.json`](numbers.json) lists every university.

## The pace of 2026

![How fast San Marcos spends its budget](https://research.rising.sh/peru-universities-budget/pace.svg)

The chart counts spending accrued since January against the year's budget
after changes. The last month of 2026 is partial: MEF adds each day's
spending as it comes.

## Limits

- **Current soles.** Amounts are not adjusted for inflation.
- **Budget, not results.** The data says how much a university spent on each
  spending group, not what it bought or how well.
- **Accrual.** Spending accrued (devengado) counts goods received and work
  done. Money committed but not yet accrued is not counted as spent.
- **Universities.** The figures count every pliego from 510 to 583 in the
  education sector, which are the public universities, except 540, the
  Asamblea Nacional de Rectores that SUNEDU replaced in 2014. Universities
  created since 2012 appear from their first budget.
- **2026.** The PIM and spending of 2026 change until the year closes.

## Data

MEF's open data portal publishes the
[comparison of budget and spending](https://datosabiertos.mef.gob.pe) as three
zips of five years each, 2012 to 2026, refreshed monthly, and one daily file
per year from 2025. The 2022 to 2026 zip of 2026-10-22 repeats each row's 2025
figures in its 2026 columns, so 2026 comes from the daily file.
Both files hold 2025: their spending for all public universities agrees
within S/ 816 of S/ 6,967 million.

## Reproduce

[`peru_universities_budget.py`](peru_universities_budget.py) charts the
committed tables, [`budget.csv`](budget.csv) by year, university, funding,
spending group and project type, and [`monthly.csv`](monthly.csv), spending
by month for 2025 and 2026. `--fetch` rebuilds the tables from MEF; it
streams about 5 GB and takes ten minutes. The rerun workflow fetches each
Monday.

```bash
mise run install
uv run studies/peru-universities-budget/peru_universities_budget.py --fetch
```
