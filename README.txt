NewzDeck v3.6.24
Durable Download Statistics

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.24

- Total Downloaded now combines the preserved pre-SAB NewzDeck baseline with
  SABnzbd's exact persistent lifetime byte counter.
- Completed SAB jobs are accounted exactly once in a shared durable ledger so
  service/desktop handoff and History clearing cannot double-count or erase totals.
- Transfer Time accumulates retained SAB download_time values and continues
  updating from new completions even when the Downloads page is not open.
- Average Speed is a weighted average over transfers whose timing is known;
  NewzDeck reports timing coverage instead of inventing deleted historical data.
- Peak Speed is persisted whenever a new maximum is observed and survives restarts.
- Existing SAB History and Archive are backfilled in bounded pages to recover as
  much historical timing/completion information as remains available.
- Download Statistics diagnostics expose legacy/SAB byte provenance, timed-byte
  coverage, backfill state, accounted completions and reconciliation timestamps.

NewzDeck v3.6.23 accent-insensitive Automation matching, v3.6.22 All Posts binary
resolution/recovery, v3.6.21 image browsing and Related Media, and v3.6.20
authoritative SAB/Downloads behavior are preserved. Normal installed updates
preserve settings, provider configuration, Automation data, history, queue state,
and user data.
