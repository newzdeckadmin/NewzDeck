# NewzDeck v3.6.47 — PAR2 Repair Visibility, SAB 5.1.2 & Selected Episode Monitoring

NewzDeck v3.6.47 makes SABnzbd's verification and PAR2 repair work visible after a download finishes. SABnzbd remains the authority on whether a job can be repaired; NewzDeck records and explains what SAB actually reported instead of guessing recovery-block counts or treating every terminal failure as the same condition.

## Selected Episodes monitoring

- TV shows now support a fourth monitoring mode: **Selected episodes**.
- In a show's Manage view, choose Selected episodes, save the mode, then use the existing season checkbox to select an entire season or the individual episode checkboxes to select only specific episodes.
- Selecting Season 3 monitors Season 3 only. Seasons 1, 2, 4, and later seasons remain unmonitored unless explicitly selected.
- Old aired episodes selected this way are intentionally eligible for Continuous Automation even when **Search existing missing backlog** is off, because the selection itself is an explicit user request.
- Selected episodes continue to use the show's normal quality profile and may receive quality upgrades until cutoff when automatic upgrades are enabled.
- A fully selected, fully aired, wholly missing season may use NewzDeck's conservative season-pack fallback. A partial episode selection can never escalate into grabbing the whole season pack.
- Explicit selections are persisted separately from derived All/Future/Missing monitoring state. Switching away from Selected episodes and back restores the previous selection, and metadata refreshes do not silently select newly discovered episodes.

## PAR2 / repair visibility

- Completed and Failed Downloads persist whether SAB verification was observed, whether repair was attempted, and whether SAB fetched additional PAR2/recovery data.
- A terminal repair outcome is retained across UI refreshes and runtime reconnects: `verified`, `repaired`, `unrecoverable`, `failed_unpack`, `failed_password`, `failed_filesystem`, `post_processing_aborted`, `failed_other`, or `not_observed`.
- Download details show the repair summary, failure class, SAB post-processing time, and a bounded recent SAB Verify/Repair/post-processing message history.
- Copy Diagnostics includes the same repair evidence.
- When SAB does not expose exact recovery-block counts in History, NewzDeck explicitly reports **Not reported by SAB** instead of presenting synthetic zeroes.

## Failure classification

The classification is evidence-based and observational. In particular, SAB's terminal `Aborted, cannot be completed` result is surfaced as **PAR2 UNRECOVERABLE**, while password, unpack, and disk/filesystem failures are shown separately so they are not mistaken for insufficient PAR2 data.

## Private SABnzbd 5.1.2

The pinned private engine moves from SABnzbd 5.1.1 to 5.1.2. NewzDeck provisions the official Windows x64 portable archive and verifies SHA-256 `0a48cc87023f054130758a114158e0f17f32152e8ff9158eef49cf73be04be46` before replacing a running 5.1.1 engine.

If the prior private SAB process is running during the application upgrade, NewzDeck requests SAB's graceful shutdown, waits for the authoritative localhost port to be released, then starts 5.1.2 with the same NewzDeck-owned admin/config, queue, incomplete, and download directories. No force-kill path is used for this managed version handoff. If the replacement cannot be provisioned or the old process does not exit, the working queue process is left intact and the upgrade is retried later.

## Preserved behavior

v3.6.47 does not change SAB's own verification/repair policy, Automation release matching, Smart Import, queue mutation semantics, or the v3.6.46 quality-aware release-selection model. Selected Episodes changes only which TV episode targets are explicitly monitored. v3.6.45 scan progress, Library Integrity protections, strict TV edition identity, and the serialized/fail-soft SAB control path remain in place.
