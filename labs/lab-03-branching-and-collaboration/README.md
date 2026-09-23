# Lab 03 — Branching, Pull Requests and Team Collaboration

| | |
|---|---|
| **Day** | 2 |
| **Duration** | 45 minutes — **work in pairs or threes** |
| **Module** | 2 — Version Control and CI |
| **You will produce** | A GitHub repository with branch protection, a merged PR, and a resolved merge conflict |
| **Feeds into** | Lab 04 (CI runs on these PRs), Lab 15 (the pipeline pushes to this repo) |

---

## Objective

Put your Lab 02 repository on GitHub, enforce a branching strategy with server-side rules,
work on it as a team, and deliberately create and resolve a merge conflict — because the
first time you meet one should not be in production at 17:45 on a Friday.

**Free tier used:** GitHub Free — unlimited public and private repositories, unlimited
collaborators, branch protection on public repositories.

## Prerequisites

- Lab 02 complete (`~/devops-course/paytrack-api` with four commits)
- A free GitHub account, and **two or three delegates working together**

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction is **one command in one grey box**, numbered in
the order you run it. This lab moves between the **terminal** and the **GitHub website**; each
instruction says which.

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. It shows a line ending in `$` — the prompt. |
| **How do I run a command?** | Click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait for the prompt. |
| **Nothing was printed!** | Normal — many commands say nothing when they succeed. |
| **The last line is `:` or `(END)`** | A scrollable view. Press `q`. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel. |
| **An editor opened** | That is **nano**: save with `Ctrl` + `O`, `Enter`; leave with `Ctrl` + `X`. |

**Symbols in the boxes:** `~` your home folder · `cd` move into a folder · `>` write a file ·
`>>` add to the end of a file · `|` pass output to the next command · `&&` only if that worked ·
`||` only if that failed · `$(…)` run this first and use its answer. A box that begins
`cat > … <<'EOF'` or `python3 - <<'PY'` and ends with that word is **one** command — copy all of
it, final line included.

**Placeholders to replace, every time you see them:** `<your-username>` is **your** GitHub
username, and `<maintainer>` is the GitHub username of whoever owns the team repository. Replace
the angle brackets too.

**One command in Part 2 fails on purpose** — the text says so before the box. That rejection is
the proof the lab is looking for.

🔁 **RECOVER — if Lab 02 is incomplete.** Ten commands that rebuild what Lab 02 would have left
you. ⚠️ The third one **deletes** any earlier attempt, including your Lab 01 notes — copy `docs/`
somewhere else first if you want to keep them.

```bash
mkdir -p ~/devops-course
```
**What this does:** creates the course folder if it is not there.

```bash
cd ~/devops-course
```
**What this does:** moves into it.

```bash
rm -rf paytrack-api
```
**What this does:** **deletes** the project folder and everything in it. `-r` means "and its
contents", `-f` means "do not ask". There is no recycle bin.

```bash
git clone https://github.com/kumbulanit/devops_professional.git course-material 2>/dev/null || true
```
**What this does:** downloads the course material. `2>/dev/null` hides the error if you already
have it, and `|| true` stops that error ending the sequence.

```bash
mkdir -p paytrack-api/docs
```
**What this does:** creates the project folder again, with a `docs` folder inside (Part 6 writes
there).

```bash
cp -r course-material/app paytrack-api/app
```
**What this does:** copies the application in. `-r` includes everything inside the folder.

```bash
cd paytrack-api
```
**What this does:** moves into the project.

```bash
printf '# Value Stream Map\n\nTODO: complete in Lab 01.\n' > docs/value-stream.md
```
**What this does:** writes a placeholder for the Lab 01 document.

```bash
printf '__pycache__/\n.venv/\n.pytest_cache/\n.coverage\n.env\n*.pem\n*.key\n*.tfstate\n' > .gitignore
```
**What this does:** writes the ignore list **before** the first commit, so no virtual environment
or secret can ever be committed.

```bash
git init
```
**What this does:** turns the folder into a git repository.

```bash
git add .
```
**What this does:** stages everything in the folder (the ignore list keeps the junk out).

```bash
git commit -m "feat: add PayTrack API service"
```
**What this does:** makes the first commit.

```bash
git tag -a v1.0.0 -m "PayTrack API 1.0.0 — initial service"
```
**What this does:** adds the annotated release tag that Step 1.2 pushes.

---

## Roles

Decide now, and write it down:

| Role | Who | Does |
|---|---|---|
| **Maintainer** | one person | Owns the repository, configures protection, reviews and merges |
| **Contributor A** | | Adds a feature on a branch |
| **Contributor B** | | Adds a *different* feature that touches the **same lines** — creating the conflict |

Working alone? Do all three roles yourself, in the one clone the steps use
(`~/devops-course/paytrack-api-team`). Contributor B's steps start by switching back to `main`, so
the two branches stay separate. You lose the review conversation but keep every mechanic.

---

## Part 1 — The Maintainer creates the remote (5 min)

> ⚠️ **This is YOUR repository, not the course one.** Everywhere below that says
> `<your-username>` or `<maintainer>`, substitute the relevant GitHub account —
> the maintainer's account for the shared team repo, yours for your own clones.
> `kumbulanit/devops_professional` is the *course material* and is read-only to you.

### Step 1.1 — Create an empty repository on GitHub

In your browser, go to **https://github.com/new** and set:

| Field | Value | Why |
|---|---|---|
| Repository name | `paytrack-api` | |
| Visibility | **Public** | Free unlimited Actions minutes and free GHCR packages — you need both this week |
| Initialize with README | **☐ unticked** | You already have commits; an initialised remote creates unrelated history and a painful first push |
| .gitignore / licence | **none** | Same reason |

Then select **Create repository**. Leave the page open.

### Step 1.2 — Connect and push

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api
```
**What this does:** the repository you built in Lab 02. Git commands only work on the folder you
are standing in.

**2. Tell git where the GitHub copy lives.**

```bash
git remote add origin https://github.com/<your-username>/paytrack-api.git
```
**What this does:** a **remote** is a saved address with a short name. `origin` is only a
convention — the usual name for "the copy I push to". Replace `<your-username>` with yours.
Nothing is printed.

**3. Check the spelling.**

```bash
git remote -v
```
**What this does:** `-v` lists each remote twice, for fetching and for pushing. Read the address
carefully — a typo here causes every push to fail.

**4. Upload your commits.**

```bash
git push -u origin main
```
**What this does:** sends your history to GitHub and records (`-u`) that your `main` belongs with
GitHub's `main`. From now on a bare `git push` or `git pull` knows where to go, and `git status`
can say "ahead by 2 commits".

**5. Upload the tag.**

```bash
git push origin v1.0.0
```
**What this does:** **tags are not pushed automatically** — you name them. Refresh the GitHub page
and your files are there.

> ⚠️ **Authentication.** GitHub does not accept account passwords over HTTPS. If you did
> **Lab 00 Step 8.1** (`gh auth login … --scopes workflow`), git is already signed in — skip this box.
> Otherwise use a **Personal Access Token** (Settings → Developer settings → Personal access tokens →
> Fine-grained → repository access to `paytrack-api`, permissions **`Contents: Read and write`** and
> **`Workflows: Read and write`** — Lab 04 cannot push `.github/workflows/` without the second).
> Cache it so you type it once:
> ```bash
> git config --global credential.helper "cache --timeout=28800"
> ```
> **What this does:** keeps the token in memory for 8 hours. SSH keys are the better
> long-term answer (`ssh-keygen -t ed25519 -C "you@example.com"`, then add the public key to
> GitHub and use the `git@github.com:` URL).

### Step 1.3 — Add your teammates

On GitHub: **Settings → Collaborators → Add people** → their GitHub usernames → **Write** access.
They accept the emailed invitation.

✅ **Checkpoint:** every team member can see the repository and `git clone` it.

---

## Part 2 — Enforce the branching strategy (5 min)

A branching strategy that is not enforced by the server is a suggestion. This is where you
turn convention into a control.

### Step 2.1 — Protect `main`

On GitHub: **Settings → Branches → Add branch protection rule** (or *Add classic branch protection
rule*), branch name pattern `main`:

| Setting | Value | What it prevents |
|---|---|---|
| ☑ Require a pull request before merging | on | Direct pushes to `main`, including yours |
| ☑ Require approvals | **1** | Unreviewed code reaching the mainline |
| ☑ Dismiss stale approvals when new commits are pushed | on | Approving v1 and silently merging v3 |
| ☑ Require conversation resolution before merging | on | Merging with open review comments |
| ☑ Require status checks to pass | on *(add `CI passed` after Lab 04)* | Merging a red build |
| ☑ Require branches to be up to date before merging | on | "It passed on my branch" against a stale base |
| ☐ Allow force pushes | **off** | History rewrites on a shared branch |
| ☐ Allow deletions | **off** | Deleting `main` |

**Settings → General → Pull Requests:** tick **Allow squash merging**, untick *Allow merge
commits* and *Allow rebase merging*, and tick **Automatically delete head branches**.

**Why squash-only:** you are using GitHub Flow (Module 2 §2.3). Each PR becomes one tidy,
individually revertable commit on `main`, and the branch's "fix typo / actually fix typo"
noise stays out of the mainline. Auto-deleting merged branches keeps the branch list
meaningful.

### Step 2.2 — Prove the protection works

**1. Make a change on `main`.**

```bash
echo "# should not be allowed" >> README.md
```
**What this does:** `echo` prints a line and `>>` adds it to the end of `README.md`, creating the
file if it does not exist.

**2. Stage it.**

```bash
git add README.md
```
**What this does:** marks the file for the next commit.

**3. Commit it.**

```bash
git commit -m "test: attempt a direct push to main"
```
**What this does:** records it locally. Nothing has reached GitHub yet — your rules live there.

**4. Try to push it. This is rejected on purpose.**

```bash
git push origin main
```
**What this does:** GitHub refuses with `GH006: Protected branch update failed` and
`Changes must be made through a pull request`. **This is the point of the exercise** — see the
control fire before you rely on it.

**5. Undo the local commit.**

```bash
git reset --hard origin/main
```
**What this does:** moves your branch back to match GitHub's copy and resets your files to match
(`--hard`). Safe here because the commit was never shared — exactly the case where `reset` is the
right tool (Lab 02 Step 8).

---

## Part 3 — Contributors branch and open PRs (15 min)

### Step 3.1 — Both contributors clone and branch

**1. Go to the course folder.**

```bash
cd ~/devops-course
```
**What this does:** the folder that holds all your work.

**2. Clone the team repository.**

```bash
git clone https://github.com/<maintainer>/paytrack-api.git paytrack-api-team
```
**What this does:** creates the folder `paytrack-api-team`, downloads all the history, checks out
`main`, and saves the address as `origin` — all in one step. Replace `<maintainer>` with the
username of whoever owns the repository (your own, if you are working alone).

**3. Move into it.**

```bash
cd paytrack-api-team
```
**What this does:** every command in Parts 3 to 6 runs from here.

**Contributor A — 4. Create your branch.**

```bash
git switch -c feature/PAY-101-add-uptime-field
```
**What this does:** `-c` **c**reates a branch at the current commit and moves you onto it. The
name encodes the **type**, the **ticket** and a short description — the convention from Module 2
§2.4. (`git checkout -b` is the older spelling of the same thing.)

**Contributor B — do not create your branch yet.** You create it in Step 3.2, straight after
pulling the latest `main`. (Creating it here as well makes Step 3.2's `git switch -c` fail with
*a branch named … already exists*, and your commit then lands on `main` instead of your branch.)

**5. Look at your branches.**

```bash
git branch -vv
```
**What this does:** lists local branches with the server branch each one follows and its newest
commit. Contributor A sees the new branch with **no** upstream — it exists only on their machine.
Contributor B sees only `main`, following `origin/main`.

### Step 3.2 — Both make a change to the *same lines*

This collision is deliberate. It is how you get a conflict to resolve.

#### Contributor A — add an uptime field to the info endpoint

**1. Make sure you are in the clone.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the paths in the next command are relative to this folder.

**2. Edit the application.** One command — copy the whole box, including the final `PY`:

```bash
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace(
    '            host=os.getenv("HOSTNAME", "localhost"),\n        )',
    '            host=os.getenv("HOSTNAME", "localhost"),\n'
    '            uptime_seconds=round(time.perf_counter() - _STARTED, 1),\n        )'
)
s = s.replace(
    'BANNER = """<!doctype html>',
    '_STARTED = time.perf_counter()\n\nBANNER = """<!doctype html>'
)
assert "uptime_seconds" in s, "patch did not apply - is app/src/app.py unmodified?"
p.write_text(s)
print("patched app.py for PAY-101")
PY
```
**What this does:** `python3 - <<'PY'` runs the Python program that follows, up to the line `PY`.
It edits `app.py` so that everyone in the room produces an identical change — far more reliable in
a classroom than "open the file and add a line". The change records when the process started and
returns uptime from `/api/v1/info`. It prints `patched app.py for PAY-101`.

**3. Read your change before staging it.**

```bash
git diff
```
**What this does:** shows the added lines, marked `+`. Press `q` to leave the view.

**4. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api-team/app
```
**What this does:** the Python project lives here. This is a **fresh clone**, so it has no virtual
environment yet — `.venv/` is in `.gitignore` and is never pushed or cloned.

**5. Create the virtual environment if it is missing.**

```bash
[ -d .venv ] || python3 -m venv .venv
```
**What this does:** `[ -d .venv ]` asks "does that folder exist?"; `||` means "if not, do the next
thing". So it creates the private Python environment only when needed.

**6. Switch your terminal into it.**

```bash
source .venv/bin/activate
```
**What this does:** `source` runs the file **in your current shell**, which is what lets it change
your `PATH`. Your prompt gains `(.venv)`. It must be its own command: inside brackets it would
happen in a throw-away shell and `pytest` would then be *command not found*.

**7. Install the packages.**

```bash
pip install -q -r requirements-dev.txt
```
**What this does:** installs the pinned tools; `-q` keeps it quiet. On later runs it only checks,
so it is quick.

**8. Run the tests.**

```bash
pytest
```
**What this does:** runs the suite. Expect `19 passed`. **Never push a red branch** — you are
about to ask a colleague for their time.

**9. Return to the repository root.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** go back **even if the tests failed**, because the commands below use paths
like `app/src/app.py` that only work from here.

**10. Stage your change.**

```bash
git add app/src/app.py
```
**What this does:** stages that one file by name, so nothing else can slip into the commit.

**11. Commit it.**

```bash
git commit -m "feat(api): expose process uptime in /api/v1/info

PAY-101. Lets operators distinguish a pod that has just restarted from
one that has been serving for hours - the first question during an incident."
```
**What this does:** one command over several lines — copy all of it, both quote marks included.
The first line says what; the paragraph says **why**, which the diff cannot.

**12. Publish the branch.**

```bash
git push -u origin feature/PAY-101-add-uptime-field
```
**What this does:** uploads the branch and links it to GitHub's copy (`-u`), so later pushes are
just `git push`. GitHub prints a URL for opening the pull request.

#### Contributor B — add a region field, touching the same block

**1. Go to the clone.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the same folder (or your own clone, if you are a separate person).

**2. Go to the main branch.**

```bash
git switch main
```
**What this does:** B branches from `main`, not from A's work.

**3. Get the latest `main`.**

```bash
git pull
```
**What this does:** downloads and applies anything new on GitHub's `main`.

**4. Create B's branch.**

```bash
git switch -c feature/PAY-102-add-region-field
```
**What this does:** creates it and moves you onto it. **This is the only place B creates a
branch.**

**5. Edit the same part of the application.** One command, ending at `PY`:

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace(
    '            host=os.getenv("HOSTNAME", "localhost"),\n        )',
    '            host=os.getenv("HOSTNAME", "localhost"),\n'
    '            region=config.REGION,\n        )'
)
# The HTML banner already passes region=config.REGION, so after the patch there must be TWO.
assert s.count("region=config.REGION") == 2, "patch did not apply - is app/src/app.py unmodified?"
p.write_text(s)
print("patched app.py for PAY-102")
PY
```
**What this does:** adds `region` to the JSON returned by `/api/v1/info` — **the same lines A
changed**, which is the classic conflict. The `assert` counts occurrences rather than asking "is
it in the file?", because the HTML banner already contains that text and the simpler check would
pass even if the edit had failed.

**6. Check the size of the change.**

```bash
git diff --stat
```
**What this does:** one summary line: the file, and how many lines changed.

**7. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api-team/app
```
**What this does:** as for A — and in B's own clone the virtual environment does not exist yet.

**8. Create the virtual environment if it is missing.**

```bash
[ -d .venv ] || python3 -m venv .venv
```
**What this does:** creates it only when it is absent.

**9. Activate it.**

```bash
source .venv/bin/activate
```
**What this does:** puts `python` and `pytest` from `.venv` on your `PATH`; the prompt shows
`(.venv)`.

**10. Install the packages.**

```bash
pip install -q -r requirements-dev.txt
```
**What this does:** installs the pinned tools quietly.

**11. Run the tests.**

```bash
pytest
```
**What this does:** expect `19 passed`.

**12. Return to the repository root.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** whatever the test result, the next commands need this folder.

**13. Stage the file.**

```bash
git add app/src/app.py
```
**What this does:** stages only the file B changed.

**14. Commit it.**

```bash
git commit -m "feat(api): expose deployment region in /api/v1/info

PAY-102. Data residency: with entities in more than one jurisdiction we need to
identify which region answered a request, for both incident triage and the
residency evidence Compliance asks for."
```
**What this does:** one command over several lines. The body records **why** — data residency.

**15. Publish the branch.**

```bash
git push -u origin feature/PAY-102-add-region-field
```
**What this does:** uploads B's branch and links it to GitHub's copy.

### Step 3.3 — Open the pull requests

On GitHub, **Pull requests → New pull request** for each branch, base `main`.

Write a real description. Use these headings — in Part 5 you commit them as a **pull request
template**, so GitHub pre-fills every later PR with them:

```markdown
## What
<One paragraph: what changes, in plain language.>

## Why
<The problem this solves. Link the ticket.>

## How to verify
<Paste the exact commands a reviewer can run to see this working.>

## Risk & rollback
- Risk level: low / medium / high
- Rollback: <how to undo this if it misbehaves in production>

## Checklist
- [ ] Tests added or updated
- [ ] `pytest` passes locally
- [ ] No secrets, keys or credentials in the diff
- [ ] Documentation updated if behaviour changed
```

> Why not create the template file now? You are on your feature branch. A file created here but
> never committed stays behind as an untracked file, follows you from branch to branch, and gets
> swept into the next `git add -A` — Lab 04 would commit it into a branch that is then deleted.

### Step 3.4 — The Maintainer reviews and merges PR #1

Open PR #1 → **Files changed** → add at least one comment (a genuine question is better than
"LGTM") → **Review changes → Approve** → **Squash and merge**.

✅ **Checkpoint:** `main` now contains A's change as **one** commit, and the branch was
deleted automatically.

---

## Part 4 — Resolve the merge conflict (10 min)

PR #2 now reports **"This branch has conflicts that must be resolved."** Good.

### Step 4.1 — Reproduce it locally

**1. Go to the clone.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** all four commands in this step run here.

**2. Switch to B's branch.**

```bash
git switch feature/PAY-102-add-region-field
```
**What this does:** the branch with the conflict.

**3. Download what changed on GitHub.**

```bash
git fetch origin
```
**What this does:** downloads new commits into your copy of `origin/main` **without touching your
files**. Fetching is always safe.

**4. Bring `main` into your branch. This stops with a conflict, on purpose.**

```bash
git merge origin/main
```
**What this does:** tries to combine the two lines of work. Both changed the same place, so git
stops and asks you to decide:

```
Auto-merging app/src/app.py
CONFLICT (content): Merge conflict in app/src/app.py
Automatic merge failed; fix conflicts and then commit the result.
```

> **Git is not broken. It is asking a question it cannot answer.**

**5. Ask git where you stand.**

```bash
git status
```
**What this does:** lists the file under "Unmerged paths" — and prints exactly which commands to
run next. Read it rather than guessing.

### Step 4.2 — Read the markers

**1. Find the conflict in the file.**

```bash
grep -n -A 12 '<<<<<<<' app/src/app.py
```
**What this does:** `grep` searches for text; `-n` adds line numbers and `-A 12` also prints the
12 lines **a**fter each match. You see:

```python
<<<<<<< HEAD                                   ← YOUR branch (PAY-102)
            region=config.REGION,
=======                                        ← divider
            uptime_seconds=round(time.perf_counter() - _STARTED, 1),
>>>>>>> origin/main                            ← THEIR change, already on main
```

### Step 4.3 — Resolve it correctly

The right answer here is **both**, not one — which is why a human is required.

**1. Replace the conflicted block with both lines.** One command, ending at `PY`:

```bash
python3 - <<'PY'
import pathlib, re
p = pathlib.Path("app/src/app.py")
s = p.read_text()
resolved = (
    '            region=config.REGION,\n'
    '            uptime_seconds=round(time.perf_counter() - _STARTED, 1),\n'
)
s = re.sub(r'<<<<<<< HEAD\n.*?=======\n.*?>>>>>>> [^\n]*\n', resolved, s, flags=re.S)
p.write_text(s)
print("conflict resolved: kept BOTH fields")
PY
```
**What this does:** rewrites the whole conflicted region — the three marker lines included — as
the two fields together. (By hand you would open `nano app/src/app.py`, delete the marker lines
and keep both entries.)

**2. Prove no markers are left.**

```bash
grep -c '<<<<<<<' app/src/app.py
```
**What this does:** `-c` **c**ounts matching lines. It must print **0**. Any marker left behind is
a syntax error that will ship.

**3. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api-team/app
```
**What this does:** **always run the tests after resolving a conflict.** A resolution that merges
cleanly can still be wrong; the tests are what catch it.

**4. Create the virtual environment if this clone has none.**

```bash
[ -d .venv ] || python3 -m venv .venv
```
**What this does:** creates it only if it is missing.

**5. Activate it.**

```bash
source .venv/bin/activate
```
**What this does:** the prompt shows `(.venv)`.

**6. Install the packages.**

```bash
pip install -q -r requirements-dev.txt
```
**What this does:** quietly installs or checks the pinned tools.

**7. Run the tests.**

```bash
pytest
```
**What this does:** expect `19 passed` — the merged code still works.

**8. Return to the repository root.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the next command needs this folder.

**9. Mark the conflict resolved.**

```bash
git add app/src/app.py
```
**What this does:** staging a conflicted file is how you tell git "I have dealt with this one".

**10. Complete the merge.**

```bash
git commit --no-edit
```
**What this does:** `--no-edit` accepts git's prepared merge message instead of opening an editor.

**11. Update the pull request.**

```bash
git push
```
**What this does:** sends the merge to GitHub, which re-checks whether the PR can now be merged.

### Step 4.4 — Merge PR #2

Approve and **Squash and merge** on GitHub.

✅ **Checkpoint** — four commands.

```bash
git switch main
```
**What this does:** back to the main branch.

```bash
git pull
```
**What this does:** downloads the merged result.

```bash
grep -n 'region=\|uptime_seconds=' app/src/app.py
```
**What this does:** prints every line that sets `region` or `uptime_seconds`, with line numbers
(`\|` means "or"). Expect:

```
160:            region=config.REGION,
185:            region=config.REGION,
186:            uptime_seconds=round(time.perf_counter() - _STARTED, 1),
```

The first `region` line is the HTML banner, which always had it. The last two are your resolution
inside `/api/v1/info`: **both** fields, side by side.

```bash
git log --oneline --graph -6
```
**What this does:** draws the recent history: the two squashed pull-request commits, `(#1)` and
`(#2)`, on top of Lab 02's work.

---

## Part 5 — Pull request template and CODEOWNERS (5 min)

**1. Go to the clone.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** where the work happens.

**2. Go to `main`.**

```bash
git switch main
```
**What this does:** start this change from the mainline, not from a feature branch.

**3. Make sure it is current.**

```bash
git pull
```
**What this does:** brings in both merged pull requests.

**4. Create a branch for this change.**

```bash
git switch -c chore/add-pr-template-and-codeowners
```
**What this does:** even a configuration change goes through a pull request — that is what the
rules in Part 2 mean.

**5. Create the `.github` folder.**

```bash
mkdir -p .github
```
**What this does:** this is the folder GitHub reads repository configuration from. `-p` means "do
nothing if it already exists".

**6. Write the pull request template.** One command, ending at `EOF`:

```bash
cat > .github/pull_request_template.md <<'EOF'
## What
<One paragraph: what changes, in plain language.>

## Why
<The problem this solves. Link the ticket.>

## How to verify
<Paste the exact commands a reviewer can run to see this working.>

## Risk & rollback
- Risk level: low / medium / high
- Rollback: <how to undo this if it misbehaves in production>

## Checklist
- [ ] Tests added or updated
- [ ] `pytest` passes locally
- [ ] No secrets, keys or credentials in the diff
- [ ] Documentation updated if behaviour changed
EOF
```
**What this does:** writes the headings from Step 3.3 into the file GitHub uses to pre-fill the
body of **every new pull request**. A template raises the floor on description quality without
anyone having to nag — the cheapest process improvement available to a team.

**7. Write the code-owners file.** One command, ending at `EOF`. **Replace
`@<maintainer-username>` with the real GitHub username**, `@` included:

```bash
cat > .github/CODEOWNERS <<'EOF'
# The LAST matching rule wins, so put the broad default first and specific paths after it.

# Default owner for everything
*                       @<maintainer-username>

# The application
/app/                   @<maintainer-username>

# Anything that changes how code reaches production must be reviewed with extra care
/.github/workflows/     @<maintainer-username>
/k8s/                   @<maintainer-username>
/terraform/             @<maintainer-username>
EOF
```
**What this does:** GitHub reads `CODEOWNERS` and automatically requests review from the matching
owners on every pull request. **The pipeline and deployment paths are the important entries:** a
change to `.github/workflows/` can expose every secret in the repository, so it deserves stricter
review than a change to a stylesheet. Turn on *Require review from Code Owners* in the branch
protection rule to enforce it.

**8. Stage both files by name.**

```bash
git add .github/pull_request_template.md .github/CODEOWNERS
```
**What this does:** naming them means nothing else in the folder can slip into the commit.

**9. Commit them.**

```bash
git commit -m "chore: add a pull request template and CODEOWNERS"
```
**What this does:** one commit, one purpose.

**10. Publish the branch.**

```bash
git push -u origin chore/add-pr-template-and-codeowners
```
**What this does:** uploads it and prints the URL for the pull request.

Open the PR — notice the reviewer is requested automatically — then merge it.

---

## Part 6 — See the whole team's work in one picture (5 min)

This is the part delegates remember. Everyone has been working on their own branch, in their
own terminal, seeing only their own commits. **One page turns that into a single shared
picture.**

### Step 6.1 — Everyone pushes a branch first

Each team member, in their own clone — nine commands.

**1. Go to your clone.**

```bash
cd ~/devops-course/paytrack-api-team 2>/dev/null || cd ~/devops-course/paytrack-api
```
**What this does:** contributors cloned `paytrack-api-team` in Step 3.1, while the Maintainer's
clone is the original `paytrack-api` from Lab 02. `||` means "if that folder does not exist, use
this one instead", and `2>/dev/null` hides the error message from the first attempt.

**2. Go to `main`.**

```bash
git switch main
```
**What this does:** start from the mainline.

**3. Update it.**

```bash
git pull
```
**What this does:** brings in everything merged so far.

**4. Make sure the docs folder exists.**

```bash
mkdir -p docs
```
**What this does:** a no-op if it is already there.

**5. Build a safe branch name from your git name.**

```bash
SLUG=$(git config user.name | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')
```
**What this does:** takes your configured name, makes it lower-case (`tr '[:upper:]' '[:lower:]'`),
turns every run of other characters into a single hyphen (`tr -cs 'a-z0-9' '-'`, so spaces,
apostrophes and accents cannot produce an awkward branch name), trims stray hyphens from the ends
(`sed`), and stores the result under the name `SLUG`. Nothing is printed.

**6. Create your demo branch.**

```bash
git switch -c "demo/${SLUG:-delegate}-graph"
```
**What this does:** `${SLUG:-delegate}` means "use SLUG, or the word `delegate` if it is empty".
So you get a branch such as `demo/ana-silva-graph`.

**7. Add your line to the shared file.**

```bash
echo "- $(git config user.name) was here at $(date +%H:%M)" >> docs/team-log.md
```
**What this does:** `$(…)` runs a command and drops its answer into the text, so the line carries
your name and the time. `>>` adds it to the end of the file.

**8. Stage and commit it.**

```bash
git add docs/team-log.md
```
**What this does:** stages the file.

```bash
git commit -m "docs: add my line to the team log"
```
**What this does:** records it.

**9. Push your branch.**

```bash
git push -u origin HEAD
```
**What this does:** `HEAD` means "the branch I am on", so you never retype the name. `-u` links it
to GitHub's copy.

**Everyone has now touched the same file on a different branch**, which is exactly the shape
that makes the graph interesting.

### Step 6.2 — 🎯 The one thing: the GitHub Network graph

**Go to:** `https://github.com/<maintainer>/paytrack-api/network`

*(Or in the repository: **Insights → Network**.)*

**Put it on the projector.** Every delegate sees:

```
        ┌─ alice/demo-graph ──●
        │
 main ──●──●──●──●──────────────────────────────●  ← the squashed merges from Part 3
        │           │
        │           └─ bob/demo-graph ──●
        │
        └─ carol/demo-graph ──●──●
```

- **One coloured line per contributor**, labelled with their avatar and branch name
- Where each branch **left** `main`, and whether it has come back
- Hovering any dot shows the commit, the author and the message
- It **updates on refresh** — push a commit and watch your line grow

> 🔑 **Why this is the right tool for this moment.** Delegates have just learned that a branch
> is "a movable pointer to a commit" and that history is a DAG. That is abstract. The Network
> graph is the *same DAG*, drawn, with their own name on it. It converts a definition into a
> picture of the team's actual week.

**Ask the room, looking at the graph:**
1. **Whose branch is furthest from `main`?** That is the person who will have the worst merge
   conflict — this is what "long-lived branches" costs, made visible.
2. **How many branches are unmerged right now?** That is your work in progress.
3. **Which commits on `main` are squashed PRs?** Notice how clean the mainline is compared
   with the branch lines. That is the squash-merge policy from Part 2 paying off.
4. **If everyone had committed straight to `main` instead** — what would this picture look
   like? (One line. No visible parallel work. No review point.)

### Step 6.3 — The same thing in the terminal

**1. Download every branch.**

```bash
git fetch --all --prune
```
**What this does:** `--all` fetches from every remote; `--prune` deletes your copies of branches
that no longer exist on the server, so the picture is honest.

**2. Draw the graph.**

```bash
git log --oneline --graph --decorate --all
```
**What this does:** renders the same shape as GitHub's Network page, in text. **This works
offline, in any repository, with no GitHub** — which is why Lab 02 made it the `git lg` alias.

**A live version, for a second monitor:**

```bash
watch -n 5 'git fetch --all --prune -q; git log --oneline --graph --decorate --all -25'
```
**What this does:** `watch -n 5` re-runs something every 5 seconds and redraws the screen. Leave
it running while the team works and you can watch branches appear, advance and merge. Press
`Ctrl` + `C` to stop.

### Step 6.4 — Two more team-visibility views, in order of usefulness

| Where | Shows | Use it for |
|---|---|---|
| **Insights → Network** | The branch DAG, per person | **Understanding branching.** The one above |
| **Pull requests** tab | Open work, who is waiting on review | **The daily standup.** Sort by "Oldest" to expose review latency |
| **Insights → Contributors** | Commits per person over time | Trends only — **never** for performance management |

> ⚠️ **Say this out loud when you show Contributors:** commit counts are a *vanity metric*
> (Module 9 §9.2). One person refactoring safely may commit less than someone churning. Using
> this graph to compare people destroys exactly the collaboration the rest of the week is
> trying to build.

### Step 6.5 — Clean up the demo branches

**1. Remember which branch you are on.**

```bash
BRANCH=$(git branch --show-current)
```
**What this does:** stores the current branch name under the name `BRANCH` — **before** you switch
away, because afterwards the answer would be `main` and you would delete the wrong thing. Nothing
is printed.

**2. Go to `main`.**

```bash
git switch main
```
**What this does:** you cannot delete the branch you are standing on.

**3. Delete it on GitHub.**

```bash
git push origin --delete "$BRANCH"
```
**What this does:** removes the branch from the server. The quotes keep the name in one piece even
if it contains something odd.

**4. Delete your local copy.**

```bash
git branch -D "$BRANCH"
```
**What this does:** `-D` deletes the label even though it was never merged into `main`.

**5. Tidy the stale references.**

```bash
git fetch --prune
```
**What this does:** drops your copies of branches that no longer exist on the server. Refresh the
Network graph — the lines are gone.

> ⚠️ **The Network graph requires a public repository** on GitHub Free. Yours is public (Part
> 1), so it works. On a private repo you would need GitHub Team or Enterprise — in that case
> use the `git log --graph --all` version in 6.3, or **GitKraken** / **Sourcetree** (free
> desktop clients that draw the same graph locally). The picture matters more than the tool.

---

## ⭐ Advanced — optional, in this folder

This lab is finished. If you want to go further with Git, everything you need is **beside this
page in the same folder** — nothing on Day 3 onwards depends on any of it.

| In this folder | What it is | Time | Needs |
|---|---|---|---|
| **[README-03A — Git, Going Further](README-03A-git-going-further.md)** | A hands-on lab on a practice repository built to be broken: stash, `add -p`, amend, the three resets, reflog rescue, bisect, revert, clean, tags, cherry-pick, merge vs rebase, interactive rebase, and force-pushing against a "colleague" | 80 min, in eight parts you can do separately | Nothing — no GitHub, no Docker, no network |
| **`Lab03A_Advanced_Git.pptx`** | The 32 advanced slides behind that lab: sections A, B and C of the Day 2 *Going Further* material | Read it first, or use it to teach the material | PowerPoint |
| **`setup-gym.sh`** | Builds (and rebuilds) the practice repository the lab uses | 2 seconds | Run by the lab |

**Do them in that order:** read the deck, then work through the page. Every command in the deck
is run for real in the lab, including the ones that destroy work — which is the point of doing
it on a practice repository rather than on `paytrack-api`.

---

## 🧩 Stretch (homework)

1. **Rebase instead of merge.** On a new branch, `git fetch && git rebase origin/main`.
   Compare the resulting history with the merge you did in Part 4. Then read Module 2 §2.5
   and explain why you would never do this to a branch a colleague has pulled.
   **[Lab 03A](README-03A-git-going-further.md) Part 7** walks through merge versus rebase,
   a rebase conflict and interactive rebase step by step, and Part 8 shows what force-pushing does to
   a colleague.
2. **`git bisect`.** [Lab 03A](README-03A-git-going-further.md) Part 5 gives you a practice
   repository with a hidden bug, and finds it with `git bisect run` in three steps.
3. **Signed commits.** `git config --global commit.gpgsign true` with an SSH signing key, and
   turn on *Require signed commits* in branch protection.

---

## 🎯 Outcome

A GitHub repository with enforced branch protection, squash-only merges, a PR template,
CODEOWNERS, two merged pull requests and one professionally resolved merge conflict — plus a
shared **Network graph** in which every delegate can see their own branch alongside everyone
else's. This is the repository every remaining lab pushes to.

**Next:** [Lab 04 — GitHub Actions CI](../lab-04-github-actions-ci/README.md) ·
*Optional:* [Lab 03A — Git, Going Further](README-03A-git-going-further.md) (reset, reflog,
bisect, cherry-pick, interactive rebase, force-push — on a practice repository)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Timing:** Part 1–2 in 10 min, Part 3 in 15, Part 4 in 10, Part 5 in 5, Part 6 in 5.
  Parts 4 and 6 are the point of the lab — protect their time by driving Parts 1–2 from the
  front.
- **Part 6 needs the projector.** Have `https://github.com/<maintainer>/paytrack-api/network` open and
  refresh it as delegates push. The moment the room sees their own branch on a shared picture
  is the moment branching stops being abstract — it is the highest-value five minutes of
  day 2.
- **Set up a shared GitHub organisation before the course** and invite delegates. It removes
  five minutes of per-team collaborator faff.
- **The three things that go wrong:**
  1. Authentication. Half the room will try their password. Have the PAT instructions on a
     slide, ready.
  2. Someone ticks *Initialize with README* and gets
     `refusing to merge unrelated histories`. Fix: delete the repo and start again — quicker
     than explaining `--allow-unrelated-histories`.
  3. The conflict does not appear because B branched *after* A's merge. Insist that both
     contributors branch from the same `main` before either PR is merged.
- **Teaching moment:** when the direct push to `main` is rejected in Step 2.2, ask the room
  how many of their repositories would have accepted it.
- **Debrief question:** "Your CI config lives in the same repo as your code. Who in your
  organisation can currently change it, and what could they do with that access?"
</details>
