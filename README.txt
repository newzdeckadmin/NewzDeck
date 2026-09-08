NewzDeck v3.6.55
Terminal History Index & Diagnostics Efficiency

New in v3.6.55:
- Unchanged terminal-history sync passes return before copying, sorting, or rebuilding the durable Completed/Failed index.
- Real terminal-history mutations now own exactly one index rebuild, removing the duplicate rebuild path seen during sustained v3.6.54 operation.
- New terminal-history sync/no-op/rebuild telemetry makes long-history efficiency directly observable.
- /api/diagnostics now uses scope-native Live Downloads and reports operational tracked/presentable jobs separately from durable Completed/Failed/Cancelled counts.
- Unmeasured provider latency/success is reported as N/A instead of 0 ms / None%.
- Multi-active diagnostics retain current/last overlap signatures and distinguish raw SAB overlap from visible-card normalization.
- Preserves v3.6.54 compaction/startup efficiency, v3.6.53 NZB identity/Smart Import safeguards, and private SABnzbd 5.1.2 authority.
