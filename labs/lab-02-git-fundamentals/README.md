# Lab 02 — Git Fundamentals

| | |
|---|---|
| **Day** | 1 |
| **Duration** | 25 minutes (+ optional 15-minute stretch as homework) |
| **Module** | 2 — Version Control and CI |
| **You will produce** | A local git repository containing PayTrack API with a clean, meaningful history |
| **Feeds into** | Lab 03 (push to GitHub, branch, review) — and every lab after it |

---

## Objective

Turn the directory you started in Lab 01 into a real repository containing the **PayTrack API**
application that you will carry for the rest of the week. Along the way, practise the four
things that actually cause pain in real projects: staging selectively, writing useful commit
messages, reading history, and undoing mistakes safely.

## Prerequisites

- Lab 00 (git installed and configured) and Lab 01 (`~/devops-course/paytrack-api/docs/` exists)

🔁 **RECOVER — if you missed Lab 01**
```bash
mkdir -p ~/devops-course/paytrack-api/docs && cd ~/devops-course/paytrack-api
printf '# Value Stream Map\n\nTODO: complete in Lab 01.\n' > docs/value-stream.md
printf '# CALMS Assessment\n\nTODO: complete in Lab 01.\n' > docs/calms-assessment.md
```

---

## Step 1 — Initialise the repository

```bash
cd ~/devops-course/paytrack-api
git init
```
**What this does:** creates the `.git/` directory — the object database, the refs, the index,
and the config. Nothing about your files changes; git simply starts being able to track them.
Because Lab 00 set `init.defaultBranch main`, your first branch is `main`.

```bash
ls -a && ls .git
```
**What this does:** `-a` shows hidden entries so you can see `.git`. Listing inside it shows
`objects/` (all four object types live here), `refs/` (branches and tags — each a 41-byte
file), `HEAD` (a pointer to the current branch), and `config` (repository-local settings).

```bash
git status
```
**What this does:** the command you will run more than any other. Right now it reports
"No commits yet" and lists your `docs/` files as **untracked** — git can see them but is not
managing them.

---

## Step 2 — Bring in the PayTrack API application

```bash
git clone https://github.com/<your-org>/devops-professional.git ~/devops-course/course-material
```
**What this does:** clones the course material repository — the one containing these lab
guides and the PayTrack API source. `git clone` creates the directory, downloads the full
history, checks out the default branch and configures the remote `origin` automatically.
**Your trainer will give you the actual URL**; if you were given a zip instead, unzip it to
`~/devops-course/course-material` and skip to the copy below.

```bash
cp -r ~/devops-course/course-material/app ~/devops-course/paytrack-api/app
```
**What this does:** copies the application source into your repository. `-r` recurses into
subdirectories. Your repository is now yours — the course-material clone is only a source of
files and is never touched again.

```bash
tree -L 3 ~/devops-course/paytrack-api
```
**What this does:** shows the structure, limited to 3 levels deep. You should see:

```
paytrack-api/
├── app
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .flake8
│   ├── wsgi.py
│   ├── src
│   │   ├── __init__.py
│   │   ├── app.py       ← the Flask application
│   │   ├── config.py    ← 12-factor configuration
│   │   └── store.py     ← memory + postgres backends
│   └── tests
│       └── test_api.py  ← the suite CI will run
└── docs
    ├── calms-assessment.md
    ├── value-stream.md
    └── vsm-calc.py
```

---

## Step 3 — Run the application before you commit it

Never commit code you have not run.

```bash
cd ~/devops-course/paytrack-api/app
python3 -m venv .venv
source .venv/bin/activate
```
**What this does:** `venv` creates an isolated Python environment in `.venv/` so the course's
packages never collide with your system Python (which Ubuntu 24.04 protects under PEP 668).
`source` modifies your **current shell** to put `.venv/bin` first on `PATH` — which is why it
is `source` and not `./`. Your prompt now shows `(.venv)`.

```bash
pip install -r requirements-dev.txt
```
**What this does:** installs Flask, gunicorn, the Postgres driver, the Prometheus client, and
the dev tools (pytest, flake8, black, bandit, pip-audit). Every version is **pinned** —
that is what makes the build reproducible, and it is a requirement, not a style choice.

```bash
pytest
```
**What this does:** runs the test suite. Pytest reads `pytest.ini`, discovers `tests/`, and
runs everything named `test_*`. Expect **9 passed** in well under a second. The suite needs
no database because `config.DATABASE_URL` is empty, so the app uses the in-memory store —
this is exactly why the CI pipeline in Lab 04 will be fast and reliable.

```bash
python -m src.app
```
**What this does:** runs the Flask development server on port 8080. `-m` runs the module as a
script, which makes the package-relative imports in `app.py` resolve correctly.

Open a **second terminal** and probe it:

```bash
curl -s localhost:8080/health | jq
curl -s localhost:8080/api/v1/info | jq
curl -s -X POST localhost:8080/api/v1/authorisations \
  -H 'Content-Type: application/json' \
  -d '{"merchant":"NORTHGATE FUEL","amount_minor":4599,"currency":"GBP","card_last4":"4242"}' | jq
curl -s localhost:8080/api/v1/authorisations | jq
curl -s localhost:8080/metrics | head -20
```
**What each does:**
- `/health` — the **liveness** endpoint. Never touches the database, so a DB outage cannot
  cause a restart loop. Returns `{"status":"ok",...}`.
- `/api/v1/info` — identity: version, colour, environment, storage backend. You will use this
  constantly from day 4 onward to confirm *which* version is serving you.
- `POST /api/v1/authorisations` — records a card authorisation. `-X POST` sets the method,
  `-H` sets the content type, `-d` supplies the JSON body. Returns **201** with the stored row.
  **Note `amount_minor: 4599`** — that is £45.99 held as an integer number of pence.
  Money is never a float: `0.1 + 0.2 != 0.3` in binary floating point, and a rounding error
  in a ledger becomes a reconciliation break and then an audit finding.
  **Note also what the API refuses**: send `"pan": "4111111111111111"` and it returns 400.
  Accepting a full card number would pull this service — and every log and backup
  downstream of it — into PCI-DSS cardholder-data scope.
- `GET /api/v1/authorisations` — lists them back, proving the write worked.
- `/metrics` — Prometheus exposition format. Day 6 scrapes this.
- `| jq` pretty-prints and colourises JSON. `-s` silences curl's progress meter so the pipe
  stays clean.

Also open **http://localhost:8080/** in a browser: a blue banner reading *PayTrack API 1.0.0*.
That colour is driven by the `APP_COLOR` environment variable and is how you will *see*
blue-green and canary traffic splitting in Lab 16.

Stop the server with `Ctrl+C`, then:

```bash
deactivate
cd ~/devops-course/paytrack-api
```
**What this does:** `deactivate` removes the venv from your `PATH`. Then you return to the
repository root — **all git commands from here on run from the repository root.**

---

## Step 4 — Write `.gitignore` *before* the first commit

```bash
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.coverage
coverage.xml
*.egg-info/

# Environment & secrets  ── never commit these
.env
*.pem
*.key
secrets.yaml

# Terraform
.terraform/
*.tfstate
*.tfstate.*
crash.log

# Editors & OS
.vscode/
.idea/
.DS_Store
*.swp
EOF
```
**What this does:** tells git which paths to ignore. Three groups matter for different
reasons:
- **`.venv/`** — hundreds of megabytes of installed packages, reproducible from
  `requirements.txt`. Committing it bloats every clone forever.
- **`.env`, `*.pem`, `*.key`** — secrets. Git history is permanent and every clone has a full
  copy, so a committed secret is a leaked secret even after you delete it.
- **`*.tfstate`** — Terraform state contains **plaintext credentials**. You will meet this in
  Lab 13; the ignore rule goes in now so you can never make the mistake.

> ⚠️ **`.gitignore` only affects files git is not already tracking.** If you commit a file and
> *then* add it to `.gitignore`, git keeps tracking it. Untrack it with
> `git rm --cached <file>`.

---

## Step 5 — Stage and inspect before committing

```bash
git status
```
**What this does:** shows untracked files. Note that `.venv/` no longer appears — the ignore
rule is working.

```bash
git add .gitignore docs/
git status
```
**What this does:** `git add` copies the current content of those paths into the **index**
(the staging area) — the proposed contents of the next commit. `git status` now shows them
under "Changes to be committed", in green.

```bash
git diff --staged
```
**What this does:** shows what is in the index but not yet committed — **this is your last
chance to review exactly what you are about to record.** Get into the habit of running it
every time; it is how you catch the debug print, the commented-out block, and the API key.
`git diff` with no flag shows the opposite: working-tree changes *not* yet staged.

---

## Step 6 — Your first commit

```bash
git commit -m "docs: add value stream map and CALMS assessment

Baseline analysis from Lab 01. Flow efficiency measured at X%, with the
constraint identified as <step>. These figures are the baseline for the
Day 6 DORA comparison."
```
**What this does:** creates a commit object from the index: a tree hash, the parent
(none — this is the root commit), your name and email from Lab 00, timestamps, and the
message. **The commit is immutable and content-addressed** — its SHA is derived from all of
that.

**The message format matters.** The convention used throughout this course is
[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <subject, imperative mood, ≤ 50 chars, no full stop>
                                          ← blank line, required
<body: WHY the change was made, wrapped at 72 chars. The diff already
shows WHAT changed; only you can record why.>
```
Types: `feat` · `fix` · `docs` · `test` · `refactor` · `chore` · `ci` · `build` · `perf`.
This is not pedantry: it lets you generate release notes automatically, makes `git log`
readable, and is what tools like semantic-release consume.

```bash
git add app/
git commit -m "feat: add PayTrack API service

Flask REST API for recording service health checks.

- /health   liveness probe, no external dependencies
- /ready    readiness probe, verifies the storage backend
- /metrics  Prometheus exposition format
- pluggable storage: in-memory for tests, Postgres for deployment

Config is read entirely from the environment so one image can be promoted
across every environment without a rebuild."
```
**What this does:** stages the whole application directory and commits it as a second,
separate commit. Two commits rather than one because they are **two unrelated logical
changes** — and that is what makes `git log`, `git revert` and `git bisect` useful later.

✅ **Checkpoint**
```bash
git log --oneline
```
Two commits, newest first, each with a 7-character abbreviated SHA.

---

## Step 7 — Read the history

```bash
git log --oneline --graph --decorate --all
```
**What this does:** the single most useful log invocation.
`--oneline` = one line per commit · `--graph` = draw the DAG with ASCII branch lines ·
`--decorate` = show branch and tag pointers · `--all` = every branch, not just the current
one. Make it an alias:

```bash
git config --global alias.lg "log --oneline --graph --decorate --all"
git lg
```
**What this does:** registers `git lg` as a permanent shortcut in your global config.

```bash
git show HEAD
git show HEAD~1 --stat
```
**What this does:** `git show HEAD` prints the most recent commit's metadata and full diff.
`HEAD~1` means "one commit before HEAD"; `--stat` prints only a summary of files changed and
line counts instead of the whole diff. Learn this notation — `HEAD~3`, `HEAD^`, and a raw
SHA all work anywhere a commit is expected.

```bash
git log --follow -p app/src/app.py | head -40
```
**What this does:** shows the full change history of one file. `-p` includes the patch;
`--follow` keeps tracking it across renames.

---

## Step 8 — Make a change, and practise undoing it three ways

```bash
sed -i 's/APP_VERSION", "1.0.0"/APP_VERSION", "1.1.0"/' app/src/config.py
git diff
```
**What this does:** `sed -i` edits the file **in place**; `s/old/new/` substitutes. Then
`git diff` shows the unstaged change: one `-` line and one `+` line.

**Undo method 1 — discard an unstaged working-tree change:**
```bash
git restore app/src/config.py
git diff
```
**What this does:** overwrites the working-tree file with the version from the index (here,
from `HEAD`). The diff is now empty. ⚠️ **This is destructive and unrecoverable** — the edit
was never recorded anywhere.

**Undo method 2 — unstage something you staged by mistake:**
```bash
sed -i 's/APP_VERSION", "1.0.0"/APP_VERSION", "1.1.0"/' app/src/config.py
git add app/src/config.py
git status                       # staged
git restore --staged app/src/config.py
git status                       # modified but NOT staged — the edit is still there
```
**What this does:** `--staged` removes the path from the index while leaving the working tree
untouched. This is the safe undo: nothing is lost.

**Undo method 3 — revert a commit that already exists:**
```bash
git add app/src/config.py
git commit -m "chore: bump version to 1.1.0"
git log --oneline
git revert HEAD --no-edit
git log --oneline
```
**What this does:** `git revert` creates a **new** commit that applies the inverse of the
target commit. `--no-edit` accepts the generated message. You now have three commits: the
bump, and the revert of the bump.

> 🔴 **`revert` vs `reset` — the rule that saves careers.**
> `git revert` **adds** a commit undoing a change. History is preserved, everyone's clone
> stays consistent. **Safe on shared branches.**
> `git reset --hard <sha>` **moves the branch pointer backwards**, discarding commits. It
> rewrites history and requires a force-push to share. **Never do this to a branch other
> people have.** Use `reset` only on your own un-pushed work.

---

## Step 9 — Tag the release

```bash
git tag -a v1.0.0 -m "PayTrack API 1.0.0 — initial service"
git tag
git show v1.0.0 | head -12
```
**What this does:** `-a` creates an **annotated** tag — a real git object with a tagger,
date, message and optional GPG signature. A *lightweight* tag (`git tag v1.0.0`, no `-a`) is
just a pointer with none of that metadata. **Always use `-a` for releases**: the metadata is
your audit trail, and `git describe` only considers annotated tags by default.

---

## ✅ Final checkpoint

```bash
git log --oneline --graph --decorate
git status
```
Expect **four commits**, tag `v1.0.0` visible, and `working tree clean`.

```bash
git count-objects -vH
```
**What this does:** reports how many objects your repository holds and how much space they
occupy — a concrete look at the object database from Module 2 §2.2.

---

## 🧩 Stretch (homework, 15 minutes)

```bash
git add -p app/src/config.py
```
**What this does:** **interactive staging.** Git presents each *hunk* of your changes and
asks whether to stage it (`y`/`n`/`s` to split a hunk further/`q` to quit). This is how you
turn a messy working tree containing three unrelated fixes into three clean, separately
revertable commits. It is the single most underused git feature.

```bash
git commit --amend -m "chore: bump version to 1.1.0 for the Docker lab"
```
**What this does:** replaces the most recent commit with a new one (new SHA) containing the
current index plus the new message. Useful for fixing a typo you just made.
⚠️ **Only ever amend a commit you have not pushed.** Amending a pushed commit rewrites shared
history — the Golden Rule from Module 2 §2.5.

```bash
git stash push -m "wip: experiment"
git stash list
git stash pop
```
**What this does:** `stash push` saves your uncommitted changes onto a stack and returns the
working tree to a clean state — for when you need to switch branches urgently mid-thought.
`pop` re-applies the top of the stack and removes it. `git stash list` shows what is saved;
stashes are easy to forget about, so check it occasionally.

---

## 🎯 Outcome

`~/devops-course/paytrack-api` is a git repository with four commits, an annotated tag, a
correct `.gitignore`, a tested Flask application, and your Lab 01 analysis — all under
version control.

**Next:** [Lab 03 — Branching and Collaboration](../lab-03-branching-and-collaboration/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Publish the course-material repo before day 1** and put the clone URL on the slide. If
  network access is restricted, hand out a zip and adapt step 2.
- **The three things that go wrong:**
  1. `pip install` fails with *externally-managed-environment* — they skipped the venv.
     Point them back to `python3 -m venv .venv && source .venv/bin/activate`.
  2. They run `python src/app.py` instead of `python -m src.app` and get
     `ImportError: attempted relative import`. Explain why `-m` matters; it is a useful
     Python lesson that pays off in the Dockerfile on day 3.
  3. Someone commits `.venv/`. Perfect teaching moment: `git rm -r --cached .venv` and a
     discussion of why history is permanent.
- **Do not rush step 8.** revert-vs-reset is the highest-value five minutes in the lab.
  Ask the room who has force-pushed a shared branch — the stories are excellent material.
- **Debrief question:** "Your teammate says they will 'just reset main back to yesterday'.
  What do you say, and what do you suggest instead?"
</details>
