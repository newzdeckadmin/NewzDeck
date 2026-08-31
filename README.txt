NewzDeck v3.6.21
Newsgroups Image Browsing & Related Media

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.21

- Direct loose-image downloads from Newsgroups now finish in the configured
  Download Folder root without extra image- or job-named folders.
- Group Related Media now uses a dedicated Related Media side pane instead of
  mixing image sets into the main browsing stream.
- Continuous browsing updates sets incrementally while keeping the main scroll
  stable and avoiding full-gallery regroup/rebuild work.
- Large broken image sets are rejected with bounded health probes instead of
  spending a long time walking missing members one by one.
- Long Continuous sessions use measured DOM windowing plus an incremental set
  index to reduce Chromium layout and regrouping overhead.
- Related Media covers use stable set ownership, bounded sequential retrieval,
  reserved scheduler capacity, cached-cover activation, and visible-task queue
  promotion so cards do not remain stuck waiting for an offscreen-priority job.
- Missing/corrupt image failures avoid redundant preview recovery and failed-card
  cleanup is batched to reduce browsing stalls.
- Diagnostics now expose Related Media cover queue, activation, promotion, and
  timing state for troubleshooting.

NewzDeck v3.6.20 SAB/Downloads/Automation reliability behavior is preserved.
Normal installed updates preserve settings, provider configuration, Automation
data, history, queue state, and user data.
