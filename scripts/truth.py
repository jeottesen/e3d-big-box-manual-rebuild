"""The reviewed per-sheet data: data/sheets/*.json. Standard library only.

One file per drawing sheet, holding the parts list a person has checked. The build reads only these files. The extraction
tools (drawings.py, drawing_images.py, match_sheets.py) never write them: they write proposals to work/proposed/, and
scripts/drift.py compares the proposals with the data here and says what differs. A person accepts a change on purpose.

A sheet file (see data/README.md for the full description):

  id          "pdf-28" for page 28 of the exploded drawings PDF, "img-Z-AXIS_DRAG_CHAIN" for a sheet that only exists as an image
  title       the sheet's title
  source      {"kind": "pdf", "file", "sha256", "page"} or {"kind": "image", "file", "sha256", "image_sheet": [n, of]}
  images      [{"file", "role"}]  role: wiki (as the wiki has it), redrawn (replaced by a drawing of the PDF sheet, original kept),
              enlarged (made twice the size, original kept), lost (the wiki's image was not archived; drawn from the PDF sheet)
  rows        [{"item", "qty", "part", "description", "how", ...}]  how: pdf-text (exact), ocr, ocr+fix (corrected by rule),
              hand (corrected by a person), entered (typed by a person from the drawing and the manual; no tool read it, so it has a "basis").
              Corrected rows keep "read_as": what the tool read. OCR rows keep "confidence". "approx": true marks a quantity the manual gives as approximate.
  confirmed   null, or {"by", "on"}: a person has checked this sheet against the drawing
  notes       free text
"""
import collections, hashlib, json, os
from ocr_text import key   # one way of comparing names, shared with the OCR rules

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = f'{ROOT}/data/sheets'
PROPOSED = f'{ROOT}/work/proposed'     # the tools' output (git-ignored): proposals, never the truth
PDF = f'{ROOT}/docs/files/EXPLODED_DRAWINGS.pdf'
PDF_REL = 'docs/files/EXPLODED_DRAWINGS.pdf'
ROLES = ('wiki', 'redrawn', 'enlarged', 'lost')
HOW = ('pdf-text', 'ocr', 'ocr+fix', 'hand', 'entered')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()

def dumps(sheet): return json.dumps(sheet, indent=1, ensure_ascii=False) + '\n'

def load_truth():
    """{id: sheet} for every file in data/sheets/."""
    out = {}
    if os.path.isdir(DATA):
        for f in sorted(os.listdir(DATA)):
            if f.endswith('.json'):
                with open(f'{DATA}/{f}', encoding='utf-8') as fh: out[f[:-5]] = json.load(fh)
    return out

def write_sheet(sheet):
    os.makedirs(DATA, exist_ok=True)
    with open(f'{DATA}/{sheet["id"]}.json', 'w', encoding='utf-8') as f: f.write(dumps(sheet))

def _is_int(v): return isinstance(v, int) and not isinstance(v, bool)

def problems(sheet):
    """What is wrong with a sheet's shape. [] when it is fine. Never raises, whatever a hand edit left in the file."""
    if not isinstance(sheet, dict): return ['a sheet must be an object']
    out = []
    for field in ('id', 'title', 'source', 'images', 'rows', 'confirmed'):
        if field not in sheet: out.append(f'missing "{field}"')
    if out: return out
    src = sheet['source']
    if not isinstance(src, dict) or src.get('kind') not in ('pdf', 'image'): return ['source must be an object with kind pdf or image']
    if not isinstance(sheet['id'], str) or not sheet['id'].startswith('pdf-' if src['kind'] == 'pdf' else 'img-'): out.append('id must start with pdf- for a PDF sheet and img- for an image sheet')
    if not isinstance(src.get('file'), str) or not isinstance(src.get('sha256'), str): out.append('source needs file and sha256')
    if src['kind'] == 'pdf' and not (_is_int(src.get('page')) and src['page'] >= 1): out.append('a PDF sheet needs source.page')
    if not isinstance(sheet['images'], list): return out + ['images must be a list']
    if src['kind'] == 'image' and not sheet['images']: out.append('an image sheet needs at least one image')
    for im in sheet['images']:
        if not isinstance(im, dict) or not isinstance(im.get('file'), str): out.append('each image needs a file'); continue
        if im.get('role') not in ROLES: out.append(f'image {im["file"]}: role must be one of {ROLES}')
        if im.get('role') in ('lost', 'redrawn') and src['kind'] != 'pdf': out.append(f'image {im["file"]}: only a PDF sheet can have a {im["role"]} image (it is drawn from the PDF page)')
    if not isinstance(sheet['rows'], list): return out + ['rows must be a list']
    for i, r in enumerate(sheet['rows']):
        if not isinstance(r, dict): out.append(f'row {i}: must be an object'); continue
        if not _is_int(r.get('qty')) or r['qty'] < 1: out.append(f'row {i}: qty must be a whole number')
        if not (isinstance(r.get('part'), str) and r['part']): out.append(f'row {i}: no part')
        if not isinstance(r.get('description'), str): out.append(f'row {i}: description must be text (empty if there is none)')
        if r.get('how') not in HOW: out.append(f'row {i}: how must be one of {HOW}')
        if r.get('how') in ('ocr+fix', 'hand') and not isinstance(r.get('read_as'), dict): out.append(f'row {i}: a corrected row must keep what the tool read (read_as)')
        if r.get('how') == 'entered' and not r.get('basis'): out.append(f'row {i}: an entered row must say what it is based on (basis)')
        if 'approx' in r and not isinstance(r['approx'], bool): out.append(f'row {i}: approx must be true or false')
    c = sheet['confirmed']
    if c is not None and not (isinstance(c, dict) and isinstance(c.get('by'), str) and c['by'] and isinstance(c.get('on'), str) and c['on']): out.append('confirmed needs by and on')
    return out

def all_problems(sheets):
    """problems() for every sheet, plus what only shows across sheets: a file name that does not match its id, and a drawing
    image claimed by two sheets. [] when the data is sound."""
    out = []
    owners = {}
    for sid, s in sorted(sheets.items()):
        out += [f'{sid}: {p}' for p in problems(s)]
        if isinstance(s, dict) and s.get('id') != sid: out.append(f'{sid}: the file name and the id ({s.get("id")!r}) differ')
        if isinstance(s, dict) and isinstance(s.get('images'), list):
            for im in s['images']:
                if isinstance(im, dict) and isinstance(im.get('file'), str): owners.setdefault(im['file'], []).append(sid)
    out += [f'image {f} belongs to more than one sheet: {ids}' for f, ids in sorted(owners.items()) if len(ids) > 1]
    return out


# ---------- turning the tools' output into sheets (proposals) ----------

def _load(name):
    path = f'{PROPOSED}/{name}'
    if not os.path.exists(path): return None
    with open(path, encoding='utf-8') as f: return json.load(f)

def proposals(fixes, lost_images):
    """{id: sheet} built from work/proposed/{parts,parts_images,sheet_matches}.json.
    fixes: the hand-corrections table (targets.OCR_FIXES). lost_images: {file: sheet} for drawings the archive lost (targets.SHEET_IMAGES)."""
    parts, ocr, matches = _load('parts.json'), _load('parts_images.json'), _load('sheet_matches.json')
    if not (parts and ocr and matches): raise SystemExit('Nothing proposed yet: run `mise run propose` first.')
    matches = matches['matches']; hand = {key(k) for k in fixes}
    out = {}
    for sh in parts['sheets']:
        if not sh['rows']: continue   # a blank sheet
        n = sh['sheet']
        images = [{'file': f, 'role': 'redrawn' if m.get('action') == 'redraw' else 'wiki'} for f, m in sorted(matches.items()) if m['status'] == 'confirmed' and m['sheet'] == n]
        images += [{'file': f, 'role': 'lost'} for f, s in sorted(lost_images.items()) if s == n]
        out[f'pdf-{n:02d}'] = {
            'id': f'pdf-{n:02d}', 'title': sh['title'],
            'source': {'kind': 'pdf', 'file': PDF_REL, 'sha256': sha256(PDF), 'page': n},
            'images': images,
            'rows': [{'item': r['item'], 'qty': int(r['qty']), 'part': r['part'], 'description': r['description'], 'how': 'pdf-text'} for r in sh['rows']],
            'confirmed': None, 'notes': ''}
    for sh in ocr['sheets']:
        if matches.get(sh['image'], {}).get('status') == 'confirmed' or not sh['rows']: continue   # a sheet the PDF has is read from the PDF
        f = sh['image']; stem = os.path.splitext(f)[0]
        original = f'docs/images/original/{f}' if os.path.exists(f'{ROOT}/docs/images/original/{f}') else f'docs/images/{f}'
        rows = []
        for r in sh['rows']:
            was = r.get('ocr')
            how = 'ocr' if not was else 'hand' if (key(was['part']) in hand or key(was['description']) in hand) else 'ocr+fix'
            row = {'item': r['item'], 'qty': int(r['qty']), 'part': r['part'], 'description': r['description'], 'how': how, 'confidence': r['confidence']}
            if was: row['read_as'] = was
            if r.get('review'): row['unsure'] = True
            rows.append(row)
        out[f'img-{stem}'] = {
            'id': f'img-{stem}', 'title': sh['title'],
            'source': {'kind': 'image', 'file': original, 'sha256': sha256(f'{ROOT}/{original}'), 'image_sheet': [sh['sheet'], sh['of']]},
            'images': [{'file': f, 'role': 'enlarged' if matches.get(f, {}).get('action') == 'enlarge' else 'wiki'}],
            'rows': rows, 'confirmed': None, 'notes': ''}
    return out


# ---------- comparing proposals with the truth ----------

def rowkey(r): return (r['qty'], key(r['part']), key(r['description']))

def _rows(sheet): return collections.Counter(rowkey(r) for r in sheet['rows'])

def _how(r): return (r['how'], bool(r.get('approx')), bool(r.get('unsure')), json.dumps(r.get('read_as'), sort_keys=True))

def diff(truth, proposed):
    """[(severity, id, message)]. severity "error" for a change to exact PDF text, a changed PDF, or a broken truth file; else "info".
    A row is the same row when its quantity, part and description match (spacing and case aside). For the same row, a change to how it
    was read (how, read_as, approx, unsure) is reported too: it means a correction or a flag the person made is not what the tools propose."""
    out = []
    for sid in sorted(set(truth) | set(proposed)):
        t, p = truth.get(sid), proposed.get(sid)
        if t is None: out.append(('info', sid, f'new sheet, no data yet ({len(p["rows"])} rows); accept it with --accept {sid}')); continue
        if p is None:
            if not all(r['how'] == 'entered' for r in t['rows']): out.append(('info', sid, 'in the data but the tools no longer propose it'))   # a sheet a person entered is not the tools' to propose
            continue
        exact = t['source']['kind'] == 'pdf'
        sev = 'error' if exact else 'info'
        if exact and t['source'].get('sha256') != p['source']['sha256']: out.append(('error', sid, 'the PDF has changed since this sheet was recorded'))
        a, b = _rows(t), _rows(p)
        for row, n in sorted((a - b).items()): out.append((sev, sid, f'row in the data but not proposed: {n} x {row}'))
        for row, n in sorted((b - a).items()): out.append((sev, sid, f'row proposed but not in the data: {n} x {row}'))
        tr, pr = {rowkey(r): r for r in t['rows']}, {rowkey(r): r for r in p['rows']}
        for k in sorted(set(tr) & set(pr)):
            if _how(tr[k]) != _how(pr[k]): out.append((sev, sid, f'row {k} was read differently: data {_how(tr[k])[:3]}, proposed {_how(pr[k])[:3]}' + (' (read_as differs)' if _how(tr[k])[3] != _how(pr[k])[3] else '')))
        if t['title'] != p['title']: out.append(('info', sid, f'title: data {t["title"]!r}, proposed {p["title"]!r}'))
        if sorted((i['file'], i['role']) for i in t['images']) != sorted((i['file'], i['role']) for i in p['images']):
            out.append(('info', sid, f'images: data {[(i["file"], i["role"]) for i in t["images"]]}, proposed {[(i["file"], i["role"]) for i in p["images"]]}'))
    return out
