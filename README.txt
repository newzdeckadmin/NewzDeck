NewzDeck v3.6.52
Scope-Native Downloads Projection & SAB Probe Efficiency

New in v3.6.52:
- Routine Live Downloads polling now builds a scope-native presentation from live/non-terminal jobs instead of constructing every Completed/Failed card first and discarding terminal history afterward. Global Completed/Failed counts remain accurate.
- The presentation state gate is zero-wait: one non-blocking in-memory lock attempt either succeeds immediately or reuses the last coherent presentation, removing scheduler overshoot from the former retry/sleep loop.
- Once the running engine has been proven as the pinned SAB 5.1.2 generation, recent authenticated API success is enough to skip redundant version fingerprints. Unknown/older generations still reach the strict upgrade boundary, and proven-current fingerprints are rate-limited to sparse recovery/upgrade checks instead of every engine-loop cycle.
- Adds scope-native projection telemetry, including projected job count and terminal records skipped from routine Live builds.
- Preserves v3.6.51 cached engine health, SAB handoff grace and episode-based overlap telemetry; v3.6.50 Queue/History sampling/deferred persistence, v3.6.49 bounded Downloads payloads, Smart Import ownership, Library Integrity, Selected Episodes/PAR2 visibility and private SABnzbd 5.1.2 remain intact.
