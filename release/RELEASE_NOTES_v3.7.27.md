# NewzDeck v3.7.27 — Downloads Live Status Reliability & Responsiveness

## Fixed
- A large queued set could leave Downloads and Diagnostics unresponsive while background SABnzbd continued transferring. Frequent UI progress reads now use the existing background SAB sample through a bounded, nonblocking, read-only `/api/downloads/pulse` endpoint. No additional SAB connections or control API reads are generated.
- Full authoritative queue/history snapshots remain enabled for queue membership, completion, controls, and error states, but are fetched less frequently while Downloads is visible.
- Existing visible file rows and single-job Image Set package cards receive in-place progress updates without rebuilding the full download list at every pulse.
- Bulk Image Set submissions yield to the UI every three batches rather than starving user interaction; partial successes and ambiguous failures preserve the existing retry safeguards.
- `/api/diagnostics/ping` offers a lightweight backend liveness indicator even if the full diagnostics aggregation is slow. A stalled full refresh is reported rather than silently showing old status as fresh.
- Copied Diagnostics includes event-loop lag, last full update age, pulse age, request failures and bulk-submission state.

## Preserved
- All current files, transfers, history, identities, retry protections, active download service/tray, SABnzbd 5.1.2, SABCTools 9.6.3, media automation and Smart Import.
- v3.7.26 high-speed Entire Group search (no persistent index or automatic history), v3.7.25 Image Sets OFF layout, v3.7.24 yEnc parser correction and earlier fixes.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unchanged.

## Windows acceptance
1. Queue several large Image Sets and keep transferring for at least 2 minutes. Switch between Downloads, Newsgroups and Diagnostics; verify navigation and progress updates.
2. With 100–300 queued images, check that active file and package progress continue moving, and that queue membership/completed history resolve through the full snapshot.
3. Pause/resume, cancel a selected job, and verify no duplicated or lost submissions. Test one ambiguous or failed add response; failed selections must remain selected.
4. Deliberately delay SAB control status or Diagnostics aggregation and confirm the UI labels it stale while live downloads keep progressing.
5. Copy Diagnostics during load; note event-loop lag and last-full/pulse ages. Compare against v3.7.25 behavior.
6. Reconfirm live Entire Group search, image/video previews, Image Sets toggle, filename restoration and Smart Import after upgrade.

## Limitations
- Offline simulation is not a substitute for Windows + Easynews stress validation. Large queue rendering, network performance and actual SAB contention depend on the user's system.
- v3.7.26 is a publication prerequisite: publish and verify that immutable release before using the v3.7.27 guarded publisher.
- This ZIP is a Git publishing package, not an installer. It does not publish automatically.
