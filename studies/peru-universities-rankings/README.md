---
summary: How many global university rankings place each Peruvian university first in Peru, in Peru's top three or anywhere, counted from 13 named rankings and set beside the table Percy Mayta-Tristán posted.
topic: peru-universities
status: finished
published: 2026-11-20
data: 2026-11-18
replicates: https://x.com/MaytaTristan/status/2123099835351888118
original: Universidades peruanas con mayor presencia en rankings globales el 2026
author: Percy Mayta-Tristán
outlet: X
posted: 2026-11-18
---

# Peruvian universities in global rankings

On 2026-11-18 Percy Mayta-Tristán posted a table of eleven Peruvian
universities. For each one it counts the global rankings that place it first
in Peru, in Peru's top three, and anywhere in the ranking. The post does not
list the rankings it counts.

This study counts the same three things over 13 named rankings, each at its
latest edition published on or before 2026-11-18. [`ranks.csv`](ranks.csv)
holds every Peru rank the counts use, with the rank the ranking publishes and
a link to the page it was read from. Universities that share a rank share
their place in Peru: in QS 2027, Científica and the Universidad de Lima are
both fourth.

![Rankings that place the university first in Peru](https://research.rising.sh/peru-universities-rankings/leader.svg)

PUCP is first in Peru in 8 of the 13 rankings and Cayetano Heredia in 4. The
thirteenth, uniRank, places the Universidad Tecnológica del Perú first, a
university the post does not list.

![Rankings that place the university in Peru's top three](https://research.rising.sh/peru-universities-rankings/top3.svg)

![Rankings that include the university](https://research.rising.sh/peru-universities-rankings/present.svg)

| Short name | University                                            |
| ---------- | ----------------------------------------------------- |
| PUCP       | Pontificia Universidad Católica del Perú              |
| UPCH       | Universidad Peruana Cayetano Heredia                  |
| UNMSM      | Universidad Nacional Mayor de San Marcos              |
| Científica | Universidad Científica del Sur                        |
| UPC        | Universidad Peruana de Ciencias Aplicadas             |
| UNALM      | Universidad Nacional Agraria La Molina                |
| UPN        | Universidad Privada del Norte                         |
| Pacífico   | Universidad del Pacífico                              |
| ULima      | Universidad de Lima                                   |
| USMP       | Universidad de San Martín de Porres                   |
| UNTRM      | Universidad Nacional Toribio Rodríguez de Mendoza     |
| UTP        | Universidad Tecnológica del Perú                      |

## Rankings counted

| Ranking | Edition | What orders it |
| ------- | ------- | -------------- |
| [SCImago Institutions Rankings](https://www.scimagoir.com/rankings.php?sector=Higher%20educ.&country=PER) | 2026 | Research, innovation and web visibility, higher education sector |
| [Webometrics](https://doi.org/10.6084/m9.figshare.33062150.v3) | 2026, July | Web presence and citations; the Figshare edition, CC BY 4.0 |
| [CWTS Leiden Ranking Open Edition](https://open.leidenranking.com/ranking/2026/list) | 2026 | Publications (P), 2021 to 2024, all sciences, at least 100; CC0 |
| [QS World University Rankings](https://www.topuniversities.com/world-university-rankings?countries=pe) | 2027 | Reputation, citations and ratios |
| [CWUR](https://cwur.org/2026.php) | 2026 | Education, employability, faculty and research |
| [U.S. News Best Global Universities](https://www.usnews.com/education/best-global-universities/search?country=peru) | 2026-2027 | Research and reputation |
| [NTU Ranking](https://nturanking.csti.tw/ranking/ByCountry/2026/PE) | 2026 | Scientific papers |
| [MosIUR Three University Missions](https://mosiur.org/ranking/) | 2026 | Education, research and the university's role in society |
| [Nature Index](https://www.nature.com/nature-index/institution-outputs/generate/all/countries-Peru/all) | 1 July 2025 to 30 June 2026 | Share of articles in its journals; CC BY-NC-SA 4.0 |
| [Round University Ranking](https://roundranking.com/ranking/world-university-rankings.html) | 2026 | Teaching, research, international diversity and finances |
| [UI GreenMetric](http://web.archive.org/web/20260314234938/https://greenmetric.ui.ac.id/rankings/overall-rankings-2025) | 2025 | Campus sustainability |
| [EduRank](https://edurank.org/geo/pe/) | 2026 | Research output, influence and alumni |
| [uniRank](https://www.4icu.org/pe/) | 2026 | Web metrics |

The Nature Index lists every Peruvian institution. The Peru place here counts
universities only, so an institute, an NGO or a hospital above a university
does not move it down. Webometrics' July edition prints the top of its world
list. UNALM, Pacífico and UNTRM fall below that cut, so they count as absent.
GreenMetric's site did not answer on 2026-11-20, so its 2025 list was read
from the Internet Archive's copy.

QS World University Rankings data: Source: QS Quacquarelli Symonds
([www.qs.com](https://www.qs.com)). With permission from QS Quacquarelli
Symonds.

### Left out

- **Times Higher Education** World University Rankings 2027, Impact Rankings
  and Interdisciplinary Science Rankings. THE's terms of use forbid collecting
  its data, and it licenses the data separately.
- **QS Sustainability Rankings 2027**, published 2026-11-17. QS permits reuse
  of the World University Rankings only.
- **ARWU 2026** ranks no Peruvian university.
- **URAP** did not load on 2026-11-20.
- **AD Scientific Index** updates continuously and has no dated edition.

## What differs from the original

- **Rankings.** The original counts at least 16 rankings: PUCP alone appears
  in 16. This study counts 13 and names each one. The four rankings left out
  above account for part of the gap.
- **First place.** The original has Cayetano Heredia first in Peru in 8
  rankings and PUCP in 7. Here PUCP leads 8 and Cayetano Heredia 4. UNMSM,
  Científica and UPC each lead one ranking in the original and none here.
- **Top three.** The original places each of its eleven universities in Peru's
  top three at least once. Here UNALM, UPN, ULima, USMP and UNTRM never reach
  it.
- **Presence.** UPN, Pacífico, ULima, USMP and UNTRM appear in more rankings
  here than in the original. EduRank and uniRank include all five.
- **Universities.** uniRank places UTP first in Peru. The original does not
  list UTP, which suggests it does not count uniRank.

## Checked against the original

The post gives counts and no ranks, so the check is by count.
[`numbers.json`](numbers.json) lists each of the original's 33 counts beside
this study's under `against_original`, and the 24 that differ under
`differs_from_post`. The 9 that match include UNMSM's 7 top-three places,
UPC's one, and Pacífico's one, which here is its third place in MosIUR.

## Reproduce

[`peru_universities_rankings.py`](peru_universities_rankings.py) reads
[`ranks.csv`](ranks.csv), counts each measure for the universities in
[`original.csv`](original.csv), which holds the post's table, and writes the
chart files [`leader.json`](leader.json), [`top3.json`](top3.json) and
[`present.json`](present.json) and [`numbers.json`](numbers.json). The ranks
were read by hand from the linked pages on 2026-11-20, and the script reads no
network.

```bash
mise run install
uv run studies/peru-universities-rankings/peru_universities_rankings.py
```
