# NewzDeck v3.6.96 - Library Article-Aware Sorting

NewzDeck v3.6.96 is a narrow presentation-order update built on the proven v3.6.95 production baseline. It changes only how TV Shows and Movies are alphabetized in the Automation library.

## Changed

- **Leading articles no longer control library placement.** A title beginning with **A**, **An**, or **The** is sorted using the next word.
- **A Knight of the Seven Kingdoms** sorts under **K** (Knight).
- **The Legend of Vox Machina** sorts under **L** (Legend).
- **An American...** sorts under **A** (American).
- Article matching is case-insensitive and requires a complete leading word followed by whitespace, so titles such as **Theodore** and **Annihilation** are unaffected.
- The title shown on cards and throughout NewzDeck remains exactly the original title; this does not rename media, folders, or metadata.

## Preserved

- TV and Movie libraries continue to use the same deterministic comparator, with the full title, year, and media id retained as tie-breakers.
- All twelve themes and the v3.6.95 light-theme readability fixes are unchanged.
- No Automation monitoring, Wanted, Smart Import, Discover, Newsgroup Browser, Downloads, post-processing, SABnzbd, metadata, or library naming behavior is changed.
- The Defender-clean folder-only Picker, accepted yEnc helper, direct checksum-verified Setup updater, and installer-owned runtime handoff are unchanged.
- Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.

## Release-gate additions

- The release gate verifies article-aware sorting examples and confirms visible titles are unchanged.
- The v3.6.95 stylesheet/theme payload and protected native/update architecture are frozen.
