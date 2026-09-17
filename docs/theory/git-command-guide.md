# Git Command Guide — what each command means, how to use it, and when (in plain English)

> **Day 2 · Module 2 companion · used in Labs 02–05 and every lab after**
>
> One section per command, always in the same order: **what it means · how · when to use it ·
> when not to · what to watch for**. Every terminal block is **real output** captured from a
> scripted PayTrack API repository. Only three things were edited: machine paths, the remote
> URL (shown as your GitHub URL), and Git's multi-line `hint:` text where it adds nothing.
>
> Merging and rebasing have their own, longer treatment in
> [Module 2 §2.5 — Rebase in practice](module-02-version-control-and-ci.md#rebase-in-practice--what-it-means-how-to-do-it-when-to-use-it).
>
> **Written for beginners.** Nothing is assumed beyond Day 1. Read *Words you need* first, then the
> everyday commands in order. Sections marked **Going further** are optional.
>
> **Want to try the Going further commands yourself?**
> [Lab 03A — Git, Going Further](../../labs/lab-03a-git-going-further/README.md) builds a practice
> repository where you run every one of them — reset, reflog, bisect, cherry-pick, interactive rebase
> and safe force-pushing — with nothing to lose.

---

## Words you need

| Word | In plain English |
|---|---|
| **Repository (repo)** | A project folder plus the full history of every change made to it |
| **Working tree** | Your files, as they are on your disk right now |
| **Staging area** (also *index*) | The "basket" of changes you have picked for your next commit (`git add` fills it) |
| **Commit** | A saved snapshot of the project, with a note saying what changed and why |
| **Commit ID** (also *SHA*) | The unique code that names a commit, such as `b8c506c` |
| **Branch** | A separate line of work; behind the scenes, a label that points at a commit |
| **main** | The official branch that everyone builds on |
| **HEAD** | Git's word for "where you are now" — normally the branch you are on |
| **Remote** · **origin** | Another copy of the project, usually on GitHub · the usual name for that copy |
| **Upstream** | The branch on GitHub that your local branch is linked to (set by `git push -u`) |
| **Push · fetch · pull** | Upload your commits · download new commits only · download *and* combine them |
| **Merge** · **merge conflict** | Combine two branches · the same line was changed on both, so a person must decide |
| **Fast-forward** | A merge where nothing needs combining: the branch simply moves forward |
| **Rebase** | Move your branch so it starts from the latest main; your commits get new IDs |
| **Force-with-lease** | A careful way to overwrite **your own** branch on GitHub after a rebase or amend |
| **Detached HEAD** | Looking at an old commit without being on any branch |
| **Untracked** · **.gitignore** | A file Git is not following · a list of files Git should never pick up |

## Contents

**Everyday commands — read these first**

| Get started | Save your work | Share with the team | Undo safely |
|---|---|---|---|
| [init · clone](#git-init--git-clone--start-a-repository) | [add · rm · mv](#git-add--git-rm--git-mv--choose-what-goes-into-the-next-commit) | [remote · fetch · pull](#git-remote--git-fetch--git-pull--keep-up-with-the-team) | [stash](#git-stash--park-unfinished-work) |
| [status · diff](#git-status--git-diff--see-what-has-changed) | [commit](#git-commit--record-a-change-and---amend) | [push](#git-push--publish-your-commits) | [restore](#git-restore--throw-away-or-unstage-changes-to-files) |
| [log · show · blame](#git-log--git-show--git-blame--read-the-history) | [branch · switch](#git-branch--git-switch--work-on-a-separate-line) | [merge · rebase](#merge-and-rebase) | [revert](#git-revert--undo-a-commit-that-is-already-shared) |

**Going further — optional:**
[reset](#git-reset--move-the-branch-back-soft--mixed--hard) ·
[reflog](#git-reflog--find-a-commit-you-thought-you-had-lost) ·
[cherry-pick](#git-cherry-pick--copy-one-commit-to-another-branch) ·
[tag · describe](#git-tag--git-describe--name-a-release) ·
[bisect](#git-bisect--find-the-commit-that-broke-it) ·
[clean](#git-clean--delete-files-git-is-not-tracking)

Two tables at the end pull it together: [which undo command?](#which-undo-command) and
[the commands that can destroy work](#the-commands-that-can-destroy-work).

### The picture every command acts on

```
 ┌──────────────┐   git add    ┌──────────────┐  git commit  ┌──────────────┐   git push   ┌──────────────┐
 │ WORKING TREE │ ───────────► │    INDEX     │ ───────────► │  LOCAL REPO  │ ───────────► │    REMOTE    │
 │ files on disk│ ◄─────────── │ (next commit)│ ◄─────────── │    .git/     │ ◄─────────── │   (GitHub)   │
 └──────────────┘  git restore └──────────────┘  git reset   └──────────────┘  git fetch   └──────────────┘
```

A command either **looks** at these areas (safe any time) or **changes** one of them. Before
pressing Enter, know which area you are about to change.

---

## `git init` · `git clone` — start a repository

**What it means.** `git init` tells Git to start keeping a history for a folder. It creates a hidden
`.git` folder where that history is stored; your own files are not changed. `git clone` downloads a
copy of a project that already exists — all its files and its full history — and remembers where it
came from, under the name `origin`.

**How.**

```
$ mkdir paytrack-api && cd paytrack-api
$ git init
Initialized empty Git repository in /home/you/devops-course/paytrack-api/.git/

$ git clone https://github.com/kumbulanit/devops_professional.git course-material
Cloning into 'course-material'...
remote: Enumerating objects: 140, done.
remote: Counting objects: 100% (140/140), done.
remote: Compressing objects: 100% (87/87), done.
remote: Total 140 (delta 22), reused 136 (delta 21), pack-reused 0 (from 0)
Receiving objects: 100% (140/140), 386.04 KiB | 10.16 MiB/s, done.
Resolving deltas: 100% (22/22), done.
$ cd course-material && git remote -v
origin	https://github.com/kumbulanit/devops_professional.git (fetch)
origin	https://github.com/kumbulanit/devops_professional.git (push)
```

| Option | Does |
|---|---|
| `git clone <url> <dir>` | Clone into a folder with a name you choose |
| `git clone --depth 1 <url>` | Only the latest commit — fast for CI, but no history for `log`, `blame` or `bisect` |
| `git clone -b <branch> <url>` | Check out a branch other than the default |

**Use it when.** `init` for brand-new work; `clone` for everything that already exists. Lab 02
uses both: `init` for `paytrack-api`, `clone` for the course material.

**Don't use it when / watch out.**
- Don't `git init` inside another repository — the nested repository confuses `status` and `add`.
  Run `git status` first; if it answers, you are already inside one.
- Don't put a password or token in the clone URL. It is stored in plain text in `.git/config`.
  Use a credential helper or SSH.

---

## `git status` · `git diff` — see what has changed

**What it means.** `git status` tells you what has changed since your last commit (your last save):
which files you have edited, which of those you have already picked for the next commit
(**staged**), and which files are new and not yet tracked by Git (**untracked**). `git diff` shows
the actual lines you changed; `git diff --staged` shows exactly what your next commit will contain.

**How.**

```
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   README.md

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   app/src/config.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	app/src/probes.py

$ git status -s
M  README.md
 M app/src/config.py
?? app/src/probes.py
$ git diff
diff --git a/app/src/config.py b/app/src/config.py
index 637a457..33f783d 100644
--- a/app/src/config.py
+++ b/app/src/config.py
@@ -3,5 +3,5 @@ import os
 
 class Config:
     VERSION = os.getenv("APP_VERSION", "1.0.0")
-    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "30"))
+    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "45"))
     REGION = os.getenv("APP_REGION", "local")
$ git diff --staged
diff --git a/README.md b/README.md
index 64d9350..cbd1350 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,3 @@
 # PayTrack API
+
+Card authorisation service.
```

Reading `git status -s`: the **first** column is the index, the **second** is the working tree.

| Code | Meaning |
|---|---|
| `M ` | Modified and staged |
| ` M` | Modified, not staged |
| `MM` | Staged, then edited again |
| `A ` | New file, staged |
| `R ` | Renamed, staged |
| `D ` / ` D` | Deleted (staged / not staged) |
| `??` | Untracked |

| Option | Does |
|---|---|
| `git status -sb` | Short form plus the branch and ahead/behind counts |
| `git diff --staged` | Index vs the last commit — **the next commit** |
| `git diff HEAD` | Everything (staged and not) vs the last commit |
| `git diff main...feature` | What `feature` adds since it branched from `main` |
| `git diff --stat` | Files and line counts only |

**Use it when.** Before **every** `add`, `commit`, `pull`, `switch` or `rebase`. `status` also
tells you when you are in the middle of a merge, rebase or cherry-pick — and prints the commands
that get you out.

**Watch out.** Once everything is staged, plain `git diff` shows **nothing**. That is exactly the
moment a debug print or a key gets committed. Make `git diff --staged` the last thing you run
before `git commit`.

---

## `git add` · `git rm` · `git mv` — choose what goes into the next commit

**What it means.** `git add` picks changes to go into your next commit. Git keeps them in the
**staging area** (also called the *index*) — think of a basket you fill before you pay. Nothing is
saved until you run `git commit`. `git rm --cached` takes a file out of the basket and tells Git to
stop tracking it, but leaves the file on your disk. `git mv` renames a file and tells Git about the
rename in one step.

**How.**

```
$ git add -p app/src/config.py
diff --git a/app/src/config.py b/app/src/config.py
index 637a457..33f783d 100644
--- a/app/src/config.py
+++ b/app/src/config.py
@@ -3,5 +3,5 @@ import os
 
 class Config:
     VERSION = os.getenv("APP_VERSION", "1.0.0")
-    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "30"))
+    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "45"))
     REGION = os.getenv("APP_REGION", "local")
(1/1) Stage this hunk [y,n,q,a,d,e,p,?]? y
$ git add app/src/probes.py
$ git status -s
M  app/src/config.py
A  app/src/probes.py
$ git commit -qm "feat: add readiness probe; raise settlement timeout to 45s"
$ git add .
$ git status -s
A  config/local.env
$ git rm --cached config/local.env
rm 'config/local.env'
$ echo 'config/local.env' >> .gitignore
$ git mv README.md docs/README.md
$ git add .gitignore
$ git status -s
M  .gitignore
R  README.md -> docs/README.md
```

| Command | Does |
|---|---|
| `git add <path>` | Stage a file or directory |
| `git add -p [path]` | Stage **hunk by hunk**: `y` stage · `n` skip · `s` split · `e` edit · `q` quit |
| `git add .` | Stage everything under the current directory, including new files |
| `git add -u` | Stage edits and deletions of **tracked** files only — never new files |
| `git rm <file>` | Delete the file and stage the deletion |
| `git rm --cached <file>` | Stop tracking, keep the file on disk |
| `git mv <old> <new>` | Rename and stage the rename |

**Use it when.** Every commit should be **one logical change**. `git add -p` is how a working tree
with three unrelated edits becomes three clean commits that can each be reviewed and reverted.

**Don't use it when / watch out.**
- Don't `git add .` without reading `git status` first. It is how `local.env`, `.venv/` and
  private keys reach a repository.
- `git rm --cached` only stops **future** tracking. If a secret was already **committed**, it is in
  history on every clone — **rotate the secret**; removing it from history is a separate,
  disruptive job.
- A rename shows as `R` only when the content is mostly unchanged; rename and heavy edit in one
  commit, and Git sees a delete plus an add.

---

## `git commit` — record a change (and `--amend`)

**What it means.** `git commit` saves everything in the staging area as a **commit**: a snapshot of
the project with a note saying what changed and why. Every commit gets a unique ID — a long code
such as `b8c506c…`, usually shown as its first seven characters; Git calls it a *SHA*. Commits are
permanent: `--amend` does not edit the last commit, it **replaces** it with a new one that has a new
ID.

**How.**

```
$ git switch -c feature/PAY-160
$ git status -s
 M app/src/probes.py
$ git commit -am "feat: report the store in /ready"
[feature/PAY-160 b8c506c] feat: report the store in /ready
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git push -u origin HEAD
To https://github.com/<your-username>/paytrack-api.git
 * [new branch]      HEAD -> feature/PAY-160
branch 'feature/PAY-160' set up to track 'origin/feature/PAY-160'.
# ...then you notice the missing docstring, add it, and amend
$ git commit -a --amend --no-edit
[feature/PAY-160 fcf6e04] feat: report the store in /ready
 Date: Thu Sep 17 08:26:43 2026 +0200
 1 file changed, 2 insertions(+), 1 deletion(-)
$ git push
To https://github.com/<your-username>/paytrack-api.git
 ! [rejected]        feature/PAY-160 -> feature/PAY-160 (non-fast-forward)
error: failed to push some refs to 'https://github.com/<your-username>/paytrack-api.git'
$ git push --force-with-lease
To https://github.com/<your-username>/paytrack-api.git
 + b8c506c...fcf6e04 feature/PAY-160 -> feature/PAY-160 (forced update)
```

| Option | Does |
|---|---|
| `-m "type: subject"` | Message on the command line (Conventional Commits: `feat:`, `fix:`, `docs:` …) |
| `-a` | Stage edits to **tracked** files first. New files are **not** included |
| `--amend` | Replace the last commit (new SHA) — with the current index and, unless `--no-edit`, a new message |
| `--fixup <sha>` | A commit marked to be folded into `<sha>` later by `git rebase -i --autosquash` |

**Use it when.** One logical change is complete and the tests pass. Small commits make
`git revert` and `git bisect` precise. `--amend` is for the commit you **just** made: a typo in the
message, a forgotten file.

**Don't use it when / watch out.**
- Don't `--amend` a commit that is already pushed. The push is rejected (as above), and forcing it
  rewrites history that someone may have pulled. On **your own** branch, `--force-with-lease` is
  acceptable; on a shared branch, add a new commit instead.
- `-a` silently skips new files. `git status` afterwards shows them still untracked.
- The subject says **what**; the body says **why**. The diff already shows what changed.

---

## `git log` · `git show` · `git blame` — read the history

**What it means.** `git log` lists past commits, newest first. `git show` opens one commit so you
can see exactly what it changed. `git blame` goes through a file line by line and tells you which
commit last changed each line. Together they answer *what changed, when, who did it — and why*, if
the commit notes are good.

**How.**

```
$ git log --oneline --graph --decorate
* 8159e94 (HEAD -> main, origin/main) feat: default region eu-west
* cf09014 fix: raise settlement timeout to 45s
* e901672 feat: add PayTrack API service
$ git log --oneline -- app/src/config.py
8159e94 feat: default region eu-west
cf09014 fix: raise settlement timeout to 45s
e901672 feat: add PayTrack API service
$ git log --oneline --grep=timeout
cf09014 fix: raise settlement timeout to 45s
$ git show --stat HEAD~1
commit cf09014a132e3fb76f3d590efa68c14b0f04556a
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:25:01 2026 +0200

    fix: raise settlement timeout to 45s

 app/src/config.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git blame --date=short -L 5,7 app/src/config.py
^e901672 (Your Name 2026-09-17 5)     VERSION = os.getenv("APP_VERSION", "1.0.0")
cf09014a (Your Name 2026-09-17 6)     TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "45"))
8159e940 (Your Name 2026-09-17 7)     REGION = os.getenv("APP_REGION", "eu-west")
```

| Command | Answers |
|---|---|
| `git log --oneline --graph --decorate --all` | The whole commit graph (Lab 02's `git lg` alias) |
| `git log -- <path>` | Commits that touched this file |
| `git log --follow -p <file>` | A file's full history with patches, across renames |
| `git log --author="Name" --since="2 weeks ago"` | Who did what, recently |
| `git log --grep="PAY-142"` | Commits whose **message** mentions a ticket |
| `git log -S "SETTLEMENT_TIMEOUT"` | Commits that **added or removed** that text |
| `git log main..origin/main` | Commits on `origin/main` that `main` does not have yet |
| `git show <sha>` · `git show <sha> --stat` | One commit, with its full diff or just the file list |
| `git blame -L 40,60 <file>` | Last change to each of those lines |

In `blame`, `^` in front of a SHA marks a line that has not changed since the first commit in the
range.

**Use it when.** Investigating a bug, reviewing what a release contains, or answering an audit
question: *who changed the settlement timeout, when, and why?* — answered in seconds, with no
meeting.

**Watch out.** `blame` names the **last** commit to touch a line, not the commit that introduced
the problem. A reformat or a rename hides the real change: use `git log -S "text"`, or
`git blame <sha>^ -- <file>` to look at the file as it was before that commit.

---

## `git branch` · `git switch` — work on a separate line

**What it means.** A **branch** is a separate line of work. Behind the scenes it is just a label
pointing at a commit, which moves forward each time you commit — which is why creating a branch is
instant. `git switch` moves you to a branch and changes the files in your folder to match it. (Older
guides use `git checkout` for this.)

**How.**

```
$ git switch -c feature/PAY-150-region-header
Switched to a new branch 'feature/PAY-150-region-header'
$ git branch
* feature/PAY-150-region-header
  main
# ...one commit on the branch...
$ git switch main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
$ git branch -vv
  feature/PAY-150-region-header d48abee feat: add region header
* main                          c479b91 [origin/main] feat: report the store in /ready
$ git branch -d feature/PAY-150-region-header
error: the branch 'feature/PAY-150-region-header' is not fully merged
hint: If you are sure you want to delete it, run 'git branch -D feature/PAY-150-region-header'
$ git branch -D feature/PAY-150-region-header
Deleted branch feature/PAY-150-region-header (was d48abee).
$ git switch --detach HEAD~3
HEAD is now at ff42a9b docs: describe the service
$ git switch main
Previous HEAD position was ff42a9b docs: describe the service
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
```

| Command | Does |
|---|---|
| `git switch -c <name>` | Create a branch at the current commit and switch to it (`git checkout -b <name>`) |
| `git switch <name>` | Switch to an existing branch |
| `git switch -` | Switch back to the previous branch |
| `git switch --detach <commit or tag>` | Look at an old commit without being on a branch |
| `git branch` · `git branch -vv` | List branches · with upstream, ahead/behind and last commit |
| `git branch -d <name>` | Delete a branch that is merged |
| `git branch -D <name>` | Force-delete, merged or not |
| `git branch -m <new>` | Rename the current branch |

**Use it when.** Every change gets its own short-lived branch named
`type/TICKET-short-description` (Module 2 §2.4). Use `--detach` to inspect a release —
`git switch --detach v1.0.0` — then switch back.

**Watch out.**
- `-D` deletes unmerged work. The commits are then reachable only through the
  [reflog](#git-reflog--find-a-commit-you-thought-you-had-lost). Read the `-d` error before forcing.
- Git refuses to switch if your uncommitted edits would be overwritten. Commit or
  [stash](#git-stash--park-unfinished-work) first.
- Commits made on a detached `HEAD` belong to no branch. Before switching away, keep them with
  `git switch -c <name>`.
- After a **squash** merge, `git branch -d` may say the branch is not merged — because its commits
  are not on `main`; a new squashed commit is. Check the PR was merged, then use `-D`.

---

## `git remote` · `git fetch` · `git pull` — keep up with the team

**What it means.** A **remote** is another copy of the project, usually on GitHub; `origin` is
simply the name Git gives the copy you cloned from. `git fetch` downloads new commits from it but
does **not** change your files or your branches — the downloaded work waits under names such as
`origin/main`. `git pull` downloads the new work **and** combines it into the branch you are on (a
fetch followed by a merge).

**How.**

```
$ git remote -v
origin	https://github.com/<your-username>/paytrack-api.git (fetch)
origin	https://github.com/<your-username>/paytrack-api.git (push)
$ git fetch origin
From https://github.com/<your-username>/paytrack-api
   1ecd14b..4949c99  main       -> origin/main
$ git status -sb
## main...origin/main [behind 1]
$ git log --oneline main..origin/main
4949c99 docs: add contributing guide
$ git pull
Updating 1ecd14b..4949c99
Fast-forward
 docs/CONTRIBUTING.md | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 docs/CONTRIBUTING.md
```

| Command | Does |
|---|---|
| `git remote -v` | List remotes and their URLs |
| `git remote add <name> <url>` | Add a remote (Lab 03 adds `origin`) |
| `git remote set-url origin <url>` | Change a remote's URL — for example HTTPS to SSH |
| `git fetch` · `git fetch --prune` | Download · and drop `origin/*` branches deleted on the server |
| `git pull` | `fetch` + `merge` (Lab 00 sets `pull.rebase false`) |
| `git pull --rebase` | `fetch` + `rebase` — no merge commit on your own branch |
| `git pull --ff-only` | Only if it can fast-forward; otherwise stop and let you decide |

**Use it when.** `fetch` any time — it is always safe. `pull` when your branch has **no local
commits**, so it simply fast-forwards (as above). With local commits, a plain `pull` creates a
merge commit; on your own branch prefer `git pull --rebase`.

**Watch out.**
- `pull` with uncommitted edits to the same files is refused. Commit or stash first.
- A habit worth keeping: `git fetch`, look at `git log main..origin/main`, then merge or rebase
  **on purpose** — instead of a blind `pull` that combines whatever happened to arrive.

---

## `git push` — publish your commits

**What it means.** `git push` uploads your **commits** to GitHub. Edits you have not committed are
not sent. GitHub only accepts a push that doesn't throw away anything already there — so if a
colleague pushed first, you pull their work before you can push yours.

**How.**

```
$ git switch -c feature/PAY-170
$ git commit -qm "feat: supported currency list"
$ git push
fatal: The current branch feature/PAY-170 has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin feature/PAY-170

$ git push -u origin HEAD
To https://github.com/<your-username>/paytrack-api.git
 * [new branch]      HEAD -> feature/PAY-170
branch 'feature/PAY-170' set up to track 'origin/feature/PAY-170'.
$ git status -sb
## feature/PAY-170...origin/feature/PAY-170
$ git push origin --delete feature/PAY-170
To https://github.com/<your-username>/paytrack-api.git
 - [deleted]         feature/PAY-170
```

| Command | Does |
|---|---|
| `git push -u origin HEAD` | First push of a branch: create it on the remote and remember it as the upstream |
| `git push` | Every push after that |
| `git push --force-with-lease` | Overwrite **your own** rewritten branch — refuses if anyone else pushed since your last fetch |
| `git push origin --delete <branch>` | Delete a remote branch |
| `git push origin <tag>` · `git push origin --tags` | Publish tags — they are not sent with commits |

**Use it when.** You want the change reviewed, backed up, or tested by CI. Push early to a branch;
a draft pull request makes work in progress visible.

**Don't use it when / watch out.**
- `! [rejected] ... (non-fast-forward)` means the remote has commits you do not. Fetch and
  integrate them. The **only** exception is when you rewrote your own branch (amend, rebase) — then
  `--force-with-lease`.
- Never `--force`: it overwrites whatever is there, including a colleague's push from a minute ago.
- Never force-push `main` or any shared branch. Branch protection (Lab 03) should make it
  impossible.

---

## `git stash` — park unfinished work

**What it means.** `git stash` puts your unsaved changes aside and gives you a clean folder, so you
can switch to something else — like sweeping your desk into a drawer. `git stash pop` takes them
back out of the drawer.

**How.**

```
$ git status -s
 M app/src/app.py
$ git stash push -m "wip: retry budget"
Saved working directory and index state On main: wip: retry budget
$ git status -s
$ git stash list
stash@{0}: On main: wip: retry budget
$ git switch -c hotfix/PAY-160
Switched to a new branch 'hotfix/PAY-160'
# ...fix, commit and push the hotfix...
$ git switch main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
$ git stash pop
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   app/src/app.py

no changes added to commit (use "git add" and/or "git commit -a")
Dropped refs/stash@{0} (fe5910451df5361b311fb3370d6ef5808673fc5c)
```

| Command | Does |
|---|---|
| `git stash push -m "note"` | Save tracked changes with a description |
| `git stash push -u -m "note"` | Include **untracked** files too |
| `git stash list` | Show the stack — `stash@{0}` is the newest |
| `git stash pop` | Re-apply the newest stash and **drop** it |
| `git stash apply stash@{1}` | Re-apply a stash and **keep** it |
| `git stash show -p stash@{0}` | Show what a stash contains |
| `git stash drop stash@{0}` | Delete one stash |

**Use it when.** An urgent hotfix arrives mid-change; or you need to `pull` or `switch` before you
are ready to commit.

**Don't use it when / watch out.**
- New, untracked files are **not** stashed by default — they follow you onto the other branch. Use
  `-u`.
- `pop` can conflict if the branch changed underneath; the stash is then **kept** until you resolve
  and `git stash drop` it.
- Don't use stash as storage. Stashes are easy to forget and never pushed. For anything longer than
  a coffee break, commit to a branch.

---

## `git restore` — throw away or unstage changes to files

**What it means.** `git restore` puts a **file** back the way it was at your last commit, throwing
away the edits you made since. With `--staged` it only takes the file out of the staging area (the
basket) and keeps your edits. It never creates or deletes commits.

**How.**

```
$ git status -s
 M app/src/app.py
 M app/src/config.py
$ git restore app/src/config.py
$ git add app/src/app.py
$ git status -s
M  app/src/app.py
$ git restore --staged app/src/app.py
$ git status -s
 M app/src/app.py
$ git restore --source=HEAD~2 app/src/config.py
$ git diff --stat
 app/src/app.py    | 1 +
 app/src/config.py | 4 ++--
 2 files changed, 3 insertions(+), 2 deletions(-)
```

| Command | Does | Destroys work? |
|---|---|---|
| `git restore <file>` | Discard unstaged edits to the file | **Yes — unrecoverable** |
| `git restore --staged <file>` | Unstage, keep the edit | No |
| `git restore --source=<commit> <file>` | Bring back the file as it was in that commit | Overwrites current edits |
| `git restore .` | Discard **all** unstaged edits under this directory | **Yes** |

**Use it when.** `--staged` is the everyday, safe undo for "I added the wrong file".
`restore <file>` when an experiment went nowhere. `--source` to recover an old version of a
single file without touching the rest of the history.

**Watch out.** `git restore <file>` cannot be undone: those edits were never committed, so neither
the reflog nor anything else can bring them back. If you are not sure, `git stash` instead.

---

## `git reset` — move the branch back (soft · mixed · hard)

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** `git reset <commit>` moves your current branch back to an earlier commit, so the
commits after it are no longer on the branch. The option you choose decides what happens to the
changes those commits contained:

| Mode | Branch pointer | Index | Working tree | In one sentence |
|---|---|---|---|---|
| `--soft` | Moves | Keeps the changes **staged** | Untouched | "Uncommit, keep everything ready to commit again" |
| `--mixed` (default) | Moves | Changes **unstaged** | Untouched | "Uncommit and unstage, keep the edits" |
| `--hard` | Moves | Reset | **Reset — edits discarded** | "Make everything look exactly like that commit" |

**How.**

```
$ git log --oneline -2
c26a67d chore: note the retry budget
8159e94 feat: default region eu-west
$ git reset --soft HEAD~1
$ git status -s
M  app/src/app.py
$ git commit -qm "chore: note the retry budget"
$ git reset HEAD~1
Unstaged changes after reset:
M	app/src/app.py
$ git status -s
 M app/src/app.py
$ git commit -qam "chore: note the retry budget"
$ git reset --hard HEAD~1
HEAD is now at 8159e94 feat: default region eu-west
$ git status -s
$ git log --oneline -1
8159e94 feat: default region eu-west
```

(The re-made commit got the same SHA, `c26a67d`, each time — same snapshot, parent, author, second
and message.)

**Use it when.** Only on commits that are **not pushed**: splitting the last commit (`--soft` or
`--mixed`, then `add -p`), or abandoning local work entirely (`--hard`). `git reset --hard
origin/main` makes a local branch match the server exactly — Lab 03 uses it after the rejected push
to a protected `main`.

**Don't use it when / watch out.**
- Never reset a branch that is pushed and shared. It rewrites history; use
  [`git revert`](#git-revert--undo-a-commit-that-is-already-shared).
- `--hard` also discards uncommitted edits, and those are gone for good. Committed work can still be
  found with the [reflog](#git-reflog--find-a-commit-you-thought-you-had-lost).

---

## `git reflog` — find a commit you thought you had lost

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** The **reflog** is Git's private diary of everywhere you have been in your copy of
the project: every commit, switch, reset and rebase. It even remembers commits that no branch points
to any more — which is why a commit you think you have lost can almost always be found.

**How.**

```
$ git reset --hard HEAD~1
HEAD is now at 8159e94 feat: default region eu-west
# ..."wait — I needed that commit"
$ git reflog -4
8159e94 HEAD@{0}: reset: moving to HEAD~1
c26a67d HEAD@{1}: commit: chore: note the retry budget
8159e94 HEAD@{2}: reset: moving to HEAD~1
c26a67d HEAD@{3}: commit: chore: note the retry budget
$ git reset --hard HEAD@{1}
HEAD is now at c26a67d chore: note the retry budget
$ git log --oneline -2
c26a67d chore: note the retry budget
8159e94 feat: default region eu-west
```

| Command | Does |
|---|---|
| `git reflog` · `git reflog -10` | Where `HEAD` has been, newest first |
| `git reflog show <branch>` | Where one branch pointer has been |
| `git reset --hard HEAD@{n}` | Put the branch back to that position |
| `git switch -c rescue HEAD@{n}` | Keep that commit on a new branch without moving the current one |
| `ORIG_HEAD` | Shortcut to where the branch was before the last reset, merge or rebase |

**Use it when.** A `reset --hard`, an `--amend`, a rebase or a `branch -D` removed something you
needed.

**Watch out.** The reflog is **local** (a colleague's reflog cannot help you, and a fresh clone has
none), entries **expire** (about 90 days by default), and edits that were never committed were
never in it.

---

## `git revert` — undo a commit that is already shared

**What it means.** `git revert` undoes an old commit by creating a **new** commit that does the
exact opposite. Nothing is deleted or rewritten, so it is safe even after the change has been
shared: everyone else simply pulls one more commit, and the history shows both the mistake and its
fix.

**How.**

```
$ git log --oneline -3
6862196 perf: cut settlement timeout to 5s
c479b91 feat: report the store in /ready
b3b21c8 docs: move README under docs/; ignore local env
# ...pushed an hour ago — and settlements start timing out
$ git revert HEAD --no-edit
[main b4a1a93] Revert "perf: cut settlement timeout to 5s"
 Date: Thu Sep 17 08:22:25 2026 +0200
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline -3
b4a1a93 Revert "perf: cut settlement timeout to 5s"
6862196 perf: cut settlement timeout to 5s
c479b91 feat: report the store in /ready
$ git show --stat HEAD
commit b4a1a930a94acfbe4b8aaa8f8ab61251c2e1f1b0
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:22:25 2026 +0200

    Revert "perf: cut settlement timeout to 5s"
    
    This reverts commit 68621963449596b4f6056a595649c7ca2a33690e.

 app/src/config.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

| Option | Does |
|---|---|
| `git revert <sha>` | Undo one commit (opens the editor for the message) |
| `git revert --no-edit <sha>` | Accept the generated message |
| `git revert -m 1 <merge-sha>` | Undo a **merge** commit, keeping parent 1 (the branch you merged into) |
| `git revert --no-commit <a> <b>` | Undo several commits as one reviewable change |

**Use it when.** The commit is already pushed, or already on `main`. In a regulated environment it
is the audit-friendly rollback: the revert names the commit it undoes and goes through the same
pull request and CI as any other change (Appendix A).

**Watch out.**
- If later commits built on the reverted one, the revert can conflict — resolve it like a merge and
  run the tests.
- Reverting a revert brings the change back. Do it deliberately, with the fix that made the change
  safe, not as a reflex.

---

## `git cherry-pick` — copy one commit to another branch

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** `git cherry-pick` copies the change from one commit onto the branch you are on,
as a **new** commit with a new ID. The original stays where it was. It is how a single fix is copied
to an older release without bringing everything else along.

**How.**

```
$ git log --oneline -1
1ecd14b fix: default currency to EUR
$ git switch release/2026.10
Switched to branch 'release/2026.10'
Your branch is up to date with 'origin/release/2026.10'.
$ git cherry-pick -x 1ecd14b
[release/2026.10 3d690ff] fix: default currency to EUR
 Date: Thu Sep 17 08:22:26 2026 +0200
 1 file changed, 1 insertion(+)
$ git log --oneline -2
3d690ff fix: default currency to EUR
c479b91 feat: report the store in /ready
$ git log -1 --format=%B
fix: default currency to EUR

(cherry picked from commit 1ecd14bd10ed4f148fec87bd9e69e0a7fe973d8d)
```

| Option | Does |
|---|---|
| `-x` | Append "(cherry picked from commit …)" — the audit trail for a back-port |
| `<a>..<b>` | Pick a range (commits after `a` up to `b`) |
| `--continue` · `--abort` | After resolving a conflict · give up and restore the branch |

**Use it when.** A fix must reach a **release branch** without everything else on `main` — the
classic hotfix back-port (GitFlow, Module 2 §2.4).

**Don't use it when / watch out.**
- Don't move whole features between long-lived branches with cherry-pick. You create duplicate
  commits with different SHAs, and a later merge of those branches conflicts with itself. Merge
  instead.
- It can conflict exactly like a merge: fix the file, `git add`, `git cherry-pick --continue`.

---

## `git tag` · `git describe` — name a release

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** A **tag** is a permanent name for one commit, such as `v1.1.0`. Unlike a branch
it never moves, so `v1.1.0` always means exactly the same code. An **annotated** tag (`-a`) also
records who created it, when, and a message — use that kind for releases.

**How.**

```
$ git tag -a v1.1.0 -m "PayTrack API 1.1.0"
$ git tag -n
v1.1.0          PayTrack API 1.1.0
$ git push origin v1.1.0
To https://github.com/<your-username>/paytrack-api.git
 * [new tag]         v1.1.0 -> v1.1.0
# ...one more commit lands on main...
$ git describe --tags
v1.1.0-1-g32fc9b7
$ git show v1.1.0 --no-patch
tag v1.1.0
Tagger: Your Name <you@example.com>
Date:   Thu Sep 17 08:22:26 2026 +0200

PayTrack API 1.1.0

commit 4949c99cf69f1aa1c760ce18063c92880f2f1581
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:22:26 2026 +0200

    docs: add contributing guide
```

| Command | Does |
|---|---|
| `git tag -a v1.2.0 -m "Release 1.2.0"` | Annotated tag on `HEAD` — **use this for releases** |
| `git tag -a v1.2.0 <sha> -m "…"` | Tag an earlier commit |
| `git tag -n` · `git tag -l "v1.*"` | List with messages · filter |
| `git push origin v1.2.0` · `git push origin --tags` | Publish — tags are **not** pushed with commits |
| `git describe --tags` | Name the current commit from its nearest tag |

Reading `v1.1.0-1-g32fc9b7`: **one** commit after `v1.1.0`, at commit `32fc9b7` (the `g` stands
for git). Lab 06 stamps the same short SHA into every image (`org.opencontainers.image.revision`)
for exactly this traceability.

**Don't use it when / watch out.** Never move or re-use a published tag: someone has already built
and deployed from it. If `v1.1.0` is wrong, release `v1.1.1`.

---

## `git bisect` — find the commit that broke it

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** `git bisect` finds the commit that broke something. You tell it one version that
worked and one that doesn't; it picks the commit halfway between, you test it and say good or bad,
and it halves the range again. About ten tests are enough to search a thousand commits.

**How.** Card fees were right in `v1.0.0` (`fee(4599) == 45`) and are wrong today, seven commits
later:

```
$ git log --oneline
1f01f26 chore: tidy imports
fca16b8 docs: update changelog
ca37b9a feat: fee for GBP cards
4f79a0c refactor: simplify fee rounding
7bfd8d9 chore: bump flask to 3.0.3
200d865 test: add fee examples
940514e docs: explain fee rounding
a672017 feat: card fee (1 %)
$ git bisect start
status: waiting for both good and bad commits
$ git bisect bad
status: waiting for good commit(s), bad commit known
$ git bisect good v1.0.0
Bisecting: 3 revisions left to test after this (roughly 2 steps)
[7bfd8d959e5f653ae56caa21fabb5f72a8b3af37] chore: bump flask to 3.0.3
$ git bisect run python3 test_fee.py
running 'python3' 'test_fee.py'
ok
Bisecting: 1 revision left to test after this (roughly 1 step)
[ca37b9aca84d73133b3e4630d9f7c508762a2969] feat: fee for GBP cards
running 'python3' 'test_fee.py'
Traceback (most recent call last):
  File "test_fee.py", line 2, in <module>
    assert fee(4599) == 45, fee(4599)
AssertionError: 46
Bisecting: 0 revisions left to test after this (roughly 0 steps)
[4f79a0c204e4d74a1ed2417bc369756c88713493] refactor: simplify fee rounding
running 'python3' 'test_fee.py'
Traceback (most recent call last):
  File "test_fee.py", line 2, in <module>
    assert fee(4599) == 45, fee(4599)
AssertionError: 46
4f79a0c204e4d74a1ed2417bc369756c88713493 is the first bad commit
commit 4f79a0c204e4d74a1ed2417bc369756c88713493
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:23:42 2026 +0200

    refactor: simplify fee rounding

 CHANGELOG.md | 1 +
 fee.py       | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
bisect found first bad commit
$ git bisect reset
Previous HEAD position was 4f79a0c refactor: simplify fee rounding
Switched to branch 'main'
```

The "harmless" refactor replaced `amount_minor // 100` (always round down) with
`round(amount_minor / 100)` (round to nearest) — so a fee of 45.99 became 46 instead of 45. Found
in three tests, not by reading seven diffs.

| Command | Does |
|---|---|
| `git bisect start` · `bad [commit]` · `good <commit>` | Begin, and mark the two ends |
| `git bisect good` · `git bisect bad` | Answer for the commit Git has checked out |
| `git bisect skip` | This commit cannot be tested (for example, it does not build) |
| `git bisect run <command>` | Let a script answer: exit **0** = good · **1–127** = bad · **125** = skip |
| `git bisect reset` | Finish and return to where you started |

**Use it when.** "It worked in 1.0.0" and nobody knows what changed — the reason the test suite
must run on any commit, and why small commits pay off.

**Watch out.** Always finish with `git bisect reset`, or you are left on a detached `HEAD` in the
middle of history.

---

## `git clean` — delete files Git is not tracking

> **Going further — optional.** Not needed for the labs on Day 2; come back to it once the everyday commands feel familiar.

**What it means.** `git clean` deletes files from your disk that Git is **not** tracking — build
output, scratch files. Because those files were never in Git, once they are deleted they are gone
for good.

**How.**

```
$ git status -s
?? build/
?? scratch.txt
$ git clean -n
Would remove scratch.txt
$ git clean -nd
Would remove build/
Would remove scratch.txt
$ git clean -fd
Removing build/
Removing scratch.txt
$ git status -s
```

| Option | Does |
|---|---|
| `-n` | **Dry run** — list what would be deleted. Always run this first |
| `-f` | Actually delete (required) |
| `-d` | Include untracked directories |
| `-x` | Also delete **ignored** files — `.venv/`, `.env`, build caches |
| `-i` | Interactive: choose file by file |

**Use it when.** Build output or scratch files clutter the tree and you want exactly what is in the
repository — for example before reproducing a CI failure locally.

**Don't use it when / watch out.**
- Never `git clean -fdx` in a project you are working in: `-x` deletes `.venv/` and `.env` too.
  Ignored does not mean unimportant.
- There is **no undo**. Untracked files were never in Git, so not even the reflog can bring them
  back.

---

## Merge and rebase

Both combine work from two branches; they differ in what they do to history. They have their own
section in Module 2, with the same kind of real output:

- [§2.5 — the four merge strategies](module-02-version-control-and-ci.md#25-merge-strategies--what-each-one-does-to-history):
  fast-forward, merge commit, squash, rebase.
- [§2.5 — Rebase in practice](module-02-version-control-and-ci.md#rebase-in-practice--what-it-means-how-to-do-it-when-to-use-it):
  what rebase means, how to rebase, conflicts during a rebase, interactive rebase, undoing a
  rebase, and when to rebase or merge.

| Command | One line |
|---|---|
| `git merge <branch>` | Join the branch in; creates a merge commit with two parents unless it can fast-forward |
| `git merge --squash <branch>` | Stage the branch's combined change as one new commit |
| `git merge --abort` | Give up on a conflicted merge |
| `git rebase <base>` | Replay your commits on top of `<base>` as new commits |
| `git rebase -i <base>` | Edit the replay plan: reorder, squash, fixup, reword, drop |
| `git rebase --continue` · `--skip` · `--abort` | Move on after a conflict · drop this commit · give up |

> **Rule of thumb:** rebase to tidy and update **your** work; merge to combine **shared** work.

---

## Which undo command?

Pick by **what has already happened** to the change.

| The change is… | You want to… | Command | Safe on a shared branch? |
|---|---|---|---|
| Edited, not staged | Throw the edit away | `git restore <file>` | — (local only) · **unrecoverable** |
| Edited, not staged | Keep it for later | `git stash push -m "…"` | — |
| Staged | Unstage it, keep the edit | `git restore --staged <file>` | — |
| Committed, **not pushed** | Fix the message or add a file | `git commit --amend` | No |
| Committed, **not pushed** | Uncommit, keep the changes | `git reset --soft HEAD~1` | No |
| Committed, **not pushed** | Throw the commit away | `git reset --hard HEAD~1` | No |
| Committed and **pushed** | Undo it | `git revert <sha>` | **Yes** |
| Rebased, reset or deleted by mistake | Get it back | `git reflog` → `git reset --hard HEAD@{n}` | Local only |
| A file from an old commit | Bring back that version | `git restore --source=<sha> <file>` | Yes (then commit) |

## The commands that can destroy work

| Command | What is lost | Recoverable? |
|---|---|---|
| `git restore <file>` / `git restore .` | Uncommitted edits | **No** |
| `git reset --hard` | Uncommitted edits (and commits, from the branch) | Commits via reflog; edits **no** |
| `git clean -f` (and especially `-fdx`) | Untracked (and ignored) files | **No** |
| `git branch -D` | An unmerged branch | Via reflog, for a while |
| `git stash drop` / `git stash clear` | Stashed changes | Only with low-level recovery — treat as **no** |
| `git push --force` | Other people's commits on the remote | Only from someone's local clone |
| `git commit --amend` / `git rebase` after pushing | The shared history others built on | Via reflog — but everyone must resynchronise |

> Before any of these: `git status`, and for `clean` always `-n` first. When in doubt, `git stash`
> or commit to a scratch branch — both are cheap and reversible.

---

**Back to:** [Module 2 — Version Control and CI](module-02-version-control-and-ci.md) ·
[Git cheat sheet](../../reference/git-cheatsheet.md) ·
Labs [02](../../labs/lab-02-git-fundamentals/README.md) ·
[03](../../labs/lab-03-branching-and-collaboration/README.md) ·
[04](../../labs/lab-04-github-actions-ci/README.md)
