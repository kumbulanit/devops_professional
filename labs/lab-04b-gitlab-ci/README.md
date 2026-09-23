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

---

## Before you start — how to follow this lab

This lab moves between **two places**: the **terminal** on your machine, and the **GitLab website**
in your browser. Every instruction says which.

**In the terminal:**

| Question | Answer |
|---|---|
| **How do I open one?** | Press `Ctrl` + `Alt` + `T`. (Or press the ⊞ key, type `terminal`, press `Enter`.) |
| **How do I run a command?** | Click into the terminal, type or paste the contents of one box, press `Enter`. |
| **How do I paste?** | Copy with `Ctrl` + `C`; paste into the terminal with **`Ctrl` + `Shift` + `V`**. |
| **When is it finished?** | When the `$` prompt comes back. |
| **Nothing was printed!** | Normal — many commands say nothing when they succeed. |
| **The last line is `:` or `(END)`** | You are in a pager. Press `q`. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel. |
| **A box is many lines long** | If it starts with `cat > … <<'EOF'`, copy **all** of it — the last `EOF` line included. It is one command. |

**On the GitLab website:** menus are written in **bold** exactly as they appear, in the order you
click them — for example **Settings** → **Repository** → **Protected branches**. GitLab redesigns
its menus from time to time; if a name has moved, use the search box at the top of the page.

**Symbols in the boxes:**

| Symbol | Means |
|---|---|
| `~` | Your home folder; `~/.ssh` is the hidden `.ssh` folder inside it |
| `cd` | Move into a folder; everything after that happens there |
| `-o` | An **option** passed on to GitLab with a push |
| `<your-username>` / `<your-gitlab-path>` | **Replace these**, including the angle brackets, with your own |

One command in Part 5 **fails on purpose** — the text says so before the box. That failure is the
proof the lab is looking for.

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

> Already have an account? Do Steps 1.4 and 1.5 anyway: without an SSH key, Part 2 fails.

### Step 1.1 — Sign up

1. In your browser, go to **https://gitlab.com/users/sign_up**.
2. Enter your first and last name, a **username**, your email and a strong password (use a password
   manager). The username appears in every project URL — `gitlab.com/<username>/paytrack-api` — so
   choose one you are happy to show a colleague.
3. Select **Register**, then open the email GitLab sends you and **confirm your address** (a link or
   a code).
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

1. Select your **avatar** (top right) → **Edit profile**.
2. In the left menu, choose **Access** → **Password and authentication**.
3. Select **Register authenticator**.
4. Scan the QR code with an authenticator app (Microsoft Authenticator, Google Authenticator,
   1Password…).
5. Type the six-digit code it shows, plus your GitLab password, and select **Register with
   two-factor app**.
6. **Save the recovery codes somewhere safe** — a password manager, or printed and locked away.
   Without them, losing your phone locks you out of the account permanently.

### Step 1.4 — Add your SSH key

**1. Print your public key.**

```bash
cat ~/.ssh/id_ed25519.pub
```
**What this does:** `cat` prints a file. This one is your **public** key — a single line starting
`ssh-ed25519` and ending with a comment. It is safe to share: it can only verify you, never
impersonate you. The matching *private* key sits next to it in `~/.ssh/id_ed25519` and must never
be copied anywhere.

> **"No such file or directory"?** You have not made a key yet. Create one with
> `ssh-keygen -t ed25519 -C "you@example.com"` (Lab 00 Step 8.2), pressing `Enter` to accept the
> default location, then run the command above again.

**2. Copy the whole line.** Select it in the terminal and press `Ctrl` + `Shift` + `C`.

**3. Add it to GitLab.** In the browser: **avatar** → **Edit profile** → **Access** → **SSH keys**
→ **Add new key**. Paste the line into **Key**, give it a **Title** such as `devops-course-laptop`,
leave **Usage type** as *Authentication & Signing*, and select **Add key**.

### Step 1.5 — Prove the key works

**1. Open a test connection.**

```bash
ssh -T git@gitlab.com
```
**What this does:** `ssh` connects to another machine securely; `-T` means "do not open a shell,
just test". The **first** time, SSH asks whether you trust the server and shows its fingerprint:
```
ED25519 key fingerprint is SHA256:eUXGGm1YGsMAS7vkcx6JOJdOGHPem5gQp4taiCfCLB8.
```
**Compare it with the line above before you answer.** If it matches, type `yes` and press `Enter`.
You should then see `Welcome to GitLab, @<your-username>!`

> 🔑 **Why check the fingerprint?** It is how you know you are talking to GitLab and not to someone
> sitting in the middle of your network. Typing `yes` without looking defeats the point.

---

## Part 2 — Create the project and push your code (10 min)

### Step 2.1 — An empty project

In the browser:

1. Select the **+** at the top left → **New project/repository** → **Create blank project**.
2. **Project name:** `paytrack-api`.
3. **Project URL:** leave your username selected.
4. **Visibility level:** *Public* — the same choice as your GitHub repository, so reviewers can see
   it. *Private* also works.
5. **Untick "Initialize repository with a README".** You are pushing existing history; an
   initialised project would have unrelated history, exactly as in Lab 03.
6. Select **Create project**. Leave the page open — it shows the address you need next.

### Step 2.2 — A separate clone with two remotes

**1. Go to your course folder.**

```bash
cd ~/devops-course
```
**What this does:** moves into the folder that holds all your work for the week.

**2. Clone your GitHub repository into a new folder.**

```bash
git clone https://github.com/<your-username>/paytrack-api.git paytrack-api-gitlab
```
**What this does:** makes a **second, separate copy** of your project in a folder called
`paytrack-api-gitlab`. Working here means nothing you do for GitLab can end up in
`paytrack-api-team` by accident. Replace `<your-username>` with your GitHub username.

**3. Move into it.**

```bash
cd paytrack-api-gitlab
```
**What this does:** everything from here on happens in the GitLab copy.

**4. Rename the server it came from.**

```bash
git remote rename origin github
```
**What this does:** a **remote** is a saved server address with a short name. The clone called
GitHub `origin`; renaming it to `github` frees the name `origin` for GitLab.

**5. Add GitLab as `origin`.**

```bash
git remote add origin git@gitlab.com:<your-gitlab-path>/paytrack-api.git
```
**What this does:** saves your GitLab project's SSH address. Replace `<your-gitlab-path>` with your
GitLab username (or group). The project page shows the exact address under **Code** → **Clone with
SSH**. In this folder, a plain `git push` now means "push to GitLab".

**6. Check both servers are listed.**

```bash
git remote -v
```
**What this does:** `-v` (verbose) lists each remote twice — once for fetching, once for pushing.
You should see `github` with an `https://github.com/…` address and `origin` with a
`git@gitlab.com:…` one. One local repository can talk to as many servers as you like.

**7. Upload the main branch.**

```bash
git push -u origin main
```
**What this does:** sends your whole history to GitLab and remembers (`-u`) that this branch belongs
with GitLab's `main`.

**8. Upload your tags.**

```bash
git push origin --tags
```
**What this does:** tags are not sent by an ordinary push, so `--tags` sends them — here, the
`v1.0.0` you made in an earlier lab.

✅ **Checkpoint:** refresh the project page in your browser. Your files are there. The `.github/`
folder is there too, but **GitLab ignores it** — its pipeline lives in `.gitlab-ci.yml`, which you
write next.

---

## Part 3 — Write the pipeline in GitLab's language (15 min)

**1. Start a branch for the change.**

```bash
git switch -c ci/add-gitlab-ci
```
**What this does:** `-c` creates a branch and switches to it. Work goes on a branch, never straight
onto `main` — the same habit as Lab 03.

**2. Write the pipeline file.**

```bash
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
```
**What this does:** this is **one command** — copy the whole box, including the last `EOF` line, and
press `Enter` once. `cat > <file> <<'EOF'` means "write everything up to the line `EOF` into this
file", so you get the indentation exactly right without typing it. The file describes your whole
pipeline; the table below reads it beside Lab 04's `ci.yml`.

**3. Check the file is valid.**

```bash
python3 -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml')); print('YAML is valid')"
```
**What this does:** tries to parse the file the way GitLab will. It prints `YAML is valid`, or an
error naming the line that is wrong. YAML cares about indentation — two spaces, never a Tab.

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

**1. Stage the new file.**

```bash
git add .gitlab-ci.yml
```
**What this does:** marks the file to go into the next commit. New files always need this.

**2. Commit it.**

```bash
git commit -m "ci: add the GitLab CI pipeline"
```
**What this does:** saves the change with a message. `-m` supplies the message so no editor opens.

**3. Push, and ask GitLab to open the merge request as it arrives.**

```bash
git push -u -o merge_request.create -o merge_request.target=main -o merge_request.title="ci: add the GitLab CI pipeline" origin ci/add-gitlab-ci
```
**What this does:** one long command. `-u` links the branch to GitLab. The three `-o` **push
options** are instructions for the server: *create a merge request*, *target `main`*, *use this
title*. GitLab replies with a link to the new merge request — hold `Ctrl` and click it, or copy it
into your browser. (GitHub does not understand push options — there you used `gh pr create`.)

### Step 4.2 — Watch it

Open the link. On the merge request page:

1. The **pipeline** widget near the top shows it running. Select the pipeline number to see the
   graph: the **lint** stage — `lint`, `format`; then the **test** stage — `test: [3.11]`,
   `test: [3.12]`. Each is a separate job, in its own container.
2. Select a job name to read its log — the `pip install`, then flake8 or pytest.
3. In the left sidebar, choose **Build** → **Pipeline editor**, and switch the branch selector to
   `ci/add-gitlab-ci`: GitLab validates the file and tells you whether the syntax is correct. This
   is the place to check a pipeline change **before** you push it.

✅ **Checkpoint:** the pipeline **passes**. `format` may show an orange **!** — failed but allowed,
like the advisory `black` step in Lab 04. The merge request shows the **test summary** (19 tests)
and the **coverage** percentage.

> **Pipeline fails at once with a message about identity verification or no runners?** See Step 1.2.
> Also check **Settings** → **CI/CD** → **Runners** that *instance runners* are turned on.

4. Select **Merge** (keep **Delete source branch** ticked).

---

## Part 5 — Protect `main` and require a green pipeline (10 min)

### Step 5.1 — Protected branch

In the browser: **Settings** → **Repository** → **Protected branches**. New GitLab projects already
protect the default branch; select **Edit** on the `main` row and set:

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

### Step 5.3 — Prove it: try to push straight to `main`

**1. Go back to the main branch.**

```bash
git switch main
```
**What this does:** leaves the feature branch, which GitLab deleted when you merged.

**2. Get the merged pipeline file.**

```bash
git pull
```
**What this does:** downloads the merge you just did in the browser.

**3. Make a commit that changes nothing.**

```bash
git commit --allow-empty -m "test: try to push straight to main"
```
**What this does:** `--allow-empty` lets you commit with no changes at all — perfect for testing a
rule without touching the code.

**4. Try to push it. This fails on purpose.**

```bash
git push origin main
```
**What this does:** GitLab's server refuses:
```
remote: GitLab: You are not allowed to push code to protected branches on this project.
 ! [remote rejected] main -> main (pre-receive hook declined)
```
The rule is enforced by the **server**, so no option on your side can get past it.

**5. Remove the rejected commit.**

```bash
git reset --hard origin/main
```
**What this does:** makes your local `main` match GitLab's again, deleting the empty commit. Your
branch and the server now tell the same story.

---

## Part 6 — A broken merge request cannot merge (10 min)

**1. Start a branch for the broken change.**

```bash
git switch -c test/deliberately-break-ci
```
**What this does:** creates and switches to a branch whose name says what it is for.

**2. Break the health endpoint.**

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
break as Lab 04 Step 6: the service answers `BROKEN` where the tests expect `ok`.

**3. Commit it.**

```bash
git commit -am "test: deliberately break the health endpoint contract"
```
**What this does:** `-a` stages the modified file (it is already tracked) and `-m` gives the
message.

**4. Push it with a merge request.**

```bash
git push -u -o merge_request.create -o merge_request.target=main origin test/deliberately-break-ci
```
**What this does:** the same push options as Part 4, without a title this time — GitLab uses the
commit message. Open the link it prints.

✅ **Checkpoint — the important one:**
1. Both `test` jobs go **red**; the pipeline **fails**.
2. The merge request's **test summary** names the failing test, `test_health_is_always_ok`.
3. **There is no way to merge**: the merge button is replaced by a message that the pipeline must
   succeed. That is *Pipelines must succeed* doing its job — the same control you built on GitHub,
   under a different name.

**5. Go back to `main`.**

```bash
git switch main
```
**What this does:** leaves the broken branch. The broken code never reached `main`.

**6. Delete the branch on GitLab.**

```bash
git push origin --delete test/deliberately-break-ci
```
**What this does:** `--delete` removes a branch from the server. On GitLab this does **not** close
the merge request — open it in the browser and select **Close merge request**.

**7. Delete your local copy of the branch.**

```bash
git branch -D test/deliberately-break-ci
```
**What this does:** `-D` deletes the branch label even though it was never merged. The commit is
gone from your branch list; nothing else is affected.

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
| `fatal: repository … not found` on the first push | The address in `git remote add origin …` does not match the project | Copy it from the project page (**Code** → **Clone with SSH**), then `git remote set-url origin <address>` |
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
  3. Delegates run the GitLab commands inside `paytrack-api-team`. Part 2 deliberately uses a
     second folder — have them run `pwd` if a push goes to the wrong server.
  4. The second rule in `workflow: rules` removed makes every MR push run two pipelines — show it
     if someone asks why the rule exists.
- **Debrief question:** "On GitLab Free you cannot require an approval. Is a mandatory green
  pipeline without a mandatory reviewer enough of a control for a payments service? What would
  your auditor say?"
</details>
