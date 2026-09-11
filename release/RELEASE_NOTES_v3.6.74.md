# NewzDeck v3.6.74 — Video Cancellation Overlap Diagnostics

v3.6.74 is a diagnostics-only Newsgroup Browser observability release built on v3.6.73. It does not retune thumbnail scheduling, provider allocation, concurrency, sampling, downloads, or automation behavior.

## Added: correlated Video thumbnail lifecycle evidence

- Every Video thumbnail HTTP attempt receives a short local request ID carried to `/api/thumbnail/video`.
- The request records the browser's logical Video/overall thumbnail active counts at dispatch.
- The backend tracks each request from endpoint entry through final exit.
- When a newer browse session supersedes an older session, active older Video requests are marked as superseded without changing their execution policy.
- Existing browse-session cancellation checks record when cancellation is first detected by backend work.

## Passive browsing telemetry schema 11

Schema 11 retains all schema-10 queue/identity evidence and adds:

- `video_thumbnail_cancel_detect_delay` — time from server registration of the newer browse session until obsolete Video work first detects cancellation.
- `video_thumbnail_cancel_drain` — time from that session supersession until the obsolete Video endpoint finally exits.
- current-session versus superseded active/peak Video endpoint counts.
- bounded recent Video request lifecycle records containing request ID, client logical active counts, lifetime, superseded state, cancellation detection, detection delay, and drain duration.
- client lifecycle/cancellation timing samples used only for correlation and aggregate diagnostics.

No collector or application diagnostic feature creates synthetic browsing or thumbnail workload.

## Deliberately unchanged

- thumbnail scheduler scoring formula
- Image thumbnail HTTP admission limit of 5
- high-connection Video thumbnail ceiling of 6
- adaptive preview/download budget
- 24 MB Video sample size and 12-segment cap
- 800-header first paint / 800-header OVER-XOVER chunks / 1,000-item progressive threshold
- All Posts automatic 1.4 s soft / 3.0 s max and manual 1.8 s soft / 4.2 s max resolver waits
- v3.6.69 Settings atomic-replace retry behavior
- provider/NNTP allocation and native decode architecture
- stable thumbnail task identity behavior from v3.6.73
- private SABnzbd 5.1.2
- terminal download-history schema 3
- Smart Import, Automation reconciliation, Discover and Metadata Server v0.3.3

## Diagnostic acceptance target

Under aggressive Continuous Browse/session switching, schema-11 evidence should distinguish:

1. current-session Video work that remains within the browser's six-request logical ceiling; and
2. older superseded requests that are still draining server-side after the browser moved on.

If backend peaks above six are explained by superseded work, the next optimization can target cancellation/drain latency rather than raising concurrency. If superseded active work remains zero during an above-six backend peak, the evidence instead points to another current-session admission path.
