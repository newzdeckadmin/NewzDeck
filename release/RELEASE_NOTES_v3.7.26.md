# NewzDeck v3.7.26 — High-Speed Entire Group Search

## Performance improvements

- Entire Group Search retrieves headers through up to four concurrent, independent NNTP lanes, constrained by each provider’s existing browsing reserve and an additional global cap across simultaneous searches. A provider with a one-lane allowance continues to use one lane.
- Each worker claims non-overlapping ranges newest-first. Successful fast responses gradually increase the header request window from 5,000 to at most 8,000; slow responses reduce it to at least 2,500. Requests larger than 5,000 retry through bounded 5,000-header subrequests when necessary.
- The overview parser applies decoded text, poster and size filters before expensive media/multipart classification. The complete filter criteria still apply to returned matches, preserving media type, age and extension filtering.
- Progress shows scanned article-number positions, matching posts, active/live worker lanes and successful overview requests. Results can be displayed while the search is scanning, with throttled incremental updates only when the first page is not being actively inspected or scrolled.
- Cancel interrupts in-flight search sockets, releases lane reservations and does not stop SABnzbd download connections.

## No search index or automatic history

- Searches always query live NNTP headers. No persistent header index, result database, automatic search-history writes, cached full-group headers or resume checkpoint is introduced.
- In-memory matches exist only for the current application's search job and can be replaced/pruned. Existing explicitly user-saved search *criteria* remain an optional preexisting feature and are not used for caching results.

## Completeness safeguards

- Every claimed header-number range must succeed (or the job fails visibly); no range is silently skipped. Some article numbers may be unavailable at the provider, as in earlier NewzDeck versions.
- The entire retained article-number range is scanned unless explicitly cancelled or failed. Searches are not made artificially shorter by a match limit.
- Working NNTP provider configuration, private SABnzbd 5.1.2, SABCTools 9.6.3, downloads, Automation, Smart Import, tray/service, image/video galleries, Image Sets, obfuscated binary discovery and yEnc inspection remain intact.
- No user-data migration; Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 unchanged.

## Validation

- The production GroupSearchManager code is tested with controlled NNTP fakes for exact range coverage, non-overlap, multiple workers, low-connection provider behavior, transient retry, permanent failure and cancelled in-flight requests.
- The production overview parser's early filter is compared against complete filtering, including RFC 2047 subjects and extensionless posts.
- The real search polling function is tested for safe live refresh, while all retained v3.7.25 and earlier regression tests remain enabled in the Windows release workflow.

## Windows acceptance

1. Search a large newsgroup with a selective query and watch active search lanes and live result updates.
2. Compare search completeness against v3.7.25 for a group of manageable size (matching posts and related multipart groups), especially media, size and age filters.
3. Test while a large SABnzbd transfer is active; ensure download throughput is not significantly degraded.
4. Cancel during a long-running search; confirm it stops promptly, with no lingering search sessions or download cancellations.
5. Search the same group again: it should retrieve live headers anew, with no persistent index creation.
6. Validate one-connection providers and transient server disconnects; all scanned ranges should be accounted for.

Source, simulated NNTP and Windows CI success cannot substitute for real-world provider throughput and correctness acceptance on the user's Windows system.
