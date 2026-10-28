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
