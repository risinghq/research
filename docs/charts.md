# Charts

Every figure in an article is a chart file, `NAME.json`, beside its README. The
article's script writes it through the `figures` package. research.rising.sh
draws each file twice at build time: as the interactive chart on the article's
page, and as a static SVG at `https://research.rising.sh/SLUG/NAME.svg`.

A README shows a figure by linking that SVG:

```markdown
![Yearly and median-day HHI, 2010 to 2026](https://research.rising.sh/bvl-brokers/hhi.svg)
```

The site replaces the image with the interactive chart from `NAME.json` and
fails the build when the file is missing. GitHub shows the SVG, so the README
reads the same in both places. The repository holds no images.

## Fields

| Field      | Value                                                                    |
| ---------- | ------------------------------------------------------------------------ |
| `kind`     | `line`, `columns` (vertical), `bars` (horizontal) or `scatter`           |
| `title`    | The chart title                                                          |
| `subtitle` | What a value measures: frequency, adjustment, base, how to read marks    |
| `source`   | The source line, without a "Source:" prefix                              |
| `unit`     | `%` follows a value, `$` precedes it, a word such as `jobs` follows it; empty for a bare number such as an index |
| `decimals` | The decimals a value is shown with                                       |
| `x`        | The x axis, below                                                        |
| `series`   | `{label, points}`, one or more; a line chart draws one line per series   |
| `view`     | Optional. The first x the chart opens on                                 |
| `compare`  | Optional. `{label, points}` of `{x, y}`: another set of values drawn beside the first series, such as the values a replicated post published |
| `marks`    | Optional. `{x, label}`: a labelled vertical rule at an x of the series   |
| `span`     | Optional. `{from, to, label}`: a shaded band between two x of the series |

The x axis is one of:

- `{"kind": "period"}`: `x` is `YYYY`, `YYYY-Qn`, `YYYY-MM` or `YYYY-MM-DD`.
  Points are placed in order, one step each, so every series of the chart has
  the same periods.
- `{"kind": "number", "label", "unit", "decimals"}`: `x` is a number, placed by
  its value.
- `{"kind": "category"}`: `x` is a label, placed in order.

A point is `{x, y}`, oldest or first first, with these optional keys:

| Key           | Meaning                                                           |
| ------------- | ----------------------------------------------------------------- |
| `preliminary` | The source marks the value preliminary; the chart marks it too    |
| `low`, `high` | A whisker, such as a 95% interval, on a `bars` chart              |
| `size`        | A scatter point's area, relative to the other points              |
| `name`        | A scatter point's label in the readout                            |

A `y` is null where the source published nothing, such as the months BLS did
not collect during the October 2025 lapse in appropriations; the chart leaves
a gap there. A readout shows a sign on every value when any `y` is negative.

`figures` rounds `y` to six significant digits and snaps a mark or a span to
the first x of the series on or after its date, so a weekly line can carry a
mark for any day.
