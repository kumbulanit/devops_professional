# -*- coding: utf-8 -*-
"""Build the six DevOps Professional theory decks.

    python build.py            # build all six
    python build.py 1 3        # build only days 1 and 3

Re-runnable: always overwrites the decks in ../slides/.
"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deckkit as dk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'slides'))
TEMPLATE = os.path.expanduser(
    '~/Documents/devops trainning/NP Template Logo 2.0 (2).pptx')

TITLES = {
    1: 'Day1_DevOps_Foundations',
    2: 'Day2_Version_Control_and_CI',
    3: 'Day3_Containers_with_Docker',
    4: 'Day4_Kubernetes',
    5: 'Day5_IaC_and_Continuous_Delivery',
    6: 'Day6_DevSecOps_Observability_Enterprise',
}


LAB_REF = ('Lab guide: labs/lab-{n}/README.md — it carries the full command list, the '
           'RECOVER block for anyone who has fallen behind, and an Instructor notes section '
           'with the expected duration, the three failures that actually happen in the room, '
           'and a debrief question. Check the run sheet (docs/run-sheet.md) for the time box.')

CHECK_REF = ('Run this as a discussion, not a quiz — the reasoning matters more than the answer. '
             'Worked answers: solutions/. Modules 2-9 self-checks are deliberately open because '
             'they ask about the delegate\'s own organisation.')

SECTION_REF = ('Section divider. Use it to re-set attention and to say explicitly which lab this '
               'block leads into.')

BANK_REF = ('Banking slide. Source: docs/theory/appendix-a-devops-in-a-regulated-bank.md. '
            'Expect push-back here - that is the point. The three arguments this cohort will '
            'raise are segregation of duties (A.3), the CAB (A.4) and change freezes (A.7).')


def _default_notes(prs, spec):
    """Give every lab / check / section / bank slide a useful trainer note if the
    content file did not supply one."""
    for slide, item in zip(prs.slides, spec):
        kind = item[0]
        tf = slide.notes_slide.notes_text_frame
        if tf.text.strip():
            continue
        if kind == 'lab':
            n = str(item[1]).split('+')[0].strip().zfill(2)
            tf.text = LAB_REF.format(n=n)
        elif kind == 'check':
            tf.text = CHECK_REF
        elif kind == 'section':
            tf.text = SECTION_REF
        elif kind == 'bank':
            tf.text = BANK_REF


def build_day(day):
    mod = importlib.import_module(f'content_day{day}')
    spec = getattr(mod, f'DAY{day}')
    prs = dk.new_deck(TEMPLATE)
    dk.build(prs, spec)
    _default_notes(prs, spec)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{TITLES[day]}.pptx')
    n = len(prs.slides._sldIdLst)      # includes auto-added exercise reveal slides
    prs.save(path)
    return path, n


if __name__ == '__main__':
    days = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5, 6]
    total = 0
    for d in days:
        try:
            path, n = build_day(d)
            total += n
            print(f'  Day {d}: {n:3d} slides  →  {os.path.basename(path)}')
        except ModuleNotFoundError:
            print(f'  Day {d}: content_day{d}.py not written yet — skipped')
    print(f'  {total} slides total')
