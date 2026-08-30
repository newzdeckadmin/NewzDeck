# NewzDeck v3.6.16 - Verified Download Control & Active Continuity

NewzDeck v3.6.16 is a focused Downloads/SAB reliability release built on v3.6.15.

## Verified Failed/Completed removal

- **Retryable verification:** terminal Failed/Completed Remove retries transient SAB Queue/History reads rather than turning one busy localhost response into a failed control.
- **Safe terminal-history proof:** an explicit SAB Failed, Completed, or Cancelled history record can prove that the transfer is already stopped when Queue itself is temporarily unreadable.
- **Live transfers remain protected:** terminal-history proof is never used for a non-terminal job; a live queue job is not hidden until Queue absence is verified.
- **Specific control errors:** expected Remove/Cancel verification failures are returned with their real reason rather than as a generic unexpected application error.
- **No stale resurrection:** successful Remove/Cancel clears the cached pre-mutation SAB snapshot.
- **Duplicate-click protection:** package controls show Removing... or Cancelling... while verified control is running.

## Stable Active state through transient SAB global Pause

- **NewzDeck pause intent is authoritative:** if NewzDeck knows the user did not pause the queue, one transient SAB aggregate `Paused` sample no longer immediately wipes a previously proven Active queue.
- **Bounded coherent-snapshot bridge:** NewzDeck can hold the last coherent Active snapshot for up to 12 seconds while SAB resolves the transient pause.
- **Background recovery:** the SAB coordinator reasserts Resume; the UI polling thread does not mutate SAB.
- **Real pauses remain real:** a user-requested Pause disables the bridge immediately, and a SAB pause that persists beyond the grace becomes visible normally.
- **Diagnostics:** transient SAB-pause bridges are counted independently from ordinary per-job Active-card continuity bridges.
- **Consistent runtime identity:** SAB adapter/version telemetry now matches NewzDeck v3.6.16.

## Preserved

- v3.6.15 Wanted-state reconciliation, QUEUEING handoff state, cycle progress, bounded automatic NZB retrieval, and maintenance decoupling.
- v3.6.14 Windows-safe Automation JSON persistence and responsive monitoring Save acknowledgement.
- v3.6.13 verified Remove/Cancel, hidden-transfer reconciliation, and fallback-only season packs.
- v3.6.12 installer-owned Update Center runtime restoration.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under NewzDeck's version-independent user-data directory.
