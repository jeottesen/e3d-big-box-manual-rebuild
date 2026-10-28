#!/usr/bin/env python3
"""Build two extra manual pages from recovered material (written to raw/recovered/ for build.py):

  Appendix_Older_Version_Content  sections that existed in older wiki versions but were later removed
                                  (slicer-profile notes and alpha slicer profiles)
  Datasheets                      links to the wiki-hosted PDF datasheets in raw/files/ that apply to the BigBox

Run after recover.py:  python3 -I scripts/appendix.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
src = open(f'{ROOT}/scripts/recover.py').read().split("if __name__")[0]
ns = {'__file__': f'{ROOT}/scripts/recover.py'}; exec(compile(src, 'recover', 'exec'), ns)
sections = ns['sections']

def old_version(page, ts):
    for d in ('versions', 'versions_removed/unchanged', 'versions_removed/errors'):
        f = f'{RAW}/{d}/{page}/{ts}.html'
        if os.path.exists(f): return open(f).read()
    raise FileNotFoundError(f'{page} {ts}')

def section(page, ts, rx):
    return next(((t, b) for t, _, b, _ in sections(old_version(page, ts), rx)), None)

parts, sources = [], []
def add(heading, page, ts, rx, note):
    s = section(page, ts, rx)
    if not s: print('NOT FOUND:', page, ts, rx); return
    parts.append(f'<h2>{html.escape(heading)}</h2><p class="src">From the {page.replace("_", " ")} page, version {ts}. {note}</p>{s[1]}')
    sources.append(f'{page} {ts}')

NOTE_LINKS = 'File and download links in this section pointed to files that the archive did not keep.'
add('Slicer profiles (older Software page)', 'BigBox_Software', '20160601234712', r'^BigBox Slicer Profiles$',
    'Describes the Simplify3D and Slic3r profiles that were once offered, including the experimental dual-extruder profile. ' + NOTE_LINKS)
add('Simplify3D alpha profile (older First Print page)', 'Your_First_Print', '20151230221140', r'^Simplify3D$', 'Early single-extruder profile. ' + NOTE_LINKS)
add('Slic3r alpha profile (older First Print page)', 'Your_First_Print', '20151230221140', r'^Slic3r$', 'Early single-extruder profile. ' + NOTE_LINKS)
os.makedirs(f'{RAW}/recovered', exist_ok=True)
index_path = f'{RAW}/recovered/index.json'
index = json.load(open(index_path)) if os.path.exists(index_path) else {}

open(f'{RAW}/recovered/Appendix_Older_Version_Content.html', 'w').write(
    '<div id="mw-content-text"><p>Content that appeared in older versions of this manual and was later removed, kept here for completeness. '
    'It is not part of the current build instructions.</p>' + ''.join(parts) + '</div>')
index['Appendix_Older_Version_Content'] = {'parent': 'older versions of several pages', 'version': ', '.join(sources), 'heading': 'appendix', 'lines': len(parts)}

DESC = {
    'V6-175-ASSM': 'E3D V6 1.75 mm hotend, assembly drawing', 'V6-175-BREAK': 'E3D V6 1.75 mm heatbreak, drawing',
    'V6-175-SINK': 'E3D V6 1.75 mm heatsink, drawing', 'V6-300-BREAK': 'E3D V6 3.00 mm heatbreak, drawing',
    'V6-300-SINK-D': 'E3D V6 3.00 mm heatsink, drawing', 'V6-BLOCK-CARTRIDGE': 'E3D V6 heater block and heater cartridge, drawing',
    'V6-NOZZLE-ALL': 'E3D V6 nozzles, drawing', 'E-MOTOR-NEMA17-ALL_PUBLIC': 'NEMA17 stepper motor datasheet',
    'Motor-Datasheet-All': 'Stepper motor datasheets (combined)', 'DC_Fans': 'DC fan datasheet'}
files = json.load(open(f'{RAW}/files.json'))
rows = ''.join(f'<li><a href="files/{n}.pdf">{n}.pdf</a> — {DESC.get(n, "datasheet")} <span class="src">(archived {v["snapshot"][:8]}, {v["bytes"]//1024} KB; description inferred from the file name)</span></li>'
               for n, v in files.items() if v)
open(f'{RAW}/recovered/Datasheets.html', 'w').write(f'<div id="mw-content-text"><p>PDF datasheets and drawings that were hosted on the wiki and apply to BigBox parts '
                                                   f'(V6 hotend, stepper motors, fans). Volcano and heater-mat datasheets were left out as they are not BigBox parts.</p><ul>{rows}</ul></div>')
index['Datasheets'] = {'parent': 'wiki-hosted files', 'version': 'various', 'heading': 'datasheets', 'lines': len(files)}
json.dump(index, open(index_path, 'w'), indent=1)
print('wrote appendix with', len(parts), 'sections;', len([v for v in files.values() if v]), 'datasheets')
