NewzDeck v3.6.41
Downloads Snapshot Responsiveness

Focused production reliability release based on a completed v3.6.40 Diagnostic Collector capture.

WHAT'S NEW IN v3.6.41

- Live Downloads Queue/History reads now use a bounded wait for the serialized private-SAB control transport instead of waiting behind long-running control operations.
- Once a coherent Downloads snapshot exists, concurrent API callers can immediately reuse it while a new snapshot is being built, preventing diagnostics and /api/downloads from lining up behind the same slow snapshot.
- Live presentation reads use short single-attempt Queue/History budgets; authoritative non-live recovery, reconciliation, mutation, and crash-recovery paths keep their stronger existing retry behavior.
- SAB transport telemetry is observational and no longer acquires the same control lock merely to report diagnostics.
- New snapshot/transport telemetry records build duration, lock-busy fallbacks, transport wait time, active control mode, and busy timeouts for future Diagnostic Collector analysis.
- Installed-runtime detection now recognizes Inno Setup's canonical unins000.exe marker while retaining compatibility with the retired Uninstall.exe marker.

This release does not weaken serialized SAB transport, queue ownership, destructive reconciliation guards, Automation admission, Smart Import, no-downgrade behavior, or the v3.6.38-v3.6.40 recovery and runtime-storage protections.
