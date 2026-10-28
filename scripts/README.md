# Scripts: how the manual is recovered and built

Python 3, standard library only. Run everything from the repository root with `python3 -I scripts/<name>.py`.

## Where the data lives

The scripts work in a data folder that is **not** in git (saved page versions, CDX inventories, images; tens of MB). It defaults to `raw/` in the repository root, which is git-ignored. Point at another folder with `BIGBOX_RAW=/path/to/data`. The HTML build goes to `docs/` (override with `BIGBOX_SITE`).

Optionally set `BIGBOX_SEED` to a read-only folder laid out like a data folder. Files are copied from it before any network request, so a previous download can be reused without being modified.

## The pipeline

Only the manual's own pages are fetched. Steps 1 and 2 use the network; steps 3 to 6 are offline.

| # | Command | What it does |
|---|---|---|
| 1 | `fetch.py` | Starts at `BigBox_Build_Manual` and follows links. For each page it takes the **newest good capture** (stepping back if that capture is an error page). For pages the archive never saved, it looks back through older versions of the parent page, newest first, and stops at the first version that still has the section. For the removed sections kept in the appendix, which date from the earliest captures, it bisects the page's versions instead (falling back to the newest-first scan if the section is not in the oldest capture). It then fetches only the images those page versions use: the full-size original if archived, otherwise the widest archived thumbnail. |
| 2 | `fetch_files.py` | Downloads the PDF datasheets that apply to the BigBox (V6 hotend, NEMA17 motors, DC fans). |
| 3 | `recover.py` | Rebuilds the pages the archive never saved by cutting their section out of the older parent-page version found in step 1. |
| 4 | `appendix.py` | Builds the "Older version content" appendix and the Datasheets page. |
| 5 | `build.py` | Writes the HTML manual to `docs/`: one page per wiki page, `index.html`, and `manual.html` (everything on one page). |
| 6 | `missing_report.py` | Writes `MISSING.md`: what the archive does not have. |

`targets.py` holds what cannot be derived from the archive: which missing pages to rebuild and from where, which removed sections go in the appendix, and which PDFs apply. Edit it to change those choices.

Every fetching step caches what it has and can be re-run safely. They are polite to the Wayback Machine (one connection, a delay between requests, backoff on errors) and stop after repeated failures.

## Optional: the full edit history

These are for analysis, not for building the manual. They download every distinct archived version of each page, so they are much slower.

| Command | What it does |
|---|---|
| `versions.py all` | Finds every capture of each page under both wiki URL forms (`/wiki/Title` from 2015–16 and `/Title` from 2018+), keeps one file per distinct content hash, and writes text diffs between versions. |
| `clean.py --apply` | Moves error pages, mid-history dips and text-identical duplicates to `versions_removed/`, and writes the latest good version of each page. |
| `crawl.py pages` / `crawl.py images` | The original crawler: the manual's pages nearest 2016-10-18, and images for every saved version. `fetch.py` uses this file's helpers. |

`notes/CLEAN_REPORT.md` and `notes/ANALYSIS.md` came from this full-history run.

## Choices baked in

- **Latest good version.** Each page uses its newest non-error capture.
- **The wiki's closure notice is removed** from every page (it pointed to a site that no longer exists). The index page mentions it once.
- **Images** that exist only as thumbnails are used as thumbnails. Images with no capture show a placeholder with the original file name.
- **Pages the archive lacks** (Dual X-Carriage, Non-Titan Idler Arms, the IR sensor bracket, Mesh Levelling, Z-Offset calibration) were inline sections of bigger pages until Sept 2016, so they are cut from the last such version. Each says so on the page.
- **Stub pages are skipped.** `BigBox_Troubleshooting` never had content beyond "Coming Soon!", so it has no valid capture and is left out.

## Pitfalls found while building this

- Some captures arrive **gzip-compressed**. The fetchers decompress them; without that the page is binary noise and looks like an error.
- A CDX query with **no matches returns an empty body**, which is not a failure. Treating it as one wrongly discards the other URL form's results.
- The wiki's table-of-contents block must be removed as a balanced `<div>`; a regex that stops at the first `</div></div>` deletes real content.
- Asking CDX for non-image files with a mimetype filter hides `warc/revisit` records. The inventory queries use no mimetype filter.

## How this was tested

- From an empty data folder seeded with a previous download, the six steps ran without errors and without any network request. They touched 47 page versions, where the full archive holds about 250.
- A second run with a deliberately damaged seed (two pages' captures and files, three images and one PDF removed) fetched those live (7 requests), and produced a site identical to the first run, with byte-identical downloads.
- The committed `docs/` is that build.
- Not tested: one uninterrupted run with **no** seed. The live fetch paths were exercised only for the small set above.
