# NewzDeck v3.7.17 — Original Image Set Filenames

Fixes new loose images downloaded from Newsgroups/Image Sets occasionally being saved as `NewzDeck Loose <token>.jpg` rather than the filename NewzDeck originally displayed.

## Fixed

- SABnzbd still receives a unique internal `NewzDeck Loose <token>` staging job identity for safe queue reconciliation.
- On completion, if a single recovered image is named after **that job's exact internal token** and the expected filename is known and has the same image extension, NewzDeck uses the original filename for the saved file.
- Both the staged-folder completion path and SABnzbd's direct-to-download-folder path are covered.
- Existing filename collisions use NewzDeck's numbered suffixes (for example, `photo (2).jpg`) instead of overwriting a file.
- Completed display names agree with the recorded flattened filename, not SABnzbd's temporary staging name.

## Safety and scope

- No guessing when filenames are unknown/opaque; no renaming of multi-file packages, unrelated tokens, non-image files, or already-correct names.
- Previously completed files are **not** renamed automatically. This change applies when new completed jobs are finalized.
- Existing v3.7.16 silent FFmpeg/FFprobe helpers, v3.7.15 media filtering and bulk queue jobs, v3.7.14 Completed-history safety, and v3.7.13 preview recovery remain unchanged.
- NNTP, SABnzbd 5.1.2, SABCTools 9.6.3, PAR2, Smart Import, Metadata Server, Diagnostic Collector, background service, tray, and managed updates remain unchanged.

## Windows acceptance

1. Download an Image Set that previously generated a `NewzDeck Loose <token>.jpg` file. Verify saved files use the recognized image names.
2. Download the same filename twice. Confirm `(2)` is appended and the original file is not overwritten.
3. Confirm Completed displays the saved name, video previews remain console-free, and the bulk queue and history controls still work.
4. Confirm unknown names and genuine multi-file packages are not silently renamed.

Automated tests verify the naming logic, not live NNTP or Windows filesystem behavior.
