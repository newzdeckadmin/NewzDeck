# NewzDeck v3.7.18 — Windows CI Path Identity Recovery

Repairs the Windows GitHub Actions release validation failure that prevented v3.7.17 from producing binaries. The v3.7.17 source and annotated tag were already pushed, but the CI pipeline stopped at the test-only `validate-v3717-loose-filenames.py` assertion.

## Fixed

- The loose-image finalization test now compares completed-history storage directories by **filesystem identity** (`Path.samefile`) instead of literal path text. On Windows, `%TEMP%` may be spelled with either a canonical long name (`runneradmin`) or an 8.3 short alias (`RUNNER~1`); they can identify the same directory.
- Retains all filename-restoration test cases, including staged files, direct-root completion, existing-name collisions, opaque names, unrelated staging tokens, and multi-file payloads.
- Keeps the prior **v3.7.17 original Image Set filename restoration** code intact, now included in the built v3.7.18 release.

## Preserved

No changes to actual SABnzbd download/rename behavior since the v3.7.17 source commit. v3.7.16 silent FFmpeg/FFprobe, v3.7.15 filtered Newsgroup views and bulk queue handling, v3.7.14 Completed history removal, v3.7.13 gallery preview safeguards, NNTP, SABnzbd 5.1.2, SABCTools 9.6.3, metadata server, diagnostic collector, Direct Unpack/PAR2, and managed installer lifecycle are retained.

**Release provenance:** v3.7.17's annotated tag must remain untouched. v3.7.18 has a new source commit and immutable annotated tag. The original v3.7.17 CI run failed before producing a Setup EXE or Portable ZIP. The official v3.7.18 Windows CI pipeline builds those deliverables only after all tests pass.

**Validation remaining:** Windows CI build, clean install/upgrade smoke, and live NNTP Image Set filename acceptance after publishing.
