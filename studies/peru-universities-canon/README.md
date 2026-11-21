---
summary: Peru's public universities spent 66% of their S/ 1,117 million canon budget in 2025, up from 13% in 2012, and left S/ 378 million unspent. Of what they spent since 2012, 80% bought buildings, equipment and other assets, and 9% went to what MEF classes as research.
topic: peru-universities
status: live
published: 2026-11-21
data: 2026-11-21
---

# How Peru's public universities spend their canon

Public universities in mining, gas and oil regions receive part of the canon,
the share of the state's resource income that goes back to those regions.
Ley 28077 of 2003 reserved the universities' share for scientific and
technological research. A
[presentation by Milton von Hesse](https://perumin.com/perumin37/public/uploads/shares/programas-doc/encuentro_academia/11_30-12_30_Milton_Von_Hesse.pdf)
at Perumin quotes the rule with infrastructure for research added.

For a decade the press has reported that universities leave most of it
unspent. [El Búho](https://elbuho.pe/archivo/2014/01/02/universidades-solo-utilizaron-un-14-de-los-fondos-de-canon-que-recibieron-para-investigacion/index.html)
reported a Contraloría note on 2013,
[ProActivo](https://proactivo.com.pe/universidades-como-aumentar-ejecucion-del-dinero-del-canon/)
an El Comercio count of 2014, and
[Gestión](https://gestion.pe/economia/snmpe-universidades-nacionales-recibieron-s-498-millones-de-canon-y-regalias-este-ano-rmmn-noticia/)
the mining society SNMPE's count of 2012 to 2021. None links a table. This
study tests their figures against the budget data of the Ministerio de
Economía y Finanzas (MEF) and shows what the money bought.

- Universities spent 66.2% of their canon budget after changes (PIM) in 2025,
  S/ 739 million of S/ 1,117 million. They spent 13.0% in 2012 and passed
  half for the first time in 2019.
- From 2012 to 2025 they spent S/ 4,867 million of canon. 79.8% bought
  non-financial assets: buildings took 43.6% of the total and machinery and
  equipment 20.7%. MEF classes 8.8% under its two research groups, applied
  and basic research.
- The press figures for 2013 and 2014 match MEF. The Contraloría's S/ 828.5
  million available in 2013 is MEF's PIM, S/ 828.8 million, though MEF's
  year-end spending gives 20.5%, not the 14.1% El Búho reported. El
  Comercio's S/ 771 million and S/ 216.2 million for 2014 match MEF to
  S/ 0.3 million and S/ 0.1 million; those two figures give 28.0%, not the
  28.5% printed. The Universidad Nacional del Santa had S/ 18.3 million and
  spent S/ 13,774.
- The SNMPE said universities received S/ 2,072 million from 2012 to 2021 and
  spent 39%. MEF shows them spending S/ 2,629 million of canon in those ten
  years, more than the SNMPE's total. The 39% matches ten years of spending
  over ten years of PIM summed, 39.3%, a sum that counts each balance again
  in every year it is carried over.

None of the reports cited here alleges misuse of funds, and this study tests
no such claim. It measures how much was budgeted, how much was spent and on
which items, not whether the spending was right.

## Budget and spending

![Public universities' canon budget and spending](https://research.rising.sh/peru-universities-canon/canon.svg)

The opening budget (PIA) is the one Congress approves in December. The budget
after changes (PIM) adds the year's changes, chiefly the balance a university
did not spend the year before. That is why the PIM runs above the PIA and why
the yearly PIMs cannot be added up as money received. 2026 runs to the date
of the data.

![How much of their canon universities spend](https://research.rising.sh/peru-universities-canon/execution.svg)

![How much of their 2025 canon universities spent](https://research.rising.sh/peru-universities-canon/universities.svg)

The Universidad Nacional de San Antonio Abad del Cusco has the largest canon
budget: S/ 162.9 million in 2025, of which it spent 60.1%. In 2014 it had
S/ 154.8 million and spent 17.0%. The Universidad Nacional de Arte Diego
Quispe Tito del Cusco spent 3.4% of S/ 30.4 million in 2025. San Marcos gets
almost no canon: S/ 92,567 in 2014. [`numbers.json`](numbers.json) lists
every university.

## What the money bought

![What universities spend their canon on](https://research.rising.sh/peru-universities-canon/uses.svg)

![What universities buy with their canon](https://research.rising.sh/peru-universities-canon/items.svg)

MEF codes each line twice: by functional group, the purpose, and by spending
item, the thing bought. Most canon spending is on projects, 69.4% of it, and
the largest are new faculties and campus buildings. The largest from 2012 to
2025 is San Antonio Abad's project for teaching, research and extension
support, S/ 126.6 million.

Regional governments also passed canon to universities as transfers. MEF
books those under donations and transfers, not under the canon, so the
charts leave them out. Their spending peaked at S/ 116.0 million in 2018, and
the last were in 2022.

## Limits

- **Current soles.** Amounts are not adjusted for inflation.
- **Classification, not content.** MEF's functional group says what a line
  is for. A building coded under university education may hold
  laboratories, and a research line may pay for equipment.
- **Accrual.** Spending accrued (devengado) counts goods received and work
  done. Money committed but not yet accrued is not counted as spent.
- **Budget, not transfers.** The data has budgets and spending, not the
  canon each university was sent in a year. The SNMPE's S/ 2,072 million and
  Gestión's yearly transfer figures cannot be tested from it.
- **Universities.** The study counts every pliego from 510 to 583 in the
  education sector, which are the public universities, except 540, the
  Asamblea Nacional de Rectores that SUNEDU replaced in 2014.
- **2026.** The PIM and spending of 2026 change until the year closes.

## Data

MEF's open data portal publishes the
[comparison of budget and spending](https://datosabiertos.mef.gob.pe) as three
zips of five years each, 2012 to 2026, and one daily file per year from 2025.
The 2022 to 2026 zip repeats each row's 2025 figures in its 2026 columns, so
the study takes 2026 from the daily file. The canon is the funding rubro
"Canon y sobrecanon, regalías, renta de aduanas y participaciones", which
also holds royalties.

## Reproduce

[`peru_universities_canon.py`](peru_universities_canon.py) charts the
committed tables: [`canon.csv`](canon.csv) by year, university, project
type, spending item and functional group, [`projects.csv`](projects.csv) by
project, and the names in [`items.csv`](items.csv),
[`project_names.csv`](project_names.csv) and
[`universities.csv`](universities.csv). `--fetch` rebuilds them from MEF; it
streams about 5 GB and takes ten minutes. The rerun workflow fetches each
Monday.

```bash
mise run install
uv run studies/peru-universities-canon/peru_universities_canon.py --fetch
```
