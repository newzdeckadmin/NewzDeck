# NewzDeck v3.6.77 - UX Polish Phase 2: Layout & Control Consistency

v3.6.77 continues NewzDeck's staged overall UX polish work. This release is intentionally presentation-only: it improves alignment, spacing, control consistency and responsive dialog layout without changing working application functionality.

## Improved: control consistency and layout rhythm

- Common primary, secondary and destructive action buttons now share a consistent 40 px control height, internal alignment and spacing.
- Settings receives more consistent field height, grid spacing, check-row padding, textarea treatment and footer alignment.
- Add Media / Automation dialogs receive more breathing room, cleaner edge padding, more consistent control height and better responsive spacing at narrower window widths.
- Automation library panels, section headings and supporting rows receive a more consistent spacing rhythm while preserving the accepted 2:3 poster geometry and card structure.
- Discover filter controls and section headings are aligned more consistently without changing posters, metadata loading, recommendations, filtering or title-detail behavior.
- Downloads tabs, statistics, rows and action groups receive spacing/alignment polish without changing queue state, progress, speed, ETA, post-processing or Download Statistics calculations.
- Keyboard focus indicators are clearer, and common action buttons receive subtle press feedback without changing click behavior.

## Deliberately unchanged

- Newsgroup Browser JavaScript logic, page geometry, thumbnail scheduling/scoring and gallery virtualization
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

`validate-v3677-regressions.py` proves that the functional application files normalize byte-for-byte to the v3.6.76 production baseline after removing only the v3.6.77 identity bump. It also proves that `styles.css` is the exact v3.6.76 production stylesheet plus the single guarded Phase 2 UX override block, then rechecks all frozen browsing/concurrency/sample/Settings/SAB/yEnc protections.
