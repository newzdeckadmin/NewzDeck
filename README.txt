NewzDeck v3.6.19
Non-Disruptive SAB Runtime & Single-Foreground Downloads

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.19

- SAB control-plane recovery is now non-disruptive: one brief localhost probe miss
  cannot immediately relaunch/reconfigure the private download engine.
- Recent successful Queue/status/config API traffic is accepted as liveness proof.
- A recently healthy or active runtime gets a non-mutating recovery window before
  disruptive engine launch recovery is allowed.
- Launch recovery no longer force-rewrites all provider configuration.
- Partial config-sync failures no longer cause a three-second full rewrite loop.
- Short SAB aggregate Pause transitions are ignored; recovery requires sustained state.
- One-package queue mode now guarantees at most one Active foreground package.
- Live package progress cannot regress backward during reconnect/handoff snapshots.
- Diagnostics exposes engine-control and configuration-recovery counters.

v3.6.18 idle-aware recovery, v3.6.17 canonical Downloads state and Smart Import
recovery, and v3.6.16 verified Remove/Cancel remain preserved.
