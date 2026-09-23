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

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction below is **one command in one grey box**,
numbered in the order you run it.

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. It shows a line ending in `$` — the prompt. |
| **How do I run a command?** | Click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait for the `$` prompt to return. |
| **Nothing was printed!** | Normal — many commands say nothing when they succeed. |
| **The last line is `:` or `(END)`** | You are in a scrollable view. Press `q` to get back to the prompt. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel. |
| **An editor opened** | That is **nano**. Save with `Ctrl` + `O`, `Enter`; leave with `Ctrl` + `X`. |

**Symbols in the boxes:** `~` is your home folder · `cd` moves into a folder · `>` writes a file ·
`>>` adds to the end of a file · `|` passes one command's output to the next · `#` starts a note
the computer ignores. A box that begins `cat > … <<'EOF'` and ends with `EOF` is **one** command
that writes a file — copy all of it.

🔁 **RECOVER — if you missed Lab 01**, run these four commands; otherwise skip to Step 1.

```bash
mkdir -p ~/devops-course/paytrack-api/docs
```
**What this does:** creates the project folder and a `docs` folder inside it.

```bash
cd ~/devops-course/paytrack-api
```
**What this does:** moves into the project folder.

```bash
printf '# Value Stream Map\n\nTODO: complete in Lab 01.\n' > docs/value-stream.md
```
**What this does:** writes a placeholder file. `printf` prints text and `>` sends it into a file
instead of onto the screen; `\n` means "new line".

```bash
printf '# CALMS Assessment\n\nTODO: complete in Lab 01.\n' > docs/calms-assessment.md
```
**What this does:** the second placeholder. You now have what Lab 01 would have produced.

---

## Step 1 — Initialise the repository

**1. Go to the project folder.**

```bash
cd ~/devops-course/paytrack-api
```
**What this does:** makes it your current folder. **Every git command in this lab runs from
here** — git always works on the folder you are standing in.

**2. Turn the folder into a repository.**

```bash
git init
```
**What this does:** creates the hidden `.git/` folder — the object database, the refs, the index
and the config. None of your files change; git simply starts being able to track them. Because
Lab 00 set `init.defaultBranch main`, your first branch is `main`.

**3. Look at what appeared.**

```bash
ls -a
```
**What this does:** `ls` **l**i**s**ts the folder; `-a` includes names beginning with a dot, which
Linux hides by default. You can now see `.git`.

**4. Look inside it.**

```bash
ls .git
```
**What this does:** lists git's own storage: `objects/` (every version of every file lives here),
`refs/` (branches and tags — each one a tiny file), `HEAD` (a pointer to the branch you are on)
and `config` (settings for this repository only).

**5. Ask git how things stand.**

```bash
git status
```
**What this does:** the command you will run more than any other. Right now it reports "No commits
yet" and lists your `docs/` files as **untracked** — git can see them but is not managing them.

---

## Step 2 — Bring in the PayTrack API application

**1. Download the course material.**

```bash
git clone https://github.com/kumbulanit/devops_professional.git ~/devops-course/course-material
```
**What this does:** `git clone <address> <folder>` copies a project from the internet — here the
repository holding these lab guides and the PayTrack API source. It creates the folder, downloads
the full history, and checks out the latest files.

> 🔑 **Two different repositories are in play this week — do not mix them up.**
>
> | | Repository | You |
> |---|---|---|
> | **Course material** | `kumbulanit/devops_professional` | **read only.** A source of files; you never push to it |
> | **Your project** | `paytrack-api`, under **your own** GitHub account (Lab 03) | own it, push to it, and it carries your work for six days |
>
> That is why the course URL below is concrete and every `paytrack-api` URL says
> `<your-username>` — substitute your own GitHub username there.

**2. Copy the application into your repository.**

```bash
cp -r ~/devops-course/course-material/app ~/devops-course/paytrack-api/app
```
**What this does:** `cp` **c**o**p**ies; `-r` means "and everything inside the folder". Your
repository is now yours — the course-material copy is only a source of files and is never touched
again.

**3. Look at the structure.**

```bash
tree -L 3 ~/devops-course/paytrack-api
```
**What this does:** draws the folder as a tree, three levels deep (`-L 3`). You should see:

```
paytrack-api/
├── app
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   ├── pytest.ini
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

> `tree` hides names that begin with a dot, so two files are not shown: `app/.flake8` (style
> rules, used in Lab 04) and the `.git` folder itself. `tree -a -L 2 app` would show them.

---

## Step 3 — Run the application before you commit it

Never commit code you have not run.

**1. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api/app
```
**What this does:** the Python project lives here. This is the only part of the lab that does not
run from the repository root.

**2. Create an isolated Python environment.**

```bash
python3 -m venv .venv
```
**What this does:** `venv` makes a private copy of Python in a folder called `.venv`, so the
course's packages never collide with the system's. Ubuntu 24.04 insists on this. Nothing is
printed; it takes a few seconds.

**3. Switch your terminal into that environment.**

```bash
source .venv/bin/activate
```
**What this does:** `source` runs a file **in your current shell** (rather than in a new one),
which is what lets it change your settings: `.venv/bin` goes to the front of your `PATH`, so
`python` and `pip` now mean the private copies. Your prompt gains a `(.venv)` marker — that is how
you know it worked.

**4. Install the application's packages.**

```bash
pip install -r requirements-dev.txt
```
**What this does:** `pip` is Python's installer; `-r <file>` means "install everything listed in
this file" — Flask, gunicorn, the Postgres driver, the Prometheus client, and the development
tools (pytest, flake8, black, bandit, pip-audit). Every version is **pinned** to an exact number:
that is what makes a build reproducible, and it is a requirement, not a style choice.

**5. Run the tests.**

```bash
pytest
```
**What this does:** finds every file named `test_*` under `tests/` and runs it. Expect
**19 passed** in well under a second. The suite needs no database, because `DATABASE_URL` is
unset and the app then uses an in-memory store — which is exactly why the CI pipeline in Lab 04
will be fast and reliable.

**6. Start the application.**

```bash
python -m src.app
```
**What this does:** runs the Flask development server on port 8080. `-m` runs the code as a
*module*, which makes its internal imports resolve correctly (`python src/app.py` would fail —
a useful Python lesson that pays off in the Dockerfile on day 3). **This command does not
finish**: it keeps running and printing request logs. Leave it.

**Now open a second terminal** (`Ctrl` + `Alt` + `T` again) and try the API. The five commands
below run in that second window.

**7. Ask whether it is alive.**

```bash
curl -s localhost:8080/health | jq
```
**What this does:** `curl` fetches a web address from the command line (`-s` hides its progress
meter), and `| jq` lays the JSON answer out readably. `/health` is the **liveness** endpoint: it
never touches the database, so a database outage cannot put the service into a restart loop. You
get `{"status":"ok", …}`.

**8. Ask what it is.**

```bash
curl -s localhost:8080/api/v1/info | jq
```
**What this does:** returns version, colour, environment and storage backend. From day 4 you use
this constantly to confirm *which* version is answering you.

**9. Record a card authorisation.**

```bash
curl -s -X POST localhost:8080/api/v1/authorisations \
  -H 'Content-Type: application/json' \
  -d '{"merchant":"NORTHGATE FUEL","amount_minor":4599,"currency":"GBP","card_last4":"4242"}' | jq
```
**What this does:** one command over three lines — copy all of it. `-X POST` sends data instead of
asking for a page, `-H` sets the content type and `-d` carries the JSON body. You get **201** and
the stored record back.
- **Note `amount_minor: 4599`** — that is £45.99 held as a whole number of pence. Money is never a
  decimal fraction in a computer: `0.1 + 0.2 != 0.3` in binary, and a rounding error in a ledger
  becomes a reconciliation break and then an audit finding.
- **Note what the API refuses:** send `"pan": "4111111111111111"` and it returns 400. Accepting a
  full card number would pull this service — and every log and backup downstream of it — into
  PCI-DSS cardholder-data scope.

**10. List what it stored.**

```bash
curl -s localhost:8080/api/v1/authorisations | jq
```
**What this does:** returns the authorisations, proving the write worked.

**11. Look at its metrics.**

```bash
curl -s localhost:8080/metrics | head -20
```
**What this does:** prints the first 20 lines of the Prometheus metrics page — counters and timings
in a plain-text format. Day 6 collects these.

Also open **http://localhost:8080/** in a browser: a blue banner reading *PayTrack API 1.0.0*.
That colour comes from the `APP_COLOR` setting and is how you will *see* blue-green and canary
traffic splitting in Lab 16.

**12. Stop the server.** Go back to the **first** terminal and press `Ctrl` + `C`. The prompt
returns.

**13. Leave the Python environment.**

```bash
deactivate
```
**What this does:** removes `.venv` from your `PATH`; the `(.venv)` marker disappears. The
environment still exists — `source .venv/bin/activate` brings it back whenever you need it.

**14. Return to the repository root.**

```bash
cd ~/devops-course/paytrack-api
```
**What this does:** **every git command from here on runs from the repository root.**

---

## Step 4 — Write `.gitignore` *before* the first commit

**1. Write the file.** One command — copy the whole box, including the final `EOF`:

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
**What this does:** writes the list of paths git should ignore. Nothing is printed. Three groups
matter, for different reasons:
- **`.venv/`** — hundreds of megabytes of installed packages, all reproducible from
  `requirements.txt`. Committing it bloats every clone, forever.
- **`.env`, `*.pem`, `*.key`** — secrets. Git history is permanent and every clone holds a full
  copy, so a committed secret is a leaked secret even after you delete it.
- **`*.tfstate`** — Terraform state contains **passwords in plain text**. You meet this in Lab 13;
  the rule goes in now so you cannot make the mistake.

> ⚠️ **`.gitignore` only affects files git is not already tracking.** If you commit a file and
> *then* add it to `.gitignore`, git keeps tracking it. Untrack it with
> `git rm --cached <file>`.

---

## Step 5 — Stage and inspect before committing

**1. See what git can see.**

```bash
git status
```
**What this does:** lists the untracked files. Note that `.venv/` no longer appears — the ignore
rule is working.

**2. Stage the files you want in the first commit.**

```bash
git add .gitignore docs/
```
**What this does:** `git add` copies the current content of those paths into the **index** (also
called the staging area) — your proposal for the next commit. Nothing is printed.

**3. Confirm what is staged.**

```bash
git status
```
**What this does:** the same files now appear under "Changes to be committed", in green.

**4. Read exactly what you are about to record.**

```bash
git diff --staged
```
**What this does:** shows the difference between the last commit and the index — **your last
chance to review what you are about to commit.** Make this a habit; it is how you catch the debug
line, the commented-out block and the API key. (`git diff` without `--staged` shows the opposite:
changes you have **not** staged.) Press `q` to leave the view.

---

## Step 6 — Your first commit

**1. Commit the documents.**

```bash
git commit -m "docs: add value stream map and CALMS assessment

Baseline analysis from Lab 01. Flow efficiency measured at X%, with the
constraint identified as <step>. These figures are the baseline for the
Day 6 DORA comparison."
```
**What this does:** one command spanning several lines — copy all of it, both quote marks
included. It records everything in the index as a commit: a snapshot, the parent commit (none —
this is the first), your name and email from Lab 00, the time, and the message. **A commit cannot
be changed afterwards**: its identifier is calculated from all of that content.

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

**2. Stage the application.**

```bash
git add app/
```
**What this does:** stages the whole application folder — the ignore rules keep `.venv/` and the
caches out.

**3. Commit it separately.**

```bash
git commit -m "feat: add PayTrack API service

Flask REST API for recording service health checks.

- /health   liveness probe, no external dependencies
- /ready    readiness probe, verifies the storage backend
- /metrics  Prometheus exposition format
- pluggable storage: in-memory for tests, Postgres for deployment

Config is read entirely from the environment so one image can be promoted
across every environment without a rebuild."
```
**What this does:** a second commit, because this is a **separate logical change** from the
documents. Small, single-purpose commits are what make `git log`, `git revert` and `git bisect`
useful later.

✅ **Checkpoint**

```bash
git log --oneline
```
**What this does:** prints one line per commit, newest first. Expect two, each starting with a
short identifier of about seven characters.

---

## Step 7 — Read the history

**1. Draw the history.**

```bash
git log --oneline --graph --decorate --all
```
**What this does:** the single most useful version of `git log`. `--oneline` = one line per
commit · `--graph` = draw the branch lines · `--decorate` = show branch and tag names · `--all` =
every branch, not just this one.

**2. Save it as a shortcut.**

```bash
git config --global alias.lg "log --oneline --graph --decorate --all"
```
**What this does:** an **alias** is your own name for a longer command. `--global` means it works
in every repository on this machine. Nothing is printed.

**3. Use the shortcut.**

```bash
git lg
```
**What this does:** exactly what command 1 did, with eight fewer words to type.

**4. Look at the newest commit in full.**

```bash
git show HEAD
```
**What this does:** `HEAD` means "where I am now" — the newest commit of the branch you are on.
You get its author, date, message and every changed line. Press `q` to leave.

**5. Summarise the one before it.**

```bash
git show HEAD~1 --stat
```
**What this does:** `HEAD~1` is "one commit before HEAD" (`HEAD~3` would be three back), and
`--stat` prints just a summary of which files changed and by how many lines, instead of the whole
difference. This notation works anywhere git expects a commit.

**6. Follow one file through history.**

```bash
git log --follow -p app/src/app.py | head -40
```
**What this does:** the history of a single file: `-p` includes the changes themselves,
`--follow` keeps tracking the file across renames, and `| head -40` stops it after 40 lines.

---

## Step 8 — Make a change, and practise undoing it three ways

### Undo method 1 — discard an edit you have not staged

**1. Make an edit.**

```bash
sed -i 's/APP_VERSION", "1.0.0"/APP_VERSION", "1.1.0"/' app/src/config.py
```
**What this does:** `sed` edits text; `-i` means "**i**n the file itself" and `s/old/new/`
substitutes one piece of text for another. Nothing is printed — the version is now 1.1.0.

**2. See the change.**

```bash
git diff
```
**What this does:** shows what you changed but have not staged: one `-` line (removed) and one
`+` line (added).

**3. Throw it away.**

```bash
git restore app/src/config.py
```
**What this does:** rewrites the file from the last commit. ⚠️ **The edit is gone and cannot be
recovered** — it was never recorded anywhere.

**4. Confirm.**

```bash
git diff
```
**What this does:** prints nothing. The file matches the last commit again.

### Undo method 2 — unstage something you staged by mistake

**1. Make the edit again.**

```bash
sed -i 's/APP_VERSION", "1.0.0"/APP_VERSION", "1.1.0"/' app/src/config.py
```
**What this does:** as before — the version is 1.1.0 in your working files.

**2. Stage it.**

```bash
git add app/src/config.py
```
**What this does:** puts the change into the index, ready to be committed.

**3. Check.**

```bash
git status
```
**What this does:** the file is listed under "Changes to be committed".

**4. Take it back out of the index.**

```bash
git restore --staged app/src/config.py
```
**What this does:** `--staged` removes the path from the index **without touching your files**.
This is the safe undo: nothing is lost.

**5. Check again.**

```bash
git status
```
**What this does:** the file is now under "Changes not staged for commit" — still edited, no longer
staged.

### Undo method 3 — reverse a commit that already exists

**1. Stage the change.**

```bash
git add app/src/config.py
```
**What this does:** back into the index.

**2. Commit it.**

```bash
git commit -m "chore: bump version to 1.1.0"
```
**What this does:** records the version bump as a third commit.

**3. Look at the history.**

```bash
git log --oneline
```
**What this does:** three commits, the bump on top.

**4. Reverse it.**

```bash
git revert HEAD --no-edit
```
**What this does:** creates a **new** commit that undoes exactly what the target commit did.
`--no-edit` accepts the generated message instead of opening an editor.

**5. Look again.**

```bash
git log --oneline
```
**What this does:** **four** commits now: the bump, and the revert of the bump. Nothing was
deleted — the record shows both the change and the decision to undo it. The file says `1.0.0`
again.

> 🔴 **`revert` vs `reset` — the rule that saves careers.**
> `git revert` **adds** a commit undoing a change. History is preserved, everyone's clone
> stays consistent. **Safe on shared branches.**
> `git reset --hard <sha>` **moves the branch pointer backwards**, discarding commits. It
> rewrites history and requires a force-push to share. **Never do this to a branch other
> people have.** Use `reset` only on your own un-pushed work.

---

## Step 9 — Tag the release

**1. Name this commit as version 1.0.0.**

```bash
git tag -a v1.0.0 -m "PayTrack API 1.0.0 — initial service"
```
**What this does:** `-a` creates an **annotated** tag — a real object recording who tagged it,
when, why, and optionally a signature. (Without `-a` you get a *lightweight* tag: a bare pointer
with none of that.) **Always use `-a` for releases**: the metadata is your audit trail, and
`git describe` only considers annotated tags by default.

**2. List your tags.**

```bash
git tag
```
**What this does:** prints `v1.0.0`.

**3. Look at it.**

```bash
git show v1.0.0 | head -12
```
**What this does:** prints the tag's own details and the start of the commit it points at;
`| head -12` keeps it to twelve lines.

---

## ✅ Final checkpoint

**1. Look at the whole history.**

```bash
git log --oneline --graph --decorate
```
**What this does:** expect **four commits** with `v1.0.0` shown against the second one.

**2. Confirm nothing is outstanding.**

```bash
git status
```
**What this does:** must say `working tree clean` — everything is committed.

**3. Look at the object database.**

```bash
git count-objects -vH
```
**What this does:** reports how many objects your repository holds and how much space they take
(`-H` in human-readable units) — a concrete look at the storage model from Module 2 §2.2.

---

## 🧩 Stretch (homework, 15 minutes)

**1. Make an edit to practise on.**

```bash
sed -i 's/APP_VERSION", "1.0.0"/APP_VERSION", "1.1.0"/' app/src/config.py
```
**What this does:** bumps the version again, so there is something to stage.

**2. Stage it piece by piece.**

```bash
git add -p app/src/config.py
```
**What this does:** **interactive staging.** Git shows each changed block (**hunk**) and asks
`Stage this hunk [y,n,q,a,d,s,…]?` — press `y` then `Enter` to stage this one. `n` skips a hunk,
`s` splits it into smaller ones, `q` quits. This is how you turn a messy working folder holding
three unrelated fixes into three clean, separately revertable commits. It is the single most
underused git feature.

**3. Commit it.**

```bash
git commit -m "chore: bump version to 1.1.0"
```
**What this does:** records the staged hunk as a fifth commit.

**4. Rewrite that commit's message.**

```bash
git commit --amend -m "chore: bump version to 1.1.0 for the Docker lab"
```
**What this does:** **replaces** the previous commit with a new one — same content, new message,
new identifier. ⚠️ **Only ever amend a commit you have not pushed.** Amending a pushed commit
rewrites shared history — the Golden Rule from Module 2 §2.5.

**5. Start another edit, then get interrupted.**

```bash
printf '\n# TODO: ask Risk about the referral limit\n' >> app/src/config.py
```
**What this does:** `>>` adds a line to the end of the file — an unfinished thought, the kind of
thing that is never ready to commit.

**6. Put it on a shelf.**

```bash
git stash push -m "wip: experiment"
```
**What this does:** saves your uncommitted changes onto a stack and returns your files to a clean
state — for when you must switch branches urgently mid-thought.

**7. See what is on the shelf.**

```bash
git stash list
```
**What this does:** lists saved stashes, newest first. They are easy to forget about, so look
occasionally.

**8. Take it back.**

```bash
git stash pop
```
**What this does:** re-applies the top of the stack and removes it from the list. Your TODO line
is back.

**9. Tidy up the experiment.**

```bash
git restore app/src/config.py
```
**What this does:** throws away the TODO line.

**10. Undo the version bump, so the next labs match the guide.**

```bash
git reset --hard HEAD~1
```
**What this does:** moves the branch back one commit **and** resets your files to match, removing
the 1.1.0 bump entirely. This is safe here only because that commit was never pushed anywhere —
which is exactly the distinction the red box in Step 8 makes. `git log --oneline` should show four
commits again.

---

## 🎯 Outcome

`~/devops-course/paytrack-api` is a git repository with four commits, an annotated tag, a
correct `.gitignore`, a tested Flask application, and your Lab 01 analysis — all under
version control.

**Next:** [Lab 03 — Branching and Collaboration](../lab-03-branching-and-collaboration/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **The course material is published at `github.com/kumbulanit/devops_professional`** and the
  labs clone it by that exact URL. If network access is restricted in the room, hand out a zip
  and adapt step 2 (unzip to `~/devops-course/course-material`).
- **Say the two-repo distinction out loud** before they start: the course repo is read-only to
  them; `paytrack-api` under their own account is the one they own. Delegates who miss this
  spend Lab 03 trying to push to somebody else's repository.
- **The three things that go wrong:**
  1. `pip install` fails with *externally-managed-environment* — they skipped the venv.
     Point them back to `python3 -m venv .venv` and `source .venv/bin/activate`.
  2. They run `python src/app.py` instead of `python -m src.app` and get
     `ImportError: attempted relative import`. Explain why `-m` matters; it is a useful
     Python lesson that pays off in the Dockerfile on day 3.
  3. Someone commits `.venv/`. Perfect teaching moment: `git rm -r --cached .venv` and a
     discussion of why history is permanent.
- **Two terminals from Step 3 onwards.** Half the room will try to run `curl` in the window that
  is running the server. Say it before they start, and show the `Ctrl` + `C` that stops it.
- **Do not rush step 8.** revert-vs-reset is the highest-value five minutes in the lab.
  Ask the room who has force-pushed a shared branch — the stories are excellent material.
- **Debrief question:** "Your teammate says they will 'just reset main back to yesterday'.
  What do you say, and what do you suggest instead?"
</details>
