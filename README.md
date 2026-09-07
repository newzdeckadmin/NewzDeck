# NewzDeck

<p align="center">
  <img src="assets/NewzDeck.png" alt="NewzDeck" width="128" />
</p>

<p align="center">
  <strong>A modern Usenet newsreader, downloader, and personal media automation app for Windows.</strong>
</p>

<p align="center">
  <a href="https://www.newzdeck.com/">Website</a> Ã‚Â·
  <a href="https://github.com/newzdeckadmin/NewzDeck/releases/latest">Download</a> Ã‚Â·
  <a href="https://github.com/newzdeckadmin/NewzDeck/issues">Report an issue</a>
</p>

## Download

The current stable release is **NewzDeck v3.6.42** for 64-bit Windows.

**Recommended:** download `NewzDeck_v3.6.42_Setup.exe` from the [latest release](https://github.com/newzdeckadmin/NewzDeck/releases/latest).

A Portable ZIP is also available if you prefer to run NewzDeck without a normal installation.

NewzDeck is free and open source. **Usenet access is not included** Ã¢â‚¬â€ you need your own Usenet provider account. Automation and interactive NZB search can also use your own Newznab-compatible indexer.

## What NewzDeck does

- **Browse newsgroups visually** with gallery and list views, image/video previews, grouping, tabs, bookmarks, filtering, and search.
- **Download at high speed** through the bundled private SABnzbd engine with queue controls, retries, provider-aware transfers, PAR2 verification/repair, unpacking, and post-processing.
- **See downloads live** with near-real-time transfer state, stable Active cards, and live Verify, Repair, Unpack, and Smart Import progress.
- **Discover movies and TV** with TMDB-powered posters, backdrops, metadata, cast/crew, trending titles, new releases, recommendations, filtering, and responsive title details.
- **Automate TV and movies** with monitored libraries, quality profiles, Wanted items, calendar, history, root folders, and Newznab-compatible indexers.
- **Organize media** with Smart Import, including completed downloads and explicit external TV season/episode imports, canonical renaming/moving, duplicate/existing-media handling, and safe quality upgrades.
- **Keep downloads running in the background** with the Windows background service and system tray companion.

## v3.6.42 highlights

v3.6.42 hardens TV release identity and long-running Automation reliability based on a completed v3.6.41 diagnostic review.

- **Strict TV series prefix identity:** unrelated shows and episode-title text can no longer satisfy another show's Automation target.
- **Library reconciliation safety:** TV scans prefer a proven series folder and reject stale cross-title folder ownership.
- **Needs Review audit:** existing suspicious cross-title/edition/identity records are reported read-only; media is never automatically deleted or rewritten.
- **Reservation hygiene:** only expired Automation Grab reservations are pruned, preserving active duplicate-Grab protection.
- **Drive reserve protection:** Automation can preserve a configurable percentage of every media/staging drive in addition to the GB minimum.
- **Cleaner diagnostics:** Win64 memory telemetry is fixed and generic SAB warnings no longer masquerade as provider failures.
- **Permanent release guards:** launcher log identity is dynamic and production CI runs the strict TV identity regression suite.

See [the full v3.6.42 release notes](release/RELEASE_NOTES_v3.6.42.md).
## Requirements

- Windows 10 or Windows 11, 64-bit
- A Usenet provider account with NNTP server credentials
- Internet access for provider connections and online metadata
- Optional: a Newznab-compatible indexer for Automation and interactive NZB search

## Getting started

1. Download and run the latest **Setup.exe**.
2. Start NewzDeck.
3. Open **Settings** and add your Usenet provider details.
4. Browse or search newsgroups and start downloading.
5. If you want TV/movie automation, add your media root folders and configure a compatible indexer.

Your NewzDeck settings, history, queue state, provider configuration, and other persistent data are stored separately from the program files under `%LOCALAPPDATA%\NewzDeck`, so normal application updates preserve your data.

## Windows SmartScreen

NewzDeck is currently distributed **unsigned**, so Windows may show an **Unknown Publisher** or Microsoft Defender SmartScreen warning.

Only download NewzDeck from this repository or the official website. The release includes `NewzDeck_v3.6.42_SHA256.txt` so you can verify the installer and Portable ZIP before running them.

## Updating

Installed users should normally install the newest Setup.exe over their existing installation or use NewzDeck's verified update flow when offered.

Portable users should close NewzDeck before replacing the application files. See [UPDATING.txt](UPDATING.txt) for the short update guide.

## Troubleshooting and support

If something is not working, check NewzDeck's in-app status and diagnostic information first. When reporting a problem, include the NewzDeck version, what you were doing, what you expected to happen, and any relevant error message or screenshot.

[Open a GitHub issue](https://github.com/newzdeckadmin/NewzDeck/issues)

Please do **not** post Usenet passwords, API keys, tokens, or other private credentials in an issue.

## Open source

NewzDeck-owned source code in this repository is licensed under the **GNU General Public License v3.0 only (GPL-3.0-only)** unless a file or third-party notice says otherwise. See [LICENSE](LICENSE).

Third-party software, services, data, logos, and other assets retain their own licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

For source-publication history and release provenance, see [docs/SOURCE_RELEASES.md](docs/SOURCE_RELEASES.md).

## Building from source

Most people do not need to build NewzDeck themselves. The official Windows binaries are built from the public source in this repository. Contributor build notes are available under [`release/windows/`](release/windows/README.md).
