NewzDeck v3.6.39
Automation Startup Reservation Refinement

Focused follow-up to v3.6.38 based on a live post-update diagnostic snapshot.

WHAT'S NEW IN v3.6.39

- pending-* Automation handoff reservations now receive only a 120-second startup grace period instead of consuming queue capacity for the full ten-minute recovery window.
- Persisted targets with a durable non-pending collection identity keep the stronger v3.6.38 startup recovery protection.
- Automatic queue admission still rechecks authoritative live occupancy immediately before every Grab.
- The cycle no longer uses a static max-grab allowance calculated from its first snapshot.
- Search budget is based on configured queue depth, so capacity that becomes available during a running cycle can be used immediately.
- v3.6.38 crash-recovered Smart Import reconciliation, sole paused-job recovery, and engine-ready gating are preserved unchanged.

This release is intentionally narrow and does not alter Newznab matching/scoring, failure blacklists, Smart Import transaction behavior, no-downgrade protection, or manual Search/Grab.
