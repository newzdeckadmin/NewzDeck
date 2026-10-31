# NewzDeck v3.7.14 — Completed Downloads Remove All

Adds a **Remove all completed (N)** action in **Downloads → Completed**.

- Shows the action only while the Completed history contains entries and displays the **entire** Completed count, including pages not yet loaded.
- Requires explicit confirmation that removal is history-only and that downloaded/imported media will **not** be deleted.
- Clears the durable NewzDeck completed-history index and makes a history-only SABnzbd cleanup request (`del_files=0`), never a general Remove or Queue delete.
- Does not erase download files, imported media, lifetime statistics, active/queued work, unfinished post-processing, or Failed downloads.
- The existing **Clear completed** shortcut now routes through the same guarded confirmation and backend action.
- Handles a temporarily unavailable SABnzbd history connection without deleting media or unexpectedly clearing active downloads; history tombstones prevent stale completed entries from reappearing.

Preserves all v3.7.13 deferred-preview fixes and image/related-set handling, SABnzbd 5.1.2, SABCTools 9.6.3, NNTP, Direct Unpack/PAR2, Smart Import, Automation, themes and managed updates.
