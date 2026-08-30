# NewzDeck v3.6.15 - Wanted State Reconciliation & Responsive Automation

NewzDeck v3.6.15 is a focused Continuous Automation and Wanted-state reliability release built on v3.6.14.

## Wanted state is reconciled with live Downloads

- **Live queue state is authoritative:** Wanted no longer trusts an old persisted `QUEUED`, `GRABBED`, `PROCESSING`, or similar runtime marker indefinitely when the live download engine has no matching job.
- **Bounded handoff grace:** newly queued jobs retain a 75-second handoff window so brief SAB/NewzDeck visibility delays do not create false retries.
- **Stale queue markers recover:** after that grace, an absent job changes to `RETRYING` with an explanation that the previously queued job is no longer present.
- **Honest cross-runtime state:** a temporary cross-runtime grab reservation displays `QUEUEING`, not `QUEUED`, until a real live download becomes visible.
- **Active Targets and row badges agree:** both are now grounded in the current download-manager snapshot.

## Continuous Automation is easier to understand

- **Real cycle progress:** the Wanted banner reports current phase and target, such as `Checking 3/8 • Dark Matter S01E04`.
- **Next Cycle is accurate:** while a cycle is active, the UI says `In progress` rather than the contradictory `Due now`.
- **Maintenance is off the critical path:** metadata refresh and library reconciliation continue on background workers instead of making release searching wait for potentially long bulk work.
- **Automatic NZB retrieval is bounded:** automatic retrieval has a 45-second per-release wall budget and individual automatic requests are capped at 15 seconds. Manual Interactive Search/Grab retains the existing more generous behavior.
- **Concurrent runtime changes are preserved:** a long-running cycle merges newer failure/blacklist and maintenance state before its final runtime save instead of overwriting newer information with an old snapshot.

## Preserved

- v3.6.14 Windows-safe Automation JSON persistence and immediate truthful monitoring Save acknowledgement.
- v3.6.13 stable Active cards, verified Remove/Cancel, hidden-transfer recovery, Wanted policy clarity, and fallback-only season packs.
- v3.6.12 installer-owned Update Center runtime restoration.
- Prior SAB ownership, Smart Import, and Python source-freshness protections.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under NewzDeck's version-independent user-data directory.
