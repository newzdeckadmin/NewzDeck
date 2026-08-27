NewzDeck v3.5.33 - First Source-Complete Windows Release

Release status
--------------
NewzDeck v3.5.33 is the current production release and the first Windows
release in which every NewzDeck-owned executable shipped by the Portable/Setup
package maps to buildable public source.

Source-complete Windows foundation
----------------------------------
- NewzDeck.exe owns first-run private CPython 3.12.10 provisioning directly.
- Legacy NewzDeckBootstrap.exe and NewzDeckCore.exe are retired and are not
  shipped.
- NewzDeckService.exe, NewzDeckTray.exe, NewzDeckPicker.exe,
  NewzDeckThumb.exe and NewzDeckYenc.exe are built from published Go source.
- The established-runtime near-instant startup path is preserved.
- SABnzbd remains NewzDeck's private transfer/post-processing engine.
- Metadata Server v0.3.3 remains the matching server baseline.

v3.5.33 acceptance hardening
----------------------------
- r2 fixed the Windows SAB/Automation completion race by serializing engine
  identity operations, hardening engine.json replacement, and preserving
  completion reconciliation after restart.
- r3 hardened SAB identity/temp-file handling and duplicate Automation
  prevention, retained active targets through import, added fail-closed
  reservation behavior, and persisted imported state.
- r4 made SAB addlocalfile submission ambiguity-safe, adopting an accepted SAB
  queue ID after a connection reset rather than blindly submitting a duplicate.
  It also added bounded control-plane retries and user-facing transport errors.
- r5 added the final Grab-operation exception boundary, sanitized raw
  WinError/Errno 10054/10061 failures, detached Downloads-refresh error
  handling, and prevented local SAB control-channel resets from blacklisting
  releases.

Release integrity
-----------------
Published Portable SHA-256:
a2e7ec5a79904f40e5fb0b864ee420c002b591e01aa64b840b58b026eed90935

Published Setup SHA-256:
03d0f94e3591b48ddcbad9d80f0a015dbe2c5d31ca8c52f83e41c9e971a6d7bb

Published SHA256 manifest asset SHA-256:
d4b3786ac8f8e2d1ae7bf36b691ad5e03d62d34be9a60cca2cff1c92198e5e97

Historical final-r5 acceptance Portable SHA-256:
6b96d0cd8ea92a29e5178d33eea1208de0309c70cf0b3e6e04d40ebf65cc2e39

The r5 value is retained as pre-publication acceptance provenance. The
published Portable hash is the integrity value for the v3.5.33 asset currently
distributed from GitHub.

License
-------
NewzDeck-owned source is licensed under GNU GPL v3.0 only. Third-party
components retain their own licenses. See LICENSE and THIRD_PARTY_NOTICES.md.