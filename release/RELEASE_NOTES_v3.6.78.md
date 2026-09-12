# NewzDeck v3.6.78 - Windows Defender LF Build Pipeline Hotfix

v3.6.78 is a narrow production build-pipeline hotfix built directly on v3.6.77. No application feature, UX, browsing, download, Automation, Smart Import, Discover, Settings, SAB or yEnc decoder behavior is changed.

## Fixed: Defender false-positive build divergence

The v3.6.75 build-profile change removed stripping and the forced empty Go build ID from `NewzDeckYenc.exe`, but later investigation proved an important build-environment difference remained: the Windows GitHub Actions checkout compiled CRLF working-tree source bytes, while the Defender acceptance tests that passed used the exact canonical LF Git source bytes on Linux.

Test D confirmed that the complete official v3.6.77 Portable payload passes Windows Defender when only `NewzDeckYenc.exe` is replaced by the exact LF/Linux Test C helper.

v3.6.78 makes that accepted representation the canonical release path:

- A dedicated `ubuntu-24.04` GitHub Actions job checks out the release source with LF policy and verifies `src/windows/NewzDeckYenc.go` SHA-256 is exactly `ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd`.
- The helper is built with Go 1.23.2, `GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`, `-trimpath`, and `-ldflags='-H windowsgui'`.
- The Linux job refuses to upload the helper unless its SHA-256 is exactly `4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad`, the exact Test C/Test D binary accepted by Defender.
- The Windows release job downloads that verified helper and `build-portable.py` copies it into the production payload instead of rebuilding yEnc from the Windows CRLF working tree.
- Setup/Portable validation rechecks the accepted helper hash, source provenance, normal Go symbol table and manifest metadata before publication.

## Deliberately unchanged

- `NewzDeckYenc.go` source and decoder protocol/behavior
- all v3.6.77 UX Phase 1/2 CSS and layout work
- Newsgroup Browser JavaScript logic, page geometry, thumbnail scheduling/scoring and gallery virtualization
- Image thumbnail HTTP admission limit of 5 and high-connection Video thumbnail ceiling of 6
- 24 MB Video sample size, 12-segment cap, 800/800/1000 header strategy and All Posts resolver timing
- provider/NNTP allocation and adaptive preview/download allocation
- download queue/state projection, post-processing and private SABnzbd 5.1.2
- terminal download-history schema 3
- Settings persistence/atomic-replace behavior
- Smart Import, Automation reconciliation/import ownership and Discover data behavior
- Metadata Server v0.3.3
- Windows launcher/service/tray runtime architecture

## Regression strategy

`validate-v3678-regressions.py` proves the functional application files normalize byte-for-byte to v3.6.77 after removing only release identity, requires the exact v3.6.77 stylesheet, freezes the yEnc source Git blob, and verifies the dedicated LF/Linux helper build/handoff/hash gates are present in both the builder and canonical release workflow.
