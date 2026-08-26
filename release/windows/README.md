# Windows release process

The tag workflow builds the conventional unsigned NewzDeck installer and the
portable ZIP from one tested payload. It does not build or change the NewzDeck
runtime, the Metadata Server, or the GitHub Pages site.

## Required payload layout

The resolved payload must have these files at its root:

```text
VERSION.txt                 # X.Y.Z only
NewzDeck.exe                # application entry point
NewzDeck.ico                # real NewzDeck application icon
NewzDeck.Integration.exe    # optional existing integration repair helper
...                         # all other tested runtime files
```

`VERSION.txt` currently records the confirmed NewzDeck baseline, `3.5.31`.
The Metadata Server remains at its confirmed `0.3.3` baseline inside the tested
application payload; this release automation does not build or modify it.

If the existing payload supplies `NewzDeck.Integration.exe`, the installer calls
it after files are installed as:

```text
repair --install-root <install directory> --data-root <persistent data directory>
```

On uninstall it calls:

```text
remove --install-root <install directory> --data-root <persistent data directory> --preserve-user-data
```

That application-owned helper is the safe place to repair/migrate the existing
background-service registration and tray autostart, and to remove only that
integration during uninstall. When the helper is absent, an upgrade leaves the
existing registration untouched. The stable Inno Setup `AppId` and install path
also preserve the existing Inno uninstall journal. Confirm once, before the
first automated release, that `AppId=NewzDeck` matches the historical installer.

The installer never deletes `%LOCALAPPDATA%\NewzDeck`. Settings, provider
credentials, SAB state, queues, Automation libraries, metadata settings, and
other persistent data therefore survive both upgrades and uninstalls.

## Choose where the payload comes from

Edit `payload-source.json` and use one of these source types:

- `repository` (default): copy the tested payload into `payload/` and commit it.
  This is simplest when the payload is a reasonable size.
- `actions-artifact`: set `artifactName` and `runId` to a non-expired artifact
  produced by a trusted build workflow in this repository. The artifact contents
  must be the payload root, not another ZIP. This avoids committing large binaries.
- `url`: set an immutable HTTPS ZIP URL and its lowercase or uppercase SHA-256 in
  `sha256`. The workflow verifies the digest and rejects unsafe archive paths
  before extraction.

Do not use Git LFS merely for releases. Prefer a specific Actions artifact run
or an immutable, checksum-pinned build ZIP when the compiled payload is large.

## Publish a release

1. Put the new, tested Windows payload in the configured source. The payload is
   opaque to this repository: do not change runtime behavior while packaging it.
2. Update the payload's `VERSION.txt` to `X.Y.Z`. For a repository payload this is
   `release/windows/payload/VERSION.txt`.
3. If using an Actions artifact or URL, update `payload-source.json` to pin that
   exact input.
4. Commit and push the payload/configuration change to `main`.
5. Create and push the matching annotated tag:

   ```text
   git tag -a vX.Y.Z -m "NewzDeck vX.Y.Z"
   git push origin vX.Y.Z
   ```

Only a pushed tag matching `v*.*.*` starts publication. Normal branch pushes,
including pushes to `main`, do not run the release workflow.

The workflow then checks that the tag is exactly `v` plus the payload version,
verifies and installs Inno Setup 6.7.3 on a GitHub-hosted Windows runner, builds the installer,
creates the portable ZIP from the same payload, generates SHA-256 checksums, and
creates or updates the matching GitHub Release with exactly these assets:

```text
NewzDeck_vX.Y.Z_Setup.exe
NewzDeck_vX.Y.Z_Portable.zip
NewzDeck_vX.Y.Z_SHA256.txt
```

## One-time repository checks

- GitHub Actions must be enabled.
- Repository or organization policy must allow the workflow's `GITHUB_TOKEN` to
  use `actions: read` and `contents: write`. No personal access token is needed.
- Confirm that the historical installer used `AppId=NewzDeck`. If it used a GUID
  or another value, replace the `AppId` in `NewzDeck.iss` with that exact value
  before the first automated release, then never change it.
- Confirm that the tested payload's existing integration helper follows the
  command contract above. If integration is managed by the application itself,
  omit the helper; the installer will not invent or replace that behavior.

The application remains unsigned. Windows SmartScreen may warn users; the
workflow does not add signing, Defender exclusions, PowerShell exclusions,
self-extracting launchers, or other nonstandard installer behavior.
