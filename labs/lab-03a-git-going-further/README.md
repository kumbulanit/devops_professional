# Lab 03A — Git, Going Further: Undo, Rescue, Rewrite and Release

| | |
|---|---|
| **Day** | 2 — **optional**, after class or as homework |
| **Duration** | About 80 minutes, in eight parts you can do on different evenings |
| **Module** | 2 — Version Control and CI (the *Going Further* slides, sections B and C) |
| **You will produce** | Nothing the later labs need — you will have *used* every advanced command in the slides, on a practice copy |
| **Feeds into** | Nothing. This is a skills lab: it makes Labs 03–19 less frightening |

---

## Objective

The Going Further deck *shows* `reset`, `reflog`, `cherry-pick`, `bisect`, interactive rebase and
force-pushing. This lab makes you **do** each one and watch what happens — including the
commands that destroy work, run where destroying work costs nothing.

You work in a **practice repository** (we call it "the gym"): a copy of PayTrack API with ten
days of history written by four people. One of those commits quietly breaks the card-fee maths.
You will find it without reading a single diff.

> 🔑 **Never practise these commands on `paytrack-api-team`.** Several of them delete work on
> purpose. The gym can be rebuilt in two seconds; your real repository cannot.

## Prerequisites

- Lab 00 Step 6 done (git knows your name and email)
- The course material cloned at `~/devops-course/course-material` (Lab 00 did this)
- **No GitHub account, no network and no Docker needed** — everything runs on your machine

## Words you need

| Word | Plain meaning |
|---|---|
| **HEAD** | "Where I am now" — normally the latest commit of the branch you are on |
| **Detached HEAD** | You are looking at an old commit directly, not at a branch. Fine for looking; do not commit here |
| **Hunk** | One block of changed lines inside a file |
| **Reflog** | Your clone's private diary of every place HEAD has been. Nothing you commit is lost while it is in the reflog |
| **ORIG_HEAD** | Where the branch was just before the last big move (reset, rebase, merge) |
| **Upstream** | The branch on the server that your local branch pushes to and pulls from |
| **Lease** | "Only overwrite the server if it still looks the way I last saw it" |

🔁 **RECOVER / START AGAIN** — at any point, from anywhere:
```bash
cd ~/devops-course/course-material && git pull --ff-only
bash ~/devops-course/course-material/labs/lab-03a-git-going-further/setup-gym.sh
```
**What this does:** updates the course material, then deletes and rebuilds the gym (and the
`git-gym-origin.git` and `git-gym-colleague` folders Part 8 creates). Nothing else is touched.
If `git pull` complains, skip it — the script works with the copy you already have.

---

## Part 1 — Build the gym (5 min)

```bash
bash ~/devops-course/course-material/labs/lab-03a-git-going-further/setup-gym.sh
cd ~/devops-course/git-gym
```
**What this does:** runs a script that copies the PayTrack API app into
`~/devops-course/git-gym` and makes **ten commits as four different people** (you, Ana, Ben and
Chen), spread over the last ten days. It tags the first commit `v1.0.0`. Read the script if you
are curious — but try not to look for the bug yet.

✅ **Checkpoint** — the script ends by printing ten commits, newest first (your hashes will
differ):
```
23cf3fc (HEAD -> main) chore: bump version to 1.1.0
22e794b docs: record card fees in the changelog
...
f80abaf feat(fees): add the card fee calculator
dc28ee8 (tag: v1.0.0) feat: add PayTrack API service
```

---

## Part 2 — Read the history like a detective (5 min)

```bash
git log --oneline --graph --decorate --all
```
**What this does:** one line per commit (`--oneline`), a drawing of branches (`--graph`), branch
and tag names (`--decorate`) for every branch (`--all`). This is the command you will type most
often in this lab.

```bash
git log --format='%h  %<(11)%an %<(12)%ar %s'
```
**What this does:** a custom layout — short hash (`%h`), author name padded to 11 characters
(`%<(11)%an`), how long ago (`%ar`) and the message (`%s`). You should see Ana, Ben and Chen, with
dates from "10 days ago" to "24 hours ago".

```bash
git show --stat HEAD~3
```
**What this does:** shows one commit — who, when, the message and which files changed
(`--stat`). `HEAD~3` means "three commits before where I am".

```bash
git log --oneline -S MIN_FEE_MINOR
```
**What this does:** the **pickaxe**. It finds the commits that *added or removed* the text
`MIN_FEE_MINOR`. Expect exactly one: `feat(fees): add a minimum fee of 5 cents`. This is how you
answer "when did this setting appear?" in a repository with ten thousand commits.

```bash
git log --oneline -- docs/fees.md
git log --oneline --author=Ben
```
**What this does:** the history of **one file** (everything after `--` is a path), then only
**Ben's** commits. Filters combine: `git log --author=Ben -- docs/fees.md` works too.

```bash
git blame -L 1,5 app/src/fees.py
```
**What this does:** for lines 1 to 5 of the file, shows **who last changed each line, in which
commit, and when**. Lines 1–3 come from Ana; line 4 (`MIN_FEE_MINOR`) from Chen. "Blame" is an
unkind name for a useful command: it tells you whom to *ask*.

---

## Part 3 — Put work aside, and save only part of it (10 min)

### Step 3.1 — `git stash`: an urgent interruption

You are halfway through a change when someone asks, "What version did 1.0.0 report?"

```bash
printf '\nFees are shown on every receipt.\n' >> docs/fees.md
printf 'Ask Risk whether refunds pay a fee.\n' > notes.txt
git status -s
```
**What this does:** makes an unfinished edit to a tracked file and creates a new, untracked
file. `git status -s` shows ` M docs/fees.md` (modified) and `?? notes.txt` (untracked).

```bash
git switch --detach v1.0.0
```
**What this does:** tries to look at the `v1.0.0` commit. **It fails, on purpose:**
`error: Your local changes to the following files would be overwritten by checkout`. Git refuses
to throw your edit away. You need somewhere to put it.

```bash
git stash push --include-untracked -m "wip: receipts paragraph and notes"
git status -s
git stash list
```
**What this does:** `stash push` saves your uncommitted changes on a shelf and makes the working
folder clean. `--include-untracked` shelves the **new** file too — without it, `notes.txt` would
stay behind. `git status -s` now prints nothing; `git stash list` shows
`stash@{0}: On main: wip: receipts paragraph and notes`.

```bash
git switch --detach v1.0.0
grep -n APP_VERSION app/src/config.py
git switch main
```
**What this does:** now the switch works (`HEAD is now at … feat: add PayTrack API service`). You
read the answer — `"APP_VERSION", "1.0.0"` — and go back to `main`.

```bash
git stash pop
git status -s
```
**What this does:** takes the top item off the shelf and puts the changes back
(`Dropped refs/stash@{0}`). Both ` M docs/fees.md` and `?? notes.txt` are back.

> ⚠️ **Pop on the branch you stashed from.** Popping onto a different commit can conflict —
> for example if the file does not exist there. If that happens the stash is **kept**, so
> nothing is lost: `git reset --hard`, switch back, and pop again.

```bash
rm notes.txt
git restore docs/fees.md
```
**What this does:** throws both changes away, so the next step starts clean. `git restore <file>`
puts a tracked file back to its last committed state — **the edit is gone for good**.

### Step 3.2 — `git add -p`: commit part of a file

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("docs/fees.md")
s = p.read_text()
s = s.replace("PayTrack charges a fee on every card payment.",
              "PayTrack charges a small fee on every card payment.")
s = s.replace("| 1.00 | 0.05 (the minimum) |",
              "| 1.00 | 0.05 (the minimum) |\n| 45.99 | 0.68 (rounded down) |")
p.write_text(s)
PY
git diff --stat
```
**What this does:** makes **two unrelated edits** in one file — a wording change near the top
and a new example row at the bottom. `git diff --stat` shows one file changed.

```bash
git add -p docs/fees.md
```
**What this does:** **p**atch mode. Git shows each hunk and asks
`Stage this hunk [y,n,q,a,d,…]?`
- For the **first** hunk (`small fee`) press **`y`** then Enter — stage it.
- For the **second** hunk (the `45.99` row) press **`n`** then Enter — leave it.

```bash
git status -s
git commit -m "docs: say the fee is smal"
```
**What this does:** `git status -s` shows `MM docs/fees.md` — the **first** M means "some changes
staged", the **second** "some changes not staged". The commit takes only the staged hunk… and has
a typo in its message.

### Step 3.3 — `git commit --amend`: fix the commit you just made

```bash
git commit --amend -m "docs: say the fee is small"
git log --oneline -2
```
**What this does:** **replaces** the last commit with a new one — same changes, new message,
**new hash**. The log shows one `docs: say the fee is small` commit, not two.

⚠️ Only amend a commit you have **not pushed**. Part 8 shows what happens to the people who had
already pulled it.

```bash
git diff
git commit -am "docs: add a rounding example"
```
**What this does:** `git diff` shows the change still waiting — the `45.99` row. `commit -am`
stages every modified tracked file and commits it. Two clean commits, each with one purpose,
from one messy editing session.

---

## Part 4 — Undo: restore, reset, reflog (10 min)

### Step 4.1 — `git restore`: undo an edit you have not committed

```bash
echo 'FEE_BPS = 9999' >> app/src/fees.py
git status -s
git restore app/src/fees.py
git status -s
```
**What this does:** makes a bad edit (` M app/src/fees.py`), then throws it away. The second
`git status -s` prints nothing.

### Step 4.2 — `git reset`: move the branch back, three ways

First, make a commit to experiment with:

```bash
python3 -c "import pathlib; p=pathlib.Path('app/src/fees.py'); p.write_text(p.read_text().replace('FEE_BPS = 150', 'FEE_BPS = 200'))"
git commit -am "experiment: try a 2% fee"
git log --oneline -2
```
**What this does:** changes the fee rate from 150 to 200 basis points and commits it.

```bash
git reset --soft HEAD~1
git status -s
```
**What this does:** moves `main` back one commit but **keeps the change staged** — status shows
`M  app/src/fees.py` (M in the first column). Use it to redo a commit: split it, or add a file you
forgot.

```bash
git commit -m "experiment: try a 2% fee"
git reset HEAD~1
git status -s
```
**What this does:** commits again, then resets **without** a flag. That is `--mixed`, the
default: the commit is undone and the change is **kept but unstaged** — status shows
` M app/src/fees.py` (M in the second column).

```bash
git commit -am "experiment: try a 2% fee"
git reset --hard HEAD~1
git status -s
grep -n 'FEE_BPS =' app/src/fees.py
```
**What this does:** commits a third time, then resets `--hard`: the commit is undone **and the
change is deleted from your files**. Status is empty and the file says `FEE_BPS = 150` again.

| | The commit | Staged? | Your files |
|---|---|---|---|
| `git reset --soft HEAD~1` | undone | ✔ still staged | kept |
| `git reset HEAD~1` (mixed) | undone | ✘ unstaged | kept |
| `git reset --hard HEAD~1` | undone | ✘ | **deleted** |

### Step 4.3 — `git reflog`: get the "deleted" commit back

```bash
git reflog -6
```
**What this does:** prints your clone's diary of where HEAD has been, newest first:
```
6feb74f HEAD@{0}: reset: moving to HEAD~1
85c99d4 HEAD@{1}: commit: experiment: try a 2% fee
...
```
`HEAD@{1}` is the commit `--hard` threw away. **It still exists.**

```bash
git branch experiment/two-percent HEAD@{1}
git show experiment/two-percent:app/src/fees.py | grep "FEE_BPS ="
```
**What this does:** puts a branch label on that commit so it cannot get lost again, then reads the
file *as it is in that commit*, without switching to it (`<branch>:<path>`). You see
`FEE_BPS = 200` — rescued.

```bash
git branch -D experiment/two-percent
git branch experiment/two-percent HEAD@{1}
git branch
```
**What this does:** force-deletes the branch — Git prints `Deleted branch experiment/two-percent
(was 85c99d4).` — and immediately recreates it. **Deleting a branch deletes the label, not the
commits.** Write down the hash in the `(was …)` message; `git branch <name> <hash>` brings it back
too.

```bash
git branch -D experiment/two-percent
```
**What this does:** tidies up. The experiment is not needed again.

> 🔑 The reflog is **local** and **temporary** — it lives only in your clone and entries expire
> after about 90 days. It cannot rescue a commit that was never committed.

---

## Part 5 — Find the bug with `git bisect`, fix it with `git revert` (10 min)

### Step 5.1 — The symptom

```bash
python3 app/tests/check_fees.py
```
**What this does:** runs the card-fee checks. **They fail:**
`AssertionError: expected 68, got 69: a fee was rounded UP`. The bank's rule is that fees round
*down*. Somewhere in the last ten days, something changed that. Which commit?

### Step 5.2 — Find a commit you know was good

```bash
git log --oneline -S "def card_fee"
GOOD=$(git log --format=%h -S "def card_fee")
echo "$GOOD"
```
**What this does:** the pickaxe again — the commit that first added the `card_fee` function. It
went through review with its check passing, so it is **known good**. The second line stores its
hash in a shell variable, `GOOD`, so you do not have to copy it by hand.

### Step 5.3 — Let Git search for you

```bash
git bisect start HEAD "$GOOD"
```
**What this does:** starts a binary search between a **bad** commit (`HEAD`, now) and a **good**
one. Git checks out the commit halfway between and prints
`Bisecting: 4 revisions left to test after this (roughly 2 steps)`.

```bash
git bisect run python3 app/tests/check_fees.py
```
**What this does:** runs the check on each commit Git picks. **Exit code 0 means good; any other
code (except 125) means bad.** Git halves the range after every answer. In about three runs it
prints:
```
8ccacf5… is the first bad commit
commit 8ccacf5…
Author: Ben Okafor <ben.okafor@example.com>
    refactor(fees): simplify the fee maths
```
Ten commits would take 10 checks by hand; bisect needs 3. A thousand commits need 10.

```bash
BAD=$(git rev-parse --short refs/bisect/bad)
git bisect reset
git show "$BAD"
```
**What this does:** saves the culprit's hash in `BAD` (**before** `reset` removes the bisect
labels), returns you to `main`, and shows the commit. There it is: `// 10_000` (whole-number
division, which rounds down) became `round(… / 10_000)` (which rounds to the *nearest*). A
"simplification" that changed a banking rule.

> **Doing it by hand.** Without a script: `git bisect start`, then `git bisect bad` or
> `git bisect good` after testing each commit Git checks out, until it names the culprit.

### Step 5.4 — Undo it safely with `git revert`

```bash
git revert --no-edit "$BAD"
python3 app/tests/check_fees.py
git log --oneline -3
```
**What this does:** creates a **new** commit, `Revert "refactor(fees): simplify the fee maths"`,
that does the exact opposite of the bad one. Nothing in history is rewritten, so it is safe on a
branch everyone has pulled. The checks now print `fee checks passed`. `--no-edit` accepts Git's
suggested message without opening the editor.

| Undo with… | What happens to history | Safe after pushing? |
|---|---|---|
| `git revert` | Adds a new "opposite" commit | ✔ **Yes** |
| `git reset` | Moves the branch back; later commits disappear from it | ✘ Only on unpushed work |

### Step 5.5 — `git clean`: delete files Git does not track

```bash
mkdir -p build && echo 'pretend artefact' > build/paytrack.tar.gz
echo 'scratch' > scratch.txt
mkdir -p app/src/__pycache__ && echo x > app/src/__pycache__/fees.cpython-312.pyc
git status -s
```
**What this does:** creates the sort of clutter a build leaves behind. `git status -s` lists
`?? build/` and `?? scratch.txt` — but **not** `__pycache__/`, because `.gitignore` hides it.

```bash
git clean -n
git clean -nd
git clean -ndX
```
**What this does:** **`-n` is a dry run** — it only prints what *would* be removed. Always run it
first.
- `-n` → `Would remove scratch.txt` (files only)
- `-nd` → adds `build/` (`-d` includes folders)
- `-ndX` → `Would remove app/src/__pycache__/` (capital `-X`: **only** ignored files)

```bash
git clean -fd
git status -s --ignored
```
**What this does:** `-f` (force) actually deletes `build/` and `scratch.txt`. `--ignored` shows
that `!! app/src/__pycache__/` is still there, untouched.

> 🔴 **`git clean -fdx` (lower-case x) deletes untracked *and ignored* files** — which includes
> your `.venv/`, your `.env` with its passwords and any local database. There is no undo: these
> files were never committed, so not even the reflog knows about them. Dry-run with `-n` first,
> every time.

---

## Part 6 — Releases: tags, versions and hot-fixes (10 min)

### Step 6.1 — Tag a release, and let Git describe any commit

```bash
git tag -a v1.1.0 -m "PayTrack API 1.1.0 - card fees"
git describe --tags
```
**What this does:** creates an **annotated** tag — it records who tagged, when and why — on the
current commit. `git describe --tags` prints `v1.1.0`: this commit *is* the release.

```bash
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Fixed: card fees round down again.\n'))"
git commit -am "docs: note the rounding fix in the changelog"
git describe --tags
```
**What this does:** adds a changelog line and commits it. Now `git describe --tags` prints
something like `v1.1.0-1-g66fa224`, which reads as **"1 commit after v1.1.0, at commit 66fa224"**
(the `g` stands for git). CI pipelines use this string as a build version: every build is named,
and every name leads back to an exact commit.

```bash
git tag v1.1.0-rc1 HEAD~4
git cat-file -t v1.1.0
git cat-file -t v1.1.0-rc1
git tag -d v1.1.0-rc1
```
**What this does:** makes a **lightweight** tag — just a name, no author, date or message — then
asks Git what each tag really is: `tag` (annotated, a real object) versus `commit` (lightweight, a
bare pointer). Use annotated tags for releases. Then delete the lightweight one.

| Version change | When | Example |
|---|---|---|
| **MAJOR** `2.0.0` | You break something callers rely on | Removing an API field |
| **MINOR** `1.1.0` | You add a feature that breaks nothing | Card fees |
| **PATCH** `1.0.1` | You fix a bug that breaks nothing | The list-limit fix below |

### Step 6.2 — Fix on `main`, then copy the fix to an older release

Risk asks that `/api/v1/authorisations` returns **at most 100** records. Customers still run
1.0, so the fix must reach both lines of development.

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
old = 'request.args.get("limit", 50)), 200)'
assert old in s, "patch did not apply"
p.write_text(s.replace(old, 'request.args.get("limit", 50)), 100)'))
PY
git commit -am "fix(api): list at most 100 authorisations per request"
```
**What this does:** changes the cap from 200 to 100 and commits the fix to `main` — **always fix
the main line first**, so the bug cannot come back in the next release.

```bash
git switch -c release/1.0 v1.0.0
git cherry-pick -x main
git log -1 --format=%B
```
**What this does:**
- `git switch -c release/1.0 v1.0.0` creates a **release branch** starting at the 1.0.0 tag.
- `git cherry-pick -x main` **copies** the latest commit on `main` — the fix — onto this branch.
- `-x` adds `(cherry picked from commit aa6b9be…)` to the message, so auditors can trace the copy
  back to the original.

```bash
git tag -a v1.0.1 -m "PayTrack API 1.0.1 - list limit fix"
git describe --tags
git switch main
```
**What this does:** tags the patch release, confirms it (`v1.0.1`), and returns to `main`.

```bash
git cherry -v main release/1.0
git log --oneline --graph --decorate --simplify-by-decoration main release/1.0
```
**What this does:**
- `git cherry` lists the commits on `release/1.0` that are not on `main`. Its one line starts with
  **`-`**, meaning *"main already has an equivalent change"* — the same fix under a different hash.
  Cherry-pick makes a **copy**, not a link.
- `--simplify-by-decoration` draws only the commits that carry a branch or tag name, so the shape
  is easy to see: two lines of development growing from `v1.0.0` — `main` (with `v1.1.0`) and
  `release/1.0` (with `v1.0.1`).

> 🔑 **This is where branching strategies differ.** Supporting two versions at once, with release
> branches and hot-fixes, is what **GitFlow** is built for. A web service with one live version
> (**GitHub Flow**, which this course uses) rarely needs `release/*` branches at all — you fix
> `main` and deploy.

---

## Part 7 — Merge or rebase, conflicts, and tidying a branch (15 min)

### Step 7.1 — The same branch, merged and rebased

```bash
git switch -c feature/PAY-150-settlement-docs main~2
printf '# Settlement\n\nCard payments settle within 60 seconds.\n' > docs/settlement.md
git add docs/settlement.md && git commit -m "docs: record the settlement timeout"
printf '\nFailed settlements are retried 3 times.\n' >> docs/settlement.md
git commit -am "docs: record settlement retries"
```
**What this does:** starts a feature branch from an **older** `main` (two commits back) and adds
two commits. `main` has moved on since the branch began — exactly the everyday situation.

```bash
git branch try-merge
git branch try-rebase
```
**What this does:** makes two identical copies of the branch so you can try both approaches on
the same starting point.

```bash
git switch try-merge
git merge --no-edit main
git log --oneline --graph -6
```
**What this does:** **merges** `main` into the copy. The graph shows a fork that joins again at
`Merge branch 'main' into try-merge` — a new commit with **two parents**. Your two commits keep
their original hashes.

```bash
git switch try-rebase
git rebase main
git log --oneline --graph -5
git log --oneline -2 feature/PAY-150-settlement-docs
```
**What this does:** **rebases** the other copy: Git lifts your two commits off and replays them
**on top of** the latest `main`. The graph is one straight line with no merge commit. Compare the
hashes with the original branch — **they are different**. The commits were re-created, which is
what "rewriting history" means.

```bash
git diff try-merge try-rebase
```
**What this does:** compares the **files** on the two copies. **It prints nothing: the files are
identical.** Merge and rebase give the same code with a different *history*.

### Step 7.2 — A conflict during a rebase

```bash
git switch main
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Changed: list endpoint returns at most 100 records.\n'))"
git commit -am "docs: note the list limit in the changelog"
git switch -c feature/PAY-151-refund-fees main~1
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Added: refunds pay no card fee.\n'))"
git commit -am "docs: note refund fees in the changelog"
```
**What this does:** `main` and a feature branch **both add a line in the same place** — directly
under `## Unreleased`. This is the most common real conflict there is: two people updating the
changelog.

```bash
git rebase main
```
**What this does:** tries to replay your commit on top of `main`, and **stops**:
```
CONFLICT (content): Merge conflict in CHANGELOG.md
error: could not apply 7873191... docs: note refund fees in the changelog
```

```bash
git status
head -10 CHANGELOG.md
```
**What this does:** `git status` says `You are currently rebasing branch
'feature/PAY-151-refund-fees'` and lists `both modified: CHANGELOG.md`. The file shows:
```
## Unreleased
<<<<<<< HEAD
- Changed: list endpoint returns at most 100 records.
=======
- Added: refunds pay no card fee.
>>>>>>> 7873191 (docs: note refund fees in the changelog)
```

> ⚠️ **During a rebase, the labels are the other way round from a merge.** `HEAD` is **main's**
> line — the branch you are rebasing *onto*. **Your** line is the bottom one, labelled with your
> commit. This catches everyone at least once.

Both lines are right, so keep both. **By hand:** open `nano CHANGELOG.md`, delete the three marker
lines (`<<<<<<<`, `=======`, `>>>>>>>`), save with `Ctrl+O` Enter, exit with `Ctrl+X`. **Or** run:

```bash
grep -v -e '^<<<<<<< ' -e '^=======$' -e '^>>>>>>> ' CHANGELOG.md > CHANGELOG.tmp && mv CHANGELOG.tmp CHANGELOG.md
head -6 CHANGELOG.md
```
**What this does:** writes the file again without the three marker lines — `grep -v` keeps every
line that does **not** match — and shows that both entries are now under `## Unreleased`.

```bash
git add CHANGELOG.md
GIT_EDITOR=true git rebase --continue
git log --oneline -3
```
**What this does:** `git add` tells Git "this file is resolved". `git rebase --continue` finishes
the replay (`Successfully rebased and updated refs/heads/feature/PAY-151-refund-fees`).
`GIT_EDITOR=true` accepts the commit message as it is instead of opening the editor.

> **Changed your mind half-way?** `git rebase --abort` puts the branch back exactly as it was
> before `git rebase` started.

### Step 7.3 — Interactive rebase: tidy your commits before review

```bash
git switch -c feature/PAY-152-fee-guide main
printf '# Refunds\n\nA refund pays no card fee.\n' > docs/refunds.md
git add docs/refunds.md && git commit -m "docs: explain refund fees"
printf '# Receipts\n\nThe fee is printed on every receipt.\n' > docs/receipts.md
git add docs/receipts.md && git commit -m "docs: explain fees on receipts"
```
**What this does:** a branch with two good commits, each adding one page.

```bash
printf 'The original fee is returned with the refund.\n' >> docs/refunds.md
git commit -a --fixup HEAD~1
printf 'It is also shown on the monthly statement.\n' >> docs/receipts.md
git commit -am "wip"
git log --oneline main..
```
**What this does:** two small follow-up changes, the way real work goes.
- `--fixup HEAD~1` creates a commit named `fixup! docs: explain refund fees` — a note saying "this
  belongs inside that earlier commit".
- `wip` is the lazy version: a commit that belongs with `docs: explain fees on receipts`.
- `main..` means "commits on my branch that are not on main". You see four, messy.

```bash
git rebase -i --autosquash main
```
**What this does:** opens the rebase **plan** in your editor, oldest commit first — the
**reverse** of `git log`. Because of `--autosquash`, Git has already moved the `fixup!` commit
under the one it fixes:
```
pick  1f8681d docs: explain refund fees
fixup 88f56c3 fixup! docs: explain refund fees
pick  eee6a47 docs: explain fees on receipts
pick  81c7b68 wip
```
**Change `pick` to `fixup` on the `wip` line**, then save and close (nano: `Ctrl+O`, Enter,
`Ctrl+X`). Your hashes will differ. Git 2.50 and later print a `#` before each message
(`pick 81c7b68 # wip`) — it is only a comment; change the first word the same way.

| Plan word | Does |
|---|---|
| `pick` | Keep the commit as it is |
| `reword` | Keep it, but edit the message |
| `squash` | Meld into the line above and combine the messages |
| `fixup` | Meld into the line above and **drop** this message |
| `drop` | Delete the commit |
| *(move a line)* | Reorder the commits |

```bash
git log --oneline main..
git show --stat --format=%s HEAD
```
**What this does:** four commits became **two**, each one complete: `docs: explain refund fees`
and `docs: explain fees on receipts`. The `--stat` shows the receipts commit now adds all 4 lines
of `docs/receipts.md`, including the "wip" line.

### Step 7.4 — Undo a rebase you regret

```bash
git reset --hard ORIG_HEAD
git log --oneline main..
```
**What this does:** `ORIG_HEAD` is where the branch was before the rebase. Resetting to it
**undoes the whole rebase** in one step — the four messy commits are back.

```bash
git reflog -4
git reset --hard HEAD@{1}
git log --oneline main..
```
**What this does:** the reflog shows `reset: moving to ORIG_HEAD` at `HEAD@{0}` and
`rebase (finish)` at `HEAD@{1}`. Resetting to `HEAD@{1}` **redoes** the tidy version. You have
just undone an undo: **nothing a local rebase does is permanent** while the reflog remembers it.

---

## Part 8 — A shared server: force-pushing safely (15 min)

A branch that only you have is yours to rewrite. The moment a colleague has pulled it, rewriting
it creates work for them — or quietly deletes theirs. Here you play both people.

### Step 8.1 — A "server" and a colleague

```bash
cd ~/devops-course
git clone --bare git-gym git-gym-origin.git
git clone git-gym-origin.git git-gym-colleague
git -C git-gym-colleague config user.name "Ben Okafor"
git -C git-gym-colleague config user.email "ben.okafor@example.com"
```
**What this does:**
- `git clone --bare` makes a copy **with no working files** — only the history. That is what a
  server such as GitHub stores. It plays "GitHub" in this part.
- The second clone is **Ben's laptop**. `git -C <folder>` runs a git command in another folder
  without `cd`-ing into it; the two `config` lines make Ben's commits carry Ben's name.

```bash
cd ~/devops-course/git-gym
git remote add origin ~/devops-course/git-gym-origin.git
git fetch origin
git switch feature/PAY-152-fee-guide
git branch --set-upstream-to=origin/feature/PAY-152-fee-guide
git status -sb
```
**What this does:** connects **your** gym to the "server", downloads its branches, and links
your feature branch to the server's copy. `git status -sb` prints
`## feature/PAY-152-fee-guide...origin/feature/PAY-152-fee-guide` — in step with the server.

### Step 8.2 — `--force-with-lease` saves your colleague's work

Ben adds a page to the shared branch and pushes it:

```bash
cd ~/devops-course/git-gym-colleague
git switch feature/PAY-152-fee-guide
printf '# Chargebacks\n\nA chargeback returns the card fee too.\n' > docs/chargebacks.md
git add docs/chargebacks.md && git commit -m "docs: explain chargeback fees"
git push
```

Meanwhile **you** — who have not fetched — reword your last commit:

```bash
cd ~/devops-course/git-gym
git commit --amend -m "docs: explain fees on receipts and statements"
git push
```
**What this does:** the normal push is **rejected** — `! [rejected] … (fetch first)`. The server
has a commit (Ben's) that you do not have, and a normal push never deletes commits.

```bash
git push --force-with-lease
```
**What this does:** a **careful** force-push: "overwrite the server, but only if it still matches
what I last saw". It does not — Ben pushed since — so it is **rejected**: `(stale info)`. **The
lease just saved Ben's commit.**

```bash
git fetch origin
git push --force-with-lease --force-if-includes
```
**What this does:** `git fetch` updates your picture of the server. That quietly **renews the
lease** — a plain `--force-with-lease` would now succeed and **delete Ben's commit** (we tested
it). Editors that fetch automatically in the background cause exactly this. `--force-if-includes`
adds a second check — "have I actually *seen* the server's latest commit in my own branch?" — and
rejects the push: `(remote ref updated since checkout)`.

```bash
git config --global alias.pushf "push --force-with-lease --force-if-includes"
```
**What this does:** creates a shortcut, so from now on `git pushf` is the only force-push you use.

```bash
git log --oneline --graph HEAD origin/feature/PAY-152-fee-guide -5
git reset --hard origin/feature/PAY-152-fee-guide
git log --oneline main..
```
**What this does:** the graph shows the two versions splitting: your reworded commit on one side,
Ben's `docs: explain chargeback fees` on the other. **The right fix is to stop rewriting a shared
branch.** Your only change was a message, so you drop it and take the server's version. Ben's
commit is now in your log.

> 🔑 **Once someone else has commits on your branch, add new commits. Do not rewrite the old ones.**

### Step 8.3 — What a plain `--force` does

Ben pushes another commit:

```bash
cd ~/devops-course/git-gym-colleague
printf 'A chargeback can arrive up to 120 days later.\n' >> docs/chargebacks.md
git commit -am "docs: chargeback time limit"
git push
```

You rewrite again without fetching, and this time use the blunt tool:

```bash
cd ~/devops-course/git-gym
git commit --amend -m "docs: explain chargeback fees (reviewed)"
git push --force
git log --oneline origin/feature/PAY-152-fee-guide -2
```
**What this does:** `--force` means "make the server match me, no questions asked". It succeeds —
`+ … (forced update)`. The server's log no longer contains `docs: chargeback time limit`. **Ben's
commit is gone from the server**, and nobody was warned.

Ben only gets it back because it is still on his laptop:

```bash
cd ~/devops-course/git-gym-colleague
git fetch
git status -sb
git reset --hard origin/feature/PAY-152-fee-guide
git cherry-pick ORIG_HEAD
git push
git log --oneline -3
```
**What this does:**
- `git fetch` reports `(forced update)`, and `git status -sb` says Ben is `[ahead 2, behind 1]` —
  his copy and the server's have split.
- `git reset --hard origin/…` makes Ben's branch match the server (`ORIG_HEAD` remembers where he
  was).
- `git cherry-pick ORIG_HEAD` copies his lost commit back on top; `git push` puts it on the server
  again.

> ⚠️ **Why not `git pull --rebase`?** After a force-push it treats commits you had *already
> pushed* as the server's history — and can **drop them silently**. We tested it: Ben's commit
> vanished from his laptop too. After a forced update, reset and cherry-pick deliberately, as
> above.

### Step 8.4 — Stop it happening: protect `main` on the server

```bash
git -C ~/devops-course/git-gym-origin.git config receive.denyNonFastForwards true
cd ~/devops-course/git-gym
git switch main
git branch --set-upstream-to=origin/main
git commit --amend -m "docs: note the list limit in the changelog (reworded)"
git push --force origin main
```
**What this does:** switches on a **server-side** rule that rejects any push that would remove
commits, then tries to force-push a rewritten `main`:
```
remote: error: denying non-fast-forward refs/heads/main (you should pull first)
 ! [remote rejected] main -> main (non-fast-forward)
```
Even `--force` cannot get past a rule on the server. On GitHub this is the **"Allow force pushes:
off"** setting you left unticked in Lab 03 Step 2.1; on GitLab it is the **"Allowed to force
push"** switch on a protected branch.

```bash
git reset --hard origin/main
git status -sb
```
**What this does:** throws away the local rewrite so `main` matches the server again:
`## main...origin/main`.

---

## Which command do I need?

| I want to… | Use | Rewrites history? |
|---|---|---|
| Put unfinished work aside | `git stash push -u -m "…"` / `git stash pop` | No |
| Commit only part of my changes | `git add -p` | No |
| Fix my last, **unpushed** commit | `git commit --amend` | Yes |
| Throw away an uncommitted edit | `git restore <file>` | No — but the edit is gone |
| Undo my last commits, **unpushed** | `git reset --soft / --mixed / --hard` | Yes |
| Undo a commit that is **already pushed** | `git revert <sha>` | **No** |
| Find a "lost" commit | `git reflog`, then `git branch <name> <sha>` | No |
| Find which commit broke something | `git bisect start <bad> <good>` + `git bisect run <check>` | No |
| Copy one commit to another branch | `git cherry-pick -x <sha>` | No |
| Name a release | `git tag -a v1.2.0 -m "…"` | No |
| Tidy my branch before review | `git commit --fixup <sha>` + `git rebase -i --autosquash main` | Yes |
| Undo a rebase | `git reset --hard ORIG_HEAD` | Yes |
| Push a branch I have rewritten | `git push --force-with-lease --force-if-includes` | Yes — only if nobody else uses the branch |
| Delete build clutter | `git clean -n`, then `git clean -fd` | No — but untracked files are gone for good |

The full reference, with real output for every command:
[`docs/theory/git-command-guide.md`](../../docs/theory/git-command-guide.md).

---

## 🧩 Stretch (homework)

1. **`git rerere`.** `git config --global rerere.enabled true`, repeat Step 7.2 on a fresh branch,
   abort, and rebase again. Git remembers how you resolved the conflict and does it for you.
2. **`git worktree`.** `git worktree add ../gym-hotfix release/1.0` checks out a second branch in
   a second folder, so a hot-fix never needs `git stash`.
3. **Bisect by hand.** Rebuild the gym and find the bug with `git bisect good` / `git bisect bad`
   instead of `run`. Count the steps.
4. **Sign a tag.** `git config --global gpg.format ssh`,
   `git config --global user.signingkey ~/.ssh/id_ed25519.pub`, then `git tag -s v1.2.0 -m "…"`.
   Verify it with `git tag -v v1.2.0` after setting up an allowed-signers file.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `setup-gym.sh: Set your git identity first` | No `user.email` configured | Lab 00 Step 6 |
| An editor opens and you do not know how to leave | Git asked for a message or a plan | nano: `Ctrl+O` Enter `Ctrl+X`. vim: `Esc`, then `:wq` Enter |
| `You are in 'detached HEAD' state` | You switched to a tag or a hash, not a branch | `git switch main` |
| `git stash pop` reports a conflict | You popped onto a different commit | The stash is kept: `git reset --hard`, switch back, pop again |
| `could not apply …` during a rebase | A conflict | Fix the file, `git add`, `git rebase --continue` — or `git rebase --abort` |
| `fatal: It seems that there is already a rebase-merge directory` | A rebase is still in progress | `git rebase --continue` or `git rebase --abort` |
| Bisect names the wrong commit | The check fails for another reason on some commits (e.g. a missing file) | Make the check `exit 125` on commits it cannot test — bisect skips those |
| `! [rejected] … (stale info)` | The server changed since you last fetched | That is the lease working — fetch and look before you force anything |
| Anything else | The gym is in a state you do not understand | Run the RECOVER block — two seconds |

---

## 🎯 Outcome

You have used every command from the Going Further Git slides and seen the output of each: stash,
patch staging, amend, restore, the three resets, reflog rescue, bisect, revert, clean, annotated
and lightweight tags, `describe`, a release branch with a cherry-picked hot-fix, merge versus
rebase on the same branch, a rebase conflict, interactive rebase with autosquash, undoing a
rebase, and a lease that saved a colleague's commit.

**Next:** [Lab 04 — GitHub Actions CI](../lab-04-github-actions-ci/README.md), or
[Lab 04A — Run CI on your laptop with act](../lab-04a-act-and-pipeline-security/README.md) once
Lab 04 is done.

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **This lab is optional and self-paced.** It needs no network, no GitHub and no Docker, so it is
  the one lab that works on a train. Point delegates who finish Lab 03 early at Parts 3–5.
- **Parts 5 and 8 are the memorable ones.** If you demo one thing from the front, demo
  `git bisect run` finding Ben's "simplification" in three steps, then Step 8.2's
  `(stale info)` rejection.
- **Things that go wrong:**
  1. The editor. Half the room has never left nano or vim. Put the key sequences on the screen
     before Step 7.3.
  2. Step 7.3: people change the wrong line to `fixup` because the plan is oldest-first. Step 7.4
     is the fix — let them discover it.
  3. Someone runs a command in `paytrack-api-team` instead of the gym. `pwd` before Part 4.
- **Debrief question:** "Which of today's commands would you allow on `main` in your organisation,
  and which should the server refuse? Where is that rule written down today?"
</details>
