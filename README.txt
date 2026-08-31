NewzDeck v3.6.22
All Posts Binary Resolution & Recovery

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.22

- Complete All Posts multipart binaries remain downloadable even when their
  posted filename is delayed, absent, or deliberately obfuscated.
- Name resolution now drains loaded unresolved items automatically in bounded
  batches and distinguishes RESOLVED, OBFUSCATED NAME, NO FILENAME,
  ARTICLE UNAVAILABLE, and retryable provider outcomes.
- Temporary provider failures back off and retry instead of turning the rest of
  a page into permanent NAME UNAVAILABLE results.
- Long package reconstruction continues polling until completion or navigation
  cancellation instead of giving up after a short fixed polling window.
- Direct loose binary downloads now finish in the configured Download Folder
  root without a per-file subfolder, matching direct loose-image behavior.
- Opaque yEnc names remain valid download identities; completed file signatures
  can supply a safe extension where possible.
- Exact PAR2 FileDesc metadata can opportunistically recover a protected
  filename using byte length plus full-file MD5, in either PAR2/payload order.
- Archive contents can provide conservative NAME HINT information without
  guessing the original outer archive filename.

NewzDeck v3.6.21 image browsing/Related Media behavior and v3.6.20
SAB/Downloads/Automation reliability behavior are preserved.
Normal installed updates preserve settings, provider configuration, Automation
data, history, queue state, and user data.
