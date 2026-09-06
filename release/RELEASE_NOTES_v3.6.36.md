# NewzDeck v3.6.36 — Automation Action Wiring Recovery

NewzDeck v3.6.36 is a focused production hotfix for a browser-side regression introduced by the v3.6.35 Manual Import progress UI edit.

## What broke in v3.6.35

The v3.6.35 `app.js` edit unintentionally removed a shared block of Automation helper functions while leaving the UI controls that call those functions in place. In particular, `wireReleaseSearchButtons()` was removed even though Wanted and TV item rendering still invoked it. The resulting JavaScript `ReferenceError` prevented manual release-search controls from receiving their click handlers.

The same lost block also contained several adjacent Automation item helpers, so the regression was broader than the first visible Search symptom.

## Restored Automation actions

v3.6.36 restores the accepted v3.6.34 implementations for:

- Wanted **Search releases** buttons;
- TV episode **Search** buttons;
- **Search Season pack** buttons;
- Automation item **Save**;
- **Refresh metadata**;
- **Open folder**;
- **Remove**;
- **Scan library**.

The release-search backend, Newznab requests, scoring, blacklist logic, and manual Grab behavior were not removed and are not redesigned by this hotfix. v3.6.36 restores the browser-side functions that connect the existing controls to those established paths.

## Regression prevention

The production publishing package now treats the Automation action helpers as release blockers. Before a production source commit can be created, validation requires all restored helper definitions, the `data-release-search` and season-pack bindings, and the v3.6.35 Manual Import progress markers to coexist in the final `app.js`.

The validation suite also executes the restored `wireReleaseSearchButtons()` function against mock episode and season-pack buttons and verifies that clicking them dispatches the expected item/season/episode arguments.

## Preserved behavior

- v3.6.35 Manual Media Import live progress, asynchronous start/poll behavior, phase/current-file reporting, and 100%-after-Wanted-reconciliation semantics remain unchanged.
- v3.6.34 Manual Media Import mapping, preview, transactional rename/move, no-unsafe-partial-import behavior, and immediate Wanted reconciliation remain intact.
- v3.6.32 last-second target validation, existing-quality recovery, no-downgrade Smart Import protection, and scan/import concurrency safeguards remain intact.
- v3.6.33 country-edition search aliases and local release identity compatibility remain unchanged.
- v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 Downloads continuity remain unchanged except for required v3.6.36 version identity markers.
