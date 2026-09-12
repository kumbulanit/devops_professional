# -*- coding: utf-8 -*-
"""Native-vector diagrams. Every one is drawn as PowerPoint shapes - no images -
so they stay crisp, editable and recolourable in the room."""
from pptx.enum.shapes import MSO_SHAPE
from deckkit import (box, label, line, arrow, chev, NAVY, TEAL, ORANGE, GREEN,
                     LTBLUE, PLUM, GOLD, RED, GREY, WHITE, PALE, M, CW, TOP, BOT)

# ══════════════════════════════════════════════════════ DAY 1
def wall_of_confusion(s):
    box(s, M, 1.95, 4.9, 3.5, fill=PALE['blue'], line_col=TEAL)
    label(s, M, 2.08, 4.9, 0.35, 'DEVELOPMENT', 13, True, TEAL, align='c')
    for i, t in enumerate(['Rewarded for CHANGE', 'Ships features', 'Owns the backlog',
                           '"It works on my machine"']):
        label(s, M + 0.30, 2.60 + i * 0.46, 4.3, 0.36, '· ' + t, 11.5, False, NAVY)
    x2 = M + CW - 4.9
    box(s, x2, 1.95, 4.9, 3.5, fill=PALE['orange'], line_col=ORANGE)
    label(s, x2, 2.08, 4.9, 0.35, 'OPERATIONS', 13, True, ORANGE, align='c')
    for i, t in enumerate(['Rewarded for STABILITY', 'Carries the pager', 'Owns uptime',
                           '"Then don\'t ship it"']):
        label(s, x2 + 0.30, 2.60 + i * 0.46, 4.3, 0.36, '· ' + t, 11.5, False, NAVY)
    bx = M + 4.9 + 0.12
    bw = CW - 9.8 - 0.24
    box(s, bx, 1.80, bw, 3.80, fill='C9CED4')
    for yy in range(6):
        label(s, bx, 2.05 + yy * 0.58, bw, 0.4, '▚', 20, True, '9AA3AC', align='c')
    label(s, bx - 0.55, 5.72, bw + 1.1, 0.36, 'THE WALL OF CONFUSION', 11.5, True, '6B7580', align='c')
    box(s, M, 6.08, CW, 0.62, fill=PALE['green'], line_col=GREEN)
    label(s, M + 0.2, 6.16, CW - 0.4, 0.46,
          'DevOps removes the wall by making the SAME team responsible for building it and running it —'
          ' shared goals, shared pager, shared definition of done.', 11.5, False, NAVY)


def calms(s):
    items = [('C', 'CULTURE', 'Shared ownership,\nblameless learning', TEAL),
             ('A', 'AUTOMATION', 'CI/CD, IaC,\ntesting, self-service', LTBLUE),
             ('L', 'LEAN', 'Small batches,\nlimit WIP, flow', GREEN),
             ('M', 'MEASUREMENT', 'DORA metrics,\nSLOs, telemetry', ORANGE),
             ('S', 'SHARING', 'Runbooks, post-mortems,\ncross-team reuse', PLUM)]
    w, gap = 2.12, 0.23
    x = M + (CW - (5 * w + 4 * gap)) / 2
    for letter, name, body, col in items:
        box(s, x, 2.00, w, 0.86, fill=col)
        label(s, x, 2.06, w, 0.7, letter, 38, True, WHITE, align='c', font='Aptos Display')
        box(s, x, 2.86, w, 1.62, fill=PALE['grey'], line_col=col, line_w=0.75)
        label(s, x + 0.08, 3.00, w - 0.16, 0.34, name, 11.5, True, col, align='c')
        label(s, x + 0.10, 3.42, w - 0.20, 0.95, body, 10.5, False, NAVY, align='c', anchor='m')
        x += w + gap
    box(s, M, 4.95, CW, 1.05, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 5.05, CW - 0.44, 0.85,
          'CALMS is a diagnostic, not a checklist. Score each dimension 1–5 and invest in the LOWEST — '
          'not the most interesting. Most organisations score highest on Automation and lowest on '
          'Culture or Measurement, which is exactly why buying tools alone never works.',
          11.5, False, NAVY)


def lifecycle(s):
    stages = [('PLAN', TEAL), ('CODE', TEAL), ('BUILD', LTBLUE), ('TEST', LTBLUE),
              ('RELEASE', ORANGE), ('DEPLOY', ORANGE), ('OPERATE', GREEN), ('MONITOR', GREEN)]
    w = 1.30
    x = M + 0.15
    for i, (name, col) in enumerate(stages):
        chev(s, x, 2.35, w + 0.22, 0.84, name, col, pt=10.5)
        x += w
    label(s, M, 3.42, CW, 0.3, '◄────────────────────  continuous feedback  ────────────────────►',
          11, True, GREY, align='c')
    box(s, M, 3.95, CW, 0.92, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.20, 4.04, CW - 0.4, 0.74,
          'DEV SIDE (plan → test): shorten the loop, make feedback fast and cheap.   '
          'OPS SIDE (release → monitor): make change safe, observable and reversible.', 12, False, NAVY)
    pairs = [('Lab 02–03', 'source control'), ('Lab 04–05', 'CI'), ('Lab 06–07', 'containers'),
             ('Lab 10–12', 'Kubernetes'), ('Lab 15–16', 'delivery'), ('Lab 18', 'monitoring')]
    x = M
    w2 = CW / len(pairs)
    for a, b in pairs:
        box(s, x + 0.05, 5.10, w2 - 0.10, 0.72, fill=PALE['grey'], line_col='C9D2DA', line_w=0.5)
        label(s, x + 0.05, 5.18, w2 - 0.10, 0.28, a, 10.5, True, TEAL, align='c')
        label(s, x + 0.05, 5.46, w2 - 0.10, 0.28, b, 10, False, GREY, align='c')
        x += w2
    label(s, M, 6.00, CW, 0.3, 'This course walks the whole loop, in order.', 11.5, True, NAVY, align='c')


def flow_efficiency(s):
    label(s, M, 1.85, CW, 0.3, 'A typical enterprise change: 22 h of work, 340 h of lead time',
          13, True, NAVY)
    y = 2.35
    total = 340.0
    segs = [('work', 22, TEAL), ('waiting in queues', 318, 'D3D9DF')]
    x = M
    for name, val, col in segs:
        w = CW * val / total
        box(s, x, y, w, 0.72, fill=col)
        if w > 1.2:
            label(s, x, y + 0.17, w, 0.4, f'{name}  {val} h', 12, True,
                  WHITE if col == TEAL else '4A5560', align='c')
        x += w
    label(s, M, y + 0.82, CW, 0.3, '│◄─ 6.5 % ─►│', 11, True, TEAL)
    box(s, M, 3.62, 5.55, 1.55, fill=PALE['red'], line_col=RED)
    label(s, M + 0.2, 3.72, 5.2, 0.3, 'WHERE TEAMS USUALLY INVEST', 10.5, True, RED)
    label(s, M + 0.2, 4.05, 5.2, 1.0,
          'Faster builds · better IDEs · more developers.\nAll of it attacks the 6.5 %.',
          12, False, NAVY)
    x2 = M + CW - 5.55
    box(s, x2, 3.62, 5.55, 1.55, fill=PALE['green'], line_col=GREEN)
    label(s, x2 + 0.2, 3.72, 5.2, 0.3, 'WHERE THE TIME ACTUALLY IS', 10.5, True, GREEN)
    label(s, x2 + 0.2, 4.05, 5.2, 1.0,
          'Approval queues · hand-offs · environment waits ·\nreview latency · release windows.',
          12, False, NAVY)
    box(s, M, 5.42, CW, 1.24, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 5.52, CW - 0.44, 1.05,
          "LITTLE'S LAW   ·   Lead Time = WIP ÷ Throughput\n"
          'WIP 30, throughput 3/week → 10 weeks.  Cut WIP to 10 → 3.3 weeks.\n'
          'A 67 % reduction in lead time with no new tools, no new people and no process redesign.',
          12.5, False, NAVY, line=1.15)


def dora_quadrant(s):
    box(s, M + 0.6, 1.95, 5.1, 2.05, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.8, 2.05, 4.7, 0.32, 'THROUGHPUT  (speed)', 11.5, True, TEAL)
    label(s, M + 0.8, 2.44, 4.7, 1.4,
          '1 · Deployment frequency\n     How often you deploy to production\n\n'
          '2 · Lead time for change\n     Commit → running in production', 12, False, NAVY, line=1.05)
    x2 = M + CW - 5.7
    box(s, x2, 1.95, 5.1, 2.05, fill=PALE['green'], line_col=GREEN)
    label(s, x2 + 0.2, 2.05, 4.7, 0.32, 'STABILITY  (quality)', 11.5, True, GREEN)
    label(s, x2 + 0.2, 2.44, 4.7, 1.4,
          '3 · Change failure rate\n     % of deploys needing remediation\n\n'
          '4 · Failed-deployment recovery\n     How long to restore service', 12, False, NAVY, line=1.05)
    arrow(s, M + 5.85, 2.75, 0.55, 0.42, GREY, 'right')
    arrow(s, M + 5.85, 3.25, 0.55, 0.42, GREY, 'left')
    box(s, M, 4.28, CW, 0.78, fill=NAVY)
    label(s, M + 0.2, 4.38, CW - 0.4, 0.6,
          'THE CENTRAL FINDING:  these do NOT trade off.  Elite performers are better at BOTH — '
          'because speed comes FROM the practices that create stability.', 13, True, WHITE)
    rows = [('Elite', 'On demand', '< 1 hour', '0–15 %', '< 1 hour', GREEN),
            ('High', 'Weekly–monthly', '1 day–1 week', '16–30 %', '< 1 day', LTBLUE),
            ('Medium', 'Monthly–6 mo', '1–6 months', '16–30 %', '1 day–1 week', ORANGE),
            ('Low', '> 6 months', '> 6 months', '16–30 %', '> 6 months', RED)]
    hdr = ['', 'Deploy freq.', 'Lead time', 'Change fail', 'Recovery']
    ws = [1.5, 2.6, 2.5, 2.3, 2.6]
    x = M
    for w, h in zip(ws, hdr):
        label(s, x + 0.06, 5.20, w, 0.28, h, 10, True, GREY)
        x += w
    y = 5.48
    for name, a, b, c, d, col in rows:
        x = M
        box(s, M, y, CW, 0.31, fill=WHITE, line_col='DDE2E7', line_w=0.5)
        box(s, M, y, 0.07, 0.31, fill=col)
        for w, v, bold in zip(ws, [name, a, b, c, d], [True, False, False, False, False]):
            label(s, x + 0.14, y + 0.015, w - 0.16, 0.28, v, 10.5, bold,
                  col if bold else NAVY, anchor='m')
            x += w
        y += 0.33


# ══════════════════════════════════════════════════════ DAY 2
def git_areas(s):
    names = [('WORKING TREE', 'the files you edit', TEAL),
             ('INDEX / STAGING', 'the proposed next commit', LTBLUE),
             ('LOCAL REPOSITORY', 'committed history (.git)', GREEN),
             ('REMOTE', 'origin, on GitHub', PLUM)]
    w = 2.62
    gap = (CW - 4 * w) / 3
    x = M
    for n, sub, col in names:
        box(s, x, 2.10, w, 1.15, fill=PALE['grey'], line_col=col, line_w=1.0)
        label(s, x + 0.08, 2.24, w - 0.16, 0.34, n, 11.5, True, col, align='c')
        label(s, x + 0.08, 2.62, w - 0.16, 0.5, sub, 10.5, False, GREY, align='c')
        x += w + gap
    fwd = ['git add', 'git commit', 'git push']
    bwd = ['git restore', 'git restore --staged', 'git fetch / pull']
    for i in range(3):
        x0 = M + (i + 1) * w + i * gap
        arrow(s, x0 + 0.04, 2.36, gap - 0.08, 0.26, TEAL, 'right')
        label(s, x0 - 0.45, 2.06, gap + 0.9, 0.26, fwd[i], 9.5, True, TEAL, align='c')
        arrow(s, x0 + 0.04, 2.90, gap - 0.08, 0.26, GREY, 'left')
        label(s, x0 - 0.55, 3.14, gap + 1.1, 0.26, bwd[i], 9, False, GREY, align='c')
    box(s, M, 3.85, CW, 1.35, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 3.95, CW - 0.44, 0.3, 'THE FOUR OBJECT TYPES', 10.5, True, TEAL)
    objs = [('blob', 'file contents'), ('tree', 'a directory listing'),
            ('commit', 'a tree + parent(s) + author + message'), ('tag', 'a named pointer')]
    x = M + 0.25
    for n, d in objs:
        box(s, x, 4.32, 2.55, 0.72, fill=WHITE, line_col='C9D2DA', line_w=0.5)
        label(s, x + 0.1, 4.40, 2.35, 0.28, n, 11.5, True, NAVY)
        label(s, x + 0.1, 4.68, 2.35, 0.3, d, 9.5, False, GREY)
        x += 2.72
    box(s, M, 5.48, CW, 1.15, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 5.58, CW - 0.44, 0.95,
          'Every object is addressed by the SHA-1/SHA-256 of its contents. Change one byte anywhere and '
          'every hash from that point forward changes.\nThat is why git history is tamper-evident — and why, '
          'in a bank, the commit graph is admissible audit evidence.', 12, False, NAVY, line=1.12)


def branching_compare(s):
    cols = [('TRUNK-BASED', 'Hours', ['Everyone commits to main', 'Branches live < 1 day',
                                      'Feature flags hide WIP', 'Highest DORA correlation'], GREEN),
            ('GITHUB FLOW', 'Days', ['One branch per change', 'PR → review → squash merge',
                                     'main is always deployable', 'What this course uses'], TEAL),
            ('GITFLOW', 'Weeks', ['develop + release + hotfix', 'Heavy, many long branches',
                                  'Merge pain is routine', 'Only for versioned releases'], ORANGE)]
    w = (CW - 0.5) / 3
    x = M
    for name, life, pts, col in cols:
        box(s, x, 1.95, w, 3.35, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 1.95, w, 0.46, fill=col)
        label(s, x + 0.1, 2.02, w - 0.2, 0.32, name, 12.5, True, WHITE, align='c')
        label(s, x + 0.1, 2.52, w - 0.2, 0.3, f'branch lifetime: {life}', 10.5, True, col, align='c')
        y = 2.95
        for p in pts:
            box(s, x + 0.18, y + 0.07, 0.10, 0.10, fill=col)
            label(s, x + 0.40, y - 0.04, w - 0.58, 0.55, p, 11, False, NAVY)
            y += 0.52
        x += w + 0.25
    box(s, M, 5.50, CW, 1.15, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 5.60, CW - 0.44, 0.95,
          'The DORA research is consistent: fewer, shorter-lived branches correlate with higher performance. '
          'The mechanism is batch size — a branch that lives three weeks is three weeks of unintegrated, '
          'untested divergence, and its merge is the riskiest event of the sprint.', 12, False, NAVY, line=1.12)


def ci_pipeline(s):
    stages = [('COMMIT', '< 5 min', ['lint', 'unit tests', 'SAST + secrets', 'BUILD IMAGE ONCE'], TEAL),
              ('ACCEPTANCE', '< 20 min', ['integration', 'contract tests', 'image scan', 'SBOM'], LTBLUE),
              ('STAGING', 'prod-like', ['smoke tests', 'performance', 'DAST'], ORANGE),
              ('PRODUCTION', 'gated', ['rolling / canary', 'smoke test', 'watch SLOs'], GREEN)]
    w = (CW - 3 * 0.42) / 4
    x = M
    for i, (name, sub, items, col) in enumerate(stages):
        box(s, x, 2.00, w, 2.65, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 2.00, w, 0.44, fill=col)
        label(s, x + 0.08, 2.06, w - 0.16, 0.32, name, 11.5, True, WHITE, align='c')
        label(s, x + 0.08, 2.52, w - 0.16, 0.28, sub, 10, True, col, align='c')
        y = 2.88
        for it in items:
            label(s, x + 0.18, y, w - 0.3, 0.32, '· ' + it, 11, False, NAVY)
            y += 0.36
        if i < 3:
            arrow(s, x + w + 0.06, 3.05, 0.30, 0.34, GREY, 'right')
        x += w + 0.42
    box(s, M, 4.95, CW, 0.62, fill=NAVY)
    label(s, M + 0.2, 5.04, CW - 0.4, 0.44,
          'THE SAME IMAGE DIGEST FLOWS ALL THE WAY THROUGH   ·   sha256:9f3e2a…   ·   never rebuilt, only re-tagged',
          12, True, WHITE, align='c')
    box(s, M, 5.78, CW, 0.88, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 5.87, CW - 0.44, 0.7,
          'Rebuilding per environment invalidates every earlier test: you tested one binary and shipped another. '
          'In a regulated change record, "what exactly was tested?" must have one answer — a digest.',
          12, False, NAVY, line=1.1)


# ══════════════════════════════════════════════════════ DAY 3
def vm_vs_container(s):
    box(s, M, 1.95, 5.45, 3.55, fill=PALE['orange'], line_col=ORANGE)
    label(s, M, 2.04, 5.45, 0.34, 'VIRTUAL MACHINES', 12.5, True, ORANGE, align='c')
    lay = [('App A   App B   App C', WHITE, 0.40),
           ('Guest OS  Guest OS  Guest OS', 'F6D9C4', 0.55),
           ('Hypervisor', 'EFC4A4', 0.42),
           ('Host operating system', 'E9B78C', 0.42),
           ('Physical hardware', 'DFA876', 0.42)]
    y = 2.48
    for t, c, h in lay:
        box(s, M + 0.22, y, 5.0, h, fill=c, line_col='D9A87C', line_w=0.5)
        label(s, M + 0.22, y + (h - 0.26) / 2, 5.0, 0.26, t, 10.5, False, NAVY, align='c')
        y += h + 0.05
    label(s, M + 0.22, 5.02, 5.0, 0.3, 'GB each  ·  boots in minutes', 10.5, True, ORANGE, align='c')
    x2 = M + CW - 5.45
    box(s, x2, 1.95, 5.45, 3.55, fill=PALE['green'], line_col=GREEN)
    label(s, x2, 2.04, 5.45, 0.34, 'CONTAINERS', 12.5, True, GREEN, align='c')
    lay2 = [('App A   App B   App C', WHITE, 0.40),
            ('Container runtime', 'CFE6D2', 0.42),
            ('Host operating system  (SHARED KERNEL)', 'B9DCC2', 0.55),
            ('Physical hardware', 'A6D2B2', 0.42)]
    y = 2.48
    for t, c, h in lay2:
        box(s, x2 + 0.22, y, 5.0, h, fill=c, line_col='9CC7AB', line_w=0.5)
        label(s, x2 + 0.22, y + (h - 0.26) / 2, 5.0, 0.26, t, 10.5, False, NAVY, align='c')
        y += h + 0.05
    label(s, x2 + 0.22, 5.02, 5.0, 0.3, 'MB each  ·  starts in milliseconds', 10.5, True, GREEN, align='c')
    box(s, M, 5.72, CW, 0.95, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 5.80, CW - 0.44, 0.78,
          'A container is a PROCESS on the host kernel, isolated by namespaces (what it can see) and '
          'limited by cgroups (what it can use). It is not a small VM — there is no guest kernel, which is '
          'both why it is fast and why kernel-level isolation is weaker.', 12, False, NAVY, line=1.1)


def image_layers(s):
    label(s, M, 1.85, 5.6, 0.3, 'NAIVE BUILD  ~1.1 GB', 12, True, RED)
    lay = [('CMD python -m src.app', 'F3C9C4', 0.34),
           ('RUN pip install -r requirements-dev.txt', 'F0BDB6', 0.42),
           ('COPY . .   ← invalidates cache on ANY change', 'EBB0A8', 0.42),
           ('FROM python:3.12   (~1 GB)', 'E49E94', 0.86)]
    y = 2.22
    for t, c, h in lay:
        box(s, M, y, 5.6, h, fill=c, line_col='D08A7E', line_w=0.5)
        label(s, M + 0.12, y + (h - 0.26) / 2, 5.4, 0.26, t, 10, False, NAVY)
        y += h + 0.04
    x2 = M + CW - 5.6
    label(s, x2, 1.85, 5.6, 0.3, 'MULTI-STAGE  ~150 MB', 12, True, GREEN)
    lay2 = [('CMD gunicorn … wsgi:app', 'CDE6D5', 0.30),
            ('USER 10001   ← drops root', 'BFE0CA', 0.30),
            ('COPY src/', 'B2DBC0', 0.30),
            ('COPY --from=builder /install', 'A5D6B6', 0.34),
            ('FROM python:3.12-slim  (~150 MB)', '92CDA6', 0.50)]
    y = 2.22
    for t, c, h in lay2:
        box(s, x2, y, 5.6, h, fill=c, line_col='79B790', line_w=0.5)
        label(s, x2 + 0.12, y + (h - 0.24) / 2, 5.4, 0.24, t, 10, False, NAVY)
        y += h + 0.04
    box(s, x2, y + 0.06, 5.6, 0.46, fill=PALE['grey'], line_col='C9D2DA', line_w=0.5)
    label(s, x2 + 0.12, y + 0.16, 5.4, 0.3, 'builder stage — compilers, source — DISCARDED',
          10, True, GREY, italic=True)
    box(s, M, 4.62, CW, 0.95, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 4.71, CW - 0.44, 0.78,
          'ORDER DEPENDENCIES FIRST.  COPY requirements.txt → RUN pip install → COPY src/.  '
          'A source change then rebuilds only the last layer: 3 seconds instead of 3 minutes, '
          'on every commit, for every engineer.', 12, False, NAVY, line=1.1)
    box(s, M, 5.72, CW, 0.95, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 5.81, CW - 0.44, 0.78,
          'Every layer is immutable and content-addressed. `docker history` shows every ARG and ENV — '
          'which is exactly why a secret passed as a build argument is a secret published to anyone '
          'who can pull the image.', 12, False, NAVY, line=1.1)


def compose_stack(s):
    box(s, M + 0.9, 2.05, CW - 1.8, 3.15, fill='F7F9FB', line_col='C9D2DA', line_w=1.0)
    label(s, M + 1.1, 2.13, 5.0, 0.3, 'user-defined network  "paytrack-net"', 10.5, True, GREY)
    tiers = [('nginx  :80', 'reverse proxy · rate limit · TLS', TEAL, 2.55),
             ('paytrack-api  :8080   × 2', 'the application — no published port', LTBLUE, 3.40),
             ('postgres  :5432', 'the ledger — bound to 127.0.0.1 only', GREEN, 4.25)]
    for name, sub, col, y in tiers:
        box(s, M + 1.6, y, 6.4, 0.68, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, M + 1.6, y, 0.08, 0.68, fill=col)
        label(s, M + 1.85, y + 0.06, 4.0, 0.3, name, 12, True, NAVY)
        label(s, M + 1.85, y + 0.34, 6.0, 0.28, sub, 10, False, GREY)
    for y in (3.23, 4.08):
        arrow(s, M + 4.6, y, 0.3, 0.17, GREY, 'down')
    box(s, M + 8.35, 4.25, 2.1, 0.68, fill=PALE['gold'], line_col=GOLD, line_w=1.0)
    label(s, M + 8.45, 4.34, 1.9, 0.5, 'volume\n"pgdata"', 10.5, True, GOLD, align='c')
    arrow(s, M + 8.05, 4.47, 0.26, 0.16, GOLD, 'right')
    label(s, M, 5.35, CW, 0.3, 'DNS by service name — "api", "db" — never an IP address',
          12, True, TEAL, align='c')
    box(s, M, 5.75, CW, 0.92, fill=PALE['red'], line_col=RED)
    label(s, M + 0.22, 5.84, CW - 0.44, 0.74,
          'depends_on: { db: { condition: service_healthy } } — wait for READY, not merely STARTED. '
          'Without it the API races the database on every start, and the usual "fix" is a sleep 10 in an '
          'entrypoint script.', 12, False, NAVY, line=1.1)


# ══════════════════════════════════════════════════════ DAY 4
def k8s_architecture(s):
    box(s, M, 1.92, 5.3, 3.25, fill=PALE['blue'], line_col=TEAL, line_w=1.0)
    label(s, M, 2.00, 5.3, 0.32, 'CONTROL PLANE', 12.5, True, TEAL, align='c')
    cp = [('kube-apiserver', 'the ONLY way in — authn, authz, admission'),
          ('etcd', 'the cluster state store'),
          ('kube-scheduler', 'decides WHICH node'),
          ('controller-manager', 'the reconciliation loops')]
    y = 2.44
    for n, d in cp:
        box(s, M + 0.20, y, 4.9, 0.60, fill=WHITE, line_col='C4D4E0', line_w=0.5)
        label(s, M + 0.32, y + 0.05, 4.7, 0.26, n, 11, True, NAVY)
        label(s, M + 0.32, y + 0.31, 4.7, 0.26, d, 9.5, False, GREY)
        y += 0.66
    x2 = M + CW - 5.75
    box(s, x2, 1.92, 5.75, 3.25, fill=PALE['green'], line_col=GREEN, line_w=1.0)
    label(s, x2, 2.00, 5.75, 0.32, 'WORKER NODES', 12.5, True, GREEN, align='c')
    for i in range(2):
        xx = x2 + 0.20 + i * 2.75
        box(s, xx, 2.44, 2.6, 2.55, fill=WHITE, line_col='A9CDB5', line_w=0.75)
        label(s, xx, 2.52, 2.6, 0.26, f'node-{i+1}', 10.5, True, GREEN, align='c')
        for j, (n, d) in enumerate([('kubelet', 'runs the pods'),
                                    ('kube-proxy', 'service routing'),
                                    ('container runtime', 'containerd')]):
            box(s, xx + 0.12, 2.84 + j * 0.52, 2.36, 0.46, fill=PALE['grey'], line_col='D0D9E0', line_w=0.4)
            label(s, xx + 0.2, 2.88 + j * 0.52, 2.2, 0.22, n, 9.5, True, NAVY)
            label(s, xx + 0.2, 3.08 + j * 0.52, 2.2, 0.22, d, 8.5, False, GREY)
        box(s, xx + 0.12, 4.42, 2.36, 0.44, fill=PALE['blue'], line_col=TEAL, line_w=0.5)
        label(s, xx + 0.12, 4.50, 2.36, 0.28, 'pods', 10, True, TEAL, align='c')
    arrow(s, M + 5.38, 3.30, 0.30, 0.28, GREY, 'right')
    box(s, M, 5.32, CW, 0.66, fill=NAVY)
    label(s, M + 0.2, 5.41, CW - 0.4, 0.48,
          'THE RECONCILIATION LOOP:   observe actual  →  compare with desired  →  close the gap  →  repeat, forever',
          12.5, True, WHITE, align='c', anchor='m')
    box(s, M, 6.08, CW, 0.62, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 6.16, CW - 0.44, 0.46,
          'You never tell Kubernetes what to DO. You tell it what you WANT, and controllers close the gap — '
          'which is why a deleted pod comes back and a failed node self-heals.', 11.5, False, NAVY)


def k8s_objects(s):
    chain = [('Deployment', 'you write this', TEAL),
             ('ReplicaSet', 'created per revision', LTBLUE),
             ('Pod', 'the scheduled unit', GREEN)]
    x = M + 0.3
    for i, (n, d, col) in enumerate(chain):
        box(s, x, 2.05, 3.2, 0.92, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 2.05, 3.2, 0.32, fill=col)
        label(s, x, 2.09, 3.2, 0.26, n, 11.5, True, WHITE, align='c')
        label(s, x + 0.1, 2.48, 3.0, 0.4, d, 10.5, False, NAVY, align='c')
        if i < 2:
            arrow(s, x + 3.28, 2.38, 0.42, 0.28, GREY, 'right')
        x += 3.9
    box(s, M, 3.25, CW, 0.62, fill=PALE['orange'], line_col=ORANGE)
    label(s, M + 0.22, 3.34, CW - 0.44, 0.46,
          'A rollout creates a NEW ReplicaSet and scales the old one to zero — it is not deleted. '
          'That surviving ReplicaSet is what makes `kubectl rollout undo` take seconds.', 11.5, False, NAVY)
    label(s, M, 4.02, CW, 0.3, 'AND THE OBJECTS AROUND IT', 10.5, True, TEAL)
    grid = [('Service', 'stable VIP + DNS in front of changing pods'),
            ('Ingress', 'HTTP routing (needs a controller pod)'),
            ('ConfigMap', 'non-confidential configuration'),
            ('Secret', 'credentials — base64, NOT encrypted by default'),
            ('PVC / PV', 'storage that outlives the pod'),
            ('HPA', 'scales replicas on metrics (needs CPU requests)'),
            ('PodDisruptionBudget', 'minimum availability during drains'),
            ('NetworkPolicy', 'pod-to-pod firewall (needs a capable CNI)')]
    for i, (n, d) in enumerate(grid):
        xx = M + (i % 2) * (CW / 2 + 0.1)
        yy = 4.40 + (i // 2) * 0.58
        box(s, xx, yy, CW / 2 - 0.1, 0.50, fill=WHITE, line_col='D3DAE1', line_w=0.5)
        box(s, xx, yy, 0.06, 0.50, fill=TEAL)
        label(s, xx + 0.18, yy + 0.03, 2.3, 0.26, n, 10.5, True, NAVY)
        label(s, xx + 2.45, yy + 0.04, CW / 2 - 2.6, 0.42, d, 9.8, False, GREY)


def probes(s):
    rows = [('startupProbe', '/health', 'Has it finished booting?',
             'Holds the other two off. Lets a slow start take 60 s without weakening liveness.', LTBLUE),
            ('livenessProbe', '/health', 'Is it wedged?',
             'FAILING ⇒ RESTART the container. Must have NO external dependency.', ORANGE),
            ('readinessProbe', '/ready', 'Can it serve traffic?',
             'FAILING ⇒ removed from the Service. May check the database.', GREEN)]
    y = 2.00
    for n, ep, q, d, col in rows:
        box(s, M, y, CW, 1.02, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, M, y, 0.09, 1.02, fill=col)
        label(s, M + 0.28, y + 0.10, 2.7, 0.32, n, 13, True, col)
        label(s, M + 3.05, y + 0.12, 1.5, 0.28, ep, 11, True, NAVY)
        label(s, M + 4.65, y + 0.10, 6.6, 0.32, q, 12, True, NAVY)
        label(s, M + 0.28, y + 0.52, CW - 0.5, 0.42, d, 11, False, GREY)
        y += 1.14
    box(s, M, 5.52, CW, 1.15, fill=PALE['red'], line_col=RED)
    label(s, M + 0.22, 5.60, CW - 0.44, 0.3, 'THE MISTAKE THAT TAKES DOWN A PLATFORM', 10.5, True, RED)
    label(s, M + 0.22, 5.92, CW - 0.44, 0.72,
          'A liveness probe that checks the database. The database blips for 30 seconds → every liveness probe '
          'fails → Kubernetes restarts all 40 pods simultaneously → the stampede of reconnections keeps the '
          'database down. A brief dependency outage becomes a full outage, caused by your own health check.',
          12, False, NAVY, line=1.12)


# ══════════════════════════════════════════════════════ DAY 5
def terraform_flow(s):
    steps = [('WRITE', '.tf files\nin git', TEAL),
             ('PLAN', 'read-only diff\ndesired vs actual', LTBLUE),
             ('REVIEW', 'a human reads\nthe plan in the PR', GOLD),
             ('APPLY', 'execute exactly\nthe reviewed plan', GREEN)]
    w = 2.45
    x = M + 0.55
    for i, (n, d, col) in enumerate(steps):
        box(s, x, 2.00, w, 1.15, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 2.00, w, 0.36, fill=col)
        label(s, x, 2.04, w, 0.28, n, 12, True, WHITE, align='c')
        label(s, x + 0.08, 2.46, w - 0.16, 0.6, d, 10.5, False, NAVY, align='c')
        if i < 3:
            arrow(s, x + w + 0.06, 2.42, 0.34, 0.3, GREY, 'right')
        x += w + 0.46
    box(s, M + 3.4, 3.55, 5.0, 0.72, fill=NAVY)
    label(s, M + 3.5, 3.64, 4.8, 0.54, 'STATE  ·  terraform.tfstate\nthe map from code → real resources',
          11.5, True, WHITE, align='c')
    for xx in (M + 3.1, M + 8.5):
        arrow(s, xx, 3.24, 0.28, 0.26, GREY, 'down')
    box(s, M, 4.48, 5.55, 1.02, fill=PALE['red'], line_col=RED)
    label(s, M + 0.18, 4.56, 5.2, 0.3, 'STATE IS SENSITIVE', 10.5, True, RED)
    label(s, M + 0.18, 4.86, 5.2, 0.58,
          'It holds secrets in PLAINTEXT — sensitive = true masks CLI output only. '
          'Never commit it. Remote backend, encrypted, LOCKED.', 10.5, False, NAVY)
    x2 = M + CW - 5.55
    box(s, x2, 4.48, 5.55, 1.02, fill=PALE['green'], line_col=GREEN)
    label(s, x2 + 0.18, 4.56, 5.2, 0.3, 'DRIFT DETECTION', 10.5, True, GREEN)
    label(s, x2 + 0.18, 4.86, 5.2, 0.58,
          'terraform plan -detailed-exitcode on a schedule.\n'
          'exit 0 = no change · exit 2 = someone changed production by hand.', 10.5, False, NAVY)
    box(s, M, 5.68, CW, 0.98, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 5.77, CW - 0.44, 0.8,
          'THE SYMBOL TO FEAR IN A PLAN:   -/+  destroy and then create replacement.  '
          'On a stateless service that is a rollout. On a database it is data loss. '
          'Read every plan; put prevent_destroy on anything irreplaceable.', 12, False, NAVY, line=1.1)


def deployment_strategies(s):
    y0 = 1.95
    box(s, M, y0, CW, 1.30, fill=PALE['grey'], line_col=TEAL, line_w=0.75)
    label(s, M + 0.18, y0 + 0.08, 2.1, 0.3, 'ROLLING', 12, True, TEAL)
    label(s, M + 0.18, y0 + 0.38, 2.3, 0.7, 'the default\nno extra capacity', 10, False, GREY)
    seq = [('v1 v1 v1 v1', '9BB7C9'), ('v1 v1 v1 v2', '7FA8BF'), ('v1 v1 v2 v2', '5F97B3'), ('v2 v2 v2 v2', TEAL)]
    x = M + 2.75
    for i, (t, c) in enumerate(seq):
        box(s, x, y0 + 0.34, 1.75, 0.55, fill=c)
        label(s, x, y0 + 0.46, 1.75, 0.3, t, 11, True, WHITE, align='c')
        if i < 3:
            arrow(s, x + 1.80, y0 + 0.50, 0.28, 0.24, GREY, 'right')
        x += 2.08
    y1 = 3.38
    box(s, M, y1, CW, 1.30, fill=PALE['grey'], line_col=GREEN, line_w=0.75)
    label(s, M + 0.18, y1 + 0.08, 2.3, 0.3, 'BLUE-GREEN', 12, True, GREEN)
    label(s, M + 0.18, y1 + 0.38, 2.4, 0.7, 'instant rollback\n2× capacity', 10, False, GREY)
    box(s, M + 2.75, y1 + 0.28, 2.6, 0.68, fill=TEAL)
    label(s, M + 2.75, y1 + 0.44, 2.6, 0.3, 'BLUE  v1  LIVE', 11, True, WHITE, align='c')
    box(s, M + 6.0, y1 + 0.28, 2.6, 0.68, fill='BBD5C4')
    label(s, M + 6.0, y1 + 0.44, 2.6, 0.3, 'GREEN  v2  warm', 11, True, NAVY, align='c')
    box(s, M + 9.05, y1 + 0.28, 2.3, 0.68, fill=PALE['gold'], line_col=GOLD, line_w=0.75)
    label(s, M + 9.1, y1 + 0.36, 2.2, 0.55, 'flip the Service\nselector = 1 edit', 9.8, True, GOLD, align='c')
    y2 = 4.81
    box(s, M, y2, CW, 1.30, fill=PALE['grey'], line_col=ORANGE, line_w=0.75)
    label(s, M + 0.18, y2 + 0.08, 2.3, 0.3, 'CANARY', 12, True, ORANGE)
    label(s, M + 0.18, y2 + 0.38, 2.4, 0.7, 'smallest blast radius\nneeds good metrics', 10, False, GREY)
    box(s, M + 2.75, y2 + 0.28, 6.1, 0.68, fill=TEAL)
    label(s, M + 2.75, y2 + 0.44, 6.1, 0.3, 'STABLE  90 %', 11, True, WHITE, align='c')
    box(s, M + 8.95, y2 + 0.28, 0.95, 0.68, fill=ORANGE)
    label(s, M + 8.95, y2 + 0.44, 0.95, 0.3, '10 %', 10.5, True, WHITE, align='c')
    label(s, M + 10.05, y2 + 0.30, 2.3, 0.66, 'watch metrics →\npromote or ABORT', 10, True, ORANGE)
    box(s, M, 6.24, CW, 0.5, fill=PALE['blue'], line_col=TEAL)
    label(s, M + 0.22, 6.31, CW - 0.44, 0.36,
          'Choose by one question: can the two versions coexist against the same database schema? If not, no strategy saves you — fix the migration first.',
          11.5, False, NAVY)


def gitops(s):
    box(s, M, 1.95, 5.35, 2.55, fill=PALE['red'], line_col=RED, line_w=1.0)
    label(s, M, 2.03, 5.35, 0.32, 'PUSH-BASED CD', 12.5, True, RED, align='c')
    label(s, M + 0.25, 2.48, 4.85, 1.9,
          'CI pipeline holds CLUSTER CREDENTIALS\n\n'
          '✗  production credentials live outside the cluster\n'
          '✗  drift is invisible\n'
          '✗  no automatic self-healing', 11.5, False, NAVY, line=1.15)
    x2 = M + CW - 5.35
    box(s, x2, 1.95, 5.35, 2.55, fill=PALE['green'], line_col=GREEN, line_w=1.0)
    label(s, x2, 2.03, 5.35, 0.32, 'PULL-BASED  (GitOps)', 12.5, True, GREEN, align='c')
    label(s, x2 + 0.25, 2.48, 4.85, 1.9,
          'CI commits a new image tag. An in-cluster agent PULLS.\n\n'
          '✔  no credential ever leaves the cluster\n'
          '✔  drift is corrected continuously\n'
          '✔  git history IS the deployment record', 11.5, False, NAVY, line=1.15)
    flow = [('git push', TEAL), ('CI: test → build → scan', LTBLUE),
            ('commit new tag\nto the config repo', GOLD), ('agent reconciles\nthe cluster', GREEN)]
    w = 2.62
    x = M + 0.35
    for i, (t, col) in enumerate(flow):
        box(s, x, 4.85, w, 0.82, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 4.85, 0.07, 0.82, fill=col)
        label(s, x + 0.18, 4.93, w - 0.28, 0.66, t, 10.8, True, NAVY)
        if i < 3:
            arrow(s, x + w + 0.05, 5.14, 0.28, 0.24, GREY, 'right')
        x += w + 0.38
    box(s, M, 5.92, CW, 0.78, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 6.00, CW - 0.44, 0.62,
          'FOR A BANK THIS IS THE STRONGER CONTROL: no human and no external system holds production write '
          'access, every change is a reviewed commit, and rollback is `git revert` — same review, same audit trail.',
          12, False, NAVY, line=1.1)


# ══════════════════════════════════════════════════════ DAY 6
def shift_left(s):
    stages = ['design', 'code', 'build', 'test', 'deploy', 'production']
    costs = [0.35, 0.55, 0.95, 1.55, 2.55, 4.20]
    cols = [GREEN, GREEN, LTBLUE, ORANGE, 'D9601F', RED]
    w = 1.55
    x = M + 0.6
    base = 5.55
    for st, c, col in zip(stages, costs, cols):
        box(s, x, base - c, w, c, fill=col)
        label(s, x, base - c - 0.30, w, 0.28, {0.35: '1×', 0.55: '2×', 0.95: '5×',
                                              1.55: '15×', 2.55: '50×', 4.20: '100×+'}[c],
              11, True, col, align='c')
        label(s, x, base + 0.10, w, 0.3, st, 11, True, NAVY, align='c')
        x += w + 0.28
    arrow(s, M + 0.6, 6.02, 4.2, 0.26, GREEN, 'left')
    label(s, M + 0.6, 6.30, 5.0, 0.3, 'SHIFT LEFT — cheaper, and the author still has context',
          11, True, GREEN)
    label(s, M + 6.9, 6.30, 5.2, 0.3, 'and EXTEND RIGHT — runtime detection, production feedback',
          11, True, ORANGE)
    box(s, M + 6.2, 1.95, 5.4, 1.55, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 6.4, 2.04, 5.0, 0.3, 'THE ARITHMETIC THAT FORCES THIS', 10.5, True, GOLD)
    label(s, M + 6.4, 2.36, 5.0, 1.05,
          '~1 security engineer : ~10 ops : ~100 developers.\n'
          'Serial manual review at the end cannot keep up. It becomes a rubber stamp, '
          'the constraint in the value stream, or both.', 11.5, False, NAVY, line=1.12)


def secure_pipeline(s):
    stages = [('LOCAL', ['pre-commit hooks', 'gitleaks', 'IDE linting'], GREEN, 'seconds'),
              ('COMMIT', ['secret scan', 'SAST (bandit)', 'SCA (pip-audit)', 'IaC scan'], TEAL, 'minutes'),
              ('ARTEFACT', ['image scan', 'SBOM', 'sign the image'], LTBLUE, 'per build'),
              ('DEPLOY', ['admission policy', 'no :latest', 'runAsNonRoot'], ORANGE, 'at apply'),
              ('RUNTIME', ['anomaly detection', 're-scan SBOMs', 'incident response'], PLUM, 'always')]
    w = (CW - 4 * 0.24) / 5
    x = M
    for i, (n, items, col, when) in enumerate(stages):
        box(s, x, 2.00, w, 2.60, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 2.00, w, 0.42, fill=col)
        label(s, x, 2.05, w, 0.3, n, 11.5, True, WHITE, align='c')
        label(s, x, 2.48, w, 0.26, when, 9.5, True, col, align='c')
        y = 2.84
        for it in items:
            label(s, x + 0.14, y, w - 0.24, 0.4, '· ' + it, 10, False, NAVY)
            y += 0.38
        if i < 4:
            arrow(s, x + w + 0.02, 3.05, 0.20, 0.28, GREY, 'right')
        x += w + 0.24
    box(s, M, 4.90, CW, 1.78, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 4.99, CW - 0.44, 0.3, 'GATE ON RISK, NOT ON EVERYTHING', 11, True, GOLD)
    rows = [('Secret in code or history', 'FAIL — always. Rotate first, scrub second.'),
            ('CRITICAL / HIGH with a fix available', 'FAIL the build.'),
            ('HIGH / CRITICAL with NO fix', 'Warn. Record an accepted risk with an owner and an expiry date.'),
            ('MEDIUM / LOW', 'Report to a dashboard. Fix in planned work.')]
    y = 5.34
    for a, b in rows:
        label(s, M + 0.28, y, 4.5, 0.3, '· ' + a, 11, True, NAVY)
        label(s, M + 5.0, y, CW - 5.3, 0.3, b, 11, False, GREY)
        y += 0.32
    label(s, M + 0.28, 6.40, CW - 0.5, 0.28,
          'A pipeline that is always red gets bypassed — and a bypassed gate is worse than no gate, because you believe you are protected.',
          10.5, True, RED, italic=True)


def three_pillars(s):
    pil = [('METRICS', 'numbers over time, aggregatable',
            ['✔ cheap, constant cost', '✔ ideal for alerting', '✗ no per-request detail',
             '✗ cardinality explodes'], 'Prometheus', TEAL),
           ('LOGS', 'discrete timestamped events',
            ['✔ rich exact context', '✔ the "why"', '✗ expensive at volume',
             '✗ hard to aggregate'], 'Loki · ELK', ORANGE),
           ('TRACES', 'one request across services',
            ['✔ shows WHERE time goes', '✔ essential for microservices', '✗ needs instrumentation',
             '✗ usually sampled'], 'Jaeger · Tempo', GREEN)]
    w = (CW - 0.5) / 3
    x = M
    for n, sub, pts, tool, col in pil:
        box(s, x, 1.95, w, 3.35, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 1.95, w, 0.44, fill=col)
        label(s, x, 2.01, w, 0.3, n, 12.5, True, WHITE, align='c')
        label(s, x + 0.1, 2.48, w - 0.2, 0.34, sub, 10.5, True, col, align='c')
        y = 2.92
        for p in pts:
            mark, txt = p[0], p[2:]
            label(s, x + 0.18, y, 0.26, 0.28, mark, 10.5, True, GREEN if mark == '✔' else RED)
            label(s, x + 0.46, y, w - 0.62, 0.5, txt, 10.5, False, NAVY)
            y += 0.46
        box(s, x + 0.15, 4.92, w - 0.3, 0.30, fill=WHITE, line_col=col, line_w=0.5)
        label(s, x + 0.15, 4.955, w - 0.3, 0.26, tool, 10, True, col, align='c')
        x += w + 0.25
    box(s, M, 5.50, CW, 0.55, fill=NAVY)
    label(s, M + 0.2, 5.58, CW - 0.4, 0.4,
          'BOUND TOGETHER BY A TRACE / CORRELATION ID  —  the fourth thing that matters, and the one most teams skip',
          12, True, WHITE, align='c')
    box(s, M, 6.14, CW, 0.55, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 6.22, CW - 0.44, 0.4,
          'In a bank: never a PAN, a customer name or an account number in a log line. Logs are widely readable and long-retained.',
          11.5, False, NAVY)


def error_budget(s):
    label(s, M, 1.88, CW, 0.32, 'SLO 99.5 % over 28 days   →   error budget = 0.5 %   =   3 h 22 m of permitted failure',
          13, True, NAVY)
    box(s, M, 2.38, CW, 0.82, fill=PALE['grey'], line_col='C4CCD4', line_w=0.75)
    box(s, M, 2.38, CW * 0.72, 0.82, fill=ORANGE)
    label(s, M, 2.55, CW * 0.72, 0.5, '72 % CONSUMED', 14, True, WHITE, align='c')
    label(s, M + CW * 0.72, 2.55, CW * 0.28, 0.5, '57 min left', 12.5, True, GREY, align='c')
    states = [('BUDGET REMAINING', 'ship freely · take risks · deploy often', GREEN),
              ('NEARLY EXHAUSTED', 'freeze features · reliability work only', ORANGE),
              ('BLOWN', 'everything stops until the budget recovers', RED)]
    x = M
    w = (CW - 0.5) / 3
    for n, d, col in states:
        box(s, x, 3.42, w, 0.92, fill=PALE['grey'], line_col=col, line_w=1.0)
        box(s, x, 3.42, w, 0.30, fill=col)
        label(s, x, 3.455, w, 0.26, n, 10.5, True, WHITE, align='c')
        label(s, x + 0.12, 3.80, w - 0.24, 0.48, d, 10.5, False, NAVY, align='c')
        x += w + 0.25
    box(s, M, 4.58, CW, 0.72, fill=NAVY)
    label(s, M + 0.2, 4.67, CW - 0.4, 0.54,
          'THE ERROR BUDGET IS WHAT CONVERTS "Dev wants speed, Ops wants stability" FROM A POLITICAL ARGUMENT '
          'INTO ONE SHARED NUMBER THAT BOTH TEAMS MANAGE.', 12, True, WHITE, align='c')
    hdr = ['SLO', 'Downtime / 30 days', 'Downtime / year']
    rows = [('99 %', '7 h 12 m', '3.65 days'), ('99.9 %', '43 m 12 s', '8.77 hours'),
            ('99.99 %', '4 m 19 s', '52.6 minutes')]
    x = M
    ws = [2.6, 4.4, 4.5]
    for w, h in zip(ws, hdr):
        label(s, x + 0.12, 5.46, w, 0.28, h, 10, True, GREY); x += w
    y = 5.74
    for r in rows:
        box(s, M, y, CW, 0.30, fill=WHITE, line_col='DDE2E7', line_w=0.5)
        x = M
        for w, v in zip(ws, r):
            label(s, x + 0.14, y + 0.015, w - 0.2, 0.27, v, 10.5, w == 2.6, NAVY, anchor='m')
            x += w
        y += 0.32
    label(s, M, 6.62, CW, 0.26, 'Do not choose 99.99 % by default — each nine multiplies cost.',
          10, True, ORANGE, italic=True)


def platform_engineering(s):
    box(s, M, 1.98, 5.45, 3.05, fill=PALE['red'], line_col=RED, line_w=1.0)
    label(s, M, 2.06, 5.45, 0.32, 'WITHOUT A PLATFORM', 12.5, True, RED, align='c')
    label(s, M + 0.28, 2.50, 4.9, 2.35,
          'Every team invents its own:\n'
          '·  CI pipeline\n·  Kubernetes manifests\n·  monitoring setup\n·  secret handling\n\n'
          '12 teams × 6 weeks of setup\n12 different failure modes', 11.5, False, NAVY, line=1.18)
    x2 = M + CW - 5.45
    box(s, x2, 1.98, 5.45, 3.05, fill=PALE['green'], line_col=GREEN, line_w=1.0)
    label(s, x2, 2.06, 5.45, 0.32, 'WITH A PLATFORM', 12.5, True, GREEN, align='c')
    label(s, x2 + 0.28, 2.50, 4.9, 2.35,
          'One golden path:\n'
          '·  templated pipeline\n·  generated manifests\n·  observability wired in\n·  secrets injected\n\n'
          'new service running in 30 minutes\none hardened, patched, supported path', 11.5, False, NAVY, line=1.18)
    arrow(s, M + 5.55, 3.25, 0.6, 0.4, GREY, 'right')
    prin = [('Treat it as a PRODUCT', 'users, roadmap, docs, satisfaction metrics'),
            ('Golden paths, not golden cages', 'make the paved road easiest — allow escape hatches'),
            ('Self-service', 'a ticket-and-wait platform is the old ops team renamed'),
            ('Reduce cognitive load', 'do not merely relocate it into a bespoke DSL')]
    y = 5.22
    for i, (n, d) in enumerate(prin):
        xx = M + (i % 2) * (CW / 2 + 0.1)
        yy = y + (i // 2) * 0.66
        box(s, xx, yy, CW / 2 - 0.1, 0.56, fill=WHITE, line_col='D3DAE1', line_w=0.5)
        box(s, xx, yy, 0.06, 0.56, fill=TEAL)
        label(s, xx + 0.18, yy + 0.04, CW / 2 - 0.35, 0.26, n, 11, True, NAVY)
        label(s, xx + 0.18, yy + 0.28, CW / 2 - 0.35, 0.26, d, 9.8, False, GREY)


def sod_control(s):
    box(s, M, 1.95, 5.45, 3.75, fill=PALE['grey'], line_col=GREY, line_w=1.0)
    label(s, M, 2.03, 5.45, 0.32, 'TRADITIONAL', 12.5, True, GREY, align='c')
    steps = ['Developer writes the change', 'Hands it to a release team',
             'Release team deploys manually', 'Evidence: a signed form, filed']
    y = 2.50
    for i, t in enumerate(steps):
        box(s, M + 0.3, y, 4.85, 0.52, fill=WHITE, line_col='C9D2DA', line_w=0.5)
        label(s, M + 0.45, y + 0.12, 4.6, 0.3, t, 11, False, NAVY)
        y += 0.62
    box(s, M + 0.3, y + 0.05, 4.85, 0.62, fill=PALE['red'], line_col=RED, line_w=0.75)
    label(s, M + 0.45, y + 0.14, 4.6, 0.46,
          'Applies to: the changes that\nreached the meeting agenda', 10.5, True, RED)
    x2 = M + CW - 5.45
    box(s, x2, 1.95, 5.45, 3.75, fill=PALE['green'], line_col=GREEN, line_w=1.0)
    label(s, x2, 2.03, 5.45, 0.32, 'DEVOPS-NATIVE', 12.5, True, GREEN, align='c')
    steps2 = ['Developer opens a pull request', 'Branch protection REFUSES self-approval',
              'A different named person approves', 'The pipeline deploys — no human']
    y = 2.50
    for t in steps2:
        box(s, x2 + 0.3, y, 4.85, 0.52, fill=WHITE, line_col='A9CDB5', line_w=0.5)
        label(s, x2 + 0.45, y + 0.12, 4.6, 0.3, t, 11, False, NAVY)
        y += 0.62
    box(s, x2 + 0.3, y + 0.05, 4.85, 0.62, fill=PALE['green'], line_col=GREEN, line_w=0.75)
    label(s, x2 + 0.45, y + 0.14, 4.6, 0.46,
          'Applies to: 100 % of changes,\nalways, with automatic evidence', 10.5, True, GREEN)
    arrow(s, M + 5.55, 3.55, 0.6, 0.42, GOLD, 'right')
    box(s, M, 5.88, CW, 0.82, fill=PALE['gold'], line_col=GOLD)
    label(s, M + 0.22, 5.97, CW - 0.44, 0.66,
          'SAY THIS TO YOUR AUDITOR:  "Under the old process two people reviewed the changes that reached the '
          'CAB agenda. Under this one the system makes it impossible to merge without a second named approver, '
          'on every change, and produces the evidence itself."', 12, False, NAVY, line=1.1)
