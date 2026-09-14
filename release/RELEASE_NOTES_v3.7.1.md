# NewzDeck v3.7.1 — Native Decoder Integration & Defender Compatibility

NewzDeck v3.7.1 replaces the standalone `NewzDeckYenc.exe` subprocess used by queued Usenet downloads with an in-process SABCTools decoder while preserving the proven v3.7.0 network, queue, cache, disk, SABnzbd, Direct Unpack, Automation, Backup & Restore, and UI architecture.

## Highlights

- **No shipped `NewzDeckYenc.exe`:** the Defender-sensitive standalone Go yEnc helper is no longer built into the Portable ZIP or Setup payload.
- **In-process SABCTools 9.6.3:** the production workflow builds the exact upstream SABCTools 9.6.3 source at commit `54d7663b9e8f527b5ab196d43f0d5c561a87c1ac` for NewzDeck's pinned CPython 3.12.10 runtime and vendors that native package directly with NewzDeck.
- **Preserved high-speed split pipeline:** NNTP socket reads remain separate from decode work, so provider connections can refill while native yEnc decoding occurs on the existing decode executor.
- **Emergency compatibility fallback:** if the vendored native decoder cannot load or rejects an article, NewzDeck falls back to the existing bulk-Python yEnc implementation instead of failing the download outright.
- **Upgrade cleanup:** Setup still terminates a legacy `NewzDeckYenc.exe` process if an older install left one running, then explicitly deletes the retired binary before overlaying v3.7.1.

## Validation

The release workflow refuses publication unless all of the following pass on Windows Server 2022:

- Python 3.12.10 is active.
- SABCTools source resolves to exact version 9.6.3 at the pinned upstream commit.
- A `cp312-win_amd64` SABCTools wheel builds successfully.
- The wheel imports from an isolated target and reports version 9.6.3.
- Synthetic yEnc articles covering escaped bytes and a ~700 KiB article decode correctly with CRC validation.
- Concurrent native decode succeeds with eight worker threads.
- The Portable ZIP contains the vendored SABCTools package and does **not** contain `NewzDeckYenc.exe`.
- The final Setup and Portable checksums validate before publication.
- A clean Setup smoke installation contains the SABCTools native extension and no retired yEnc helper.

## Performance basis

Before the production integration, the same NewzDeck decoder adapter was benchmarked on the target Windows machine under NewzDeck's exact CPython 3.12.10 runtime using the last official CPython 3.12 SABCTools Windows wheel. It sustained roughly 250–303 MiB/s across 1–12 workers with zero decode failures, providing substantial headroom over NewzDeck's established ~90–100 MB/s real-world Usenet target. v3.7.1 does not rely on that older wheel: the release pipeline builds and validates exact SABCTools 9.6.3.

## Preserved behavior

This release intentionally leaves the following systems on their v3.7.0 behavior:

- provider connection management and 40–55+ connection workloads;
- queue refill/backpressure logic;
- article cache and asynchronous disk writes;
- Direct Unpack and post-processing;
- private SABnzbd 5.1.2 engine ownership;
- Newsgroup Browser and preview/recovery paths;
- Automation, Smart Import, Calendar and Wanted behavior;
- Backup & Restore and library sorting;
- tray, launcher, service, picker and thumbnail helper architecture;
- all twelve UI themes.

## Defender note

The original problem was a Microsoft Defender machine-learning detection against the small standalone `NewzDeckYenc.exe` helper. v3.7.1 removes that executable from newly published artifacts and from upgraded installations rather than attempting another fingerprint-only rebuild of the same helper architecture.
