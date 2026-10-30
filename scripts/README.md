# Scripts: how the manual is recovered and built

Python 3, standard library only. Run everything from the repository root with `python3 -I scripts/<name>.py`, or use the mise tasks in `mise.toml` (`mise run build`).

## Where the data lives

The scripts work in a data folder that is **not** in git (saved page versions, CDX inventories, images; tens of MB). It defaults to `raw/` in the repository root, which is git-ignored. Point at another folder with `BIGBOX_RAW=/path/to/data`. The HTML build goes to `docs/` (override with `BIGBOX_SITE`).

Optionally set `BIGBOX_SEED` to a read-only folder laid out like a data folder. Files are copied from it before any network request, so a previous download can be reused without being modified.

## The pipeline

**The pipeline only fetches what the manual needs**: the newest good capture of each page it links to, a few older versions of specific pages (see step 1), and the images those use. It does not download the wiki's edit history. Steps 1 and 2 use the network; the rest are offline.

| # | Command | What it does |
| --- | --- | --- |
| 1 | `fetch.py` | Starts at `BigBox_Build_Manual` and follows links to wiki pages (not `File:`, `Special:` and the other wiki namespaces, and not pages about other E3D products; a colon alone does not make a title a namespace). For each page it takes the **newest good capture** (stepping back if that capture is an error page). For pages the archive never saved, it looks back through older versions of the parent page, newest first, and stops at the first version that still has the section. For the removed sections kept in the appendix, which date from the earliest captures, it bisects the page's versions instead (falling back to the newest-first scan if the section is not in the oldest capture). It then fetches only the images those page versions use: the full-size original if archived, otherwise the widest archived thumbnail. |
| 2 | `fetch_files.py` | Downloads the PDF datasheets that apply to the BigBox (V6 hotend, NEMA17 motors, DC fans). |
| 3 | `recover.py` | Rebuilds the pages the archive never saved by cutting their section out of the older parent-page version found in step 1. |
| 4 | `appendix.py` | Builds the "Older version content" appendix and the Datasheets page. |
| 5 | `build.py` | Writes the HTML manual to `docs/`: one page per wiki page, `index.html`, and `manual.html` (everything on one page). |
| 6 | `missing_report.py` | Writes `MISSING.md`: what the archive does not have. |
| 7 | `markdown.py` | Converts the HTML in `docs/` to GitHub Markdown in `manual/` (needs [pandoc](https://pandoc.org): `mise use -g pandoc`). Images and PDFs are not copied; the Markdown links to `docs/images` and `docs/files`. Heading links are rewritten to GitHub's anchors. Override the folders with `BIGBOX_SITE` and `BIGBOX_MD`. |
| 8 | `check_markdown.py` | Checks that every link and image in `manual/` resolves and every `#section` anchor exists. |
| 9 | `check_links.py` | `list` records every external link in `notes/link-status.json` and writes `notes/external-links.md`; `check` tests them (it needs a network that allows the hosts) and records the result. A link whose status is `dead` keeps its text in the manual and is labelled "(dead link)", with a link to the Wayback Machine copy if there is one. A host the sandbox does not allow is recorded as `blocked`, never as dead. `archive` marks a host down when three or more of its links answer 503 and none work, then looks up a Wayback Machine copy of every dead link. |
| 10 | `markdownlint-cli2` | Lints all Markdown in the repository, including the generated `manual/`. Install with `mise use -g npm:markdownlint-cli2`; the rules that do not fit this content are switched off, with reasons, in `.markdownlint-cli2.jsonc`. |

**Reading the exploded drawings** is a separate step, `mise run extract`, which `mise run build` runs first and which is skipped when its inputs have not changed. `drawings.py` reads the parts list off every sheet of the archived `EXPLODED_DRAWINGS.pdf` (a vector PDF, so its text is read directly) into `notes/parts.json`. `drawing_images.py` does the same by OCR (rapidocr, which bundles its models) for the drawing sheets that exist as images in `docs/images`, into `notes/parts_images.json`. The packages they need are in `requirements.txt` (compiled from `requirements.in`). `build.py` uses both files to fill in the Bill of Materials' Printed Parts and Fixings sections. Each script checks its own result and lists sheets it is unsure of under `problems`. `render_sheets.py` (`mise run render`) draws the PDF sheets that stand in for drawing images the archive did not keep (`SHEET_IMAGES` in `targets.py`); `build.py` uses them in place of the missing image and says where they come from.

`targets.py` holds what cannot be derived from the archive: which missing pages to rebuild and from where, which removed sections go in the appendix, and which PDFs apply. Edit it to change those choices.

`fetch.py` also checks saved page versions, including copies from the seed, for an old crawler bug that stored gzip data as text. It reports each one and downloads it again.

Every fetching step caches what it has and can be re-run safely. They are polite to the Wayback Machine (one connection, a delay between requests, backoff on errors) and stop after repeated failures.

## Other files

- `crawl.py` – helpers used by `fetch.py` and `fetch_files.py` (polite fetching, the image inventory, choosing and downloading images, the seed folder). Not run directly.
- `targets.py` – see above.

## Edit history

How the wiki's pages changed over time was analysed once, from about 250 archived versions, with two scripts that have since been removed because the build doesn't need them. The results are in `notes/`: `ANALYSIS.md`, `CLEAN_REPORT.md` and `history/` (see `notes/README.md`). The scripts are in this repository's git history, in pull request #1.

## Choices baked in

- **Latest good version.** Each page uses its newest non-error capture.
- **The wiki's closure notice is removed** from every page (it pointed to a site that no longer exists). The index page mentions it once.
- **Images** that exist only as thumbnails are used as thumbnails. Images with no capture show a placeholder with the original file name.
- **Pages the archive lacks** (Dual X-Carriage, Non-Titan Idler Arms, the IR sensor bracket, Mesh Levelling, Z-Offset calibration) were inline sections of bigger pages until Sept 2016, so they are cut from the last such version. Each says so on the page.
- **Every page with four or more sections has a contents list**, like the wiki's, and on the Build Manual page each heading that links to another page also lists that page's sections.
- **Dead external links are labelled, not hidden.** Which links are dead comes from `notes/link-status.json` (see `check_links.py`).
- **The Downloads page** says where the files the wiki hosted can be found now (the BigBox GitHub repositories and a community settings repository). They are linked, not copied, because four of the five repositories have no licence. It also links Wayback Machine copies of the profiles, Cura and Slic3r configs, exploded drawings and Titan files that were on the old E3D file server. The list is in `targets.py`.
- **Links to pages the archive does not have are plain text.** They are not turned into links to the archive, since the archive has nothing to show.
- **File names are safe on every OS.** Titles such as `Printer_main_assemblies:_Step_By_Step_Assembly_Process` become `Printer_main_assemblies_Step_By_Step_Assembly_Process`, because a colon in a file name breaks a Windows checkout.
- **Stub pages are skipped.** `BigBox_Troubleshooting` never had content beyond "Coming Soon!", so it has no valid capture and is left out.

## Pitfalls found while building this

- Some captures arrive **gzip-compressed**. The fetchers decompress them; without that the page is binary noise and looks like an error.
- A CDX query with **no matches returns an empty body**, which is not a failure. Treating it as one wrongly discards the other URL form's results.
- The wiki's table-of-contents block must be removed as a balanced `<div>`; a regex that stops at the first `</div></div>` deletes real content.
- Asking CDX for non-image files with a mimetype filter hides `warc/revisit` records. The inventory queries use no mimetype filter.

## How this was tested

- **Seeded:** from an empty data folder seeded with a previous download, the first six steps ran without errors and without any network request, touching 47 page versions where the full archive holds about 250.
- **Partly live:** the same run with a deliberately damaged seed (two pages' captures and files, three images and one PDF removed) fetched those live (7 requests) and produced an identical site, with byte-identical downloads.
- **Fully live:** a run with no seed at all downloaded everything (490 requests, about 40 minutes, a handful of transient connection errors that recovered) and matched the committed `docs/` except for one thumbnail, `Z_difference.jpg`. The archive refused that single download once, the pipeline recorded the image as "not archived", and the same download worked a minute later. That is what the retry and failure reporting above fix.
- **Failure handling:** with a stubbed network, a refused download that succeeds on retry is fetched; a capture that is 404 every time is skipped, remembered and replaced by the next capture; one that keeps failing with anything else is reported as a failed download (not as missing); and a failed page download stops the run instead of using an older capture. The live run also found a real dead capture: the archive lists a 600 px capture of `RJ45_panel_mount_cable.jpg` that always answers 404, while its 450 px capture downloads fine.
- **Markdown:** `check_markdown.py` reports every link and image in `manual/` resolving.

## Failed downloads and dead captures

The archive's index sometimes lists a capture it cannot serve, and a working capture sometimes fails once. The two are handled differently:

- A capture that answers **404 or 410 on every attempt** is *dead*: the archive's own data is broken. It is noted, skipped, and remembered so later runs do not retry it. For an image the next capture is tried instead (the original, then thumbnails from widest to narrowest); for a page version, an older capture; for a datasheet, an older PDF. If every capture of an image is dead the image shows as not archived.
- Anything else that goes wrong (a 403, a server error, a network error, or an HTML page instead of an image) is a **failure**, even after retries. It is never mistaken for "not archived" and never falls through to a lower-quality or older capture. An image that fails is marked with an error in `images.json` and listed when `fetch.py` ends, and `fetch.py` exits non-zero; a page version that fails stops the run with a message; `fetch_files.py` reports failed datasheets the same way. Re-running retries only what failed.
- Every download of a listed capture is retried before it counts as either, and after 4 failed downloads in a row the run stops, so a blocked connection does not hammer the archive.

Lookups that are expected to sometimes find nothing (such as asking the index about a page) treat 404 as a plain answer.
