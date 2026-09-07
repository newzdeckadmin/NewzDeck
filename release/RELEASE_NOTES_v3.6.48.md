# NewzDeck v3.6.48 — Library Integrity & Downloads Runtime Hardening

NewzDeck v3.6.48 is a focused reliability release based on v3.6.47. It hardens Library Integrity against a same-series duplicate-file case found in real diagnostics, turns historical production false positives into permanent release blockers, and reduces avoidable Downloads/SAB control-plane pressure without changing SABnzbd's authoritative download or repair behavior.

## Library Integrity hardening

- Identical media fingerprints mapped to different episodes of the **same TV title** now require review when they are separate physical files.
- A single shared physical file associated with multiple episode targets remains informational, preserving legitimate multi-episode media behavior.
- The audit exposes a dedicated `same_title_cross_episode_duplicate_fingerprints` count, detailed examples, and an explicit review reason.
- The audit remains read-only and does not delete, rename, move, or rewrite media.

## Production identity regression evidence

- A new v3.6.48 release guard contains **29 exact historical false-positive/attempted release titles** retained in the September 7, 2026 v3.6.47 diagnostics.
- These include real Love Island companion/related-show collisions and a Dark Matter title collision that current strict identity logic correctly rejects.
- The Love Island: All Stars / The Morning After companion-show pattern found by Library Integrity is also guarded explicitly.
- Valid positive controls remain required so the guard cannot become overly restrictive.

## Downloads runtime hardening

- Visible Downloads polling is adaptive instead of fixed at 250 ms:
  - active queue/post-processing work: **500 ms**;
  - idle visible Downloads page: **1250 ms**;
  - hidden or non-Downloads views: **1500 ms**.
- The coherent authoritative snapshot cache increases from **0.22 seconds to 0.40 seconds**, allowing nearby UI and diagnostics requests to reuse the same state.
- New telemetry splits snapshot time into:
  - SAB Queue/History + reconciliation;
  - provider-health/recovery evaluation;
  - derived remaining NewzDeck presentation work.
- Existing snapshot sequence ordering, stale-presentation fallback, Queue/History serialization, and destructive-reconciliation freshness rules remain unchanged.

## Recovered SAB busy state

- `SAB Queue/History reader is busy` remains a bounded transient contention condition with existing counters and diagnostics evidence.
- Once a fresh Queue and History pair succeeds, that recovered transient condition is cleared from the engine's current `last_error` instead of remaining indefinitely as if the engine were still unhealthy.
- No SAB restart, force-kill, queue rewrite, or repair-policy change is introduced.

## Packaging/documentation

- `UPDATING.txt` is refreshed from the stale v3.6.20 text that was still present in v3.6.47 packages.
- The existing v3.6.47 production validation suite remains mandatory, and the new v3.6.48 supplemental guard is also run by the GitHub production release workflow.

## Preserved behavior

v3.6.48 preserves v3.6.47 Selected Episodes monitoring, persistent PAR2/repair visibility, terminal failure classification, and private pinned SABnzbd 5.1.2; v3.6.46 quality-aware release ranking; v3.6.45 scan progress; strict TV identity; Library Integrity review safety; Smart Import; Downloads continuity; installer/runtime handoff; and the source-complete GPLv3 release workflow.
