# NewzDeck v3.6.21 — Newsgroups Image Browsing & Related Media

NewzDeck v3.6.21 is the production promotion of the accepted v3.6.20-r13 Newsgroups image-browsing and Related Media work.

## Direct image downloads

- Loose images selected directly from Newsgroups finish in the configured Download Folder root instead of remaining inside image- or job-named completion folders.
- Filename collisions are handled without overwriting an existing image.
- Grouped/package downloads, imported NZBs, Automation jobs, Smart Import, and other non-loose-image workflows keep their existing folder semantics.

## Related Media side pane

- Group Related Media now places image sets in a dedicated Related Media pane instead of mixing set cards into the main scrolling gallery.
- The main visual browsing stream contains individual/un-grouped media while Related Media sets are organized separately and update live during Continuous browsing.
- Opening a set uses the existing media viewer with set-only Previous/Next navigation; returning restores the full loaded set list.
- All Posts retains its existing binary Preview/details pane.

## Continuous browsing performance

- Related Media sets are indexed incrementally as new header pages arrive instead of repeatedly regrouping the full loaded article history.
- Long Continuous sessions use measured gallery DOM windowing so distant rows can be collapsed without discarding loaded article state or causing another NNTP header request when scrolling back.
- Definitive missing, incomplete, and corrupt image failures avoid redundant full-preview recovery.
- Failed-card cleanup is batched to reduce repeated Chromium layout and scroll reconciliation.
- Broken related-image sets use bounded health sampling so a very large dead set does not have to be tested member by member.

## Related Media cover reliability

- Set covers prefer complete/downloadable members and are owned by stable media-set keys rather than transient article indices.
- Cover retrieval is bounded and sequential per set, never fans out into hidden parallel cover requests, and never escalates into full-image preview recovery.
- Visible Related Media covers reserve capacity inside the existing thumbnail concurrency budget so normal gallery activity cannot starve them indefinitely.
- Cached thumbnails are consumed before issuing new NNTP cover work.
- Cover completion survives Continuous gallery-generation and article-index changes as long as the user remains in the same browse session/newsgroup.
- Existing queued cover work is promoted in place from offscreen/nearby priority to visible priority when its set card enters the pane, fixing the long-loading condition that previously appeared to recover only after leaving and returning to Newsgroups.
- Retryable cover failures have an explicit terminal/retry state instead of remaining on Loading indefinitely.

## Diagnostics

- Copy Diagnostics reports Related Media cover visibility, queue depth, reserved capacity, activation/cache behavior, promotions, start/run timing, target misses, repairs, and the pre-navigation scheduler snapshot.

## Preserved production behavior

NewzDeck v3.6.20's authoritative SAB Queue/History control, Downloads-state reconciliation, Automation completion monitoring, and Smart Import behavior remain intact. Discover/TMDB, Metadata Server integration, Windows service/tray handoff, installer/updater behavior, and normal package download semantics are not changed by this release.

Normal installed updates preserve NewzDeck settings, provider configuration, Automation data, history, queue state, and user data.
