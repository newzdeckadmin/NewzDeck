# NewzDeck v3.6.82 - Release Pipeline Recovery Hotfix

v3.6.82 carries the complete reviewed v3.6.81 **Automation Intelligence & Quality Profiles** application behavior forward unchanged and repairs only the production release-publication path.

## Why v3.6.82 exists

The v3.6.81 production source commit and immutable `v3.6.81` tag were created successfully, and the Defender-accepted yEnc helper job passed. The canonical Windows release job then stopped before building assets because the guarded publisher wrote the trigger metadata as `source_commit=<sha>` while the canonical workflow intentionally accepts only `Source commit: <sha>`.

Because NewzDeck release policy forbids force-pushing `main` or moving an existing version tag, v3.6.82 is the clean recovery release rather than rewriting v3.6.81 history.

## Application behavior

There are **no functional application changes beyond v3.6.81**. v3.6.82 includes the full v3.6.81 feature set:

- monitored TV metadata refresh is independent of automatic downloading;
- explicit WEB-DL is ranked above ambiguous WEB at equal resolution;
- HDR upgrades SDR, Dolby Vision upgrades HDR, and Dolby Vision with HDR/HDR10/HDR10+ fallback is the preferred terminal dynamic-range state;
- Interactive Search, automatic selection, automatic-grab preflight, cutoff/Wanted decisions and Smart Import use the same source/dynamic-range upgrade model;
- the structured Quality Profile Builder supports templates, ordered quality tiers, cutoff, HDR/Dolby Vision, codecs, audio, PROPER/REPACK, release sizes, preferred groups, reject terms and advanced custom scoring.

## Release-engineering correction

- The guarded publisher now writes the exact canonical trigger line `Source commit: <40-hex-source-sha>`.
- The publisher validates the written trigger syntax before creating the trigger commit.
- The source commit, immutable `v3.6.82` tag and trigger commit remain separate and are verified before waiting for GitHub Actions.
- The canonical workflow remains fail-closed and still requires the trigger commit to change only `.release-trigger/3.6.82` and to have the production source commit as its parent.

## Deliberately unchanged

- Newsgroup Browser performance architecture and tuning
- SABnzbd 5.1.2 integration and download/post-processing behavior
- Smart Import behavior beyond the accepted v3.6.81 quality comparison model
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Windows launcher/service/tray/picker behavior
- Defender-clean LF/Linux yEnc source, build flags and accepted helper hash

## Provenance

The prior `v3.6.81` source tag remains immutable as a historical source-only tag. v3.6.82 supersedes it as the public binary release without rewriting that history.
