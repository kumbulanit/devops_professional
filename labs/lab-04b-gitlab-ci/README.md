# Lab 04B — The Same Pipeline on GitLab CI

| | |
|---|---|
| **Day** | 2 — **optional**, after class or as homework |
| **Duration** | About 60 minutes (plus 10 if you still need a GitLab account) |
| **Module** | 2 — Version Control and CI (the *Going Further* slides, section D) |
| **You will produce** | A GitLab account, a `paytrack-api` project with `.gitlab-ci.yml`, a protected `main` that only accepts merge requests with a green pipeline |
| **Feeds into** | Nothing — this is a **comparison** lab. GitHub remains the course's main platform |

---

## Objective

Many banks run GitLab rather than GitHub, often self-hosted. The ideas are identical — a pipeline
file in the repository, a protected main branch, a change that cannot merge while its checks are
red — but every name is different. You will:

1. open and secure a GitLab account;
2. push your PayTrack API code to a GitLab project;
3. rewrite Lab 04's pipeline in GitLab CI's language;
4. protect `main`, and prove that a broken merge request cannot be merged.

**Free tier used:** GitLab.com Free — **400 compute minutes a month** for running pipelines, and
up to **five users** in a private top-level group. This lab uses roughly 10 minutes. Check
[about.gitlab.com/pricing](https://about.gitlab.com/pricing/) for current limits.

## Prerequisites

- **Lab 04 complete** — you know what `ci.yml` does, because you are about to translate it
- An **SSH key** at `~/.ssh/id_ed25519.pub` (Lab 00 Step 8.2)
- A GitLab account — Part 1 creates one if you do not have it yet

## Words you need

| GitLab says | GitHub says | Plain meaning |
|---|---|---|
| **Project** | Repository | Where the code lives |
| **Group** | Organisation | A folder of projects with shared members |
| **Merge request (MR)** | Pull request | "Please review and merge my branch" |
| **Pipeline** | Workflow run | One run of all the jobs for a commit |
| **Job** | Job | One task, run by a runner in a fresh container |
| **Stage** | *(jobs linked with `needs:`)* | A group of jobs; stages run one after another, jobs inside a stage run together |
| **Runner** | Runner | The machine that executes jobs. GitLab.com provides **instance runners** |
| **CI/CD variable** | Secret / variable | A value given to jobs; can be **masked** and **protected** |

---

## Part 1 — Open a GitLab account and secure it (10 min)

> Already have an account? Do steps 1.4 and 1.5 anyway: without an SSH key Part 2 fails.

### Step 1.1 — Sign up

1. Go to **https://gitlab.com/users/sign_up**.
2. Enter your first and last name, a **username**, your email and a strong password (use a
   password manager). The username appears in every project URL —
   `gitlab.com/<username>/paytrack-api` — so choose one you are happy to show a colleague.
3. Open the email GitLab sends and **confirm your address** (a link or a code).
4. Answer the welcome questions — any answer works for this course.
   - If GitLab offers a **trial** of a paid tier, you can decline it; everything here works on Free.
   - If the welcome screens insist that you create a **group and project**, name the project
     `paytrack-api`. Its URL will then be `gitlab.com/<group>/paytrack-api`: use that path wherever
     this lab says `<your-gitlab-path>`, and skip Step 2.1.

### Step 1.2 — Be ready to verify your identity

GitLab.com asks some new accounts to prove they are a person before they may use its free runners,
to stop people mining cryptocurrency on them. Depending on its risk checks it asks for a **phone
number** or a **credit card** (the card is checked, **not charged**). It may ask at sign-up, or the
first time a pipeline runs. Nothing in this lab works until that is done, so if you are prompted,
complete it straight away.

### Step 1.3 — Turn on two-factor authentication

Select your **avatar** (top right) → **Edit profile** → **Access** → **Password and authentication**
→ **Register authenticator**. Scan the QR code with an authenticator app (Microsoft Authenticator,
Google Authenticator, 1Password…), type the six-digit code and your password, and **save the
recovery codes somewhere safe**. Without them, losing your phone locks you out.

### Step 1.4 — Add your SSH key

```bash
cat ~/.ssh/id_ed25519.pub
```
**What this does:** prints your **public** key — one line starting `ssh-ed25519`. It is safe to
share: it can only verify you, never impersonate you. (No such file? Create the key first:
`ssh-keygen -t ed25519 -C "you@example.com"` — Lab 00 Step 8.2.)

In GitLab: **avatar** → **Edit profile** → **Access** → **SSH keys** → **Add new key**. Paste the
whole line into **Key**, give it a **Title** such as `devops-course-laptop`, leave **Usage type** as
*Authentication & Signing*, and select **Add key**.

### Step 1.5 — Prove the key works

```bash
ssh -T git@gitlab.com
```
**What this does:** opens a test connection to GitLab over SSH. The **first time**, SSH asks whether
you trust the server and shows its fingerprint. **Check it** against GitLab's published value
before typing `yes`:
```
ED25519 key fingerprint is SHA256:eUXGGm1YGsMAS7vkcx6JOJdOGHPem5gQp4taiCfCLB8.
```
If it matches, type `yes`. You should then see `Welcome to GitLab, @<your-username>!`

> 🔑 **Why check the fingerprint?** It is how you know you are talking to GitLab and not to
> someone in the middle of your network. Typing `yes` without looking defeats the point.

---

## Part 2 — Create the project and push your code (10 min)

### Step 2.1 — An empty project

1. Top-left **+** (or **New project**) → **Create blank project**.
2. **Project name:** `paytrack-api`. **Project URL:** your username.
3. **Visibility level:** *Public* — the same choice as your GitHub repository, so reviewers can see
   it. *Private* also works.
4. **Untick "Initialize repository with a README".** You are pushing existing history; an initialised
   project would have unrelated history, exactly as in Lab 03.
5. **Create project.**

### Step 2.2 — A separate clone with two remotes

```bash
cd ~/devops-course
git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-gitlab
cd paytrack-api-gitlab
git remote rename origin github
git remote add origin git@gitlab.com:<your-gitlab-path>/paytrack-api.git
git remote -v
```
**What this does:**
- Clones your **GitHub** repository into a **new folder**, so nothing you do here can end up in
  `paytrack-api-team`.
- Renames the remote the clone came from to `github`, and adds GitLab as `origin`. In *this* folder,
  a bare `git push` now goes to GitLab.
- `git remote -v` lists both — one local repository can talk to as many servers as you like.

```bash
git push -u origin main
git push origin --tags
```
**What this does:** uploads `main` (and makes it the upstream) and your `v1.0.0` tag to GitLab.

✅ **Checkpoint:** refresh the project page. Your files are there. The `.github/` folder is there
too, but **GitLab ignores it** — its pipeline lives in `.gitlab-ci.yml`, which you write next.

---

## Part 3 — Write the pipeline in GitLab's language (15 min)

```bash
git switch -c ci/add-gitlab-ci
cat > .gitlab-ci.yml <<'EOF'
# PayTrack API - the same checks as .github/workflows/ci.yml, in GitLab CI's language.

workflow:                              # WHEN does a pipeline run at all?
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"   # every merge request
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS   # ...but not a second time for the branch
      when: never
    - if: $CI_COMMIT_BRANCH                              # a branch with no merge request yet
    - if: $CI_COMMIT_TAG                                 # version tags

stages:                                # stages run in order; jobs inside a stage run in parallel
  - lint
  - test

default:
  image: python:3.12-slim              # every job starts in a fresh container of this image
  interruptible: true                  # a newer pipeline on the same branch cancels this one
  timeout: 15 minutes                  # a hung job cannot burn your compute minutes

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

.python-job:                           # a TEMPLATE: names that start with a dot are not jobs
  cache:
    key:
      files: [app/requirements-dev.txt]
    paths: [.cache/pip]
  before_script:
    - cd app
    - python -m pip install -r requirements-dev.txt

lint:
  stage: lint
  extends: .python-job
  script:
    - flake8 src tests

format:
  stage: lint
  extends: .python-job
  allow_failure: true                  # advisory, like continue-on-error in GitHub Actions
  script:
    - black --check --line-length 100 src tests

test:
  stage: test
  extends: .python-job
  image: python:${PYTHON_VERSION}-slim
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12"]
  script:
    - >
      pytest -v --cov=src --cov-report=term-missing
      --cov-report=xml:coverage.xml --junitxml=junit.xml
      --cov-fail-under=70
  coverage: '/^TOTAL.+?(\d+(?:\.\d+)?%)$/'
  artifacts:
    when: always
    expire_in: 7 days
    reports:
      junit: app/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: app/coverage.xml
EOF
python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml')); print('YAML is valid')"
```
**What this does:** starts a branch, writes the pipeline, and checks the YAML parses. Read it
beside Lab 04's `ci.yml`:

| In `.gitlab-ci.yml` | In GitHub Actions | Meaning |
|---|---|---|
| `workflow: rules:` | `on:` | Which events start a pipeline. The second rule stops a push to a branch with an open MR running **two** pipelines |
| `stages:` | `needs:` | `test` waits for every `lint`-stage job to pass |
| `default: image:` | `runs-on:` + `actions/setup-python` | Each job runs **in a container**. Choosing the Python image *is* setting up Python |
| `.python-job` + `extends:` | *(copy-paste, or a composite action)* | Shared settings written once |
| `before_script:` | earlier `steps:` | Runs before `script:` **in the same shell**, so `cd app` still applies |
| `cache:` keyed on a file | `cache: pip` | Reuse downloaded packages until `requirements-dev.txt` changes |
| `allow_failure: true` | `continue-on-error: true` | The job may fail without failing the pipeline |
| `parallel: matrix:` | `strategy.matrix` | One job per Python version, at the same time |
| `--cov-fail-under=70` | the "Enforce the coverage floor" step | pytest itself fails below 70 % |
| `coverage:` regex | `$GITHUB_STEP_SUMMARY` | GitLab reads the percentage from the log and shows it on the MR |
| `artifacts: reports: junit` | `upload-artifact` | Test results appear **inside the merge request**, not only as a download |
| `timeout:` | `timeout-minutes:` | Kill a hung job |

> **There is no `act` for GitLab.** GitLab's own check is the **pipeline editor** (Step 4.2). A
> community tool, [`gitlab-ci-local`](https://github.com/firecow/gitlab-ci-local), runs jobs in
> Docker on your machine if you want the fast loop from Lab 04A.

---

## Part 4 — Push, open a merge request, watch it run (10 min)

### Step 4.1 — Push and create the merge request in one command

```bash
git add .gitlab-ci.yml
git commit -m "ci: add the GitLab CI pipeline"
git push -u -o merge_request.create -o merge_request.target=main -o merge_request.title="ci: add the GitLab CI pipeline" origin ci/add-gitlab-ci
```
**What this does:** commits the file and pushes the branch. The three `-o` **push options** are
instructions for GitLab: *create a merge request, into `main`, with this title*. GitLab replies with
a link to the new merge request. (GitHub does not understand push options — there you used
`gh pr create`.)

### Step 4.2 — Watch it

Open the link. On the merge request:

1. The **pipeline** widget shows it running. Select the pipeline to see the graph:
   **lint** stage — `lint`, `format`; **test** stage — `test: [3.11]`, `test: [3.12]`. Each is a
   separate job, in its own container.
2. Select a job to read its log — the `pip install`, then flake8 or pytest.
3. Left sidebar → **Build** → **Pipeline editor**, choose the branch `ci/add-gitlab-ci`: GitLab
   validates the file and tells you whether the syntax is correct. This is the place to check a
   pipeline change before you push it.

✅ **Checkpoint:** the pipeline **passes**. `format` may show an orange **!** — failed but allowed,
like the advisory `black` step in Lab 04. The merge request shows the **test summary** (19 tests)
and the **coverage** percentage.

> **Pipeline fails at once with a message about identity verification or no runners?** See Step 1.2.
> Also check **Settings** → **CI/CD** → **Runners** that *instance runners* are turned on.

Merge the merge request (keep **Delete source branch** ticked).

---

## Part 5 — Protect `main` and require a green pipeline (10 min)

### Step 5.1 — Protected branch

**Settings** → **Repository** → **Protected branches**. New GitLab projects already protect the
default branch; edit the `main` row so it says:

| Setting | Value | Prevents |
|---|---|---|
| **Allowed to merge** | Maintainers | Anyone less trusted merging into `main` |
| **Allowed to push and merge** | **No one** | Direct pushes — including yours. Every change goes through a merge request |
| **Allowed to force push** | **Off** | Rewriting `main`'s history (Lab 03A Part 8) |

### Step 5.2 — Merge checks

**Settings** → **Merge requests** → **Merge checks**:

| Setting | Value | GitHub equivalent |
|---|---|---|
| ☑ **Pipelines must succeed** | on | A required status check |
| ☑ **All threads must be resolved** | on | *Require conversation resolution* |

Select **Save changes**.

> **The GitLab Free difference.** On Free, anyone may approve a merge request, but you **cannot
> require** approvals, and a `CODEOWNERS` file names owners without *requiring* their review. Both
> need a paid tier. GitHub Free enforces both on public repositories. If your bank uses GitLab
> Premium or self-managed GitLab, this is where segregation of duties is configured.

### Step 5.3 — Prove it: push straight to `main`

```bash
git switch main && git pull
git commit --allow-empty -m "test: try to push straight to main"
git push origin main
```
**What this does:** updates `main` with the merged pipeline, makes an empty commit and tries to push
it past the rules. GitLab refuses:
```
remote: GitLab: You are not allowed to push code to protected branches on this project.
 ! [remote rejected] main -> main (pre-receive hook declined)
```

```bash
git reset --hard origin/main
```
**What this does:** removes the rejected commit from your local `main`, so it matches GitLab again.

---

## Part 6 — A broken merge request cannot merge (10 min)

```bash
git switch -c test/deliberately-break-ci
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/src/app.py")
s = p.read_text()
s = s.replace('return jsonify(status="ok", version=config.VERSION), 200',
              'return jsonify(status="BROKEN", version=config.VERSION), 200')
assert "BROKEN" in s, "patch did not apply"
p.write_text(s)
PY
git commit -am "test: deliberately break the health endpoint contract"
git push -u -o merge_request.create -o merge_request.target=main origin test/deliberately-break-ci
```
**What this does:** the same break as Lab 04 Step 6, pushed to GitLab with a merge request created
for it.

✅ **Checkpoint — the important one:**
1. Both `test` jobs go **red**; the pipeline **fails**.
2. The merge request's **test summary** names the failing test, `test_health_is_always_ok`.
3. **There is no way to merge**: the merge button is replaced by a message that the pipeline must
   succeed. That is *Pipelines must succeed* doing its job — the same control you built on GitHub,
   under a different name.

```bash
git switch main
git push origin --delete test/deliberately-break-ci
git branch -D test/deliberately-break-ci
```
**What this does:** deletes the branch on GitLab and locally. On GitLab, deleting the source branch
does **not** close the merge request — open it and select **Close merge request**.

---

## Side by side: what you now know about both

| Concept | GitHub | GitLab |
|---|---|---|
| Pipeline file | `.github/workflows/*.yml` — many files | `.gitlab-ci.yml` — one file, which can `include:` others |
| Reuse | Marketplace actions: `uses: owner/repo@sha` | `extends:`, `include:`, CI/CD components |
| Where a job runs | `runs-on:` a runner machine | `image:` a container, on a runner chosen by `tags:` |
| Order | `needs:` | `stages:` (or `needs:` for a graph) |
| Secrets | Repository secrets, `${{ secrets.X }}` | CI/CD variables — **masked**, and **protected** (only given to protected branches) |
| Job token | `GITHUB_TOKEN`, limited by `permissions:` | `CI_JOB_TOKEN`, limited under Settings → CI/CD → Job token permissions |
| Required checks | Branch protection + required status check | Protected branch + **Pipelines must succeed** |
| Required review | Free on public repositories | Paid tiers |
| Run it locally | `act` | Pipeline editor to validate; `gitlab-ci-local` (community) to run |
| Where a user's text reaches a script | `${{ }}` is pasted into the script — use `env:` (Lab 04A Part 5) | Values arrive as environment variables — quote them: `"$CI_MERGE_REQUEST_TITLE"` |
| Branching model it is known for | GitHub Flow | **GitLab Flow**: GitHub Flow plus environment branches (`main` → `staging` → `production`) |

**Neither is better.** Choose the one your organisation already runs well. The controls that
matter — a pipeline in the repository, a protected main, no merge while checks are red — exist in
both. What changes is which of them cost extra.

---

## 🧩 Stretch (homework)

1. **A protected variable.** Settings → CI/CD → Variables → add `DEMO_API_KEY`, tick *Mask variable*
   and *Protect variable*. Add a job that runs `echo "$DEMO_API_KEY"` on a feature branch, then on
   `main`. Explain why the value is empty on the feature branch.
2. **Pin the image.** Replace `python:3.12-slim` with its digest
   (`python:3.12-slim@sha256:…` — `docker pull python:3.12-slim` prints it), the GitLab version of
   pinning an action to a SHA.
3. **Push mirroring.** Settings → Repository → Mirroring repositories: push `main` from GitLab to a
   **new, empty** GitHub repository automatically, using a GitHub token with `Contents: write`.
4. **GitLab Flow.** Create a protected `production` branch and deploy only by merging `main` into
   it. Compare with the tag-based release in Lab 04A.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied (publickey)` | The key is not on your GitLab account, or a different key is being offered | `cat ~/.ssh/id_ed25519.pub` and compare with Edit profile → SSH keys; `ssh -vT git@gitlab.com` shows which key is tried |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` | The server key in `~/.ssh/known_hosts` differs | Check GitLab's published fingerprints **before** removing the old entry with `ssh-keygen -R gitlab.com` |
| `fatal: the receiving end does not support push options` | You pushed to GitHub, which has no push options | Push to the `origin` remote in `paytrack-api-gitlab` |
| Pipeline never starts; no pipeline on the MR | `.gitlab-ci.yml` has an error, or the `workflow: rules` matched nothing | Build → Pipeline editor shows the error |
| Job stuck: *no active runners* | Instance runners are off, or identity verification is pending | Settings → CI/CD → Runners; Step 1.2 |
| `ERROR: … could not find a version that satisfies the requirement` | Network hiccup on the runner, or a typo in requirements | Retry the job; read the first error in the log |
| Coverage not shown on the MR | The `coverage:` regex does not match the log | The job log must contain a `TOTAL … 83%` line; `--cov-report=term-missing` prints it |
| Out of compute minutes | 400 a month on Free | Wait for the monthly reset, or run jobs on your own runner |

---

## 🎯 Outcome

A GitLab account with 2FA and an SSH key, a `paytrack-api` project whose `.gitlab-ci.yml` does
everything Lab 04's workflow does, a `main` branch nobody can push to directly, and first-hand
proof that a merge request with a red pipeline cannot be merged — plus a table that translates
between the two platforms.

**Next:** [Lab 05 — Jenkins CI on localhost](../lab-05-jenkins-ci/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Accounts before the course.** GitLab's identity verification can stall a delegate for the whole
  lab. Put "create and verify a GitLab account" in the pre-course email (Lab 00 Step 8.3).
- **The comparison is the point.** Spend the debrief on the side-by-side table, not on YAML syntax.
  Ask which rows would change a bank's platform choice — usually *required review* and
  *self-hosting*.
- **Things that go wrong:**
  1. SSH key on the wrong account, or `ssh-agent` offering another key — `ssh -vT` shows it.
  2. Welcome screens forced a group: the project path is `<group>/paytrack-api`.
  3. The second rule in `workflow: rules` removed makes every MR push run two pipelines — show it
     if someone asks why the rule exists.
- **Debrief question:** "On GitLab Free you cannot require an approval. Is a mandatory green
  pipeline without a mandatory reviewer enough of a control for a payments service? What would
  your auditor say?"
</details>
