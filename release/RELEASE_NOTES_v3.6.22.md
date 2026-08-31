# NewzDeck v3.6.22 — All Posts Binary Resolution & Recovery

NewzDeck v3.6.22 promotes the accepted v3.6.22 portable acceptance cycle built on v3.6.21. The release makes reconstructed All Posts binaries reliably actionable even when their posted filenames are delayed, absent, or deliberately obfuscated, while preserving the authoritative SAB/Downloads, Automation, Smart Import, Discover/TMDB, service/tray, and installer behavior established by earlier production releases.

## All Posts binary downloads

- Structurally complete multipart binaries are actionable even before NewzDeck has recovered a friendly filename.
- Individual unresolved binaries can be selected, bulk-selected, queued, and downloaded through the same All Posts controls as named binaries.
- A user-requested download performs a bounded high-priority filename probe first, then safely falls back to a stable generated identity when the original posted name cannot be established.
- Direct loose Newsgroup binary downloads finish directly in the configured Download Folder root instead of creating a filename- or job-named subfolder.
- Grouped binary packages, imported NZBs, Automation jobs, and other package-oriented workflows keep their existing directory semantics.

## Filename resolution

- Automatic name resolution drains the currently loaded unresolved set in bounded backend batches instead of requiring repeated presses of Resolve names.
- Manual Resolve names likewise continues through the loaded candidate set while retaining bounded provider work.
- Name resolution yields to progressive package reconstruction so background filename work cannot starve or invalidate reconstruction.
- Multipart probes can sample representative first, middle, and last segment references before making a terminal classification.
- Retryable NNTP/provider conditions such as timeouts, connection limits, resets, and temporary connection failures are deferred and retried with backoff instead of being recorded as permanent filename failures.
- A circuit-breaker stops the resolver from marching through later items when a provider is temporarily unhealthy.

## Honest filename states

NewzDeck now distinguishes the result it actually observed:

- **Resolved** — a usable posted/yEnc filename was recovered.
- **OBFUSCATED NAME** — yEnc supplied a source name, but it is an opaque or extensionless token rather than a useful human-readable filename.
- **NO FILENAME** — the relevant yEnc data was successfully inspected but no usable `name=` value was supplied.
- **ARTICLE UNAVAILABLE** — representative article data required for the probe is permanently unavailable.
- **RETRYING** — the provider probe failed for a retryable reason and remains eligible for later resolution.

An obfuscated source token remains a valid download identity. NewzDeck does not incorrectly label it as missing simply because it lacks a conventional extension.

## Long package reconstruction

- Progressive package reconstruction polling no longer stops after a small fixed number of checks.
- The browser continues polling with bounded backoff until reconstruction completes, or cancels immediately if the user changes the relevant provider/group/page/session.
- Transient reconstruction polling errors retry instead of leaving a permanently stranded “Finishing package reconstruction in the background…” state.
- Required runtime helper validation prevents a syntax-valid JavaScript package from omitting the binary name-resolution helper used by reconstructed rows.

## Obfuscated-name recovery

- After an opaque loose download completes, NewzDeck can opportunistically recover an exact protected filename from local PAR2 FileDesc metadata.
- Automatic PAR2 renaming requires both the protected-file byte length and full-file MD5 to match, avoiding speculative or unsafe renames.
- Recovery works whether the PAR2 arrives before the opaque payload or after it; later PAR2 completion can reconcile already-completed opaque files from the same provider/newsgroup context.
- Local RAR, ZIP, and 7-Zip member names may provide a conservative **NAME HINT** for diagnostics and identification, but archive contents alone are not treated as proof of the original outer archive filename.
- If no trustworthy mapping exists, the obfuscated source identity is preserved rather than guessed.

## Diagnostics and UI feedback

- All Posts exposes separate resolved, resolving/retrying, obfuscated, no-filename, and unavailable states instead of collapsing them into one generic failure.
- Downloads can expose **NAME RECOVERED** when exact PAR2 recovery succeeds and **NAME HINT** when archive inspection provides useful but non-authoritative context.
- Diagnostics include filename-resolution/retry and recovery-source state to make provider and obfuscation behavior easier to distinguish.

## Preserved production behavior

NewzDeck v3.6.21 Newsgroups image browsing and Related Media behavior remains intact, including direct loose-image placement, incremental Related Media indexing, long-session DOM windowing, bounded broken-set health checks, and cover scheduling/promotion.

NewzDeck v3.6.20 authoritative SAB Queue/History control and fresh-state reconciliation remain intact. Automation, Smart Import, Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior, and normal NZB/package download semantics are not intentionally changed by this release.

Normal installed updates preserve NewzDeck settings, provider configuration, Automation data, history, queue state, and user data.
