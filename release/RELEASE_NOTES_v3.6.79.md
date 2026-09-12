# NewzDeck v3.6.79 - UX Feedback & State Clarity

v3.6.79 resumes NewzDeck's staged UX polish program after the v3.6.78 Defender build-pipeline hotfix. This release is deliberately presentation-only: functional application logic remains frozen and the proven Defender-clean yEnc release path is preserved unchanged.

## UX Polish Phase 3

This pass focuses on what NewzDeck communicates while work is happening or when something needs attention, without changing when those states occur or what any action does.

- Success, error and informational toasts have clearer visual hierarchy and outcome accents.
- Settings test results, callouts and TMDB/status notices are easier to distinguish at a glance.
- Metadata, release/indexer, health and download errors use a more consistent error surface while retaining the same text, actions and error semantics.
- Discover/release loading states and Discover/Downloads/Automation/Diagnostics empty states have more intentional structure rather than appearing like unfinished whitespace.
- Automation activity feedback receives a subtle visual emphasis while preserving the existing activity lifecycle.
- Existing metadata rows, release rows, Settings checks, download statistics and status cards receive restrained hover/focus feedback only.
- Existing busy-button behavior is unchanged; only its visual state is clarified.
- Small-screen toast presentation is tightened without changing notification timing.

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

v3.6.79 carries forward the v3.6.78 production safeguard unchanged: `NewzDeckYenc.exe` is built from the exact canonical LF Git source in the pinned Linux GitHub Actions job and release packaging refuses any helper that does not match the accepted SHA-256 `4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad`.

## Regression strategy

`validate-v3679-regressions.py` proves the functional runtime files normalize byte-for-byte to v3.6.78 after removing only release identity, requires the exact v3.6.78 stylesheet prefix plus the reviewed Phase 3 CSS suffix, rejects protected Newsgroup Browser/performance selectors from the new suffix, and verifies the v3.6.78 Defender LF/Linux build/handoff/hash gates remain present.
