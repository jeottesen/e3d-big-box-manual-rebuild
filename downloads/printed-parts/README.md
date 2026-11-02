# Printed parts (STEP files)

One STEP file for each printed part of the BigBox, named after its row in the manual's Bill of Materials. The Bill of Materials page links each file.

## Licence

These files are licensed under [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (CC BY-SA 3.0). That is not the licence of the rest of this repository (CC BY 3.0, see `NOTICE.md`): CC BY-SA requires adaptations to carry the same licence.

## Attribution

The parts are adapted from the BigBox design files by Bigbox3DP (E3D), published on Thingiverse as [E3D's BigBox 3D Printer](https://www.thingiverse.com/thing:1521722) (thing 1521722) under CC BY-SA 3.0. An [archived copy of the page](https://web.archive.org/web/20161204111516/http://www.thingiverse.com/thing:1521722), captured 2016-12-04, states that licence.

## Changes made

- Each part was cut out of the original CAD assembly it came from (`source_file` and `source_part` in `parts.csv`) and saved as its own file.
- Each part was moved so its bounding box sits on the origin. It was not rotated.
- SPOOL-HOLDER OUTER (R) was made by mirroring SPOOL-HOLDER OUTER (L), which the original files hold once.
- Each file was re-imported after writing and checked to be one solid with the expected volume.
- Names follow the manual's Bill of Materials. Characters other than letters, digits and `-` are replaced by `-`. Where one name covers two different shapes, the file name ends in `__dual` or `__regular`.

## Files

- `parts/` has the STEP files.
- `parts.csv` has one row per file: the Bill of Materials name, quantity, manual section, source file and part, size, volume and SHA-256.
- `SHA256SUMS` checks the files: `sha256sum -c SHA256SUMS`.
