# NewzDeck v3.7.13 — Deferred Preview Terminal Cleanup

Corrects the gallery's endlessly reappearing **Waiting briefly for preview recovery…** placeholders.

- Image recovery deadlines now attach to stable article identity, not a replaceable loader element.
- Timers continue offscreen and through gallery redraws and virtualization.
- After the original 12-second waiting budget expires, unrecovered images are suppressed in the current browsing session. An active full-image recovery still receives its own bounded timeout.
- Full-image fallback failures remove unusable image cards rather than leaving a retryable placeholder.
- Successfully decoded and quality-checked images clear their deferred state.

No Usenet posts, downloads, cached source files, or user settings are deleted. Image Sets, viewer actions, NNTP, SABnzbd, SABCTools, native decoder, Automation and managed updates are unchanged.
