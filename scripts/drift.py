#!/usr/bin/env python3
"""Compare what the extraction tools propose (work/proposed/) with the reviewed data (data/sheets/), and accept changes on purpose.

The reviewed data is the source of truth; the tools only propose. Run after `mise run propose`:

    python3 -I scripts/drift.py                            report the differences (exit 1 if exact PDF text has changed)
    python3 -I scripts/drift.py --strict                   exit 1 on any difference or any unchecked sheet
    python3 -I scripts/drift.py --accept ID [ID ...]       copy those proposals into data/sheets/ (confirmed is cleared if the rows changed)
    python3 -I scripts/drift.py --accept-all               the same for every proposal that differs
    python3 -I scripts/drift.py --accept ... --confirm NAME   also record that NAME has checked the sheet against the drawing

Standard library only (it reads the tools' JSON, it does not run them).
"""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # sibling modules (python -I does not add the script folder)
import truth
from targets import OCR_FIXES, SHEET_IMAGES


def accept(ids, proposed, current, confirm):
    for sid in ids:
        sheet = dict(proposed[sid])
        old = current.get(sid)
        if old:
            sheet['notes'] = old.get('notes', '')
            same = truth._rows(old) == truth._rows(sheet) and old['source'].get('sha256') == sheet['source'].get('sha256')
            if same and old.get('confirmed'): sheet['confirmed'] = old['confirmed']   # nothing a person checked has changed
        if confirm: sheet['confirmed'] = {'by': confirm, 'on': datetime.date.today().isoformat()}
        bad = truth.problems(sheet)
        if bad: raise SystemExit(f'{sid}: {bad}')
        truth.write_sheet(sheet)
        print(f'accepted {sid} ({len(sheet["rows"])} rows){" and confirmed" if confirm else ""}')


def main(argv):
    strict = '--strict' in argv
    confirm = argv[argv.index('--confirm') + 1] if '--confirm' in argv else None
    current = truth.load_truth()
    bad = [f'{sid}: {p}' for sid, s in current.items() for p in truth.problems(s)]
    proposed = truth.proposals(OCR_FIXES, SHEET_IMAGES)
    differences = truth.diff(current, proposed)
    if '--accept-all' in argv: accept(sorted({sid for _, sid, _ in differences if sid in proposed}), proposed, current, confirm); return 0
    if '--accept' in argv:
        ids = [a for a in argv[argv.index('--accept') + 1:] if not a.startswith('--') and a != confirm]
        missing = [i for i in ids if i not in proposed]
        if missing: raise SystemExit(f'Nothing proposed for: {missing}')
        accept(ids, proposed, current, confirm); return 0
    unchecked = [sid for sid, s in current.items() if s['confirmed'] is None and any(r['how'] != 'pdf-text' for r in s['rows'])]
    errors = [m for sev, _, m in differences if sev == 'error']
    for line in bad: print('ERROR  data:', line)
    for sev, sid, msg in differences: print(f'{"ERROR" if sev == "error" else "info "}  {sid}: {msg}')
    for sid in unchecked: print(f'info   {sid}: not exact PDF text (read by OCR or entered by hand) and not yet confirmed by a person')
    print(f'\n{len(current)} sheets in the data, {len(proposed)} proposed; {len(differences)} differences, {len(unchecked)} sheets not yet confirmed by a person.')
    return 1 if bad or errors or (strict and (differences or unchecked)) else 0


if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
