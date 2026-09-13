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

🔁 **RECOVER — if Lab 02 is incomplete**
```bash
cd ~/devops-course && rm -rf paytrack-api
git clone https://github.com/kumbulanit/devops_professional.git course-material 2>/dev/null || true
mkdir -p paytrack-api && cp -r course-material/app paytrack-api/app && cd paytrack-api
git init && git add . && git commit -m "feat: add PayTrack API service"
```

---

## Roles

Decide now, and write it down:

| Role | Who | Does |
|---|---|---|
| **Maintainer** | one person | Owns the repository, configures protection, reviews and merges |
| **Contributor A** | | Adds a feature on a branch |
| **Contributor B** | | Adds a *different* feature that touches the **same lines** — creating the conflict |

Working alone? Do all three roles yourself, using a second clone in
`~/devops-course/paytrack-api-b` to play Contributor B. You lose the review conversation but
keep every mechanic.

---

## Part 1 — The Maintainer creates the remote (5 min)

> ⚠️ **This is YOUR repository, not the course one.** Everywhere below that says
> `<your-username>` or `<maintainer>`, substitute the relevant GitHub account —
> the maintainer's account for the shared team repo, yours for your own clones.
> `kumbulanit/devops_professional` is the *course material* and is read-only to you.

### Step 1.1 — Create an empty repository on GitHub

Go to **https://github.com/new** and set:

| Field | Value | Why |
|---|---|---|
| Repository name | `paytrack-api` | |
| Visibility | **Public** | Free unlimited Actions minutes and free GHCR packages — you need both this week |
| Initialize with README | **☐ unticked** | You already have commits; an initialised remote creates unrelated history and a painful first push |
| .gitignore / licence | **none** | Same reason |

### Step 1.2 — Connect and push

```bash
cd ~/devops-course/paytrack-api
git remote add origin https://github.com/<your-username>/paytrack-api.git
git remote -v
```
**What this does:** `git remote add` registers a named URL. `origin` is only a convention —
it is the default name for "the place I cloned from / push to". `-v` lists remotes with
their fetch and push URLs so you can confirm the spelling.

```bash
git push -u origin main
git push origin v1.0.0
```
**What this does:** uploads your commits and sets `origin/main` as the **upstream** for your
local `main` (`-u`). From now on bare `git push` and `git pull` know where to go, and
`git status` can tell you "ahead by 2 commits". **Tags are not pushed automatically** — the
second command pushes `v1.0.0` explicitly.

> ⚠️ **Authentication.** GitHub does not accept account passwords over HTTPS. When prompted,
> use a **Personal Access Token** (Settings → Developer settings → Personal access tokens →
> Fine-grained → repo access, `Contents: read & write`). Cache it so you type it once:
> ```bash
> git config --global credential.helper "cache --timeout=28800"
> ```
> **What this does:** keeps the token in memory for 8 hours. SSH keys are the better
> long-term answer (`ssh-keygen -t ed25519 -C "you@example.com"`, then add the public key to
> GitHub and use the `git@github.com:` URL).

### Step 1.3 — Add your teammates

**Settings → Collaborators → Add people** → their GitHub usernames → **Write** access.
They accept the emailed invitation.

✅ **Checkpoint:** every team member can see the repository and `git clone` it.

---

## Part 2 — Enforce the branching strategy (5 min)

A branching strategy that is not enforced by the server is a suggestion. This is where you
turn convention into a control.

### Step 2.1 — Protect `main`

**Settings → Branches → Add branch protection rule** (or *Add classic branch protection
rule*), branch name pattern `main`:

| Setting | Value | What it prevents |
|---|---|---|
| ☑ Require a pull request before merging | on | Direct pushes to `main`, including yours |
| ☑ Require approvals | **1** | Unreviewed code reaching the mainline |
| ☑ Dismiss stale approvals when new commits are pushed | on | Approving v1 and silently merging v3 |
| ☑ Require conversation resolution before merging | on | Merging with open review comments |
| ☑ Require status checks to pass | on *(add `ci / test` after Lab 04)* | Merging a red build |
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

```bash
echo "# should not be allowed" >> README.md
git add README.md && git commit -m "test: attempt a direct push to main"
git push origin main
```
**What this does:** deliberately attempts a direct push. **It must be rejected** with
`GH006: Protected branch update failed`. This is the point of the exercise — see the control
fire before you rely on it.

```bash
git reset --hard origin/main
```
**What this does:** discards that local commit and resets your branch to match the remote.
`--hard` also resets the working tree. Safe here because the commit was never shared —
exactly the case where `reset` is the right tool (Lab 02 §8).

---

## Part 3 — Contributors branch and open PRs (15 min)

### Step 3.1 — Both contributors clone and branch

```bash
cd ~/devops-course
git clone https://github.com/<maintainer>/paytrack-api.git paytrack-api-team
cd paytrack-api-team
```
**What this does:** `clone` creates the directory, fetches all history, checks out `main` and
configures `origin` in one step.

**Contributor A:**
```bash
git switch -c feature/PAY-101-add-uptime-field
```
**Contributor B:**
```bash
git switch -c feature/PAY-102-add-region-field
```
**What this does:** `git switch -c` creates a branch at the current commit and checks it out.
(`git checkout -b` is the older equivalent; `switch` and `restore` were introduced to split
checkout's overloaded jobs into two clear commands.) The name encodes the **type**, the
**ticket** and a short description — the convention from Module 2 §2.3.

```bash
git branch -vv
```
**What this does:** lists local branches with their upstream and the last commit. Your new
branch has no upstream yet — it exists only on your machine.

### Step 3.2 — Both make a change to the *same lines*

This collision is deliberate. It is how you get a conflict to resolve.

**Contributor A** — add an uptime field to the info endpoint:
```bash
cd ~/devops-course/paytrack-api-team
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
git diff
```
**What this does:** a small Python script edits `app.py` deterministically so everyone in the
room produces the identical change (far more reliable in a classroom than "open the file and
add a line"). It records process start time and returns uptime from `/api/v1/info`.
`git diff` shows the result before you stage it.

```bash
cd app && source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements-dev.txt)
pytest -q && cd ..
```
**What this does:** activates the venv (creating it if this is a fresh clone) and runs the
tests. **Never push a red branch** — you are about to ask a colleague for their time.

```bash
git add app/src/app.py
git commit -m "feat(api): expose process uptime in /api/v1/info

PAY-101. Lets operators distinguish a pod that has just restarted from
one that has been serving for hours - the first question during an incident."
git push -u origin feature/PAY-101-add-uptime-field
```
**What this does:** commits and pushes, setting the upstream so subsequent pushes are bare
`git push`. GitHub prints a URL to open the pull request.

**Contributor B** — add a region field, touching the **same block**:
```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull      # start from the latest main
git switch -c feature/PAY-102-add-region-field
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace(
    '            host=os.getenv("HOSTNAME", "localhost"),\n        )',
    '            host=os.getenv("HOSTNAME", "localhost"),\n'
    '            region=config.REGION,\n        )'
)
assert "region=config.REGION" in s, "patch did not apply - is app/src/app.py unmodified?"
p.write_text(s)
print("patched app.py for PAY-102")
PY
git add app/src/app.py
git commit -m "feat(api): expose deployment region in /api/v1/info

PAY-102. Data residency: with entities in more than one jurisdiction we need to
identify which region answered a request, for both incident triage and the
residency evidence Compliance asks for."
git push -u origin feature/PAY-102-add-region-field
```
**What this does:** `git pull` first, so B branches from the current `main`. Both contributors
have now modified **the same two lines** of `app.py` — the classic conflict.

### Step 3.3 — Open the pull requests

On GitHub, **Pull requests → New pull request** for each branch, base `main`.

Write a real description. Add this template to the repository so it appears automatically
next time:

```bash
mkdir -p .github
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
**What this does:** GitHub pre-fills every new PR body from this file. A template raises the
floor on description quality without anyone having to nag — the cheapest process improvement
available to a team.

### Step 3.4 — The Maintainer reviews and merges PR #1

Open PR #1 → **Files changed** → add at least one comment (a genuine question is better than
"LGTM") → **Review changes → Approve** → **Squash and merge**.

✅ **Checkpoint:** `main` now contains A's change as **one** commit, and the branch was
deleted automatically.

---

## Part 4 — Resolve the merge conflict (10 min)

PR #2 now reports **"This branch has conflicts that must be resolved."** Good.

### Step 4.1 — Reproduce it locally

```bash
cd ~/devops-course/paytrack-api-team
git switch feature/PAY-102-add-region-field
git fetch origin
git merge origin/main
```
**What this does:**
- `git fetch origin` downloads the new commits into `origin/main` **without touching your
  working tree**. Fetch is always safe.
- `git merge origin/main` attempts a three-way merge of `main` into your branch. Both sides
  changed the same region, so git stops and asks you to decide:

```
Auto-merging app/src/app.py
CONFLICT (content): Merge conflict in app/src/app.py
Automatic merge failed; fix conflicts and then commit the result.
```

> **Git is not broken. It is asking a question it cannot answer.**

```bash
git status
```
**What this does:** lists the file under "Unmerged paths". `git status` during a conflict also
prints exactly which commands to run next — read it rather than guessing.

### Step 4.2 — Read the markers

```bash
grep -n -A 12 '<<<<<<<' app/src/app.py
```
**What this does:** finds the conflict markers and prints 12 lines after each (`-A 12`), with
line numbers (`-n`).

```python
<<<<<<< HEAD                                   ← YOUR branch (PAY-102)
            region=os.getenv("APP_REGION", "local"),
=======                                        ← divider
            uptime_seconds=round(time.perf_counter() - _STARTED, 1),
>>>>>>> origin/main                            ← THEIR change, already on main
```

### Step 4.3 — Resolve it correctly

The right answer here is **both**, not one — which is why a human is required.

```bash
python3 - <<'PY'
import pathlib, re
p = pathlib.Path("app/src/app.py")
s = p.read_text()
resolved = (
    '            region=os.getenv("APP_REGION", "local"),\n'
    '            uptime_seconds=round(time.perf_counter() - _STARTED, 1),\n'
)
s = re.sub(r'<<<<<<< HEAD\n.*?=======\n.*?>>>>>>> [^\n]*\n', resolved, s, flags=re.S)
p.write_text(s)
print("conflict resolved: kept BOTH fields")
PY
grep -c '<<<<<<<' app/src/app.py
```
**What this does:** replaces the whole conflicted region — markers included — with both
lines. The `grep -c` must print **0**: any remaining marker is a syntax error that will ship.

```bash
cd app && source .venv/bin/activate && pytest -q && cd ..
```
**What this does:** **always run the tests after resolving a conflict.** A resolution that
merges cleanly can still be semantically wrong; the test suite is what catches it.

```bash
git add app/src/app.py
git commit --no-edit
git push
```
**What this does:** `git add` marks the conflict resolved. `git commit --no-edit` accepts
git's prepared merge-commit message. The push updates the PR, and GitHub re-checks
mergeability.

### Step 4.4 — Merge PR #2

Approve and **Squash and merge** on GitHub.

✅ **Checkpoint**
```bash
git switch main && git pull
curl -s -o /dev/null -w '' localhost:8080 2>/dev/null
grep -n 'region=\|uptime_seconds=' app/src/app.py
git log --oneline --graph -6
```
Both fields are present on `main`, and the history shows two clean squashed commits.

---

## Part 5 — CODEOWNERS (5 min)

```bash
git switch -c chore/add-codeowners
cat > .github/CODEOWNERS <<'EOF'
# Every path matches the LAST matching rule, so order matters (unlike .gitignore).

# Default owner for everything
*                       @<maintainer-username>

# The application
/app/                   @<maintainer-username>

# Anything that changes how code reaches production must be reviewed with extra care
/.github/workflows/     @<maintainer-username>
/k8s/                   @<maintainer-username>
/terraform/             @<maintainer-username>
EOF
git add .github/CODEOWNERS
git commit -m "chore: add CODEOWNERS for automatic review routing"
git push -u origin chore/add-codeowners
```
**What this does:** GitHub reads `CODEOWNERS` and automatically requests review from the
matching owners on every PR. **The pipeline and deployment paths are the important entries:**
a change to `.github/workflows/` can exfiltrate every secret in the repository, so it deserves
stricter review than a change to a stylesheet. Enable *Require review from Code Owners* in the
branch protection rule to enforce it.

Open the PR — notice the reviewer is requested automatically — then merge it.

---

## Part 6 — See the whole team's work in one picture (5 min)

This is the part delegates remember. Everyone has been working on their own branch, in their
own terminal, seeing only their own commits. **One page turns that into a single shared
picture.**

### Step 6.1 — Everyone pushes a branch first

Each team member, in their own clone:

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
SLUG=$(git config user.name | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')
git switch -c "demo/${SLUG:-delegate}-graph"
echo "- $(git config user.name) was here at $(date +%H:%M)" >> docs/team-log.md
git add docs/team-log.md
git commit -m "docs: add my line to the team log"
git push -u origin HEAD
```
**What this does:** builds a safe branch name from your git `user.name` — lowercased
(`tr '[:upper:]' '[:lower:]'`), with every run of non-alphanumeric characters collapsed to a
single hyphen (`tr -cs 'a-z0-9' '-'`, so spaces, apostrophes and accents cannot produce an
awkward branch name), and leading/trailing hyphens trimmed. `${SLUG:-delegate}` falls back to
`delegate` if the name produces nothing. Then it adds one line to a shared file and pushes. `HEAD` in
`git push -u origin HEAD` means "the branch I am currently on" — so you never have to retype
the branch name.

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

```bash
git fetch --all --prune
git log --oneline --graph --decorate --all
```
**What this does:** `fetch --all` downloads every branch from the remote (`--prune` drops
remote-tracking branches that have been deleted); the `log` renders the same DAG as ASCII.
**This works offline, in any repo, with no GitHub** — which is why Lab 02 made it the `git lg`
alias.

**A live version, for a second monitor:**
```bash
watch -n 5 'git fetch --all --prune -q; git log --oneline --graph --decorate --all -25'
```
**What this does:** re-fetches and redraws every 5 seconds. Leave it running while the team
works and you can literally watch branches appear, advance and merge.

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

```bash
BRANCH=$(git branch --show-current)      # capture it BEFORE switching away
git switch main
git push origin --delete "$BRANCH"
git branch -D "$BRANCH"
git fetch --prune
```
**What this does:** stores the branch name in a variable **first** (once you switch to `main`,
`git branch --show-current` would return `main` and you would be trying to delete the wrong
thing), then deletes it on the remote and locally, and prunes the stale remote-tracking
reference. Refresh the Network graph — the lines are gone.

> ⚠️ **The Network graph requires a public repository** on GitHub Free. Yours is public (Part
> 1), so it works. On a private repo you would need GitHub Team or Enterprise — in that case
> use the `git log --graph --all` version in 6.3, or **GitKraken** / **Sourcetree** (free
> desktop clients that draw the same graph locally). The picture matters more than the tool.

---

## 🧩 Stretch (homework)

1. **Rebase instead of merge.** On a new branch, `git fetch && git rebase origin/main`.
   Compare the resulting history with the merge you did in Part 4. Then read Module 2 §2.5
   and explain why you would never do this to a branch a colleague has pulled.
2. **`git bisect`.** Introduce a bug, commit ten times, then use
   `git bisect start / bad / good <sha>` to find the breaking commit in log₂(n) steps.
3. **Signed commits.** `git config --global commit.gpgsign true` with an SSH signing key, and
   turn on *Require signed commits* in branch protection.

---

## 🎯 Outcome

A GitHub repository with enforced branch protection, squash-only merges, a PR template,
CODEOWNERS, two merged pull requests and one professionally resolved merge conflict — plus a
shared **Network graph** in which every delegate can see their own branch alongside everyone
else's. This is the repository every remaining lab pushes to.

**Next:** [Lab 04 — GitHub Actions CI](../lab-04-github-actions-ci/README.md)

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
