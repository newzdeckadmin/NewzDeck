NewzDeck v3.6.32
Automation Target Integrity & Downgrade Protection

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.32

- Revalidates unattended Automation targets against the current library and physical
  media immediately before NZB retrieval/submission, suppressing stale missing,
  season-pack, and unsafe upgrade grabs.
- Makes Smart Import fail closed for existing media: only a provably better incoming
  file may replace the library file; equal, worse, or indeterminate quality keeps
  the existing file.
- Recovers existing quality from live state, fingerprint history, filename metadata,
  or conservative media probing instead of treating blank quality as permission to
  overwrite.
- Prevents a long-running library scan from overwriting newer Smart Import state by
  detecting per-target scan merge conflicts at commit time.
- Adds Automation target-integrity diagnostics for stale grabs suppressed, scan merge
  conflicts, downgrades blocked, recovered existing quality, and last event time.
- Preserves v3.6.31 historical SAB probe quieting, v3.6.30 runtime-auth/no-op
  synchronization, v3.6.29 persistent HTTP/1.1 control transport, and v3.6.28
  Downloads visibility continuity unchanged except for the v3.6.32 adapter identity.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
