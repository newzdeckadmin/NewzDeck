NewzDeck v3.6.30
SAB Identity Probe Stabilization

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.30

- Removes redundant routine SAB mode=version fingerprints from the healthy runtime
  path after v3.6.29 production telemetry isolated nearly every residual low-level
  transport reset to that probe.
- Routine liveness now proves the authoritative current-generation API key through
  SAB's auth endpoint while startup/recovery/reconciliation retain full version and
  credential identity proof.
- Unchanged provider/configuration passes now return before any SAB heartbeat,
  avoiding pointless identity traffic on every engine-loop cycle.
- Diagnostics now reports version probes/failures, runtime-auth probes/failures, and
  configuration synchronization no-op skips.
- v3.6.29 persistent serialized HTTP/1.1 transport and v3.6.28 Downloads visibility
  continuity remain unchanged.

NewzDeck v3.6.29 persistent SAB control transport, v3.6.28 durable Downloads
continuity, v3.6.27 runtime adapter identity validation, v3.6.26 verified Remove /
Remove all failed, v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24
durable Download Statistics and accepted earlier behavior remain preserved.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
