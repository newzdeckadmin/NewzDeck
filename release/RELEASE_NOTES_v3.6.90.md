# NewzDeck v3.6.90 - Windows Defender Picker Compatibility & Release Gate Hardening

v3.6.90 is a Windows packaging and release-gate hotfix built on the functionally stable v3.6.89 application baseline. It responds to a Microsoft Defender machine-learning detection that identified `NewzDeckPicker.exe` inside the official v3.6.89 Portable ZIP as `Trojan:Win32/Wacatac.B!ml`.

## What was verified before this change

The v3.6.89 release artifact published by GitHub Actions matched its published SHA-256, and the flagged `NewzDeckPicker.go` source was unchanged from v3.6.88. The detection therefore points at the compiled Picker binary/build signature rather than the v3.6.89 Smart Import application changes.

`NewzDeckPicker.exe` performs legitimate native Windows integration work such as folder selection and short-lived update/installer handoff. Until v3.6.90 it was built with NewzDeck's stripped default Go flags: `-s -w -H windowsgui -buildid=`. NewzDeck previously encountered a Defender false positive on the yEnc helper and resolved that build-signature problem by retaining normal Go build metadata.

## Picker Defender-compatibility build

v3.6.90 changes the Picker build profile only:

- `NewzDeckPicker.go` behavior is unchanged.
- `NewzDeckPicker.exe` is built with `-H windowsgui`, retaining the normal Go build ID and symbol/debug metadata instead of applying `-s`, `-w`, and an empty build ID.
- `SOURCE_MANIFEST.json` records the Picker-specific build override and states that source behavior did not change.
- The Windows release workflow rejects a Portable payload if Picker has no Go build ID or if `go tool nm` cannot read its symbols.
- The existing Defender-accepted `NewzDeckYenc.exe` LF/Linux provenance and pinned binary remain unchanged.

This deliberately mirrors the successful yEnc remediation while leaving Picker functionality alone. Because Microsoft Defender cloud signatures can change independently, the final public v3.6.90 binary still needs to be observed on a real Windows Defender installation; the release pipeline cannot claim a Microsoft verdict before publication.

## Release gate repair

Review of the v3.6.89 GitHub Actions log exposed a separate release-safety weakness: several hash-based Python regression guards returned nonzero after Windows line-ending conversion, but PowerShell continued to later commands and the workflow ultimately reported success.

v3.6.90 hardens that path:

- The Windows release checkout disables `core.autocrlf`, sets LF as the working-tree EOL, and force-checks the source back out before validation.
- The main source-validation step enables `$PSNativeCommandUseErrorActionPreference = $true` under PowerShell 7 with `$ErrorActionPreference = 'Stop'`.
- Any nonzero Python, Node, Go, or other native validation process now terminates the release step immediately.
- The complete carried regression chain is still executed before any GitHub Release is created.

## Preserved application behavior

v3.6.90 intentionally carries v3.6.89 behavior forward unchanged apart from version identity:

- duplicate-fingerprint Smart Import reconciliation and Wanted clearing
- v3.6.88 dynamic-range import trust reconciliation
- v3.6.87 dynamic-range evidence authority
- v3.6.86 Automation/Search cache-snapshot performance
- Newsgroup Browser architecture and tuning
- private SABnzbd 5.1.2 integration
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31

No library rescan, cache clear, or Automation reconfiguration is required.
