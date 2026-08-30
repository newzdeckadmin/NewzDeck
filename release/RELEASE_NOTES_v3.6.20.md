# NewzDeck v3.6.20 — Authoritative SAB & Fresh-State Reconciliation

NewzDeck v3.6.20 is the production promotion of the accepted v3.6.20-r3 Downloads/SAB reliability work.

## One authoritative private SAB runtime

- Normal API identity reconciliation is restricted to the current authoritative SAB generation.
- Historical NewzDeck-owned SAB engines are identified only for retirement/quarantine and are never adopted as the active engine.
- Historical engines with live queue work are paused and preserved rather than destroyed.
- Empty historical engines can be shut down safely.
- Proven stale duplicate queue entries are removed without deleting legitimate tracked re-downloads.

## SAB configuration and provider stability

- Authoritative misc settings are bootstrapped before a fresh SAB generation launches.
- SAB 5.x nested server configuration is parsed correctly.
- Provider configuration is reconciled before optional live configuration.
- A partial live-config control failure cannot create a repeated full-provider rewrite storm.
- Provider runtime state is treated as unknown—not zero—when the SAB status request itself failed.

## Serialized control and fresh-state reconciliation

- NewzDeck-to-SAB localhost API traffic is serialized through one control transport.
- Downloads and Automation completion monitoring share one coherent Queue/History reader.
- Short localhost connection resets are absorbed with bounded read retries.
- Cached Queue/History state has a short lease and is explicitly marked stale.
- Stale cached Queue state cannot trigger engine Pause/Resume recovery.
- Stale cached state cannot drive destructive duplicate/remove reconciliation.
- An old Downloads snapshot can no longer be renewed indefinitely.
- If SAB remains unreadable beyond the coherence window, NewzDeck shows a control-channel refreshing state and treats speed/Remaining as unknown until fresh state returns.
- Ambiguous `addlocalfile` resets reconcile accepted jobs without duplicate submission.

## Verified end-to-end result

The accepted r3 test demonstrated the complete Automation path:

**Automation → Queue → SAB handoff → NNTP download → completion → Smart Import**

It also demonstrated that unavailable Usenet candidates can fail normally, be remembered, and allow Automation to continue to another candidate without leaving stale Queued state or creating a false engine-pause recovery loop.

## Diagnostics polish

- Copy Diagnostics now includes SAB Queue/History reset, short cached-read, degraded-snapshot, stale-snapshot suppression, and queue/history freshness counters.
- The previous `Adopted SAB job from another NewzDeck runtime` event wording is replaced by `Reconciled SAB job after submission/runtime handoff` for ordinary authoritative-queue handoff reconciliation.

Normal installed updates preserve NewzDeck settings, provider configuration, Automation data, history, queue state, and user data.
