# Reviewed sheet data

One JSON file per sheet of the BigBox exploded drawings: the parts list a person has checked. **This is the source of truth** for the Printed Parts and Fixings lists on the Bill of Materials page. The build (`scripts/build.py`) reads these files and nothing the tools propose.

The extraction tools (`scripts/drawings.py`, `scripts/drawing_images.py`, `scripts/match_sheets.py`; `mise run propose`) never write here. They write proposals to `work/proposed/` (git-ignored). `scripts/drift.py` (`mise run drift`) compares the proposals with these files and prints every difference. A change is accepted on purpose, with `python3 -I scripts/drift.py --accept ID [--confirm NAME]`. Accepting merges the proposal into the sheet and never throws away what a person added (a row's `how`, `read_as`, `approx` and `basis`, and the rows entered by hand); `confirmed` is cleared when a row changes.

## Files

- `sheets/pdf-NN.json` – page NN of `docs/files/EXPLODED_DRAWINGS.pdf`, read from the PDF's text (exact).
- `sheets/img-NAME.json` – a sheet that exists only as an image on the wiki (not in the PDF), read by OCR and checked by a person.

## Fields

| Field | Meaning |
| --- | --- |
| `id` | The file name without `.json`. |
| `title` | The sheet's title. |
| `source` | Where the rows came from. `kind` is `pdf` (with `file`, `sha256` of the PDF, and `page`) or `image` (with `file`, `sha256` of the original image, and `image_sheet` as `[n, of]` in the wiki's newer revision). |
| `images` | The drawing images that show this sheet, each with a `role`: `wiki` (as the wiki has it), `redrawn` (low resolution, replaced by a drawing of the PDF sheet), `enlarged` (low resolution, no PDF sheet, made twice the size), `lost` (the wiki's image was not archived; drawn from the PDF sheet), or `drawn` (the wiki never showed this sheet as an image; drawn from the PDF sheet so the Exploded Drawings page has it). |
| `rows` | The parts list. Each row has `item`, `qty` (a whole number), `part`, `description` (the bag or box, or `Printed Part`), and `how`. |
| `confirmed` | `null`, or `{"by", "on"}`: a person has checked the sheet against the drawing. Rows read by OCR are not used by the build until the sheet is confirmed. |
| `notes` | Free text. |

`how` says how a row got its text: `pdf-text` (exact), `ocr` (as the OCR read it), `ocr+fix` (corrected by a rule; these never change a number), `hand` (corrected by a person), or `entered` (typed by a person where the drawing has no parts list, with a `basis` saying what it rests on). A corrected row keeps `read_as`, what the tool read, and an OCR row keeps its `confidence`. `"approx": true` marks a quantity the manual gives as approximate; the page shows it as `~150`. A sheet made only of entered rows is not the tools' to propose, so `drift.py` does not report it as missing.

## Build sections

The build section a part links to is not stored here. It comes from where the manual shows the sheet's drawing (`embedded_sections` in `scripts/sections.py`), because the manual is the source of truth for which step a drawing belongs to.

## Printed parts the manual names that no drawing covers

`manual_parts.json` lists the printed parts the manual itself names in its step lists, such as `2 x Drive Supports (Printed Parts).` Each entry has the page and step that list it, the quantity, the part, where it comes from (`printed`, `printed-parts-box` or `printed-parts-bag`), and `drawing`: the id of the sheet in `sheets/` that covers the part, or `null` if no drawing does. The Bill of Materials adds the entries with no drawing to its Printed Parts table, marked `no drawing` and linked to the step that lists them; a part listed in two steps is one row that links both.

`scripts/manual_parts.py` finds these items in the built manual (`docs/*.html`) and reports what differs from this file; `--add-new` appends new ones with no drawing for a person to review. A test fails if the manual has such an item that the list lacks. It can only find items written in the manual's list format, with `(Printed Part…)` after the name; a printed part the manual never labels that way is not found.
