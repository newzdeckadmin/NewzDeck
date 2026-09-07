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

The current stable release is **NewzDeck v3.6.48** for 64-bit Windows.

**Recommended:** download `NewzDeck_v3.6.48_Setup.exe` from the [latest release](https://github.com/newzdeckadmin/NewzDeck/releases/latest).

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

## v3.6.48 highlights

v3.6.48 hardens Library Integrity and the Downloads control plane using evidence from real v3.6.47 diagnostics, without changing SABnzbd's authoritative transfer or repair behavior.

- **Same-title duplicate review:** identical fingerprints across different physical episode files of the same series now require review, while one shared multi-episode file remains informational.
- **Production regression evidence:** 29 exact historical false-positive TV release identities from real diagnostics are now release blockers, including Love Island companion/related-show collisions and the Dark Matter title collision.
- **Less control-plane pressure:** visible Downloads polling backs off to 2 Hz during active work and 0.8 Hz while idle, with a slower hidden-page cadence; the coherent presentation snapshot cache increases from 0.22s to 0.40s.
- **Actionable snapshot telemetry:** SAB reconciliation, provider-health, and remaining snapshot time are measured separately so slow builds can be traced instead of appearing as one opaque duration.
- **Recovered busy state:** a transient SAB Queue/History reader-busy condition is cleared from active last-error state after a later fresh Queue+History pair succeeds.
- **Existing behavior preserved:** v3.6.47 Selected Episodes, persistent PAR2/repair visibility, private SABnzbd 5.1.2, quality-aware selection, scan progress, Smart Import, strict TV identity, and installer/runtime handoff remain intact.

See [the full v3.6.48 release notes](release/RELEASE_NOTES_v3.6.48.md).
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

Only download NewzDeck from this repository or the official website. The release includes `NewzDeck_v3.6.48_SHA256.txt` so you can verify the installer and Portable ZIP before running them.

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
