"""The rules for tidying text read by OCR from the drawing images. Standard library only, so the tests can import it.

The OCR drops spaces and garbles a few things. These functions put the spaces back, correct the misreads we know how to
correct safely, and never change a number: the image-only sheets hold parts the PDF does not have, and a near miss
(a 364 mm rod for a 384 mm one) is a different part, not a misread.
"""
import difflib, re

MIN_CONF = 0.85   # below this the OCR itself was unsure

def vocabulary(sheets):
    """Exact part and description strings from the PDF's sheets (work/proposed/parts.json), keyed without spaces."""
    vocab = {}
    for sh in sheets:
        for r in sh['rows']:
            for t in (r['part'], r['description']):
                if t: vocab[key(t)] = t
    return vocab

def parts_by_description(sheets):
    """Which part names the PDF lists under each description (mostly each 'Fixings Bag N'), keyed without spaces."""
    out = {}
    for sh in sheets:
        for r in sh['rows']:
            if r['description']: out.setdefault(key(r['description']), {})[key(r['part'])] = r['part']
    return out

def fix_row(part, desc, conf, vocab, by_desc, fixes):
    """Tidy one row's part and description. Returns (part, description, by_hand). `fixes` is the hand-checked table
    (key without spaces or case -> text); a row it touches is treated as checked."""
    by_hand = key(part) in fixes or key(desc) in fixes
    part, desc_read = fixes.get(key(part), part), fixes.get(key(desc), desc)
    fixed_part, fixed_desc = normalise(part, vocab, conf), normalise(desc_read, vocab, conf)
    if key(fixed_part) not in vocab and fixed_desc.startswith('Fixings Bag') and key(fixed_desc) in by_desc:   # only a fixings bag is a short enough list to match inside
        bag = by_desc[key(fixed_desc)]
        close = [c for c in difflib.get_close_matches(key(fixed_part), list(bag), n=2, cutoff=0.8) if digits(c) == digits(key(fixed_part))]   # never change a number
        if len(close) == 1: fixed_part = bag[close[0]]
    return fixed_part, fixed_desc, by_hand

def digits(t): return re.sub(r'\D', '', t)

def key(t):
    """A name without spaces, punctuation or case, for comparing: 'M3 x 10' and 'M3X10' are the same, and the multiplication
    sign counts as an x ('M3×10'); it must not collapse into 'M310', which 'M3-10' also gives."""
    return re.sub(r'[^A-Z0-9]', '', (t or '').upper().replace('×', 'X'))

EXTRA_WORDS = 'DOCK CLAMP LEVER GUIDE HYBRID TITAN NON DIRECT BODY TOP CAP BOTTOM BED DUAL CABLE BRACKET CHAIN ANCHOR BASE UPPER LOWER'.split()

def words_of(vocab):
    """Upper-case words from the PDF's names, plus a few the image-only sheets use."""
    return {w for t in vocab.values() for w in re.findall(r'[A-Za-z]{2,}', t.upper())} | set(EXTRA_WORDS)

def segment(run, known):
    """Split a run of capitals with no spaces ('BASEBRACKETLOWER') into known words; unknown stretches stay whole."""
    n = len(run)
    best = [(0, None)] + [(10 ** 9, None)] * n   # (cost, previous index)
    for j in range(1, n + 1):
        for i in range(max(0, j - 14), j):
            w = run[i:j]
            cost = best[i][0] + (1 if w in known else 12 * len(w))
            if cost < best[j][0]: best[j] = (cost, i)
    out, j = [], n
    while j > 0: i = best[j][1]; out.append(run[i:j]); j = i
    return ' '.join(reversed(out))

def respace(text, vocab):
    """OCR gives 'M3x10SocketCapScrew' for 'M3 x 10 Socket Cap Screw'. Use the PDF's exact string if there is one."""
    if key(text) in vocab: return vocab[key(text)]
    t = text.strip()
    known = words_of(vocab)
    t = re.sub(r'[A-Z]{7,}', lambda m: segment(m.group(0), known), t)   # OCR runs capitals together: BASEBRACKETLOWER
    t = re.sub(r'(?<=\d)x(?=\d)', ' x ', t)                           # M3x10 -> M3 x 10 (before the rules that split letters from digits)
    t = re.sub(r'\b(M\d+(?:\.\d+)?)(?=[A-Z][a-z])', r'\1 ', t)         # M2Hex Nut -> M2 Hex Nut
    t = re.sub(r'(?<=\d)(?=[A-Z][a-z]{3,})', ' ', t)                   # 10Socket -> 10 Socket (but not 0.9Deg)
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)                         # HexNut -> Hex Nut, CapScrew -> Cap Screw
    if ' ' in t and not re.search(r'[a-z]\d|[A-Za-z0-9]\(', t): return t
    t = re.sub(r'(?<=[a-z])(?=\d)', ' ', t)                            # Bag8 -> Bag 8
    t = re.sub(r'(?<=[A-Za-z0-9])(?=\()', ' ', t)                      # Nut(Half) -> Nut (Half)
    return t

BAG = re.compile(r'F[A-Za-z]{1,7}\s*B[A-Za-z]{1,3}\s*(\d{1,2})', re.I)   # 'Foings Bog8', 'Fxinss Bag 12': the OCR garbles 'Fixings Bag' more than anything else

def normalise(text, vocab, conf):
    """Put the OCR text right where we can. 'Fixings Bag N' is corrected by pattern. Other names are matched to the closest exact
    string from the PDF only when the OCR itself was unsure, and never if that would change a number: the image-only sheets
    hold parts the PDF does not have, and a near miss (a 364 mm rod for a 384 mm one) is a different part, not a misread."""
    m = BAG.fullmatch(text.strip())
    if m: return f'Fixings Bag {m.group(1)}'
    if not text or key(text) in vocab: return vocab.get(key(text), text)
    if conf >= MIN_CONF: return text
    close = [c for c in difflib.get_close_matches(key(text), list(vocab), n=2, cutoff=0.88) if digits(c) == digits(key(text))]
    return vocab[close[0]] if len(close) == 1 else text
