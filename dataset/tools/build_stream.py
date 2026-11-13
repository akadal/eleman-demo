#!/usr/bin/env python3
"""build_stream.py: turn one Enron mailbox into a de-duplicated, time-ordered message stream.

Reads the CMU release tarball directly (no extraction) and refuses any other file: the SHA-256
in dataset/SOURCE.md is the anchor that makes the dataset reproducible.

  python build_stream.py stats  --tar <tarball> --out stats.csv
      one row per mailbox: unique messages, sent share, first/last date (used to pick the owner)
  python build_stream.py build  --tar <tarball> --owner beck-s --cache <dir> --manifest <csv>
      writes <cache>/<owner>.jsonl (full messages, in stream order) and the manifest

Stdlib only. Deterministic: same tarball in, byte-identical outputs.
"""
import argparse
import csv
import email
import email.policy
import email.utils
import hashlib
import json
import os
import re
import sys
import tarfile
from collections import defaultdict
from datetime import datetime, timezone

SHA256 = "b3da1b3fe0369ec3140bb4fbce94702c33b7da810ec15d718b3fadf5cd748ca7"
DATE_MIN = datetime(1998, 1, 1, tzinfo=timezone.utc)
DATE_MAX = datetime(2002, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
SENT_FOLDERS = {"sent", "sent_items", "_sent_mail", "_sent"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_tar(path):
    got = sha256_file(path)
    if got != SHA256:
        sys.exit(f"tarball SHA-256 mismatch: {got} (expected {SHA256})")


def natural_key(path):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", path)]


def addr_list(value):
    if not value:
        return []
    return sorted({a.strip().lower() for _, a in email.utils.getaddresses([value]) if a.strip()})


def parse(raw, path):
    # The CMU files are 8-bit text, mostly ASCII with Windows-1252 punctuation. Decoding here, once,
    # with replacement, keeps every later step on clean str and makes the output valid UTF-8.
    msg = email.message_from_string(raw.decode("cp1252", errors="replace"),
                                    policy=email.policy.compat32)
    try:
        dt = email.utils.parsedate_to_datetime(msg.get("Date", ""))
    except (TypeError, ValueError, IndexError):
        dt = None
    body = msg.get_payload()
    if isinstance(body, list):  # the CMU release is single-part; guard anyway
        body = "\n".join(str(p.get_payload()) for p in body)
    body = (body or "").replace("\r\n", "\n").strip()
    return {
        "path": path,
        "message_id": (msg.get("Message-ID") or "").strip(),
        "date": (msg.get("Date") or "").strip(),
        "dt": dt,
        "from": addr_list(msg.get("From")),
        "to": addr_list(msg.get("To")),
        "cc": addr_list(msg.get("Cc")),
        "subject": " ".join((msg.get("Subject") or "").split()),
        "x_from": " ".join((msg.get("X-From") or "").split()),
        "x_folder": (msg.get("X-Folder") or "").strip(),
        "body": body,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def dedup_key(m):
    utc = m["dt"].astimezone(timezone.utc).isoformat() if m["dt"] else ""
    norm = "\x1f".join([utc, ",".join(m["from"]), ",".join(m["to"]), ",".join(m["cc"]),
                        m["subject"], " ".join(m["body"].split())])
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def folder_of(path):
    parts = path.split("/")  # maildir/<owner>/<folder>/.../<n>.
    return parts[2] if len(parts) > 3 else ""


def iter_mailbox(tar_path, owner=None):
    """Yield (owner, path, raw) for every regular file under maildir/ (optionally one owner)."""
    prefix = f"maildir/{owner}/" if owner else "maildir/"
    with tarfile.open(tar_path, "r:gz") as tf:
        for ti in tf:
            if not ti.isfile() or not ti.name.startswith(prefix):
                continue
            parts = ti.name.split("/")
            if len(parts) < 3:
                continue
            yield parts[1], ti.name, tf.extractfile(ti).read()


def owner_addresses(msgs):
    """The owner's addresses: From values that make up >=5% of the sent folders."""
    counts = defaultdict(int)
    n = 0
    for m in msgs:
        if folder_of(m["path"]) in SENT_FOLDERS:
            n += 1
            for a in m["from"]:
                counts[a] += 1
    return sorted(a for a, c in counts.items() if n and c / n >= 0.05)


def unique_stream(msgs):
    """De-duplicate, drop out-of-range dates, sort by UTC instant then path."""
    msgs = sorted(msgs, key=lambda m: natural_key(m["path"]))
    kept, aliases, dropped = {}, defaultdict(list), []
    for m in msgs:
        if m["dt"] is None or m["dt"].tzinfo is None or not (DATE_MIN <= m["dt"] <= DATE_MAX):
            dropped.append(m["path"])
            continue
        k = dedup_key(m)
        if k in kept:
            aliases[k].append(m["path"])
        else:
            kept[k] = m
    stream = sorted(kept.items(), key=lambda kv: (kv[1]["dt"].astimezone(timezone.utc),
                                                  natural_key(kv[1]["path"])))
    return [(m, aliases[k]) for k, m in stream], dropped


def cmd_stats(a):
    check_tar(a.tar)
    boxes = defaultdict(list)
    for owner, path, raw in iter_mailbox(a.tar):
        boxes[owner].append(parse(raw, path))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["owner", "files", "unique", "sent", "sent_share", "first", "last", "months"])
        for owner in sorted(boxes):
            msgs = boxes[owner]
            own = set(owner_addresses(msgs))
            stream, _ = unique_stream(msgs)
            if not stream:
                continue
            sent = sum(1 for m, _ in stream if own & set(m["from"]))
            first, last = stream[0][0]["dt"], stream[-1][0]["dt"]
            months = (last.year - first.year) * 12 + last.month - first.month
            w.writerow([owner, len(msgs), len(stream), sent, f"{sent / len(stream):.3f}",
                        first.date().isoformat(), last.date().isoformat(), months])
    print(f"wrote {a.out}")


def cmd_build(a):
    check_tar(a.tar)
    msgs = [parse(raw, path) for _, path, raw in iter_mailbox(a.tar, a.owner)]
    if not msgs:
        sys.exit(f"no mailbox named {a.owner}")
    own = set(owner_addresses(msgs))
    stream, dropped = unique_stream(msgs)
    os.makedirs(a.cache, exist_ok=True)
    cache = os.path.join(a.cache, f"{a.owner}.jsonl")
    with open(cache, "w", encoding="utf-8", newline="\n") as fc, \
         open(a.manifest, "w", newline="", encoding="utf-8") as fm:
        w = csv.writer(fm, lineterminator="\n")
        w.writerow(["seq", "batch", "path", "raw_sha256", "date", "utc", "direction",
                    "chars", "alias_paths"])
        for i, (m, al) in enumerate(stream, 1):
            direction = "sent" if own & set(m["from"]) else "received"
            utc = m["dt"].astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            rec = {k: m[k] for k in ("path", "message_id", "date", "from", "to", "cc",
                                     "subject", "x_from", "x_folder", "body", "raw_sha256")}
            rec.update(seq=i, utc=utc, local=m["dt"].strftime("%Y-%m-%d %H:%M"),
                       direction=direction)
            fc.write(json.dumps(rec, ensure_ascii=False) + "\n")
            w.writerow([i, (i - 1) // a.batch + 1, m["path"], m["raw_sha256"], m["date"], utc,
                        direction, len(m["body"]), " ".join(al)])
    print(json.dumps({"owner": a.owner, "owner_addresses": sorted(own), "files": len(msgs),
                      "unique": len(stream), "dropped_bad_date": len(dropped),
                      "dropped_paths": dropped, "cache": cache}, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stats")
    s.add_argument("--tar", required=True)
    s.add_argument("--out", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tar", required=True)
    b.add_argument("--owner", required=True)
    b.add_argument("--cache", required=True)
    b.add_argument("--manifest", required=True)
    b.add_argument("--batch", type=int, default=100)
    a = p.parse_args()
    {"stats": cmd_stats, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()
