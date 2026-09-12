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

🔁 **RECOVER**
```bash
cd ~/devops-course && git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-team 2>/dev/null
cd paytrack-api-team && git switch main && git pull
```

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

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
git switch -c ci/add-github-actions
mkdir -p .github/workflows
```
**What this does:** starts a feature branch for the pipeline (the pipeline is code, so it goes
through the same review process as everything else) and creates the directory GitHub scans.
**The path `.github/workflows/` is fixed** — GitHub will not find workflows anywhere else.

---

## Step 2 — Write the pipeline

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

```bash
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML is valid')"
```
**What this does:** parses the file with Python's YAML library. **YAML indentation errors are
the number one cause of "my workflow does not appear"** — GitHub silently ignores files it
cannot parse. Catching it locally saves a push-and-wait cycle.

```bash
cd app && source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements-dev.txt)
flake8 src tests && pytest -q --cov=src --cov-report=term-missing
cd ..
```
**What this does:** runs locally exactly what CI will run. **If it fails here it will fail
there** — and finding out in 3 seconds beats finding out in 3 minutes.

---

## Step 4 — Push and watch it run

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions pipeline

Runs flake8, black (advisory) and pytest across Python 3.11 and 3.12 on every
push to main and every pull request. Enforces a 70% line-coverage floor and
publishes JUnit and coverage artefacts.

The single 'CI passed' job is the stable required status check, so the matrix
can change without editing the branch protection rule."
git push -u origin ci/add-github-actions
```

Open the PR on GitHub. Within seconds the checks appear at the bottom.

```bash
gh run watch 2>/dev/null || echo "Install the GitHub CLI (sudo apt install gh) or watch in the browser"
```
**What this does:** if you have the GitHub CLI, streams the run live in your terminal.
Otherwise use the **Actions** tab.

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

```bash
git switch main && git pull
git switch -c test/deliberately-break-ci
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
git add -A && git commit -m "test: deliberately break the health endpoint contract"
git push -u origin test/deliberately-break-ci
```
**What this does:** changes `/health` to return `"BROKEN"`, which violates the assertion in
`test_health_is_always_ok`. Open a PR.

✅ **Checkpoint — the important one:**
1. `test` goes **red**, and so does `CI passed`.
2. The PR shows **"Required statuses must pass before merging"**.
3. **The green merge button is disabled.** You cannot merge this, even as the repository
   owner.

You have just built a control that applies to 100 % of changes, automatically, with no
meeting. That is the DevOps governance argument from Module 9 §9.1, demonstrated.

```bash
git switch main
git push origin --delete test/deliberately-break-ci
git branch -D test/deliberately-break-ci
```
**What this does:** closes the PR by deleting the remote branch (`--delete`), then deletes the
local branch (`-D` = force-delete an unmerged branch).

---

## Step 7 — Dependabot

```bash
git switch -c ci/add-dependabot
mkdir -p .github
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
git add .github/dependabot.yml
git commit -m "ci: enable Dependabot for pip, actions and docker"
git push -u origin ci/add-dependabot
```
**What this does:** Dependabot opens pull requests when a dependency has a newer or
non-vulnerable version. Each PR runs through the CI you just built, so **you find out
immediately whether the upgrade is safe**. The `github-actions` ecosystem is the one people
forget, and it is the one that patches your supply chain.

Merge the PR.

---

## 🧩 Stretch (homework)

1. **Add a status badge.** Put this at the top of your `README.md` — a visible red/green
   signal is one of the eleven CI rules from Module 2 §2.7:
   `![CI](https://github.com/<user>/paytrack-api/actions/workflows/ci.yml/badge.svg)`
2. **Make `black` blocking.** Run `black --line-length 100 app/src app/tests`, commit the
   result, then remove `continue-on-error: true`. Formatting arguments now happen once, in
   a tool, instead of in every review.
3. **Add `pytest --durations=5`** and find your slowest test. Keep the suite under 10
   minutes — the rule that keeps people waiting for it.
4. **Run it locally** with [`act`](https://github.com/nektos/act) — `act pull_request` —
   which executes workflows in Docker on your machine.

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

**Next:** [Lab 05 — Jenkins CI on localhost](../lab-05-jenkins-ci/README.md)

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
