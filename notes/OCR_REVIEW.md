# OCR review

These are the drawing sheets that exist only as images on the wiki, read by OCR in scripts/drawing_images.py. This page lists what to check by eye. Totals: 30 images, 198 rows, 4 rows marked for review, 17 rows corrected automatically (20 fields).

## Rows to check

| Image | Sheet | Item | Qty | Part (as read) | Description (as read) | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| EXTRUDER_DUAL.jpg | 16 / 36 | - | 1 | EXTRUDER BOOY(DUAL) | Printed Part | 0.84 |
| EXTRUDER_HYBRID_TITAN_DIRECT.jpg | 18 / 41 | 1 | 2 | M2Hex Nut | Fixings Bag 3 | 0.74 |
| EXTRUDER_SINGLE.jpg | 15 / 36 | 8 | 1 | MAWasher | Fixings Bag 13 | 0.81 |
| EXTRUDER_SINGLE.jpg | 15 / 36 | 11 | 1 | EXTRUDER IDLER | Part Aevemby | 0.8 |

## Sheet-level problems

- EXTRUDER_DUAL.jpg: 1 of 14 rows the OCR was unsure of and could not match to a known name: no item no. EXTRUDER BOOY(DUAL)
- EXTRUDER_HYBRID_NON-TITAN_DIRECT.jpg: item numbers ['1', '2', '3', '4', '5', '6', '7', '8', '6', '10', '11', '12', '13', '14', '15', '16'] repeat; one was probably misread
- EXTRUDER_HYBRID_TITAN_DIRECT.jpg: 1 of 4 rows the OCR was unsure of and could not match to a known name: 1 M2Hex Nut
- EXTRUDER_SINGLE.jpg: 2 of 13 rows the OCR was unsure of and could not match to a known name: 8 MAWasher; 11 EXTRUDER IDLER
- FRAME-LUG_DRAWING.jpg: no PARTS LIST heading found

## Corrected automatically

These were fixed against the exact names in the PDF and are listed so they can be spot-checked.

| Image | Item | Field | OCR read | Now reads |
| --- | --- | --- | --- | --- |
| EXTRUDER_DUAL.jpg | 7 | part | M3x2S.Socket CapScrew | M3 x 25 Socket Cap Screw |
| EXTRUDER_DUAL.jpg | 7 | description | Fxings Bog7 | Fixings Bag 7 |
| EXTRUDER_DUAL.jpg | 8 | description | Foings Bog8 | Fixings Bag 8 |
| EXTRUDER_DUAL.jpg | 9 | description | Fiings Bag17 | Fixings Bag 7 |
| EXTRUDER_DUAL.jpg | 12 | description | Fxinss Bag 12 | Fixings Bag 12 |
| EXTRUDER_DUAL.jpg | 14 | part | M3x 3Skt Grb Screw Knurled Point | M3 x 3 Skt Grub Screw Knurled Point |
| EXTRUDER_DUAL.jpg | 14 | description | Fxings Bog 17 | Fixings Bag 17 |
| EXTRUDER_SINGLE.jpg | - | description | Foxings Bog 17 | Fixings Bag 17 |
| EXTRUDER_SINGLE.jpg | 1 | part | EXT RUOERE OD Y(SINGLE) | EXTRUDER BODY (SINGLE) |
| EXTRUDER_SINGLE.jpg | 3 | part | EXT RUOER CABLE BRACKET | EXTRUDER CABLE BRACKET |
| EXTRUDER_SINGLE.jpg | 4 | description | Foongs Beg 11 | Fixings Bag 11 |
| EXTRUDER_SINGLE.jpg | 6 | description | Foongs Bog8 | Fixings Bag 8 |
| EXTRUDER_SINGLE.jpg | 8 | description | Foxings Bog 13 | Fixings Bag 13 |
| EXTRUDER_SINGLE.jpg | 9 | description | Extruder Box-ElackSpring | Extruder Box - Black Spring |
| EXTRUDER_SINGLE.jpg | 11 | part | EXT RUOER IDLER | EXTRUDER IDLER |
| EXTRUDER_SINGLE.jpg | 13 | part | M3x3 Skt GrubScrewKeuriedPoint | M3 x 3 Skt Grub Screw Knurled Point |
| EXTRUDER_SINGLE.jpg | 13 | description | Fioings Bog 17 | Fixings Bag 17 |
| EXTRUDER_SINGLE.jpg | 14 | part | Boaden Couplng | Bowden Coupling |
| Y-AXIS_MOTOR.jpg | 2 | part | Y-MOTOR MOUNT CORK(SeIfAdhesive) | Y-MOTOR MOUNT CORK (Self Adhesive) |
| Z-AXIS_TOP_BRACKETS.jpg | 4 | part | ROD-G.H.SS-8-364 | ROD-G.H.SS-8-384 |

## Image sheets with no table

- FRAME-LUG_DRAWING.jpg: no parts list found
