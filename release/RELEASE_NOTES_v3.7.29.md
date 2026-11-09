# NewzDeck v3.7.29 — Metadata Refresh Reliability & Monitoring Integrity

## Root cause and resolution

In v3.7.28, `refresh_monitored_metadata()` reused its incoming `ident` filter as
its per-item loop variable. A scheduled sweep started with no filter, processed
the first monitored item, and silently excluded every other movie/TV title.
An affected library with 57 monitored TV series and 6 movies consequently
reported **one** updated title and no errors. Manual per-title refreshes worked
because they supplied the intended identifier explicitly.

v3.7.29 preserves the requested identifier separately from `item_id` and scans
**every monitored title**. Existing per-title monitoring flags, episode selection,
quality profiles, library/imported-file state, downloads, and custom paths remain
unchanged. It never performs media deletion or adds a search index/history.

## Reliability and observability

- Initial **full metadata sweep after upgrade**, regardless of the old version's
  misleading last-refresh timestamp; subsequent full sweeps follow the user's
  existing configurable interval (default six hours).
- Monitored movie/TV refreshes request a live Metadata Service response instead
  of accepting the old 30-day *local cached fallback* as verified. Ordinary
  Discover UI cache behavior remains unchanged.
- Incomplete TV season metadata and missing movie details are reported as
  per-title failures; no partially applied library update or overwritten
  last-good availability/episode data.
- Separate attempted, updated, failed, newly discovered episodes, newly Wanted,
  and home-release-date-change counters.
- Failed titles keep their earlier successful refresh timestamp and get a
  visible error. Up to 20 failures are retried per sweep after 15 minutes;
  healthy titles are not refetched just to retry others.
- Newly eligible monitored releases notify the existing automatic Wanted
  scheduler, subject to all current availability, indexer, quality, backlog,
  queue, import and safety rules.
- Movie and TV detail panes show last successful metadata refresh and errors;
  Automation Health displays verified/attempted counts and pending retry count.
  Metadata Service diagnostics include scheduler summary.

## Limits / important notes

- This is a NewzDeck **source publishing package**, not a prebuilt Windows EXE.
- Windows CI and a real metadata-service/Indexer/NNTP session must succeed after
  publication; tests are offline and do not prove Internet availability.
- A fresh successful response may reflect the metadata provider's own data and
  upstream caching. NewzDeck does not fabricate digital, physical, or TV air dates.
- Continuous Automation still queues only qualifying releases after Wanted
  eligibility, backlog rules, profile matching and release-content checks.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unchanged.

## Regression verification

`python release/windows/validate-v3729-regressions.py`

`python release/windows/validate-v3729-metadata-refresh.py`

`node release/windows/validate-v3729-metadata-ui.js`

All v3.7.28 targeted Downloads, v3.7.26 live search, Image Sets, media identity,
and yEnc validations remain in production workflow. Historical *full*
version-specific release gates must not be invoked on the new version.
