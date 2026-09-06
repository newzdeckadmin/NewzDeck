NewzDeck v3.6.29
Persistent SAB Control Transport

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.29

- Replaces explicit per-request localhost SAB HTTP connection teardown with a
  serialized persistent HTTP/1.1 control connection.
- Queue, History, statistics, completion monitoring and normal SAB API traffic can
  reuse the same private localhost socket while all requests remain single-filed.
- Genuine transport failures invalidate the connection before the existing bounded
  retry/reconciliation logic runs, so a bad socket is never reused.
- Long-idle connections, SAB listener/port changes, and server-requested closes are
  reopened cleanly without being confused with a failed download.
- Diagnostics now exposes SAB HTTP requests, connections opened/reused, reuse
  percentage, reconnects, transport resets, server closes, idle reopens, and
  transport-reset counts grouped by SAB API mode.
- The v3.6.28 Downloads visibility-continuity bridge remains unchanged as a separate
  safeguard against any Queue/History omission that still occurs.

NewzDeck v3.6.28 durable Downloads continuity, v3.6.27 runtime adapter identity
validation, v3.6.26 verified Remove / Remove all failed, v3.6.25 Automation
backlog/Smart Import safeguards, v3.6.24 durable Download Statistics and accepted
earlier behavior remain preserved.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
