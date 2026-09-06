NewzDeck v3.6.31
Historical SAB Probe Quieting

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.31

- Skips known-dead historical SAB localhost ports before any HTTP version probe by
  checking whether the port is actually occupied.
- Occupied historical ports still require the existing full SAB version fingerprint
  plus historical NewzDeck API-key authentication before quarantine actions are
  allowed.
- Adds Historical SAB sweep diagnostics for sweeps, ports considered, closed-port
  skips, occupied probes, authenticated stale engines, and last sweep time.
- Preserves v3.6.30 runtime-auth/no-op synchronization, v3.6.29 persistent HTTP/1.1
  transport, and v3.6.28 Downloads visibility continuity unchanged.

NewzDeck v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control
transport, v3.6.28 durable Downloads continuity, v3.6.27 runtime adapter identity
validation, v3.6.26 verified Remove / Remove all failed, v3.6.25 Automation
backlog/Smart Import safeguards, v3.6.24 durable Download Statistics and accepted
earlier behavior remain preserved.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
