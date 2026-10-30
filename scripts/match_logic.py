"""Deciding which PDF sheet a wiki drawing image is. Standard library only, so the tests can import it.

Inputs are plain numbers and sheet numbers, worked out by scripts/match_sheets.py:
  visual    {sheet: how much the PDF sheet looks like the image, 0..1}
  by_title  the sheets whose title matches the image's file name
  shared    {sheet: share of the image's parts rows (OCR) that the sheet also lists, or None if there are no rows}
"""
STRONG = 0.85      # the drawings look the same...
MARGIN = 0.2       # ...and no other sheet comes close
MIN_ROWS = 0.8     # share of the image's rows that must be on the sheet for the title to be believed

def decide(visual, by_title, shared):
    """Returns (status, sheet): 'confirmed', 'check' (the title points at a sheet whose parts do not agree) or 'no match'.
    The parts are compared with the sheet the title names, not with whichever sheet looks most like the image."""
    ranked = sorted(visual, key=visual.get, reverse=True)
    best, second = ranked[0], ranked[1]
    if visual[best] >= STRONG and visual[best] - visual[second] >= MARGIN: return 'confirmed', best
    named = [t for t in by_title if t in visual]
    if not named: return 'no match', None   # nothing in the PDF looks like it, and nothing has its name: a sheet from a newer revision
    t = max(named, key=lambda s: (shared.get(s) or 0, visual[s]))
    ok = (t == best) if shared.get(t) is None else shared[t] >= MIN_ROWS   # no rows to compare: the title and the look must agree
    return ('confirmed', t) if ok else ('check', t)
