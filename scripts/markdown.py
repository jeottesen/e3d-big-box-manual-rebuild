#!/usr/bin/env python3
"""Convert the HTML manual in docs/ to GitHub-flavoured Markdown in manual/ (needs pandoc).

Each docs/<Page>.html becomes manual/<Page>.md and docs/index.html becomes manual/README.md. Images and
datasheet PDFs are not copied: the Markdown links to the copies in docs/images and docs/files. Links between
pages become .md links, and #section links are rewritten to GitHub's heading anchors, since the wiki's heading
ids differ.

Install pandoc with `mise use -g pandoc` (or set PANDOC to its path), then run:  python3 -I scripts/markdown.py
Reads BIGBOX_SITE (default docs/), writes BIGBOX_MD (default manual/).
"""
import html, os, re, shutil, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('BIGBOX_SITE', f'{ROOT}/docs')
OUT = os.environ.get('BIGBOX_MD', f'{ROOT}/manual')
PANDOC = os.environ.get('PANDOC') or shutil.which('pandoc')
if not PANDOC: sys.exit('pandoc not found. Install it with `mise use -g pandoc`, or set PANDOC to its path.')

def quote(name): return urllib.parse.quote(name, safe="()-_.,!~'")

def github_slug(text, seen):
    """GitHub's heading anchor: lowercase, drop punctuation, spaces to hyphens, -1/-2 for repeats."""
    slug = re.sub(r'[^\w\- ]', '', text.strip().lower()).replace(' ', '-')
    n = seen.get(slug, 0); seen[slug] = n + 1
    return slug if n == 0 else f'{slug}-{n}'

HEADING = re.compile(r'<h([1-6])\b([^>]*)>(.*?)</h\1>', re.S)

def anchors(h):
    """wiki heading id -> GitHub anchor, for every heading in a page's html."""
    out, seen = {}, {}
    for m in HEADING.finditer(h):
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(3)))
        slug = github_slug(' '.join(text.split()), seen)
        for i in re.findall(r'\bid="([^"]+)"', m.group(2) + m.group(3)): out[html.unescape(i)] = slug
    return out

def body(h):
    """The page html without the document wrapper: no style, no nav bar."""
    h = re.sub(r'<style.*?</style>|<nav>.*?</nav>|<title>.*?</title>|<!doctype[^>]*>|<meta[^>]*>', '', h, flags=re.S | re.I)
    h = re.sub(r'<p><a href="manual\.html">.*?</a></p>', '', h)   # the one-page edition is HTML only
    h = re.sub(r'</?dl\b[^>]*>', '', h)                             # wiki indentation: <dl><dd>text</dd></dl>
    h = re.sub(r'<dd\b[^>]*>', '<p>', h); h = h.replace('</dd>', '</p>')
    h = re.sub(r'<dt\b[^>]*>(.*?)</dt>', r'<p><strong>\1</strong></p>', h, flags=re.S)
    h = re.sub(r'<span class="missing">(.*?)</span>', r'<em>\1</em>', h)   # image-not-archived placeholders
    return h

def convert(page, h, pages, amap):
    own = amap[page]
    def link(m):
        href = html.unescape(m.group(1)); frag = ''
        if '#' in href: href, frag = href.split('#', 1)
        if not href and frag:                                    # #section inside this page
            return f'href="#{own[frag]}"' if frag in own else 'href="#"'
        if re.match(r'(https?:|mailto:)', href): return m.group(0)
        if href.startswith('images/') or href.startswith('files/'): return f'href="../docs/{href}"'
        name = href[:-5] if href.endswith('.html') else None
        if name == 'index': return 'href="README.md"'
        if name in pages:
            target = quote(name + '.md')
            if frag and frag in amap[name]: target += '#' + amap[name][frag]
            return f'href="{target}"'
        return m.group(0)
    h = body(h)
    # a #section link to a heading the page does not have (dangling in the wiki too) becomes plain text
    h = re.sub(r'<a\b[^>]*\bhref="#([^"]*)"[^>]*>(.*?)</a>', lambda m: m.group(0) if html.unescape(m.group(1)) in own else m.group(2), h, flags=re.S)
    h = re.sub(r'href="([^"]*)"', link, h)
    h = re.sub(r'src="images/', 'src="../docs/images/', h)
    md = subprocess.run([PANDOC, '-f', 'html', '-t', 'gfm-raw_html', '--wrap=none'], input=h, capture_output=True, text=True, check=True).stdout
    md = re.sub(r'(?m)^\\\n', '', md)            # lines holding only a backslash (a <br> between blocks)
    md = re.sub(r'\\\n(?=\n)', '\n', md)         # a hard line break at the end of a paragraph
    md = re.sub(r'[ \t]+\n', '\n', md)
    return re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'

def main():
    files = sorted(f for f in os.listdir(SITE) if f.endswith('.html') and f != 'manual.html')
    texts = {f[:-5]: open(f'{SITE}/{f}').read() for f in files}
    pages = set(texts) - {'index'}
    amap = {t: anchors(body(h)) for t, h in texts.items()}
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.md'): os.remove(f'{OUT}/{f}')   # the output folder is generated: drop pages that no longer exist
    for t, h in texts.items():
        open(f'{OUT}/{"README" if t == "index" else t}.md', 'w').write(convert(t, h, pages, amap))
    print(f'wrote {len(texts)} files to {OUT}')

if __name__ == '__main__': main()
