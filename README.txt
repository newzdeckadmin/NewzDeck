NewzDeck v3.6.78 - Windows Defender LF Build Pipeline Hotfix

This release is a packaging/build-pipeline hotfix built on v3.6.77.

Highlights:
- The full v3.6.77 application, UX, browsing, download and Automation behavior is retained.
- NewzDeckYenc.exe is now built in a dedicated pinned Linux GitHub Actions job from the exact canonical LF Git source bytes.
- The release workflow requires the exact Defender-tested helper SHA-256 before Setup/Portable packaging can continue.
- NewzDeckYenc.go and the decoder protocol/behavior are unchanged.
- SABnzbd 5.1.2, Metadata Server v0.3.3, Smart Import, Automation, Settings and all frozen Newsgroup Browser performance behavior are unchanged.

See release/RELEASE_NOTES_v3.6.78.md for details.
