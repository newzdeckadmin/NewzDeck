# NewzDeck v3.6.76 - UX Polish Phase 1: Readability & Visual Rhythm

v3.6.76 begins NewzDeck's staged overall UX polish work. This release is intentionally conservative: it changes presentation only and does not retune or rewrite working application functionality.

## Improved: readability and visual hierarchy

- Increased undersized secondary labels, captions and help text across the main application chrome, Discover, Automation, Downloads, Settings and common dialogs.
- Improved line-height and supporting-text contrast so dense screens are easier to scan without making the interface feel oversized.
- Made sidebar section labels, provider context, top-action labels and version/status copy more legible while preserving the existing navigation geometry.
- Improved Discover card metadata and detail copy without changing poster dimensions, image loading, recommendations, filters or title-detail behavior.
- Improved Automation card metadata/status/footer copy while preserving the accepted 2:3 poster ratio, fixed card-row geometry, monitoring controls and all Automation actions.
- Improved Downloads statistics labels, package metadata and error readability without changing tabs, queue state, post-processing, ETA/speed logic or Download Statistics calculations.
- Improved Settings/modal labels, descriptions and help text without changing saved values, form semantics or action wiring.
- Empty/help states now read more clearly as guidance rather than faint/disabled-looking content.

## Deliberately unchanged

- Newsgroup Browser JavaScript logic, thumbnail scheduling/scoring and gallery virtualization
- Image thumbnail HTTP admission limit of 5
- high-connection Video thumbnail ceiling of 6
- adaptive preview/download allocation and provider/NNTP allocation
- 24 MB Video sample size and 12-segment cap
- 800-header first paint / 800-header OVER-XOVER chunks / 1,000-item progressive threshold
- All Posts resolver timing and schema-11 browsing diagnostics
- download queue/state projection, post-processing and private SABnzbd 5.1.2
- terminal download-history schema 3
- Settings persistence/atomic-replace behavior
- Smart Import and Automation reconciliation/import ownership
- Discover metadata/cache/data behavior and Metadata Server v0.3.3
- Windows launcher/service/tray runtime architecture
- NewzDeckYenc.go decoder behavior and the v3.6.75 Defender-compatible yEnc build profile

## Regression strategy

`validate-v3676-regressions.py` proves that the functional application source normalizes byte-for-byte to the v3.6.75 production baseline after removing only the v3.6.76 identity bump. It also proves that `styles.css` consists of the exact v3.6.75 stylesheet plus the single guarded UX override block, then rechecks all frozen browsing/concurrency/sample/Settings/SAB/yEnc protections.
