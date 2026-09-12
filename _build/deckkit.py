# -*- coding: utf-8 -*-
"""deckkit — slide builders for the DevOps Professional theory decks.

Builds on the NobleProg template's own layouts so the master branding, fonts and
footer are inherited; content is drawn as explicit shapes so dense technical
slides stay under control.

Slide canvas is 13.33 x 7.50 in (16:9).
    title   y 0.40 h 0.95   (we shrink the layout's 1.45in title box)
    content y 1.65 -> 6.80
    footer  y 6.95
"""
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy
import os as _os

# ─────────────────────────────────────────────────────────────── palette
# Lifted from Cheat_Sheet_full.pptx so the decks and the cheat sheet are one family.
NAVY   = '123A5F'   # headings, primary structure
INK    = '1F2933'   # body text and neutral labels
TEAL   = '117A69'   # "compare" / good practice
ORANGE = 'D2760D'   # "build" / best practice / warnings
PLUM   = 'A0275C'   # "audit" / exceptions
GREEN  = '3E7D32'   # a true green, distinct from the teal above
LTBLUE = '29ABE2'   # bright accent (top bar)
BLUE   = '1B75BB'   # deep accent (bottom bar)
GOLD   = 'D2760D'   # banking callouts share the build colour
RED    = 'B3261E'   # anti-patterns / failure
GREY   = '5A6570'
WHITE  = 'FFFFFF'

PALE = {
    'blue':   'ECF1F6', 'teal': 'E6F4F1', 'orange': 'FDF1E2', 'green': 'EDF4EA',
    'gold':   'FDF1E2', 'red':  'FBEBEA', 'grey':   'F3F6F8', 'plum': 'FAECF2',
}

# ─────────────────────────────────────────────────────────────── geometry
SW, SH = 13.333, 7.5
M       = 0.72          # margins match the cheat sheet
CW      = 11.89
TOP     = 1.95          # first content row (below title + rule)
BOT     = 6.42          # floor: the footer swirl starts at 6.59
TITLE_W = 9.05          # title stops short of the logo

HERE    = _os.path.dirname(_os.path.abspath(__file__))
LOGO    = _os.path.join(HERE, 'assets', 'nobleprog_logo.png')
SWIRL   = _os.path.join(HERE, 'assets', 'footer_swirl.png')


def inch(v):
    return Inches(v)


# ─────────────────────────────────────────────────────────────── primitives
def _tf(shape, text, pt, bold=False, colour=NAVY, align='l', anchor='t',
        italic=False, space_after=2, font='Aptos', line=0.92):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE,
                          'b': MSO_ANCHOR.BOTTOM}[anchor]
    lines = text.split('\n') if isinstance(text, str) else list(text)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER,
                       'r': PP_ALIGN.RIGHT}[align]
        p.space_after = Pt(space_after)
        p.line_spacing = line
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(pt)
        r.font.bold = bold
        r.font.italic = italic
        r.font.name = font
        r.font.color.rgb = RGBColor.from_string(colour)
    return shape


def box(slide, x, y, w, h, fill=None, text='', pt=11, bold=False, colour=NAVY,
        align='l', anchor='t', line_col=None, line_w=0.75, radius=None,
        italic=False, shape=MSO_SHAPE.RECTANGLE, space_after=2, font='Aptos'):
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        sh.fill.background()
    if line_col:
        sh.line.color.rgb = RGBColor.from_string(line_col); sh.line.width = Pt(line_w)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    _tf(sh, text, pt, bold, colour, align, anchor, italic, space_after, font)
    return sh


def label(slide, x, y, w, h, text, pt=11, bold=False, colour=NAVY, align='l',
          anchor='t', italic=False, space_after=2, font='Aptos', line=0.92):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    _tf(tb, text, pt, bold, colour, align, anchor, italic, space_after, font, line)
    return tb


def line(slide, x1, y1, x2, y2, colour=TEAL, w=1.0, dash=False):
    from pptx.enum.shapes import MSO_CONNECTOR
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                   Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = RGBColor.from_string(colour)
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = 4  # dash
    return c


def arrow(slide, x, y, w, h, colour=TEAL, direction='right'):
    shp = {'right': MSO_SHAPE.RIGHT_ARROW, 'down': MSO_SHAPE.DOWN_ARROW,
           'left': MSO_SHAPE.LEFT_ARROW, 'up': MSO_SHAPE.UP_ARROW}[direction]
    a = slide.shapes.add_shape(shp, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor.from_string(colour)
    a.line.fill.background(); a.shadow.inherit = False
    return a


def chev(slide, x, y, w, h, text, fill, colour=WHITE, pt=10.5, bold=True):
    s = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y),
                               Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(fill)
    s.line.fill.background(); s.shadow.inherit = False
    _tf(s, text, pt, bold, colour, 'c', 'm')
    return s


# ─────────────────────────────────────────────────────────────── autofit
def fit_pt(text_lines, base, floor, chars_at_base, rows_at_base):
    """Shrink font until the block plausibly fits: considers both the longest
    line and the number of wrapped rows."""
    rows = 0
    longest = 1
    for ln in text_lines:
        longest = max(longest, len(ln))
        rows += max(1, (len(ln) // max(1, chars_at_base)) + 1)
    pt = base
    if longest > chars_at_base:
        pt = min(pt, base * chars_at_base / longest)
    if rows > rows_at_base:
        pt = min(pt, base * rows_at_base / rows)
    return max(floor, round(pt, 1))


def fit_block(items, avail, chars_at_base, base, floor, lead=0.12,
              head_h=0.30, sub_h=0.26, row=0.21):
    """Shrink the font until the measured stack fits `avail`, and return the
    EXACT per-item heights the drawing loop must then use.

    Measuring and drawing used to use separate formulas, which let the last
    item drift through the floor (and made `spread` inflate the gaps). One
    source of truth removes both bugs.
    """
    pt = base
    while True:
        scale = max(0.6, pt / base)
        cpl = max(14, int(chars_at_base / scale))
        heights, used = [], 0.0
        for it in items:
            head, sub = (it if isinstance(it, tuple) else (it, None))
            hh = (head_h + row * (len(head) // cpl)) * scale
            hs = ((sub_h + (row - 0.02) * (len(sub) // int(cpl * 1.12))) * scale
                  if sub else 0.0)
            heights.append((hh, hs))
            used += hh + lead + (hs + 0.05 if sub else 0.0)
        if used <= avail or pt <= floor:
            return round(pt, 1), used, heights
        pt -= 0.4


def spread(n, avail, used, cap=0.34):
    """Extra gap to add between n items so they fill `avail` rather than
    clumping at the top. Capped so a 2-item list does not become a ladder."""
    if n < 2:
        return 0.0
    return max(0.0, min(cap, (avail - used) / (n - 1)))


# ─────────────────────────────────────────────────────────────── slide frame
def _blank(prs, layout=6, chrome=True):
    """Blank layout + the NobleProg chrome: logo top-right, swirl and page
    number at the foot. Matches Cheat_Sheet_full.pptx exactly."""
    s = prs.slides.add_slide(prs.slide_layouts[layout])
    if chrome:
        _chrome(s, len(prs.slides._sldIdLst))
    return s


def _chrome(slide, page_no):
    try:
        slide.shapes.add_picture(LOGO, Inches(9.99), Inches(0.24),
                                 Inches(3.11), Inches(0.98))
        slide.shapes.add_picture(SWIRL, Inches(1.25), Inches(6.59),
                                 Inches(10.66), Inches(0.82))
    except Exception:
        pass
    label(slide, 12.10, 6.86, 0.90, 0.30, str(page_no), 10, False, GREY, align='r')


def _set_title(slide, title, kicker=None, sub=None):
    """Cheat-sheet header: small caps kicker, large navy title, optional
    grey standfirst, then a short accent rule."""
    if kicker:
        label(slide, M, 0.36, TITLE_W, 0.26, kicker.upper(), 10, True, GREY)
    label(slide, M, 0.66, TITLE_W, 0.95, title,
          fit_pt([title], 28, 19, 46, 2), True, NAVY, anchor='m',
          font='Aptos Display', line=0.98)
    y = 1.52
    if sub:
        label(slide, M, y, CW, 0.40, sub, fit_pt([sub], 13, 11, 128, 2), False, GREY)
        y += 0.34
    line(slide, M, y + 0.06, M + 2.60, y + 0.06, LTBLUE, 2.0)
    return y


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ═══════════════════════════════════════════════════════════ slide types
def s_title(prs, day, title, subtitle, bullets, footer, client='UniCredit'):
    s = _blank(prs, 6, chrome=False)
    box(s, 0, 0, SW, SH, fill=WHITE)
    box(s, 0, 0, SW, 0.30, fill=LTBLUE)
    box(s, 0, 7.20, SW, 0.30, fill=BLUE)
    try:
        s.shapes.add_picture(LOGO, Inches(0.80), Inches(0.92),
                             Inches(3.06), Inches(1.02))
    except Exception:
        pass
    label(s, 0.80, 2.42, 11.60, 0.34,
          f'NOBLEPROG · DEVOPS PROFESSIONAL · {client.upper()} · DAY {day} OF 6',
          11, True, LTBLUE)
    label(s, 0.80, 2.86, 11.40, 1.20, title,
          fit_pt([title], 34, 24, 44, 2), True, NAVY, font='Aptos Display', line=1.0)
    line(s, 0.80, 4.33, 4.00, 4.33, LTBLUE, 2.5)
    label(s, 0.80, 4.50, 11.40, 0.44, subtitle, 15, False, GREY)
    y = 5.08
    for b in bullets:
        box(s, 0.80, y + 0.075, 0.12, 0.12, fill=ORANGE)
        label(s, 1.08, y - 0.045, 10.9, 0.32, b, 12, False, INK)
        y += 0.36
    label(s, 0.80, 6.62, 11.40, 0.34, footer, 10.5, False, GREY, italic=True)
    return s


def s_section(prs, number, title, blurb, items=None):
    s = _blank(prs, 6, chrome=False)
    box(s, 0, 0, SW, SH, fill=PALE['blue'])
    box(s, 0, 0, SW, 0.30, fill=LTBLUE)
    box(s, 0, 7.20, SW, 0.30, fill=BLUE)
    try:
        s.shapes.add_picture(LOGO, Inches(9.99), Inches(0.62),
                             Inches(3.11), Inches(0.98))
    except Exception:
        pass
    label(s, 0.80, 2.55, 1.8, 1.5, number, 68, True, 'B9CBDA',
          font='Aptos Display')
    label(s, 2.45, 2.62, 9.0, 0.95, title, 32, True, NAVY,
          font='Aptos Display', anchor='m')
    label(s, 2.48, 3.58, 9.0, 0.42, blurb, 14, False, GREY)
    if items:
        y = 4.22
        for it in items:
            box(s, 2.48, y + 0.075, 0.12, 0.12, fill=ORANGE)
            label(s, 2.76, y - 0.045, 8.8, 0.32, it, 12.5, False, INK)
            y += 0.36
    return s


def s_bullets(prs, title, bullets, kicker=None, note=None, cols=1):
    """bullets: list of str, or (head, sub) tuples."""
    s = _blank(prs); _set_title(s, title, kicker)
    flat = []
    for b in bullets:
        flat.append(b[0] if isinstance(b, tuple) else b)
        if isinstance(b, tuple) and b[1]:
            flat.append(b[1])
    avail = (BOT - 0.45 if note else BOT) - TOP
    if cols == 2:
        half = (len(bullets) + 1) // 2
        groups = [(M, bullets[:half]), (M + CW / 2 + 0.15, bullets[half:])]
        wid = CW / 2 - 0.15
    else:
        groups = [(M, bullets)]
        wid = CW
    fits = {id(g): fit_block(g, avail, int(wid * 8.2), 14, 9.0)
            for _, g in groups if g}
    pt = min(f[0] for f in fits.values())
    gap = min(spread(len(g), avail, fits[id(g)][1], cap=0.26)
              for _, g in groups if g)
    for x0, group in groups:
        if not group:
            continue
        heights = fits[id(group)][2]
        y = TOP
        for b, (hh, hs) in zip(group, heights):
            head, sub = (b if isinstance(b, tuple) else (b, None))
            box(s, x0 + 0.02, y + 0.085, 0.13, 0.13, fill=TEAL)
            label(s, x0 + 0.30, y - 0.045, wid - 0.32, hh, head, pt, bool(sub), NAVY)
            y += hh + 0.04
            if sub:
                label(s, x0 + 0.30, y - 0.02, wid - 0.32, hs, sub, pt - 1.8, False, GREY)
                y += hs + 0.06
            y += 0.10 + gap
    if note:
        _note(s, note)
    return s


def _note(s, note, colour=GOLD, pale='gold', y=None):
    txt = note if isinstance(note, str) else note[1]
    tag = 'NOTE' if isinstance(note, str) else note[0]
    h = 0.44 + 0.20 * (len(txt) // 118)
    y = y if y is not None else BOT - h + 0.06
    box(s, M, y, CW, h, fill=PALE[pale], line_col=colour, line_w=0.75)
    label(s, M + 0.16, y + 0.07, 1.05, 0.26, tag, 9, True, colour)
    label(s, M + 1.20, y + 0.06, CW - 1.38, h - 0.12,
          txt, fit_pt([txt], 11.5, 9, 118, 3), False, NAVY)
    return s


def s_define(prs, term, definition, points=None, kicker='DEFINITION', note=None):
    s = _blank(prs); _set_title(s, term, kicker)
    dh = 0.62 + 0.24 * (len(definition) // 96)
    box(s, M, TOP, CW, dh, fill=PALE['teal'], line_col=TEAL, line_w=1.0)
    box(s, M, TOP, 0.075, dh, fill=TEAL)
    label(s, M + 0.32, TOP + 0.08, CW - 0.55, dh - 0.16, definition,
          fit_pt([definition], 15, 11, 96, 4), False, NAVY, anchor='m', line=1.0)
    y = TOP + dh + 0.26
    if points:
        avail = (BOT - 0.5 if note else BOT) - y
        flat = [p[0] if isinstance(p, tuple) else p for p in points]
        pt, used, heights = fit_block(points, avail, 96, 13, 9.0)
        gap = spread(len(points), avail, used, cap=0.26)
        for pnt, (hh, hs) in zip(points, heights):
            head, sub = (pnt if isinstance(pnt, tuple) else (pnt, None))
            box(s, M + 0.02, y + 0.08, 0.13, 0.13, fill=ORANGE)
            label(s, M + 0.32, y - 0.04, CW - 0.34, hh, head, pt, bool(sub), NAVY)
            y += hh + 0.03
            if sub:
                label(s, M + 0.32, y - 0.02, CW - 0.34, hs, sub, pt - 1.7, False, GREY)
                y += hs + 0.05
            y += 0.09 + gap
    if note:
        _note(s, note)
    return s


def s_two(prs, title, left, right, kicker=None, note=None):
    """left/right: (heading, [items], colour_key)"""
    s = _blank(prs); _set_title(s, title, kicker)
    w = (CW - 0.34) / 2
    bot = (BOT - 0.5) if note else BOT
    for i, (head, items, ckey) in enumerate((left, right)):
        col = {'teal': TEAL, 'orange': ORANGE, 'green': GREEN,
               'red': RED, 'grey': GREY, 'gold': GOLD}[ckey]
        pk = {'teal': 'teal', 'orange': 'orange', 'green': 'green',
              'red': 'red', 'grey': 'grey', 'gold': 'gold'}[ckey]
        x = M + i * (w + 0.34)
        box(s, x, TOP, w, bot - TOP, fill=PALE[pk], line_col=col, line_w=0.75)
        box(s, x, TOP, w, 0.44, fill=col)
        label(s, x + 0.16, TOP + 0.06, w - 0.3, 0.32, head, 12.5, True, WHITE)
        y = TOP + 0.62
        pt = fit_pt(items, 12, 8.8, int(w * 8.6), int((bot - y) / 0.34))
        for it in items:
            mark, txt = ('', it)
            if it[:2] in ('✔ ', '✗ ', '→ ', '• '):
                mark, txt = it[0], it[2:]
            hh = 0.28 + 0.205 * (len(txt) // int(w * 9.0))
            if mark:
                label(s, x + 0.16, y - 0.035, 0.26, 0.3, mark, pt, True,
                      GREEN if mark == '✔' else (RED if mark == '✗' else col))
                label(s, x + 0.45, y - 0.035, w - 0.62, hh, txt, pt, False, NAVY)
            else:
                box(s, x + 0.18, y + 0.075, 0.11, 0.11, fill=col)
                label(s, x + 0.44, y - 0.035, w - 0.62, hh, txt, pt, False, NAVY)
            y += hh + 0.11
    if note:
        _note(s, note)
    return s


def s_table(prs, title, headers, rows, kicker=None, note=None, widths=None,
            emph=None, first_bold=True):
    s = _blank(prs); _set_title(s, title, kicker)
    bot = (BOT - 0.52) if note else BOT
    n = len(headers)
    widths = widths or [1.0 / n] * n
    widths = [w / sum(widths) for w in widths]
    xs, acc = [], M
    for w in widths:
        xs.append((acc, CW * w)); acc += CW * w
    hh = 0.40
    box(s, M, TOP, CW, hh, fill=TEAL)
    for (x, w), h in zip(xs, headers):
        label(s, x + 0.10, TOP + 0.045, w - 0.18, 0.30, h, 10.8, True, WHITE)
    avail = bot - (TOP + hh) - 0.04
    rh = min(0.52, max(0.26, avail / max(1, len(rows))))
    allcells = [c for r in rows for c in r]
    pt = fit_pt(allcells, 11, 8.2, int(min(w for _, w in xs) * 8.8),
                max(1, int(rh / 0.20)))
    y = TOP + hh
    for i, r in enumerate(rows):
        fill = WHITE if i % 2 == 0 else PALE['grey']
        if emph and i in emph:
            fill = PALE['gold']
        box(s, M, y, CW, rh, fill=fill, line_col='D8DEE4', line_w=0.5)
        for j, ((x, w), cell) in enumerate(zip(xs, r)):
            col = NAVY
            txt = cell
            if txt[:2] in ('✔ ', '✗ '):
                col = GREEN if txt[0] == '✔' else RED
            label(s, x + 0.10, y + 0.035, w - 0.18, rh - 0.07, txt, pt,
                  first_bold and j == 0, col, anchor='m')
        y += rh
    if note:
        _note(s, note)
    return s


def s_bank(prs, title, points, kicker='IN A REGULATED BANK', lead=None, ref=None):
    s = _blank(prs); _set_title(s, title, kicker)
    y = TOP
    if lead:
        h = 0.52 + 0.22 * (len(lead) // 104)
        box(s, M, y, CW, h, fill=PALE['gold'], line_col=GOLD, line_w=1.0)
        box(s, M, y, 0.075, h, fill=GOLD)
        label(s, M + 0.30, y + 0.06, CW - 0.5, h - 0.12, lead,
              fit_pt([lead], 14, 10.5, 104, 3), False, NAVY, anchor='m', line=1.0)
        y += h + 0.24
    bot = BOT - (0.42 if ref else 0)
    pt, used_b, heights = fit_block(points, bot - y, 98, 13, 9.0)
    gap_b = spread(len(points), bot - y, used_b, cap=0.22)
    for pnt, (hh, hs) in zip(points, heights):
        head, sub = (pnt if isinstance(pnt, tuple) else (pnt, None))
        box(s, M + 0.02, y + 0.085, 0.14, 0.14, fill=GOLD, shape=MSO_SHAPE.DIAMOND)
        label(s, M + 0.34, y - 0.04, CW - 0.36, hh, head, pt, bool(sub), NAVY)
        y += hh + 0.03
        if sub:
            label(s, M + 0.34, y - 0.02, CW - 0.36, hs, sub, pt - 1.7, False, GREY)
            y += hs + 0.05
        y += 0.10 + gap_b
    if ref:
        label(s, M, BOT - 0.30, CW, 0.28, ref, 9.5, True, GOLD, italic=True)
    return s


def s_lab(prs, lab_no, lab_title, objective, steps, outcome):
    s = _blank(prs); _set_title(s, lab_title, f'HANDS-ON  ·  LAB {lab_no}')
    box(s, M, TOP, CW, 0.72, fill=PALE['green'], line_col=GREEN, line_w=1.0)
    label(s, M + 0.20, TOP + 0.06, 1.25, 0.28, 'OBJECTIVE', 9, True, GREEN)
    label(s, M + 0.20, TOP + 0.30, CW - 0.4, 0.38, objective,
          fit_pt([objective], 13.5, 10.5, 108, 2), False, NAVY)
    y = TOP + 0.96
    label(s, M, y, CW, 0.3, 'YOU WILL', 9.5, True, TEAL); y += 0.34
    avail_l = BOT - 0.95 - y
    pt = fit_pt(steps, 12.5, 10, 100, max(1, int(avail_l / 0.34)))
    used_l = sum(0.30 + 0.21 * (len(st) // 100) + 0.10 for st in steps)
    gap_l = spread(len(steps), avail_l, used_l, cap=0.30)
    for i, st in enumerate(steps, 1):
        box(s, M + 0.02, y + 0.015, 0.26, 0.26, fill=TEAL, shape=MSO_SHAPE.OVAL)
        label(s, M + 0.02, y + 0.035, 0.26, 0.22, str(i), 9, True, WHITE, align='c')
        hh = 0.30 + 0.21 * (len(st) // 100)
        label(s, M + 0.42, y - 0.015, CW - 0.44, hh, st, pt, False, NAVY)
        y += hh + 0.10 + gap_l
    h = 0.52 + 0.2 * (len(outcome) // 108)
    box(s, M, BOT - h, CW, h, fill=PALE['blue'], line_col=TEAL, line_w=0.75)
    label(s, M + 0.20, BOT - h + 0.05, 1.15, 0.26, 'OUTCOME', 9, True, TEAL)
    label(s, M + 1.35, BOT - h + 0.04, CW - 1.55, h - 0.1, outcome,
          fit_pt([outcome], 12, 9.5, 108, 3), False, NAVY, anchor='m')
    return s


def s_check(prs, title, questions, kicker='CHECK YOUR UNDERSTANDING'):
    s = _blank(prs); _set_title(s, title, kicker)
    y = TOP
    pt = fit_pt(questions, 13, 9.5, 104, max(1, int((BOT - y) / 0.40)))
    used_c = sum(0.34 + 0.215 * (len(q) // 104) + 0.16 for q in questions)
    gap_c = spread(len(questions), BOT - y, used_c, cap=0.30)
    for i, q in enumerate(questions, 1):
        hh = 0.34 + 0.215 * (len(q) // 104)
        box(s, M, y, 0.34, hh, fill=PALE['blue'])
        label(s, M, y + 0.02, 0.34, 0.3, str(i), 11, True, TEAL, align='c')
        label(s, M + 0.50, y + 0.005, CW - 0.55, hh, q, pt, False, NAVY)
        y += hh + 0.16 + gap_c
    return s


def s_quote(prs, quote, attrib, kicker=None):
    s = _blank(prs, 6, chrome=False)
    box(s, 0, 0, SW, SH, fill=NAVY)
    box(s, 0, 0, SW, 0.30, fill=LTBLUE)
    box(s, 0, 7.20, SW, 0.30, fill=BLUE)
    label(s, 1.4, 2.35, 10.5, 2.1, '\u201c' + quote + '\u201d',
          fit_pt([quote], 27, 16, 52, 4), True, WHITE, align='c', anchor='m',
          font='Aptos Display', line=1.1)
    label(s, 1.4, 4.75, 10.5, 0.4, '\u2014 ' + attrib, 14, False, '9FC0D8', align='c')
    return s


DIAG_SRC = (1.80, 6.80)        # the band the diagram functions were drawn for


def s_diagram(prs, title, fn, kicker=None, note=None):
    s = _blank(prs); _set_title(s, title, kicker)
    before = len(s.shapes._spTree)
    fn(s)
    floor = (BOT - 0.62) if note else BOT
    _rescale(s, before, DIAG_SRC, (TOP, floor))
    if note:
        _note(s, note)
    return s


def _rescale(slide, from_index, src, dst):
    """Linearly map the vertical extent of shapes added after `from_index`
    from the `src` band into the `dst` band. Lets 22 diagrams drawn for one
    geometry survive a change of template without being rewritten."""
    s0, s1 = src
    d0, d1 = dst
    k = (d1 - d0) / (s1 - s0)
    if abs(k - 1.0) < 0.01 and abs(d0 - s0) < 0.01:
        return
    tree = slide.shapes._spTree
    for el in list(tree)[from_index:]:
        for sh in slide.shapes:
            if sh._element is el:
                try:
                    top = Emu(sh.top).inches
                    hgt = Emu(sh.height).inches
                except Exception:
                    break
                sh.top = Inches(d0 + (top - s0) * k)
                sh.height = Inches(max(0.06, hgt * k))
                break


def s_close(prs, day, title, recap, tomorrow):
    s = _blank(prs, 6, chrome=False)
    box(s, 0, 0, SW, SH, fill=WHITE)
    box(s, 0, 0, SW, 0.30, fill=LTBLUE)
    box(s, 0, 7.20, SW, 0.30, fill=BLUE)
    try:
        s.shapes.add_picture(LOGO, Inches(9.99), Inches(0.52),
                             Inches(3.11), Inches(0.98))
    except Exception:
        pass
    label(s, M, 0.70, 8.8, 0.28, f'DAY {day} · WRAP-UP', 10, True, GREY)
    label(s, M, 1.00, 8.8, 0.62, title, 28, True, NAVY, font='Aptos Display')
    line(s, M, 1.78, M + 2.60, 1.78, LTBLUE, 2.0)
    y = 2.10
    label(s, M, y, CW, 0.28, 'WHAT YOU BUILT TODAY', 10, True, TEAL)
    y += 0.36
    for r in recap:
        box(s, M + 0.02, y + 0.07, 0.12, 0.12, fill=TEAL)
        label(s, M + 0.30, y - 0.05, CW - 0.34, 0.34, r, 12.5, False, INK)
        y += 0.38
    y += 0.16
    h = 6.30 - y
    box(s, M, y, CW, h, fill=PALE['blue'])
    box(s, M, y, 0.07, h, fill=NAVY)
    label(s, M + 0.30, y + 0.10, CW - 0.5, 0.28,
          'TOMORROW' if day < 6 else 'WHERE TO GO NEXT', 10, True, NAVY)
    label(s, M + 0.30, y + 0.42, CW - 0.6, h - 0.52, tomorrow,
          fit_pt([tomorrow], 13, 10.5, 120, 4), False, INK, line=1.12)
    return s



# ═══════════════════════════════════════════════════ engagement slides
EX_STYLE = {
    'predict': dict(label='PREDICT',  accent=NAVY,   pale='blue',
                    lead='Write your answer down BEFORE the reveal.'),
    'compare': dict(label='COMPARE',  accent=TEAL,   pale='teal',
                    lead='Two minutes in pairs. Be ready to defend your choice.'),
    'audit':   dict(label='AUDIT',    accent=PLUM,   pale='plum',
                    lead='Score your OWN organisation. Honestly.'),
    'discuss': dict(label='DISCUSS',  accent=ORANGE, pale='orange',
                    lead='Whole room. There is no single right answer.'),
}


def s_exercise(prs, kind, title, prompt, items, reveal=None, minutes=3):
    """PREDICT / COMPARE / AUDIT / DISCUSS — one per topic keeps a technical
    day participatory instead of a three-hour monologue."""
    st = EX_STYLE[kind]
    acc, pale = st['accent'], st['pale']
    s = _blank(prs); _set_title(s, title, st['label'] + f'  ·  {minutes} MIN')

    box(s, M, TOP, 1.05, 0.34, fill=acc)
    label(s, M, TOP + 0.045, 1.05, 0.26, st['label'], 9.5, True, WHITE, align='c')
    label(s, M + 1.22, TOP + 0.035, CW - 1.3, 0.28, st['lead'], 10.5, True, acc)

    y = TOP + 0.52
    ph = 0.60 + 0.24 * (len(prompt) // 104)
    box(s, M, y, CW, ph, fill=PALE[pale], line_col=acc, line_w=1.0)
    box(s, M, y, 0.075, ph, fill=acc)
    label(s, M + 0.32, y + 0.06, CW - 0.52, ph - 0.12, prompt,
          fit_pt([prompt], 15, 11.5, 104, 3), True, NAVY, anchor='m', line=1.05)
    y += ph + 0.26

    bot = BOT - (0.80 if reveal else 0)
    if items:
        pt = fit_pt(items, 13, 10, 108, max(1, int((bot - y) / 0.36)))
        used = sum(0.32 + 0.21 * (len(i) // 108) + 0.12 for i in items)
        gap = spread(len(items), bot - y, used, cap=0.26)
        for i, it in enumerate(items, 1):
            box(s, M + 0.02, y + 0.02, 0.28, 0.28, fill=acc, shape=MSO_SHAPE.OVAL)
            label(s, M + 0.02, y + 0.04, 0.28, 0.24, str(i), 9.5, True, WHITE, align='c')
            hh = 0.32 + 0.21 * (len(it) // 108)
            label(s, M + 0.46, y - 0.01, CW - 0.5, hh, it, pt, False, INK)
            y += hh + 0.12 + gap

    if reveal:
        label(s, M, BOT - 0.34, CW, 0.30,
              'Answers on the next slide — commit to yours first.',
              11, True, acc, italic=True)
        _reveal_slide(prs, kind, title, prompt, reveal)
    return s


def _reveal_slide(prs, kind, title, prompt, reveal):
    """The answer gets its own slide, so the exercise is a real exercise.
    Q-slide then A-slide, the same pattern as the strategy decks."""
    st = EX_STYLE[kind]
    acc = st['accent']
    s = _blank(prs); _set_title(s, title, st['label'] + '  ·  THE ANSWER')

    ph = 0.54 + 0.22 * (len(prompt) // 112)
    box(s, M, TOP, CW, ph, fill=PALE['grey'])
    box(s, M, TOP, 0.06, ph, fill=GREY)
    label(s, M + 0.28, TOP + 0.05, CW - 0.5, ph - 0.10, prompt,
          fit_pt([prompt], 12.5, 10, 112, 3), False, GREY, anchor='m', italic=True)

    y = TOP + ph + 0.30
    h = BOT - y
    box(s, M, y, CW, h, fill=NAVY)
    box(s, M, y, 0.08, h, fill=acc)
    label(s, M + 0.34, y + 0.18, CW - 0.6, 0.30, 'THE ANSWER', 10, True, LTBLUE)
    label(s, M + 0.60, y + 0.58, CW - 1.2, h - 0.78, reveal,
          fit_pt([reveal], 21, 13, 78, max(2, int((h - 0.9) / 0.42))),
          False, WHITE, anchor='m', line=1.26)
    return s


def s_myth(prs, title, pairs, kicker='MYTH vs REALITY'):
    """pairs: [(myth, reality), ...] — excellent for a post-lunch slot."""
    s = _blank(prs); _set_title(s, title, kicker)
    w = (CW - 0.30) / 2
    label(s, M + 0.10, TOP, w, 0.28, 'WHAT PEOPLE SAY', 10, True, PLUM)
    label(s, M + w + 0.40, TOP, w, 0.28, 'WHAT IS ACTUALLY TRUE', 10, True, TEAL)
    y = TOP + 0.34
    flat = [t for pr in pairs for t in pr]
    pt = fit_pt(flat, 12, 9.2, int(w * 8.6), max(1, int((BOT - y) / (0.52 * len(pairs)))))
    for myth, real in pairs:
        hh = max(0.46, 0.30 + 0.215 * (max(len(myth), len(real)) // int(w * 8.8)) + 0.16)
        box(s, M, y, w, hh, fill=PALE['plum'], line_col=PLUM, line_w=0.6)
        label(s, M + 0.16, y + 0.04, w - 0.3, hh - 0.08, '\u201c' + myth + '\u201d',
              pt, False, INK, anchor='m', italic=True)
        box(s, M + w + 0.30, y, w, hh, fill=PALE['teal'], line_col=TEAL, line_w=0.6)
        label(s, M + w + 0.46, y + 0.04, w - 0.3, hh - 0.08, real,
              pt, False, INK, anchor='m')
        y += hh + 0.14
    return s


# ─────────────────────────────────────────────────────────────── assembly
def new_deck(template):
    from pptx import Presentation
    prs = Presentation(template)
    for i in range(len(prs.slides) - 1, -1, -1):        # strip sample slides
        rid = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(rid)
        del prs.slides._sldIdLst[i]
    return prs


def build(prs, spec):
    """spec: list of (kind, args...) tuples. Returns the presentation."""
    fns = {'title': s_title, 'section': s_section, 'bullets': s_bullets,
           'define': s_define, 'two': s_two, 'table': s_table, 'bank': s_bank,
           'lab': s_lab, 'check': s_check, 'quote': s_quote,
           'diagram': s_diagram, 'close': s_close,
           'predict': lambda p, *a, **k: s_exercise(p, 'predict', *a, **k),
           'compare': lambda p, *a, **k: s_exercise(p, 'compare', *a, **k),
           'audit':   lambda p, *a, **k: s_exercise(p, 'audit', *a, **k),
           'discuss': lambda p, *a, **k: s_exercise(p, 'discuss', *a, **k),
           'myth':    s_myth}
    for item in spec:
        kind, rest = item[0], item[1:]
        note = None
        if isinstance(rest[-1], dict):
            kw = rest[-1]; rest = rest[:-1]
            note = kw.pop('speaker', None)
        else:
            kw = {}
        slide = fns[kind](prs, *rest, **kw)
        if note:
            notes(slide, note)
    return prs
