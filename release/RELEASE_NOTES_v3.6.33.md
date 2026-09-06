# NewzDeck v3.6.33 — TV Edition Search Alias Compatibility

NewzDeck v3.6.33 is a narrowly scoped Automation/indexer compatibility release based on a production case where valid **Love Island USA** episodes were present on configured Newznab indexers under release names using **Love Island US**. The v3.6.32 search path sent only the canonical TMDB title and its local release validator required that same canonical token sequence, so these releases could be invisible even though a manual indexer search found them.

The fix is generalized to the same common country-edition naming variations used by other TV releases. The v3.6.32 target-integrity/downgrade protections and the accepted SAB/download-control stack are not redesigned in this release.

## Safe country-edition title aliases

For TV items only, NewzDeck now creates bounded search/match aliases when both the canonical title and persisted TV country identity agree on the same edition. Supported suffix families are:

- United States: `USA` ↔ `US`
- Australia: `Australia` ↔ `AU` ↔ `AUS`
- United Kingdom: `United Kingdom` ↔ `UK` ↔ `GB`
- Canada: `Canada` ↔ `CA` ↔ `CAN`
- New Zealand: `New Zealand` ↔ `NZ` ↔ `NZL`

For example, **Love Island Australia** yields the exact search variants:

- `Love Island Australia`
- `Love Island AU`
- `Love Island AUS`

Short country codes must be uppercase in the canonical stored title. This prevents ordinary mixed-case words such as the `Us` in **This Is Us** from being reinterpreted as a country marker. The rule does not create fuzzy franchise aliases and does not make a bare ambiguous franchise title equivalent to a country edition.

## Indexer search compatibility

The canonical specialized Newznab TV search remains first. For a confirmed country-edition title, NewzDeck also performs bounded generic searches using its equivalent country-suffix aliases. If the canonical specialized query returns nothing, the existing canonical generic fallback remains in place as well. Results from all successful paths are merged and deduplicated by GUID/download URL/title.

The per-indexer worker wall-clock allowance is expanded only enough to cover one canonical specialized request plus the canonical generic fallback and at most two alias generic searches. Ordinary titles preserve the previous fast path when their canonical specialized search returns results.

## Alias-aware release identity validation

Local validation accepts any permitted exact country-suffix variant before applying the existing edition-safety checks. For example, an Australian item whose canonical title is **Love Island Australia** can accept:

- `Love.Island.Australia.S03E20...`
- `Love.Island.AU.S03E20...`
- `Love.Island.AUS.S03E20...`

while rejecting conflicting editions such as `Love.Island.US...` or `Love.Island.UK...`. The same exact-edition behavior applies to the supported US, UK, Canada, and New Zealand suffix families.

## Preserved behavior

- Base retry timing, smart retry state, Wanted policy, queue depth, and Continuous Automation scheduling behavior are unchanged.
- v3.6.32 last-second target revalidation, no-downgrade Smart Import guard, existing-quality recovery, and scan/import optimistic concurrency remain intact.
- v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 Downloads continuity remain unchanged except for required v3.6.33 version identity markers.
