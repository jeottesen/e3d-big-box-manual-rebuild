# Scripts: how the manual is recovered and built

Python 3, standard library only. Run everything from the repository root with `python3 -I scripts/<name>.py`.

## Where the data lives

The scripts work on an archive data folder that is **not** in git (it holds saved page versions, CDX inventories and raw HTML, tens of MB). It defaults to `raw/` in the repository root, which is git-ignored. Point at another folder with `BIGBOX_RAW=/path/to/data`. The HTML build goes to `docs/` (override with `BIGBOX_SITE`).

## The pipeline

Steps 1–5 fetch from the Wayback Machine (slow and polite, by design). Steps 6–8 are offline and quick.

| # | Command | What it does |
|---|---|---|
| 1 | `crawl.py pages` | Lists every captured wiki page and image via the Wayback CDX API, then fetches the pages reachable from `BigBox_Build_Manual` (capture nearest 2016-10-18). |
| 2 | `versions.py all` | For each page, finds every capture under both wiki URL forms (`/wiki/Title` from 2015–2016 and `/Title` from 2018+), keeps one file per distinct content hash, and writes text diffs between versions. |
| 3 | `clean.py --apply` | Classifies versions: error pages, mid-history dips, and text-identical duplicates are moved to `versions_removed/`. Writes `versions/latest.json`, the latest good version of each page. |
| 4 | `crawl.py images` | Fetches every image used by any saved version: the full-size original when archived, otherwise the widest archived thumbnail. Records which in `images.json`. |
| 5 | `fetch_files.py` | Downloads the PDF datasheets that apply to the BigBox (V6 hotend, NEMA17 motors, DC fans). |
| 6 | `recover.py` | Rebuilds pages the archive never saved by cutting their section out of older versions of the page that used to contain them. |
| 7 | `appendix.py` | Builds the "Older version content" appendix and the Datasheets page. |
| 8 | `build.py` | Writes the HTML manual to `docs/`: latest good version of each page, images, datasheets, one page per wiki page plus `manual.html` (everything on one page). |

`missing_report.py` writes `MISSING.md` (what the archive does not have) from the saved manifests. `versions.py diff` regenerates the text diffs after `clean.py` has changed the set of versions.

Every fetching step caches what it has and can be re-run safely. They stop after repeated failures instead of hammering the archive.

## Rebuilding only the site

If the data folder is already populated, steps 6–8 reproduce `docs/` exactly:

```
python3 -I scripts/recover.py
python3 -I scripts/appendix.py
python3 -I scripts/build.py
```

## Choices baked in

- **Latest good version.** Each page uses its newest non-error capture. The 2016-10-18 snapshot was only the starting point for the crawl.
- **The wiki's closure notice is removed** from every page (it pointed to a site that no longer exists). The index page mentions it once.
- **Images** that exist only as thumbnails are used as thumbnails. Images with no capture show a placeholder with the original file name.
- **Pages the archive lacks** (Dual X-Carriage, Non-Titan Idler Arms, the IR sensor bracket, Mesh Levelling, Z-Offset calibration) were inline sections of bigger pages until Sept 2016, so `recover.py` cuts them from the last such version. Each says so on the page.

## Pitfalls found while building this

- Some captures arrive **gzip-compressed**. The fetchers decompress them; without that the page is binary noise and looks like an error.
- A CDX query with **no matches returns an empty body**, which is not a failure. Treating it as one wrongly discards the other URL form's results.
- The wiki's table-of-contents block must be removed as a balanced `<div>`; a regex that stops at the first `</div></div>` deletes real content.
- Asking CDX for non-image files with a mimetype filter hides `warc/revisit` records. The inventory queries use no mimetype filter.

## Status of this process

The offline steps 6–8 were verified to reproduce `docs/` exactly from the saved data. The fetching steps were run in stages, with fixes in between, and are resumable. One uninterrupted run from an empty data folder has not been done.
