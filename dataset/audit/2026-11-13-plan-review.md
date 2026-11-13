# Plan review, 2026-11-13

An adversarial review of plan v1 (`dataset/PLAN.md`) before any code ran. Reviewer: a separate
model instance (Claude Fable 5.2) given the plan and the eleman mechanism at `fd83674`, asked
only for problems that would invalidate the dataset, mislead the cost measurement, or let the
unattended run fail or corrupt the memory; at most eight findings. Each finding was checked
against the code before anything was changed. Verdicts: accepted, partly accepted, rejected.

The reviewer first confirmed that `lint.py` and `sleep-audit.py` never read the system clock;
dates are only shape-checked, so 2000-era dates, English content and `<date>--mail.md` names do
not break either gate on their own. Verified: neither file imports `datetime` or `time`.

| # | Finding | Verdict | What changed |
|---|---|---|---|
| 1 | The outside gate re-run is vacuous: after the model commits, `sleep-audit.py` without arguments sees no diff and says green; a run that reset itself and committed nothing would be tagged as a success. | Accepted (verified, `sleep-audit.py` main) | `run.sh` records the feed commit, sets the `pre-sleep` tag itself, audits the run's own commit by sha (`--last <sha>`), and fails the batch if the run made no commit, left inbox files or left the tree dirty. |
| 2 | The people index ceiling (2,900 characters, roughly 30 people) will be hit inside the pilot; a full ceiling turns lint red or quietly stops entity creation. | Accepted (verified, `format.md` lint-config) | `people_index` raised to [5000, 6500] in the `lint-config` block before batch 1, recorded as a deviation. Domain index budgets left as shipped; watched in the pilot. |
| 3 | FABRICATION only tests whether a bracket date occurs in the raw text: a fact dated by an event in an email body goes red early, and late in the run almost any date passes. | Accepted | The preamble says a fact's bracket date is the date of the message that reported it; event dates go in the prose. Each block also carries an ISO `Date:` line. FABRICATION is reported in the pilot as a date-presence check only. |
| 4 | Real-clock dates outside fact lines (`updated:`, questions, logs the run writes) are checked by nothing, and once archived they are immutable. | Accepted | `date_leaks.py` fails the batch on any date outside [first message, simulated today] in the memory core, outside fenced message bodies and outside `rules/`, `tools/`, `secret/`. The preamble sends the run's own log lines to `<today>--mail.md`. |
| 5 | A calendar day split across two batches collides in the archive; the time zone of file days is unspecified. | Partly accepted | `feed.py` names the continuation `<day>--mail-2.md` itself, so the archive move is a plain rename. File days stay in the time zone written in each message's own header (the CMU release normalised headers to US Pacific time); the manifest also carries UTC. Checked on the built stream (see `dataset/README.md`). |
| 6 | Cost will be understated: per-run cost grows with the memory; `sonnet` is an alias; the budget cap can kill a run mid-pass; a large batch can force context compaction. | Accepted | Full model ID passed; per-model usage and CLI version stored per run; projection uses the trend and the last runs, failed runs included; a killed run stops the pipeline (finding 1's guard); characters per batch recorded in the manifest. |
| 7 | `questions.md` from the template says "Cap: 5 items", contradicting `format.md` (no cap) and the plan's reliance on approval items piling up. | Accepted (verified, `setup/templates/questions.md`) | `questions.md` written by hand without the cap sentence. The template bug is reported upstream. |
| 8 | Raw mail in the inbox is link-checked and marker-scanned; a body with `[[...]]`, a `memory/...md` string, a `## ` line, `(sleep-task)` or `(feedback)` can turn a run red with no legal repair; non-UTF-8 bytes crash lint. | Accepted | Bodies are fenced (fence longer than any backtick run; lint skips fenced code); bytes are decoded once as Windows-1252 with replacement and written as UTF-8; lint runs after every feed, before any model sees the batch. Marker counts for the chosen mailbox are in `dataset/README.md`. |

Open after review: whether `--setting-sources project` keeps Claude Code's per-user
auto-memory out of the run. Checked empirically after batch 1 (`dataset/README.md`).
