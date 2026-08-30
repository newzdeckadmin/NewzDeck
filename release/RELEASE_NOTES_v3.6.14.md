# NewzDeck v3.6.14 - Automation Save Reliability & Responsiveness

NewzDeck v3.6.14 is a focused Automation state reliability and responsiveness hotfix built on v3.6.13.

## Windows-safe Automation state persistence

- **Same-file serialization:** Automation JSON readers and atomic writers now share a per-file reentrant lock. A NewzDeck reader can no longer keep `media-library.json` open while another NewzDeck thread tries to replace it.
- **Bounded sharing retry:** short-lived Windows `Access is denied` / sharing-style failures during the final atomic replace are retried with bounded backoff before NewzDeck surfaces a real save error.
- **Atomicity preserved:** NewzDeck still writes a temporary JSON file and atomically replaces the destination. It does not fall back to truncating or rewriting the live state file in place.
- **External-handle tolerance:** the bounded retry window also absorbs brief third-party file handles such as antivirus or indexing activity without allowing an indefinite save stall.

## Faster monitoring-setting saves

- **Truthful immediate acknowledgement:** after `/api/automation/media/update` successfully persists the item, the Automation detail dialog immediately reports the Save as complete.
- **Summary refresh no longer blocks Save:** Wanted, Calendar, health, counts, and other aggregate Automation state refresh asynchronously after persistence.
- **Authoritative item state is merged first:** the server-returned media item is applied locally before the background summary refresh starts.
- **Season/episode toggles are responsive too:** individual monitoring toggles no longer wait synchronously for a full Automation summary rebuild.

## Preserved from v3.6.13

- Stable Active cards across transient SAB presentation gaps.
- Verified Remove/Cancel and hidden-transfer reconciliation.
- Wanted backlog/upgrade policy visibility.
- Individual-episode-first Automation with season packs only as a whole-season fallback.
- v3.6.12 installer-owned Update Center runtime restoration.
- Prior SAB ownership, Smart Import, and Python source-freshness protections.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under NewzDeck's version-independent user-data directory.
