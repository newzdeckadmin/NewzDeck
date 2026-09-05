# NewzDeck v3.6.25 — Automation Backlog & Smart Import Reliability

NewzDeck v3.6.25 promotes the accepted v3.6.25-r1 reliability work built on production v3.6.24 and adds bulk cleanup for Failed downloads. This release is focused on correctness and stability when Automation is monitoring very large backlogs and the private SAB engine is completing, importing, retrying, and reconciling many jobs over long periods.

## Smart Import retry correctness

- A Smart Import that exhausts its retry limit is now genuinely terminal.
- Failed imports are excluded from automatic re-claim until the user explicitly chooses **Retry Import**.
- This prevents the same unresolved completion from cycling hundreds or thousands of times and repeatedly rewriting shared state.
- Explicit Retry Import still clears the terminal state and allows a deliberate fresh attempt.

## Job-owned, fail-closed output resolution

- Smart Import no longer treats an arbitrary recent SAB output or `_UNPACK_` directory as a substitute for the completed job's own output.
- Exact SAB/history storage, persisted job ownership, and exact release-folder evidence are preferred.
- When ownership cannot be proven safely, the import remains available for review instead of consuming another download's media.
- Output folders that belong to another SAB job are not eligible as a fallback source.
- The existing source-cleanup behavior continues only after the import source has been proven to belong to the intended download.

## TV franchise and edition identity protection

- TV release acceptance and Smart Import now validate country/franchise suffixes instead of relying only on a base-title prefix match.
- Generic titles such as `Love Island` cannot silently consume `Love Island Australia`, `Love Island USA`, `Love Island Games`, or other conflicting editions/spin-offs.
- `Big Brother` and `Big Brother Canada` are likewise kept separate.
- Existing canonical TMDB identity, manual library-title overrides, and country suffix naming remain preserved.
- The v3.6.23 accent-insensitive title folding remains in effect, so this stricter edition protection does not regress titles such as `90 Day Fiancé` / `90 Day Fiance`.

## Large-backlog persistence and SAB control stability

- Smart Import progress remains live in memory, while durable progress/heartbeat persistence is throttled to reduce repeated large JSON rewrites during multi-gigabyte copies.
- Completion/failure/ownership transitions still persist immediately.
- Successful private-SAB Queue reads are shared for a short bounded interval instead of issuing redundant parallel reads from every consumer.
- Lifetime Download Statistics polling is less aggressive while retaining the durable v3.6.24 accounting model.
- Failed private-SAB launch/recovery attempts observe a cooldown instead of repeatedly cycling startup recovery.
- Stale ownership-release state is persisted so desktop/service reconciliation cannot repeatedly resurrect and re-log the same abandoned claim.

## Read-only library integrity audit

- Copy Diagnostics now includes a read-only audit of media fingerprints registered to multiple Automation targets.
- The audit also reports TV edition/country mismatches between persisted library identity and filenames.
- This audit never deletes, moves, renames, or repairs media automatically; it exists to identify possible historical cross-import damage safely.

## Remove all failed

- The Downloads **Failed** view now includes **Remove all failed** when failed/attention entries are present.
- The button shows the number of affected downloads and asks for confirmation before acting.
- All affected job IDs are sent through one NewzDeck batch control request instead of requiring an individual Remove click for every card.
- Existing verified Remove semantics remain authoritative: successfully removed jobs are tombstoned/cleared, while any job whose SAB removal cannot be verified remains visible and the user is told that removal was not confirmed.
- Already-imported library files are not deleted by this bulk history/download cleanup action.

## Preserved production behavior

NewzDeck v3.6.24 durable Download Statistics remain intact, including additive pre-SAB/SAB lifetime byte accounting, idempotent completion statistics, retained-history timing backfill, weighted Average Speed, persistent Peak Speed, and History-independent lifetime counters.

NewzDeck v3.6.23 accent-insensitive Automation/Newznab matching, v3.6.22 All Posts binary resolution/recovery, v3.6.21 image browsing and Related Media behavior, and v3.6.20 authoritative SAB Queue/History control and fresh-state reconciliation also remain intact.

Automation queue depth remains bounded. Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior, provider settings, normal NZB/package semantics, and user-data preservation are not intentionally changed by this release.
