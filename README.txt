NewzDeck v3.6.91 - Defender Picker Release Gate Compatibility Fix

This release completes the Windows Defender Picker packaging remediation after the v3.6.90
canonical workflow correctly stopped on obsolete historical whole-builder fingerprint guards.

NewzDeckPicker.go application behavior is unchanged. The normal-metadata -H windowsgui Picker
build, Defender-clean yEnc pipeline, Automation/Wanted/Smart Import behavior, SABnzbd 5.1.2,
Metadata Server v0.3.3, and Diagnostic Collector v1.0.31 are preserved.

See release/RELEASE_NOTES_v3.6.91.md for details.
