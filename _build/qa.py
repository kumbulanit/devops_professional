# -*- coding: utf-8 -*-
"""QA gate for the theory decks.

Converts each deck to PDF with LibreOffice, then checks every page for:
  · text extending past the right margin or below the content floor
  · text rendered smaller than the legibility floor
  · pages that are suspiciously empty
Exit code is non-zero if anything fails, so this can gate a rebuild.
"""
import os, subprocess, sys, glob
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES = os.path.abspath(os.path.join(HERE, '..', 'slides'))
WORK = os.path.join(HERE, '.qa')
SOFFICE = '/Applications/LibreOffice.app/Contents/MacOS/soffice'

PT_IN = 72.0
RIGHT_LIMIT = 12.70 * PT_IN     # content must end before this (slide is 13.33in)
BOTTOM_LIMIT = 6.52 * PT_IN     # the footer swirl starts at 6.59in
LEFT_MIN = 0.30 * PT_IN
MIN_FONT = 7.6                  # legibility floor

# Deliberate chrome, exempt from the content checks: the page number sits in the
# bottom-right corner, and full-bleed cover/section/close slides run to the edges.
CHROME_ZONES = [
    (11.90 * PT_IN, 6.70 * PT_IN, 13.34 * PT_IN, 7.50 * PT_IN),   # page number
    (0.00 * PT_IN, 6.55 * PT_IN, 13.34 * PT_IN, 7.50 * PT_IN),    # footer band
]
FULL_BLEED_MARKERS = ('DAY 1 OF 6', 'DAY 2 OF 6', 'DAY 3 OF 6', 'DAY 4 OF 6',
                      'DAY 5 OF 6', 'DAY 6 OF 6', '· WRAP-UP')


def _in_chrome(bbox):
    x0, y0, x1, y1 = bbox
    return any(x0 >= zx0 - 1 and y0 >= zy0 - 1 and x1 <= zx1 + 1 and y1 <= zy1 + 1
               for zx0, zy0, zx1, zy1 in CHROME_ZONES)


def convert(pptx):
    os.makedirs(WORK, exist_ok=True)
    subprocess.run([SOFFICE, '--headless', '--convert-to', 'pdf',
                    '--outdir', WORK, pptx],
                   check=True, capture_output=True, timeout=300)
    return os.path.join(WORK, os.path.basename(pptx).replace('.pptx', '.pdf'))


def check(pdf):
    doc = pymupdf.open(pdf)
    issues = []
    for i, page in enumerate(doc, 1):
        d = page.get_text('dict')
        blocks = [b for b in d['blocks'] if b['type'] == 0]
        if not blocks:
            issues.append((i, 'EMPTY', 'no text on page'))
            continue
        page_text = page.get_text()
        full_bleed = any(m in page_text for m in FULL_BLEED_MARKERS)
        for b in blocks:
            x0, y0, x1, y1 = b['bbox']
            if _in_chrome(b['bbox']) or full_bleed:
                continue
            txt = ' '.join(s['text'] for l in b['lines'] for s in l['spans'])[:48]
            if x1 > RIGHT_LIMIT:
                issues.append((i, 'RIGHT', f'{x1/PT_IN:.2f}in  "{txt}"'))
            if y1 > BOTTOM_LIMIT:
                issues.append((i, 'BOTTOM', f'{y1/PT_IN:.2f}in  "{txt}"'))
            if x0 < LEFT_MIN:
                issues.append((i, 'LEFT', f'{x0/PT_IN:.2f}in  "{txt}"'))
            for l in b['lines']:
                for sp in l['spans']:
                    if sp['size'] < MIN_FONT and sp['text'].strip():
                        issues.append((i, 'TINY', f"{sp['size']:.1f}pt  \"{sp['text'][:40]}\""))
    doc.close()
    return issues


if __name__ == '__main__':
    # Default: every taught deck, plus the per-lab ADVANCED decks that live in labs/.
    # Pass paths to check only those:  python qa.py ../labs/lab-03-*/Lab03A_Advanced_Git.pptx
    LABS = os.path.abspath(os.path.join(HERE, '..', 'labs'))
    decks = [os.path.abspath(a) for a in sys.argv[1:]] or (
        sorted(glob.glob(os.path.join(SLIDES, '*.pptx')))
        + sorted(glob.glob(os.path.join(LABS, '*', '*.pptx'))))
    decks = [d for d in decks if not os.path.basename(d).startswith('~$')]
    total_issues = 0
    for p in decks:
        pdf = convert(p)
        issues = check(pdf)
        n = len(pymupdf.open(pdf))
        seen, uniq = set(), []
        for it in issues:
            k = (it[0], it[1])
            if k not in seen:
                seen.add(k); uniq.append(it)
        status = 'CLEAN' if not uniq else f'{len(uniq)} issue(s)'
        print(f'  {os.path.basename(p):46s} {n:3d} pages   {status}')
        for pg, kind, detail in uniq[:8]:
            print(f'       p{pg:<3d} {kind:7s} {detail}')
        total_issues += len(uniq)
    print(f'\n  {"ALL DECKS CLEAN" if total_issues == 0 else f"{total_issues} issues to fix"}')
    sys.exit(1 if total_issues else 0)
