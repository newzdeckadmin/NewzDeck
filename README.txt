NewzDeck v3.6.36
Automation Action Wiring Recovery

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.36

- Restores Automation manual Search / Search releases buttons that stopped responding
  in v3.6.35 because their shared browser-side wiring helper was accidentally removed.
- Restores TV episode search, Wanted Search releases, and season-pack search wiring.
- Restores the adjacent Automation item actions lost by the same edit: Save, Refresh
  metadata, Open folder, Remove, and Scan library.
- Adds production release checks that require these Automation helper functions before
  a source commit can be published, preventing the same regression from shipping again.
- Preserves v3.6.35 Manual Import live progress and all accepted v3.6.34 import,
  v3.6.32 integrity/no-downgrade, v3.6.33 TV-edition, and SAB/download-control behavior.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.
