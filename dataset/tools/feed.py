#!/usr/bin/env python3
"""feed.py: append one batch of the message stream to memory/inbox/, like a read tap.

The feed writes and does not think: no summarising, no filtering, no model. Batch k holds
messages 100(k-1)+1 .. 100k of the stream built by build_stream.py, in stream order, one inbox
file per calendar day (the date as written in the message's own Date header), one `## HH:MM`
block per message. The body sits in a code fence longer than any backtick run inside it, so
nothing in an email can open a markdown heading, close the block, or be read by lint as a link
(lint skips fenced code), and the text reads as material, not as instructions.

A calendar day can straddle two batches. Its first part is archived by the earlier
consolidation; the later part then goes to `<day>--mail-2.md` (then -3, ...), so the archive move
is always a plain rename and never a name collision (rules/consolidation.md, close-out).

  python feed.py --cache <dir>/<owner>.jsonl --batch 3 [--size 100] [--cap 6000]

Prints a JSON line: first/last seq, first/last date, files touched, characters written.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "memory" / "inbox"
ARCHIVE = ROOT / "memory" / "archive" / "inbox"
MACHINE = "mail"
MAX_ADDR = 10


def addrs(lst):
    if len(lst) <= MAX_ADDR:
        return ", ".join(lst)
    return ", ".join(lst[:MAX_ADDR]) + f" (+{len(lst) - MAX_ADDR} more)"


def fence_for(text):
    longest = max((len(r) for r in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def block(m, cap):
    body = m["body"]
    note = ""
    if len(body) > cap:
        note = f"\n[truncated at {cap} of {len(body)} characters]"
        body = body[:cap]
    fence = fence_for(body)
    quoted = f"{fence}text\n{body or '(empty body)'}\n{fence}"
    head = [
        f"## {m['local'][11:16]}",
        "",
        f"(mail · {m['direction']} · {m['path']})",
        f"Date: {m['local']} · {m['date']}",
        f"From: {addrs(m['from'])}" + (f" ({m['x_from']})" if m["x_from"] else ""),
        f"To: {addrs(m['to'])}",
    ]
    if m["cc"]:
        head.append(f"Cc: {addrs(m['cc'])}")
    head.append(f"Subject: {m['subject'] or '(no subject)'}")
    return "\n".join(head) + "\n\n" + quoted + note + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cache", required=True)
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--cap", type=int, default=6000)
    a = p.parse_args()

    lo, hi = (a.batch - 1) * a.size + 1, a.batch * a.size
    msgs = []
    with open(a.cache, encoding="utf-8") as f:
        for line in f:
            m = json.loads(line)
            if lo <= m["seq"] <= hi:
                msgs.append(m)
    if not msgs:
        sys.exit(f"batch {a.batch} is empty")

    INBOX.mkdir(parents=True, exist_ok=True)
    touched, chars = [], 0
    def target(day):
        """The inbox file for this day: a fresh suffix if earlier parts are already archived."""
        n = 1
        while (ARCHIVE / name(day, n)).exists():
            n += 1
        return INBOX / name(day, n)

    def name(day, n):
        return f"{day}--{MACHINE}.md" if n == 1 else f"{day}--{MACHINE}-{n}.md"

    for m in msgs:
        day = m["local"][:10]
        path = target(day)
        text = ""
        if not path.exists():
            text = (f"---\ntype: log\ndate: {day}\nmachine: {MACHINE}\n---\n"
                    f"# {day} ({MACHINE})\n")
        text += "\n" + block(m, a.cap)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(text)
        chars += len(text)
        if path.name not in touched:
            touched.append(path.name)
    print(json.dumps({"batch": a.batch, "first_seq": msgs[0]["seq"], "last_seq": msgs[-1]["seq"],
                      "first_date": msgs[0]["local"], "last_date": msgs[-1]["local"],
                      "files": touched, "chars": chars}))


if __name__ == "__main__":
    main()
