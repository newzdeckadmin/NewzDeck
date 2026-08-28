# NewzDeck v3.6.2 — Tray Upgrade Lock Reliability

NewzDeck v3.6.2 is a focused installed-upgrade hotfix for a second Windows file-lock race discovered while upgrading a real v3.5.x/v3.6.x installation. It preserves the accepted v3.6.0 UI/UX Overhaul and the v3.6.1 background-service shutdown fix.

## Fixed

- **Tray executable file lock during Setup** — v3.6.1 could still show `DeleteFile failed; code 5` / `Access is denied` while replacing `NewzDeckTray.exe`.
- **Window-close/process-exit race removed** — Setup no longer treats disappearance of the hidden `NewzDeckTrayWindow` as proof that the tray executable is unlocked. It captures the owning process before sending `WM_CLOSE` and waits for that process itself to exit.
- **Bounded hung-tray recovery** — if the tray does not exit after the graceful wait, Setup terminates the exact process owning the NewzDeck tray window and performs a second bounded exit wait.
- **Fail-safe upgrade gate** — if tray shutdown still cannot be confirmed, Setup stops before overlaying application files instead of entering a partial upgrade.
- **Delayed-exit tray regression test** — GitHub Actions now keeps the tray smoke executable alive for six seconds after its hidden window disappears. This specifically reproduces the race that the v3.6.1 window-only smoke helper missed.

## Preserved

The v3.6.1 service upgrade fix remains intact: Setup uses the existing NewzDeck service helper and waits for the Windows Service Control Manager to confirm `STOPPED` before replacing `NewzDeckService.exe`.

The complete v3.6.0 UI/UX Overhaul is unchanged, including reorganized navigation, readability/contrast improvements, Newsgroups tab layout, Discover detail treatment, Automation alignment, utility controls, and responsive component styling.

All accepted v3.5.x runtime behavior remains preserved: private SAB high-throughput downloads, Smart Import, Automation, Discover metadata integration, authoritative service-runtime handoff, BOM-safe providers, Session 0-safe SAB launch, smooth post-processing, durable Grab queueing, and resilient tray behavior.

Metadata Server compatibility remains **v0.3.3**.

## Upgrade notes

You may install v3.6.2 directly over an existing NewzDeck installation. Setup is specifically hardened to stop both the existing tray process and the background service before replacing their executables; manual process/service shutdown should not be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.2_SHA256.txt` if desired.
