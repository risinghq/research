# sbs

[`sbs`](../packages/sbs/sbs.py) reads the monthly workbooks of Peru's
Superintendencia de Banca, Seguros y AFP (SBS): one workbook per system,
report and month, one column per firm. The
[`peru-microfinance-profits`](../studies/peru-microfinance-profits) study
uses it.

## Files

A workbook's path is
`https://intranet2.sbs.gob.pe/estadistica/financiera/{year}/{Mes}/{code}-{mm}{year}.XLS`.
The month folder is the Spanish name, with "Setiembre" for September, and `mm`
is its two-letter short form; `sbs.file_path` builds it.

| System | Statements | Indicators |
| --- | --- | --- |
| Cajas municipales | C-1101 | C-1301 |
| Cajas rurales | C-2101 | C-2301 |
| Empresas financieras | B-3101 | B-3301 |
| Empresas de crédito (EDPYMEs to 2021) | C-4103 | C-4301 |

## Download

The site sits behind Incapsula, which answers curl and httpx with a challenge
page, and it drops connections now and then. A real browser passes. Open any
page of `intranet2.sbs.gob.pe` in `cap browser`, then fetch each file from that
page, same origin, as base64:

```bash
cap browser --host mathew act --act open https://intranet2.sbs.gob.pe/estadistica/financiera/
cap browser --host mathew eval --act --out C-1101-se2026.b64 "fetch('/estadistica/financiera/2026/Setiembre/C-1101-se2026.XLS').then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.arrayBuffer()}).then(b=>{let s='';const u=new Uint8Array(b);for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)})"
tr -d '"\n' < C-1101-se2026.b64 | base64 -d > C-1101-se2026.xls
```

Retry a file that fails; the next request usually passes.

## Reading

- Every file is named `.XLS`, but some are Excel 2007 workbooks. `sbs.grids`
  reads a file by its first bytes, whatever its extension.
- Net profit is "UTILIDAD (PÉRDIDA) NETA" to 2012 and "RESULTADO NETO DEL
  EJERCICIO" from 2013. It is in thousands of soles, year to date.
- Return on equity annualises profit as the month plus the previous December
  minus the same month a year before, over average equity of the last twelve
  months, as the indicators sheet's footnote states.
- The statements and indicators of the same month spell some firms
  differently; `sbs.SPELLINGS` maps them to the indicators' names.
- A firm that stopped reporting keeps a column of zeros.
- "TOTAL Servicios Financieros" is a firm, not a sum; `sbs.is_aggregate` tells
  them apart.
