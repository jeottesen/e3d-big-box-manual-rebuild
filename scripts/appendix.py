#!/usr/bin/env python3
"""Build two extra manual pages from recovered material (written to raw/recovered/ for build.py):

  Appendix_Older_Version_Content  sections that existed in older wiki versions but were later removed
                                  (slicer-profile notes and alpha slicer profiles)
  Datasheets                      links to the wiki-hosted PDF datasheets in raw/files/ that apply to the BigBox

Run after recover.py:  python3 -I scripts/appendix.py
"""
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
from recover import find_section
from targets import APPENDIX

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW

def saved_versions(page):
    """(timestamp, path) of every saved version of a page, newest first."""
    p = f'{RAW}/versions/{page}'
    out = [(f[:-5], f'{p}/{f}') for f in os.listdir(p) if f.endswith('.html')] if os.path.isdir(p) else []
    return sorted(out, reverse=True)

def newest_with_section(page, rx, must):
    """Newest saved version of page that has the section, as (timestamp, section html)."""
    for ts, path in saved_versions(page):
        found = find_section(open(path).read(), rx, must)
        if found: return ts, found[1]
    return None

parts, sources = [], []
for heading, page, rx, must, note in APPENDIX:
    hit = newest_with_section(page, rx, must)
    if not hit: print('NOT FOUND:', page, rx); continue
    ts, section_html = hit
    parts.append(f'<h2>{html.escape(heading)}</h2><p class="src">From the {page.replace("_", " ")} page, version {ts}. {note}</p>{section_html}')
    sources.append(f'{page} {ts}')
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
