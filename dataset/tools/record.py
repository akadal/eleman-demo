#!/usr/bin/env python3
"""record.py: one JSON record per consolidation, printed to stdout (run.sh writes it to
dataset/runs/sleep-kk.json). Reads the harness's own JSON output for tokens and cost, and
measures the memory core on disk. Stdlib only.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEM = ROOT / "memory"


def size(paths):
    files = [p for p in paths if p.is_file() and p.suffix == ".md"]
    return {"files": len(files), "chars": sum(len(p.read_text(encoding="utf-8")) for p in files)}


def layer_sizes():
    return {
        "root": size([MEM / "MEMORY.md"]),
        "state": size([MEM / "state.md"]),
        "questions": size([MEM / "questions.md"]),
        "todo": size([MEM / "todo.md"]),
        "domains": size(list((MEM / "domains").rglob("*.md"))),
        "people": size(list((MEM / "people").rglob("*.md"))),
        "archive_inbox": size(list((MEM / "archive" / "inbox").glob("*.md"))),
        "archive_other": size([p for p in (MEM / "archive").rglob("*.md")
                               if "inbox" not in p.relative_to(MEM / "archive").parts[:1]]),
    }


def open_questions():
    q = MEM / "questions.md"
    if not q.exists():
        return 0
    return sum(1 for ln in q.read_text(encoding="utf-8").splitlines()
               if re.match(r"^- \[\d{4}-\d{2}-\d{2}\] ", ln))


def harness(kk):
    p = ROOT / "dataset" / "runs" / f"sleep-{kk}.claude.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"parse_error": True}
    keep = ("subtype", "is_error", "num_turns", "duration_ms", "duration_api_ms",
            "total_cost_usd", "usage", "modelUsage", "stop_reason")
    out = {k: d.get(k) for k in keep if k in d}
    out["result_summary"] = (d.get("result") or "")[:2000]
    return out


def main():
    p = argparse.ArgumentParser()
    for k in ("kk", "feed", "today", "exit", "seconds", "quota-before", "quota-after", "lint",
              "audit", "commits", "dirty", "inbox-left", "date-leaks"):
        p.add_argument("--" + k, default="")
    a = p.parse_args()

    def js(s):
        try:
            return json.loads(s)
        except ValueError:
            return s or None

    cli = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    rec = {
        "sleep": int(a.kk),
        "simulated_today": a.today,
        "feed": js(a.feed),
        "harness_cli": cli,
        "exit_code": int(a.exit or -1),
        "wall_seconds": int(a.seconds or 0),
        "quota_before": js(a.quota_before),
        "quota_after": js(a.quota_after),
        "gates": {"lint": a.lint, "sleep_audit": a.audit},
        "commits_by_run": int(a.commits or 0),
        "dirty_files_after": int(a.dirty or 0),
        "inbox_files_left": int(a.inbox_left or 0),
        "date_leaks": js(a.date_leaks),
        "open_questions": open_questions(),
        "sizes": layer_sizes(),
        "harness": harness(a.kk),
    }
    sys.stdout.reconfigure(encoding="utf-8", newline="
")  # Windows consoles default to cp1252
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
