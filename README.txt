NewzDeck v3.6.33
TV Edition Search Alias Compatibility

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.33

- Adds safe country-edition TV title aliases when persisted metadata confirms the
  same edition: USA/US, Australia/AU/AUS, United Kingdom/UK/GB, Canada/CA/CAN,
  and New Zealand/NZ/NZL.
- Searches canonical and equivalent suffix forms through bounded Newznab fallback
  queries, then merges and deduplicates returned releases.
- Makes local release identity validation understand the same exact country-suffix
  equivalence while continuing to reject conflicting editions and fuzzy/bare aliases.
- Short country codes must be explicit uppercase suffixes, so ordinary mixed-case
  title words are not reinterpreted as country-edition markers.
- Preserves v3.6.32 Automation target-integrity/no-downgrade protections and the
  accepted v3.6.28-v3.6.31 SAB/download-control stack except for required v3.6.33
  identity markers.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
