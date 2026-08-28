# NewzDeck v3.5.52

v3.5.52 is the stable Windows production release that consolidates the accepted v3.5.36–v3.5.52 reliability cycle on top of v3.5.35.

## User-visible improvements

- resilient system-tray context menu across long idle periods and Explorer/taskbar recreation;
- near-real-time Downloads updates with stable Active cards and in-place progress updates;
- improved Smart Import completion, cleanup, duplicate/existing-media reconciliation, and Movie import reliability;
- one-time Movie and safely identifiable TV organization from manual Discover grabs without adding the title to Automation;
- faster Discover title opening, detail prefetch/cache, and corrected Interactive Search sizing;
- durable immediate Grab queueing independent of private SAB startup timing;
- corrected private SAB launch when NewzDeck's backend runs under the Windows background service;
- live Verify/Repair/Unpack/Import progress with smooth post-processing motion;
- BOM-safe provider-state loading and authoritative service-runtime handoff so the UI and background service share the same provider state.

The private SAB transfer engine, Automation, Smart Import, and Metadata Server v0.3.3 remain compatible with the established NewzDeck architecture.

## Published release

Tag: `v3.5.52`

Published files:

- `NewzDeck_v3.5.52_Setup.exe`
- `NewzDeck_v3.5.52_Portable.zip`
- `NewzDeck_v3.5.52_SHA256.txt`

Download the release from:

https://github.com/newzdeckadmin/NewzDeck/releases/tag/v3.5.52
