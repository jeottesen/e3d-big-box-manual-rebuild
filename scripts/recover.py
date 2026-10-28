#!/usr/bin/env python3
"""Recover wiki pages that are not archived by cutting their text out of older versions of parent pages.

Before ~Sept 2016 several pages (Dual X-Carriage, Non-Titan idler arms, IR sensor bracket, ...) were
inline sections of bigger pages. For each target below, scan every saved version of the candidate parent
pages in raw/versions for a heading that matches, take that section (up to the next heading of the same
or higher level), and keep the fullest one. Output: raw/recovered/<Title>.html + raw/recovered/index.json.
Run:  python3 -I scripts/recover.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
VER, OUT = f'{RAW}/versions', f'{RAW}/recovered'
os.makedirs(OUT, exist_ok=True)

# missing page -> (parent pages to search, heading regex)
TARGETS = {
    'Dual_X-Carriage': (['BigBox_Parts_Preparation'], r'dual x.carriage'),
    'Non-Titan_Idler_Arms': (['BigBox_Parts_Preparation'], r'(non.titan )?single (&|and) dual extruder filament idlers'),
    'Single_&_Dual_Direct-Drive_IR_Sensor_Bracket': (['BigBox_Parts_Preparation'], r'single (&|and) dual direct.drive ir sensor bracket'),
    'Single_Direct-Drive_Extruder': (['BigBox_Printer_Sub-assemblies'], r'single direct.drive extruder'),
    'Mesh_Levelling_the_Non-Hybrid_Dual': (['Printer_Commissioning'], r'mesh levelling the (non.hybrid )?dual'),
    'Non-Hybrid_Dual_Calibrating_Z_Offset': (['Printer_Commissioning'], r'(non.hybrid )?dual calibrating z.?offset|calibrating z.?offset dual'),
}

HEAD = re.compile(r'<h([2-6])\b[^>]*>(.*?)</h\1>', re.S)

def content(h):
    m = re.search(r'id="mw-content-text"[^>]*>(.*?)<div class="printfooter"', h, re.S) or re.search(r'id="mw-content-text"[^>]*>(.*)', h, re.S)
    return m.group(1) if m else h

def htext(s): return html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<span class="mw-editsection">.*?</span></span>', '', s, flags=re.S))).strip()

def sections(h, rx):
    c = content(h); hs = list(HEAD.finditer(c))
    for i, m in enumerate(hs):
        title = htext(m.group(2))
        if not re.search(rx, title, re.I): continue
        lvl = int(m.group(1)); end = len(c)
        for n in hs[i + 1:]:
            if int(n.group(1)) <= lvl: end = n.start(); break
        body = c[m.end():end]
        lines = [l for l in htext(re.sub(r'</(p|li|div|tr)>|<br\s*/?>', '\n', body)).splitlines() if l.strip()]
        yield title, m.group(0), body, len(lines)

def main():
    index = {}
    for target, (parents, rx) in TARGETS.items():
        best = None
        for parent in parents:
            d = f'{VER}/{parent}'
            if not os.path.isdir(d): continue
            for f in sorted(os.listdir(d)):
                if not f.endswith('.html'): continue
                for title, head, body, n in sections(open(f'{d}/{f}').read(), rx):
                    if best is None or n > best['lines'] or (n == best['lines'] and f[:-5] > best['version']):
                        best = dict(parent=parent, version=f[:-5], heading=title, lines=n, head=head, body=body)
        if not best or best['lines'] < 4:
            print(f'{target}: NOT RECOVERABLE (best {best["lines"] if best else 0} lines)'); index[target] = None; continue
        note = f'<p class="src">Recovered from an older version of {best["parent"].replace("_"," ")} ({best["version"]}), section "{html.escape(best["heading"])}" — the separate wiki page is not in the archive.</p>'
        open(f'{OUT}/{target}.html', 'w').write(f'<div id="mw-content-text">{note}{best["body"]}</div>')
        index[target] = {k: best[k] for k in ('parent', 'version', 'heading', 'lines')}
        print(f'{target}: {best["lines"]} lines from {best["parent"]} {best["version"]} "{best["heading"]}"')
    json.dump(index, open(f'{OUT}/index.json', 'w'), indent=1)

if __name__ == '__main__': main()
