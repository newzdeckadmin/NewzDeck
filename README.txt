NewzDeck v3.6.82 - Automation Intelligence & Quality Profiles

This release is a targeted Automation decision-model update built on the verified v3.6.80 production baseline.

Highlights:
- Monitored TV metadata refresh is independent of automatic downloading, so future/new episodes can be discovered even when Continuous Automation is off.
- Explicit WEB-DL is now treated as better than ambiguous WEB at the same resolution.
- HDR/Dolby Vision are real upgrade dimensions: HDR upgrades SDR, Dolby Vision upgrades HDR, and Dolby Vision + HDR/HDR10/HDR10+ fallback is the preferred terminal dynamic-range state.
- Interactive Search, automatic selection, Smart Import and automatic-grab preflight now use the same upgrade model.
- New Quality Profiles use a structured builder with templates, an ordered quality ladder, cutoff, dynamic-range, codec, audio, PROPER/REPACK, size, release-group, reject-term and advanced custom-score controls.
- Third-party notices now correctly identify SABnzbd 5.1.2.
- The accepted Newsgroup Browser performance architecture, SABnzbd 5.1.2 runtime, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and Defender-clean yEnc pipeline remain unchanged.

See release/RELEASE_NOTES_v3.6.82.md for details.

Release engineering note:
- v3.6.82 supersedes the unpublished v3.6.81 binary release after the v3.6.81 source/tag were accepted but its malformed release-trigger metadata prevented GitHub Actions from publishing assets.
- Runtime behavior is unchanged from the reviewed v3.6.81 source.
