"""What the pipeline knows that cannot be derived from the archive: which pages to rebuild from older
versions of their parent, which removed sections to keep in the appendix, and which PDFs apply.
Imported by fetch.py, recover.py, appendix.py and fetch_files.py (it is data, not a script)."""

# Pages the archive never saved. They were inline sections of a bigger page until Sept 2016.
# title -> (parent pages to search, regex for the section heading in the OLD parent)
TARGETS = {
    'Dual_X-Carriage': (['BigBox_Parts_Preparation'], r'dual x.carriage'),
    'Non-Titan_Idler_Arms': (['BigBox_Parts_Preparation'], r'(non.titan )?single (&|and) dual extruder filament idlers'),
    'Single_&_Dual_Direct-Drive_IR_Sensor_Bracket': (['BigBox_Parts_Preparation'], r'single (&|and) dual direct.drive ir sensor bracket'),
    'Single_Direct-Drive_Extruder': (['BigBox_Printer_Sub-assemblies'], r'single direct.drive extruder'),
    'Single_Direct-Drive_X-Carriage': (['Printer_main_assemblies:_Step_By_Step_Assembly_Process'], r'^(\(6\) )?single direct.drive x.carriage$'),
    'Dual_Direct-Drive_X-Carriage': (['Printer_main_assemblies:_Step_By_Step_Assembly_Process'], r'^(\(7\) )?dual direct.drive x.carriage$'),
    'Mesh_Levelling_the_Non-Hybrid_Dual': (['Printer_Commissioning'], r'mesh levelling the (non.hybrid )?dual'),
    'Non-Hybrid_Dual_Calibrating_Z_Offset': (['Printer_Commissioning'], r'(non.hybrid )?dual calibrating z.?offset|calibrating z.?offset dual'),
}

NOTE_LINKS = 'File and download links in this section pointed to files that the archive did not keep.'

# Sections that were removed from the wiki but are kept in the appendix page.
# (appendix heading, page, section heading regex, text the section must contain, note)
APPENDIX = [
    ('Slicer profiles (older Software page)', 'BigBox_Software', r'^BigBox Slicer Profiles$', 'Dual Experimental',
     'Describes the Simplify3D and Slic3r profiles that were once offered, including the experimental dual-extruder profile. ' + NOTE_LINKS),
    ('Simplify3D alpha profile (older First Print page)', 'Your_First_Print', r'^Simplify3D$', 'alpha release',
     'Early single-extruder profile. ' + NOTE_LINKS),
    ('Slic3r alpha profile (older First Print page)', 'Your_First_Print', r'^Slic3r$', 'alpha release',
     'Early single-extruder profile. ' + NOTE_LINKS),
    ('Hybrid Titan extruder steps (older Step By Step page)', 'Printer_main_assemblies:_Step_By_Step_Assembly_Process',
     r'^(\(21\.1\) )?Titan Extruder\.?$', 'Pinion Gear Grub Screw',
     'The Titan extruder bracket, nuts, motor and lid steps, as written in section (21.1) until June 2016, when they were replaced by a link to the Sub-assemblies page. '
     'Only the gear spacing note was kept there. The photos of these steps were never archived.'),
]

# Wiki-hosted PDF datasheets that apply to the BigBox (V6 hotend, NEMA17 motors, DC fans).
# Left out: Volcano drawings, the silicone heater mat and Super Whopper datasheets (not BigBox parts).
WANT_FILES = ['V6-175-ASSM', 'V6-175-BREAK', 'V6-175-SINK', 'V6-300-BREAK', 'V6-300-SINK-D', 'V6-BLOCK-CARTRIDGE',
              'V6-NOZZLE-ALL', 'E-MOTOR-NEMA17-ALL_PUBLIC', 'Motor-Datasheet-All', 'DC_Fans']


# Files the wiki linked to that are no longer on the wiki, and where to find them now. They are linked, not copied:
# four of the five repositories have no licence. Checked against the GitHub repositories on 2026-10-29.
from urllib.parse import quote

def gh(repo, path='', kind='blob', ref='master'):
    return f'https://github.com/{repo}' + (f'/{kind}/{ref}/{quote(path)}' if path else '')

# The original CAD assemblies the printed parts' STEP files were cut from: (file, where it can be downloaded, what it holds, licence).
# The files themselves are not stored here (see downloads/printed-parts/). They are from E3D's BigBox design files on Thingiverse (thing 1521722, by
# Bigbox3DP), which the wiki's main page links. That page says CC BY-SA 3.0 (the archived copy of 2016-12-04 links creativecommons.org/licenses/by-sa/3.0/)
# and offers STEP.zip. The maintainer downloaded it from Thingiverse and confirmed that the files named here are in it and that the licence is right (2026-11-02/03).
# tests/test_printed_parts.py fails if a source or licence is missing, so the parts are not published without them.
UNRECORDED = 'source and licence not yet recorded'
THINGIVERSE = 'https://www.thingiverse.com/thing:1521722'
CC_BY_SA = 'CC BY-SA 3.0, Bigbox3DP on Thingiverse'
STEP_SOURCES = [
    ('bigbox_v1.1.0.stp', THINGIVERSE, 'BigBox v1.1: 54 of the parts', CC_BY_SA),
    ('Hybrid_v1.1.0.stp', THINGIVERSE, 'BigBox v1.1 Hybrid: 10 of the parts', CC_BY_SA),
    ('bigbox_dual_v1.0.0.stp', THINGIVERSE, 'BigBox v1.0 Dual: 7 of the parts', CC_BY_SA),
    ('BB_FRAME_M3_NUT_TRAP.stp', THINGIVERSE, 'the frame nut trap: 1 part', CC_BY_SA),
]

# (heading, intro, [(text, url or None, note)])
DOWNLOADS = [
    ('Simplify3D profiles',
     'The Software page offered Simplify3D profiles, but the files were hosted on the wiki and are gone. The BigBox repository has profiles, and a community repository has a second set whose settings follow the material, quality and extruder you choose. The original profiles, including the experimental dual one, are under "Archived copies from the old E3D file server" below.',
     [(f'BigBox {v}.fff', gh('BigBox3D/Simplify3D', f'BigBox {v}.fff'), 'BigBox3D/Simplify3D') for v in ('Pro', 'Dual', 'Hybrid-Pro', 'Hybrid-Dual', 'Print Farm')] +
     [('BigBox-Settings: README', gh('Alex9779/BigBox-Settings', 'README.md'), 'Alex9779/BigBox-Settings; explains the profiles')] +
     [(f'BigBox {v}.fff', gh('Alex9779/BigBox-Settings', f'{d}/Simplify3D/BigBox {v}.fff'), 'Alex9779/BigBox-Settings')
      for d, v in (('Pro', 'Pro'), ('Dual', 'Dual'), ('Hybrid-Pro', 'Hybrid-Pro'), ('Hybrid-Dual', 'Hybrid-Dual'),
                   ('Hybrid-Dual', 'Hybrid-Dual Mirrored'), ('Dual Titan', 'Dual Titan'))] +
     [('BigBoxBedAssembly.stl', gh('Alex9779/BigBox-Settings', 'BigBoxBedAssembly.stl'), 'a model of the BigBox bed for Simplify3D; Alex9779/BigBox-Settings')]),
    ('Firmware',
     'Precompiled Marlin builds for each BigBox version, from the BigBox firmware repository. The mesh bed levelling builds need the IR sensor moved to the heated bed.',
     [('marlin_direct_dual.hex', gh('BigBox3D/Firmware', 'marlin_direct_dual.hex'), 'BigBox v1.0 Dual (Direct Dual), Kickstarter'),
      ('marlin_direct_pro.hex', gh('BigBox3D/Firmware', 'marlin_direct_pro.hex'), 'BigBox v1.0 Pro (Direct Pro), Kickstarter'),
      ('marlin_hybrid_dual.hex', gh('BigBox3D/Firmware', 'marlin_hybrid_dual.hex'), 'BigBox v1.1 Dual Hybrid (Titan and non-Titan), auto bed levelling'),
      ('marlin_hybrid_pro.hex', gh('BigBox3D/Firmware', 'marlin_hybrid_pro.hex'), 'BigBox v1.1 Pro Hybrid (Titan and non-Titan), auto bed levelling'),
      ('marlin_hybrid_dual_mesh.hex', gh('BigBox3D/Firmware', 'marlin_hybrid_dual_mesh.hex'), 'BigBox v1.1 Dual Hybrid, mesh bed levelling'),
      ('marlin_hybrid_pro_mesh.hex', gh('BigBox3D/Firmware', 'marlin_hybrid_pro_mesh.hex'), 'BigBox v1.1 Pro Hybrid, mesh bed levelling'),
      ('Firmware README', gh('BigBox3D/Firmware', 'README.md'), 'which file is for which version, and how to flash it'),
      ('BigBox Marlin source', gh('BigBox3D/Marlin'), 'one branch per BigBox version (GPL v3)')]),
    ('SD card files',
     'The files that came on the SD card in the kit.',
     [('3DBenchy.stl', gh('BigBox3D/SD-Card', '3DBenchy.stl'), 'BigBox3D/SD-Card'),
      ('Pro/3DBenchy.gcode', gh('BigBox3D/SD-Card', 'Pro/3DBenchy.gcode'), 'sliced for the Pro'),
      ('Dual/3DBenchy.gcode', gh('BigBox3D/SD-Card', 'Dual/3DBenchy.gcode'), 'sliced for the Dual'),
      ('Pro/calibration/extruder_0.gcode', gh('BigBox3D/SD-Card', 'Pro/calibration/extruder_0.gcode'), ''),
      ('Dual/calibration/extruder_0.gcode', gh('BigBox3D/SD-Card', 'Dual/calibration/extruder_0.gcode'), ''),
      ('Dual/calibration/extruder_1.gcode', gh('BigBox3D/SD-Card', 'Dual/calibration/extruder_1.gcode'), '')]),
    ('Printed parts (STEP files)',
     'One STEP file for each printed part, named after its Bill of Materials row and linked from it. Each is one solid in its own frame, moved so its bounding box sits on the origin and never rotated, so a slicer can open it directly. '
     'They were cut from the original BigBox CAD assemblies listed below, which are not stored here. '
     'The designs are by Bigbox3DP (E3D) on Thingiverse, thing 1521722. '
     'The right-hand SPOOL-HOLDER OUTER (R) was made by mirroring (L), which the originals hold once.',
     [('parts.csv', '../downloads/printed-parts/parts.csv', 'one row per file: Bill of Materials name, quantity, manual section, source assembly and part, size, volume and SHA-256'),
      ('SHA256SUMS', '../downloads/printed-parts/SHA256SUMS', 'check the files with sha256sum -c SHA256SUMS in downloads/printed-parts')] +
     [(f'{name} (source assembly)', url, note) for name, url, note, _licence in STEP_SOURCES] +
     [('Thingiverse page, archived copy of 2016-12-04', 'https://web.archive.org/web/20161204111516/http://www.thingiverse.com/thing:1521722', 'the page the files are from; it offers STEP.zip')]),
    ('Archived copies from the old E3D file server',
     'The wiki\'s own file server (files.e3d-online.com) is gone, but the Wayback Machine kept these. The links go to the archived copies.',
     [
      ('bigbox_pro.fff', 'https://web.archive.org/web/20160831005447/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_pro.fff', 'Simplify3D profile for the Pro'),
      ('bigbox_dual.fff', 'https://web.archive.org/web/20160531182702/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_dual.fff', 'Simplify3D profile for the Dual'),
      ('bigbox_dual_experimental.fff', 'https://web.archive.org/web/20160831005324/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_dual_experimental.fff', 'the experimental dual-extruder Simplify3D profile described in the appendix'),
      ('bigbox_hybrid.fff', 'https://web.archive.org/web/20160831005610/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_hybrid.fff', 'Simplify3D profile for the Hybrid'),
      ('bigbox_1.1.fff', 'https://web.archive.org/web/20160831005209/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_1.1.fff', 'Simplify3D profile for BigBox 1.1'),
      ('BigBox_Slic3r_config_bundle.ini', 'https://web.archive.org/web/20160422181925/http://files.e3d-online.com/BigBox/Slicer%20Configs/Slic3r/BigBox_Slic3r_config_bundle.ini', 'Slic3r configuration bundle'),
      ('BigBox_Cura_0.10.ini', 'https://web.archive.org/web/20160519153237/http://files.e3d-online.com/BigBox/Slicer%20Configs/Cura/BigBox_Cura_0.10.ini', 'Cura configuration, 0.10 layer height'),
      ('BigBox_Cura_0.20.ini', 'https://web.archive.org/web/20160519153242/http://files.e3d-online.com/BigBox/Slicer%20Configs/Cura/BigBox_Cura_0.20.ini', 'Cura configuration, 0.20 layer height'),
      ('BigBox_Cura_0.25.ini', 'https://web.archive.org/web/20160519152959/http://files.e3d-online.com/BigBox/Slicer%20Configs/Cura/BigBox_Cura_0.25.ini', 'Cura configuration, 0.25 layer height'),
      ('EXPLODED_DRAWINGS.pdf', 'files/EXPLODED_DRAWINGS.pdf', 'BigBox exploded drawings; this repository holds a copy of the file the archive saved on 2016-01-09'),
      ('Titan_Assembly_Supplementary.pdf', 'https://web.archive.org/web/20160527143731/http://files.e3d-online.com/Titan/Titan_Assembly_Supplementary.pdf', 'Titan assembly supplementary instructions (the wiki linked it with spaces in the name)'),
      ('ASM_EX_THUMB_SCREW.stp', 'https://web.archive.org/web/20170910104341/http://files.e3d-online.com/Titan/ASM_EX_THUMB_SCREW.stp', 'Titan thumb screw CAD model'),
      ('ASM_EX_AERO_285.stl', 'https://web.archive.org/web/20171114074932/http://files.e3d-online.com/Titan/ASM_EX_AERO_285.stl', 'Titan Aero 2.85 mm model'),
     ]),
    ('Still missing',
     'Not in the repositories above, and not kept by the Wayback Machine.',
     [('BigBox_Fixings.pdf', None, 'the fixings list linked from the Bill of Materials (it was on Dropbox; the archive has only a capture of the error page)'),
      ('BRACKET_PRINTED.pdf', None, 'the Titan mounting bracket engineering drawing linked from Titan Assembly (it was on files.e3d-online.com)'),
      ('BigBoxSingle-alpha-settings.fff', None, 'the early alpha Simplify3D profile (it was on Dropbox)'),
      ('ASM_EX_THUMB_SCREW.stl', None, 'the Titan thumb screw model linked from Titan Assembly; the archive has the .stp version above but not this file')]),
]

# Drawing images the wiki used but the archive did not keep, whose sheet is in the exploded drawings PDF: file name -> sheet.
# scripts/render_sheets.py draws these sheets from the PDF and the build uses them in place of the missing image.
# Checked by eye against the page each one appears on. (X-CARRIAGE_DUAL, PRINT-HEAD_(SINGLE) and PRINT-HEAD_(DUAL) have no
# sheet in the PDF: sheet 8 is blank.)
SHEET_IMAGES = {
    'EXTRUDER_IDLER.jpg': 4,
    'X-CARRIAGE_SINGLE.jpg': 7,
    'PRINT_FAN_DUCT.jpg': 12,
    'IR_SENSOR_ASSEMBLY.jpg': 13,
}

# Matches decided by eye, for images the matcher cannot confirm on its own: image -> PDF sheet. They are treated as confirmed, and a low
# resolution one is still redrawn from that sheet. (This maps an image to the sheet it shows, not to a step of the manual: build sections
# come from where the manual embeds the drawing.)
MATCH_OVERRIDES = {
    'EXTRUDER_SINGLE.jpg': 14,   # the wiki's 800 px image is the same drawing as PDF sheet 14, but too small for the OCR to agree with the PDF's rows
}

# OCR misreads on the image-only drawing sheets, checked against the drawing by eye: what the OCR read -> what the drawing says.
# (EXTRUDER_DUAL.jpg is only 800 px wide.) scripts/drawing_images.py applies these and treats the rows as checked.
OCR_FIXES = {
    'EXTRUDER BOOY(DUAL)': 'EXTRUDER BODY (DUAL)',
    'Motox Box-0.9Deg': 'Motor Box - 0.9Deg',
    'E-AXIS CABLE BRACKET(DUAL)(R)': 'E-AXIS CABLE BRACKET (DUAL)(R)',
    'E-AXIS CABLE BRACKET(DUAL)IL)': 'E-AXIS CABLE BRACKET (DUAL)(L)',
    'M3x2S.Socket CapScrew': 'M3 x 25 Socket Cap Screw',
    'MAWasher': 'M4 Washer',
    'HOBDGOBLIN-SOOIO': 'HOBBGOBLIN-500ID',
    'M3x 3Skt Grb Screw Knurled Point': 'M3 x 3 Skt Grub Screw Knurled Point',
    'M2Hex Nut': 'M3 Hex Nut',   # the hybrid drawings themselves print 'M2 Hex Nut' (E3D's typo): Fixings Bag 3 holds the M3 hex nut and no M2 screws or nuts are listed anywhere (confirmed by the maintainer)
    '30x30x30 DC Fan (24v)': '30x30x10 DC Fan (24v)',   # sheet 26 prints 30x30x30 (E3D's typo or a misprint): there is no 30x30x30 fan in the build, it is the 30x30x10 hotend fan (confirmed by the maintainer)
}
# (lookup ignores spaces and case, so 'M2 HexNut' and 'M2Hex Nut' both match)

# Printed parts the manual names in its step lists ("2 x Spool Inner Brackets (Printed Parts)") that a drawing also shows, matched to the row of
# the drawing that is the same part: the manual's name -> (sheet id in data/sheets, the drawing's name for it). The Bill of Materials shows the
# drawing's name (one name per part), with the quantity the manual's step uses: a drawing shows one part that applies to several places, such as
# one corner of the four of the Z bed. A printed part the manual names that is not here has no drawing and is added from the manual.
# Checked against the drawings by the maintainer: the right cable bracket, the belt tensioner, the dock and the three Z-bed parts are the same parts. The manual's
# Spool Inner Brackets are NOT the SPOOL-HOLDER INNER drawing (they look different), so they have no drawing.
# Names for parts that have no drawing, where the manual's name is not the one the part goes by (the printed parts package names it so).
# 'Bearing Clamps' (dual carriage) is the larger version of the X-AXIS CARRIAGE BEARING CLAMP, checked by the maintainer.
NO_DRAWING_NAMES = {'Bearing Clamps': 'X-AXIS CARRIAGE BEARING CLAMP DUAL',
                    'Main Block': 'Non-Titan Direct-Drive Bowden Main Block'}   # the maintainer's name for it

# Parts of the Printed Parts Box or Bag that are not 3D printed. They are not in the printed parts table but in the General table, which is the General
# sheet of E3D's spreadsheet (data/bom.ods), under the sheet's name for them: manual or drawing name -> the sheet's Component. The cork parts are one
# item on the sheet. 'Black Spring' is the filament idler spring (it is fitted in the Non-Titan Direct-Drive Bowden System).
GENERAL_ROWS = {'Y-AXIS BACK (L) CORK (Self Adhesive)': 'Laser Cut Cork Dampener Parts',
                'Y-AXIS FRONT CORK (L & R) (Self Adhesive)': 'Laser Cut Cork Dampener Parts',
                'Y-MOTOR MOUNT CORK (Self Adhesive)': 'Laser Cut Cork Dampener Parts',
                'Cork Pads': 'Laser Cut Cork Dampener Parts',
                'Embedded Bowden Coupler': 'Embedded Bowden Coupling for Plastic',
                'Black Spring': 'Filament-Idler Spring',
                'Hobgoblin': 'E3D HobGoblin (5mm) (M3 x 4 Grub)'}
# Where the manual puts the parts of the General sheet (data/bom.ods), by the sheet's Component. Each entry is evidence in the manual itself, and the build
# fails if one stops resolving: ('part', NAME) a row of the exploded drawings with that part name (the steps that show those drawings), ('item', NAME) a
# list item in a step ("1 x Rumba (Electronics Box)."), ('heading', PAGE, TEXT) a step whose heading is that part. The build section is every step found.
# Checked by the maintainer. The parts of GENERAL_ROWS above are added to their rows too. A component not here has no step the manual ties it to.
_SUB, _MAIN, _COM = 'BigBox_Printer_Sub-assemblies', 'Printer_main_assemblies_Step_By_Step_Assembly_Process', 'Printer_Commissioning'
GENERAL_SOURCES = {
    'PT100 Single amp cable': [('heading', _SUB, '(12.5) PT100 Amplifier(s)')],
    'PT100 Double amp cable': [('heading', _SUB, '(12.5) PT100 Amplifier(s)')],
    'PT100 Amp': [('heading', _SUB, '(12.5) PT100 Amplifier(s)')],
    'PT100 (1700mm Cable)': [('part', 'PT100'), ('heading', _SUB, '(12.7) PT100 Wiring')],
    'PSU to Rumba': [('heading', _SUB, '(12.6) PSU - Rumba Wiring')],
    'IEC to PSU (Mains to PSU (300mm))': [('heading', _SUB, '(12.6) PSU - Rumba Wiring')],
    'Bed Wiring Loom': [('item', 'Heated Bed Wiring'), ('heading', _MAIN, '(32.3) Connecting the Heated Bed')],
    'IR Endstop Cable': [('item', '3-Wire IR Sensor Cable')],
    'IEC Socket with Fuse': [('heading', _MAIN, '(17.6) A/C IEC Socket')],
    'Rumba': [('heading', _SUB, '(12.4) Rumba')],
    'A4988': [('heading', _MAIN, '(27) Tuning The Stepper Drivers')],
    'PSU': [('heading', _SUB, '(12.3) Power Supply Unit (PSU)')],
    'IR Sensor': [('part', 'IR-SENSOR')],
    'EndStops MicroSwitch (with Cable)': [('item', 'Endstop'), ('heading', _MAIN, '(29) Y-Axis Frame Endstop')],
    'Heated Bed': [('heading', _MAIN, '(32.3) Connecting the Heated Bed')],
    'LCD': [('heading', _SUB, '(13.3) The LCD Enclosure')],
    'Z-Motor Cable (300mm)': [('heading', _MAIN, '(17.4) Z-Axis Motors')],
    'E-Motor Cable (1500mm)': [('heading', _MAIN, '(21.8) Extruder Motor Cable')],
    'Y-Motor Cable (1000mm)': [('item', '1000mm Y-Axis Motor Cable')],
    'Panel Mount USB Extension': [('item', 'USB Panel Mount Cable')],
    'Nitrile 70 O-Rings 12mm ID 17 OD': [('item', 'O-Ring')],
    'E3D HobGoblin (5mm) (M3 x 4 Grub)': [('part', 'HOBBGOBLIN-500ID')],
    'E3D V6 Lite (Direct, 24V, PT100 Block, No Electronics)': [('heading', _MAIN, '(21.3) Assembly of the E3D V6 HotEnds.')],
    'E3D V6 (Direct, 24V, PT100 Block, No Electronics)': [('heading', _MAIN, '(21.3) Assembly of the E3D V6 HotEnds.')],
    'Heater Cartridge': [('part', 'HEATER-CARTRIDGE-24V-30W')],
    'Embedded Bowden Coupling for Plastic': [('part', 'Bowden Coupling')],
    '4mm x 3mm x 1000mm PTFE Filament Guide': [('item', '1000mm 4mm OD - 3mm ID Thin-Walled PTFE Tube')],
    '60x60x10 24v (300mm lead w/ 4mm fork ferrule)': [('item', '60x60x10 Exhaust Fan')],
    '50x50x10 24v (250mm lead w/ 0.1" connector)': [('part', 'FAN-50-50-10')],
    '40x40x20 Blower 24v (1700mm lead w/ 0.1" connector)': [('part', 'FAN-SNAIL-BLOWER'), ('item', '40x40x20 Blower Fan')],
    'BigBox M3 Nut Traps': [('item', 'Nut Traps')],
    'Laser Cut Acrylic / Plywood Frame': [('heading', _SUB, '(13.2) Main Frame')],
    'Filament-Idler Spring': [('part', 'Extruder Spring')],
    'Viton A Rubber Strip (1.5 x 12) 40mm': [('item', 'Rubber Stip')],
    'V6 Direct PTFE tubing (2mm x 4mm)': [('item', '2mm ID PTFE Tubing')],
    'Spring (spool holder)': [('part', 'Spool-Holder Spring')],
    'Glass Bed': [('heading', _COM, '(2.2) Glass')],
    'Drag Chain 400mm': [('item', 'Drag Chain')],
    'Glass Bed Clips': [('item', 'Bed Clips')],
    '604-ZZ (4x12x4)': [('part', 'BEARING-604ZZ')],
    'F604 (4x12x4 Flange-13.5)': [('part', 'BEARING-F604ZZ')],
    '634ZZ (4x16x5)': [('part', 'BEARING-634ZZ')],
    '688-ZZ (8x16x5)': [('part', 'BEARING-688ZZ')],
    'LM8LUU (8x45)': [('part', 'BEARING-LM8LUU')],
    '66 Tooth (132mm) GT2 Loop Belt': [('part', 'GT2-BELT-CLOSED-66T')],
    'GT2 6mm Belt (3000mm)': [('item', 'GT2 Belt')],
    'GT2 16T (5mm)': [('part', 'GT2-16T-5ID')],
    'GT2 20T (5mm)': [('part', 'GT2-20T-5ID')],
    'GT2 20T (8mm)': [('part', 'GT2-20T-8ID')],
    'GT2 36T (8mm)': [('part', 'GT2-36T-8ID')],
    '5mm – 8mm Couplers': [('item', '5mm - 8mm Aluminium Couplers')],
    'TR8 Leadscrew (347mm)': [('heading', _COM, '(1.4) Leadscrews')],
    'SiS. 532mm (Y)': [('part', 'ROD-SS-8-532')],
    'GHSiS 484mm (X)': [('part', 'ROD-G.H.SS-8-484')],
    'GHSiS 384mm (Y)': [('part', 'ROD-G.H.SS-8-384')],
    'GHSiS 364mm (Z)': [('part', 'ROD-G.H.SS-8-364')],
    'Bed Thermistor Semitec': [('heading', _MAIN, '(25.1) Single Extruder')],
    'X-Motor Cable (1500mm)': [('heading', _MAIN, '(25.1) Single Extruder')],
    'USB A-Mini cable (~500mm)': [('heading', _SUB, '(12.8) OctoPrint Upgrades')],
    'Short uUSB cable': [('heading', _SUB, '(12.8) OctoPrint Upgrades')],
    'Rumba to DCDC Power In (300mm lead. 0.1” - Tinned)': [('heading', _SUB, '(12.8) OctoPrint Upgrades')],
    'Raspberry Pi 2 + 8gb': [('heading', _SUB, '(12.8) OctoPrint Upgrades')],
    '5v DC DC Converter': [('heading', _SUB, '(12.8) OctoPrint Upgrades')],
    'Link': [('heading', 'BigBox_Parts_Preparation', '(19) IEC Socket')],
    '30x30x10 24v (1700mm lead w/ 0.1" connector)': [('part', '30x30x10 DC Fan (24v)'), ('heading', _MAIN, '(21.3) Assembly of the E3D V6 HotEnds.')],   # sheet 26 prints it 30x30x30 (corrected in data/sheets/pdf-26.json)
    '40nm NEMA 17 (200 Steps) (Wantai 42BYGHW609L20P1-X2)': [('heading', _MAIN, '(17.4) Z-Axis Motors')],
    'TR8 Nut (4 x M3 Mounting Holes)': [('heading', _SUB, '(10) Z-Axis Bed Assembly'), ('heading', _COM, '(1.4) Leadscrews')],
    'SiS 325mm (S)': [('heading', _MAIN, '(30) Spool Carrier')],
    'Viton A Rubber Strip (1.5 x 12) 77mm': [('heading', _MAIN, '(31.2) Dual Extruder Dock')],
    'Panel Mount RJ45 Socket (600mm)': [('item', 'RJ45 Panel Mount Cable')],
    'Camera & 750mm FFC Cable': [('item', '750mm FFC'), ('item', 'Raspberry Pi Camera Module')],
    '46nm NEMA 17 (400 Steps) (Wantai 42BYGHM809L20P4.5-17-X2)': [('part', 'NEMA17-400')],
}
MANUAL_PART_NAMES = {
    'Right Cable Bracket': ('img-EXTRUDER_DUAL', 'E-AXIS CABLE BRACKET (DUAL)(R)'),
    'Belt Tensioner': ('pdf-22', 'X-AXIS BELT-TENSIONER'),
    'Dock': ('img-DOCK-BRACKET', 'DOCK-BRACKET'),
    'Z-Axis Top Bottoms': ('img-Z-AXIS_TOP_BRACKETS', 'Z-AXIS TOP BOTTOM'),   # the Z bed has four corners: the drawing shows one, the manual uses 4
    'Top Tops': ('img-Z-AXIS_TOP_BRACKETS', 'Z-AXIS TOP TOP'),
    'Caps': ('img-Z-AXIS_TOP_BRACKETS', 'Z-AXIS TOP CAP'),
}
