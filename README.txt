NewzDeck v3.6.47
PAR2 Repair Visibility, SAB 5.1.2 & Selected Episode Monitoring

New in v3.6.47:
- Adds Selected Episodes monitoring for TV shows: choose whole seasons or individual episodes, including old aired episodes, without monitoring other seasons. Explicit selections bypass the global old-backlog gate and partial selections cannot trigger whole-season packs.
- Completed and Failed downloads retain SAB's observed Verify/PAR2/Repair outcome instead of reducing every terminal job to a generic status.
- Download details distinguish unrecoverable article/recovery data from unpack, password, filesystem, post-processing-aborted, and other terminal failures when SAB reports that evidence.
- PAR2 outcome, repair attempt, extra PAR2 fetch observation, post-processing time, and bounded SAB repair-history messages are visible and included in copied diagnostics.
- Exact recovery-block counts are shown as Not reported by SAB when SAB History does not expose them; NewzDeck no longer implies a real zero.
- The private embedded SABnzbd runtime is upgraded from 5.1.1 to pinned 5.1.2 with official SHA-256 validation and a graceful queue-preserving startup handoff.
- v3.6.46 quality-aware release selection, v3.6.45 library-scan progress, Library Integrity, strict TV identity, and Downloads continuity are preserved.
