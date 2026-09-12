NewzDeck v3.6.75 - Windows Defender Compatibility

This release is a narrow Windows build/distribution compatibility update built on v3.6.74.

- NewzDeckYenc.go decoder source and behavior are unchanged.
- NewzDeckYenc.exe now retains the normal Go build ID and symbol/debug metadata instead of using the stripped -s/-w/empty-buildid profile.
- Only the yEnc helper uses this compatibility build override; all other native helpers keep their established build profile.
- The isolated helper, a full Portable acceptance package, and a final exact-production-source helper build all passed Windows Defender testing before this release was authorized.
- Browsing schema 11, thumbnail scheduling/concurrency, provider allocation, SABnzbd 5.1.2, Settings reliability, Automation, Smart Import, Discover and Metadata Server behavior are unchanged.

See release/RELEASE_NOTES_v3.6.75.md for details.
