# Theory decks

Six PowerPoint decks, one per day, built for **UniCredit** on the NobleProg template.

The course is delivered **theory-first**: each session (3 h 30 m; Day 2 is 3 h) is mostly taught from its deck —
with exercises and live demos built in — and ends with a short guided practical that starts
the day's labs together. The labs are finished after class. See
[docs/run-sheet.md](../docs/run-sheet.md) for the minute-by-minute plan.

| Deck | Day | Slides | Modules |
|---|---|---|---|
| `Day1_DevOps_Foundations.pptx` | 1 | 63 | 1 — Foundations · 2a — Git fundamentals |
| `Day2_Version_Control_and_CI.pptx` | 2 | 46 | 2b — Working together on code, for beginners, in 3 hours: branches, everyday Git commands, merge and rebase, pull requests, CI, GitHub Actions and Jenkins |
| `Day2_Version_Control_and_CI_Going_Further.pptx` | 2 | 49 | *Optional reading, not taught:* single-command slides, stash, reset, reflog, cherry-pick, tag, bisect, clean, rebase in depth, reviews, CODEOWNERS, test types, Jenkins, pipeline security — plus lab slides for the hands-on Labs 03A, 04A and 04B |
| `Day3_Containers_with_Docker.pptx` | 3 | 57 | 3 — Containers, images, Dockerfiles, Compose, networking, storage |
| `Day4_Kubernetes.pptx` | 4 | 57 | 4 — Kubernetes |
| `Day5_IaC_and_Continuous_Delivery.pptx` | 5 | 57 | 5 — IaC (Terraform, Ansible) · 6 — Continuous Delivery |
| `Day6_DevSecOps_Observability_Enterprise.pptx` | 6 | 60 | 7 — DevSecOps · 8 — Observability · 9 — Enterprise · Appendix A |

**340 taught slides (+ 49 optional reading) · 16:9 · 32 native-vector diagrams** — no images, so every diagram is editable and
recolourable live in the room.

## What is on the slides

Each deck follows its module section by section, with a numbered section divider for each
block of the run sheet.

| Slide type | Count | What it is for |
|---|---|---|
| **Agenda** | 6 | The shape of the day: theory, exercises, demos, break, practical, after-class labs |
| **Definition** | 39 | A term stated precisely, then the points that make it usable |
| **Table** | 75 | Comparisons, decision tables, command references, key terms |
| **Diagram** | 33 | Architecture and mechanism pictures, drawn as editable shapes |
| **Annotated code** | 32 | Real config and code from the labs — Dockerfiles, manifests, HCL, PromQL — with numbered explanations |
| **Workflow** | 13 | A process as numbered steps: what `kubectl apply` does, a rolling update, expand/contract, incident response |
| **Live demo** | 7 | A terminal session to type in front of the room, with the expected output and what to watch for |
| **In a regulated bank** | 9 | The banking argument for the topic, citing Appendix A |
| **Lab bridge** | 13 | What the day's lab builds — started together in class, finished after |

## Making it a course people enjoy

**16 exercises**, each with the answer on a *following* slide so the exercise is a real exercise:

| Type | Colour | What it does |
|---|---|---|
| **PREDICT** | navy | Commit to an answer before the reveal — flow efficiency, the constraint, a force-pushed main, image size, a node failure, drift, security gates |
| **COMPARE** | teal | Two minutes in pairs — a post-mortem finding, branching habits, Alpine vs slim, liveness vs readiness, who holds production credentials |
| **AUDIT** | plum | Score your own organisation — CALMS, and the day-6 commitment |
| **DISCUSS** | orange | Whole room, no single right answer — "everything is green and nobody can pay" |
| **MYTH vs REALITY** | plum/teal | What DevOps is not, what you hear in a bank, CI myths, Kubernetes myths |

Plus a **key terms** slide and a **check-your-understanding** slide closing every day.

## Design

Matched to `Cheat_Sheet_full.pptx` so the decks and the cheat sheet are one family:

| | |
|---|---|
| Chrome | NobleProg logo top-right, swirl rule and page number at the foot; covers use the bright/deep blue bars |
| Navy | `#123A5F` — headings and structure |
| Teal | `#117A69` — COMPARE, good practice |
| Orange | `#D2760D` — live demos, best practice, banking callouts |
| Plum | `#A0275C` — AUDIT, exceptions |
| Green / Red | `#3E7D32` / `#B3261E` — success and failure in diagrams |
| Bright / deep blue | `#29ABE2` / `#1B75BB` — accent rules and cover bars |
| Type | Aptos Display (headings), Aptos (body), Consolas (code) |

## Rebuilding

The decks are generated, not hand-edited. Source is in `../_build/`:

```bash
cd ../_build
python build.py          # all six
python build.py 4        # just day 4
python qa.py             # convert to PDF and check for overflow / tiny text
```

| File | Purpose |
|---|---|
| `deckkit.py` | 21 slide types, the fitters, adaptive spreading, chrome |
| `diagrams.py` | 32 native-vector diagrams |
| `content_dayN.py` | The content for each day, as data tuples |
| `build.py` | Assembles the decks, adds default trainer notes, reports any over-full block |
| `qa.py` | LibreOffice → PDF → PyMuPDF gate: overflow, tiny text, empty pages |
| `assets/` | NobleProg logo and footer swirl, extracted from the cheat sheet |

**If you hand-edit a .pptx, note it here** — otherwise the next `build.py` run overwrites it.

### Not in the public repository

Two things are deliberately git-ignored:

| Path | Why | Effect |
|---|---|---|
| `slides/*.pptx` | Built artefacts — regenerate them, do not version them | Run `cd _build && python build.py` |
| `_build/assets/*.png` | **NobleProg's logo and footer swirl** — their trademark, not ours to redistribute | Decks build fine without them; they simply have no logo |

To restore the branding, extract the two images from `Cheat_Sheet_full.pptx` into
`_build/assets/` as `nobleprog_logo.png` (3:1 aspect) and `footer_swirl.png` (13:1), then
rebuild. `deckkit.py` skips them silently if they are absent.

### Things to know before editing content

1. Content items are **tuples**; keyword arguments go in a **trailing dict**, never as
   `key=value` inside the tuple.
2. `qa.py` catches overflow but **not** clumped or overlapping content — render a few pages to
   PNG and look at them after any layout change. `build.py` also prints any block whose text
   could not fit even at the smallest allowed size.
3. Exercises add a reveal slide, so slide numbers and spec positions differ after the first
   exercise; `deckkit.LAST_PAIRS` maps each spec item to the slide it produced.

### Re-branding for another client

Change `client='UniCredit'` in `deckkit.py` (`s_title`) and rebuild. To change template
entirely, point `TEMPLATE` in `build.py` elsewhere — the decks use only `Blank` / `Title Only`
layouts plus their own drawing, so they move cleanly.
