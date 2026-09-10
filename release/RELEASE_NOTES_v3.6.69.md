# NewzDeck v3.6.69 — Settings Save Contention Recovery & Reliability Telemetry

v3.6.69 is a narrow Windows reliability release driven by repeated production diagnostics. v3.6.67 and v3.6.68 both captured intermittent `/api/settings/save` failures where Python had successfully written a unique temporary settings file but Windows rejected the final `os.replace()` with WinError 5 (`Access is denied`). Later saves succeeded, identifying transient replacement contention rather than a permanently unwritable settings directory.

## Changes

- **Bounded settings replacement retry.** `settings.json` atomic replacement now retries only Windows WinError 5 (access denied), 32 (sharing violation), and 33 (lock violation) for up to three seconds.
- **Existing file remains protected.** New settings are still written to a unique temporary file first. Retries operate on that same completed temp file, and the old `settings.json` remains untouched until atomic replacement succeeds.
- **Settings writes are serialized.** Only the final settings-file writer is serialized, preventing NewzDeck request threads from competing with each other at the replace step.
- **No global state-write retune.** Other JSON state writers keep the established single-attempt atomic behavior; this release is scoped to the repeatedly observed settings path.
- **Passive reliability telemetry.** `/api/diagnostics` now exposes `settings_save_reliability` with attempts, successes, recovered-after-retry saves, retry attempts, terminal failures, last retry count, elapsed time, and WinError. No settings values are included.

## Deliberately unchanged

- browsing-performance schema 7
- v3.6.68 All Posts two-batch / three-second automatic name-resolution render accumulator
- v3.6.67 six-slot Video thumbnail ceiling for 48+ connection providers
- v3.6.65 five-request Image thumbnail HTTP admission gate
- provider connection allocation and NNTP download behavior
- 24 MB Video sample size and 12-segment cap
- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- v3.6.66 preview failure classification
- private SABnzbd 5.1.2 and Downloads/post-processing
- Smart Import and Automation reconciliation
- Metadata Server v0.3.3 and Discover
- terminal download-history schema 3

## Acceptance target

A production diagnostic after normal Settings use should show successful settings saves with zero terminal WinError 5 failures. If Windows briefly blocks replacement, `recovered_after_retry` and `retry_attempts` may increase while `failures` remains zero. Browsing performance should remain consistent with accepted v3.6.68 behavior.
