# NewzDeck v3.6.80 - UX Final Consistency & Accessibility

v3.6.80 completes NewzDeck's current staged broad UX polish program with a presentation-only final consistency and accessibility pass. Functional application logic remains frozen and the proven Defender-clean yEnc release path remains unchanged.

## UX Polish Phase 4

This pass focuses on consistency, keyboard clarity and Windows scaling/reduced-motion presentation without changing what any control does or when any state occurs.

- Dialog families receive a more consistent radius, shadow, header hierarchy and close-button placement.
- Settings, Automation, Discover, Downloads and Diagnostics supporting copy uses more consistent line-height and section rhythm.
- Existing navigation, tabs, dialog controls and action buttons gain one predictable high-contrast keyboard focus treatment.
- Disabled common controls are visually distinguished as intentionally unavailable without changing their disabled logic.
- Existing Settings/Add Media placeholders, labels and helper text receive small readability/consistency refinements.
- Status chips and established action rows are aligned visually without changing content, actions or state.
- Constrained/high-scaling Windows viewports receive safer dialog insets through responsive CSS only.
- `prefers-reduced-motion` disables only nonessential polish transitions; loading/activity semantics and application timing are untouched.

## Deliberately unchanged

- `server.py`, `sab_engine.py`, `automation_engine.py` and `app.js` behavior; only their release identity changes
- Newsgroup Browser JavaScript logic, page geometry, thumbnail scheduling/scoring and virtualization
- Image thumbnail HTTP admission limit of 5 and high-connection Video thumbnail ceiling of 6
- 24 MB Video sample size, 12-segment cap, 800/800/1000 header strategy and All Posts resolver timing
- provider/NNTP allocation and adaptive preview/download allocation
- private SABnzbd 5.1.2, Downloads state/history/post-processing behavior and terminal-history schema 3
- Settings atomic persistence/retry behavior
- Smart Import and Automation search/reconciliation/import semantics
- Discover metadata/data behavior and Metadata Server v0.3.3
- Windows launcher, service, tray, picker and installer handoff behavior
- `NewzDeckYenc.go` and the decoder protocol/behavior

## Defender-clean build pipeline preserved

v3.6.80 carries forward the v3.6.78 production safeguard unchanged: `NewzDeckYenc.exe` is built from the exact canonical LF Git source in the pinned Linux GitHub Actions job and release packaging refuses any helper that does not match the accepted SHA-256 `4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad`.

## Regression strategy

`validate-v3680-regressions.py` proves the functional runtime files normalize byte-for-byte to v3.6.79 after removing only release identity, requires the exact v3.6.79 stylesheet prefix plus the reviewed Phase 4 CSS suffix, rejects protected Newsgroup Browser/performance selectors from the new suffix, and verifies the Defender LF/Linux build/handoff/hash gates remain present.
