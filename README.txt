NewzDeck v3.6.28
Downloads Continuity & SAB Recovery Hardening

Downloads visibility continuity:
- Durably owned non-terminal downloads stay visible through transient SAB Queue/History omissions.
- A missing slot is shown as refreshing rather than removing the card from Downloads.
- Stale ownership can expire only after both Queue and History remain freshly absent for the existing retention window.
- Explicit Remove/Cancel tombstones and terminal SAB state remain authoritative.

SAB recovery hardening:
- Shared live Queue/History observations are reused slightly longer to reduce localhost control pressure.
- Temporary tray/user-session launch failures no longer create unnecessary new admin-vN generations.
- SAB startup and HTTP User-Agent labels now follow the current NewzDeck adapter version.
- Diagnostics exposes visibility bridges, queued bridges, open bridges, longest gaps, and SAB omission events.

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.28

- Fixes the intermittent Downloads-card disappear/reappear behavior observed while
  the underlying SAB download continued normally.
- Keeps live status conservative during observation gaps: an expired Active lease
  becomes visible Queued/refreshing rather than falsely claiming active transfer.
- Preserves v3.6.27 runtime adapter identity validation and v3.6.26 verified Remove /
  Remove all failed behavior.
- Preserves v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable
  Download Statistics, and accepted earlier NewzDeck behavior.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
