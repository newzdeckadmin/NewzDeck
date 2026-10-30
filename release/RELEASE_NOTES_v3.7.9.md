# NewzDeck v3.7.9 — Preview Recovery & Browser Responsiveness

This is a focused Newsgroups image-preview and image-set-index reliability release built on the v3.7.8 baseline.

## Fixed

- **No unbounded idle-preview deferral:** visible image previews no longer wait indefinitely for every thumbnail request, queue, and download to become idle.
- **Bounded recovery:** after a short quiet-window grace period, one isolated full-image recovery may start while other thumbnails are still active. A visible image is forced eligible within approximately 8 seconds; an occupied recovery lane reaches a Retry/error state by approximately 12 seconds instead of remaining stuck.
- **Recovery failures become actionable:** failed or timed-out full-image attempts show a Retry/error card rather than silently leaving the loader. The fallback request has a 12-second client deadline.
- **No duplicate thumbnail requeue while deferred:** the demand scanner and queued thumbnail API respect the deferred state, preventing repeated failing thumbnail requests for the same visible image.
- **Image Sets indexing work reduced:** duplicate detection now uses a per-set Set of stable article identities instead of scanning all prior set members. This avoids quadratic browser main-thread work when v3.7.8 discovers large image sets.

## Preserved

- v3.7.8 Image Sets ON/OFF controls and detection patterns, grouping threshold, poster/group identity and Continuous browsing presentation are unchanged.
- Newsgroups splitter, all twelve themes, thumbnail formats, browser viewer, NNTP concurrency, download scheduling, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack, PAR2 repair, Automation, Smart Import and Backup & Restore are unchanged.
- No native Windows cursor customizations are introduced. The cursor flicker may have other causes; this release specifically removes repeated deferred thumbnail work and large-set index stalls that can contribute to UI unresponsiveness.

Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 remain separate unchanged products.
