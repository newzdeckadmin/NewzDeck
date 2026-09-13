NewzDeck v3.6.90 - Windows Defender Picker Compatibility & Release Gate Hardening

This release fixes the remaining Automation repeat-download loop when Smart Import
proves that the downloaded release is byte-identical to the existing library file.
A fingerprint-proven DUPLICATE now transfers the selected release provenance and
dynamic-range trust to that existing file, recalculates its cutoff state, and stops
Wanted from repeatedly selecting the same payload.

Preserved:
- v3.6.88 confidence-aware dynamic-range and Wanted reconciliation behavior
- v3.6.86 Automation/Interactive Search cache snapshot performance
- SABnzbd 5.1.2 integration and Smart Import transaction safety
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Frozen Newsgroup Browser architecture and tuning

See release/RELEASE_NOTES_v3.6.90.md for details.
