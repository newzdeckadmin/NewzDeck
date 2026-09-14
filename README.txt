NewzDeck v3.7.2 - Runtime Identity & Release Metadata Hotfix

NewzDeck is a free and open-source Windows Usenet newsreader, downloader, and personal media automation application.

v3.7.2 corrects the v3.7.1 runtime-version mismatch that could report a v3.7.0 download-engine adapter while the UI/runtime were v3.7.1. All shipped runtime identities now agree on v3.7.2.

The v3.7.1 in-process SABCTools 9.6.3 decoder architecture is preserved. NewzDeckYenc.exe remains retired from new payloads, the private SABnzbd 5.1.2 engine and Direct Unpack/post-processing behavior are unchanged, and the Python yEnc fallback remains available for compatibility.

The GitHub README, website fallback release labels, build/source documentation, and bundled SABCTools third-party notices are updated with this hotfix.

License: GNU GPLv3. Bundled SABCTools retains its GPL-2.0-or-later license; see THIRD_PARTY_NOTICES.txt and licenses/SABCTOOLS-LICENSE.md.
