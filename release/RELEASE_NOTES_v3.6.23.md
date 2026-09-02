# NewzDeck v3.6.23 — Accent-Insensitive Automation Search

NewzDeck v3.6.23 promotes the accepted v3.6.23-r1 Automation title-normalization fix built on production v3.6.22. The release fixes searches and local identity checks for canonical metadata titles containing accents when Usenet/indexer releases use ordinary ASCII scene naming.

## Accent-insensitive title identity

- Latin diacritics are folded for search and matching only. Canonical TMDB/library/display titles remain unchanged.
- `90 Day Fiancé` now safely matches release titles such as `90.Day.Fiance.SxxExx`.
- Unicode NFKD decomposition removes combining marks for normal accented Latin characters.
- A small explicit compatibility map handles common Latin characters that do not decompose into simple ASCII equivalents, including `ø`, `ł`, `æ`, `œ`, `ð`, `þ`, `đ`, `ı`, and `ß`.

## Newznab search compatibility

- TV and movie specialized Newznab queries use an accent-folded compatibility title when needed.
- The bounded generic-search fallback uses the same compatibility title together with the existing season/episode or movie-year tokens.
- The original canonical media title remains attached to the Automation item and result metadata; this change does not rewrite library identity.

## Consistent matching across Automation

- The same folded normalization is used by safe local release-title filtering and scoring.
- Filesystem/library reconciliation uses the same title equivalence, preventing an ASCII release filename from being ignored solely because the canonical title contains an accent.
- Smart Import title identity checks use the same normalization while preserving existing destination naming rules and canonical metadata titles.

## Regression safety

- Matching remains token/phrase based rather than arbitrary substring based. `Silo` still does not match the release-group token `EPSILON`.
- Existing stylized/acrostic handling such as `S.W.A.T.` and `9-1-1` remains intact.
- Existing movie year safety remains unchanged after title matching.
- Normal ASCII-only titles follow the same behavior as v3.6.22.

## Preserved production behavior

NewzDeck v3.6.22 All Posts binary resolution/recovery remains intact, including actionable unresolved binaries, `OBFUSCATED NAME` / `NO FILENAME` / `ARTICLE UNAVAILABLE` / retry behavior, long reconstruction polling, loose-binary placement in the configured Download Folder root, and conservative PAR2/archive name recovery.

NewzDeck v3.6.21 image browsing and Related Media behavior remains intact. NewzDeck v3.6.20 authoritative SAB Queue/History control and fresh-state reconciliation also remain intact. Downloads, Automation scheduling, Smart Import, Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior, and normal NZB/package download semantics are not intentionally changed by this release.

Normal installed updates preserve NewzDeck settings, provider configuration, Automation data, history, queue state, and user data.
