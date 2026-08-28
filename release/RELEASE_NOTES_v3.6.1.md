# NewzDeck v3.6.1 — Installer Upgrade Reliability

NewzDeck v3.6.1 is a focused hotfix for installed upgrades from v3.5.x/v3.6.0. It preserves the accepted v3.6.0 UI/UX Overhaul and all established download, Automation, Smart Import, Discover, provider, service-runtime, and tray behavior.

## Fixed

- **Background-service file lock during Setup** — v3.6.0 could show `DeleteFile failed; code 5` / `Access is denied` while replacing `NewzDeckService.exe`.
- **Unsafe fixed service-stop delay removed** — Setup no longer assumes the service will exit within 1.2 seconds after `sc stop`.
- **Confirmed service shutdown before overlay** — when upgrading an installation with the background service, Setup now runs the installed `NewzDeckService.exe stop` helper with elevation and waits for its bounded service-state check to confirm `STOPPED` before copying application files.
- **Fail-safe upgrade gate** — if the service helper is missing, elevation is denied, or the service cannot stop, Setup stops before overlaying application files and provides a clear error instead of entering a partial upgrade.
- **Locked-service regression test** — GitHub Actions now runs a deliberately slow-stopping `NewzDeckService.exe` that stays active beyond the old 1.2-second timing window, then verifies the installer successfully replaces the locked executable with the release build. Existing tray-lock upgrade coverage remains in place.

## Preserved

The full v3.6.0 UI/UX Overhaul is unchanged, including the reorganized navigation, readability/contrast system, Newsgroups tab layout, Discover detail treatment, Automation alignment, utility controls, and responsive component styling.

The accepted v3.5.x reliability architecture is also preserved: private SAB high-throughput downloads, Smart Import, Automation, Discover metadata integration, authoritative service-runtime handoff, BOM-safe providers, Session 0-safe SAB launch, smooth post-processing, durable Grab queueing, and resilient tray behavior.

Metadata Server compatibility remains **v0.3.3**.

## Upgrade notes

You may install v3.6.1 directly over an existing NewzDeck installation. Setup is specifically hardened to stop and wait for the existing background service automatically; manual service shutdown should not be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.1_SHA256.txt` if desired.
