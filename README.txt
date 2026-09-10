NewzDeck v3.6.69
Settings Save Contention Recovery & Reliability Telemetry

New in v3.6.69:
- Recovers settings.json saves from intermittent Windows file-replacement contention by retrying only transient WinError 5/32/33 failures inside a hard three-second window.
- Serializes settings-file replacement attempts and reuses the already-written temporary file; the previous settings file remains intact until atomic replacement succeeds.
- Adds passive settings_save_reliability diagnostics so recovered retries and any terminal failures can be verified directly.
- Preserves browsing schema 7, the accepted All Posts accumulator, six-slot Video ceiling, five-request Image gate, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation.

NewzDeck remains free and open source under GPL-3.0-only.
