# Lab 01 — Map a Value Stream and Find the Bottleneck

| | |
|---|---|
| **Day** | 1 |
| **Duration** | 35 minutes (20 mapping · 10 calculating · 5 discussion) |
| **Module** | 1 — DevOps Foundations |
| **You will produce** | `value-stream.md` and `calms-assessment.md` — committed in Lab 02 |
| **Feeds into** | Lab 02 (these become the first files in your repository); the capstone plan on day 6 |

---

## Objective

Map how a change *actually* travels from request to production in **your own organisation**,
measure it, calculate flow efficiency, and identify the real constraint — which is almost
never the one the team believes it is.

This is the only lab with no tooling. It is also the one delegates most often report as the
most valuable, because every automation decision for the rest of the week should be
justified by what you find here.

## Prerequisites

- Lab 00 complete
- Module 1 §1.6 (Value Stream Management) covered
- Honesty about your own process. Optimistic numbers produce a useless map.

---

## Background — the four numbers

For every step in the stream you record:

| Number | Definition | How to get it honestly |
|---|---|---|
| **PT** — Process Time | Hands-on-keyboard time actually spent working the item | Ask "if nothing interrupted you, how long?" |
| **WT** — Wait Time | Time the item sits in a queue between steps | Ask "how long from *ready* for this step to *started*?" — **this is where the surprises are** |
| **%C/A** | % arriving usable, needing no rework or clarification | "Out of ten items, how many come to you complete and correct?" |
| **LT** — Lead Time | `Σ PT + Σ WT` | Calculated |

And the two headline figures:

```
  FLOW EFFICIENCY = Σ PT ÷ LT × 100 %          typical unimproved enterprise: 5–15 %
  ROLLED %C/A     = %C/A₁ × %C/A₂ × … × %C/Aₙ  the chance an item passes through untouched
```

---

## Step 1 — Create the workspace

```bash
mkdir -p ~/devops-course/paytrack-api/docs && cd ~/devops-course/paytrack-api
```
**What this does:** creates the directory that becomes your project repository in Lab 02, with
a `docs/` subdirectory. Working here now means your value stream map is version-controlled
from the first commit — "everything as code" starting with your own analysis.

---

## Step 2 — Choose one real change

Pick a **specific, recent, ordinary** change your team shipped. Not the heroic emergency
fix; not the six-month programme. A typical one — "add a field to a form", "fix a null check",
"bump a dependency".

> 🏦 **Good banking candidates:** add a field to an onboarding screen · change a fraud rule
> threshold · add a currency to a payments service · fix a rounding error in a statement ·
> patch a library flagged by a scan · add a field to a regulatory report.
>
> **Avoid, for this exercise:** anything involving the core banking platform or a vendor
> package release. Those have genuinely different economics and will distort your first map.
> Map one of those *second*, once you know what the shape looks like.

Write it down:

```bash
cat > docs/value-stream.md <<'EOF'
# Value Stream Map — <your team / service>

**Date mapped:** <today>
**Change mapped:** <the specific change, e.g. "PAY-142: add a readiness endpoint">
**Mapped by:** <names — ideally including someone from Ops>

## Why this change
<Why is it representative? What made it typical?>
EOF
```
**What this does:** starts the document with the scope stated. `<<'EOF'` writes the block
literally; you will edit the placeholders in the next step.

---

## Step 3 — Walk the stream backwards

> **Walk it backwards, from production to the original request.** Forward-walking produces
> the *official* process. Backward-walking produces the *real* one, because each person can
> only tell you truthfully where their input actually came from.

For each step, record: **who** does it, **PT**, **WT**, **%C/A**, and the **tool** used.

Typical steps to consider — delete what does not apply, add what does:

```
 idea/request → prioritised → refined → assigned → coding → code review → merge →
 build → automated test → manual QA → security review → change approval (CAB) →
 release scheduling → deploy to staging → UAT → deploy to production → verified
```

**Bank-specific steps to add where they apply** — these are usually where the queue is:

```
 … → risk assessment → architecture review board → information-security sign-off →
 data-privacy (DPIA) review → third-party/vendor approval → penetration test slot →
 CAB submission deadline → CAB meeting → release window / batch window →
 business sign-off → post-implementation review
```

> ⚠️ **Record the *deadline* effects honestly.** "CAB meets Thursday, submissions close
> Tuesday" means a change ready on Wednesday waits **six days** before it is even discussed.
> That is wait time, and it is invisible unless you write it down.

Append your table:

```bash
cat >> docs/value-stream.md <<'EOF'

## The map

| # | Step | Who | Tool | PT (h) | WT (h) | %C/A |
|---|------|-----|------|--------|--------|------|
| 1 | Request logged        |  |  |  |  |  |
| 2 | Prioritised / refined |  |  |  |  |  |
| 3 | Development           |  |  |  |  |  |
| 4 | Code review           |  |  |  |  |  |
| 5 | Build & automated test|  |  |  |  |  |
| 6 | Manual QA             |  |  |  |  |  |
| 7 | Security review       |  |  |  |  |  |
| 8 | Change approval       |  |  |  |  |  |
| 9 | Deploy to staging     |  |  |  |  |  |
|10 | UAT / sign-off        |  |  |  |  |  |
|11 | Deploy to production  |  |  |  |  |  |
|12 | Verified in production|  |  |  |  |  |
EOF
nano docs/value-stream.md
```
**What this does:** `>>` **appends** to the file rather than `>` which would overwrite it —
an important habit. Then `nano` opens it so you can fill in the numbers. Save with
`Ctrl+O`, `Enter`; exit with `Ctrl+X`.

> ⚠️ **The most common mistake:** recording only PT and leaving WT blank or small. If your
> WT column looks small, you are measuring the process as documented, not as experienced.
> Ask: *how long between the developer marking it ready for review and the reviewer opening
> it?* That number is usually 1–3 **days**, not 30 minutes.

---

## Step 4 — Calculate

Fill your numbers into this script:

```bash
cat > docs/vsm-calc.py <<'EOF'
#!/usr/bin/env python3
"""Value stream arithmetic. Edit STEPS to match docs/value-stream.md, then run."""

# (name, process_time_hours, wait_time_hours, percent_complete_and_accurate)
# Example numbers below are a COMPOSITE from real bank delivery teams. Replace with
# your own - but note the shape: the engineering steps are small, the governance
# queues are enormous, and that is the finding.
STEPS = [
    ("Request logged",        0.5,   24, 0.85),
    ("Prioritised / refined", 2.0,   40, 0.80),
    ("Risk assessment",       1.0,   56, 0.85),
    ("Development",          16.0,    4, 0.90),
    ("Code review",           1.0,   26, 0.85),
    ("Build & test",          0.5,    1, 0.95),
    ("Manual QA",             8.0,   60, 0.70),
    ("InfoSec sign-off",      2.0,   72, 0.90),
    ("CAB submission wait",   0.5,  120, 0.95),   # ready Wed, CAB Thu, cut-off Tue
    ("Deploy to staging",     1.0,    8, 0.95),
    ("UAT / business sign-off", 4.0,  40, 0.85),
    ("Release window wait",   0.0,   96, 1.00),   # pure queue: nobody is working
    ("Deploy to production",  2.0,    4, 0.90),
]

pt = sum(s[1] for s in STEPS)
wt = sum(s[2] for s in STEPS)
lt = pt + wt
rolled = 1.0
for s in STEPS:
    rolled *= s[3]

print(f"{'STEP':<24}{'PT(h)':>8}{'WT(h)':>8}{'%C/A':>8}{'% of LT':>10}")
print("-" * 58)
for name, p, w, c in STEPS:
    print(f"{name:<24}{p:>8.1f}{w:>8.1f}{c*100:>7.0f}%{(p+w)/lt*100:>9.1f}%")
print("-" * 58)
print(f"{'TOTAL':<24}{pt:>8.1f}{wt:>8.1f}")
print()
print(f"  Lead time            : {lt:,.1f} h  ({lt/8:,.1f} working days)")
print(f"  Process time         : {pt:,.1f} h")
print(f"  Wait time            : {wt:,.1f} h   <-- pure queue")
print(f"  FLOW EFFICIENCY      : {pt/lt*100:.1f} %")
print(f"  ROLLED %C/A          : {rolled*100:.1f} %")
print()
worst_wait = max(STEPS, key=lambda s: s[2])
worst_qual = min(STEPS, key=lambda s: s[3])
print(f"  BIGGEST QUEUE        : {worst_wait[0]} ({worst_wait[2]} h waiting)")
print(f"  WORST QUALITY GATE   : {worst_qual[0]} ({worst_qual[3]*100:.0f}% complete & accurate)")
print()
print("  Little's Law: Lead Time = WIP / Throughput")
print("  -> halving WIP halves lead time at constant throughput.")
EOF
python3 docs/vsm-calc.py
```
**What this does:** runs the arithmetic so nobody has to do it by hand, and prints the three
figures that matter: flow efficiency, rolled %C/A, and the largest queue. Replace the
example `STEPS` with your own numbers and run it again.

✅ **Checkpoint:** you have a flow efficiency percentage. **Say it out loud to the room.**
If it is above 40 %, your wait times are almost certainly under-reported — go back to
step 3.

---

## Step 5 — Identify the constraint and the top three actions

```bash
cat >> docs/value-stream.md <<'EOF'

## Results

| Figure | Value |
|---|---|
| Total lead time | ___ h ( ___ working days ) |
| Total process time | ___ h |
| Total wait time | ___ h |
| **Flow efficiency** | ___ % |
| **Rolled %C/A** | ___ % |
| **Largest queue (the constraint)** | ___ |

## What the room *believed* the bottleneck was
<Write this BEFORE looking at the numbers.>

## What the map says the bottleneck actually is
<And by how much.>

## Top 3 improvements, in order of expected impact

| # | Action | Step it targets | Expected effect on lead time | Effort | Owner |
|---|--------|-----------------|------------------------------|--------|-------|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |

## Which course day addresses each
<e.g. "#1 automate the manual regression suite → Day 2, Lab 04">
EOF
nano docs/value-stream.md
```
**What this does:** appends the analysis section. The *believed vs actual* pair is the point
of the exercise — capture the belief before the arithmetic, or the finding loses its force.

> **Rule from the Theory of Constraints:** any improvement made anywhere other than the
> constraint is an illusion. If your constraint is a 120-hour approval queue, adding more
> automated tests will not shorten your lead time by one minute.

---

## Step 6 — CALMS self-assessment

```bash
cat > docs/calms-assessment.md <<'EOF'
# CALMS Assessment — <team / organisation>

Score each dimension 1–5.
1 Initial (ad hoc, heroic) · 2 Repeatable (documented, manual) · 3 Defined (standardised,
partly automated) · 4 Managed (automated, measured) · 5 Optimising (self-service, data-driven)

| Dimension | Score | Evidence for the score | The single biggest gap |
|---|---|---|---|
| **C**ulture — shared ownership, blamelessness, who carries the pager |  |  |  |
| **A**utomation — CI/CD, IaC, testing, self-service |  |  |  |
| **L**ean — batch size, WIP limits, queues, visible work |  |  |  |
| **M**easurement — DORA metrics, SLOs, telemetry |  |  |  |
| **S**haring — runbooks, post-mortems, cross-team reuse |  |  |  |

## Diagnostic answers

- **Culture:** when production last broke, what was the *first question* asked in the room?
- **Automation:** how many humans must type something for a one-line change to reach prod?
- **Lean:** what % of lead time is queue time? (from value-stream.md)
- **Measurement:** what is your change failure rate? (If nobody knows — that is the answer.)
- **Sharing:** can another team find and read your last incident review?

## Lowest score = your constraint

**Lowest dimension:** ___
**First experiment to run:** ___
**How we will know it worked (the measure):** ___
EOF
nano docs/calms-assessment.md
```
**What this does:** creates the maturity assessment. The lowest-scoring dimension, not the
most interesting one, is where the next investment belongs.

---

## Step 7 — Estimate your DORA baseline

```bash
cat >> docs/calms-assessment.md <<'EOF'

## DORA baseline (estimate today; measure properly on Day 6)

| Metric | Our value today | DORA band | Where we want to be in 90 days |
|---|---|---|---|
| Deployment frequency |  |  |  |
| Lead time for change (commit → prod) |  |  |  |
| Change failure rate |  |  |  |
| Failed-deployment recovery time |  |  |  |

*Bands: Elite = on-demand / <1 h / 0-15 % / <1 h · High = weekly-monthly / 1 day-1 week /
16-30 % / <1 day · Medium = monthly-6 months / 1-6 months / 16-30 % / 1 day-1 week ·
Low = <every 6 months / >6 months / 16-30 % / >6 months*
EOF
```
**What this does:** captures the numbers you will compare against in the day-6 capstone
debrief. Estimating them now, badly, is far better than not having a baseline at all — and
noticing you *cannot* estimate them is itself the finding.

---

## ✅ Checkpoint

```bash
ls -la docs/ && head -20 docs/value-stream.md
```
You should have `value-stream.md`, `calms-assessment.md` and `vsm-calc.py`, all with real
content.

---

## Discussion (5 minutes, whole room)

1. Whose flow efficiency was lowest? What was their constraint?
2. **How many rooms found the constraint was an approval or a hand-off rather than an
   engineering step?** (In most cohorts: nearly all of them.)
3. Which of the improvements you listed can be implemented **without permission from anyone
   outside the team**? Start there on Monday.
4. Apply Little's Law: if you halved your WIP tomorrow, what would your lead time become?

---

## 🎯 Outcome

`~/devops-course/paytrack-api/docs/` contains your value stream map, CALMS assessment, DORA
baseline and the calculator. These become the **first commit** of your repository in Lab 02,
and you will revisit them in the Lab 19 capstone debrief.

**Next:** [Lab 02 — Git Fundamentals](../lab-02-git-fundamentals/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Timing:** 20 min mapping, 10 min calculating, 5 min plenary. Do not let mapping run long
  — precision is not the objective, the *shape* is.
- **The three things that go wrong:**
  1. Delegates map the process as documented, not as lived. Push hard on wait times: "how
     long between ready-for-review and review-started?" is the unlocking question.
  2. Someone maps a whole programme instead of one change. Redirect to a single small item.
  3. Solo delegates with no Ops colleague present guess the deploy-side numbers. Pair them
     with someone from a different function.
- **Have a worked example ready** on the projector — the numbers already in `vsm-calc.py`
  give 9 % flow efficiency and a CAB constraint. Run it live before they start.
- **Debrief question that lands hardest:** "Of your total lead time, what percentage was
  anyone actually working on this change?" Let the silence sit.
- If a delegate genuinely has no employer process to map (student, between roles), have
  them map the course's own chain: local edit → commit → push → CI → image → deploy.
</details>
