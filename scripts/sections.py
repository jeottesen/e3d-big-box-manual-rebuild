"""Which step of the manual shows each drawing. Standard library only, so the tests can import it.

The manual is the source of truth for which step a drawing belongs to: the wiki author placed each drawing under the step that
uses it. build.py uses this to link each Bill of Materials row to the steps that show its drawing, and the tests check it
against the built pages.
"""
import html, re, urllib.parse

HEADING = re.compile(r'<h([1-6])\b([^>]*)>(.*?)</h\1>', re.S)   # the page title is added separately, so any h1 in a body is a section (Titan Assembly uses them)
IMG_SRC = re.compile(r'<img\b[^>]*?\ssrc="([^"]+)"')
NOT_BUILD_PAGES = {'BigBox_Build_Manual', 'Bill_Of_Materials', 'Downloads', 'Datasheets', 'Appendix_Older_Version_Content'}   # pages that are not build steps
STEP = re.compile(r'\(\d')   # a heading that starts with a step number: "(8) Electronics Cover", "(20.2) Assembly of the E3D HotEnds"


def thumb_file(src):
    """The file name of an image from its src, whether the wiki gave the full image or a thumbnail of it."""
    p = urllib.parse.unquote(urllib.parse.urlparse(html.unescape(src)).path)
    m = re.match(r'/images/thumb/[^/]+/[^/]+/([^/]+)/', p)
    return m.group(1) if m else p.rsplit('/', 1)[-1]


def headings(body):
    """[(level, id, text)] for every heading that has an id, in document order. The wiki puts the id on an inner span."""
    out = []
    for m in HEADING.finditer(body):
        found = re.search(r'\bid="([^"]+)"', m.group(2) + m.group(3))
        if found: out.append((int(m.group(1)), html.unescape(found.group(1)), ' '.join(html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).split())))
    return out


def embedded_sections(bodies, slug=lambda t: t):
    """image file name -> [(page slug, heading id or None, heading text)]: where the manual shows each image.
    bodies is {page title: html}. An image belongs to the nearest heading above it that starts with a step number, else the nearest
    heading of any kind; a drawing above a page's first heading (the sub-pages are mostly one drawing) belongs to the page itself,
    with no heading id. Headings are taken in document order, so an image in a gallery or a table still finds its heading."""
    out = {}
    for t, body in bodies.items():
        if t in NOT_BUILD_PAGES: continue
        marks = []   # (position, 'h', heading) or (position, 'i', src)
        for m in HEADING.finditer(body):
            found = re.search(r'\bid="([^"]+)"', m.group(2) + m.group(3))
            if found: marks.append((m.start(), 'h', (int(m.group(1)), html.unescape(found.group(1)), ' '.join(html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).split()))))
        marks += [(m.start(), 'i', m.group(1)) for m in IMG_SRC.finditer(body)]
        stack = []   # the headings above this point, outermost first: (level, id, text)
        for _, kind, v in sorted(marks, key=lambda x: x[0]):
            if kind == 'h':
                while stack and stack[-1][0] >= v[0]: stack.pop()
                stack.append(v)
            else:
                chosen = next((h for h in reversed(stack) if STEP.match(h[2])), stack[-1]) if stack else (0, None, t.replace('_', ' '))
                found = out.setdefault(thumb_file(v), [])
                if (slug(t), chosen[1], chosen[2]) not in found: found.append((slug(t), chosen[1], chosen[2]))
    return out
