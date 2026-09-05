# NewzDeck v3.6.27 — Runtime Adapter Identity Repair

NewzDeck v3.6.27 fixes a production version-consistency regression in v3.6.26. The v3.6.26 UI/backend correctly identified itself as 3.6.26, but the built-in SAB adapter still emitted a hard-coded 3.6.25 runtime identity. NewzDeck's own safety guard therefore reported a background-runtime version mismatch even after a full Windows restart.

## Correct runtime identity

- The built-in SAB adapter now reports **v3.6.27**, matching the UI/backend, manifest, tray and launcher identities.
- The adapter identity is centralized in a single `ADAPTER_VERSION` constant instead of being repeated independently in the snapshot and engine-label paths.
- Queue/download state remains preserved; this release does not reset SAB, Automation state, statistics, or user settings.

## Release validation hardened

- The production publisher now validates the actual `sab_engine.py` runtime identity, not only `build-manifest.json`.
- Publishing is blocked unless `ADAPTER_VERSION`, `APP_VERSION`, `UI_VERSION`, `version.txt`, the build manifest, tray identity and launcher identity all resolve to the same production version.
- Validation also rejects stale literal runtime adapter labels from earlier releases, preventing this exact regression from being published again.

## Preserved behavior

NewzDeck v3.6.26 verified Remove and truly bulk **Remove all failed** behavior remains intact, including targeted Queue/History verification, reduced SAB control pressure and active-transfer safety.

The v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation search, v3.6.22 All Posts binary resolution/recovery, v3.6.21 Related Media/image browsing, and v3.6.20 authoritative SAB Queue/History reconciliation also remain intact.

Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior, provider settings and user-data preservation are not otherwise changed by this release.
