# NewzDeck v3.6.37 — Operation Progress & Activity Feedback

NewzDeck v3.6.37 is a focused browser/UI feedback release based on an audit of user-triggered actions that can legitimately take long enough to make the application appear unresponsive even though the underlying operation is working.

## Automation Scan files now visibly works

The clearest gap was **Scan files** inside an Automation TV/movie item. The established scan function changed only the global `automationScanBtn`. When invoked from an item modal, the clicked `autoItemScan` button remained visually unchanged while the library scan and reconciliation ran.

v3.6.37 keeps the same `/api/automation/library/scan` path and reconciliation behavior, but the actual clicked item button now enters a disabled **Scanning files…** state with an animated activity indicator. The item modal also shows an inline status explaining that NewzDeck is checking the library location and reconciling file, quality, and cutoff state.

## Audited activity feedback

The audit intentionally distinguishes between operations that already have good feedback and operations that did not.

New busy indicators are added for:

- Automation item **Scan files**, **Refresh metadata**, and **Remove**;
- Automation **Add media**, **Save Continuous Automation**, and **Save import settings**;
- Settings **Save**, **Restore configuration**, **Clear thumbnail cache**, and **Clear preview cache**;
- Diagnostics manual **Refresh** and **Clear**;
- provider **Save** and **Delete**.

These are indeterminate activity indicators because those existing endpoints do not expose trustworthy percentage completion. NewzDeck does not invent fake percentages.

## Existing progress surfaces preserved

The audit found several paths that already communicate activity well, so they are deliberately left on their accepted implementations:

- Manual Media Import uses its real Smart Import transaction percentage/phase/current-file progress;
- full-group search has job progress and cancellation state;
- Newsgroup header loading has skeleton/loading surfaces;
- Discover and title/person details have loading surfaces;
- release searches open an explicit Searching modal;
- indexer/provider/metadata tests and Update Center already show working states;
- Downloads remains driven by its near-real-time authoritative card/state refresh rather than button animation that could obscure download state.

## Version display repair

The published v3.6.36 runtime identity was correct, but its static `index.html` sidebar and About header still displayed **v3.6.35**. v3.6.37 corrects those visible labels and adds a production validation blocker requiring the static visible version, UI version, backend version, SAB adapter version, launcher identity, tray identity, and build manifest to agree.

## Preserved behavior

- v3.6.36 Automation Search/action wiring recovery remains intact.
- v3.6.35 Manual Import live progress remains intact.
- v3.6.34 Manual Import mapping, transactional organization, no-unsafe-partial-import behavior, and immediate Wanted reconciliation remain intact.
- v3.6.32 last-second target validation, existing-quality recovery, no-downgrade protection, and scan/import concurrency safeguards remain intact.
- v3.6.33 country-edition search aliases and local release identity compatibility remain unchanged.
- v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 Downloads continuity remain unchanged except for required v3.6.37 version identity markers.
