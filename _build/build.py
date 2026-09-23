# -*- coding: utf-8 -*-
"""Build the six DevOps Professional theory decks.

    python build.py            # build all six (and the two per-lab advanced decks)
    python build.py 1 3        # build only days 1 and 3
    python build.py labs       # build only the per-lab advanced decks

Re-runnable: always overwrites the decks in ../slides/. The two ADVANCED decks are
written into the lab folders they belong to, beside their README pages.
"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deckkit as dk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'slides'))
TEMPLATE = os.path.expanduser(
    '~/Documents/devops trainning/NP Template Logo 2.0 (2).pptx')

LABS = os.path.abspath(os.path.join(HERE, '..', 'labs'))

# Optional advanced decks, written beside the lab pages they support: day -> entries.
LAB_DECKS = {
    2: [('LAB03_ADVANCED', 'lab-03-branching-and-collaboration', 'Lab03A_Advanced_Git'),
        ('LAB04_ADVANCED', 'lab-04-github-actions-ci', 'Lab04AB_Advanced_Pipelines')],
    3: [('LAB06A_ADVANCED', 'lab-06-docker-images', 'Lab06A_Advanced_Builds'),
        ('LAB07A_ADVANCED', 'lab-07-docker-compose-stack', 'Lab07A_Advanced_Compose'),
        ('LAB08A_ADVANCED', 'lab-08-docker-networking-volumes', 'Lab08A_Advanced_Hardening')],
    4: [('LAB10A_ADVANCED', 'lab-10-k8s-deploy-app', 'Lab10A_Advanced_Debugging'),
        ('LAB11A_ADVANCED', 'lab-11-k8s-config-secrets-storage', 'Lab11A_Advanced_Access_and_Storage'),
        ('LAB12A_ADVANCED', 'lab-12-k8s-ingress-scaling', 'Lab12A_Advanced_Scaling')],
}

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

DEMO_REF = ('Live demo. Type it, do not paste it — the pauses are where people learn. If the environment '
            'misbehaves, walk through the expected output already on the slide and carry on; the same steps '
            'are in the lab README for everyone to run after class.')

CODE_REF = ('Walk the code top to bottom. The numbered points on the right are the talk track; the full, '
            'runnable version is in the matching lab README.')

BANK_REF = ('Banking slide. Source: docs/theory/appendix-a-devops-in-a-regulated-bank.md. '
            'Expect push-back here - that is the point. The three arguments this cohort will '
            'raise are segregation of duties (A.3), the CAB (A.4) and change freezes (A.7).')


def _default_notes(prs, spec):
    """Give every lab / check / section / bank / demo / code slide a useful trainer note
    if the content file did not supply one. Pairs come from the build itself: exercises
    insert a reveal slide, so zipping slides with the spec would drift after the first one."""
    for slide, item in dk.LAST_PAIRS:
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
        elif kind == 'demo':
            tf.text = DEMO_REF
        elif kind == 'code':
            tf.text = CODE_REF


def _build_one(day, spec, filename, outdir=None):
    prs = dk.new_deck(TEMPLATE)
    dk.build(prs, spec)
    _default_notes(prs, spec)
    outdir = outdir or OUT
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f'{filename}.pptx')
    n = len(prs.slides._sldIdLst)      # includes auto-added exercise reveal slides
    if dk.OVERFULL:
        print(f'  Day {day}: {len(dk.OVERFULL)} over-full block(s) in {filename}:')
        for w in dk.OVERFULL:
            print('     -', w)
        dk.OVERFULL.clear()
    prs.save(path)
    return path, n


def build_day(day):
    """Build the taught deck. If the content file also defines DAY<n>_EXTRA, build that too as a
    separate optional reading deck (<title>_Going_Further.pptx), so the taught deck stays lean."""
    mod = importlib.import_module(f'content_day{day}')
    path, n = _build_one(day, getattr(mod, f'DAY{day}'), TITLES[day])
    extra = getattr(mod, f'DAY{day}_EXTRA', None)
    if extra:
        xpath, xn = _build_one(day, extra, f'{TITLES[day]}_Going_Further')
        print(f'  Day {day}: {xn:3d} slides  →  {os.path.basename(xpath)}  (optional reading)')
    build_lab_decks(day)
    return path, n


def build_lab_decks(day=None):
    """Build the per-lab ADVANCED decks into their lab folders. No day: every day that has some."""
    for d in ([day] if day is not None else sorted(LAB_DECKS)):
        for attr, folder, filename in LAB_DECKS.get(d, []):
            try:
                mod = importlib.import_module(f'content_day{d}')
            except ModuleNotFoundError:
                continue
            spec = getattr(mod, attr, None)
            if not spec:
                continue
            out = os.path.join(LABS, folder)
            path, n = _build_one(d, spec, filename, outdir=out)
            print(f'  Lab deck: {n:3d} slides  →  labs/{folder}/{os.path.basename(path)}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == 'labs':
        build_lab_decks()
        raise SystemExit(0)
    days = [int(a) for a in args] or [1, 2, 3, 4, 5, 6]
    total = 0
    for d in days:
        try:
            path, n = build_day(d)
            total += n
            print(f'  Day {d}: {n:3d} slides  →  {os.path.basename(path)}')
        except ModuleNotFoundError:
            print(f'  Day {d}: content_day{d}.py not written yet — skipped')
    print(f'  {total} slides total')
