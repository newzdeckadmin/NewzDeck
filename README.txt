NewzDeck v3.6.25
Automation Backlog & Smart Import Reliability

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.25

- Smart Import retries that exhaust their limit now remain terminal until the user
  explicitly chooses Retry Import, preventing infinite retry churn.
- Smart Import output discovery is now job-owned and fail-closed. NewzDeck no
  longer guesses from unrelated recent SAB/_UNPACK_ folders when exact ownership
  cannot be proven.
- TV release matching protects franchise/country identity so generic Love Island,
  Big Brother, and similar titles do not consume different editions or spin-offs.
- Smart Import progress persistence is throttled during large Automation backlogs,
  reducing repeated multi-megabyte state rewrites without making the UI less live.
- SAB Queue reads are reused for short safe intervals, lifetime statistics polling
  is less aggressive, and failed private-SAB launch recovery observes a cooldown.
- Stale import ownership release state persists across desktop/service merges so
  the same abandoned claims are not repeatedly reclaimed and logged.
- Copy Diagnostics includes a read-only library integrity audit for duplicate
  fingerprints across different targets and TV edition mismatches.
- The Failed downloads view now includes Remove all failed, using one batch control
  request so large groups of failed downloads do not require one Remove click each.

NewzDeck v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation
matching, v3.6.22 All Posts binary resolution/recovery, v3.6.21 Related Media/image
browsing, and v3.6.20 authoritative SAB/Downloads behavior remain preserved.
Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
