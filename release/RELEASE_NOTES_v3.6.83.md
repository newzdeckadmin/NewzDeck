# NewzDeck v3.6.83 - Quality Profile UI & Update Version Coherency

v3.6.83 is a focused correctness and presentation release built on the published v3.6.82 baseline. It fixes the two issues observed after the v3.6.82 rollout without retuning Newsgroup Browser performance, downloads, SABnzbd, Smart Import, or the accepted Automation quality model.

## Quality Profile editor layout

The structured Quality Profile Builder introduced in v3.6.81 keeps the same fields and behavior, but its dialog now has a dedicated layout instead of inheriting general Automation modal spacing.

- Fixed dialog header and action footer with a separately scrollable body.
- Consistent 22-24 px desktop gutters and responsive mobile/tablet insets.
- Aligned Profile name / template fields.
- Uniform input/select heights and label/helper spacing.
- Cleaner Quality Ladder alignment and Add control geometry.
- More even Dynamic Range, Video Codec and Audio policy grids.
- Better spacing for release-size, preferred-group, reject-term and advanced custom-score controls.
- Stable Save/Delete action placement while scrolling long profiles.

No Quality Profile schema, scoring semantics, cutoff behavior, upgrade logic, or saved-profile compatibility changes are made by this UI pass.

## About & Updates version correctness

The About dialog still contained a historical hard-coded `NewzDeck v3.6.62` string even though the application was running v3.6.82. v3.6.83 removes that static identity and reports the installed version dynamically.

The update center now treats three version identities separately:

- **Installed version** - read from the current `version.txt` on disk.
- **Runtime version** - the backend process's in-memory `APP_VERSION`.
- **UI version** - the currently served `app.js` identity.

If those identities disagree, NewzDeck reports a runtime version mismatch rather than claiming that the already-installed release is an available upgrade.

## Same-version update protection

The backend now compares GitHub's latest release against the installed `version.txt` value instead of relying only on the process-start version constant. Update-feed cache entries are accepted only when they were created for the same installed version.

The browser UI also independently compares the latest release against the newer of the installed/UI versions. This provides a second safety boundary: even if an older backend process or stale feed result claims the current release is newer, the currently installed/UI release cannot be offered as an upgrade.

If a release-feed refresh fails, cached release metadata is only reused when it belongs to the current installed version, and `update_available` is recalculated against that installed version before the result is returned.

## Preserved behavior

- v3.6.81 monitored metadata refresh independence from automatic grabbing
- WEB-DL > generic WEB at equal resolution
- SDR -> HDR -> Dolby Vision -> Dolby Vision + HDR fallback upgrade progression
- Smart Import / automatic-grab / Interactive Search upgrade-model alignment
- Structured Quality Profile schema and saved profile compatibility
- Newsgroup Browser performance architecture and accepted tuning constants
- SABnzbd 5.1.2 integration and download/post-processing behavior
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Defender-clean LF/Linux yEnc source/build/hash identity
- v3.6.82 canonical source -> immutable tag -> trigger release topology
