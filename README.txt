NewzDeck v3.6.4
Newsgroup Package Browser & Binary Reconstruction
Getting Started

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application. v3.6.4 builds on the accepted
v3.6.3 baseline with a major Newsgroup browsing overhaul focused on useful
package-level browsing, multipart reconstruction, obfuscation recovery,
downloadability, filtering, and layout reliability.

WHAT'S NEW IN v3.6.4

- All Posts is now a wide, metadata-first Package browser. Images and Video keep
  their Gallery/List thumbnail experience and media Preview pane.
- Packages / Raw posts lets advanced users switch between reconstructed releases
  and the underlying Usenet article/file rows.
- Multipart RAR, legacy RAR, split ZIP/7-Zip/numeric files, PAR2 sets, and matching
  sidecars can collapse into one package with expandable original filenames and
  subjects.
- Complete non-image/video binaries are first-class selectable/queueable downloads.
  Healthy grouped sets enter Downloads under one collection identity.
- Package health distinguishes likely-complete sets from incomplete articles,
  missing archive volumes, and sets with PAR2 recovery data. Incomplete fragments
  are hidden from Downloadable view but remain available in troubleshooting views.
- Sorting includes Newest, Oldest, Largest, Smallest, Name A-Z, Most files, and
  Best health.
- A persistent Min size filter is always visible in All Posts > Packages. It accepts
  MB/GB values including decimals; 0 disables it. The cutoff uses reconstructed
  binary/package size rather than individual yEnc segment size.
- Obfuscated yEnc streams are reconstructed from part/total structure before they
  reach the browser, including conservative anonymous reconstruction when both the
  visible subject and From identity are randomized.
- Bounded header-only XOVER expansion can scan enough surrounding headers to finish
  very large multipart binaries without downloading BODY payloads merely to browse.
- Low-bandwidth name resolution can recover filenames from yEnc control headers,
  PAR2/SFV metadata, and bounded RAR4/RAR5/ZIP/best-effort 7-Zip header inspection.
- Structural package reconstruction can connect randomized binaries using recovered
  title hints, counters, posting sequence/proximity, and conservative size patterns.
- Opening or reopening a newsgroup now starts from a fresh page 1 load rather than
  restoring a stale page/session position; useful display preferences remain saved.
- Newsgroup toolbar wrapping/alignment and UNSEEN/NEW badge containment are corrected.
- Newsgroup deobfuscation remains provider-agnostic: there is no Easynews web
  scraping/integration and no Newznab/indexer reconciliation traffic while browsing.

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
