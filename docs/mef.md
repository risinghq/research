# mef

[`mef`](../packages/mef/mef.py) streams the open budget data of Peru's
Ministerio de Economía y Finanzas (MEF) from `datosabiertos.mef.gob.pe`. The
[`peru-universities-canon`](../studies/peru-universities-canon) and
[`peru-universities-budget`](../studies/peru-universities-budget) studies use
it. The module docstring describes the files and their quirks.

## Revenue before 2025

The open data has revenue only from 2025, in `{year}-Ingreso-Diario.zip`.
Earlier years are in
[Consulta Amigable de Ingresos](https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/default.aspx),
a page that drills down one dimension at a time. Each page takes its
selection as URL keys, and `_tgt=xls` returns the table as HTML labelled as
a spreadsheet.

| Key | Dimension | Value used |
| --- | --- | --- |
| `y` | Year | `2012` |
| `0` | Total | empty |
| `1` | Level of government | `E`, national |
| `2` | Sector | `10`, education |
| `9` | Funding rubro | `18`, canon, royalties and participations |
| `18` | Transaction type and genérica | `1-4` transfers, `1-5` other income, `1-9` balance carried over |
| `11` | Resource type | `H` mining canon, `P` mining royalties, and so on |
| `17` | Month | `1` to `12` |
| `3` | Pliego | empty, to list them |

A key with an empty value is the dimension the page lists. `3=` lists the
pliegos, and `11=` lists the resource types.

## Download

Incapsula answers curl with a challenge page. Open the navigator in
`cap browser`, then fetch each table from that page, same origin:

```bash
cap browser --host mathew act --act open https://apps5.mineco.gob.pe/transparenciaingresos/Navegador/Navegar_6.aspx
cap browser --host mathew eval --act --out transfers-2012.json "fetch('Navegar_6.aspx?_tgt=xls&_uhc=yes&0=&1=E&2=10&9=18&18=1-4&3=&y=2012').then(r=>r.text()).then(t=>{const d=new DOMParser().parseFromString(t,'text/html');const rows=[...d.querySelectorAll('tr')].map(r=>[...r.cells].map(c=>c.innerText.trim()));return rows.slice(rows.findIndex(r=>r[0]==='Pliego')+1)})"
```

A loop over years, genéricas and resource types runs longer than one eval
allows. Start it as a promise stored on `window`, then read the variable with
later evals until it is set.

## Reading

- The rows above the level header ("Pliego", "Tipo de Recurso") hold the
  totals of the selection the session viewed last, not of the URL. Read only
  the rows after the header.
- Amounts are soles with thousands separators, rounded to the sol. A
  breakdown by resource type matches the pliego total within S/ 2.
- Genérica 4 books the opening budget and the budget after changes under
  resource type 0 and the amount received under the specific types.
- The balance carried over (genérica 9) is booked as collected in the year it
  enters. One year's balance plus its income less its spending gives the next
  year's balance within 0.2%.
