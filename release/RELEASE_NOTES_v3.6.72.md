# NewzDeck v3.6.72 — Browse Timeout Error Attribution

v3.6.72 is a focused error-attribution release driven by the v3.6.71 production capture where normal Video browsing briefly displayed **“A required local service was temporarily unavailable”** even though the NewzDeck backend remained healthy and browsing recovered.

## Fixed

- **Provider timeout attribution.** An HTTP error returned by `/api/articles` containing a timeout now reports that the **news provider timed out while article headers were loading** instead of claiming a required local service was unavailable.
- **Provider reset attribution.** An HTTP error returned by `/api/articles` that identifies a connection reset now reports the provider reset and makes clear browsing can continue/retry.
- **Local backend wording is reserved for local transport failures.** Browser/network failures such as localhost connection refusal, failed fetch, reset, or local request timeout keep NewzDeck-local recovery wording.
- **No double translation of HTTP errors.** Once an HTTP response has been classified, the generic network catch path does not reclassify it.
- **Automation Grab wording retained.** Existing download-engine transport guidance remains source-aware for Grab operations.
- **Complete Video policy reason labels.** v3.6.71's schema-9 `video_thumbnail_policy` labels now use compact `browser-decode` / `-nr` tokens so supported demand/sample combinations remain below the existing 48-character reason limit.

## Diagnostics

Diagnostic Collector v1.0.29 adds a passive `live/browse-request-failure-summary.json` derived only from already-collected diagnostics and endpoint timing data. It separates current-runtime article overview timeout/reset/connection-limit/DNS failures from Collector-observed localhost snapshot failures. It adds **no browsing requests or synthetic load**.

## Deliberately unchanged

- browsing-performance schema 9
- Image thumbnail HTTP admission limit of 5
- high-connection Video thumbnail ceiling of 6
- 24 MB Video sample size and 12-segment cap
- 800-header first paint / OVER-XOVER chunking and 1,000-item progressive threshold
- v3.6.68 All Posts resolver accumulator and wait bounds
- v3.6.69 Settings atomic-replace retry behavior
- provider/NNTP allocation and native decode architecture
- private SABnzbd 5.1.2
- terminal download-history schema 3
- Smart Import, Automation reconciliation, Discover and Metadata Server v0.3.3

## Acceptance target

When an upstream `/api/articles` timeout occurs, the UI should identify the **news provider**, not a local service. Genuine localhost transport failures should still identify the local NewzDeck backend. Collector v1.0.29 should expose the current-runtime article failure classification and localhost collection health side by side.
