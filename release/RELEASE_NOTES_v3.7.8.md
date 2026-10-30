# NewzDeck v3.7.8 - Image Sets Detection & Controls

v3.7.8 improves Newsgroup Image Sets recognition and makes the existing grouping preference unmistakably optional.

## Improved detection

- Recognize sequences numbered at the **beginning** of filenames (for example `01 - Vacation.jpg`, `[02] Vacation.jpg`, `#03_Vacation.jpg`) as well as existing trailing and bracketed/index-total patterns.
- Recognize `part`, `page`, and `scan` numbering alongside `img`, `image`, `photo`, `pic`, and other already-supported media labels.
- Use an explicitly numbered subject such as `Beach Album [03/20]` to identify an album when its attachment filenames are generic (`IMG_0003.jpg`, `003.jpg`), rather than grouping unrelated camera filenames under `IMG`.
- Keep different poster addresses, newsgroups, media kinds, and subject album identities separate.
- Preserve the minimum of **three related posts** before promoting a set and the existing safeguards against treating bare years as photo counters.

## Optional Image Sets

- The Newsgroups toolbar now clearly reads **Image Sets: ON** or **Image Sets: OFF**.
- In Settings, the existing saved **Group related media** preference is now labeled **Image Sets**, with an explanation of the effect of each mode.
- **OFF:** every image or video remains individually visible in the normal browsing gallery/list; no Image Set cards hide items from it.
- **ON:** recognized sequences move into Related Media while individual posts remain in the normal gallery/list.
- The setting persists across sessions using the existing `group_related_media` preference; no data migration is required. The All Posts binary-packages control remains independent.

## Preserved

v3.7.7 Newsgroups splitter and width persistence, v3.7.5 grouping index/Continuous-browsing stabilization, thumbnails, gallery virtualization, viewer, NNTP concurrency, private SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack, PAR2/repair, Automation, Smart Import, Backup & Restore, all themes, and managed update lifecycle remain unchanged. Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unaffected.
