# Lab 04A — Run CI on Your Laptop with act, Then Harden the Pipeline

| | |
|---|---|
| **Day** | 2 — **optional**, after class or as homework |
| **Duration** | About 90 minutes, in nine parts |
| **Module** | 2 — Version Control and CI (the *Going Further* slides, section D) |
| **You will produce** | `act` working on your machine; a hardened `ci.yml` with a build job; `release.yml`; `Makefile`; two demo workflows; an audit that reports **no findings** |
| **Feeds into** | Nothing depends on it. Lab 06 adds `build.yml` and Lab 17 adds `security.yml` beside the files you harden here |

---

## Objective

In Lab 04 every change to the pipeline cost a push and a few minutes of waiting. Here you run the
**same workflow on your own machine** with [`act`](https://github.com/nektos/act), in seconds.
Then you use that fast loop to see the pipeline-security slides *behave*:

- a secret masked in the log — and the same secret leaking in plain sight
- a pull-request title that **runs its own commands** inside your pipeline
- two tools that find those problems for you
- a pipeline that builds **one** versioned artefact and publishes it from a tag

## Prerequisites

- **Lab 04 complete**: `.github/workflows/ci.yml` merged, *CI passed* a required check
- **Docker running** — `act` runs every job in a container (`docker info` must work without `sudo`)
- About **6 GB free disk** (the runner image is large, and it is downloaded once)
- `gh` signed in with the `workflow` scope (Lab 00 Step 8.1)

---

## Before you start — how to run the commands in this lab

**You do not need to know Linux.** Every instruction below is **one command in one grey box**,
numbered in the order you run it. Here is everything you need to know about the terminal:

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. (Or press the ⊞ key, type `terminal`, press `Enter`.) |
| **How do I run a command?** | Click into the terminal, type or paste the contents of one box, press `Enter`. |
| **How do I paste?** | Copy from this page with `Ctrl` + `C`; paste into the terminal with **`Ctrl` + `Shift` + `V`** — plain `Ctrl` + `V` does nothing there. |
| **When is it finished?** | When the `$` prompt comes back. Some commands in this lab take minutes; wait. |
| **Nothing was printed!** | Normal — many commands say nothing when they succeed. |
| **The screen filled and the last line is `:` or `(END)`** | You are in a pager. Press `q`. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel. |
| **It asked for a password** | A `sudo` command needs your login password. **Nothing appears as you type** — not even dots. Type it and press `Enter`. |
| **A box is several lines long** | If it starts with `cat > … <<'EOF'`, copy **all** of it — the last `EOF` line included — and press `Enter` once. It is still one command. |

**Symbols you will meet in the boxes:**

| Symbol | Means |
|---|---|
| `~` | Your home folder. `~/devops-course` is the `devops-course` folder inside it |
| `cd` | Move into a folder; everything after that happens there |
| `>` / `>>` | Put the output into a file / onto the end of a file |
| `\|` | Send the first command's output into the second one |
| `$(…)` | Run this first and use its answer here |
| `NAME=value` | Remember `value` under the name `NAME`, for this terminal window only |
| `&&` | Only run the next part if this part succeeded |
| `\|\|` | Only run the next part if this part **failed** |
| `sudo` | Run this one command as the machine's administrator |

Two warnings specific to this lab:

1. **Some commands fail on purpose** — the text says so before the box. That is the lesson, not a
   mistake.
2. **YAML files care about spaces.** The `cat > … <<'EOF'` boxes write them for you exactly right.
   If you retype one by hand, keep the indentation identical: two spaces, never a Tab.

🔁 **RECOVER — make sure you have the repository this lab works on**

```bash
cd ~/devops-course
```
**What this does:** moves into the course folder that holds all your work.

```bash
[ -d paytrack-api-team ] || git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-team
```
**What this does:** `[ -d <folder> ]` asks "does this folder exist?" and `||` means "if not, do the
next thing" — clone your repository. Replace `<your-username>` with your own GitHub username.

```bash
cd paytrack-api-team
```
**What this does:** moves into your project.

```bash
git switch main
```
**What this does:** puts you on the main branch.

```bash
git pull
```
**What this does:** downloads anything merged on GitHub since you last looked.

```bash
ls .github/workflows/ci.yml
```
**What this does:** `ls` lists a file if it exists. If it says *No such file or directory*, finish
Lab 04 first — this lab hardens that file.

## Words you need

| Word | Plain meaning |
|---|---|
| **Workflow** | A file in `.github/workflows/` describing jobs GitHub should run for you |
| **Job** | One unit of that work, run on a fresh machine |
| **act** | A free tool that reads `.github/workflows/*.yml` and runs the jobs in Docker on your machine |
| **Container** | A small, disposable machine-inside-your-machine that Docker starts and throws away |
| **Runner image** | The container that pretends to be GitHub's `ubuntu-24.04` machine |
| **Event** | What started the workflow: `push`, `pull_request`, `workflow_dispatch`… act needs you to name one |
| **Masking** | GitHub (and act) replacing a secret's exact text with `***` in logs |
| **Script injection** | Text from outside (a PR title, a branch name) being run as a command |
| **Pinning** | Referring to an action by its full commit hash, which cannot be moved, instead of a tag such as `v4`, which can |
| **Artefact** | The file a build produces — here, a `.tar.gz` of the app |

---

## Part 1 — Install act (10 min)

**1. Check whether you already have it.**

```bash
act --version || echo "act is not installed yet"
```
**What this does:** prints `act version 0.2.89` if act is already installed (Lab 00 Step 8.4 or the
course installer does it). `||` means "if that failed, do this instead" — so otherwise you see the
message. **If it is already installed, skip to command 9.**

**2. Choose the version to install.**

```bash
ACT_VERSION=0.2.89
```
**What this does:** remembers the version number under the name `ACT_VERSION` for the rest of this
terminal window. Nothing is printed. Pinning a version means everyone installs the same tool.

**3. Work out which build your machine needs.**

```bash
ACT_ARCH=$(uname -m | sed 's/aarch64/arm64/')
```
**What this does:** `uname -m` prints your processor type (`x86_64` on most laptops, `aarch64` on
Apple silicon and ARM servers). `sed 's/a/b/'` swaps one word for another — here turning `aarch64`
into `arm64`, which is what act calls it. The answer is stored under the name `ACT_ARCH`.

**4. Check what it decided.**

```bash
echo "$ACT_ARCH"
```
**What this does:** prints `x86_64` or `arm64`. If it prints nothing, run command 3 again in this
same window.

**5. Move to a scratch folder.**

```bash
cd /tmp
```
**What this does:** `/tmp` is the system's scratch space — everything in it is deleted when the
machine restarts, which is exactly right for a download.

**6. Download the release.**

```bash
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/act_Linux_${ACT_ARCH}.tar.gz"
```
**What this does:** `curl` downloads a file from the internet. `-O` saves it under its own name,
`-L` follows redirects, and `-fs` keep it quiet unless something goes wrong. `${ACT_VERSION}` and
`${ACT_ARCH}` are replaced with what you stored earlier.

**7. Download the project's list of fingerprints.**

```bash
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/checksums.txt"
```
**What this does:** downloads a small text file in which the act project published a **checksum**
(a fingerprint) for every file in this release.

**8. Check the download is genuine.**

```bash
grep " act_Linux_${ACT_ARCH}.tar.gz\$" checksums.txt | sha256sum -c -
```
**What this does:** `grep` picks the one line about your file out of the list, the `|` hands it to
`sha256sum -c`, which re-calculates the fingerprint of the file you downloaded and compares the
two. You must see `act_Linux_x86_64.tar.gz: OK` (or `arm64`). **If it says FAILED, stop** — the
file is not what the project published. This is the safe version of the `curl | bash` install from
Lab 00: download, **verify**, then install.

**9. Install it.**

```bash
sudo tar -xzf "act_Linux_${ACT_ARCH}.tar.gz" -C /usr/local/bin act
```
**What this does:** `tar` unpacks the downloaded archive: `-x` extract, `-z` it is compressed,
`-f` from this file, `-C` into this folder. `/usr/local/bin` is where programs everyone can run
live, which is why `sudo` (administrator) is needed. The last word means "extract only the file
called `act`".

**10. Check it runs.**

```bash
act --version
```
**What this does:** prints `act version 0.2.89`.

**11. Go back to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** leaves the scratch folder. Everything from here on happens in your repository.

> **Other ways in:** `gh extension install nektos/gh-act` gives you `gh act`; on a Mac,
> `brew install act`. The commands below are the same.

**12. Confirm Docker is running.**

```bash
docker info --format 'Docker {{.ServerVersion}} is running'
```
**What this does:** asks Docker for its version, which only works if the Docker service is running
and your user is allowed to talk to it. act needs both. If you get *permission denied*, log out and
back in (Lab 00 Step 2).

---

## Part 2 — Run your pipeline on your laptop (15 min)

### Step 2.1 — Tell act which image stands in for GitHub's machine

**1. Make sure you are in the project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the workflow files are here, and act must be run from the folder that contains
`.github/`.

**2. Go to the main branch.**

```bash
git switch main
```
**What this does:** starts you from the reviewed code, not a leftover branch.

**3. Get the latest version.**

```bash
git pull
```
**What this does:** downloads whatever was merged on GitHub since your last pull.

**4. Start a branch for this lab's work.**

```bash
git switch -c ci/act-and-hardening
```
**What this does:** `-c` creates the branch and switches to it. Everything you change in this lab
lives here until Part 9 merges it.

**5. Write act's settings file.**

```bash
cat > .actrc <<'EOF'
-P ubuntu-24.04=catthehacker/ubuntu:act-24.04
--artifact-server-path /tmp/act-artifacts
EOF
```
**What this does:** one command — copy the whole box, final `EOF` included. `cat > <file> <<'EOF'`
means "write everything up to the line `EOF` into this file". The file holds options act reads
every time it starts in this folder, so everyone on the team runs it the same way:
- `-P ubuntu-24.04=…` — "when a job says `runs-on: ubuntu-24.04`, use this container image". The
  `catthehacker` images are built to resemble GitHub's runners and are the ones the act project
  recommends. Without this line, act stops on first use and asks you to choose.
- `--artifact-server-path` — starts a small local stand-in for GitHub's artefact storage, so
  `actions/upload-artifact` works. Files land in `/tmp/act-artifacts`.

**6. Read the file back.**

```bash
cat .actrc
```
**What this does:** `cat` prints a file to the screen. You should see exactly the two lines above.

### Step 2.2 — See what act found

**1. List the jobs without running anything.**

```bash
act -l
```
**What this does:** `-l` is for **l**ist:
```
Stage  Job ID     Job name                                     Workflow name  Workflow file  Events
0      lint       Lint & format                                CI             ci.yml         push,pull_request,workflow_dispatch
0      test       Unit tests (py${{ matrix.python-version }})  CI             ci.yml         push,pull_request,workflow_dispatch
1      ci-passed  CI passed                                    CI             ci.yml         push,pull_request,workflow_dispatch
```
**Stage 0** jobs run at the same time; **stage 1** waits for them — that is `needs: [lint, test]`.
On an Apple-silicon or ARM machine you may also see a warning about container architecture; ignore
it unless a job fails (see Troubleshooting).

### Step 2.3 — Run one job

**1. Run the lint job as if a pull request had been opened.**

```bash
act pull_request -j lint
```
**What this does:** `pull_request` is the **event** you are pretending happened; `-j lint` picks
the one job whose id is `lint`. **The first run downloads the runner image — more than a gigabyte,
once — so give it a few minutes.** Then read the log:

| You see | Means |
|---|---|
| `[CI/Lint & format] ⭐ Run Main flake8 …` | A step starting. The prefix is `[workflow/job]` |
| `\| …` | Output of the command inside the step |
| `✅  Success - Main flake8 …` | The step passed |
| `❌  Failure - Main …` | The step failed |
| `🏁  Job succeeded` | The whole job passed |

### Step 2.4 — Run one leg of the matrix, then everything

**1. Run the tests for one Python version only.**

```bash
act pull_request -j test --matrix python-version:3.12
```
**What this does:** the `test` job normally runs twice, once per Python version. `--matrix key:value`
picks a single combination — handy when only one version is failing.

**2. Run the whole pipeline.**

```bash
act pull_request
```
**What this does:** with no `-j`, act runs **every** job for a pull request: lint and both test
legs, then `ci-passed`.

**3. Look at the files the pipeline produced.**

```bash
ls -R /tmp/act-artifacts | head -20
```
**What this does:** `ls -R` lists a folder and everything inside it; `| head -20` keeps only the
first 20 lines so the screen is not flooded. You see the coverage and JUnit files that
`upload-artifact` saved to the local artefact server.

✅ **Checkpoint:** the last job prints `All CI jobs passed.` and `🏁  Job succeeded`.

---

## Part 3 — Break it before anyone sees (5 min)

**1. Break the health endpoint on purpose.**

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace('return jsonify(status="ok", version=config.VERSION), 200',
              'return jsonify(status="BROKEN", version=config.VERSION), 200')
assert "BROKEN" in s, "patch did not apply"
p.write_text(s)
PY
```
**What this does:** one command — copy the whole box including the final `PY`. It makes the same
break as Lab 04 Step 6 (the service now answers `BROKEN` instead of `ok`), **without committing
it**.

**2. Confirm the file is changed but not committed.**

```bash
git status -s
```
**What this does:** lists two things: ` M app/src/app.py` — **m**odified, not staged and not
committed — and `?? .actrc`, the new file from Step 2.1 that git is not yet tracking.

**3. Run the tests locally.**

```bash
act pull_request -j test --matrix python-version:3.12
```
**What this does:** the job fails — `❌  Failure - Main Run pytest with coverage` and
`🏁  Job failed` — in seconds, with no commit, no push and no waiting for GitHub.

> 🔑 **act runs the files in your folder, not your last commit.** Uncommitted edits are included.
> That is what makes it a fast feedback loop.

**4. Undo the break.**

```bash
git restore app/src/app.py
```
**What this does:** rewrites the file from the last commit, removing the `BROKEN` line.

**5. Check what is left.**

```bash
git status -s
```
**What this does:** now lists only `?? .actrc`, the new file you created in Step 2.1.

### What act can — and cannot — tell you

| act **does** | act **does not** |
|---|---|
| Run your `run:` steps and most `uses:` actions | Enforce branch protection or required checks — only GitHub can refuse a merge |
| Honour `needs:`, `matrix`, `if:`, `env:` and `working-directory` | Give you a real `GITHUB_TOKEN` (pass one with `-s GITHUB_TOKEN="$(gh auth token)"` only if a step truly needs it) |
| Mask secrets you pass with `-s` | Provide OIDC tokens, GitHub's caches or `concurrency` cancelling |
| Show you a failure in seconds | Promise an identical machine: the image *resembles* GitHub's; the final word is GitHub's |

act sets `ACT=true` inside every job. A step that must never run locally — publishing a release,
say — can skip itself with `if: ${{ !env.ACT }}`. You will use that in Part 7.

---

## Part 4 — Secrets: masking, and where masking stops (10 min)

**1. Write a workflow that prints a secret — badly, on purpose.**

```bash
cat > .github/workflows/secrets-demo.yml <<'EOF'
name: Secrets demo

on: workflow_dispatch            # only runs when someone presses "Run workflow"

permissions:
  contents: read

jobs:
  show:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - name: Use a secret (badly, on purpose)
        env:
          DEMO_API_KEY: ${{ secrets.DEMO_API_KEY }}
        run: |
          echo "The key is: $DEMO_API_KEY"
          echo "The key, base64-encoded: $(printf '%s' "$DEMO_API_KEY" | base64)"
          echo "Running under act? ${ACT:-no}"
EOF
```
**What this does:** writes a workflow with one job that prints the secret twice — once as it is,
once **base64-encoded** (a reversible way of rewriting text that looks like gibberish). Copy the
whole box including the final `EOF`.

**2. Run it with a pretend secret.**

```bash
act workflow_dispatch -W .github/workflows/secrets-demo.yml -s DEMO_API_KEY=not-a-real-key-123
```
**What this does:** `-W` runs one specific workflow file; `-s NAME=value` supplies a secret. The log
shows:
```
| The key is: ***
| The key, base64-encoded: bm90LWEtcmVhbC1rZXktMTIz
| Running under act? true
```
The plain value is masked. **The encoded value is not.**

**3. Decode the "hidden" secret.**

```bash
echo bm90LWEtcmVhbC1rZXktMTIz | base64 -d; echo
```
**What this does:** `base64 -d` **d**ecodes, revealing `not-a-real-key-123`. The final `; echo`
just adds a line break so the next prompt is tidy. Anyone reading the log can do this.

> 🔴 **Masking is text-matching, not protection.** GitHub hides the *exact* secret text. Encode it,
> reverse it, print half of it, or write it to a file you upload as an artefact, and it is out.
> The rule is simple: **never print a secret, in any form.** If you must use a value derived from a
> secret, mask it first with `echo "::add-mask::$DERIVED"`.

Also worth knowing:
- **Pull requests from forks get no secrets** with the `pull_request` event. That is deliberate —
  a stranger's code would otherwise run with your keys.
- `pull_request_target` **does** get secrets, and runs in the context of *your* branch. Combine it
  with checking out the stranger's code and you have handed them your secrets. Avoid it unless you
  know exactly why you need it.

---

## Part 5 — Script injection: watch it happen, then close it (10 min)

### Step 5.1 — A useful check, written unsafely

**1. Write a workflow that checks pull-request titles.**

```bash
cat > .github/workflows/pr-title.yml <<'EOF'
name: PR title

on:
  pull_request:
    types: [opened, edited, synchronize]

permissions:
  contents: read

jobs:
  title:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - name: Check the title follows Conventional Commits (UNSAFE)
        run: |
          title="${{ github.event.pull_request.title }}"
          echo "Checking: $title"
          if ! printf '%s' "$title" | grep -Eq '^(feat|fix|docs|test|refactor|chore|ci|build)(\([a-z0-9-]+\))?: .+'; then
            echo "::error::PR title must look like 'feat(scope): what changed'"
            exit 1
          fi
EOF
```
**What this does:** writes a workflow that fails any pull request whose title does not look like
`feat: …` or `fix(api): …`. It *looks* fine. The problem is the line that pastes
`${{ github.event.pull_request.title }}` straight into the script.

**2. Keep a copy of the unsafe version.**

```bash
cp .github/workflows/pr-title.yml /tmp/pr-title-unsafe.yml
```
**What this does:** `cp` copies a file. You will feed this copy to the audit tools in Part 6, after
fixing the real one.

### Step 5.2 — Open a "pull request" with a nasty title

**1. Write the event GitHub would send, with an attacker's title.**

```bash
cat > /tmp/evil-pr.json <<'EOF'
{
  "pull_request": {
    "number": 7,
    "title": "feat: add refunds\"; echo \"INJECTED: this command came from the PR title\"; echo \"",
    "head": { "ref": "feature/refunds" },
    "base": { "ref": "main" }
  }
}
EOF
```
**What this does:** writes a small JSON file — the same kind of message GitHub sends a workflow when
a pull request is opened. The title contains quote marks and semicolons, which is the whole trick.

**2. Run the check against that event.**

```bash
act pull_request -W .github/workflows/pr-title.yml -e /tmp/evil-pr.json
```
**What this does:** `-e` gives act an **event file** instead of inventing one, so you control the
title. The log shows:
```
| INJECTED: this command came from the PR title
|
| Checking: feat: add refunds
```
**A line of the title ran as a command.** GitHub replaces `${{ … }}` with the text *before* the
shell sees the script, so the title's quote characters closed the string and the rest became code.
Here it only echoed. A real attacker would send your repository's token or secrets to their own
server — and the check would still pass.

### Step 5.3 — Close it: pass untrusted text through an environment variable

**1. Rewrite the workflow safely.**

```bash
cat > .github/workflows/pr-title.yml <<'EOF'
name: PR title

on:
  pull_request:
    types: [opened, edited, synchronize]

permissions:
  contents: read

jobs:
  title:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - name: Check the title follows Conventional Commits
        env:
          TITLE: ${{ github.event.pull_request.title }}   # data goes in an env var ...
        run: |                                            # ... and the script only reads it
          echo "Checking: $TITLE"
          if ! printf '%s' "$TITLE" | grep -Eq '^(feat|fix|docs|test|refactor|chore|ci|build)(\([a-z0-9-]+\))?: .+'; then
            echo "::error::PR title must look like 'feat(scope): what changed'"
            exit 1
          fi
EOF
```
**What this does:** overwrites the file with the safe version. The title now arrives as the
**value of a variable** called `TITLE`, and the script only reads that variable.

**2. Run the same attack again.**

```bash
act pull_request -W .github/workflows/pr-title.yml -e /tmp/evil-pr.json
```
**What this does:** the shell never treats a variable's contents as code, so the log prints the
whole title as harmless text: `Checking: feat: add refunds"; echo "INJECTED: …` — and nothing runs.

> 🔑 **Rule:** in a `run:` block, never write `${{ github.event.… }}`, `${{ github.head_ref }}` or
> anything else a stranger can type. Put it in `env:` and use `"$VAR"`.

**3. Build a second event file, with a title that is merely wrong.**

```bash
sed 's/feat: add refunds/Add refunds/' /tmp/evil-pr.json > /tmp/bad-title-pr.json
```
**What this does:** `sed 's/old/new/'` swaps one piece of text for another as the file passes
through, and `>` saves the result as a new file. The title no longer starts with `feat:`.

**4. Check that the rule still does its real job.**

```bash
act pull_request -W .github/workflows/pr-title.yml -e /tmp/bad-title-pr.json
```
**What this does:** the check fails as it should: `::error::PR title must look like
'feat(scope): what changed'` and `🏁  Job failed`. Safe **and** still useful.

---

## Part 6 — Let tools audit the pipeline (10 min)

People miss these problems in review. Two free tools do not.

**1. Move to the scratch folder.**

```bash
cd /tmp
```
**What this does:** the downloads below land here, not in your repository.

**2. Download actionlint.**

```bash
bash <(curl -sSfL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash) 1.7.12
```
**What this does:** downloads the actionlint project's own install script and runs it, asking for
version 1.7.12. `bash <(…)` means "run the output of this command as a script". It leaves a file
called `actionlint` in the current folder.

**3. Install it for everyone.**

```bash
sudo install -m 0755 actionlint /usr/local/bin/actionlint
```
**What this does:** `install` copies a file and sets its permissions in one go; `-m 0755` means
"everyone may run it, only the administrator may change it".

**4. Remove the downloaded copy.**

```bash
rm actionlint
```
**What this does:** deletes the leftover file from `/tmp`. The installed copy stays.

**5. Make a private Python environment for the second tool.**

```bash
python3 -m venv ~/.venvs/zizmor
```
**What this does:** a **virtual environment** is a self-contained folder with its own copy of
Python and its own packages, so installing something cannot disturb the system Python.

**6. Install zizmor into it.**

```bash
~/.venvs/zizmor/bin/pip install -q zizmor==1.30.1
```
**What this does:** installs exactly version 1.30.1 using that environment's own `pip`. `-q` keeps
it quiet.

**7. Make it runnable by name.**

```bash
sudo ln -sf ~/.venvs/zizmor/bin/zizmor /usr/local/bin/zizmor
```
**What this does:** `ln -s` creates a **symbolic link** — a signpost in `/usr/local/bin` pointing
at the real program — so you can type `zizmor` from anywhere. `-f` replaces an older signpost.

**8. Go back to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the audits below run on your workflow files.

**9. Check the first tool works.**

```bash
actionlint -version
```
**What this does:** prints `1.7.12`. actionlint checks workflow files for mistakes: bad YAML keys,
wrong expressions, and shell errors inside `run:` blocks.

**10. Check the second tool works.**

```bash
zizmor --version
```
**What this does:** prints `zizmor 1.30.1`. zizmor audits workflows for **security** problems.

**11. Point actionlint at the unsafe copy.**

```bash
actionlint /tmp/pr-title-unsafe.yml
```
**What this does:** reports `"github.event.pull_request.title" is potentially untrusted. avoid
using it directly in inline scripts. instead, pass it through an environment variable.` — exactly
the hole from Part 5, found automatically.

**12. Audit the unsafe copy and your real workflows.**

```bash
zizmor --offline /tmp/pr-title-unsafe.yml .github/workflows/
```
**What this does:** audits both, using no network (`--offline`). Expect findings like:

| Finding | Where | Means |
|---|---|---|
| `error[template-injection]` | the unsafe copy | Part 5's attack |
| `error[unpinned-uses]` | `ci.yml`, every `uses: …@v4` / `@v5` | A tag can be moved to different code — Part 8 fixes it |
| `warning[artipacked]` | `ci.yml`, each `actions/checkout` | The token is left in `.git/config` for later steps (and artefacts) to read — Part 7 fixes it |

The summary line reads like `… findings (…): 0 informational, 0 low, 2 medium, 6 high`. Your
`pr-title.yml` is **not** in the list any more — you already fixed it.

---

## Part 7 — Harden `ci.yml`, build once, version the artefact (15 min)

### Step 7.1 — One command to build: a `Makefile`

**1. Write the Makefile.**

```bash
cat > Makefile <<'EOF'
# PayTrack API - one command builds it the same way on a laptop, in act and in CI.
#   make          lint, test and build
#   make build    only package the artefact
.RECIPEPREFIX = >
PY      ?= python3
VENV    := app/.venv
VERSION := $(shell git describe --tags --always --dirty)
COMMIT  := $(shell git rev-parse HEAD)
ARTEFACT = paytrack-api-$(VERSION).tar.gz

.PHONY: all venv lint test build clean
all: lint test build

venv:
> test -d $(VENV) || $(PY) -m venv $(VENV)
> $(VENV)/bin/pip install -q -r app/requirements-dev.txt

lint: venv
> cd app && .venv/bin/flake8 src tests

test: venv
> cd app && .venv/bin/pytest --cov=src --cov-fail-under=70

build:
> rm -rf dist && mkdir -p dist
> printf 'version=%s\ncommit=%s\n' '$(VERSION)' '$(COMMIT)' > dist/BUILD_INFO
> tar -czf dist/$(ARTEFACT) --exclude=__pycache__ -C app src wsgi.py requirements.txt -C ../dist BUILD_INFO
> cd dist && sha256sum $(ARTEFACT) > $(ARTEFACT).sha256
> @echo "Built dist/$(ARTEFACT)"

clean:
> rm -rf dist $(VENV)
EOF
```
**What this does:** writes a **Makefile** — the classic build-automation file, understood by the
`make` command that has existed since 1976.
- A Makefile lists **targets** (`lint`, `test`, `build`) and the commands for each. `make` on its
  own runs `all`, which runs the three in order and **stops at the first failure**.
- `.RECIPEPREFIX = >` lets the commands start with `>` instead of a **Tab** character. Tabs are
  easily turned into spaces by copy and paste, which breaks a normal Makefile with
  `missing separator`.
- `VERSION` comes from `git describe`, which you met in Lab 03A: `v1.0.0-7-g4fa861d` means "7
  commits after v1.0.0, at commit 4fa861d". **Every artefact is named after exactly one commit.**
- `build` packs the app into `dist/paytrack-api-<version>.tar.gz`, adds a `BUILD_INFO` file
  recording the full commit hash, and writes a **SHA-256 checksum** beside it.

**2. Tell git to ignore the build folder.**

```bash
grep -qx 'dist/' .gitignore || echo 'dist/' >> .gitignore
```
**What this does:** `grep -qx 'dist/'` quietly asks "is there already a line that is exactly
`dist/`?"; `||` means "if not", and `>>` adds it. Built files should never be committed — they are
made from the code, not part of it.

**3. Ignore any local secrets file too.**

```bash
grep -qx '.secrets' .gitignore || echo '.secrets' >> .gitignore
```
**What this does:** the same for `.secrets`, the file act can read secrets from. Committing it
would publish them.

**4. Build the project.**

```bash
make
```
**What this does:** runs lint, then the tests, then the build — each in turn, stopping at the first
failure. The first run creates a virtual environment and installs packages, so it takes a minute.

✅ **Checkpoint:** the tests pass (`Required test coverage of 70% reached`, `19 passed`) and the
last line is like `Built dist/paytrack-api-v1.0.0-5-g0a8f72c-dirty.tar.gz`.

**Why `-dirty`?** You have files that are not committed yet (the Makefile itself, for a start), so
`git describe --dirty` marks the build. A dirty build cannot be traced to one exact commit, so it
must never be released. CI checks out a clean commit, so its builds never carry the mark.

**5. Go into the build folder.**

```bash
cd dist
```
**What this does:** moves into the folder `make build` created.

**6. Verify the artefact against its checksum.**

```bash
sha256sum -c *.sha256
```
**What this does:** `*` means "every file whose name ends like this". The command re-calculates the
archive's fingerprint and compares it with the recorded one, printing `…tar.gz: OK`. Whoever
deploys this later runs the same check and knows it is the file CI built.

**7. Go back up.**

```bash
cd ..
```
**What this does:** `..` means "the folder above this one" — back to the project root.

### Step 7.2 — The hardened pipeline

**1. Replace `ci.yml` with a hardened version.**

```bash
cat > .github/workflows/ci.yml <<'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

# Every job gets a read-only token unless it asks for more.
permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Lint & format
    runs-on: ubuntu-24.04
    timeout-minutes: 10                  # HARDENED: a hung job cannot burn minutes for hours
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false     # HARDENED: do not leave the token in .git/config

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: app/requirements-dev.txt

      - name: Install dependencies
        working-directory: app
        run: pip install -r requirements-dev.txt

      - name: flake8 (style and obvious errors)
        working-directory: app
        run: flake8 src tests

      - name: black --check (formatting)
        working-directory: app
        run: black --check --line-length 100 src tests
        continue-on-error: true

  test:
    name: Unit tests (py${{ matrix.python-version }})
    runs-on: ubuntu-24.04
    timeout-minutes: 15                  # HARDENED
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false     # HARDENED

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: app/requirements-dev.txt

      - name: Install dependencies
        working-directory: app
        run: pip install -r requirements-dev.txt

      - name: Run pytest with coverage
        working-directory: app
        run: |
          pytest -v \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            --junitxml=junit.xml

      - name: Enforce the coverage floor
        working-directory: app
        run: |
          COV=$(python -c "import xml.etree.ElementTree as E; \
            print(round(float(E.parse('coverage.xml').getroot().get('line-rate'))*100))")
          echo "Line coverage: ${COV}%"
          echo "### Coverage: ${COV}%" >> "$GITHUB_STEP_SUMMARY"
          if [ "$COV" -lt 70 ]; then
            echo "::error::Coverage ${COV}% is below the 70% floor"
            exit 1
          fi

      - name: Upload test artefacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-py${{ matrix.python-version }}
          path: |
            app/coverage.xml
            app/junit.xml
          retention-days: 7

  build:                                 # NEW: build the artefact once, name it after the commit
    name: Build the artefact
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0                 # full history and tags, so `git describe` can name the build
          persist-credentials: false

      - name: Build once
        run: make build

      - name: Upload the artefact
        uses: actions/upload-artifact@v4
        with:
          name: paytrack-api-${{ github.sha }}
          path: dist/
          retention-days: 7

  ci-passed:
    name: CI passed
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    needs: [lint, test, build]
    if: always()
    steps:
      - name: Verify all required jobs succeeded
        env:                             # HARDENED: expressions go in env, not inside the script
          LINT: ${{ needs.lint.result }}
          TEST: ${{ needs.test.result }}
          BUILD: ${{ needs.build.result }}
        run: |
          echo "lint=$LINT test=$TEST build=$BUILD"
          if [ "$LINT" != "success" ] || [ "$TEST" != "success" ] || [ "$BUILD" != "success" ]; then
            echo "::error::A required job failed - blocking the merge"
            exit 1
          fi
          echo "All CI jobs passed."
EOF
```
**What this does:** overwrites Lab 04's workflow with a hardened version. It is long, but every
change is one of these:

| Change | Why |
|---|---|
| `timeout-minutes` on every job | GitHub's default is **6 hours**. A hung test should cost minutes, not your monthly allowance |
| `persist-credentials: false` | Without it, checkout writes the job's token into `.git/config`, where every later step — and any artefact that includes `.git` — can read it |
| New `build` job with `needs: [lint, test]` | The artefact is built **once**, only from code that passed. Deployment later uses *this* file; it is never rebuilt |
| `fetch-depth: 0` in `build` | Checkout normally fetches one commit and no tags, so `git describe` would have nothing to count from |
| Artefact named `paytrack-api-${{ github.sha }}` | You can always find the build of a given commit |
| `ci-passed` also needs `build`, and reads results via `env:` | The required check still has the **same name**, so branch protection needs no change |

### Step 7.3 — A release, published from a tag

**1. Write the release workflow.**

```bash
cat > .github/workflows/release.yml <<'EOF'
name: Release

on:
  push:
    tags: ["v*.*.*"]                     # runs when you push a tag such as v1.1.0

permissions:
  contents: read                         # the default for every job in this file

jobs:
  release:
    name: Build and publish the release
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: write                    # ONLY this job may create a release
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: Build once
        run: make build

      - name: Publish the GitHub release
        if: ${{ !env.ACT }}              # act has no GitHub to publish to
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ github.ref_name }}
        run: gh release create "$TAG" dist/* --title "PayTrack API $TAG" --generate-notes --verify-tag
EOF
```
**What this does:** writes a second workflow that runs **only when a version tag is pushed**. It
builds with the same `make build` and publishes the files as a GitHub Release.
- `permissions: contents: write` sits on the **job**, not the file: the one step that needs write
  access gets it, and nothing else does.
- `--verify-tag` refuses to create a release if the tag is not really on GitHub.
- `if: ${{ !env.ACT }}` means you can rehearse the build with act without publishing anything.

### Step 7.4 — Check your work locally

**1. Check every workflow file is valid YAML.**

```bash
python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]; print('YAML is valid')"
```
**What this does:** reads every `.yml` file in that folder and tries to parse it. If one has broken
indentation you get an error naming the file and line; otherwise it prints `YAML is valid`.

**2. Run the linter over all of them.**

```bash
actionlint
```
**What this does:** with no file named, actionlint checks every workflow in the repository. **No
output means no problems.**

**3. List the jobs again.**

```bash
act -l
```
**What this does:** the table now shows **`build` in stage 1** and **`ci-passed` in stage 2**, plus
the `release`, `show` and `title` jobs from the other files.

**4. Run the new build job.**

```bash
act pull_request -j build
```
**What this does:** runs `build` — and, because of `needs:`, the `lint` and `test` jobs it depends
on — in containers on your machine. The artefact appears under `/tmp/act-artifacts`.

---

## Part 8 — Pin every action to a commit (5 min)

`actions/checkout@v4` means "whatever the `v4` tag points to **today**". Whoever controls that
repository can move the tag to different code, and your pipeline runs it with your token. A
40-character commit hash cannot be moved.

**1. Rewrite every `uses:` line to a commit hash.**

```bash
python3 - <<'PY'
import pathlib, re, subprocess

def commit_sha(repo, tag):
    out = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}",
                          f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
                         capture_output=True, text=True, check=True).stdout.split()
    return out[-2]          # for an annotated tag the last line (^{}) is the commit

USES = re.compile(r"uses: ([\w.-]+/[\w.-]+)@(v[\w.-]+)\s*$", re.M)
for wf in sorted(pathlib.Path(".github/workflows").glob("*.yml")):
    text = wf.read_text()
    for repo, tag in sorted(set(USES.findall(text))):
        sha = commit_sha(repo, tag)
        text = re.sub(rf"uses: {re.escape(repo)}@{re.escape(tag)}\s*$",
                      f"uses: {repo}@{sha} # {tag}", text, flags=re.M)
        print(f"{wf.name}: {repo}@{tag} -> {sha}")
    wf.write_text(text)
PY
```
**What this does:** one command — copy the whole box including the final `PY`. For every
`uses: owner/repo@vN` line in every workflow, it asks GitHub (with `git ls-remote`, which needs no
login) which **commit** that tag points to right now, and rewrites the line. It prints one line per
change.

**2. Look at the result.**

```bash
grep -n "uses:" .github/workflows/*.yml
```
**What this does:** prints every `uses:` line with its file and line number. They now read:
```
uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
```
The hash is what runs; the `# v4` comment tells humans — and Dependabot — which version it is.
Pinning does **not** upgrade anything: you run exactly the code you ran before, frozen. Your hashes
may differ from these if a maintainer has moved a tag since this was written — which is precisely
the point.

**3. Audit again.**

```bash
zizmor --offline .github/workflows/
```
**What this does:** re-runs the security audit. It now ends with **`No findings to report. Good
job!`**

**4. Lint again.**

```bash
actionlint
```
**What this does:** prints nothing — still clean.

> **Keeping pins current.** Lab 04 Step 7 enabled Dependabot for `github-actions`. It understands
> hash-plus-comment pins and opens pull requests that move both together — each one tested by the
> CI you just hardened. Expect PRs proposing newer major versions (`actions/checkout` is well past
> v4); read their release notes before merging.

---

## Part 9 — Ship it: pull request, a secret on GitHub, a tagged release (15 min)

### Step 9.1 — Pull request

**1. Stage your new and changed files by name.**

```bash
git add .actrc .gitignore Makefile .github/workflows/
```
**What this does:** stages exactly these four things. Naming them (instead of `git add .`) means a
stray file cannot slip in — and `dist/` and `.secrets` are ignored anyway.

**2. Check what is about to be committed.**

```bash
git status -s
```
**What this does:** staged files show a letter in the **first** column: `A` for added, `M` for
modified. Anything still in the second column is not part of this commit.

**3. Commit with a message that explains why.**

```bash
git commit -m "ci: run CI locally with act and harden the pipeline

Adds .actrc so the whole team runs the same act image, a Makefile that
builds a versioned artefact, a build job and a tag-triggered release
workflow. Pins every action to a commit, stops checkout persisting the
token, adds job timeouts, and adds a PR-title check that reads the title
from an environment variable. actionlint and zizmor report no findings."
```
**What this does:** one command spanning several lines — copy all of it, both quote marks included.
The first line is the summary; the paragraph after the blank line is the detail a reviewer reads.

**4. Push the branch to GitHub.**

```bash
git push -u origin ci/act-and-hardening
```
**What this does:** uploads the branch and remembers (`-u`) that it belongs with the branch of the
same name on GitHub.

> ⚠️ **Push rejected with** `refusing to allow an OAuth App to create or update workflow … without
> workflow scope`? Your `gh` login is not allowed to change workflow files. Run
> `gh auth refresh -s workflow` and push again.

**5. Open the pull request from the terminal.**

```bash
gh pr create --fill
```
**What this does:** `gh` is GitHub's own command-line tool. `--fill` takes the title and body
straight from your commit message, and prints a link to the new pull request.

**6. Watch the checks run.**

```bash
gh pr checks --watch
```
**What this does:** follows the pipeline live, updating as each job finishes. Press `Ctrl` + `C` to
stop watching.

✅ **Checkpoint:** `Lint & format`, both `Unit tests`, **`Build the artefact`**, `CI passed` and
`title` all pass. On the run's page (**Actions** tab), the **Artifacts** section now lists
`paytrack-api-<commit>` beside the test results. Merge the pull request as you did in Lab 04.

### Step 9.2 — The secret on GitHub

**1. Go back to the main branch.**

```bash
git switch main
```
**What this does:** you merged the pull request, so the work is on `main` now.

**2. Get the merged code.**

```bash
git pull
```
**What this does:** downloads the merge you just made on GitHub.

**3. Store a secret in the repository.**

```bash
gh secret set DEMO_API_KEY --body "not-a-real-key-123"
```
**What this does:** saves an **encrypted repository secret**. Settings → Secrets and variables →
Actions will list its name — but never show its value again, not even to you.

**4. Start the demo workflow.**

```bash
gh workflow run secrets-demo.yml
```
**What this does:** presses "Run workflow" from the terminal. A `workflow_dispatch` workflow can
only be started once it is on the default branch, which is why you merged first.

**5. Find the run.**

```bash
gh run list --workflow secrets-demo.yml --limit 1
```
**What this does:** lists the newest run of that workflow. If the list is empty, wait a few seconds
and run it again — GitHub takes a moment to queue it.

**6. Follow it.**

```bash
gh run watch
```
**What this does:** asks you to pick the run with the arrow keys, then follows it until it finishes.

**7. Read the secret lines from the log.**

```bash
gh run view --log | grep "The key"
```
**What this does:** downloads the run's log and `grep` keeps only the lines containing "The key".
**GitHub behaves exactly as act did:** `The key is: ***`, and the base64 line in plain text.

### Step 9.3 — A release, built once and verified

**1. Tag the release.**

```bash
git tag -a v1.1.0 -m "PayTrack API 1.1.0"
```
**What this does:** creates an annotated tag on the merged `main` — a permanent name for this exact
commit.

**2. Push the tag.**

```bash
git push origin v1.1.0
```
**What this does:** tags are not pushed by `git push` on its own; you name them. This push matches
`tags: ["v*.*.*"]`, so the **Release** workflow starts.

**3. Watch the release run.**

```bash
gh run watch
```
**What this does:** pick the `Release` run. It builds the artefact and publishes it.

**4. Look at the release.**

```bash
gh release view v1.1.0
```
**What this does:** shows the release page in the terminal, including the three files attached to
it: the archive, its checksum and `BUILD_INFO`.

**5. Download it to a scratch folder.**

```bash
gh release download v1.1.0 --dir /tmp/release-check --clobber
```
**What this does:** downloads every file of the release into `/tmp/release-check`. `--clobber`
overwrites anything already there from a previous attempt.

**6. Go to that folder.**

```bash
cd /tmp/release-check
```
**What this does:** moves in, so the next command finds the files.

**7. Verify the checksum.**

```bash
sha256sum -c ./*.sha256
```
**What this does:** prints `paytrack-api-v1.1.0.tar.gz: OK` — proof the file you downloaded is
byte-for-byte the file CI built.

**8. Read the build record from inside the archive.**

```bash
tar -xzOf paytrack-api-v1.1.0.tar.gz BUILD_INFO
```
**What this does:** `-O` prints a file from inside the archive to the screen instead of unpacking
it. You see `version=v1.1.0` and the exact commit hash. Anyone deploying this release can prove
which commit it came from.

**9. Go back to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** leaves the scratch folder behind.

---

## The pipeline-security checklist — what you did

| The slide says | Where you did it |
|---|---|
| Pin third-party Actions to a full commit SHA | Part 8 |
| Least-privilege `permissions:` | `contents: read` for every file; `contents: write` only on the release job (Step 7.3) |
| Never expose secrets to pull requests from forks | Part 4: `pull_request`, not `pull_request_target` |
| Treat anything a user can type as data, not code | Part 5 |
| CODEOWNERS on `.github/workflows/` | Lab 03 Part 5 |
| Ephemeral runners — one job per runner | GitHub-hosted runners, and act's containers, are thrown away after each job |
| Short-lived OIDC tokens instead of stored secrets | Not here — it needs a cloud account. The idea: `permissions: id-token: write`, and the cloud trusts GitHub's token for *this* repository and branch, so no long-lived key is stored at all |
| *(extra)* No token left on disk, timeouts, automated audits | Parts 6–8 |

---

## 🧩 Stretch (homework)

1. **Audit in CI.** Add a job to `ci.yml` that installs pinned `actionlint` and `zizmor` and runs
   them on every pull request, so an unsafe workflow change cannot be merged.
2. **See a flaky test.** Add `app/tests/test_flaky.py` containing
   `import random` and `def test_sometimes(): assert random.random() > 0.3`, then run
   `for i in $(seq 10); do act pull_request -j test --matrix python-version:3.12 >/dev/null 2>&1 && echo pass || echo FAIL; done`.
   Count the reds, delete the file, and decide what your team's rule for flaky tests is.
3. **Rehearse the release.** Write `{"ref": "refs/tags/v9.9.9"}` to `/tmp/tag.json` and run
   `act push -W .github/workflows/release.yml -e /tmp/tag.json`. The build runs; the publish step
   skips itself because `ACT` is set.
4. **Watch the timeout work.** Add a step `run: sleep 600` to a copy of a job with
   `timeout-minutes: 1` and run it on GitHub.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running, or your user is not in the `docker` group | Start Docker; log out and back in (Lab 00 Step 2) |
| act asks you to choose an image size | No `-P` option found | Run act from the repository root, where `.actrc` lives |
| `Unable to get the ACTIONS_RUNTIME_TOKEN env variable` | `upload-artifact` with no local artefact server | Keep `--artifact-server-path` in `.actrc` |
| Odd failures on an ARM machine (Apple silicon, Multipass on a Mac) | An action or tool has no ARM build | Add `--container-architecture linux/amd64` to `.actrc` — slower, but emulates GitHub's machines |
| `$ACT_ARCH` or `$ACT_VERSION` is empty | You opened a new terminal window since setting it | Re-run those two commands in the window you are using |
| `make: *** missing separator` | The `.RECIPEPREFIX` line is missing, or a very old `make` | Re-create the Makefile from Step 7.1; `make --version` should be 4.x |
| `sha256sum: command not found` | You are on macOS, not Ubuntu | `shasum -a 256` does the same |
| `Permission denied` writing to `/usr/local/bin` | The `sudo` was left off | Run the command again with `sudo` in front |
| zizmor still reports `unpinned-uses` | A `uses:` line the script did not match, such as a branch (`@main`) | Pin it by hand: find the commit with `git ls-remote https://github.com/<owner>/<repo>` |
| `gh release create` fails with `403` | The job has no `contents: write` | Check the `permissions:` block on the `release` job |
| `refusing to allow an OAuth App to create or update workflow` | `gh` token lacks the `workflow` scope | `gh auth refresh -s workflow` |

---

## 🎯 Outcome

You can run any workflow in seconds without pushing, you have **seen** secret masking fail and a
pull-request title execute code, and your repository now has a pipeline that is pinned, time-boxed,
least-privileged, audited, and builds **one** checksummed, commit-named artefact that a tag turns
into a release.

**Next:** [Lab 04B — The same pipeline on GitLab CI](../lab-04b-gitlab-ci/README.md), or
[Lab 05 — Jenkins CI](../lab-05-jenkins-ci/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Pre-pull the image.** `docker pull catthehacker/ubuntu:act-24.04` on every machine before the
  session; on conference Wi-Fi the first `act` run is otherwise the whole lab.
- **Part 5 is the one to demo.** Put the `INJECTED` line on the projector, then ask who has a
  workflow that echoes a branch name or PR title. Most hands go up.
- **Things that go wrong:**
  1. Docker group not applied — `act` fails immediately. Same fix as Lab 00.
  2. ARM laptops: most jobs work natively; if `setup-python` fails, add
     `--container-architecture linux/amd64`.
  3. The workflow-scope push rejection in Step 9.1 — have `gh auth refresh -s workflow` on a slide.
  4. Variables (`ACT_ARCH`) set in one terminal window and used in another. Tell them to keep one
     window open for the whole lab.
- **Debrief question:** "Your pipeline holds credentials to production. Who reviewed the last
  change to it, and would they have spotted Part 5?"
</details>
