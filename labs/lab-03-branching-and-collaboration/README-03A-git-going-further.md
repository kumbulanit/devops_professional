# Lab 03A — Git, Going Further: Undo, Rescue, Rewrite and Release

| | |
|---|---|
| **Day** | 2 — **optional**, after class or as homework |
| **Duration** | About 80 minutes, in eight parts you can do on different evenings |
| **Module** | 2 — Version Control and CI (the *Going Further* slides, sections B and C) |
| **Slides** | `Lab03A_Advanced_Git.pptx` — in this folder, 32 slides, read it first |
| **Parent lab** | [Lab 03 — Branching, Pull Requests and Team Collaboration](README.md) |
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

---

## Before you start — how to run the commands in this lab

**You do not need to know Linux.** Every instruction below is **one command in one grey box**.
Do them in order, one at a time. Here is everything you need to know about the terminal:

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. (Or press the ⊞ key, type `terminal`, press `Enter`.) |
| **What am I looking at?** | A line ending in `$`, called the **prompt**. It is waiting for you to type. |
| **How do I run a command?** | Click into the terminal window, type or paste the contents of one box, press `Enter`. |
| **How do I paste?** | Copy from this page with `Ctrl` + `C`. Paste into the terminal with **`Ctrl` + `Shift` + `V`** — in a terminal, plain `Ctrl` + `V` does nothing. |
| **When is it finished?** | When the `$` prompt comes back. **Wait for it** before running the next box. |
| **Nothing was printed!** | Normal. Many commands print nothing when they succeed — in Linux, silence means "done". |
| **The screen filled up and the bottom shows `:` or `(END)`** | You are in a **pager** (a scrollable view). Press `q` to come back to the prompt. Arrow keys scroll. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel and get the prompt back. |
| **An editor opened and I am trapped** | You are in **nano**. Save and leave with `Ctrl` + `O`, then `Enter`, then `Ctrl` + `X`. |
| **I typed it wrong** | Nothing is lost. Press `Enter`, read the error, type it again. Upper and lower case matter, and so do spaces. |

**Reading the boxes.** Each box holds **one command**. These symbols appear in them:

| Symbol | Say it as | Means |
|---|---|---|
| `~` | "tilde" | Your home folder — `/home/<your-name>`. So `~/devops-course` is the folder `devops-course` inside your home folder |
| `cd` | "see-dee" | **C**hange **D**irectory: move into a folder. Everything you type afterwards happens *in that folder* |
| `>` | "into" | Send what the command prints **into a file**, replacing whatever was there |
| `>>` | "onto the end of" | Send what the command prints **onto the end of a file**, keeping what was there |
| `\|` | "pipe" | Send the first command's output into the second command |
| `$(…)` | — | Run the command in the brackets first, and use its answer here |
| `"$NAME"` | — | The value you stored earlier under the name `NAME` |
| `#` | "hash" | A comment for humans; the computer ignores the rest of the line |

Three more things about this lab in particular:

1. **Some commands fail on purpose.** Each one says so *before* the box. A red error where we
   predicted one means you are on track — do not "fix" it.
2. **Stay in one terminal window.** A few steps remember an answer (`GOOD=…`) for later steps; a
   new window would forget it.
3. **You cannot break anything.** If the gym gets into a state you do not understand, run the two
   RECOVER commands below and start the part again.

🔁 **RECOVER / START AGAIN** — at any point, from anywhere:

```bash
cd ~/devops-course/course-material && git pull --ff-only
```
**What this does:** moves into the folder holding the course material and downloads any update to
it. If this prints an error, ignore it — the rest works with the copy you already have.

```bash
bash ~/devops-course/course-material/labs/lab-03-branching-and-collaboration/setup-gym.sh
```
**What this does:** `bash <file>` means "run the list of commands in this file". This particular
file deletes and rebuilds the gym — including the `git-gym-origin.git` and `git-gym-colleague`
folders that Part 8 creates. Nothing outside the gym is touched.

## Words you need

| Word | Plain meaning |
|---|---|
| **Repository (repo)** | A folder whose contents git is keeping the history of |
| **Commit** | One saved version of the whole project, with a message saying why |
| **Branch** | A moving label on a line of commits — the name of one line of work |
| **HEAD** | "Where I am now" — normally the latest commit of the branch you are on |
| **Detached HEAD** | You are looking at an old commit directly, not at a branch. Fine for looking; do not commit here |
| **Hunk** | One block of changed lines inside a file |
| **Reflog** | Your clone's private diary of every place HEAD has been. Nothing you commit is lost while it is in the reflog |
| **ORIG_HEAD** | Where the branch was just before the last big move (reset, rebase, merge) |
| **Remote** | Another copy of the repository, usually on a server, that yours can talk to |
| **Upstream** | The branch on the server that your local branch pushes to and pulls from |
| **Lease** | "Only overwrite the server if it still looks the way I last saw it" |

---

## Part 1 — Build the gym (5 min)

**1. Build the practice repository.**

```bash
bash ~/devops-course/course-material/labs/lab-03-branching-and-collaboration/setup-gym.sh
```
**What this does:** runs a script that copies the PayTrack API app into `~/devops-course/git-gym`
and makes **ten commits as four different people** (you, Ana, Ben and Chen), spread over the last
ten days. It tags the first commit `v1.0.0`. Read the script if you are curious — but try not to
look for the bug yet.

**2. Move into the gym.**

```bash
cd ~/devops-course/git-gym
```
**What this does:** makes the gym your **current folder**, so every git command from now on works
on the gym and not on your real project.

**3. Check you are in the right place.**

```bash
pwd
```
**What this does:** **p**rint **w**orking **d**irectory — shows which folder you are in. It must
end with `/devops-course/git-gym`. If it does not, run command 2 again.

✅ **Checkpoint** — the setup script ended by printing ten commits, newest first (your hashes —
the short codes at the start of each line — will be different from these):
```
23cf3fc (HEAD -> main) chore: bump version to 1.1.0
22e794b docs: record card fees in the changelog
...
f80abaf feat(fees): add the card fee calculator
dc28ee8 (tag: v1.0.0) feat: add PayTrack API service
```

---

## Part 2 — Read the history like a detective (5 min)

Seven commands, each answering a different question about the past. Run them one at a time.

**1. Draw the whole history.**

```bash
git log --oneline --graph --decorate --all
```
**What this does:** one line per commit (`--oneline`), a drawing of the branches down the left
(`--graph`), branch and tag names (`--decorate`), for every branch (`--all`). This is the command
you will type most often in this lab. If the output fills the screen, press `q` to return to the
prompt.

**2. Ask who wrote what, and when.**

```bash
git log --format='%h  %<(11)%an %<(12)%ar %s'
```
**What this does:** a custom layout — short hash (`%h`), author name padded to 11 characters
(`%<(11)%an`), how long ago (`%ar`) and the message (`%s`). You should see Ana, Ben and Chen, with
dates from "10 days ago" to "24 hours ago". The single quotes keep the whole recipe together as
one piece of text.

**3. Look inside one commit.**

```bash
git show --stat HEAD~3
```
**What this does:** shows one commit — who, when, the message and which files changed (`--stat`).
`HEAD~3` means "three commits before where I am"; `HEAD~1` would be the one just before this.

**4. Find when a setting first appeared.**

```bash
git log --oneline -S MIN_FEE_MINOR
```
**What this does:** the **pickaxe**. `-S <text>` finds the commits that *added or removed* that
text anywhere in the project. Expect exactly one: `feat(fees): add a minimum fee of 5 cents`. This
is how you answer "when did this appear?" in a repository with ten thousand commits.

**5. Read the history of one file.**

```bash
git log --oneline -- docs/fees.md
```
**What this does:** shows only the commits that touched `docs/fees.md`. Everything after the two
dashes (`--`) is a **file path**, not an option — the dashes exist so git cannot confuse a file
called `main` with the branch called `main`.

**6. Read the history of one person.**

```bash
git log --oneline --author=Ben
```
**What this does:** shows only Ben's commits. Filters combine: `git log --author=Ben -- docs/fees.md`
would show only Ben's commits that touched that file.

**7. Ask who last changed each line.**

```bash
git blame -L 1,5 app/src/fees.py
```
**What this does:** for lines 1 to 5 of the file (`-L 1,5`), shows **who last changed each line, in
which commit, and when**. Lines 1–3 come from Ana; line 4 (`MIN_FEE_MINOR`) from Chen. "Blame" is
an unkind name for a useful command: it tells you whom to *ask*.

---

## Part 3 — Put work aside, and save only part of it (10 min)

### Step 3.1 — `git stash`: an urgent interruption

You are halfway through a change when someone asks, "What version did 1.0.0 report?"

**1. Start an unfinished edit in a file git already tracks.**

```bash
printf '\nFees are shown on every receipt.\n' >> docs/fees.md
```
**What this does:** `printf` prints a piece of text; `>>` sends it **onto the end of** the file
instead of onto your screen. `\n` means "start a new line here". Nothing appears on screen — the
text went into the file.

**2. Create a brand-new file git has never seen.**

```bash
printf 'Ask Risk whether refunds pay a fee.\n' > notes.txt
```
**What this does:** the same, but a single `>` **creates or replaces** the file. `notes.txt` did
not exist, so it is created.

**3. Ask git what changed.**

```bash
git status -s
```
**What this does:** the short (`-s`) summary. Two lines:
- ` M docs/fees.md` — **M**odified: a file git tracks has changed.
- `?? notes.txt` — **untracked**: git can see this file but is not looking after it.

**4. Try to go and look at the old release. This fails on purpose.**

```bash
git switch --detach v1.0.0
```
**What this does:** tries to show you the project as it was at the `v1.0.0` tag. **It refuses:**
`error: Your local changes to the following files would be overwritten by checkout`. Git will not
throw your unfinished edit away. You need somewhere to put it.

**5. Put the unfinished work on a shelf.**

```bash
git stash push --include-untracked -m "wip: receipts paragraph and notes"
```
**What this does:** `stash push` takes every uncommitted change off your files and stores it on a
shelf, leaving the folder clean. `--include-untracked` shelves the **new** file as well — without
it, `notes.txt` would be left behind. `-m "…"` is a label so you know later what is on the shelf.

**6. Confirm the folder is clean now.**

```bash
git status -s
```
**What this does:** prints **nothing at all**. Nothing is modified, nothing is new: exactly the
state git wanted before letting you move.

**7. Look at what is on the shelf.**

```bash
git stash list
```
**What this does:** lists your shelves, newest first:
`stash@{0}: On main: wip: receipts paragraph and notes`. `stash@{0}` is its address.

**8. Now the move works.**

```bash
git switch --detach v1.0.0
```
**What this does:** switches your files to the `v1.0.0` commit and prints `HEAD is now at …
feat: add PayTrack API service`. "Detached" means you are looking at a commit directly rather than
standing on a branch — fine for reading, but do not make commits here.

**9. Read the answer you were asked for.**

```bash
grep -n APP_VERSION app/src/config.py
```
**What this does:** `grep` searches inside a file for a piece of text and prints the lines that
contain it; `-n` adds line numbers. You get `"APP_VERSION", "1.0.0"` — the answer.

**10. Go back to your branch.**

```bash
git switch main
```
**What this does:** puts your files back to the latest `main` and attaches you to that branch
again.

**11. Take the work back off the shelf.**

```bash
git stash pop
```
**What this does:** restores the shelved changes into your files and removes the shelf entry —
you see `Dropped refs/stash@{0}`.

**12. Check both changes came back.**

```bash
git status -s
```
**What this does:** ` M docs/fees.md` and `?? notes.txt` are both listed again, exactly as in
command 3.

> ⚠️ **Pop on the branch you stashed from.** Popping onto a different commit can conflict — for
> example if the file does not exist there. If that happens the stash is **kept**, so nothing is
> lost: run `git reset --hard`, switch back to the right branch, and pop again.

**13. Delete the new file.**

```bash
rm notes.txt
```
**What this does:** `rm` **r**e**m**oves a file. There is no recycle bin: `notes.txt` is gone. That
is safe here because git never tracked it and you do not need it.

**14. Undo the edit to the tracked file.**

```bash
git restore docs/fees.md
```
**What this does:** puts the file back to its last committed state. **The edit is gone for good** —
this command is for changes you are sure you do not want.

### Step 3.2 — `git add -p`: commit part of a file

**1. Make two unrelated edits in the same file.**

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
```
**What this does:** this whole box is **one command** — copy all of it, including the last `PY`
line, and press `Enter` once. `python3 - <<'PY'` means "run the Python program that follows, up to
the line that says `PY`". The program changes a word near the top of the page and adds an example
row at the bottom. We use Python instead of an editor so that everyone's file ends up identical.

**2. Confirm one file changed.**

```bash
git diff --stat
```
**What this does:** `git diff` shows changes you have not staged yet; `--stat` summarises them as
one line per file: `docs/fees.md | 3 ++-`.

**3. Choose which of the two edits to commit.**

```bash
git add -p docs/fees.md
```
**What this does:** **p**atch mode. Git shows each changed block (**hunk**) in turn and asks
`Stage this hunk [y,n,q,a,d,…]?`
- For the **first** hunk (the `small fee` wording) press **`y`** then `Enter` — stage it.
- For the **second** hunk (the `45.99` row) press **`n`** then `Enter` — leave it for later.

**4. See the half-and-half state.**

```bash
git status -s
```
**What this does:** prints `MM docs/fees.md`. The **first** `M` means "some changes are staged,
ready to commit"; the **second** means "some changes are still only in the file".

**5. Commit the staged half — with a typo in the message, on purpose.**

```bash
git commit -m "docs: say the fee is smal"
```
**What this does:** saves **only the staged hunk** as a commit. `-m` supplies the message so no
editor opens. Note the missing "l" — you fix it next.

### Step 3.3 — `git commit --amend`: fix the commit you just made

**1. Replace the last commit.**

```bash
git commit --amend -m "docs: say the fee is small"
```
**What this does:** `--amend` **replaces** the previous commit with a new one — same changes,
corrected message, and a **new hash**, because a commit's message is part of what makes its
identity.

**2. Prove there is only one commit, not two.**

```bash
git log --oneline -2
```
**What this does:** `-2` shows the two newest commits. The top one reads
`docs: say the fee is small`; the typo version has been replaced, not added to.

⚠️ Only amend a commit you have **not pushed**. Part 8 shows what happens to the people who had
already pulled it.

**3. Look at what is still uncommitted.**

```bash
git diff
```
**What this does:** shows the change you left behind in Step 3.2 — the `45.99` row, marked with a
`+` because it is an added line. Press `q` if a pager opens.

**4. Commit the rest.**

```bash
git commit -am "docs: add a rounding example"
```
**What this does:** `-a` stages every **tracked** file that changed and `-m` gives the message, so
one command does the work of `git add` plus `git commit`. (`-a` never picks up brand-new files —
those still need `git add`.) One messy editing session has become two clean commits, each with a
single purpose.

---

## Part 4 — Undo: restore, reset, reflog (10 min)

### Step 4.1 — `git restore`: undo an edit you have not committed

**1. Make a deliberately bad edit.**

```bash
echo 'FEE_BPS = 9999' >> app/src/fees.py
```
**What this does:** `echo` prints a line of text, and `>>` adds it to the end of the source file —
a fee rate 66 times too high.

**2. See that git noticed.**

```bash
git status -s
```
**What this does:** prints ` M app/src/fees.py`.

**3. Throw the edit away.**

```bash
git restore app/src/fees.py
```
**What this does:** rewrites the file from the last commit. The bad line is gone.

**4. Confirm.**

```bash
git status -s
```
**What this does:** prints nothing — the folder matches the last commit again.

### Step 4.2 — `git reset`: move the branch back, three ways

First, make a commit to experiment with.

**1. Change the fee rate.**

```bash
python3 -c "import pathlib; p=pathlib.Path('app/src/fees.py'); p.write_text(p.read_text().replace('FEE_BPS = 150', 'FEE_BPS = 200'))"
```
**What this does:** `python3 -c "…"` runs the short Python program inside the quotes: it reads the
file, swaps `150` for `200` (a fee of 2% instead of 1.5%) and writes it back.

**2. Commit it.**

```bash
git commit -am "experiment: try a 2% fee"
```
**What this does:** stages the modified file and commits it, as in Step 3.3.

**3. See it at the top of the history.**

```bash
git log --oneline -2
```
**What this does:** your experiment is now the newest commit.

Now undo that commit three different ways.

**4. Undo it, keeping the change staged.**

```bash
git reset --soft HEAD~1
```
**What this does:** moves the branch label back one commit (`HEAD~1`) but leaves the change
**staged**, ready to commit again. Use this when you want to redo a commit — split it, or add a
file you forgot.

**5. Look at the result.**

```bash
git status -s
```
**What this does:** prints `M  app/src/fees.py` — the `M` is in the **first** column, meaning
staged.

**6. Commit it again so you can undo it a second way.**

```bash
git commit -m "experiment: try a 2% fee"
```
**What this does:** re-creates the commit from what is already staged.

**7. Undo it, keeping the change but unstaged.**

```bash
git reset HEAD~1
```
**What this does:** `reset` with no option is `--mixed`, the default: the commit is undone and the
change stays in your files but is **no longer staged**.

**8. Look at the result.**

```bash
git status -s
```
**What this does:** prints ` M app/src/fees.py` — the `M` has moved to the **second** column.

**9. Commit a third time.**

```bash
git commit -am "experiment: try a 2% fee"
```
**What this does:** stages and commits the change again.

**10. Undo it and delete the work.**

```bash
git reset --hard HEAD~1
```
**What this does:** moves the branch back **and overwrites your files** to match. The commit is
undone and the change is deleted. This is the dangerous one.

**11. Confirm nothing is left.**

```bash
git status -s
```
**What this does:** prints nothing.

**12. Confirm the file really went back.**

```bash
grep -n 'FEE_BPS =' app/src/fees.py
```
**What this does:** searches the file for that text: it says `FEE_BPS = 150` again. The 2% version
is nowhere in your files.

| | The commit | Staged? | Your files |
|---|---|---|---|
| `git reset --soft HEAD~1` | undone | ✔ still staged | kept |
| `git reset HEAD~1` (mixed) | undone | ✘ unstaged | kept |
| `git reset --hard HEAD~1` | undone | ✘ | **deleted** |

### Step 4.3 — `git reflog`: get the "deleted" commit back

**1. Open your clone's diary.**

```bash
git reflog -6
```
**What this does:** prints the last six places `HEAD` has been, newest first:
```
6feb74f HEAD@{0}: reset: moving to HEAD~1
85c99d4 HEAD@{1}: commit: experiment: try a 2% fee
...
```
`HEAD@{1}` means "where HEAD was one move ago" — the commit `--hard` supposedly destroyed.
**It still exists**, it just has no label pointing at it.

**2. Put a label on the "lost" commit.**

```bash
git branch experiment/two-percent HEAD@{1}
```
**What this does:** `git branch <name> <where>` creates a branch label at that commit without
switching to it. The commit is now safe: anything with a label is never cleaned up.

**3. Read a file from inside that commit.**

```bash
git show experiment/two-percent:app/src/fees.py | grep "FEE_BPS ="
```
**What this does:** `<branch>:<file>` reads a file *as it is in that commit*, without switching
branches. The `|` (pipe) passes that file into `grep`, which prints only the matching line:
`FEE_BPS = 200`. Rescued.

**4. Delete the label again.**

```bash
git branch -D experiment/two-percent
```
**What this does:** `-D` force-deletes the branch label. Git prints
`Deleted branch experiment/two-percent (was 85c99d4).` — **write that hash down**; it is your way
back.

**5. Re-create it from the diary.**

```bash
git branch experiment/two-percent HEAD@{1}
```
**What this does:** creates the label again. `git branch <name> <hash>` using the hash from the
"(was …)" message works just as well. **Deleting a branch deletes the label, not the commits.**

**6. List your branches.**

```bash
git branch
```
**What this does:** lists every branch; `*` marks the one you are on. `experiment/two-percent` is
back. Press `q` if a pager opens.

**7. Tidy up.**

```bash
git branch -D experiment/two-percent
```
**What this does:** deletes the experiment for the last time. You do not need it again.

> 🔑 The reflog is **local** and **temporary** — it lives only in your clone and entries expire
> after about 90 days. It cannot rescue a change that was never committed at all.

---

## Part 5 — Find the bug with `git bisect`, fix it with `git revert` (10 min)

### Step 5.1 — The symptom

**1. Run the card-fee checks.**

```bash
python3 app/tests/check_fees.py
```
**What this does:** runs a small program that checks the fee maths. **It fails:**
`AssertionError: expected 68, got 69: a fee was rounded UP`. The bank's rule is that fees round
*down*. Somewhere in the last ten days something changed that. Which commit?

### Step 5.2 — Find a commit you know was good

**1. Find where the calculator was first written.**

```bash
git log --oneline -S "def card_fee"
```
**What this does:** the pickaxe again — the commit that added the words `def card_fee`, which is
the moment the function was created. It passed review with its check green, so it is **known
good**.

**2. Store that commit's hash under a name.**

```bash
GOOD=$(git log --format=%h -S "def card_fee")
```
**What this does:** runs the command inside `$(…)` and keeps its answer in a **variable** called
`GOOD`, so you never have to retype the hash. Nothing is printed. The name lasts until you close
this terminal window.

**3. Check what you stored.**

```bash
echo "$GOOD"
```
**What this does:** prints the value — a seven-character hash such as `f80abaf`. If it is empty,
run command 2 again in this same window.

### Step 5.3 — Let Git search for you

**1. Start the search.**

```bash
git bisect start HEAD "$GOOD"
```
**What this does:** tells git "this commit (`HEAD`, now) is **bad**, and that one is **good** —
find the first bad one between them". Git jumps your files to the commit halfway between and
prints `Bisecting: 4 revisions left to test after this (roughly 2 steps)`.

**2. Let git test each candidate for you.**

```bash
git bisect run python3 app/tests/check_fees.py
```
**What this does:** runs the check on each commit git picks. **Exit code 0 means good; anything
else means bad** — that is how a program tells the system whether it succeeded. Git halves the
range after every answer and, in about three runs, prints:
```
8ccacf5… is the first bad commit
commit 8ccacf5…
Author: Ben Okafor <ben.okafor@example.com>
    refactor(fees): simplify the fee maths
```
Ten commits would take ten checks by hand; bisect needed three. A thousand commits need ten.

**3. Save the culprit's hash before the labels disappear.**

```bash
BAD=$(git rev-parse --short refs/bisect/bad)
```
**What this does:** `git rev-parse` turns a name into a hash; `--short` shortens it. The answer
goes into a variable called `BAD`. Nothing is printed. Do this **before** the next command, which
removes bisect's temporary labels.

**4. Leave bisect mode.**

```bash
git bisect reset
```
**What this does:** puts your files back to `main` and clears the search. Always run this when you
are finished; otherwise you are left in a detached HEAD.

**5. Look at the bad commit.**

```bash
git show "$BAD"
```
**What this does:** shows the culprit. There it is: `// 10_000` (whole-number division, which
rounds down) became `round(… / 10_000)` (which rounds to the *nearest*). A "simplification" that
changed a banking rule. Press `q` to leave the pager.

> **Doing it by hand.** Without a script: `git bisect start`, then type `git bisect bad` or
> `git bisect good` yourself after testing each commit git checks out, until it names the culprit.

### Step 5.4 — Undo it safely with `git revert`

**1. Create an "opposite" commit.**

```bash
git revert --no-edit "$BAD"
```
**What this does:** makes a **new** commit called `Revert "refactor(fees): simplify the fee maths"`
that does the exact opposite of the bad one. Nothing already in history is changed, which is why
this is safe on a branch other people have pulled. `--no-edit` accepts git's suggested message
instead of opening an editor.

**2. Prove the bug is gone.**

```bash
python3 app/tests/check_fees.py
```
**What this does:** prints `fee checks passed`.

**3. See both commits in the history.**

```bash
git log --oneline -3
```
**What this does:** the bad commit is still there, and the revert sits above it. The record is
honest: it shows the mistake *and* the fix.

| Undo with… | What happens to history | Safe after pushing? |
|---|---|---|
| `git revert` | Adds a new "opposite" commit | ✔ **Yes** |
| `git reset` | Moves the branch back; later commits disappear from it | ✘ Only on unpushed work |

### Step 5.5 — `git clean`: delete files Git does not track

**1. Make a folder the way a build would.**

```bash
mkdir -p build
```
**What this does:** `mkdir` **m**a**k**es a **dir**ectory (a folder). `-p` means "and do not
complain if it already exists".

**2. Put a pretend build artefact in it.**

```bash
echo 'pretend artefact' > build/paytrack.tar.gz
```
**What this does:** creates a file inside that folder containing one line of text.

**3. Drop a scratch file in the project root.**

```bash
echo 'scratch' > scratch.txt
```
**What this does:** the sort of file everyone leaves lying around.

**4. Make the folder Python creates for itself.**

```bash
mkdir -p app/src/__pycache__
```
**What this does:** creates the cache folder Python normally generates when it runs your code.

**5. Put a file in it.**

```bash
echo x > app/src/__pycache__/fees.cpython-312.pyc
```
**What this does:** creates a stand-in for a compiled Python file.

**6. Ask git what it can see.**

```bash
git status -s
```
**What this does:** lists `?? build/` and `?? scratch.txt` — but **not** `__pycache__/`, because
the project's `.gitignore` file tells git to ignore it.

**7. Ask what a clean-up *would* delete — files only.**

```bash
git clean -n
```
**What this does:** **`-n` is a dry run**: it only prints what *would* be removed and deletes
nothing. You see `Would remove scratch.txt`. Always do this first.

**8. Ask again, including folders.**

```bash
git clean -nd
```
**What this does:** `-d` adds folders, so `build/` appears too.

**9. Ask what would go if ignored files were included.**

```bash
git clean -ndX
```
**What this does:** a capital `-X` means "**only** the files listed in `.gitignore`". You see
`Would remove app/src/__pycache__/`.

**10. Actually delete the clutter.**

```bash
git clean -fd
```
**What this does:** `-f` (**f**orce) does what command 8 previewed — `build/` and `scratch.txt` are
removed. Git insists on `-f` so that you cannot delete files by accident.

**11. Show that ignored files survived.**

```bash
git status -s --ignored
```
**What this does:** `--ignored` also lists ignored entries, marked `!!`. `!! app/src/__pycache__/`
is still there, untouched.

> 🔴 **`git clean -fdx` (lower-case x) deletes untracked *and ignored* files** — which includes
> your `.venv/` folder, your `.env` file with its passwords, and any local database. There is no
> undo: these files were never committed, so not even the reflog knows about them. Dry-run with
> `-n` first, every time.

---

## Part 6 — Releases: tags, versions and hot-fixes (10 min)

### Step 6.1 — Tag a release, and let Git describe any commit

**1. Name this commit as release 1.1.0.**

```bash
git tag -a v1.1.0 -m "PayTrack API 1.1.0 - card fees"
```
**What this does:** creates an **annotated** tag — a permanent name for one commit that also
records who tagged it, when and why. `-a` makes it annotated; `-m` gives the message.

**2. Ask git where you are relative to the nearest tag.**

```bash
git describe --tags
```
**What this does:** prints `v1.1.0` — this commit *is* the release.

**3. Add a changelog line.**

```bash
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Fixed: card fees round down again.\n'))"
```
**What this does:** inserts a line directly under the `## Unreleased` heading of `CHANGELOG.md`.

**4. Commit it.**

```bash
git commit -am "docs: note the rounding fix in the changelog"
```
**What this does:** stages the changed file and commits it, so you are now one commit past the tag.

**5. Ask again.**

```bash
git describe --tags
```
**What this does:** now prints something like `v1.1.0-1-g66fa224`, which reads as **"1 commit after
v1.1.0, at commit 66fa224"** (the `g` just stands for git). CI pipelines use this string as a build
version: every build has a name, and every name leads back to one exact commit.

**6. Make a second, simpler kind of tag.**

```bash
git tag v1.1.0-rc1 HEAD~4
```
**What this does:** without `-a`, you get a **lightweight** tag — just a name pinned to a commit,
with no author, date or message. Here it is placed four commits back.

**7. Ask git what the first tag really is.**

```bash
git cat-file -t v1.1.0
```
**What this does:** `-t` asks for the **t**ype of the thing behind a name. The answer, `tag`, means
a real object with its own author and message.

**8. Ask about the second.**

```bash
git cat-file -t v1.1.0-rc1
```
**What this does:** the answer is `commit` — the lightweight tag is only a pointer, with nothing
recorded about who made it. Use annotated tags for anything you release.

**9. Delete the lightweight tag.**

```bash
git tag -d v1.1.0-rc1
```
**What this does:** removes that tag. `-d` is for **d**elete.

| Version change | When | Example |
|---|---|---|
| **MAJOR** `2.0.0` | You break something callers rely on | Removing an API field |
| **MINOR** `1.1.0` | You add a feature that breaks nothing | Card fees |
| **PATCH** `1.0.1` | You fix a bug that breaks nothing | The list-limit fix below |

### Step 6.2 — Fix on `main`, then copy the fix to an older release

Risk asks that `/api/v1/authorisations` returns **at most 100** records. Customers still run
1.0, so the fix must reach both lines of development.

**1. Change the limit in the code.**

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
old = 'request.args.get("limit", 50)), 200)'
assert old in s, "patch did not apply"
p.write_text(s.replace(old, 'request.args.get("limit", 50)), 100)'))
PY
```
**What this does:** one command again — copy the whole box including the final `PY`. It lowers the
cap from 200 to 100. The `assert` line makes the program stop with an error if the text it expects
is missing, rather than silently doing nothing.

**2. Commit the fix to `main`.**

```bash
git commit -am "fix(api): list at most 100 authorisations per request"
```
**What this does:** commits the change. **Always fix the main line first**, so the bug cannot come
back in the next release.

**3. Create a branch for the old release.**

```bash
git switch -c release/1.0 v1.0.0
```
**What this does:** `-c` **c**reates a branch and switches to it. Starting it at `v1.0.0` means
this branch contains version 1.0 exactly as it shipped.

**4. Copy the fix onto it.**

```bash
git cherry-pick -x main
```
**What this does:** **copies** the newest commit of `main` — your fix — onto this branch, leaving
everything else on `main` behind. `-x` adds a line recording where the copy came from.

**5. Read the copied commit's message.**

```bash
git log -1 --format=%B
```
**What this does:** prints the newest commit's full message (`%B`), which now ends with
`(cherry picked from commit aa6b9be…)` — so an auditor can trace the copy back to the original.

**6. Tag the patch release.**

```bash
git tag -a v1.0.1 -m "PayTrack API 1.0.1 - list limit fix"
```
**What this does:** names this commit 1.0.1 — same features as 1.0.0, one bug fixed.

**7. Confirm.**

```bash
git describe --tags
```
**What this does:** prints `v1.0.1`.

**8. Go back to the main line.**

```bash
git switch main
```
**What this does:** leaves the release branch. It stays where it is, ready for the next hot-fix.

**9. Ask which commits are only on the release branch.**

```bash
git cherry -v main release/1.0
```
**What this does:** compares the two branches by *content*. Its one line starts with **`-`**,
meaning *"main already has an equivalent change"* — the same fix, under a different hash. A
cherry-pick makes a **copy**, not a link.

**10. Draw the two lines of development.**

```bash
git log --oneline --graph --decorate --simplify-by-decoration main release/1.0
```
**What this does:** `--simplify-by-decoration` draws only the commits that carry a branch or tag
name, so the shape is easy to see: two lines growing out of `v1.0.0` — `main` (with `v1.1.0`) and
`release/1.0` (with `v1.0.1`).

> 🔑 **This is where branching strategies differ.** Supporting two versions at once, with release
> branches and hot-fixes, is what **GitFlow** is built for. A web service with one live version
> (**GitHub Flow**, which this course uses) rarely needs `release/*` branches at all — you fix
> `main` and deploy.

---

## Part 7 — Merge or rebase, conflicts, and tidying a branch (15 min)

### Step 7.1 — The same branch, merged and rebased

**1. Start a feature branch from an older point in history.**

```bash
git switch -c feature/PAY-150-settlement-docs main~2
```
**What this does:** creates the branch two commits back (`main~2`), which puts you in the everyday
situation where `main` has moved on since your branch began.

**2. Write a new page.**

```bash
printf '# Settlement\n\nCard payments settle within 60 seconds.\n' > docs/settlement.md
```
**What this does:** creates the file with a heading and one sentence. Each `\n` is a line break.

**3. Stage the new file.**

```bash
git add docs/settlement.md
```
**What this does:** tells git to start tracking it and include it in the next commit. Brand-new
files always need this — `git commit -a` would not pick it up.

**4. Commit it.**

```bash
git commit -m "docs: record the settlement timeout"
```
**What this does:** saves the first commit on this branch.

**5. Add a second sentence.**

```bash
printf '\nFailed settlements are retried 3 times.\n' >> docs/settlement.md
```
**What this does:** appends to the existing page.

**6. Commit that too.**

```bash
git commit -am "docs: record settlement retries"
```
**What this does:** the file is already tracked, so `-a` stages it for you. Your branch now has two
commits.

**7. Make a copy of the branch to merge.**

```bash
git branch try-merge
```
**What this does:** creates a second label at the same commit. Two names, one line of work — so
you can try two approaches from an identical starting point.

**8. Make another copy to rebase.**

```bash
git branch try-rebase
```
**What this does:** the same again, under a different name.

**9. Switch to the first copy.**

```bash
git switch try-merge
```
**What this does:** moves you onto `try-merge`. Your files do not change — it is the same commit.

**10. Merge `main` into it.**

```bash
git merge --no-edit main
```
**What this does:** brings everything that happened on `main` into your branch and records that
joining as a new commit with **two parents**. `--no-edit` accepts the standard message.

**11. Look at the shape.**

```bash
git log --oneline --graph -6
```
**What this does:** the drawing shows a fork that comes back together at
`Merge branch 'main' into try-merge`. Your two commits keep their original hashes.

**12. Switch to the other copy.**

```bash
git switch try-rebase
```
**What this does:** moves you to the untouched copy of the same branch.

**13. Rebase it onto `main`.**

```bash
git rebase main
```
**What this does:** lifts your two commits off, moves the branch to the tip of `main`, and replays
your commits **on top**. It prints `Successfully rebased and updated …`.

**14. Look at the shape.**

```bash
git log --oneline --graph -5
```
**What this does:** one straight line, no merge commit. Tidier to read — and the hashes of your
two commits have **changed**, because they were re-created.

**15. Compare with the original branch.**

```bash
git log --oneline -2 feature/PAY-150-settlement-docs
```
**What this does:** shows the same two messages under **different hashes**. That is what "rewriting
history" means.

**16. Compare the files, not the history.**

```bash
git diff try-merge try-rebase
```
**What this does:** compares the contents of the two branches. **It prints nothing: the files are
identical.** Merge and rebase give you the same code with a different story about how it got there.

### Step 7.2 — A conflict during a rebase

**1. Go back to `main`.**

```bash
git switch main
```
**What this does:** leaves the experiment branches behind.

**2. Add a changelog line on `main`.**

```bash
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Changed: list endpoint returns at most 100 records.\n'))"
```
**What this does:** inserts a line immediately under `## Unreleased`.

**3. Commit it.**

```bash
git commit -am "docs: note the list limit in the changelog"
```
**What this does:** `main` now has a line in that exact spot.

**4. Start a feature branch from just before that commit.**

```bash
git switch -c feature/PAY-151-refund-fees main~1
```
**What this does:** `main~1` is one commit back, so this branch has **not** got the line you just
added — like a colleague who branched this morning.

**5. Add a different line in the same place.**

```bash
python3 -c "import pathlib; p=pathlib.Path('CHANGELOG.md'); p.write_text(p.read_text().replace('## Unreleased\n', '## Unreleased\n- Added: refunds pay no card fee.\n'))"
```
**What this does:** inserts *your* line under the same heading. Two people have now edited the same
line of the same file — the most common real conflict there is.

**6. Commit it.**

```bash
git commit -am "docs: note refund fees in the changelog"
```
**What this does:** saves your version on the feature branch.

**7. Rebase onto `main`. This stops with a conflict, on purpose.**

```bash
git rebase main
```
**What this does:** tries to replay your commit on top of `main` and cannot decide which line
should come first:
```
CONFLICT (content): Merge conflict in CHANGELOG.md
error: could not apply 7873191... docs: note refund fees in the changelog
```
Nothing is broken. Git has paused and is waiting for you.

**8. Ask git where you stand.**

```bash
git status
```
**What this does:** says `You are currently rebasing branch 'feature/PAY-151-refund-fees'` and
lists `both modified: CHANGELOG.md`, with the commands you may use next.

**9. Look at the conflict in the file.**

```bash
head -10 CHANGELOG.md
```
**What this does:** `head -10` prints the first ten lines of a file. You see git's markers:
```
## Unreleased
<<<<<<< HEAD
- Changed: list endpoint returns at most 100 records.
=======
- Added: refunds pay no card fee.
>>>>>>> 7873191 (docs: note refund fees in the changelog)
```
Everything between `<<<<<<<` and `=======` is one version; everything from `=======` to `>>>>>>>`
is the other.

> ⚠️ **During a rebase, the labels are the other way round from a merge.** `HEAD` is **main's**
> line — the branch you are rebasing *onto*. **Your** line is the bottom one, labelled with your
> commit. This catches everyone at least once.

**10. Resolve it — keep both lines.**

Both lines are true, so the fix is to delete only the three marker lines. **By hand:** run
`nano CHANGELOG.md`, delete the lines starting `<<<<<<<`, `=======` and `>>>>>>>`, save with
`Ctrl` + `O` then `Enter`, and leave with `Ctrl` + `X`. **Or** run this command, which does exactly
that:

```bash
grep -v -e '^<<<<<<< ' -e '^=======$' -e '^>>>>>>> ' CHANGELOG.md > CHANGELOG.tmp && mv CHANGELOG.tmp CHANGELOG.md
```
**What this does:** `grep -v` prints every line that does **not** match the patterns (`-e` adds
each pattern), `>` writes those lines into a temporary file, and `mv` renames the temporary file
over the original. The `&&` means "only do the second part if the first part succeeded".

**11. Check the result.**

```bash
head -6 CHANGELOG.md
```
**What this does:** both entries now sit under `## Unreleased`, with no markers left.

**12. Tell git the file is resolved.**

```bash
git add CHANGELOG.md
```
**What this does:** staging a conflicted file is how you say "I have dealt with this one".

**13. Finish the rebase.**

```bash
GIT_EDITOR=true git rebase --continue
```
**What this does:** carries on replaying and prints `Successfully rebased and updated
refs/heads/feature/PAY-151-refund-fees`. `GIT_EDITOR=true` in front of the command means "for this
one command, use a do-nothing editor" — it accepts the existing commit message instead of opening
nano at you.

**14. Look at the history.**

```bash
git log --oneline -3
```
**What this does:** your commit now sits on top of main's, in a straight line.

> **Changed your mind half-way?** `git rebase --abort` puts the branch back exactly as it was
> before `git rebase` started.

### Step 7.3 — Interactive rebase: tidy your commits before review

**1. Start a fresh branch from the tip of `main`.**

```bash
git switch -c feature/PAY-152-fee-guide main
```
**What this does:** creates the branch you will use for the rest of this lab, including Part 8.

**2. Write a page about refunds.**

```bash
printf '# Refunds\n\nA refund pays no card fee.\n' > docs/refunds.md
```
**What this does:** creates the file.

**3. Stage it.**

```bash
git add docs/refunds.md
```
**What this does:** new file, so it needs `git add`.

**4. Commit it.**

```bash
git commit -m "docs: explain refund fees"
```
**What this does:** your first good commit on this branch.

**5. Write a page about receipts.**

```bash
printf '# Receipts\n\nThe fee is printed on every receipt.\n' > docs/receipts.md
```
**What this does:** creates the second file.

**6. Stage it.**

```bash
git add docs/receipts.md
```
**What this does:** as before.

**7. Commit it.**

```bash
git commit -m "docs: explain fees on receipts"
```
**What this does:** two clean commits, one page each.

Now the mess that real work creates.

**8. Remember something that belongs in the first commit.**

```bash
printf 'The original fee is returned with the refund.\n' >> docs/refunds.md
```
**What this does:** adds a sentence to the refunds page.

**9. Mark it as a fix for that earlier commit.**

```bash
git commit -a --fixup HEAD~1
```
**What this does:** commits it with the automatic message `fixup! docs: explain refund fees` — a
note to git saying "this belongs *inside* that commit", not beside it.

**10. Remember something for the second commit too.**

```bash
printf 'It is also shown on the monthly statement.\n' >> docs/receipts.md
```
**What this does:** adds a sentence to the receipts page.

**11. Commit it lazily.**

```bash
git commit -am "wip"
```
**What this does:** the commit everyone has made at 17:55. "wip" means work in progress and tells a
reviewer nothing.

**12. Look at the mess.**

```bash
git log --oneline main..
```
**What this does:** `main..` means "commits on my branch that are not on main". Four commits, two
of which are noise.

**13. Tidy them in one pass.**

```bash
git rebase -i --autosquash main
```
**What this does:** `-i` (**i**nteractive) opens a **plan** in nano, oldest commit first — the
**reverse** of `git log`. `--autosquash` has already moved the `fixup!` commit underneath the commit
it belongs to:
```
pick  1f8681d docs: explain refund fees
fixup 88f56c3 fixup! docs: explain refund fees
pick  eee6a47 docs: explain fees on receipts
pick  81c7b68 wip
```
**Your job:** change the word `pick` at the start of the **`wip`** line to `fixup`, then save with
`Ctrl` + `O`, `Enter`, and exit with `Ctrl` + `X`. Git then replays the plan.

Your hashes will differ. Git 2.50 and later print a `#` before each message (`pick 81c7b68 # wip`);
that is only a comment — change the first word in the same way.

| Plan word | Does |
|---|---|
| `pick` | Keep the commit as it is |
| `reword` | Keep it, but edit the message |
| `squash` | Meld into the line above and combine the messages |
| `fixup` | Meld into the line above and **drop** this message |
| `drop` | Delete the commit |
| *(move a line)* | Reorder the commits |

**14. Look at the result.**

```bash
git log --oneline main..
```
**What this does:** four commits have become **two**, each one complete: `docs: explain refund fees`
and `docs: explain fees on receipts`.

**15. Check nothing was lost.**

```bash
git show --stat --format=%s HEAD
```
**What this does:** shows the newest commit's subject and which files it touched:
`docs/receipts.md | 4 ++++` — all four lines, including the one from the "wip" commit. The words
disappeared; the work did not.

### Step 7.4 — Undo a rebase you regret

**1. Jump back to where the branch was before the rebase.**

```bash
git reset --hard ORIG_HEAD
```
**What this does:** git saved the old position under the name `ORIG_HEAD` before it started the
rebase. Resetting to it **undoes the whole rebase** in one step.

**2. Confirm the mess is back.**

```bash
git log --oneline main..
```
**What this does:** the four untidy commits are there again.

**3. Open the diary.**

```bash
git reflog -4
```
**What this does:** shows `reset: moving to ORIG_HEAD` at `HEAD@{0}` and `rebase (finish)` at
`HEAD@{1}` — the tidy version is one move back.

**4. Redo the tidy version.**

```bash
git reset --hard HEAD@{1}
```
**What this does:** moves the branch to where it was after the rebase.

**5. Confirm.**

```bash
git log --oneline main..
```
**What this does:** two clean commits again. You have just undone an undo: **nothing a local
rebase does is permanent** while the reflog remembers it.

---

## Part 8 — A shared server: force-pushing safely (15 min)

A branch that only you have is yours to rewrite. The moment a colleague has pulled it, rewriting
it creates work for them — or quietly deletes theirs. Here you play both people: **you** work in
`git-gym`, **Ben** works in `git-gym-colleague`, and `git-gym-origin.git` plays the server.

> Each command below starts by telling you which of the three folders you are in. Most mistakes in
> this part are a command run in the wrong one — run `pwd` whenever you lose track.

### Step 8.1 — A "server" and a colleague

**1. Go up to the folder that holds everything.**

```bash
cd ~/devops-course
```
**What this does:** moves out of the gym into its parent folder, so the next commands can create
folders beside it.

**2. Create the "server".**

```bash
git clone --bare git-gym git-gym-origin.git
```
**What this does:** `--bare` copies the history **with no working files** — just the database. That
is exactly what a server such as GitHub stores. The `.git` on the end of the name is the
convention for such a copy.

**3. Create Ben's laptop.**

```bash
git clone git-gym-origin.git git-gym-colleague
```
**What this does:** clones the "server" into a second normal folder. This is your colleague's copy.

**4. Give Ben a name.**

```bash
git -C git-gym-colleague config user.name "Ben Okafor"
```
**What this does:** `git -C <folder>` runs a git command **inside another folder** without moving
there. This sets the name that folder's commits will carry.

**5. Give Ben an email address.**

```bash
git -C git-gym-colleague config user.email "ben.okafor@example.com"
```
**What this does:** the same for the email, so Ben's commits are clearly not yours.

**6. Go back to your own copy.**

```bash
cd ~/devops-course/git-gym
```
**What this does:** you are **you** again for the rest of this step.

**7. Tell your copy where the server is.**

```bash
git remote add origin ~/devops-course/git-gym-origin.git
```
**What this does:** `remote add` saves a server address under a short name. `origin` is the
customary name for "the copy I cloned from and push to". Here it is a folder on your own machine
rather than a URL, which behaves the same way.

**8. Download the server's branches.**

```bash
git fetch origin
```
**What this does:** `fetch` downloads everything the server has **without changing any of your
files or branches**. It is always safe.

**9. Switch to the branch from Step 7.3.**

```bash
git switch feature/PAY-152-fee-guide
```
**What this does:** this is the branch you will now "share" with Ben.

**10. Link it to the server's copy of the same branch.**

```bash
git branch --set-upstream-to=origin/feature/PAY-152-fee-guide
```
**What this does:** records which branch on the server this one pushes to and pulls from — its
**upstream**. Afterwards, a bare `git push` knows where to go.

**11. Check the link.**

```bash
git status -sb
```
**What this does:** `-b` adds the branch line:
`## feature/PAY-152-fee-guide...origin/feature/PAY-152-fee-guide` with no "ahead" or "behind" —
you and the server are in step.

### Step 8.2 — `--force-with-lease` saves your colleague's work

Ben adds a page to the shared branch and pushes it.

**1. Become Ben.**

```bash
cd ~/devops-course/git-gym-colleague
```
**What this does:** moves into Ben's folder. Everything until command 7 is Ben working.

**2. Switch to the shared branch.**

```bash
git switch feature/PAY-152-fee-guide
```
**What this does:** Ben starts work on the same branch as you.

**3. Write a new page.**

```bash
printf '# Chargebacks\n\nA chargeback returns the card fee too.\n' > docs/chargebacks.md
```
**What this does:** creates Ben's file.

**4. Stage it.**

```bash
git add docs/chargebacks.md
```
**What this does:** new file, so `git add` is required.

**5. Commit it.**

```bash
git commit -m "docs: explain chargeback fees"
```
**What this does:** Ben's work is now saved on his laptop.

**6. Push it to the server.**

```bash
git push
```
**What this does:** uploads Ben's commit. The server's copy of the branch is now one commit ahead
of yours.

**7. Become yourself again.**

```bash
cd ~/devops-course/git-gym
```
**What this does:** back to your own folder — where you have **not** fetched, so you do not know
about Ben's commit.

**8. Reword your last commit.**

```bash
git commit --amend -m "docs: explain fees on receipts and statements"
```
**What this does:** replaces your newest commit with one carrying a better message — and a new
hash. Your branch and the server's now tell different stories about the same work.

**9. Push it normally. This is rejected on purpose.**

```bash
git push
```
**What this does:** git refuses — `! [rejected] … (fetch first)`. The server holds a commit
(Ben's) that you do not have, and an ordinary push is never allowed to remove commits.

**10. Try the careful force-push. This is also rejected, and that is the point.**

```bash
git push --force-with-lease
```
**What this does:** `--force-with-lease` means "overwrite the server, but only if it still looks
exactly as it did when I last looked". It does not — Ben pushed since — so git refuses with
`(stale info)`. **The lease just saved Ben's commit.**

**11. Update your picture of the server.**

```bash
git fetch origin
```
**What this does:** downloads Ben's commit into your copy (without touching your branch). Careful:
this quietly **renews the lease**. A plain `--force-with-lease` would now succeed and delete Ben's
commit — we tested it. Editors that fetch in the background cause exactly this.

**12. Add the second safety check. Rejected again — correctly.**

```bash
git push --force-with-lease --force-if-includes
```
**What this does:** `--force-if-includes` asks a harder question: "have I actually *built on* the
server's latest commit?" You have not, so it refuses with
`(remote ref updated since checkout)`. This is the pair of options to use for life.

**13. Make that pair your default.**

```bash
git config --global alias.pushf "push --force-with-lease --force-if-includes"
```
**What this does:** creates a shortcut called `git pushf`. An **alias** is your own name for a
longer command; `--global` means it works in every repository on this machine. From now on, that is
the only force-push you use.

**14. See the two versions side by side.**

```bash
git log --oneline --graph HEAD origin/feature/PAY-152-fee-guide -5
```
**What this does:** the drawing forks: your reworded commit on one side, Ben's
`docs: explain chargeback fees` on the other.

**15. Give up your rewrite and take the server's version.**

```bash
git reset --hard origin/feature/PAY-152-fee-guide
```
**What this does:** makes your branch identical to the server's. Your only change was a commit
message, so dropping it costs nothing — and **the right fix, once a branch is shared, is to stop
rewriting it.**

**16. Confirm Ben's commit is now in your history.**

```bash
git log --oneline main..
```
**What this does:** lists `docs: explain chargeback fees` above your own two commits.

> 🔑 **Once someone else has commits on your branch, add new commits. Do not rewrite the old ones.**

### Step 8.3 — What a plain `--force` does

Ben pushes another commit.

**1. Become Ben.**

```bash
cd ~/devops-course/git-gym-colleague
```
**What this does:** back to the colleague's folder.

**2. Add a sentence to his page.**

```bash
printf 'A chargeback can arrive up to 120 days later.\n' >> docs/chargebacks.md
```
**What this does:** appends one more line.

**3. Commit it.**

```bash
git commit -am "docs: chargeback time limit"
```
**What this does:** the file is tracked, so `-a` stages it.

**4. Push it.**

```bash
git push
```
**What this does:** the server now has two commits from Ben.

**5. Become yourself — and again do not fetch.**

```bash
cd ~/devops-course/git-gym
```
**What this does:** back to your folder, with an out-of-date picture of the server.

**6. Rewrite history again.**

```bash
git commit --amend -m "docs: explain chargeback fees (reviewed)"
```
**What this does:** replaces the newest commit — which is *Ben's* commit — with your own version of
it. Already a bad idea.

**7. Use the blunt tool.**

```bash
git push --force
```
**What this does:** `--force` means "make the server match me, no questions asked". It **succeeds**:
`+ … (forced update)`.

**8. See what that cost.**

```bash
git log --oneline origin/feature/PAY-152-fee-guide -2
```
**What this does:** the server's history no longer contains `docs: chargeback time limit`. **Ben's
commit is gone from the server**, and nobody was warned.

Ben only gets it back because it is still on his laptop.

**9. Become Ben.**

```bash
cd ~/devops-course/git-gym-colleague
```
**What this does:** back to the colleague's folder, where the lost commit still exists.

**10. Download what the server looks like now.**

```bash
git fetch
```
**What this does:** prints `(forced update)` — git's way of saying the server's history was
rewritten.

**11. See the damage.**

```bash
git status -sb
```
**What this does:** says `[ahead 2, behind 1]` — Ben's copy and the server's have split into two
different stories.

**12. Match the server.**

```bash
git reset --hard origin/feature/PAY-152-fee-guide
```
**What this does:** takes the server's version. Ben's own commit is no longer on his branch — but
git remembers where he was, under the name `ORIG_HEAD`.

**13. Copy the lost commit back on top.**

```bash
git cherry-pick ORIG_HEAD
```
**What this does:** re-applies the commit Ben was sitting on before the reset, so his work returns
above yours.

**14. Put it back on the server.**

```bash
git push
```
**What this does:** an ordinary push now — Ben is only adding, not removing.

**15. Check the repaired history.**

```bash
git log --oneline -3
```
**What this does:** `docs: chargeback time limit` sits on top of your reviewed commit. Nothing was
lost — but only because one person still had a copy.

> ⚠️ **Why not `git pull --rebase`?** After a force-push it can treat commits you had *already
> pushed* as the server's history and **drop them silently**. We tested it: Ben's commit vanished
> from his laptop too. After a forced update, reset and cherry-pick deliberately, as above.

### Step 8.4 — Stop it happening: protect `main` on the server

**1. Switch on a rule on the server itself.**

```bash
git -C ~/devops-course/git-gym-origin.git config receive.denyNonFastForwards true
```
**What this does:** `git -C` again runs a command inside another folder — here, the server. The
setting tells the server to **reject any push that would remove commits**, from anyone, on any
branch.

**2. Go back to your copy.**

```bash
cd ~/devops-course/git-gym
```
**What this does:** you are yourself again.

**3. Switch to `main`.**

```bash
git switch main
```
**What this does:** the branch the rule protects.

**4. Link it to the server's `main`.**

```bash
git branch --set-upstream-to=origin/main
```
**What this does:** as in Step 8.1, so pushes know where to go.

**5. Rewrite the newest commit on `main`.**

```bash
git commit --amend -m "docs: note the list limit in the changelog (reworded)"
```
**What this does:** exactly the thing the rule exists to stop.

**6. Try to force it through. This fails on purpose.**

```bash
git push --force origin main
```
**What this does:** the server refuses:
```
remote: error: denying non-fast-forward refs/heads/main (you should pull first)
 ! [remote rejected] main -> main (non-fast-forward)
```
**Even `--force` cannot get past a rule on the server.** On GitHub this is the **"Allow force
pushes: off"** setting you left unticked in Lab 03 Step 2.1; on GitLab it is the **"Allowed to
force push"** switch on a protected branch.

**7. Undo your local rewrite.**

```bash
git reset --hard origin/main
```
**What this does:** makes your `main` match the server's again.

**8. Confirm you are back in step.**

```bash
git status -sb
```
**What this does:** prints `## main...origin/main` with nothing after it — no ahead, no behind.

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

1. **`git rerere`.** Run `git config --global rerere.enabled true`, repeat Step 7.2 on a fresh
   branch, abort the rebase, then rebase again. Git remembers how you resolved the conflict and
   does it for you.
2. **`git worktree`.** Run `git worktree add ../gym-hotfix release/1.0` to check out a second
   branch in a second folder, so a hot-fix never needs `git stash`.
3. **Bisect by hand.** Rebuild the gym with the RECOVER commands and find the bug using
   `git bisect good` and `git bisect bad` yourself instead of `git bisect run`. Count the steps.
4. **Sign a tag.** Run `git config --global gpg.format ssh`, then
   `git config --global user.signingkey ~/.ssh/id_ed25519.pub`, then `git tag -s v1.2.0 -m "…"`.
   Verify it with `git tag -v v1.2.0` after setting up an allowed-signers file.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `setup-gym.sh: Set your git identity first` | No `user.email` configured | Lab 00 Step 6 |
| `No such file or directory` on the setup script | The course material is not where the lab expects | Run `ls ~/devops-course/course-material` — if it is missing, clone it as in Lab 00 |
| An editor opens and you do not know how to leave | Git asked for a message or a plan | nano: `Ctrl`+`O`, `Enter`, `Ctrl`+`X`. vim: `Esc`, then type `:wq` and press `Enter` |
| The output stops and the last line is `:` or `(END)` | You are in the pager | Press `q` |
| `$GOOD` or `$BAD` is empty | You opened a new terminal window since setting it | Re-run the command that set it, in the window you are using |
| `You are in 'detached HEAD' state` | You switched to a tag or a hash, not a branch | `git switch main` |
| `git stash pop` reports a conflict | You popped onto a different commit | The stash is kept: `git reset --hard`, switch back, pop again |
| `could not apply …` during a rebase | A conflict | Fix the file, `git add`, `git rebase --continue` — or `git rebase --abort` |
| `fatal: It seems that there is already a rebase-merge directory` | A rebase is still in progress | `git rebase --continue` or `git rebase --abort` |
| Bisect names the wrong commit | The check fails for another reason on some commits (e.g. a missing file) | Make the check `exit 125` on commits it cannot test — bisect skips those |
| `! [rejected] … (stale info)` | The server changed since you last fetched | That is the lease working — fetch and look before you force anything |
| `fatal: not a git repository` | You are not inside the gym | `cd ~/devops-course/git-gym`, then `pwd` to check |
| Anything else | The gym is in a state you do not understand | Run the RECOVER commands — two seconds |

---

## 🎯 Outcome

You have used every command from the Going Further Git slides and seen the output of each: stash,
patch staging, amend, restore, the three resets, reflog rescue, bisect, revert, clean, annotated
and lightweight tags, `describe`, a release branch with a cherry-picked hot-fix, merge versus
rebase on the same branch, a rebase conflict, interactive rebase with autosquash, undoing a
rebase, and a lease that saved a colleague's commit.

**Next:** [Lab 04 — GitHub Actions CI](../lab-04-github-actions-ci/README.md), or
[Lab 04A — Run CI on your laptop with act](../lab-04-github-actions-ci/README-04A-act-and-pipeline-security.md) once
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
  3. Part 8: people lose track of which folder they are in. Tell them to read the prompt, or run
     `pwd`, before every command in that part.
  4. Someone runs a command in `paytrack-api-team` instead of the gym. `pwd` before Part 4.
- **Debrief question:** "Which of today's commands would you allow on `main` in your organisation,
  and which should the server refuse? Where is that rule written down today?"
</details>
