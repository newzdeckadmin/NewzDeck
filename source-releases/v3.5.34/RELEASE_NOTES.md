# NewzDeck v3.5.34 — unreleased reliability candidate

**This version was not published as an end-user GitHub Release.**

v3.5.34 was used to validate a set of application reliability improvements after v3.5.33. The application changes were accepted, but final Windows installer testing found upgrade/tray issues that prevented publication.

The accepted work was carried forward into **v3.5.35**, which is the released version users should install.

## Reliability work carried into v3.5.35

- updater compatibility with the official GitHub latest-release feed;
- Windows sleep/resume lifecycle hardening;
- protection against late Downloads polling responses overwriting newer state;
- Completed history ordered by actual completion time, newest first;
- TMDB attribution asset/layout correction;
- localhost request hardening and cleaner unexpected-error responses;
- Watch Folder rotation beyond the first 100 NZBs;
- production package cleanup.

The SAB transfer/post-processing data path remained unchanged.

For the current release, see:

https://github.com/newzdeckadmin/NewzDeck/releases/latest
