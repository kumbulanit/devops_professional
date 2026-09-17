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

🔁 **RECOVER**
```bash
cd ~/devops-course
[ -d paytrack-api-team ] || git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-team
cd paytrack-api-team && git switch main && git pull
ls .github/workflows/ci.yml
```
**What this does:** makes sure you have a clone of **your** repository, on an up-to-date `main`,
and that Lab 04's workflow is in it. If `ls` says *No such file*, finish Lab 04 first.

## Words you need

| Word | Plain meaning |
|---|---|
| **act** | A free tool that reads `.github/workflows/*.yml` and runs the jobs in Docker on your machine |
| **Runner image** | The container that pretends to be GitHub's `ubuntu-24.04` machine |
| **Event** | What started the workflow: `push`, `pull_request`, `workflow_dispatch`… act needs you to name one |
| **Masking** | GitHub (and act) replacing a secret's exact text with `***` in logs |
| **Script injection** | Text from outside (a PR title, a branch name) being run as a command |
| **Pinning** | Referring to an action by its full commit hash, which cannot be moved, instead of a tag such as `v4`, which can |
| **Artefact** | The file a build produces — here, a `.tar.gz` of the app |

---

## Part 1 — Install act (10 min)

```bash
act --version || echo "act is not installed yet"
```
**What this does:** prints `act version 0.2.89` if act is already installed (Lab 00 Step 8.4 or the
course installer does it). If you see *not installed*, run the next block.

```bash
ACT_VERSION=0.2.89
ACT_ARCH=$(uname -m | sed 's/aarch64/arm64/')
cd /tmp
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/act_Linux_${ACT_ARCH}.tar.gz"
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/checksums.txt"
grep " act_Linux_${ACT_ARCH}.tar.gz\$" checksums.txt | sha256sum -c -
sudo tar -xzf "act_Linux_${ACT_ARCH}.tar.gz" -C /usr/local/bin act
act --version
cd ~/devops-course/paytrack-api-team
```
**What this does, line by line:**
- Pins the version, and turns your CPU name into act's naming (`x86_64` stays; `aarch64` becomes
  `arm64`).
- Downloads the release **and** the project's list of checksums.
- `sha256sum -c` recalculates the download's fingerprint and compares it with the published one.
  You must see `act_Linux_x86_64.tar.gz: OK` (or `arm64`). **If it says FAILED, stop** — the file
  is not what the project published.
- Extracts only the `act` binary into `/usr/local/bin`, then checks it runs.

This is the safe version of `curl | bash` from Lab 00: download, **verify**, then install.

> **Other ways in:** `gh extension install nektos/gh-act` gives you `gh act`; on a Mac,
> `brew install act`. The commands below are the same.

```bash
docker info --format 'Docker {{.ServerVersion}} is running'
```
**What this does:** confirms act will be able to start containers. If you get *permission denied*,
log out and back in (Lab 00 Step 2).

---

## Part 2 — Run your pipeline on your laptop (15 min)

### Step 2.1 — Tell act which image stands in for GitHub's machine

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
git switch -c ci/act-and-hardening
cat > .actrc <<'EOF'
-P ubuntu-24.04=catthehacker/ubuntu:act-24.04
--artifact-server-path /tmp/act-artifacts
EOF
```
**What this does:** starts a branch for everything in this lab, and writes `.actrc` — the options
act reads every time it starts in this folder. Committing it means everyone on the team runs the
same image.
- `-P ubuntu-24.04=…` — "when a job says `runs-on: ubuntu-24.04`, use this image". The
  `catthehacker` images are built to resemble GitHub's runners and are the ones the act project
  recommends. Without this line, act stops on first use and asks you to choose.
- `--artifact-server-path` — starts a small local stand-in for GitHub's artefact storage, so
  `actions/upload-artifact` works. Files land in `/tmp/act-artifacts`.

### Step 2.2 — See what act found

```bash
act -l
```
**What this does:** **lists** the jobs without running anything:
```
Stage  Job ID     Job name                                     Workflow name  Workflow file  Events
0      lint       Lint & format                                CI             ci.yml         push,pull_request,workflow_dispatch
0      test       Unit tests (py${{ matrix.python-version }})  CI             ci.yml         push,pull_request,workflow_dispatch
1      ci-passed  CI passed                                    CI             ci.yml         push,pull_request,workflow_dispatch
```
**Stage 0** jobs run in parallel; **stage 1** waits for them — that is `needs: [lint, test]`. On an
Apple-silicon or ARM machine you may also see a warning about container architecture; ignore it
unless a job fails (see Troubleshooting).

### Step 2.3 — Run one job

```bash
act pull_request -j lint
```
**What this does:** pretends a **pull request** was opened (`pull_request` is the event) and runs
only the job whose id is `lint` (`-j`). **The first run downloads the runner image — more than a
gigabyte, once — so give it a few minutes.** Then read the log:

| You see | Means |
|---|---|
| `[CI/Lint & format] ⭐ Run Main flake8 …` | A step starting. The prefix is `[workflow/job]` |
| `\| …` | Output of the command inside the step |
| `✅  Success - Main flake8 …` | The step passed |
| `❌  Failure - Main …` | The step failed |
| `🏁  Job succeeded` | The whole job passed |

### Step 2.4 — Run one leg of the matrix, then everything

```bash
act pull_request -j test --matrix python-version:3.12
```
**What this does:** runs the `test` job for **Python 3.12 only**. `--matrix key:value` picks one
combination instead of all of them — handy when one version fails.

```bash
act pull_request
ls -R /tmp/act-artifacts | head -20
```
**What this does:** runs **every** job for a pull request: lint and both test legs, then
`ci-passed`. The `ls` shows the coverage and JUnit files that `upload-artifact` saved to the local
artefact server.

✅ **Checkpoint:** the last job prints `All CI jobs passed.` and `🏁  Job succeeded`.

---

## Part 3 — Break it before anyone sees (5 min)

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
git status -s
act pull_request -j test --matrix python-version:3.12
```
**What this does:** makes the same break as Lab 04 Step 6, **without committing it**, and runs the
tests with act. The job fails — `❌  Failure - Main Run pytest with coverage` and `🏁  Job failed` —
and `act` exits with a non-zero code.

> 🔑 **act runs the files in your folder, not your last commit.** Uncommitted edits are included.
> That is what makes it a fast feedback loop: no commit, no push, no waiting for a runner.

```bash
git restore app/src/app.py
git status -s
```
**What this does:** undoes the break. `git status -s` now lists only `?? .actrc`, the file you
created in Step 2.1.

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
act workflow_dispatch -W .github/workflows/secrets-demo.yml -s DEMO_API_KEY=not-a-real-key-123
```
**What this does:** writes a workflow that prints a secret twice — once as it is, once
base64-encoded — then runs it with act. `-W` picks one workflow file; `-s NAME=value` supplies a
secret. The log shows:
```
| The key is: ***
| The key, base64-encoded: bm90LWEtcmVhbC1rZXktMTIz
| Running under act? true
```
The plain value is masked. **The encoded value is not** — and anyone can decode it:

```bash
echo bm90LWEtcmVhbC1rZXktMTIz | base64 -d; echo
```
**What this does:** decodes the "hidden" secret: `not-a-real-key-123`.

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
cp .github/workflows/pr-title.yml /tmp/pr-title-unsafe.yml
```
**What this does:** a workflow that fails a pull request whose title does not look like
`feat: …` or `fix(api): …`. It *looks* fine. The last line keeps a copy of this version for Part 6.

### Step 5.2 — Open a "pull request" with a nasty title

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
act pull_request -W .github/workflows/pr-title.yml -e /tmp/evil-pr.json
```
**What this does:** `-e` gives act an **event file** — the JSON GitHub would send when a pull
request is opened — so you control the title. The log shows:
```
| INJECTED: this command came from the PR title
|
| Checking: feat: add refunds
```
**A line of the title ran as a command.** GitHub replaces `${{ … }}` with the text *before* the
shell sees the script, so the title's quote characters closed the string and the rest became code.
Here it only echoed. A real attacker would send your repository's token or secrets to their own
server, and the check would still pass.

### Step 5.3 — Close it: pass untrusted text through an environment variable

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
act pull_request -W .github/workflows/pr-title.yml -e /tmp/evil-pr.json
```
**What this does:** the title now arrives as the **value of a variable**, `$TITLE`. The shell never
treats a variable's contents as code, so the log prints the whole title as harmless text:
`Checking: feat: add refunds"; echo "INJECTED: …` — and nothing runs.

> 🔑 **Rule:** in a `run:` block, never write `${{ github.event.… }}`, `${{ github.head_ref }}` or
> anything else a stranger can type. Put it in `env:` and use `"$VAR"`.

```bash
sed 's/feat: add refunds/Add refunds/' /tmp/evil-pr.json > /tmp/bad-title-pr.json
act pull_request -W .github/workflows/pr-title.yml -e /tmp/bad-title-pr.json
```
**What this does:** a title that does not start with `feat:` and friends. The check does its real
job: `::error::PR title must look like 'feat(scope): what changed'` and `🏁  Job failed`.

---

## Part 6 — Let tools audit the pipeline (10 min)

People miss these problems in review. Two free tools do not.

```bash
cd /tmp
bash <(curl -sSfL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash) 1.7.12
sudo install -m 0755 actionlint /usr/local/bin/actionlint && rm actionlint
python3 -m venv ~/.venvs/zizmor
~/.venvs/zizmor/bin/pip install -q zizmor==1.30.1
sudo ln -sf ~/.venvs/zizmor/bin/zizmor /usr/local/bin/zizmor
cd ~/devops-course/paytrack-api-team
actionlint -version && zizmor --version
```
**What this does:** installs two pinned tools.
- **actionlint** checks workflow files for mistakes: bad YAML keys, wrong expressions, and shell
  errors inside `run:` blocks.
- **zizmor** audits workflows for **security** problems.
The download script comes from the actionlint project and fetches the release for your machine;
zizmor goes into its own virtual environment so it cannot disturb the system Python.

```bash
actionlint /tmp/pr-title-unsafe.yml
```
**What this does:** checks the unsafe copy you saved in Step 5.1. It reports:
`"github.event.pull_request.title" is potentially untrusted. avoid using it directly in inline
scripts. instead, pass it through an environment variable.` That is exactly the hole from Part 5.

```bash
zizmor --offline /tmp/pr-title-unsafe.yml .github/workflows/
```
**What this does:** audits the unsafe copy **and** your real workflows. `--offline` uses no
network. Expect findings like:

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
grep -qx 'dist/' .gitignore || echo 'dist/' >> .gitignore
grep -qx '.secrets' .gitignore || echo '.secrets' >> .gitignore
make
```
**What this does:** writes a **Makefile** — the classic build-automation file — and runs it.
- A Makefile lists **targets** (`lint`, `test`, `build`) and the commands for each. `make` alone
  runs `all`, which runs the three in order and **stops at the first failure**.
- `.RECIPEPREFIX = >` lets the commands start with `>` instead of a **Tab** character. Tabs are
  easily turned into spaces by copy and paste, which breaks a normal Makefile with
  `missing separator`.
- `VERSION` comes from `git describe`, which you met in Lab 03A: `v1.0.0-7-g4fa861d` means "7
  commits after v1.0.0, at commit 4fa861d". **Every artefact is named after exactly one commit.**
- `build` packs the app into `dist/paytrack-api-<version>.tar.gz`, adds a `BUILD_INFO` file
  recording the full commit hash, and writes a **SHA-256 checksum** beside it.
- The two `grep … || echo …` lines add `dist/` and `.secrets` to `.gitignore`, once.

✅ **Checkpoint:** the tests pass (`Required test coverage of 70% reached`, `19 passed`) and the
last line is like `Built dist/paytrack-api-v1.0.0-5-g0a8f72c-dirty.tar.gz`.

**Why `-dirty`?** You have files that are not committed yet (the Makefile itself, for a start), so
`git describe --dirty` marks the build. A dirty build can never be traced to one exact commit, so
it must never be released. CI checks out a clean commit, so its builds never carry the mark.

```bash
cd dist && sha256sum -c *.sha256 && cd ..
```
**What this does:** verifies the artefact against its checksum: `…tar.gz: OK`. Whoever deploys it
later runs the same check, and knows it is the file CI built.

### Step 7.2 — The hardened pipeline

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
**What changed from Lab 04, and why:**

| Change | Why |
|---|---|
| `timeout-minutes` on every job | GitHub's default is **6 hours**. A hung test should cost minutes, not your monthly allowance |
| `persist-credentials: false` | Without it, checkout writes the job's token into `.git/config`, where every later step — and any artefact that includes `.git` — can read it |
| New `build` job with `needs: [lint, test]` | The artefact is built **once**, only from code that passed. Deployment later uses *this* file; it is never rebuilt |
| `fetch-depth: 0` in `build` | Checkout normally fetches one commit and no tags, so `git describe` would have nothing to count from |
| Artefact named `paytrack-api-${{ github.sha }}` | You can always find the build of a given commit |
| `ci-passed` also needs `build`, and reads results via `env:` | The required check still has the **same name**, so branch protection needs no change |

### Step 7.3 — A release, published from a tag

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
**What this does:** a second workflow that runs **only when a version tag is pushed**. It builds
with the same `make build` and publishes the files as a GitHub Release.
- `permissions: contents: write` sits on the **job**, not the file: the one step that needs write
  access gets it, and nothing else does.
- `--verify-tag` refuses to create a release if the tag is not really on GitHub.
- `if: ${{ !env.ACT }}` means you can rehearse the build with act without publishing anything.

### Step 7.4 — Check your work locally

```bash
python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]; print('YAML is valid')"
actionlint
act -l
```
**What this does:** parses every workflow file, runs actionlint over all of them (no output means
no problems), and lists the jobs. `act -l` now shows **`build` in stage 1** and **`ci-passed` in
stage 2**, plus the `release`, `show` and `title` jobs from the other files.

```bash
act pull_request -j build
```
**What this does:** runs the `build` job — and, because of `needs:`, the `lint` and `test` jobs it
depends on — in act. The artefact appears under `/tmp/act-artifacts`.

---

## Part 8 — Pin every action to a commit (5 min)

`actions/checkout@v4` means "whatever the `v4` tag points to **today**". Whoever controls that
repository can move the tag to different code, and your pipeline runs it with your token. A
40-character commit hash cannot be moved.

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
grep -n "uses:" .github/workflows/*.yml
```
**What this does:** for every `uses: owner/repo@vN` line in every workflow, asks GitHub (with
`git ls-remote`, which needs no login) which **commit** the tag points to right now, and rewrites
the line as:
```
uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
```
The hash is what runs; the `# v4` comment tells humans — and Dependabot — which version it is.
Pinning does **not** upgrade anything: you run exactly the code you ran before, frozen. Your
hashes may differ if a maintainer has moved a tag since this was written — which is precisely the
point.

```bash
zizmor --offline .github/workflows/
actionlint
```
**What this does:** re-audits. zizmor now ends with **`No findings to report. Good job!`** and
actionlint prints nothing.

> **Keeping pins current.** Lab 04 Step 7 enabled Dependabot for `github-actions`. It understands
> hash-plus-comment pins and opens pull requests that move both together — each one tested by the
> CI you just hardened. Expect PRs proposing newer major versions (`actions/checkout` is well past
> v4); read their release notes before merging.

---

## Part 9 — Ship it: pull request, a secret on GitHub, a tagged release (15 min)

### Step 9.1 — Pull request

```bash
git add .actrc .gitignore Makefile .github/workflows/
git status -s
git commit -m "ci: run CI locally with act and harden the pipeline

Adds .actrc so the whole team runs the same act image, a Makefile that
builds a versioned artefact, a build job and a tag-triggered release
workflow. Pins every action to a commit, stops checkout persisting the
token, adds job timeouts, and adds a PR-title check that reads the title
from an environment variable. actionlint and zizmor report no findings."
git push -u origin ci/act-and-hardening
gh pr create --fill
gh pr checks --watch
```
**What this does:** commits everything **by name** (`.secrets` and `dist/` are ignored, so they
cannot slip in), pushes the branch, opens a pull request whose title and body come from the commit
(`--fill`), and follows the checks live.

✅ **Checkpoint:** `Lint & format`, both `Unit tests`, **`Build the artefact`**, `CI passed` and
`title` all pass. On the run's page (**Actions** tab), the **Artifacts** section now lists
`paytrack-api-<commit>` beside the test results. Merge the PR as you did in Lab 04.

> ⚠️ **Push rejected with** `refusing to allow an OAuth App to create or update workflow … without
> workflow scope`? Your `gh` login cannot change workflow files. Run `gh auth refresh -s workflow`
> and push again.

### Step 9.2 — The secret on GitHub

```bash
git switch main && git pull
gh secret set DEMO_API_KEY --body "not-a-real-key-123"
gh workflow run secrets-demo.yml
```
**What this does:** stores an **encrypted repository secret** (Settings → Secrets and variables →
Actions shows it, but never its value again), then presses "Run workflow" from the terminal. A
`workflow_dispatch` workflow can only be run once it is on the default branch — which is why you
merged first.

```bash
gh run list --workflow secrets-demo.yml --limit 1
gh run watch
gh run view --log | grep "The key"
```
**What this does:** `gh run list` shows the run once GitHub has queued it (repeat it if the list is
empty). `gh run watch` and `gh run view` ask you to pick the run, then follow it and print its
log. **GitHub behaves exactly as act did:** `The key is: ***`, and the base64 line in plain text.

### Step 9.3 — A release, built once and verified

```bash
git tag -a v1.1.0 -m "PayTrack API 1.1.0"
git push origin v1.1.0
gh run watch
```
**What this does:** creates an annotated tag on the merged `main` and pushes it. The push matches
`tags: ["v*.*.*"]`, so the **Release** workflow starts; pick it in `gh run watch`.

```bash
gh release view v1.1.0
gh release download v1.1.0 --dir /tmp/release-check --clobber
cd /tmp/release-check && sha256sum -c ./*.sha256 && tar -xzOf paytrack-api-v1.1.0.tar.gz BUILD_INFO; cd ~/devops-course/paytrack-api-team
```
**What this does:** shows the release and its three files, downloads them to a scratch folder,
**verifies the checksum** (`paytrack-api-v1.1.0.tar.gz: OK`), and prints `BUILD_INFO` from inside
the archive — `version=v1.1.0` and the exact commit. Anyone deploying this release can prove it is
the file CI built from that commit.

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
| `make: *** missing separator` | The `.RECIPEPREFIX` line is missing, or a very old `make` | Re-create the Makefile from Step 7.1; `make --version` should be 4.x |
| `sha256sum: command not found` | macOS | `shasum -a 256` does the same |
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
- **Debrief question:** "Your pipeline holds credentials to production. Who reviewed the last
  change to it, and would they have spotted Part 5?"
</details>
