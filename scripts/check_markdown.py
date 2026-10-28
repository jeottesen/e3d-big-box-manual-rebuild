#!/usr/bin/env python3
"""Check the generated Markdown: every relative link and image resolves, and every #section anchor exists.

Reads BIGBOX_MD (default manual/). Exits non-zero if anything is broken.
Run:  python3 -I scripts/check_markdown.py
"""
import os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.environ.get('BIGBOX_MD', f'{ROOT}/manual')

def slugs(text):
    """GitHub heading anchors of a Markdown file (headings outside code fences)."""
    out, seen, fenced = set(), {}, False
    for line in text.splitlines():
        if line.startswith('```'): fenced = not fenced
        m = None if fenced else re.match(r'#{1,6}\s+(.*?)\s*#*\s*$', line)
        if not m: continue
        t = re.sub(r'[\\*`]', '', re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', m.group(1)))
        slug = re.sub(r'[^\w\- ]', '', t.strip().lower()).replace(' ', '-')
        n = seen.get(slug, 0); seen[slug] = n + 1
        out.add(slug if n == 0 else f'{slug}-{n}')
    return out

files = sorted(f for f in os.listdir(MD) if f.endswith('.md'))
anchor = {f: slugs(open(f'{MD}/{f}').read()) for f in files}
bad, n_links, n_images = [], 0, 0
for f in files:
    for m in re.finditer(r'(!?)\[[^\]]*\]\(([^)\s]+)\)', open(f'{MD}/{f}').read()):
        img, target = m.group(1), m.group(2)
        if re.match(r'(https?:|mailto:)', target): continue
        path, _, frag = target.partition('#')
        if img: n_images += 1
        else: n_links += 1
        if not path:
            if frag not in anchor[f]: bad.append((f, target, 'no such heading in this page'))
            continue
        full = os.path.normpath(os.path.join(MD, urllib.parse.unquote(path)))
        if not os.path.exists(full): bad.append((f, target, 'file not found')); continue
        if frag and path.endswith('.md') and frag not in anchor.get(os.path.basename(full), set()):
            bad.append((f, target, 'no such heading in target page'))
print(f'{len(files)} files, {n_links} links and {n_images} images checked: {len(bad)} broken')
for f, t, why in bad[:40]: print(f'  {f}: {t} ({why})')
sys.exit(1 if bad else 0)
