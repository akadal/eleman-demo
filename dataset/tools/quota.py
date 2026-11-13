#!/usr/bin/env python3
"""quota.py: print the Claude subscription usage windows as one JSON line, or {} if unreadable.

Harness-specific and optional: it reads Claude Code's own OAuth credentials file and asks the
usage endpoint Claude Code itself displays. It only matters when the run uses a subscription
rather than API billing; with an API key the token counts in dataset/runs/ are the cost record.
The token goes to Anthropic only and is never printed or written.
"""
import json
import os
import urllib.request

URL = "https://api.anthropic.com/api/oauth/usage"


def main():
    try:
        path = os.path.join(os.path.expanduser("~"), ".claude", ".credentials.json")
        with open(path, encoding="utf-8") as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(URL, headers={"Authorization": "Bearer " + token,
                                                   "anthropic-beta": "oauth-2025-04-20"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.load(r)
        out = {k: v.get("utilization") for k, v in d.items() if isinstance(v, dict) and "utilization" in v}
    except Exception:
        out = {}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
