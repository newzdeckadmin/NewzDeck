NewzDeck v3.6.7
Browsing Pipeline & Long-Scroll Performance
Getting Started

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application. v3.6.7 builds on v3.6.6 with
lower-latency paging, stale-preview cancellation, predictive prefetch, and
long-scroll responsiveness improvements.

WHAT'S NEW IN v3.6.7

- Obsolete thumbnail/preview BODY work cancels quickly when the browsing context changes.
- Up to two short-lived warm NNTP header sessions reduce repeat paging setup latency.
- Continuous browsing prefetches the next older header page before the bottom.
- Thumbnail demand follows scroll direction and velocity while retaining v3.6.6 adaptive scaling.
- Large All Posts package pages can finish deep reconstruction progressively in the background.
- Far-offscreen decoded thumbnails are released in bounded batches during very long sessions.
- v3.6.6 adaptive preview scaling, v3.6.5 taskbar identity, and v3.6.4 package browsing remain preserved.
WHAT YOU NEED

- Windows 10 or Windows 11, 64-bit
- Your own Usenet provider account and NNTP server credentials
- Internet access
- Optional: a Newznab-compatible indexer for Automation and interactive search

INSTALLING NEWZDECK

For most users, download and run:
  NewzDeck_v3.6.4_Setup.exe

You may install v3.6.4 directly over an existing installation. The v3.6.1 and
v3.6.2 upgrade protections remain in place, so manual service or tray shutdown
should not normally be required.

A Portable ZIP is also available. Portable users should close NewzDeck before
replacing application files. Persistent user state remains under:
  %LOCALAPPDATA%\NewzDeck

NewzDeck is currently unsigned. Windows may show an Unknown Publisher or
Microsoft Defender SmartScreen warning. Download NewzDeck only from the
official GitHub repository or https://www.newzdeck.com/. Verify downloads with
NewzDeck_v3.6.4_SHA256.txt if desired.

FIRST START

1. Open Settings.
2. Add your Usenet provider server, port, username, password, and connection settings.
3. Save the provider and confirm it connects.
4. Browse newsgroups, search, preview, reconstruct packages, and download.

DOWNLOADS AND POST-PROCESSING

NewzDeck uses its bundled private SABnzbd engine for high-throughput downloads.
The Downloads page shows near-real-time transfer state and live Verify, Repair,
Unpack, Direct Unpack, and Smart Import progress. Complete binary sets queued
from All Posts are represented as one package while their component files remain
individually tracked for integrity and recovery.

TV AND MOVIE AUTOMATION

Automation is optional. Configure media root folders and a compatible Newznab
indexer to monitor TV shows and movies, manage Wanted items and Calendar, and
import completed media. Discover remains powered by the NewzDeck Metadata Server.

BACKGROUND DOWNLOADS

NewzDeck can use its Windows background service and system tray companion so
downloads and Automation continue after the main window closes.

UPDATES AND DATA

Normal updates preserve your NewzDeck data under:
  %LOCALAPPDATA%\NewzDeck

Do not run two different NewzDeck versions against the same per-user data
directory at the same time.

HELP

Issues:
  https://github.com/newzdeckadmin/NewzDeck/issues

Website:
  https://www.newzdeck.com/

Do not post provider passwords, API keys, tokens, or other private credentials
when asking for help.

LICENSE

NewzDeck-owned source is licensed under GNU GPL v3.0 only. Third-party
components retain their own licenses. See LICENSE.txt and THIRD_PARTY_NOTICES.txt.
