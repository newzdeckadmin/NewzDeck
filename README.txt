NewzDeck v3.5.33 — Source-Complete Build Foundation

NewzDeck v3.5.33 keeps the v3.5.32 application/download behavior while making
all NewzDeck-owned Windows executables in the portable package rebuildable from
GPLv3 source.

Key changes
-----------
- NewzDeck.exe now owns first-run private CPython provisioning directly. The
  legacy NewzDeckBootstrap.exe and NewzDeckCore.exe are retired and no longer
  shipped.
- NewzDeckService.exe, NewzDeckTray.exe, NewzDeckPicker.exe,
  NewzDeckThumb.exe and NewzDeckYenc.exe are rebuilt from published source.
- The official CPython 3.12.10 Windows embeddable x64 runtime is downloaded on
  first launch and pinned to SHA-256:
  4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3
- The v3.5.32 near-instant established-runtime startup path is preserved.
- Download Engine v2 / SABnzbd 5.1.1 behavior is unchanged.
- Metadata Server v0.3.3 remains the matching server baseline.

License
-------
NewzDeck-owned source is licensed under GNU GPL v3.0 only. Third-party
components retain their own licenses. See LICENSE.txt and THIRD_PARTY_NOTICES.txt.

Acceptance revision 2
---------------------
- Fixes a Windows engine.json read/replace race that could starve the Automation
  completion monitor after SAB finished an episode, preventing Smart Import,
  rename, and library move.
- Completed tracked Automation jobs are reconciled again after startup, so an
  already-downloaded episode can be imported without downloading it again.
