# NewzDeck v3.6.52 — Scope-Native Downloads Projection & SAB Probe Efficiency

NewzDeck v3.6.52 is a focused performance release based on a v3.6.51 diagnostic captured during full download load with all 52 SAB connections active. That capture confirmed the earlier engine-status/state-lock fixes, then isolated the remaining long-tail snapshot cost to server-side projection: one 3.14-second snapshot spent about 3.11 seconds building job/collection/statistics presentation before the Live API discarded terminal history.

## Changes

- **Scope-native Live Downloads projection.** `/api/downloads?scope=live` now asks the snapshot builder for a Live-native presentation. Terminal records that are still visible in SAB History (plus the existing brief Completed-history continuity bridge) continue to contribute to global KPI counts, but their heavyweight job and collection dictionaries are not built merely to be filtered out afterward. Older imported records retained only in NewzDeck's durable ledger remain excluded from visible Completed counts exactly as in the established full presentation. Live SAB Queue echoes and active post-processing/import states remain projected so queue visibility and cleanup invariants are unchanged.
- **Zero-wait in-memory state gate.** v3.6.51 removed disk/JSON work from the presentation path, but its short retry/sleep loop could overshoot the intended 25 ms budget when Windows/Python scheduling was saturated. v3.6.52 attempts the local state lock exactly once and immediately falls back to the last coherent presentation if it is busy.
- **Reduced SAB version-fingerprint traffic.** After the running engine has already been proven as the pinned SAB 5.1.2 generation, recent authenticated API success bypasses redundant version fingerprints. Unknown or older generations still reach the strict identity/upgrade boundary. A proven-current full fingerprint establishes a five-minute sparse recheck cooldown instead of being attempted every engine-loop pass.
- **Projection evidence.** Downloads telemetry now reports the native projection scope, number of Live-native builds, cumulative terminal records skipped from Live projection, and the last number of projected jobs.

## Diagnostic acceptance target

The release specifically targets the production observations from the v3.6.51 heavy-load capture:

- 3.110 s maximum projection phase while only about 10 Live records were needed;
- 157 ms maximum presentation-state gate despite disk I/O already being removed;
- 514 SAB version probes over roughly 33 minutes of otherwise healthy runtime;
- Queue/History sampler health remained 3,067/3,067 successful, so this release does not redesign the proven sampler.

A synthetic release guard models 250 SAB-History Completed jobs, 100 older ledger-only imported completions and 10 Live jobs. It requires the Live-native builder to return only the 10 Live records, preserve exactly the 250 visible Completed count, and prove that the 100 retired ledger records do not inflate the KPI.

## Preserved behavior

The v3.6.51 background-cached engine status, SAB ownership handoff grace, projection timing and episode-based multi-active telemetry remain intact. v3.6.50 Queue/History sampling and deferred persistence, v3.6.49 bounded Downloads transport/history behavior, strict Smart Import ownership, Library Integrity protections, Selected Episodes/PAR2 visibility and private SABnzbd 5.1.2 are preserved.

## Release guards

The Windows release remains blocked unless all historical automation identity/quality/Selected Episodes/PAR2 guards, v3.6.49 data-plane guards, v3.6.50 sampler/state-lock guards, v3.6.51 heavy-load guards and the new v3.6.52 scope-native/zero-wait/probe-efficiency guards pass.
