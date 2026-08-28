# NewzDeck v3.5.52 — Reliability & Live Workflow Release

NewzDeck v3.5.52 is the cumulative production release from the v3.5.36–v3.5.52 acceptance cycle. It keeps the high-throughput private SAB download engine and media automation architecture while making the desktop/service/download/import workflow substantially more reliable and responsive.

## Highlights

- **Live Downloads:** near-real-time foreground updates, coherent SAB snapshots, stable Active cards, and in-place UI patching so active transfers no longer disappear/reappear during transient observations.
- **Live post-processing:** Verify, Repair, Unpack, Direct Unpack, and Smart Import now expose useful current-operation/progress information with smooth motion instead of a static or flashing post-processing bar.
- **Smart Import finalization:** completed jobs clean up release debris and staging folders safely; Movies and TV reconcile existing equal/better media correctly; cleanup retries transient Windows locks.
- **One-time media organization:** Movies and safely identifiable TV releases grabbed from Discover can be renamed/moved once without first becoming monitored Automation items.
- **Faster Discover:** title modals open immediately, metadata work is parallelized/prefetched/cached, and Interactive Search remains within the usable viewport.
- **Durable Grab queueing:** a Grab is committed to NewzDeck before SAB handoff, so the browser is no longer blocked by download-engine startup timing.
- **Windows background-engine reliability:** private SAB is launched in the signed-in user session when NewzDeck's backend runs under the Windows service, avoiding SAB's Session 0 service-mode misdetection.
- **Tray resilience:** the notification-area icon/menu survives Explorer/taskbar recreation and long idle/session transitions and stays inside the usable work area.
- **Provider/runtime integrity:** BOM-safe provider state plus authoritative service-runtime handoff prevents the desktop UI and background service from drifting onto different same-version backend/provider states.

## Upgrade notes

Normal installed upgrades preserve NewzDeck data under `%LOCALAPPDATA%\NewzDeck`. You do not need to remove the previous version first.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may display an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.5.52_SHA256.txt` if desired.

Usenet service is not included; NewzDeck requires your own NNTP provider credentials. TMDB-powered Discover and Automation metadata continue to use NewzDeck's metadata service, currently compatible with Metadata Server v0.3.3.
