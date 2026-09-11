# NewzDeck v3.6.73 — Thumbnail Task Identity & Visibility Telemetry

v3.6.73 is a narrow Newsgroup Browser reliability/observability release built on v3.6.72. It addresses the source-level stale-thumbnail-task defect identified after heavy Video browsing diagnostics while preserving accepted scheduler and download behavior.

## Fixed

- **Stable queued thumbnail identity.** Every queued gallery or Related Media thumbnail task verifies that its stored array index still refers to its stable `sourceArticleKey` immediately before execution.
- **Safe relocation.** If continuous browsing/re-rendering moved that article to a different index, the task relocates to the live article and updates the task index used for completion/error UI.
- **Safe stale-task discard.** If the source article no longer exists, or the live article no longer has complete compatible Image/Video media matching the queued task kind, the task is discarded locally rather than calling a thumbnail endpoint with mismatched data.
- **Existing safeguards preserved.** Browse session, gallery generation, provider/group context, cancellation, cache, retry/non-retryable policy, Related Media reservation, and global scheduler limits are unchanged.

## Passive browsing telemetry schema 10

Schema 10 retains the existing `thumbnail_queue` metric as **total queue age** and adds:

- `thumbnail_prefetch_dwell` — time spent queued before first becoming visible; if a task executes entirely offscreen, this equals its queue age.
- `thumbnail_visible_wait` — time from first visibility until execution starts.
- `thumbnail_task_identity` — zero-duration passive decision samples with `relocated`, `stale-missing`, or `incompatible-media` reasons when stable task identity handling is exercised.

These metrics do not create browsing, thumbnail, preview, or provider traffic. They exist to distinguish actual on-screen thumbnail delay from time accumulated while prefetch work was offscreen.

## Deliberately unchanged

- Image thumbnail HTTP admission limit of 5
- high-connection Video thumbnail ceiling of 6
- adaptive preview/download budget
- 24 MB Video sample size and 12-segment cap
- 800-header first paint / 800-header OVER-XOVER chunks / 1,000-item progressive threshold
- All Posts automatic 1.4 s soft / 3.0 s max and manual 1.8 s soft / 4.2 s max resolver waits
- v3.6.69 Settings atomic-replace retry behavior
- provider/NNTP allocation and native decode architecture
- private SABnzbd 5.1.2
- terminal download-history schema 3
- Smart Import, Automation reconciliation, Discover and Metadata Server v0.3.3

## Acceptance target

Heavy continuous Image/Video browsing should no longer produce `/api/thumbnail/video` HTTP 400 `Invalid video thumbnail request` failures caused by a queued task executing against a different article occupying its old array index. Schema-10 telemetry should show whether long queue ages were accumulated offscreen versus while actually visible, without retuning the scheduler.
