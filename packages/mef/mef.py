"""Client for MEF's open budget data at `datosabiertos.mef.gob.pe`.

The dataset "Comparación de Presupuesto y Ejecución de Gasto" is Consulta
Amigable's line-item table: one row per executing unit, program, purpose,
funding source and spending classifier, with each year's budget and execution
in its own columns. MEF splits it into three zips of five years, each over a
gigabyte. Each zip holds one CSV, UTF-8 with a byte-order mark, every value
quoted. A client streams a zip and keeps the rows it needs, so nothing large
reaches the disk.

The 2022-2026 zip of 2026-10-22 repeats each row's 2025 figures in its 2026
columns, on every row. The open year comes instead from the daily file,
`{year}-Gasto-Diario.zip`: one zip per year, refreshed daily, of a CSV with
one row per line item and month and the stages in `MONTO_` columns. MEF also
serves the CSV unzipped, fifteen times larger.
Summing a line item's months gives its year. MEF publishes daily files for
2025 on, and 2025's agrees with the zip.
"""

import csv
import struct
import zlib

from typing import TYPE_CHECKING

import httpx2


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

BASE_URL = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/"
USER_AGENT = "risinghq-research (+https://github.com/risinghq/research)"
# MEF refreshes the newest span monthly; the older ones are closed years.
SPANS = {
    (2012, 2016): "comparativo_gastos_2012_2016.zip",
    (2017, 2021): "comparativo_gastos_2017_2021.zip",
    (2022, 2026): "comparativo_gastos_2022_2026.zip",
}
# Budget and execution stages, in the order each year's columns appear. PIA is
# the opening budget, PIM the budget after the year's changes, and DEVENGADO
# the spending accrued: goods received or work done.
STAGES = (
    "PIA",
    "PIM",
    "CERTIFICADO",
    "COMPROMETIDO_ANUAL",
    "COMPROMETIDO",
    "DEVENGADO",
    "GIRADO",
)
_LOCAL_HEADER = b"PK\x03\x04"
_DEFLATE = 8


def entry_offset(head: bytes) -> int:
    """Where the first entry's compressed data starts in a zip that begins with
    `head`: after the 30-byte local header, the name and the extra field."""
    if head[:4] != _LOCAL_HEADER:
        raise ValueError("not a zip local file header")
    (method,) = struct.unpack("<H", head[8:10])
    if method != _DEFLATE:
        raise ValueError(f"entry compressed with method {method}, not deflate")
    name, extra = struct.unpack("<HH", head[26:30])
    return 30 + int(name) + int(extra)


def inflate(chunks: Iterable[bytes]) -> Iterator[bytes]:
    """The first entry of a zip read as a stream of chunks. MEF's zips hold a
    single entry, so its end is the end of the deflate stream."""
    inflater = zlib.decompressobj(-zlib.MAX_WBITS)
    head = b""
    started = False
    for chunk in chunks:
        if not started:
            head += chunk
            if len(head) < 30:
                continue
            offset = entry_offset(head)
            if len(head) < offset:
                continue
            chunk = head[offset:]
            started = True
        yield inflater.decompress(chunk)
        if inflater.eof:
            return
    yield inflater.flush()


def lines(data: Iterable[bytes]) -> Iterator[str]:
    """The text lines of a UTF-8 stream, without the byte-order mark."""
    rest = b""
    first = True
    for chunk in data:
        rest += chunk
        *whole, rest = rest.split(b"\n")
        for line in whole:
            text = line.decode("utf-8-sig" if first else "utf-8").rstrip("\r")
            first = False
            yield text
    if rest:
        yield rest.decode("utf-8-sig" if first else "utf-8").rstrip("\r")


def records(
    text: Iterable[str], keep: Callable[[str], bool]
) -> Iterator[dict[str, str]]:
    """The rows whose raw line passes `keep`, as dicts keyed by the header.
    Testing the raw line first skips parsing the millions of rows a study does
    not need. MEF's values hold no line breaks, so a line is a row."""
    it = iter(text)
    header = next(csv.reader([next(it)]))
    for line in it:
        if not line or not keep(line):
            continue
        row = next(csv.reader([line]))
        if len(row) != len(header):
            raise ValueError(f"row has {len(row)} fields, header {len(header)}")
        yield dict(zip(header, row, strict=True))


def years(row: dict[str, str]) -> Iterator[tuple[int, dict[str, float]]]:
    """Each year of a row with its stages, `PIA_2024` read as 2024's PIA."""
    found = sorted({int(key[-4:]) for key in row if key.startswith("PIA_")})
    for year in found:
        yield year, {stage: amount(row[f"{stage}_{year}"]) for stage in STAGES}


def amount(value: str) -> float:
    """A stage's soles. The 2012-2016 file leaves 2013's PIA and PIM empty on
    rows with no 2013 money at all, so empty is zero."""
    return float(value) if value else 0.0


class MefClient:
    def __init__(self, *, transport: httpx2.BaseTransport | None = None) -> None:
        self._http = httpx2.Client(
            base_url=BASE_URL,
            timeout=httpx2.Timeout(120, read=600),
            transport=transport,
            headers={"User-Agent": USER_AGENT},
        )

    def close(self) -> None:
        self._http.close()

    def modified(self, span: tuple[int, int]) -> str:
        """The span file's `Last-Modified` header, the date MEF last refreshed it."""
        response = self._http.head(SPANS[span])
        response.raise_for_status()
        return response.headers["Last-Modified"]

    def rows(
        self, span: tuple[int, int], keep: Callable[[str], bool]
    ) -> Iterator[dict[str, str]]:
        """The rows of a span whose raw line passes `keep`."""
        with self._http.stream("GET", SPANS[span]) as response:
            response.raise_for_status()
            chunks = response.iter_bytes(1 << 20)
            yield from records(lines(inflate(chunks)), keep)

    def daily_modified(self, year: int) -> str:
        """The daily file's `Last-Modified` header."""
        response = self._http.head(daily_file(year))
        response.raise_for_status()
        return response.headers["Last-Modified"]

    def daily(self, year: int, keep: Callable[[str], bool]) -> Iterator[dict[str, str]]:
        """The rows of a year's daily file whose raw line passes `keep`, one per
        line item and month."""
        with self._http.stream("GET", daily_file(year)) as response:
            response.raise_for_status()
            chunks = response.iter_bytes(1 << 20)
            yield from records(lines(inflate(chunks)), keep)


def daily_file(year: int) -> str:
    return f"{year}-Gasto-Diario.zip"


def monthly(row: dict[str, str]) -> dict[str, float]:
    """A daily file row's stages, `MONTO_PIA` read as PIA."""
    return {stage: amount(row[f"MONTO_{stage}"]) for stage in STAGES}
