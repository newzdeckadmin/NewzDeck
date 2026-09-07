NewzDeck v3.6.48
Library Integrity & Downloads Runtime Hardening

New in v3.6.48:
- Library Integrity now flags identical media bytes assigned to different episodes of the same TV title when they are separate physical files, while legitimate one-file multi-episode mappings remain informational.
- A new release-blocking regression suite preserves 29 exact historical false-positive TV identities from real v3.6.47 diagnostics, including Love Island companion/related-show collisions and the Dark Matter title collision.
- Downloads polling is adaptive instead of fixed at 4 Hz: active work remains responsive at 2 Hz, idle polling relaxes further, and hidden/non-Downloads views poll less often.
- The coherent Downloads snapshot cache is widened to 0.40 seconds so nearby UI/diagnostic callers can reuse one authoritative state.
- Diagnostics telemetry now splits slow snapshot time into SAB/reconciliation, provider-health, and remaining NewzDeck presentation work.
- A recovered SAB Queue/History reader-busy event no longer remains indefinitely as the engine's current last_error after fresh Queue+History succeeds.
- UPDATING.txt is refreshed from its stale v3.6.20 text.
- v3.6.47 Selected Episodes, PAR2/repair visibility, private SABnzbd 5.1.2, quality-aware selection, scan progress, Smart Import, and strict TV identity remain preserved.
