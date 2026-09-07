NewzDeck v3.6.51
Heavy-Load Snapshot & Handoff Hardening

New in v3.6.51:
- Downloads snapshots no longer read, decode, or merge the cross-process jobs ledger from disk. The presentation path uses the already-synchronized in-memory ledger and keeps the 25 ms local-lock budget.
- Live SAB engine-status probing and identity reads move to the background coordinator; Downloads snapshots consume cached engine health instead of performing foreground localhost/disk work.
- Snapshot diagnostics now separate card/collection/statistics projection from the remaining other phase for clearer heavy-load attribution.
- Newly accepted SAB jobs receive a four-second ownership-handoff grace. Their cards remain visible immediately, but normal submit-to-ledger races no longer generate false missing-ledger warnings.
- Multiple-active-slot telemetry now counts distinct overlap episodes rather than incrementing on every poll while also reporting raw overlap samples and duration.
- Legacy downloads.json compaction telemetry reports the real unchanged file size when there is nothing left to compact.
- v3.6.50 Queue/History sampling/deferred persistence/installer cleanup, v3.6.49 bounded Downloads data plane, strict Smart Import ownership, Library Integrity protections, Selected Episodes/PAR2 repair visibility and private SABnzbd 5.1.2 remain preserved.
