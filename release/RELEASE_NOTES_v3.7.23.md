# NewzDeck v3.7.23 — Obfuscated Binary Discovery & Recovery

## New in All Posts / Raw Posts

- **Identify**: Inspect a selected article's **bounded** NNTP BODY prefix on demand. Reads the actual yEnc filename (even if extensionless), declared part/total, yEnc byte range, and a small decoded signature. No background scan of every loaded article.
- **Content type clues**: Detect JPEG, PNG, GIF, WebP, BMP, AVIF, HEIF, MP4, Matroska/WebM, AVI, ZIP, RAR, 7-Zip, PAR2, PDF and several other strong signatures. Unknown content is labelled unknown, not guessed from file size.
- **Single-file queueing**: A complete-looking single yEnc article (no multipart indicators) becomes queueable even if the subject is a random token. It still goes through the established SABnzbd download, verification and safe generated-name logic. Identification does not bypass the transport or invent missing pieces.
- **Fragment awareness**: When yEnc part counters, `=ypart` byte ranges, or the loaded header group show a multipart file, label it a **fragment** and do not pretend that one part is the complete image/video.
- **Save .part**: After identifying a yEnc fragment, the user may explicitly save that **one decoded article** to `Download Folder/Unidentified Fragments/NewzDeck_Fragment_<hash>.part`, with a 4 MiB decoded / 8 MiB wire limit, safe exclusive file creation, and yEnc trailer/CRC checks when present. This intentionally does not reconstruct the complete file, automatically import media, rename it to a playable format, or execute it.
- **Media discovery**: When a likely complete single article's signature confirms an image/video, the type and generated filename can be retained in the existing article-name cache for later browsing. The original filename is **not claimed to have been recovered** unless the yEnc header actually provides it.

## Preserved

- Embedded SABnzbd 5.1.2 and SABCTools 9.6.3, provider settings, Windows service and tray, installed settings and existing downloads.
- v3.7.22 loose image/video filename restoration and Completed history; v3.7.21 failed-cover Image Sets visibility; v3.7.20 date sequences; v3.7.19 scan I/O caching; silent Windows FFmpeg; multi-selection/queueing; Completed Remove All safety; gallery recovery.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 unchanged.

## Important limitations

- An individual 775 KB article may be a fragment of a larger file. A magic signature will usually appear only in its **first** fragment, so a middle fragment can remain unidentified.
- No automatic attempt is made to combine unrelated extensionless headers into a complete multipart file. Existing safe multipart reconstruction continues to operate where metadata allows it.
- A single article without multipart metadata is **possibly complete**, not proven complete until transfer and decoding succeed. Some providers may not have retained the BODY even when the header is listed.
- File-signature recognition is best-effort and is **not** malware protection. Untrusted file contents should not be executed.

## Windows/NNTP acceptance

1. In a newsgroup, choose All Posts, set Show = All and Min size = 0 MB, then switch to Raw Posts. Select an extensionless `POST` and click Identify.
2. Verify small yEnc single-file posts show their actual yEnc name, type if known, and a normal Download option.
3. Identify a middle part of a multi-part upload; it must show Fragment with available part metadata and **not** show normal Download.
4. Save an identified fragment. Verify it appears only in `Unidentified Fragments` with a `.part` suffix and does not replace any existing file.
5. Confirm missing BODY errors, large files and failed CRCs produce a clear error without creating a file.
6. Verify images, videos, Image Sets, loose filename restoration, queueing, Automation, service/tray and download history are unaffected.

Source and offline regression checks cannot replace this real Windows NNTP acceptance.
