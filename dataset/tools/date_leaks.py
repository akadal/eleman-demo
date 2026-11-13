#!/usr/bin/env python3
"""date_leaks.py: find dates in the memory core that the simulated clock cannot have produced.

A replayed mailbox lives in the past. Any ISO date after the simulated today, or before the
first message, came from the machine's real clock (or was invented), and once it lands in the
archive it is immutable and poisons later fabrication checks. The mechanism's own files
(rules/, tools/, secret/) are exempt: they carry the real dates of their authoring.

  python date_leaks.py --today 2000-03-14 --first 1999-12-02
Prints JSON {"count": n, "examples": [...]}; exit 1 if n > 0.
"""
import argparse
import json
import re
import sys
from pathlib import Path

MEM = Path(__file__).resolve().parents[2] / "memory"
EXEMPT = {"rules", "tools", "secret"}
DATE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--today", required=True)
    p.add_argument("--first", required=True)
    a = p.parse_args()
    hits = []
    for f in sorted(MEM.rglob("*.md")):
        rel = f.relative_to(MEM)
        if rel.parts[0] in EXEMPT:
            continue
        for d in DATE.findall(rel.name):
            if not (a.first <= d <= a.today):
                hits.append(f"name {rel}")
        fence = None  # message bodies are fenced (feed.py) and may quote any date: skip them
        for n, ln in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = re.match(r"^(`{3,})", ln)
            if m:
                if fence is None:
                    fence = m.group(1)
                elif ln.strip() == fence:
                    fence = None
                continue
            if fence:
                continue
            for d in DATE.findall(ln):
                if not (a.first <= d <= a.today):
                    hits.append(f"{rel.as_posix()}:{n} {d}")
    print(json.dumps({"count": len(hits), "examples": hits[:20]}))
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
