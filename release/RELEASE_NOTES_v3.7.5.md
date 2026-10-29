# NewzDeck v3.7.5 - Related Media Grouping Reliability

v3.7.5 is a focused Newsgroups Related Media correctness release built on the stable v3.7.4 runtime.

## Fixed

- **More obvious image/video series become Related Media sets.** The set classifier now recognizes common trailing sequence formats including bare counters, bracketed counters, and explicit index/total forms such as `(03)`, `[03]`, `03 of 25`, `03-of-25`, and `03/25`.
- **Separator differences no longer split one obvious set.** Equivalent bases such as `Family-Trip`, `Family.Trip`, and `Family Trip` normalize to the same conservative set identity when a real sequence marker is present.
- **Poster identity is more stable.** When a standard `From` address is available, grouping keys use the canonical email identity rather than requiring the entire display-name string to match byte-for-byte.
- **Year-like suffixes are protected.** A bare four-digit suffix in the 1900-2099 range is not treated as an image sequence by itself, reducing accidental grouping of year-named files.
- **Continuous browsing uses stable article keys when promoting a newly completed set.** Existing gallery cards are removed by stable article identity instead of relying on an older array index.

## Preserved

- Related Media still requires at least three members before a set is promoted.
- Sets remain isolated by newsgroup, media kind, normalized base, and poster identity.
- Existing broken-set probing, cover scheduling, thumbnail concurrency, gallery virtualization, and viewer behavior are unchanged.
- Private SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack, PAR2/repair, Automation, Smart Import, Backup & Restore, and all themes are unchanged.
- The v3.7.3 managed About & Updates Setup lifecycle remains unchanged.

## Publisher reliability

The guarded publisher now accepts a successful GitHub Pages deployment attached to either the reviewed source commit or the later trigger-only commit. GitHub may cancel either run as superseded depending on timing; a successful deployment on either valid commit is authoritative.

Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.
