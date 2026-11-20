# Replications

A replication rebuilds a chart that an author or a newsroom published, from
the public data it was drawn from. It links the original and does not copy its
image. The reader gets the same chart, the author's choices made visible, and
every month published since.

A replication is a study like any other: a folder under `studies/` with a
README, a script, its numbers and its figures. It differs in four places.

## Front matter

Besides the keys every study has, a replication's README names the original:

| Key          | Value                                          |
| ------------ | ---------------------------------------------- |
| `replicates` | The URL of the original post                   |
| `original`   | Its headline                                   |
| `author`     | Its byline                                     |
| `outlet`     | The publication                                |
| `posted`     | The day it was published, `YYYY-MM-DD`         |

The script rewrites the `data` line to the last day its numbers cover. The
README has a section "What differs from the original": the periods shown,
revisions since the post, and any choice the original made that the
replication does not.

## Original values

`original.csv` holds the values the post published, with the columns `period`
and `value`, as read from the post's chart data. A script never edits it.
`numbers.json` compares each of them with the current value under
`against_original`, and lists under `revised_since_post` those that differ at
the precision the original published: a posted 0.4 is not revised by a current
0.35028, which rounds to it. A period with no current value counts as revised.

The `replication` package writes the chart file, `numbers.json`, the figure and
the `data` date from a study's points and its original, so a study script only
fetches the series and computes its values.

## Chart file

A figure `NAME.png` with a sibling `NAME.json` is drawn on research.rising.sh
as an interactive chart; the PNG remains for GitHub and as the fallback. The
JSON holds:

| Field      | Value                                                                  |
| ---------- | ---------------------------------------------------------------------- |
| `kind`     | `columns` for changes, `line` for levels or long spans                 |
| `title`    | The chart title                                                        |
| `subtitle` | The frequency and adjustment                                           |
| `unit`     | `%` follows a value, `$` precedes it, a word such as `jobs` follows it |
| `decimals` | The decimals a value is shown with                                     |
| `source`   | The source line                                                        |
| `view`     | The first period the chart opens on: the original's first period       |
| `points`   | `{period, value, preliminary}`, oldest first, one for every period     |
| `compare`  | `{label, points}`: the values the original published, drawn beside it  |

A `period` is `YYYY-MM` for a month or `YYYY-Qn` for a quarter. A `value` is
null for a period the source published nothing for, such as the months BLS
did not collect during the October 2025 lapse in appropriations; the chart
leaves a gap there.

## Rerun

[`.github/workflows/rerun.yml`](../.github/workflows/rerun.yml) runs each live
replication on weekdays after the BLS release time and commits what changed.
master requires signed commits, so the job commits through the GraphQL API,
which signs the commit, rather than pushing from git. A rerun on unchanged data
writes identical files and commits nothing. research.rising.sh picks up the
commit with its next submodule update.

The BLS client runs without a key on a local machine. The workflow needs the
repository secret `BLS_API_KEY`, a BLS registration key: BLS counts the
keyless limit of 25 requests a day per address, and GitHub's shared runners
use it up before the rerun starts. A key raises the limit to 500 a day.
