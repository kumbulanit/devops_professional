# Lab 04 — Build a CI Pipeline with GitHub Actions

| | |
|---|---|
| **Day** | 2 |
| **Duration** | 35 minutes |
| **Module** | 2 — Version Control and CI |
| **You will produce** | `.github/workflows/ci.yml` — a lint + test + coverage pipeline gating every PR |
| **Feeds into** | Lab 06 (adds the image build), Lab 15 (adds deployment), Lab 17 (adds security gates) |

---

## Objective

Make it **impossible to merge a broken change**. You will build a real CI pipeline that runs
on every push and pull request, wire it into branch protection as a required status check,
then prove it works by trying to merge something broken.

**Free tier used:** GitHub Actions — **unlimited minutes on public repositories**, 2 000
minutes/month on private repositories on the Free plan.

## Prerequisites

- Lab 03 complete: `paytrack-api` on GitHub with branch protection

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction is **one command in one grey box**, numbered in
the order you run it. This lab moves between the **terminal** and the **GitHub website**; each
instruction says which.

- **Open a terminal** with `Ctrl` + `Alt` + `T`; it shows a line ending in `$`, the prompt.
- **Run a command:** click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press
  `Enter`, and wait for the prompt to come back.
- **Most boxes print nothing** when they succeed.
- **A box that starts `cat > … <<'EOF'` or `python3 - <<'PY'` is one command** — copy all of it,
  including the last line, and press `Enter` once.
- **Replace `<your-username>`** (angle brackets included) with your GitHub username.
- Symbols: `~` home folder · `cd` move into a folder · `>` write a file · `|` pass output on ·
  `&&` only if that worked · `||` only if that failed.

🔁 **RECOVER — if you do not have the team clone**

```bash
cd ~/devops-course
```
**What this does:** moves into the folder that holds your work.

```bash
git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-team 2>/dev/null
```
**What this does:** clones your repository into `paytrack-api-team`. `2>/dev/null` hides the error
if the folder already exists.

```bash
cd paytrack-api-team
```
**What this does:** moves into the clone.

```bash
git switch main
```
**What this does:** puts you on the main branch.

```bash
git pull
```
**What this does:** downloads anything merged since your last pull.

---

## Step 1 — Understand the anatomy before writing YAML

```
 EVENT      push / pull_request / schedule / workflow_dispatch
   └── WORKFLOW    one YAML file in .github/workflows/
         └── JOB         runs on ONE runner; jobs run in PARALLEL unless `needs:` says otherwise
               └── STEP        sequential within a job
                     ├── run:   a shell command
                     └── uses:  a reusable Action
```

**1. Go to your clone.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command in this lab runs from here unless it says otherwise.

**2. Go to the main branch.**

```bash
git switch main
```
**What this does:** start the new branch from the mainline, not from leftover work.

**3. Update it.**

```bash
git pull
```
**What this does:** downloads everything merged in Lab 03.

**4. Create a branch for the pipeline.**

```bash
git switch -c ci/add-github-actions
```
**What this does:** `-c` creates the branch and moves you onto it. **The pipeline is code**, so it
goes through the same review process as everything else.

**5. Create the folder GitHub looks in.**

```bash
mkdir -p .github/workflows
```
**What this does:** creates the folder (and its parent). **The path `.github/workflows/` is
fixed** — GitHub will not find workflows anywhere else.

---

## Step 2 — Write the pipeline

**1. Write the workflow file.** This box is **one command** — copy every line of it, including
the final `EOF`, and press `Enter` once. Nothing is printed.

```bash
cat > .github/workflows/ci.yml <<'EOF'
name: CI

# ── WHEN does this run? ────────────────────────────────────────────────────────
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:          # adds a "Run workflow" button in the Actions tab

# ── Least privilege for the automatic GITHUB_TOKEN ────────────────────────────
permissions:
  contents: read

# ── Cancel superseded runs on the same branch: saves minutes, gives faster feedback
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"

jobs:
  # ═══════════════════════════════════════════════════════════════════════════
  lint:
    name: Lint & format
    runs-on: ubuntu-24.04
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

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
        continue-on-error: true       # advisory on day 2; make it blocking once the team agrees

  # ═══════════════════════════════════════════════════════════════════════════
  test:
    name: Unit tests (py${{ matrix.python-version }})
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false                # let every matrix leg finish, so you see ALL failures
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

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
        if: always()                  # run even when a previous step failed - that is when you need them
        with:
          name: test-results-py${{ matrix.python-version }}
          path: |
            app/coverage.xml
            app/junit.xml
          retention-days: 7

  # ═══════════════════════════════════════════════════════════════════════════
  ci-passed:
    name: CI passed
    runs-on: ubuntu-24.04
    needs: [lint, test]              # this job is the DAG edge that makes the others gates
    if: always()
    steps:
      - name: Verify all required jobs succeeded
        run: |
          if [ "${{ needs.lint.result }}" != "success" ] || \
             [ "${{ needs.test.result }}" != "success" ]; then
            echo "::error::A required job failed - blocking the merge"
            exit 1
          fi
          echo "All CI jobs passed."
EOF
```

**What every part of that does:**

| Key | Meaning |
|---|---|
| `on.push` / `on.pull_request` | Triggers. **Both matter**: `pull_request` gates the merge, `push` verifies `main` itself is healthy |
| `workflow_dispatch` | Adds a manual "Run workflow" button — invaluable for debugging |
| `permissions: contents: read` | **Least privilege.** The auto-provisioned `GITHUB_TOKEN` defaults to broad write access; this restricts it to what the job needs |
| `concurrency` + `cancel-in-progress` | A second push to the same branch cancels the first run. Saves minutes and shortens feedback |
| `runs-on: ubuntu-24.04` | Pins the runner image. `ubuntu-latest` silently changes underneath you |
| `uses: actions/checkout@v4` | The repo is **not** on the runner by default. Nothing works without this step |
| `cache: pip` | Caches the wheel download between runs — typically 30–60 s saved per job |
| `working-directory: app` | Runs the step inside `app/`, so paths in `pytest.ini` and `.flake8` resolve |
| `strategy.matrix` | Runs the whole job once per Python version, in parallel |
| `fail-fast: false` | Without it, one failing leg cancels the others and hides information |
| `continue-on-error: true` | The step reports failure but does not fail the job — for advisory checks |
| `$GITHUB_STEP_SUMMARY` | Anything appended here renders as markdown on the run's summary page |
| `::error::` | A **workflow command** — annotates the specific line in the GitHub UI |
| `if: always()` | Runs the step even after an earlier failure |
| `needs: [lint, test]` | Turns parallel jobs into a dependency graph |
| `ci-passed` job | **One** stable check name to require in branch protection, so adding a matrix leg later does not break the rule |

> ⚠️ **Supply-chain note.** `uses: actions/checkout@v4` is a *mutable* tag: whoever controls
> that repository can change what `v4` points to, and it runs in your pipeline with your
> token. For production, pin the full commit SHA
> (`uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608`) and let Dependabot
> bump it. You will apply this in Lab 17.

---

## Step 3 — Validate before pushing

**1. Check the file is valid YAML.**

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML is valid')"
```
**What this does:** reads the file the way GitHub will. **Indentation errors are the number one
cause of "my workflow does not appear"** — GitHub silently ignores files it cannot parse. Catching
it here saves a push-and-wait cycle.

Now run locally exactly what CI will run. **If it fails here it will fail there** — and finding
out in 3 seconds beats finding out in 3 minutes.

**2. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api-team/app
```
**What this does:** the Python project lives here.

**3. Create the virtual environment if this clone has none.**

```bash
[ -d .venv ] || python3 -m venv .venv
```
**What this does:** `[ -d .venv ]` asks whether the folder exists; `||` means "if not, do the next
thing". A fresh clone never has one, because `.venv/` is ignored and so is never pushed.

**4. Activate it.**

```bash
source .venv/bin/activate
```
**What this does:** `source` runs the file **in your current shell** so it can change your `PATH`;
the prompt gains `(.venv)`. It must be its own command — inside brackets the change would be lost
when that sub-shell ended, and `pytest` would be *command not found*.

**5. Install the tools.**

```bash
pip install -q -r requirements-dev.txt
```
**What this does:** installs the pinned versions quietly (`-q`).

**6. Run the linter.**

```bash
flake8 src tests
```
**What this does:** checks style and obvious errors. **It prints nothing when the code is
clean** — that is a pass.

**7. Run the tests with coverage.**

```bash
pytest -q --cov=src --cov-report=term-missing
```
**What this does:** runs the suite quietly (`-q`) and prints a coverage table naming any lines no
test touches. Expect `19 passed` and coverage above 70%.

**8. Return to the repository root.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** the `git add` below only works from here.

---

## Step 4 — Push and watch it run

**1. Stage the workflow file.**

```bash
git add .github/workflows/ci.yml
```
**What this does:** stages that one file by name, so nothing else can slip into the commit.

**2. Commit it.**

```bash
git commit -m "ci: add GitHub Actions pipeline

Runs flake8, black (advisory) and pytest across Python 3.11 and 3.12 on every
push to main and every pull request. Enforces a 70% line-coverage floor and
publishes JUnit and coverage artefacts.

The single 'CI passed' job is the stable required status check, so the matrix
can change without editing the branch protection rule."
```
**What this does:** one command over several lines — copy all of it, both quote marks included.

**3. Push the branch.**

```bash
git push -u origin ci/add-github-actions
```
**What this does:** uploads it and prints a URL for opening the pull request.

**4. Open the pull request** on GitHub from that link. Within seconds the checks appear at the
bottom of the page.

**5. Follow the run in the terminal (optional).**

```bash
gh run watch 2>/dev/null || echo "Install the GitHub CLI (sudo apt install gh) or watch in the browser"
```
**What this does:** if the GitHub CLI is installed (Lab 00 Step 8.1), it streams the run live;
otherwise it prints the fallback message and you use the **Actions** tab. Press `Ctrl` + `C` to
stop watching.

✅ **Checkpoint:** the run shows `lint`, `test (3.11)`, `test (3.12)` and `CI passed`, all
green. Click into `test (3.12)` and read the coverage table and the step summary.

Merge the PR.

---

## Step 5 — Make CI a required check (this is the point of the lab)

**Settings → Branches → edit the `main` rule → Require status checks to pass → search for
`CI passed` → select it → Save.**

> The check only appears in that search box **after it has run at least once** on the
> repository. That is why you merged first.

---

## Step 6 — Prove the gate works

**1. Go back to `main`.**

```bash
git switch main
```
**What this does:** you merged the pipeline, so start from there.

**2. Get the merged pipeline.**

```bash
git pull
```
**What this does:** your local `main` now contains `ci.yml`.

**3. Create a branch for the deliberate break.**

```bash
git switch -c test/deliberately-break-ci
```
**What this does:** the branch name says exactly what it is for.

**4. Break the health endpoint.** One command, ending at `PY`:

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace('return jsonify(status="ok", version=config.VERSION), 200',
              'return jsonify(status="BROKEN", version=config.VERSION), 200')
assert "BROKEN" in s, "patch did not apply"
p.write_text(s)
print("broke the /health contract")
PY
```
**What this does:** makes `/health` answer `"BROKEN"`, which violates the assertion in the test
called `test_health_is_always_ok`. It prints `broke the /health contract`.

**5. Stage it.**

```bash
git add app/src/app.py
```
**What this does:** stages the broken file.

**6. Commit it.**

```bash
git commit -m "test: deliberately break the health endpoint contract"
```
**What this does:** records the break.

**7. Push it and open a pull request** from the link it prints.

```bash
git push -u origin test/deliberately-break-ci
```
**What this does:** uploads the branch, which starts the pipeline.

✅ **Checkpoint — the important one:**
1. `test` goes **red**, and so does `CI passed`.
2. The PR shows **"Required statuses must pass before merging"**.
3. **The green merge button is disabled.** You cannot merge this, even as the repository
   owner.

You have just built a control that applies to 100 % of changes, automatically, with no
meeting. That is the DevOps governance argument from Module 9 §9.1, demonstrated.

Clean up — three commands.

```bash
git switch main
```
**What this does:** you cannot delete the branch you are standing on.

```bash
git push origin --delete test/deliberately-break-ci
```
**What this does:** deletes the branch on GitHub, which also closes the pull request.

```bash
git branch -D test/deliberately-break-ci
```
**What this does:** deletes your local copy. `-D` forces it, because the branch was never merged.

---

## Step 7 — Dependabot

**1. Create a branch.**

```bash
git switch -c ci/add-dependabot
```
**What this does:** configuration changes go through a pull request too.

**2. Make sure the folder exists.**

```bash
mkdir -p .github
```
**What this does:** a no-op if it is already there.

**3. Write the Dependabot configuration.** One command, ending at `EOF`:

```bash
cat > .github/dependabot.yml <<'EOF'
version: 2
updates:
  - package-ecosystem: pip
    directory: /app
    schedule: { interval: weekly }
    open-pull-requests-limit: 5
    commit-message: { prefix: "build" }

  - package-ecosystem: github-actions      # keeps the ACTIONS themselves patched
    directory: /
    schedule: { interval: weekly }
    commit-message: { prefix: "ci" }

  - package-ecosystem: docker              # base images, from Lab 06 onward
    directory: /app
    schedule: { interval: weekly }
EOF
```
**What this does:** writes the file that tells **Dependabot** — GitHub's built-in dependency
updater — what to watch. Nothing is printed.

**4. Stage it.**

```bash
git add .github/dependabot.yml
```
**What this does:** stages the one file.

**5. Commit it.**

```bash
git commit -m "ci: enable Dependabot for pip, actions and docker"
```
**What this does:** records it.

**6. Push it.**

```bash
git push -u origin ci/add-dependabot
```
**What this does:** uploads the branch. Dependabot now opens a pull request whenever a dependency
has a newer or non-vulnerable version, and **each of those PRs runs through the CI you just
built**, so you find out immediately whether the upgrade is safe. The `github-actions` ecosystem
is the one people forget — and it is the one that patches your supply chain.

Merge the PR.

---

## 🧩 Stretch (homework)

1. **Add a status badge.** Put this at the top of your `README.md` — a visible red/green
   signal is one of the eleven CI rules from Module 2 §2.7:
   `![CI](https://github.com/<your-username>/paytrack-api/actions/workflows/ci.yml/badge.svg)`
2. **Make `black` blocking.** Run `black --line-length 100 app/src app/tests`, commit the
   result, then remove `continue-on-error: true`. Formatting arguments now happen once, in
   a tool, instead of in every review.
3. **Add `pytest --durations=5`** and find your slowest test. Keep the suite under 10
   minutes — the rule that keeps people waiting for it.
4. **Run it locally** with [`act`](https://github.com/nektos/act), which executes workflows in
   Docker on your machine. **[Lab 04A](../lab-04a-act-and-pipeline-security/README.md)** installs it,
   runs this pipeline with it, and uses it to show secret masking, script injection, SHA pinning
   and a versioned release. **[Lab 04B](../lab-04b-gitlab-ci/README.md)** builds the same pipeline on
   GitLab CI.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Workflow does not appear at all | Invalid YAML, or wrong path | Re-run the `yaml.safe_load` check; path must be `.github/workflows/*.yml` |
| `No such file or directory: requirements-dev.txt` | Missing `working-directory: app` | Add it, or prefix the path |
| Cache never hits | Wrong `cache-dependency-path` | Point it at the file whose hash should key the cache |
| `CI passed` not in the required-checks list | It has never run on this repo | Merge one PR first, then add it |
| Passes locally, fails in CI | Environment difference | Compare Python versions; this is exactly why day 3 containerises the build |
| Runs are queued for minutes | Free-tier concurrency | Public repos have generous limits; check Settings → Actions |

---

## 🎯 Outcome

`paytrack-api` now has a CI pipeline that lints, tests across two Python versions, enforces a
coverage floor, publishes artefacts, and **blocks any merge that breaks it**. Dependabot keeps
dependencies and Actions patched.

**Next:** [Lab 05 — Jenkins CI on localhost](../lab-05-jenkins-ci/README.md) ·
*Optional:* [Lab 04A — act and pipeline security](../lab-04a-act-and-pipeline-security/README.md) ·
[Lab 04B — GitLab CI](../lab-04b-gitlab-ci/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Timing:** 10 min explaining the anatomy, 15 writing and pushing, 10 on Steps 5–6.
  **Steps 5 and 6 are the lab.** If you are short on time, hand out `ci.yml` and spend the
  time on the disabled merge button instead.
- **The three things that go wrong:**
  1. YAML indentation. The `python3 -c yaml.safe_load` check in Step 3 removes most of it —
    make sure everyone runs it.
  2. They forget `actions/checkout` and the run fails with "no such file". A good failure to
    let happen once: it teaches that the runner starts empty.
  3. `CI passed` is not offered in the branch-protection search because no run has completed.
    Explain the ordering; do not let them hunt.
- **Teaching moment:** when the merge button greys out in Step 6, ask "how many changes
  reached production in your organisation last month without an automated check?"
- **Debrief question:** "Hosted or self-hosted CI? You are about to see the alternative in
  Lab 05 — write down your prediction of which you will prefer, and why."
</details>
