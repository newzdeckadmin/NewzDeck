# NewzDeck v3.6.60 — Discover Library Index & Cache Write Coalescing

v3.6.60 is a narrow Discover local-data-path performance release based on the first v3.6.59 production diagnostic captured with Diagnostic Collector v1.0.14. It preserves Metadata Server v0.3.3, private SABnzbd 5.1.2, v3.6.59 stale-while-revalidate Detail behavior, and the v3.6.58 Automation reconciliation stack.

## Changes

- **Signature-aware Discover library index.** Discover no longer calls `_library()` and linearly scans the full `media-library.json` for every card. The first Discover lookup for a library generation parses the file once and builds direct metadata-provider/ID, TMDB-ID, and normalized-title lookup maps. Subsequent cards reuse that index until the library file signature changes.
- **For You/library taste reuse.** Discover recommendation genre scoring, recommendation seeds, and taste signatures reuse the same indexed library generation rather than reparsing the Automation library again within the same Discover workload.
- **Metadata-cache write coalescing.** Successful metadata responses update the in-process cache immediately, but bursty `_cache_put()` calls are persisted by one short-delay compact atomic flush rather than rewriting the entire multi-megabyte `metadata-cache.json` once per response.
- **Peer-safe coalesced persistence.** A non-blocking cross-process cache-write guard serializes v3.6.60 desktop/service flushes. Before persistence, NewzDeck rechecks the disk signature and merges any peer-process cache change while preserving all local dirty responses in memory until a flush succeeds.
- **More precise Discover diagnostics.** Diagnostics now separate metadata-cache write requests from actual disk writes and expose coalesced requests, pending requests, dirty keys, flush deferrals/failures, library-index records/hits/misses/builds/build timing, and route sample count/average.
- **Honest tiny-sample percentiles.** Discover p50/p95 calculations now use linear interpolation. With only two samples, p50 is their midpoint rather than whichever endpoint Python rounding happens to select.

## Production evidence addressed

The first v3.6.59 acceptance capture showed that metadata-cache read reuse worked, but also showed two remaining local bottlenecks: cached Discover Detail requests still spent several seconds decorating titles while a roughly 5 MB Automation library was repeatedly reparsed/scanned, and 16 metadata-cache responses caused about 16 seconds of cumulative cache-write work, including an individual write above 3.6 seconds. v3.6.60 targets those two measured bottlenecks directly.

## Validation

The v3.6.60 regression guard proves that unchanged Discover card lookups build the library index exactly once, metadata/TMDB/title fallback matching remains compatible, a changed `media-library.json` causes one rebuild, dirty metadata responses are immediately readable before persistence, a six-response burst collapses to one physical compact write, peer-process cache entries are merged before that write, dirty state clears only after success, and two-sample percentile/average telemetry is mathematically coherent.

The v3.6.59 regression guard was migrated to the coalesced-write contract and still passes. The v3.6.58 Automation runtime reconciliation regression guard also still passes against v3.6.60.

A synthetic validation fixture with 3,238 library records measured the first library index build/lookup at about 17 ms and 200 subsequent indexed lookups at about 0.005 ms average on the validation host. This is a synthetic measurement, not a promise of identical production timings.

## Preserved behavior

v3.6.59 stale persisted Detail rendering, 8-second true-cold Detail budget, bounded hover prefetch, prefetch-vs-explicit viewed-history semantics, metadata-cache parsed-memory reuse, Metadata Server v0.3.3, v3.6.58 Automation orphan/state reconciliation, Smart Import ownership, Integrity Hold behavior, Library Integrity, Windows service/tray handoff, Setup behavior, and private SABnzbd 5.1.2 remain unchanged.
