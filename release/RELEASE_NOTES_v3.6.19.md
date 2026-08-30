# NewzDeck v3.6.19 - Non-Disruptive SAB Runtime & Single-Foreground Downloads

NewzDeck v3.6.19 is a deeper Downloads/SAB runtime reliability release built on v3.6.18.

## Non-disruptive private-SAB runtime management

- **Recent API traffic proves liveness:** successful Queue/status/config API traffic is treated as strong evidence that the private SAB runtime is alive.
- **No one-probe relaunch:** one brief localhost health-probe miss no longer immediately enters launch recovery.
- **Non-mutating recovery window:** a failed probe receives a quiet recovery interval before NewzDeck is allowed to take disruptive action.
- **Active runtimes get more protection:** recently healthy or actively transferring runtimes receive an extended debounce before launch recovery.
- **No forced config rewrite after a transient outage:** launch recovery reuses persisted configuration rather than forcing every SAB/provider setting to be rewritten.
- **No three-second config retry storm:** a partial configuration-sync failure is recorded without clearing the attempted signature and causing the engine loop to rewrite all provider entries over and over.
- **Real configuration changes still synchronize:** a fresh SAB admin generation or actual settings/provider change naturally invalidates/changes the signature.

## Stable one-package Downloads presentation

- **One foreground package:** Queue mode `1 package at a time` now guarantees at most one Active package in the NewzDeck snapshot.
- **Transient SAB multi-Downloading state is normalized:** queue order selects the foreground owner and other packages remain Queued.
- **Monotonic progress:** a live package cannot regress backward in downloaded bytes merely because SAB emitted a reconnect/handoff snapshot.
- **Pause recovery is sustained-state based:** SAB aggregate Pause must persist before NewzDeck displays recovery, and Resume reassertion is rate-limited.

## Diagnostics

New counters expose:

- transient SAB health-probe misses;
- disruptive recoveries deferred;
- actual launch recoveries;
- configuration sync attempts/failures;
- suppressed configuration retry storms;
- corrected multi-Active snapshots;
- corrected progress regressions.

## Preserved

- v3.6.18 idle-aware engine-pause recovery.
- v3.6.17 canonical Downloads cards/counts/Remaining state and Smart Import dead-runtime recovery.
- v3.6.16 verified Failed/Completed Remove/Cancel and Active continuity.
- v3.6.15 Wanted-state reconciliation and Continuous Automation improvements.
- v3.6.14 Automation JSON persistence hardening.
- v3.6.12 installer-owned Update Center runtime restoration.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data.
