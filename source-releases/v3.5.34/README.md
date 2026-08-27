# NewzDeck v3.5.34 source status

v3.5.34 is the first normal follow-on release after the v3.5.33
source-complete Windows transition.

## Acceptance

The final Windows behavior acceptance revision was **v3.5.34-r5**.

Acceptance Portable SHA-256:

```text
dafd586bb6b9eaa13b656310c54198f308bee3506ecdf9e0f5cdf413f71aa519
```

The `-r5` suffix and acceptance service-handoff files are intentionally **not**
part of the production release. The production source is normalized to plain
`3.5.34`, and the final Portable/Setup assets are rebuilt from the public
`v3.5.34` source tag by GitHub Actions.

## Reliability hardening

- canonical GitHub updater asset/feed support;
- Windows sleep/resume desktop-heartbeat hardening;
- out-of-order Downloads polling protection;
- localhost browser-origin protection;
- safe unexpected-error responses;
- fair Watch Folder rotation beyond 100 NZBs;
- corrected TMDB attribution asset/layout;
- Completed history ordered newest-to-oldest by real completion time;
- durable SAB completion-time backfill for pre-v3.5.34 history;
- production package cleanup.

The SAB transfer/post-processing data path is unchanged from the accepted
v3.5.33 architecture. Metadata Server v0.3.3 remains the matching service.

## Source-complete Windows model

All six NewzDeck-owned Windows executables remain mapped to public Go source:

- `NewzDeck.exe` → `src/windows/NewzDeckLauncher.go`
- `NewzDeckService.exe` → `src/windows/NewzDeckService.go`
- `NewzDeckTray.exe` → `src/windows/NewzDeckTray.go`
- `NewzDeckPicker.exe` → `src/windows/NewzDeckPicker.go`
- `NewzDeckThumb.exe` → `src/windows/NewzDeckThumb.go`
- `NewzDeckYenc.exe` → `src/windows/NewzDeckYenc.go`

The final release workflow rebuilds these binaries with Go 1.23.2 and produces
the Portable ZIP and Setup EXE from the tagged source.
