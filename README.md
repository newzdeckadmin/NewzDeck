# NewzDeck

<p align="center">
  <img src="assets/NewzDeck.png" alt="NewzDeck" width="128" />
</p>

<p align="center">
  <strong>A modern Usenet newsreader, downloader, and personal media automation app for Windows.</strong>
</p>

<p align="center">
  <a href="https://www.newzdeck.com/">Website</a> ·
  <a href="https://github.com/newzdeckadmin/NewzDeck/releases/latest">Download</a> ·
  <a href="https://github.com/newzdeckadmin/NewzDeck/issues">Report an issue</a>
</p>

## Download

The current stable release is **NewzDeck v3.6.2** for 64-bit Windows.

**Recommended:** download `NewzDeck_v3.6.2_Setup.exe` from the [latest release](https://github.com/newzdeckadmin/NewzDeck/releases/latest).

A Portable ZIP is also available if you prefer to run NewzDeck without a normal installation.

NewzDeck is free and open source. **Usenet access is not included** — you need your own Usenet provider account. Automation and interactive NZB search can also use your own Newznab-compatible indexer.

## What NewzDeck does

- **Browse newsgroups visually** with gallery and list views, image/video previews, grouping, tabs, bookmarks, filtering, and search.
- **Download at high speed** through the bundled private SABnzbd engine with queue controls, retries, provider-aware transfers, PAR2 verification/repair, unpacking, and post-processing.
- **See downloads live** with near-real-time transfer state, stable Active cards, and live Verify, Repair, Unpack, and Smart Import progress.
- **Discover movies and TV** with TMDB-powered posters, backdrops, metadata, cast/crew, trending titles, new releases, recommendations, filtering, and responsive title details.
- **Automate TV and movies** with monitored libraries, quality profiles, Wanted items, calendar, history, root folders, and Newznab-compatible indexers.
- **Organize completed media** with Smart Import, including identification, renaming, moving, duplicate/existing-media handling, and cleanup of completed download folders.
- **Grab and organize once** from Discover without having to add the Movie or safely identifiable TV release to Automation first.
- **Keep downloads running in the background** with the Windows background service and system tray companion.

## v3.6.2 highlights

v3.6.2 is an installed-upgrade reliability hotfix built on v3.6.1. It preserves the accepted v3.6.0 UI/UX Overhaul and v3.6.1 background-service shutdown fix.

- **Tray process shutdown is now authoritative:** Setup captures the real `NewzDeckTray.exe` process before asking its hidden window to close and waits for the process itself to exit, rather than assuming a vanished window means the executable is already unlocked.
- **Bounded hung-tray recovery:** if the tray does not exit after a generous graceful wait, Setup terminates only the process owning the NewzDeck tray window and waits again before file overlay.
- **Fail-safe tray upgrade gate:** if the tray process still cannot be confirmed stopped, Setup aborts before replacing files instead of reaching `DeleteFile failed; code 5`.
- **Delayed-exit tray regression coverage:** the Windows upgrade smoke helper now deliberately keeps `NewzDeckTray.exe` alive for six seconds after its hidden window disappears, reproducing the race that escaped v3.6.1.
- **v3.6.1 service fix preserved:** Setup still uses the installed service helper and waits for a confirmed `STOPPED` state before replacing `NewzDeckService.exe`.
- **v3.6.0 UI preserved:** navigation, readability, Newsgroups tabs, Discover details, Automation alignment, and the application-wide visual overhaul remain unchanged.

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

Only download NewzDeck from this repository or the official website. The release includes `NewzDeck_v3.6.2_SHA256.txt` so you can verify the installer and Portable ZIP before running them.

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
