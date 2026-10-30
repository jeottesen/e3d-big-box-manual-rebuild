#!/usr/bin/env python3
"""Recover wiki pages that are not archived by cutting their text out of older versions of parent pages.

Before ~Sept 2016 several pages (Dual X-Carriage, Non-Titan idler arms, IR sensor bracket, ...) were
inline sections of bigger pages. For each target below, scan every saved version of the candidate parent
pages in raw/versions for a heading that matches, take that section (up to the next heading of the same
or higher level), and keep the fullest one. Output: raw/recovered/<Title>.html + raw/recovered/index.json.
Run:  python3 -I scripts/recover.py
"""
import html, json, os, re, urllib.parse
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')   # archive data lives outside git; override with BIGBOX_RAW
VER, OUT = f'{RAW}/versions', f'{RAW}/recovered'
os.makedirs(OUT, exist_ok=True)

from targets import TARGETS   # missing page -> (parent pages to search, heading regex)

# an archive or MediaWiki error page rather than an article
ERR = re.compile(r'Temporarily Offline|Internal Server Error|Service Unavailable|Gateway Time-?out|Bad Gateway|'
                 r'database error|MediaWiki internal error|Wayback Machine doesn.t have|Error 50\d|'
                 r'There is currently no text in this page|Hrm\. ', re.I)

def body_text(h):
    """The article's text as a list of non-empty lines (image file names kept as '[img NAME]')."""
    m = re.search(r'id="mw-content-text"[^>]*>(.*?)(?:<div class="printfooter"|<!-- NewPP)', h, re.S) or re.search(r'id="mw-content-text"[^>]*>(.*)', h, re.S)
    b = m.group(1) if m else h
    b = re.sub(r'<(script|style).*?</\1>|<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'<img[^>]*?(?:alt="([^"]*)")?[^>]*?src="[^"]*?/([^/"]+)"[^>]*>',
               lambda m: f'\n[img {urllib.parse.unquote(m.group(2))}]\n', b)
    b = re.sub(r'</(p|li|h\d|tr|div|dd|dt|pre)>|<br\s*/?>', '\n', b)
    b = html.unescape(re.sub(r'<[^>]+>', '', b))
    return [l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith('[edit')]

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

def find_section(h, rx, must=None, min_lines=1):
    """First section of page html h whose heading matches rx (and whose text contains `must`). (title, body, lines) or None."""
    for title, _head, body, n in sections(h, rx):
        if n >= min_lines and (must is None or must.lower() in htext(body).lower()): return title, body, n
    return None

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
