NewzDeck v3.6.23
Accent-Insensitive Automation Search

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.23

- Automation and Interactive Search now treat Latin accents/diacritics as
  equivalent to the ASCII naming commonly used by Usenet releases.
- 90 Day Fiancé now safely finds and accepts releases named
  90.Day.Fiance.SxxExx while keeping the canonical library/display title.
- Newznab TV/movie and generic fallback queries use an accent-folded
  compatibility title when needed.
- The same normalization is used for safe release matching/scoring, filesystem
  reconciliation, and Smart Import title identity checks.
- Common non-decomposing Latin characters such as ø, ł, æ, œ and ß are handled
  for search/matching without changing stored metadata.
- Existing token-based safety remains intact: Silo does not match EPSILON, and
  S.W.A.T. / 9-1-1 retain their prior stylized-title behavior.

NewzDeck v3.6.22 All Posts binary resolution/recovery, v3.6.21 image browsing
and Related Media, and v3.6.20 authoritative SAB/Downloads behavior are
preserved. Normal installed updates preserve settings, provider configuration,
Automation data, history, queue state, and user data.
