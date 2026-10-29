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
     'The Software page offered Simplify3D profiles, but the files were hosted on the wiki and are gone. The BigBox repository has profiles, and a community repository has a second set whose settings follow the material, quality and extruder you choose.',
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
    ('Still missing',
     'Not in the repositories above, and not kept by the Wayback Machine.',
     [('BigBox_Fixings.pdf', None, 'the fixings list linked from the Bill of Materials (it was on Dropbox)'),
      ('BRACKET_PRINTED.pdf', None, 'the Titan mounting bracket engineering drawing linked from Titan Assembly (it was on files.e3d-online.com)'),
      ('BigBox_Slic3r_config_bundle.ini and BigBoxSingle-alpha-settings.fff', None, 'the early alpha Slic3r and Simplify3D profiles (they were on Dropbox); no Slic3r profile was found in the repositories'),
      ('Dual Experimental.fff', None, 'the experimental dual-extruder profile described in the appendix')]),
]
