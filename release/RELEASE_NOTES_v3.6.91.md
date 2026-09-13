# NewzDeck v3.6.91 - Defender Picker Release Gate Compatibility Fix

NewzDeck v3.6.91 is a narrowly scoped Windows release-pipeline compatibility hotfix built on the v3.6.90 source state.

## Fixed

- Keeps the v3.6.90 `NewzDeckPicker.exe` Defender-compatibility build (`-H windowsgui`) unchanged.
- Replaces the obsolete v3.6.79/v3.6.80 historical regression assertions that required the entire `build-portable.py` file to remain byte-identical to the old v3.6.78 builder. Those assertions were incompatible with the intentional Picker build-profile exception added in v3.6.90.
- Historical guards now validate the protected helper invariants instead: the accepted yEnc profile, the original yEnc/default routing expression, the Picker-specific normal-metadata profile, and the unchanged native helper sources.
- Adds a v3.6.91 guard so a future release cannot silently reintroduce the obsolete whole-builder hash pin.

## Preserved

- `NewzDeckPicker.go` behavior is unchanged.
- The v3.6.90 LF checkout and fatal native-command release gates remain enabled.
- Automation, Wanted, Smart Import, Newsgroup Browser, download behavior, and all v3.6.89 application functionality are unchanged apart from version identity.
- SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31, and the Defender-clean yEnc helper pipeline remain unchanged.

This roll-forward is necessary because the immutable `v3.6.90` source tag already exists while its GitHub Actions release build stopped before producing release assets.
