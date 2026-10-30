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

# Which build section each sheet of the exploded drawings belongs to: sheet -> (page, "(n)" prefix of the section heading).
# Only sheets whose title clearly matches a section are listed; a missing sheet gets no build link (a wrong link is worse
# than none). Sheets 8, 15 and 17 are blank in the archived PDF; 11, 18, 19, 25 and 29 have titles that do not obviously
# match a section. These need a manual look.
SHEET_SECTIONS = {
    1: ('BigBox_Parts_Preparation', '(1)'), 2: ('BigBox_Parts_Preparation', '(2)'), 3: ('BigBox_Parts_Preparation', '(3)'),
    4: ('BigBox_Parts_Preparation', '(4)'), 5: ('BigBox_Parts_Preparation', '(5)'), 6: ('BigBox_Parts_Preparation', '(6)'),
    7: ('BigBox_Parts_Preparation', '(7)'), 9: ('BigBox_Parts_Preparation', '(10)'), 10: ('BigBox_Parts_Preparation', '(11)'),
    12: ('BigBox_Parts_Preparation', '(13)'), 13: ('BigBox_Parts_Preparation', '(15)'), 27: ('BigBox_Parts_Preparation', '(14)'),
    14: ('BigBox_Printer_Sub-assemblies', '(1)'), 16: ('BigBox_Printer_Sub-assemblies', '(7)'), 28: ('BigBox_Printer_Sub-assemblies', '(8)'),
    20: ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(3)'), 21: ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(5)'),
    22: ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(6)'), 23: ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(10)'),
    24: ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(16)'),
    26: ('Single_Direct-Drive_Printhead_Assembly', '(19.3)'),
}

# The same for the sheets that exist only as images on the wiki (docs/images), keyed by file name. A sheet that matches a
# sheet of the PDF by title is read from the PDF instead (its text is exact), so it is not listed here.
IMAGE_SECTIONS = {
    'EXTRUDER_DUAL.jpg': ('BigBox_Printer_Sub-assemblies', '(2)'),
    'EXTRUDER_HYBRID_TITAN_DIRECT.jpg': ('BigBox_Printer_Sub-assemblies', '(3)'),
    'EXTRUDER_HYBRID_NON-TITAN_DIRECT.jpg': ('BigBox_Printer_Sub-assemblies', '(5)'),
    'Z-AXIS_DRAG_CHAIN.jpg': ('BigBox_Printer_Sub-assemblies', '(11)'),
    'SPOOL-HOLDER_CLAMP.jpg': ('BigBox_Parts_Preparation', '(17)'),
    'Y-AXIS_REAR_ASSEMBLY.jpg': ('Printer_main_assemblies_Step_By_Step_Assembly_Process', '(1)'),
}

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

# Matches decided by eye, for images the matcher could not confirm: image -> PDF sheet. They link to that sheet and are never redrawn.
MATCH_OVERRIDES = {
    'HEATED_BED_CORNERS.jpg': 9,   # the wiki's image is the same drawing from another angle
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
    'M2Hex Nut': 'M2 Hex Nut',   # it is an M2 nut, not the M3 one in the PDF's Fixings Bag 3 (confirmed against the drawing)
}
# (lookup ignores spaces and case, so 'M2 HexNut' and 'M2Hex Nut' both match)
