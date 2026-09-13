NewzDeck v3.6.93 - Defender Handoff Release Gate Recovery

This release carries the reviewed v3.6.92 application behavior forward unchanged
while repairing the canonical Windows installed-upgrade smoke test that still tried
to launch the retired Picker --taskbar-fix mode.

Users upgrading from v3.6.91 or another build whose old Picker is blocked by Microsoft
Defender should run NewzDeck_v3.6.93_Setup.exe manually once. The v3.6.93 application
then uses the direct checksum-verified Setup update path introduced by v3.6.92.

NewzDeckPicker.exe remains folder-picker-only. The release workflow now simulates a
legacy locked Picker with a dedicated inert smoke binary instead of invoking removed
production behavior.

See release/RELEASE_NOTES_v3.6.93.md for details.
