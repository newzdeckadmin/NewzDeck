# NewzDeck v3.6.81 — Automation Intelligence & Quality Profiles

v3.6.81 is a targeted Automation reliability and decision-model release built on the verified v3.6.80 production baseline. It does **not** reopen the accepted Newsgroup Browser performance architecture or the SABnzbd/download pipeline.

## Monitored metadata now stays current independently

Previously, scheduled metadata refreshes were launched from the Continuous Automation worker. A monitored TV library could therefore stop discovering newly announced/future episodes when automatic downloading was intentionally disabled.

v3.6.81 moves scheduled monitored-library metadata maintenance into the always-running service loop. Monitored shows can refresh episode/release metadata on the configured 1/3/6/12/24-hour schedule even when unattended grabbing is off. Existing monitoring choices, file state, TMDB identity, and metadata-service behavior are preserved.

## Correct WEB / WEB-DL upgrade behavior

Generic `2160p WEB` remains accepted for compatibility with ambiguous release naming, but it is no longer treated as indistinguishable from an explicit `2160p WEB-DL` when deciding whether an installed file can be upgraded. At the same profile tier, explicit WEB-DL is a real source-quality improvement over generic WEB.

## HDR and Dolby Vision are first-class upgrade traits

Release parsing now preserves independent dynamic-range flags instead of collapsing a title to one mutually exclusive label.

Within the same base quality/source tier, the upgrade progression is:

1. Dolby Vision + HDR/HDR10/HDR10+ fallback — preferred terminal state
2. Dolby Vision
3. HDR10+
4. HDR / HDR10
5. SDR / unknown dynamic range

A lower base quality tier cannot leapfrog a better one merely because it has HDR or Dolby Vision. For example, 1080p Dolby Vision does not replace an otherwise acceptable 2160p file in the 4K Preferred profile.

The same comparison model is now used by Interactive Search, Continuous Automation candidate filtering, release ordering, automatic-grab preflight, Smart Import no-downgrade checks, Wanted/cutoff decisions, and imported-file provenance.

## Structured Quality Profile Builder

The old new-profile dialog exposed a free-form quality list such as `2160p`, `1080p`, `720p`, `WEB`, even though the decision engine works with source-specific tiers such as `2160p WEB-DL` and `2160p BluRay`.

v3.6.81 replaces that editor with a structured builder:

- Start from **4K Preferred**, **1080p Balanced**, or a custom configuration.
- Add, remove, and reorder canonical source/resolution quality tiers.
- Choose the base upgrade cutoff from the actual quality ladder.
- Configure HDR/HDR10, HDR10+, Dolby Vision, and Dolby Vision + HDR fallback as Allow / Prefer / Require / Avoid.
- Configure HEVC/x265, AVC/x264, and AV1 policies.
- Configure Atmos, TrueHD, DTS-HD, DD+/E-AC-3, and AAC policies.
- Continue or stop dynamic-range upgrades after the base cutoff.
- Prefer PROPER/REPACK releases.
- Configure minimum/maximum release size, preferred groups, and hard-reject terms.
- Keep the existing advanced custom term/scoring system for power users.
- See a plain-English profile behavior summary before saving.

Existing persisted profiles remain readable. The two built-in profile IDs receive safe effective defaults for the new structured policy fields when older profile JSON does not yet contain them.

## Third-party notice correction

`THIRD_PARTY_NOTICES.md` now accurately documents the already-pinned **SABnzbd 5.1.2** runtime and current NewzDeck release wording. This is a documentation correction only; the SAB runtime remains unchanged.

## Explicitly unchanged / frozen

- Image thumbnail HTTP admission limit: **5**
- High-connection Video thumbnail ceiling: **6**
- Video thumbnail sample: **24 MB**
- Video segment cap: **12**
- First-paint headers: **800**
- OVER/XOVER chunk: **800**
- Large/progressive page threshold: **1000**
- Existing All Posts resolver timing
- Existing adaptive preview/download allocation and provider/NNTP allocation
- Thumbnail scheduling/scoring/cancellation and virtualization geometry
- SABnzbd **5.1.2** integration and throughput behavior
- Download queue, post-processing, Automation ownership, and Smart Import mechanics outside the reviewed quality comparison
- Metadata Server **v0.3.3**
- Diagnostic Collector **v1.0.31**
- Defender-accepted `NewzDeckYenc.exe` SHA-256 `4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad`
- Canonical LF/Linux yEnc source/build path and source SHA-256 `ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd`

## Release architecture

The canonical publisher must continue to create one production source commit, tag `v3.6.81` at that source commit, then create a separate `.release-trigger/3.6.81` trigger commit whose parent is the source commit. GitHub Actions builds the official Setup and Portable artifacts from that validated source. No force-push or tag movement is permitted.
