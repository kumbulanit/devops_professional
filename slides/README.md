# Theory decks

Six PowerPoint decks, one per day, covering the theory that accompanies the labs.
Built for **UniCredit** on the NobleProg template.

| Deck | Day | Slides | Modules |
|---|---|---|---|
| `Day1_DevOps_Foundations.pptx` | 1 | 32 | 1 — Foundations · 2a — Git fundamentals |
| `Day2_Version_Control_and_CI.pptx` | 2 | 24 | 2b — Branching, PRs, CI |
| `Day3_Containers_with_Docker.pptx` | 3 | 22 | 3 — Containers |
| `Day4_Kubernetes.pptx` | 4 | 24 | 4 — Kubernetes |
| `Day5_IaC_and_Continuous_Delivery.pptx` | 5 | 24 | 5 — IaC · 6 — Continuous Delivery |
| `Day6_DevSecOps_Observability_Enterprise.pptx` | 6 | 30 | 7 — DevSecOps · 8 — Observability · 9 — Enterprise · Appendix A |

**156 slides · 16:9 · 22 native-vector diagrams** — no images, so every diagram is editable and
recolourable live in the room.

## Design

Matched to `Cheat_Sheet_full.pptx` so the decks and the cheat sheet are one family:

| | |
|---|---|
| Chrome | NobleProg logo top-right, swirl rule and page number at the foot; covers use the bright/deep blue bars |
| Navy | `#123A5F` — headings and structure |
| Teal | `#117A69` — COMPARE, good practice |
| Orange | `#D2760D` — BUILD, best practice, banking callouts |
| Plum | `#A0275C` — AUDIT, exceptions |
| Green / Red | `#3E7D32` / `#B3261E` — success and failure in diagrams |
| Bright / deep blue | `#29ABE2` / `#1B75BB` — accent rules and cover bars |
| Type | Aptos Display (headings), Aptos (body) |

## Making it a course people enjoy

**15 exercises** across the six days, each with the answer on a *following* slide so the
exercise is a real exercise:

| Type | Colour | What it does |
|---|---|---|
| **PREDICT** | navy | Commit to an answer before the reveal — used before flow efficiency, image size, node failure, drift, and the security gates |
| **COMPARE** | teal | Two minutes in pairs — branching habits, Alpine vs slim, liveness vs readiness, who holds production credentials |
| **AUDIT** | plum | Score your own organisation — CALMS, and the day-6 commitment |
| **DISCUSS** | orange | Whole room, no single right answer — "everything is green and nobody can pay" |
| **MYTH vs REALITY** | plum/teal | Four DevOps myths, three Kubernetes myths |

Plus a **check-your-understanding** slide closing every day, **lab bridge** slides
(green OBJECTIVE / blue OUTCOME) before each hands-on block, and **banking slides** citing
Appendix A.

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
| `deckkit.py` | 17 slide types, the iterative fitter, adaptive spreading, chrome |
| `diagrams.py` | 22 native-vector diagrams |
| `content_dayN.py` | The content for each day, as data tuples |
| `build.py` | Assembles the decks and adds default trainer notes |
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

### Two things to know before editing content

1. Content items are **tuples**; keyword arguments go in a **trailing dict**, never as
   `key=value` inside the tuple.
2. `qa.py` catches overflow but **not** clumped or overlapping content — render a few pages to
   PNG and look at them after any layout change.

### Re-branding for another client

Change `client='UniCredit'` in `deckkit.py` (`s_title`) and rebuild. To change template
entirely, point `TEMPLATE` in `build.py` elsewhere — the decks use only `Blank` / `Title Only`
layouts plus their own drawing, so they move cleanly.
