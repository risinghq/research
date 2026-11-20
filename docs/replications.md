# Replications

A replication rebuilds a chart that an author or a newsroom published, from
the public data it was drawn from. It links the original and does not copy its
image. The reader gets the same chart, the author's choices made visible, and
every month published since.

A replication is a study like any other: a folder under `studies/` with a
README, a script, its numbers, its figures and a test. It differs in three
places.

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

## Chart file

A figure `NAME.png` with a sibling `NAME.json` is drawn on research.rising.sh
as an interactive chart; the PNG remains for GitHub and as the fallback. The
JSON holds:

| Field      | Value                                                                  |
| ---------- | ---------------------------------------------------------------------- |
| `kind`     | `columns`                                                              |
| `title`    | The chart title                                                        |
| `subtitle` | The frequency and adjustment                                           |
| `unit`     | What one unit of `value` counts, such as `jobs`                        |
| `source`   | The source line                                                        |
| `view`     | The first period the chart opens on: the original's first period       |
| `points`   | `{period, value, preliminary}`, oldest first; `period` is `YYYY-MM`    |
| `compare`  | `{label, points}`: the values the original published, drawn beside it  |

## Rerun

[`.github/workflows/rerun.yml`](../.github/workflows/rerun.yml) runs each live
replication on weekdays after the BLS release time and commits what changed.
master requires signed commits, so the job commits through the GraphQL API,
which signs the commit, rather than pushing from git. A rerun on unchanged data
writes identical files and commits nothing. research.rising.sh picks up the
commit with its next submodule update.

The BLS client needs no key. A repository secret `BLS_API_KEY` holding a BLS
registration key raises the limit from 25 to 500 requests a day.
