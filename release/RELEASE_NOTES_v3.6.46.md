# NewzDeck v3.6.46 — Quality-Aware Release Selection

v3.6.46 corrects a ranking flaw where recent failures from one indexer could subtract as many as 80 points and cause a lower-quality release to become the automatic recommendation even when the configured Quality Profile clearly preferred a higher tier.

## Quality Profile is authoritative

Candidate ordering is now hierarchical. NewzDeck first applies the existing identity, episode, edition, blacklist, safety, size-limit, and automatic-eligibility gates. Among candidates that remain safe, the configured Quality Profile rank is the primary ordering key. Within that tier NewzDeck uses the existing preference score, bounded relative file-size preference, bounded indexer reliability adjustment, and finally recency.

For the built-in **1080p Balanced** profile this means a valid 1080p WEB-DL remains above a valid 720p WEB-DL. Reliability history can choose between comparable 1080p releases, but it cannot demote the entire 1080p tier below 720p.

## Bounded file-size quality signal

File size remains subject to the profile's explicit minimum and maximum limits. In addition, accepted candidates in the same quality tier for the same title/episode are compared against each other. When their reported sizes differ by at least 15%, NewzDeck applies a bounded 0–10 point preference across that same-tier range.

This gives a materially larger same-resolution/same-source release a useful bitrate-quality advantage without creating a simplistic “largest file always wins” rule across different resolutions or quality tiers.

## Indexer reliability remains useful, but small

Indexer outcome history is still tracked over 24 hours. The adjustment is now capped at 12 points and is used only after Quality Profile rank. This preserves the value of temporarily preferring an indexer that has been supplying healthy NZBs without allowing unrelated failures to overwhelm media quality.

## Clearer Interactive Search explanations

Interactive Search now exposes the profile rank and selection score in the Score column, along with the same-tier file-size bonus and indexer reliability adjustment when they apply. **Why this release?** includes those components as well.

## Preserved behavior

This release does not loosen TV title/episode/edition matching, change blacklist semantics, alter the user's profile quality order, modify Smart Import naming, or change Downloads/SAB transport behavior. v3.6.45 library-scan progress, v3.6.44 Library Integrity routing, and the v3.6.42+ strict identity protections remain intact.
