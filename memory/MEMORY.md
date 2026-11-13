# MEMORY — entry point

Owner: Vince Kaminski, an Enron Corp. employee. This memory is built by replaying the owner's
mailbox (`kaminski-v`, CMU Enron release) in arrival order. Mail the owner sent is the owner's own
statement; mail the owner received is third-party.
Language: English. Write memory content and replies in English; structure stays English.
If something is not in memory, say so plainly. Never invent a fact.
Current context: memory/state.md (read it first on any memory-related task).

## Domains

| Domain | Scope | Entry |
|---|---|---|
| work | the owner's own projects, models, deals, decisions, research output | memory/domains/work/_index.md |
| organization | company structure, teams, hiring, policies, announcements | memory/domains/organization/_index.md |
| industry | markets, regulation, conferences, outside institutions | memory/domains/industry/_index.md |
| personal | anything private that appears in the mail | memory/domains/personal/_index.md |

People and organisations: memory/people/_index.md

## Protocol

1. READ: open the `_index.md` of the matching domain, then follow the full path on the line.
   Never read a folder wholesale; read a file under 600 tokens in full.
1b. STATUS QUESTION ("did it arrive / what happened / where does it stand / what's on me"):
   read `memory/inbox/` plus the last two days of `memory/archive/inbox/` first. An
   "Open/TODO" line in a dated document is a snapshot, not live truth; never answer from one
   file alone. **An external task or calendar list is a snapshot too:** never build an
   "outstanding work" list from it without checking it against the inbox first — today's log
   may already say the task is done. The same applies when you **build a plan**: on a project
   that runs across several sessions, never assemble the work list from a single source —
   scan every inbox file of that day for the project's name.
2. If a person or organisation is involved, check the alias table in memory/people/_index.md.
3. On a miss, search domain-scoped: `rg -m 20 "<term>" -g 'memory/domains/<d>/**'`
   (try the other languages this memory uses). Repo-wide search only with cross-domain intent.
4. Still nothing → say it is not in memory; offer the nearest partial match.
5. WRITE: add new information ONLY to `memory/inbox/<today>--<machine>.md` (append-only).
   Never edit domain or people files during a conversation; consolidation does that.
6. Schemas and grammar: memory/rules/format.md
7. TODO: memory/todo.md — a deliberately minimal list; items carry `[[wikilinks]]`.
8. SESSION START: `sh memory/tools/sleep-check.sh` — if it prints SLEEP DUE, run a
   consolidation (memory/rules/consolidation.md) before the real work.
