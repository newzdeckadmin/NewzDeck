# NewzDeck v3.7.32 — Download Queue Reliability, Asynchronous Grab & History Consistency

## Fixed: manual grabs no longer depend on a long browser POST

- Manual Grab uses an explicit asynchronous mode; the local backend acknowledges a bounded queued operation immediately and performs indexer NZB retrieval, validation, and local SABnzbd handoff in one of two daemon workers.
- An operation is tracked by a stable, random, per-attempt client ID and a server job ID. The UI polls a read-only status endpoint. A canceled or delayed acknowledgement does not trigger a second POST automatically.
- Requests for the same media target in progress coalesce; replaying the *same client ID* refers to the original operation. Across Windows runtimes, the existing atomic target reservation remains authoritative.
- UI progress distinguishes queued, retrieving NZB, validating NZB, and saving the pending SABnzbd handoff. An accepted pending ticket is explicitly described as **awaiting SABnzbd handoff**, not proof of a completed transfer.
- Reservation-only, already-queued, suppressed and failed results get distinct, actionable messages, without a misleading “Added to queue” notification. Errors do not leak NZB URLs, API keys or downloaded NZB content through the operation status endpoint.
- A service restart can lose the in-memory operation tracker, but it does **not** automatically cancel, delete, or retry persisted SAB handoffs. The UI directs the user to check Downloads before retrying.
- Other/new clients using the original synchronous `/api/automation/releases/grab` contract remain compatible; the asynchronous behavior is opt-in.

## Fixed: Completed history classification and cleanup consistency

- An already-transferred item with post-processing status `queued`, `waiting`, `verifying`, `repairing`, `extracting`, `importing`, or `needs_password` is no longer counted as a clearable **Completed** item. It remains in the existing live **Post-processing** view.
- Completed history counts, pagination, visible cards, and history-only cleanup eligibility now agree. Failure and blocked categories remain in the Failed view.
- **Remove all completed** remains explicitly history-only. No download, imported media, temporary files or incomplete post-processing data are deleted through this fix.

## Release identity and Windows build compatibility

- This is the standard **three-component** release `3.7.32`, built on the immutable published v3.7.31 source (not v3.7.30).
- The existing canonical Windows version validator, Inno Setup `VersionInfoVersion={#AppVersion}.0`, and `build-release.ps1` three-part format remain unchanged.
- Version identity is updated in the application, UI, tray helper and canonical release workflow. Existing v3.7.31 video discovery regression checks remain active.
- The guarded source-preparation step compares the reviewed baseline against immutable Git objects, not potentially transformed checkout bytes, and only writes allowlisted paths.

## Unchanged

- SABnzbd **5.1.3**, SABCTools **9.6.3**, download engine configuration, queue, provider settings, Smart Import, media library, Wanted/Automation, service/tray, and user data.
- v3.7.31 High-Performance Video Discovery & Browsing and previous Image Sets / multipart / yEnc regressions.
- Metadata Server **v0.3.3**, Diagnostic Collector **v1.0.31**. No remote service is contacted or deployed by this source package.

## Validation and limitations

Offline tests execute the production asynchronous coordinator and terminal-history classification methods, check frontend state transitions and safe no-retry behavior, and preserve existing SAB, video-discovery, metadata, download and browsing tests.

**Windows-specific build, installer upgrade smoke tests, live NNTP behavior, and actual in-browser connection-pool timing require the canonical GitHub Actions Windows workflow and field testing after separate permission to publish.** The hotfix does not guarantee that previously failing *Sinners (2025)* NZB releases contain available Usenet articles; those remain separate SAB provider/indexer failures until the per-release error is captured.

No source is pushed and no GitHub release is published by preparing this package.

## Publication package reliability
- The guarded source-preparation step now verifies immutable Git blob objects at the pinned v3.7.31 main commit rather than comparing checked-out working-tree bytes on Windows.
- Canonical source bytes are used only for allowlisted files that will be updated; unrelated files remain unchanged.
- Release uses three-component version `3.7.32`, so standard Windows version metadata and the canonical three-component version gate remain unchanged.
- Preflight fails closed if the published Git object, release tag, branch, or clean-tree state differs. The publisher performs no changes to your installed application.
