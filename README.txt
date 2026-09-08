NewzDeck v3.6.57
Import Hold Semantics & Downloads Count Integrity

New in v3.6.57:
- Completed/Failed durable counts now match the actual page-native presentation tabs while raw SAB transfer results remain available separately.
- Duplicate-content Smart Import holds use the explicit import_integrity_hold failure class and preserve reason/fingerprint evidence.
- The exact release that produced a proven duplicate-media conflict is blacklisted for that target.
- Two distinct releases producing the same conflicting fingerprint pause unattended searching for that target pending manual review.
- Automation Health shows active Integrity Holds separately from ordinary preserved imports.
- Preserves v3.6.56 duplicate protection, v3.6.55 terminal-history efficiency, diagnostics caching, recovered-warning handling and private SABnzbd 5.1.2.
