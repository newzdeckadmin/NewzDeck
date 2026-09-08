NewzDeck v3.6.53
NZB Identity Gate & Durable Downloads History

New in v3.6.53:
- Automatic single-episode TV grabs inspect actual NZB file subjects before SAB submission. Explicit multi-episode or complete-season evidence is rejected and blacklisted for that target; obfuscated/no-evidence NZBs remain admissible.
- Continuous Automation immediately advances to the next candidate after an NZB-content identity rejection.
- Live Downloads consumes a copy-on-write active-job presentation index and durable terminal counters rather than scanning the full cross-runtime ledger.
- NewzDeck owns compact terminal history (up to 5,000 rows), bootstrapped from existing durable jobs and independent of SAB's bounded History window.
- Completed/Failed pages use compact rows and fetch rich PAR2/block diagnostics only when Details is expanded.
- Queue sampler diagnostics preserve the last failure reason/timestamp and bounded failure-reason counts after recovery.
- Private SABnzbd remains pinned to 5.1.2 and remains authoritative for transfer, repair, extraction, and retry.
