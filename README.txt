NewzDeck v3.6.92 - Defender Handoff Reduction & Picker Simplification

This release removes the Defender-sensitive copied update-handoff executable and reduces
NewzDeckPicker.exe to folder-selection duties only. About & Updates now launches the
checksum-verified Setup EXE directly, and Setup no longer executes Picker during upgrade.

Users upgrading from v3.6.91 or another build whose old Picker is blocked by Microsoft
Defender should run NewzDeck_v3.6.92_Setup.exe manually once. Future updates from v3.6.92
use the direct verified-Setup path.

SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31, Automation, Wanted,
Smart Import, Newsgroup Browser behavior, and the accepted yEnc helper are preserved.

See release/RELEASE_NOTES_v3.6.92.md for details.
