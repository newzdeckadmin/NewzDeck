# NewzDeck v3.6.75 - Windows Defender Compatibility

v3.6.75 is a narrowly scoped Windows build/distribution compatibility release built on v3.6.74.

It addresses a Microsoft Defender false-positive condition observed against the historical stripped `NewzDeckYenc.exe` helper. The same detection began blocking older releases that had previously downloaded normally, while the unchanged yEnc source rebuilt with standard Go build metadata passed Defender testing.

## Fixed: Defender-compatible yEnc helper build

- `src/windows/NewzDeckYenc.go` is unchanged from v3.6.74.
- `NewzDeckYenc.exe` continues to use Go 1.23.2, `GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`, and `-trimpath`.
- Only this helper now uses `-ldflags="-H windowsgui"`.
- The normal Go build ID and symbol/debug metadata are retained for this helper.
- The previous `-s -w` stripping and empty `-buildid=` are no longer applied to `NewzDeckYenc.exe`.
- The other five NewzDeck-owned Windows executables keep the established `-s -w -H windowsgui -buildid=` profile.

## Acceptance evidence

Before authorizing this release:

1. An isolated `NewzDeckYenc.exe` rebuilt with the new profile downloaded and scanned without a Defender detection.
2. A full v3.6.74 Portable package containing the Defender-compatible helper, with all other application files unchanged, also downloaded and scanned without a Defender detection.
3. A final exact-production-source Test C used the unchanged `NewzDeckYenc.go` Git blob `38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15`, Go 1.23.2, `-trimpath`, and `-ldflags="-H windowsgui"`; that exact-source helper also downloaded and scanned without a Defender detection. Its acceptance-test binary SHA-256 was `4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad`.

The production release workflow verifies the yEnc build override in `SOURCE_MANIFEST.json`, freezes the yEnc source blob, and requires the generated helper to retain a Go symbol table before the release can be published.

## Deliberately unchanged

- `NewzDeckYenc.go` decoder logic and stdin/stdout protocol
- browsing-performance telemetry schema 11
- thumbnail scheduler scoring
- Image thumbnail HTTP admission limit of 5
- high-connection Video thumbnail ceiling of 6
- adaptive preview/download allocation
- 24 MB Video sample size and 12-segment cap
- 800-header first paint / 800-header OVER-XOVER chunks / 1,000-item progressive threshold
- All Posts resolver timing
- provider/NNTP allocation
- Settings atomic-replace retry behavior
- private SABnzbd 5.1.2
- terminal download-history schema 3
- Smart Import
- Automation reconciliation/import ownership
- Discover
- Metadata Server v0.3.3
- Windows launcher/service/tray runtime architecture

## Release guard

`validate-v3675-regressions.py` makes this a build-only change. It verifies the exact historical yEnc source blob, the one-binary build override, the canonical workflow checks, and the carried-forward browsing/download stability protections.
