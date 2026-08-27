NewzDeck v3.5.35 - Installer & Tray Reliability

NewzDeck v3.5.35 folds the accepted v3.5.34 application reliability work into
a clean full Windows build and fixes the installer/tray defects found during
final v3.5.34 installation testing.

Key changes
-----------
- Preserves the accepted v3.5.34 updater, sleep/resume, Downloads polling,
  Completed-history ordering, TMDB attribution, localhost security, error
  sanitization, Watch Folder fairness, Automation and Smart Import behavior.
- Closes NewzDeckTray.exe proactively during an installed upgrade before files
  are replaced, so users are not asked to kill the tray process manually.
- Repairs the existing-service upgrade path using supported Inno Setup runtime
  environment/path functions instead of the invalid {userprofile} constant.
- Repairs the tray right-click menu using the standard foreground-window and
  TPM_RETURNCMD notification-area pattern.
- Adds an explicit tray WM_CLOSE/Exit path used by both the menu and installer.
- Keeps the tray context menu responsive even when the backend is unavailable.

Compatibility
-------------
- Download Engine v2 / private SABnzbd behavior is unchanged.
- Metadata Server v0.3.3 remains compatible.
- Existing user state under %LOCALAPPDATA%\NewzDeck is preserved.

License
-------
NewzDeck-owned source is licensed under GNU GPL v3.0 only. Third-party
components retain their own licenses. See LICENSE.txt and THIRD_PARTY_NOTICES.txt.
