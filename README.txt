NewzDeck v3.6.68
Name Resolution Render Accumulator & Wait Telemetry

New in v3.6.68:
- Replaces the All Posts filename-resolution one-shot render timer with a bounded accumulator that can combine sequential resolver results before rebuilding the article DOM.
- Automatic resolver updates keep a 1.4-second soft point, wait at most 3.0 seconds, and flush immediately when a second batch arrives.
- Manual Resolve more names targets three batches with a 4.2-second hard cap and still flushes at the end of the manual pass.
- Adds name_resolution_render_wait telemetry and browsing-performance schema 7 for direct batching-versus-delay acceptance testing.
- Preserves the accepted six-slot high-connection Video ceiling, five-request Image HTTP gate, provider allocation, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation.

NewzDeck remains free and open source under GPL-3.0-only.
