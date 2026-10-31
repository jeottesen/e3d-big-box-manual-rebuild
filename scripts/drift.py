#!/usr/bin/env python3
"""Compare what the extraction tools propose (work/proposed/) with the reviewed data (data/sheets/), and accept changes on purpose.

The reviewed data is the source of truth; the tools only propose. Run after `mise run propose`:

    python3 -I scripts/drift.py                            report the differences (exit 1 if exact PDF text has changed or the data is malformed)
    python3 -I scripts/drift.py --strict                   exit 1 on any difference or any unchecked sheet
    python3 -I scripts/drift.py --accept ID [ID ...]       merge those proposals into data/sheets/ (confirmed is cleared if a row changed)
    python3 -I scripts/drift.py --accept ... --confirm NAME   also record that NAME has checked the sheet against the drawing
    python3 -I scripts/drift.py --accept-all               the same for every sheet that differs, except those where exact PDF text
                                                           or the PDF changed (name those yourself); it cannot be combined with --confirm

Accepting merges: the proposal supplies the source, title, images and the rows the tools read, and the reviewed data keeps what a person
added to a row (how it was corrected, what the tool read, approx, basis, unsure) and the rows a person entered by hand.

Standard library only (it reads the tools' JSON, it does not run them).
"""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import truth
from targets import OCR_FIXES, SHEET_IMAGES

FLAGS = {'--strict': 0, '--accept': None, '--accept-all': 0, '--confirm': 1}   # how many values each takes (None: any number)


def merge(old, new):
    """The sheet to write when `new` (a proposal) is accepted over `old` (the reviewed sheet; None if there is none)."""
    sheet = dict(new)
    if old is None: return sheet
    sheet['notes'] = old.get('notes', '')
    kept = {}
    for r in old['rows']: kept.setdefault(truth.rowkey(r), []).append(r)
    rows = []
    for r in new['rows']:
        same = kept.get(truth.rowkey(r))
        rows.append(same.pop(0) if same else r)   # the same row: keep what a person made of it
    rows += [r for r in old['rows'] if r['how'] == 'entered']   # a row a person typed in is never the tools' to propose
    sheet['rows'] = rows
    unchanged = rows == old['rows'] and old['source'].get('sha256') == sheet['source'].get('sha256')
    sheet['confirmed'] = old.get('confirmed') if unchanged else None   # nothing a person checked has changed, or it needs checking again
    return sheet


def accept(ids, proposed, current, confirm):
    """Merge and write. Every sheet is checked before any is written, so a bad one does not leave the others half-done."""
    merged = {}
    for sid in ids:
        sheet = merge(current.get(sid), proposed[sid])
        if confirm: sheet['confirmed'] = {'by': confirm, 'on': datetime.date.today().isoformat()}
        bad = truth.problems(sheet)
        if bad: raise SystemExit(f'{sid}: {bad}; nothing was written')
        merged[sid] = sheet
    for sid, sheet in merged.items():
        truth.write_sheet(sheet)
        print(f'accepted {sid} ({len(sheet["rows"])} rows){" and confirmed" if confirm else ""}')


def parse(argv):
    """{flag: [values]} and a usage error for anything unknown or missing a value."""
    flags, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a not in FLAGS: raise SystemExit(f'unknown argument {a!r}; see the top of scripts/drift.py')
        want = FLAGS[a]
        vals = []
        i += 1
        while i < len(argv) and not argv[i].startswith('--') and (want is None or len(vals) < want): vals.append(argv[i]); i += 1
        if want is not None and len(vals) != want: raise SystemExit(f'{a} needs {want} value(s)')
        if a == '--accept' and not vals: raise SystemExit('--accept needs at least one sheet id')
        flags[a] = vals
    if '--accept-all' in flags and '--confirm' in flags: raise SystemExit('--confirm records that a person checked a sheet, so it cannot be used with --accept-all; name the sheets')
    return flags


def main(argv):
    flags = parse(argv)
    current = truth.load_truth()
    bad = truth.all_problems(current)
    for line in bad: print('ERROR  data:', line)
    if bad: return 1   # nothing else is safe to do with malformed data
    proposed = truth.proposals(OCR_FIXES, SHEET_IMAGES)
    differences = truth.diff(current, proposed)
    confirm = flags['--confirm'][0] if '--confirm' in flags else None
    if '--accept-all' in flags:
        risky = {sid for sev, sid, _ in differences if sev == 'error'}
        ids = sorted({sid for _, sid, _ in differences if sid in proposed} - risky)
        for sid in sorted(risky): print(f'skipped {sid}: exact PDF text or the PDF changed; look at it and accept it by name')
        accept(ids, proposed, current, None)
        return 0
    if '--accept' in flags:
        ids = flags['--accept']
        missing = [i for i in ids if i not in proposed]
        if missing: raise SystemExit(f'Nothing proposed for: {missing}')
        accept(ids, proposed, current, confirm)
        return 0
    unchecked = [sid for sid, s in current.items() if s['confirmed'] is None and any(r['how'] != 'pdf-text' for r in s['rows'])]
    errors = [m for sev, _, m in differences if sev == 'error']
    for sev, sid, msg in differences: print(f'{"ERROR" if sev == "error" else "info "}  {sid}: {msg}')
    for sid in unchecked: print(f'info   {sid}: not exact PDF text (read by OCR or entered by hand) and not yet confirmed by a person')
    print(f'\n{len(current)} sheets in the data, {len(proposed)} proposed; {len(differences)} differences, {len(unchecked)} sheets not yet confirmed by a person.')
    return 1 if errors or (flags.get('--strict') is not None and (differences or unchecked)) else 0


if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
