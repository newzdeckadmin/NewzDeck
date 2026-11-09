# NewzDeck v3.7.30 — SABnzbd 5.1.3 Security & Download Engine Update

## Changes
- Update the official Windows x64 SABnzbd backend pin from **5.1.2** to **5.1.3**; published upstream SHA-256 for `SABnzbd-5.1.3-win64-bin.zip` is `62733e427534a1afec6a64b89dd06253f1a3cf51cb189d980f4e759c04f8d7eb`.
- Retain NewzDeck Download Engine v2's managed upgrade process: verify/download the new engine into its version-specific directory **before** requesting graceful shutdown of the credential-verified, localhost-only older SAB process; defer instead of force-killing or replacing a non-released listener.
- Continue to use version-independent SAB administration and incomplete-download directories, NewzDeck's job ledger, provider configuration and history. No queue migration, clearing, or loss of existing library data is intended.
- The SABnzbd release is obtained from its upstream publisher on the user's machine at provisioning time, not embedded in the NewzDeck installer or Portable ZIP. Requires internet connectivity for the initial 5.1.3 engine provisioning.

## Why update
SABnzbd's 5.1.3 release includes fixes for unauthenticated API access and symlink-related post-processing path traversal. See https://sabnzbd.org/auth-bypass and https://github.com/sabnzbd/sabnzbd/releases/tag/5.1.3 . This is an upstream engine update; no claims are made that these vulnerabilities were independently reproduced in NewzDeck's localhost-only integration.

## Preserved
- SABCTools **9.6.3** (pinned source commit `54d7663b9e8f527b5ab196d43f0d5c561a87c1ac`), NNTP data flow, PAR2, unpacking and Smart Import.
- v3.7.29's full monitored-library refresh, per-title retries, metadata validity and Wanted scheduling safeguards.
- Live Downloads pulse, provider settings, browser image sets, obfuscated binaries, original filenames and high-speed live group search.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31: **unchanged**.

## Operational notes
- During the controlled engine handoff, active transfers may pause briefly; persisted queue and incomplete files remain in place. If upstream download, SHA-256 check, identity authentication or graceful shutdown fails, NewzDeck defers the upgrade and should preserve the old engine rather than forcibly discarding jobs.
- After installation, verify Diagnostics reports **SABnzbd 5.1.3** as the running version (not just target), no pending upgrade and healthy queue/post-processing. A real Windows install and live Usenet transfer remain release acceptance gates.
- This source/publish package alone is not a published or Windows-verified release. The canonical guarded GitHub Actions workflow must successfully build the Setup EXE and Portable ZIP after separate authorization to publish.
