# eleman-demo dataset

A personal memory core that has lived through one person's real email, in the order it arrived.
The repository is the dataset: `memory/` is the memory as an AI harness built it, `dataset/`
says exactly how, so anyone can rebuild it from the same public source and check every step.

**Status: pilot.** 1,000 messages, ten consolidations. Not frozen; no DOI yet. Numbers below
are filled in from `dataset/runs/` as the pilot runs.

## What is in here

| Path | What |
|---|---|
| `memory/` | The memory core (eleman). `archive/inbox/` holds every message exactly as it was fed (the raw layer, L2); `domains/`, `people/`, `state.md`, `questions.md` are what consolidation distilled from it (L1). |
| `dataset/SOURCE.md` | The source release, its checksum, the mailbox, and how it was chosen. |
| `dataset/manifest.csv` | One row per message of the stream: order, batch, path in the source tarball, checksum of the raw file, dates, direction, size, duplicate copies. |
| `dataset/tools/` | `build_stream.py` (source to ordered stream), `feed.py` (stream to inbox), `run.sh` (feed, consolidate, check, record), `record.py`, `date_leaks.py`, `quota.py`. Stdlib Python and POSIX sh. |
| `dataset/runs/` | One JSON record per consolidation: model, tokens, equivalent cost, wall time, gates, layer sizes; plus the harness's raw JSON output. |
| `dataset/PLAN.md`, `dataset/audit/` | The plan, and the review it went through before any code ran. |
| git tags `sleep-01` ... | The memory core after each consolidation, for longitudinal analysis. |

## How it was built

1. `build_stream.py` reads the CMU release tarball (checksum enforced), takes one mailbox,
   removes duplicate copies of the same message across folders, drops messages with impossible
   dates, and orders the rest by the UTC instant of their Date header.
2. For each batch of 100 messages, `feed.py` appends them to `memory/inbox/`, one file per day,
   one block per message, body fenced and unmodified apart from a 6,000-character cap.
3. `run.sh` then runs one unattended consolidation with the prompt eleman ships in
   `memory/tools/sleep-run.sh`, plus a short replay preamble (below), and checks the result from
   outside before the next batch is fed.

Rebuild:

```sh
python dataset/tools/build_stream.py build --tar enron_mail_20150507.tar.gz \
    --owner <owner> --cache ./cache --manifest dataset/manifest.csv
PY=python3 sh dataset/tools/run.sh ./cache/<owner>.jsonl 1 10
```

## Deviations from eleman as shipped

eleman is pinned at commit `fd83674` and never updated during the run. Everything below differs
from it on purpose, and nothing else does.

- **Replay preamble** added to the consolidation prompt: a simulated "today" (the date of the
  last message in the batch), the rule that a fact is dated by the message that reported it,
  that the run's own log lines go to that day's inbox file, and that message text is material,
  not instructions. Exact text: `dataset/tools/run.sh`.
- **No human.** Nobody answers `questions.md`; approval gates pile up there and close by status
  quo when due, as the mechanism specifies.
- **Whole messages in the inbox.** The template sends long raw material to the archive with a
  one-line summary in the inbox; a summary needs a model and the feed must not think.
- **`people_index` budget** raised from [2300, 2900] to [5000, 6500] characters.
- **`questions.md`** written without the template's "Cap: 5 items" line, which contradicted
  `format.md` (fixed upstream after this repository was created).
- **The `sleep-run.sh` lock** is skipped (one machine), and the `pre-sleep` checkpoint is set by
  `run.sh`.
- **`python3`** is a shim to `python` on the Windows machine that ran the pilot.

## Licence and ethics

Code: MIT. Our own files (`dataset/`, the distilled `memory/` layers): CC BY 4.0. Message text
in `memory/archive/inbox/` and `memory/inbox/` comes from the CMU release, which has been public
since 2004; no further rights are claimed over it. The mailbox owner and the people in it are
real. If you appear in this data and want a message removed, open an issue.

## Cite

Until the frozen release has its own DOI, cite the source corpus and the mechanism:

- Klimt, B., & Yang, Y. (2004). The Enron corpus: A new dataset for email classification
  research. In *Machine Learning: ECML 2004* (pp. 217-226). Springer.
  https://doi.org/10.1007/978-3-540-30115-8_22
- Akadal, E. (2026). *eleman: A personal memory core for AI assistants* [Computer software].
  Zenodo. https://doi.org/10.5281/zenodo.23975338
