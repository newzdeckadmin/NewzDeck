NewzDeck v3.6.72 - Browse Timeout Error Attribution

This release is a narrow reliability/diagnostic-clarity update built on v3.6.71.

Highlights:
- Upstream NNTP article-header timeouts are no longer mislabeled as a local NewzDeck service outage.
- HTTP/backend errors and browser-to-localhost transport errors are attributed separately.
- Actual localhost backend connection failures still receive local-backend recovery guidance.
- Schema-9 Video decode-suppression policy labels are shortened so the existing 48-character reason contract does not truncate them.
- No browsing/download performance limits, sample sizes, provider allocation, SAB behavior, Automation, Smart Import, Discover, or Metadata Server behavior is retuned.

See release/RELEASE_NOTES_v3.6.72.md for details.
