# NewzDeck v3.7.12 — Gallery Image Lifecycle & Viewer Hotfix

Fixes gallery cards that can remain visually empty when a thumbnail never fires either the image load or error event, and prevents viewer actions from using stale numeric article indices.

- A bounded thumbnail-image load watchdog invokes existing recovery for visible, stalled image elements after 15 seconds; normal images are not classified as corrupt just for loading slowly.
- Visible image cards with no image, no loading holder and no error holder are checked again after a 5-second grace period, then excluded from the gallery for the current browsing session.
- Gallery selection, viewer, context menu, download and Retry actions resolve each card by stable article identity before using its numeric index.
- Viewer full-image `<img>` handlers are registered before `src` assignment, and a full-image decoder failure now removes the unusable card instead of leaving an apparently unresponsive viewer.
- Continuous-browsing gallery append paths also schedule orphan-card inspection.
- The existing successful-preview visual detector and bounded recovery behavior are left intact. No downloaded files or remote Usenet posts are deleted.

No changes to NNTP, the thumbnail HTTP endpoint, persistent cache schema, the native thumbnail decoder, Image Sets classification/ON-OFF, SABnzbd 5.1.2, SABCTools 9.6.3, Automation, Direct Unpack, PAR2, or the managed updater.

**Scope:** The screenshot demonstrates the symptom but does not prove which of the above failure modes occurs on the affected article. Release tests include DOM-identity and stalled-image cases; actual post behavior must be confirmed on Windows.
