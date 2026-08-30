# NewzDeck v3.6.12 - Installer-Owned Runtime Restore

v3.6.12 is an installed-update lifecycle hotfix built on v3.6.11.

Real-machine acceptance of the v3.6.10 -> v3.6.11 Update Center path proved
that Setup successfully installed the new version and stopped the existing tray
and background service, but the external coordinator did not reliably close the
browser-hosted NewzDeck window or restore the service/tray afterward.

## Installer-owned update lifecycle

- **Setup is now authoritative after file replacement.** Runtime restoration no
  longer depends on the pre-update coordinator surviving and completing a
  second post-Setup phase.
- **Browser-hosted UI closes before file replacement.** Setup invokes the
  currently installed native Picker helper from the signed-in Setup session
  before overlay, then runs the newly installed helper again afterward as a
  safety net before runtime restoration.
- **Service repair now includes service start.** Existing installed services use
  the helper's `install` action after overlay, which both repairs registration
  and waits for the service to reach RUNNING.
- **Tray state is restored.** Setup records whether the tray was running and/or
  configured before upgrade and launches the new tray after service restoration.
- **App relaunch occurs at `ssDone`.** Successful `/update` installs reopen the
  newly installed NewzDeck only after Setup has completed its post-install work.
- **No second coordinator UAC restore.** The external coordinator only launches
  and waits for Setup; Setup owns the post-install runtime state.

## Release regression coverage

The production release workflow now executes the installed smoke upgrade in
`/update` mode. It supplies a deterministic runtime-hold process so the upgraded
service can stay RUNNING, then verifies that the service is actually running
and that the new tray process was restored.

## Preserved

- v3.6.11 SAB Ownership Continuity & Managed Completion reconciliation.
- v3.6.10 Python Source Freshness & Runtime Refresh.
- v3.6.9 native helper/service shutdown protections.
- v3.6.8 Image Browsing Performance & Gallery Quality.
