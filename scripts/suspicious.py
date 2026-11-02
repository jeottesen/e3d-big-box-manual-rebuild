#!/usr/bin/env python3
"""Look for places in the manual where something is probably wrong or missing. Reports only; it changes nothing.

1. Malformed links (errors): wiki piped-link syntax or leftover brackets in a link ([[Page|text]] typed as an external
   link), encoded characters in a link target, an empty link text, and links to this wiki that were left external.
2. Thin sections (warnings): a section with almost no text of its own, or one that only points somewhere else
   ("Please refer to...", "Coming Soon", "??").
3. Shrunk sections (warnings, needs the saved archive versions in the data folder): a section whose text is much
   shorter than the longest it ever was in an older version of the same page, which is how a section that was
   moved or cut down shows up.

Reads BIGBOX_MD (default manual/) and BIGBOX_RAW (default raw/). Exits non-zero only if there are errors.
Run:  python3 -I scripts/suspicious.py [--warnings]
"""
import html, os, re, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.environ.get('BIGBOX_MD', f'{ROOT}/manual')
RAW = os.environ.get('BIGBOX_RAW', f'{ROOT}/raw')

LINK = re.compile(r'(?<!!)\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]*)(?:\s+"[^"]*")?\)')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
POINTER = re.compile(r'coming soon|\?\?|\btodo\b|please refer|click here|instructions (?:are )?(?:to come|coming)', re.I)
THIN_WORDS = 12      # fewer words than this under a heading with no sub-headings: thin
SHRUNK = 0.5         # a section now under this share of its longest older text ...
SHRUNK_WORDS = 40    # ... and at least this many words shorter, is reported


def text_lines(md):
    """(line number, line) outside code fences."""
    fenced = False
    for n, line in enumerate(md.splitlines(), 1):
        if line.startswith('```'): fenced = not fenced
        elif not fenced: yield n, line


def malformed_links(md):
    """[(line, what)] for link markup that is probably a typo carried over from the wiki."""
    out = []
    for n, line in text_lines(md):
        for m in LINK.finditer(line):
            text, target = m.group(1), m.group(2)
            raw = urllib.parse.unquote(target)
            if not text.strip(): out.append((n, f'link with no text: {target}'))
            if re.search(r'%7C|\|', target) or '|' in raw: out.append((n, f'"|" inside a link target (wiki piped-link syntax): {target}'))
            if re.search(r'%5[BD]|[\[\]]', target): out.append((n, f'square bracket inside a link target: {target}'))
            if re.match(r'https?://wiki\.e3d-online\.com/(?!images/|resources/)', target) and 'web.archive.org' not in target:
                out.append((n, f'link to the old wiki left external: {target}'))
        plain = LINK.sub('', line)
        if re.search(r'\\?\[\\?\[|\\?\]\\?\]', plain): out.append((n, 'literal [[ or ]] outside a link'))
        if re.search(r'\\\[\s*\[[^\]]*\]\([^)]*\)\s*\\\]', line): out.append((n, 'link wrapped in literal \\[ \\]'))
    return out


def sections(md):
    """[(heading, level, line, words, has_subsections)] with the words of each section's own text (not its sub-sections')."""
    heads = [(n, len(m.group(1)), m.group(2)) for n, line in text_lines(md) if (m := HEADING.match(line))]
    lines = md.splitlines()
    out = []
    for i, (n, lvl, title) in enumerate(heads):
        end = heads[i + 1][0] - 1 if i + 1 < len(heads) else len(lines)
        body = '\n'.join(lines[n:end])
        body = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', body)             # images are not words
        body = LINK.sub(lambda m: m.group(1), body)
        words = len(re.findall(r"[A-Za-z0-9][\w'.\-]*", body))
        out.append((title, lvl, n, words, i + 1 < len(heads) and heads[i + 1][1] > lvl))
    return out


def thin_sections(md):
    """[(line, title, why)] for sections that have almost no text, or only point elsewhere."""
    out = []
    for title, _lvl, n, words, has_sub in sections(md):
        if has_sub: continue                                          # a parent heading is just a heading
        body = '\n'.join(md.splitlines()[n:n + 12])
        if re.search(r'^\|', '\n'.join(md.splitlines()[n:n + 12]), re.M): continue   # a table is content
        if words < THIN_WORDS: out.append((n, title, f'{words} words of text'))
        elif POINTER.search(body) and words < 3 * THIN_WORDS: out.append((n, title, 'only points elsewhere or says it is unfinished'))
    return out


def source_page(md):
    """The wiki page a built page came from, as its saved-version folder is named (None for a generated page)."""
    m = re.search(r'source: wiki\.e3d-online\.com/wiki/([^\s·]+)', md[:600])
    return urllib.parse.unquote(m.group(1)).replace('\\', '').replace(' ', '_') if m else None


def key(title):
    """A heading without its step number, so a renumbered section still matches its older self."""
    return re.sub(r'\W+', ' ', re.sub(r'^\(?[\d.]+\)?\s*', '', html.unescape(title))).strip().lower()


def old_sizes(page):
    """{heading key: (most words in any saved version, version)} for a wiki page, over every saved version."""
    import recover
    d = f'{RAW}/versions/{page}'
    best = {}
    if not os.path.isdir(d): return best
    for f in sorted(os.listdir(d)):
        if not f.endswith('.html'): continue
        h = open(f'{d}/{f}').read()
        if 'id="mw-content-text"' not in h or recover.ERR.search(h[:6000]): continue   # an error page, not an article
        c = recover.content(h); hs = list(recover.HEAD.finditer(c))
        sizes = {}
        for i, m in enumerate(hs):
            end = hs[i + 1].start() if i + 1 < len(hs) else len(c)   # own text only: stop at the next heading of any level
            words = len(re.findall(r"[A-Za-z0-9][\w'.\-]*", recover.htext(re.sub(r'<(img|a)\b[^>]*>', ' ', c[m.end():end]))))
            sizes.setdefault(key(recover.htext(m.group(2))), []).append(words)
        for k, ws in sizes.items():
            if len(ws) == 1 and ws[0] > best.get(k, (0, ''))[0]: best[k] = (ws[0], f[:-5])   # a name used twice on the page cannot be told apart
    return best


def shrunk_sections(md, page):
    """[(line, title, why)] for sections much shorter than in an older saved version of the same page."""
    old = old_sizes(page)
    out = []
    for title, _lvl, n, words, _sub in sections(md):
        was, ts = old.get(key(title), (0, ''))
        if was - words >= SHRUNK_WORDS and words < SHRUNK * was: out.append((n, title, f'{words} words now, {was} in the {ts} version'))
    return out


def main():
    show_warnings = '--warnings' in sys.argv
    errors = warnings = 0
    for f in sorted(x for x in os.listdir(MD) if x.endswith('.md')):
        md = open(f'{MD}/{f}').read()
        page = None
        for n, what in malformed_links(md):
            errors += 1; print(f'ERROR   {f}:{n}: {what}')
        if show_warnings:
            for n, title, why in thin_sections(md):
                warnings += 1; print(f'thin    {f}:{n}: {title}: {why}')
            page = source_page(md)
            for n, title, why in (shrunk_sections(md, page) if page else []):
                warnings += 1; print(f'shrunk  {f}:{n}: {title}: {why}')
    print(f'{errors} errors' + (f', {warnings} warnings' if show_warnings else ' (run with --warnings for thin and shrunk sections)'))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
