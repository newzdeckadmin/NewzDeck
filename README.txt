NewzDeck v3.6.26
Verified Remove & Bulk Failed Cleanup

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.26

- Individual Remove no longer fails solely because a separate short SAB localhost
  ping resets while downloads remain healthy.
- Remove verifies the requested job directly against targeted SAB Queue/History
  state with bounded retries.
- Remove all failed performs targeted multi-ID verification and bulk History
  deletion instead of one full SAB control sequence per Failed card.
- Active SAB Queue jobs remain protected: NewzDeck will not hide live transfers
  without fresh safety proof.
- The v3.6.25 Automation backlog/Smart Import safeguards, franchise/edition
  protection, lower state-write pressure, and read-only integrity audit remain intact.

NewzDeck v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation
matching, v3.6.22 All Posts binary resolution/recovery, v3.6.21 Related Media/image
browsing, and v3.6.20 authoritative SAB/Downloads behavior remain preserved.
Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
