# Release Compliance Checklist

Use this checklist for each production NewzDeck release after the v3.5.32 licensing transition.

## Source

- [ ] Version/tag exists in the public repository.
- [ ] Python/JavaScript source matches the release.
- [ ] Every NewzDeck-owned Windows executable has corresponding public source.
- [ ] Every helper is rebuilt from the tagged source; no opaque previous-release NewzDeck binary is copied forward as the only build input.
- [ ] Build commands/toolchain versions are documented.
- [ ] Secret/credential scan passes.

## Licensing

- [ ] Root source tree contains `LICENSE` (GPL-3.0-only).
- [ ] Binary package contains a copy of the NewzDeck GPLv3 license (for example `LICENSE.txt`).
- [ ] Binary package contains current `THIRD_PARTY_NOTICES`.
- [ ] Go BSD license is included with Go-built binaries.
- [ ] Inno Setup notice/license is preserved for the installer distribution documentation.
- [ ] Third-party downloaded tools are identified by project, version, license, and upstream source/license URL.
- [ ] Third-party trademarks/API data are not described as GPL-covered NewzDeck content.

## Distribution

- [ ] Portable ZIP SHA-256 verified.
- [ ] GitHub Actions builds Setup from the exact tested Portable ZIP.
- [ ] Setup and checksum outputs verify successfully.
- [ ] Source archive/tag is public at the same time as the binary release.
- [ ] Release notes identify the license and link to source.
- [ ] Windows upgrade/install test passes on a real machine.

## v3.5.32

v3.5.32 predates this complete-source gate and is explicitly documented as the transition release. Do not rewrite history by claiming its source map is complete when the legacy helper source is not currently present.
