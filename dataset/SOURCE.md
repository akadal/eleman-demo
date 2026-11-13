# Source

## Release

- Enron Email Dataset, CMU release of 7 May 2015: `enron_mail_20150507.tar.gz`
- URL: https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz
- Size: 443,254,787 bytes (Last-Modified: Thu, 07 May 2015 20:35:29 GMT)
- SHA-256: `b3da1b3fe0369ec3140bb4fbce94702c33b7da810ec15d718b3fadf5cd748ca7`
  (`build_stream.py` refuses any other file)
- Downloaded 2026-11-13.
- Reference: Klimt & Yang (2004), https://doi.org/10.1007/978-3-540-30115-8_22

## Mechanism

- eleman at commit `fd83674` (https://github.com/akadal/eleman), software DOI
  10.5281/zenodo.23975338. This repository was generated from that template; the deviations are
  listed in `dataset/README.md`.

## Mailbox

Rule (fixed before looking at mailbox content): at least 3,000 unique messages after
de-duplication, at least 25% sent by the owner, a span of at least 24 months; among those, the
mailbox with the most unique messages under 15,000, so that a full run stays affordable. All 150
CMU mailboxes appear in EnronQA (Ryan et al., 2025, arXiv:2505.00263), whose records carry the
CMU path, so EnronQA questions can be mapped onto this stream.

15 of 150 mailboxes met the thresholds (`dataset/mailbox-stats.csv`, from `build_stream.py stats`). The largest, `dasovich-j` (15,876 unique), is over the
cap; the rule selects **`kaminski-v`**:

| | |
|---|---|
| files in the mailbox | 28,465 |
| unique messages | 11,523 |
| dropped for impossible dates | 26 |
| sent by the owner | 45.0% |
| first / last message | 1999-11-30 / 2002-02-03 |
| owner addresses (from the sent folders) | vince.kaminski@enron.com, j.kaminski@enron.com |
| time zones in Date headers | -0800 (5,588), -0700 (5,935): US Pacific, so local order equals UTC order |
| stream checksum (`kaminski-v.jsonl`) | built twice, byte-identical |

The pilot covers messages 1-1,000: 1999-11-30 to 2000-03-16, 525 sent by the owner. Per batch of
100 the fed text is 42k-192k characters; 46 bodies are cut at 6,000 characters. No body contains
a backtick fence, `(sleep-task)`, `(feedback)` or a `memory/...md` path; four contain `[[`, inside
the fence.
