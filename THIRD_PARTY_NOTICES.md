# Third-Party Notices

This file records third-party software, build tooling, services, data sources, and trademark assets used by or interoperated with by NewzDeck. **Nothing in the NewzDeck GPL license changes the license of these third-party works.**

## Go runtime and standard library

NewzDeck v3.5.32 ships Windows executables built with **Go 1.23.2**. Portions of the Go runtime and standard library are statically incorporated into those executables.

- Project: The Go Programming Language
- License: BSD-style / BSD-3-Clause
- Source: https://github.com/golang/go
- License text preserved at: `licenses/GO-BSD-3-CLAUSE.txt`

The Go license requires binary redistributions to reproduce its copyright notice, conditions, and disclaimer in documentation and/or other materials provided with the distribution. Future NewzDeck binary packages should therefore include this notice/license text.

## CPython 3.12.10

NewzDeck can download the official **CPython 3.12.10 Windows embeddable x64** package directly from python.org on first launch and verifies the pinned archive before extraction into NewzDeck's private runtime folder.

- Project: CPython / Python
- License: Python Software Foundation License Version 2, with additional incorporated-software notices
- Source/license: https://docs.python.org/3.12/license.html
- Runtime download origin: python.org

CPython is not embedded in the NewzDeck v3.5.32 Portable ZIP or Setup payload; it is obtained separately from the upstream publisher on the user's machine.

## SABnzbd 5.1.1

NewzDeck Download Engine v2 can provision the official **SABnzbd 5.1.1 Windows x64 portable** release and run it locally as a separate backend process behind NewzDeck's UI/API.

- Project: SABnzbd
- Copyright: The SABnzbd-Team and contributors
- License: GNU General Public License v2.0 or later (GPL-2.0-or-later)
- Homepage: https://sabnzbd.org/
- Source: https://github.com/sabnzbd/sabnzbd
- Upstream license notice preserved at: `licenses/SABNZBD-LICENSE.txt`

NewzDeck v3.5.32 does not embed the SABnzbd portable archive in its GitHub release; it is obtained separately from upstream on the user's machine. SABnzbd is an independent project and is not affiliated with NewzDeck.

## RARLAB UnRAR 7.23

For RAR extraction/Direct Unpack, NewzDeck can download the official RARLAB UnRAR 7.23 x64 command-line package on the user's machine.

- Publisher: win.rar GmbH / RARLAB
- License: RAR/WinRAR/UnRAR license terms; **not an open-source license**
- License: https://www.rarlab.com/license.htm
- Downloads: https://www.rarlab.com/download.htm

NewzDeck does not relicense UnRAR under GPL. The upstream terms apply independently. NewzDeck v3.5.32 does not embed UnRAR in the GitHub release payload.

## par2cmdline-turbo 1.5.0

For PAR2 verification and repair, NewzDeck can download the official par2cmdline-turbo v1.5.0 Windows x64 release on the user's machine.

- Project: par2cmdline-turbo
- License: GNU General Public License v2.0 (upstream repository identifies GPL-2.0)
- Source: https://github.com/animetosho/par2cmdline-turbo
- Releases: https://github.com/animetosho/par2cmdline-turbo/releases/tag/v1.5.0

NewzDeck v3.5.32 does not embed this executable in its GitHub release payload.

## 7-Zip (optional user-supplied tool)

NewzDeck can use a separately installed or user-supplied `7z.exe`, `7zz.exe`, or `7za.exe` for `.7z` archives. NewzDeck v3.5.32 does not bundle 7-Zip.

- Project: 7-Zip
- License information: https://www.7-zip.org/license.txt

## Inno Setup 7.1.0

The Windows `Setup.exe` is built by GitHub Actions using official **Inno Setup 7.1.0 x64**. Inno Setup is build/distribution tooling and its setup engine is incorporated into the generated installer.

- Project: Inno Setup
- Copyright: Jordan Russell; portions Martijn Laan
- License: Inno Setup License
- Homepage: https://jrsoftware.org/isinfo.php
- License text preserved at: `licenses/INNO-SETUP-LICENSE.txt`

NewzDeck does not claim authorship of Inno Setup.

## TVmaze

NewzDeck can use the TVmaze public API for TV-series and episode metadata.

- API data license: CC BY-SA
- API/licensing information: https://www.tvmaze.com/api

NewzDeck credits TVmaze in the application where its data is used.

## Wikidata / Wikimedia Commons / Wikipedia

- Wikidata structured data: CC0 1.0 — https://www.wikidata.org/wiki/Wikidata:Licensing
- Wikimedia Commons media: per-file licenses; NewzDeck only uses media when its per-file licensing/attribution path allows it — https://commons.wikimedia.org/
- Wikipedia text: applicable Wikimedia/Wikipedia licensing and attribution terms — https://www.wikipedia.org/

## The Movie Database (TMDB)

NewzDeck can use TMDB metadata and artwork through the NewzDeck Metadata Service.

Required attribution statement used by NewzDeck:

> This product uses the TMDB API but is not endorsed or certified by TMDB.

- TMDB: https://www.themoviedb.org/
- Logo/attribution guidance: https://www.themoviedb.org/about/logos-attribution

The TMDB name/logo and supplied metadata/artwork are third-party materials and are not relicensed under NewzDeck's GPL license.

## Windows and Microsoft components

NewzDeck uses Windows APIs and may launch the Chromium-based browser/application mode available on the user's Windows installation. Microsoft/Windows/browser components are operating-system components or separately installed software and are not distributed as NewzDeck source.
