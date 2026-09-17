# Lab 05 — The Same Pipeline in Jenkins, on localhost

| | |
|---|---|
| **Day** | 2 |
| **Duration** | 20 minutes |
| **Module** | 2 — Version Control and CI |
| **You will produce** | A local Jenkins running the same lint + test pipeline from a `Jenkinsfile` |
| **Feeds into** | Nothing structurally — this is a **comparison** lab. GitHub Actions carries the CI thread onward |

---

## Objective

Build the *identical* pipeline in Jenkins so you can compare the two models from experience
rather than from marketing. You will feel the difference in setup cost within the first five
minutes, and that feeling is the learning outcome.

**Everything runs on localhost. Jenkins is free and open source.**

> **Trainer:** if the room is behind schedule, this is the first lab to demote to a demo
> (see `docs/run-sheet.md`). Nothing downstream depends on it.

## Prerequisites

- Lab 00 (Docker) and Lab 04 (a working `ci.yml` to compare against)
- Ports 8081 and 50000 free on your machine

---

## Step 1 — Run Jenkins in Docker

```bash
mkdir -p ~/devops-course/jenkins && cd ~/devops-course/jenkins
docker volume create jenkins_home
```
**What this does:** creates a **named volume** for Jenkins' state. Jenkins keeps everything —
job configuration, build history, plugins, credentials — in `/var/jenkins_home`. Without a
volume, `docker rm` erases your entire CI system. This is the day-3 storage lesson arriving
a day early.

```bash
cat > Dockerfile <<'EOF'
FROM jenkins/jenkins:2.479.1-lts-jdk17

USER root
# Python is needed to run the PayTrack API pipeline directly on the controller.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip git \
    && rm -rf /var/lib/apt/lists/*
USER jenkins

# Pre-install plugins so the first boot is not a manual wizard.
RUN jenkins-plugin-cli --plugins \
      workflow-aggregator:latest \
      git:latest \
      junit:latest \
      pipeline-stage-view:latest \
      configuration-as-code:latest \
      credentials-binding:latest \
      timestamper:latest \
      ws-cleanup:latest
EOF
```
**What this does:** builds a Jenkins image with what the pipeline needs baked in.
- The base tag is **pinned to an LTS version** — never `latest` for something stateful.
- `USER root` … `USER jenkins` — escalate only for the install, then drop back. Jenkins must
  not run as root.
- `--no-install-recommends` and `rm -rf /var/lib/apt/lists/*` in the **same layer** keep the
  image small: deleting in a later layer would not shrink it (Module 3 §3.3).
- `jenkins-plugin-cli` installs plugins at build time, so the container starts ready.
  `timestamper` and `ws-cleanup` are there because the Jenkinsfile in Step 3 uses `timestamps()` and
  `cleanWs()`; neither comes with the Pipeline plugins, and a pipeline that names a missing step fails
  before its first stage.

```bash
docker build -t jenkins-course:1.0 .
```
**What this does:** builds the image and tags it. First build takes 2–3 minutes.

```bash
docker run -d \
  --name jenkins \
  --restart unless-stopped \
  -p 8081:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins-course:1.0
```
**What each flag does:**

| Flag | Purpose |
|---|---|
| `-d` | Detached — run in the background and return the prompt |
| `--name jenkins` | A stable name, so later commands say `jenkins` not a random ID |
| `--restart unless-stopped` | Restarts after a crash or a host reboot, but not if you stopped it deliberately |
| `-p 8081:8080` | Host **8081** → container 8080. Deliberately not 8080, which PayTrack API uses |
| `-p 50000:50000` | The JNLP port build **agents** connect back on |
| `-v jenkins_home:/var/jenkins_home` | Mounts the named volume — **the line that makes Jenkins survive** |

> ⚠️ **What we did *not* do:** mount `/var/run/docker.sock` into the container. It is a very
> common Jenkins recipe and it grants **root on your host** to anything running in that
> container — including any build. Module 7 §7.4 covers why CI systems are high-value
> targets; this is that lesson in concrete form.

```bash
docker logs -f jenkins
```
**What this does:** follows the container's stdout (`-f`). Wait for the banner containing the
initial admin password, then press `Ctrl+C`.

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
**What this does:** `docker exec` runs a command **inside a running container**. Copy the
password.

---

## Step 2 — Complete the setup wizard

1. Open **http://localhost:8081**
2. Paste the initial admin password
3. Choose **Select plugins to install → None** (they are already baked in) → Install
4. Create your admin user — **do not skip this**, or you are left with a temporary account
5. Accept the Jenkins URL → **Start using Jenkins**

✅ **Checkpoint:** the Jenkins dashboard loads.

> **Note the elapsed time.** You are ~8 minutes in and have not run a single build. In Lab 04
> you had a working pipeline in under 3 minutes. Neither number is the whole story — but the
> difference is real and it is why the comparison matters.

---

## Step 3 — Write the Jenkinsfile

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
git switch -c ci/add-jenkinsfile
```

```bash
cat > Jenkinsfile <<'EOF'
pipeline {
    agent any                       // run on any available executor

    options {
        timeout(time: 15, unit: 'MINUTES')   // never let a hung build occupy an executor forever
        disableConcurrentBuilds()            // one run per branch at a time
        buildDiscarder(logRotator(numToKeepStr: '20'))  // keep 20 builds, then discard
        timestamps()                         // prefix every log line with a timestamp
    }

    environment {
        VENV       = "${WORKSPACE}/app/.venv"
        PYTHONUNBUFFERED = '1'               // stream python output instead of buffering it
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm                 // clone the branch that triggered this build
                sh 'git log --oneline -3'
            }
        }

        stage('Set up Python') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install --quiet --upgrade pip
                        pip install --quiet -r requirements-dev.txt
                        pip --version && python --version
                    '''
                }
            }
        }

        stage('Quality gates') {
            parallel {                       // lint and security run at the SAME time
                stage('Lint') {
                    steps {
                        dir('app') {
                            sh '. .venv/bin/activate && flake8 src tests'
                        }
                    }
                }
                stage('Security (advisory)') {
                    steps {
                        dir('app') {
                            sh '. .venv/bin/activate && bandit -r src -f txt || true'
                        }
                    }
                }
            }
        }

        stage('Test') {
            steps {
                dir('app') {
                    sh '''
                        . .venv/bin/activate
                        pytest -v \
                          --cov=src --cov-report=xml:coverage.xml \
                          --junitxml=junit.xml
                    '''
                }
            }
        }

        stage('Package') {
            when { branch 'main' }           // only build the artefact on main
            steps {
                dir('app') {
                    sh '''
                        . .venv/bin/activate
                        tar czf ../paytrack-api-${BUILD_NUMBER}.tar.gz src wsgi.py requirements.txt
                    '''
                }
                archiveArtifacts artifacts: 'paytrack-api-*.tar.gz', fingerprint: true
            }
        }
    }

    post {
        always {
            junit testResults: 'app/junit.xml', allowEmptyResults: true
            echo "Build ${currentBuild.number} finished: ${currentBuild.currentResult}"
        }
        success { echo '✅ Pipeline green — this commit is releasable.' }
        failure { echo '❌ STOP THE LINE. A red mainline blocks the whole team.' }
        cleanup { cleanWs() }                // free the workspace whatever happened
    }
}
EOF
```

**What each construct does:**

| Construct | Meaning |
|---|---|
| `pipeline { }` | The **declarative** pipeline block — structured and validated. The alternative, `node { }` scripted syntax, is raw Groovy with no guard-rails |
| `agent any` | Run on any executor. In production this is `agent { label 'linux' }` or `agent { docker { image '...' } }` |
| `options.timeout` | Kills a hung build. Without it, one wedged build can occupy an executor indefinitely |
| `buildDiscarder` | Bounds disk growth — a real operational concern on a long-lived controller |
| `environment` | Variables available to every stage. `${WORKSPACE}` is Jenkins' per-build directory |
| `dir('app')` | Changes directory for the enclosed steps — the equivalent of Actions' `working-directory` |
| `sh '''…'''` | A multi-line shell script. Note `. .venv/bin/activate` must be **in the same `sh` block** as the commands that use it: each `sh` is a fresh shell |
| `parallel { }` | Runs the enclosed stages simultaneously |
| `when { branch 'main' }` | Conditional stage — package only on the mainline |
| `archiveArtifacts` | Stores the artefact against the build, with `fingerprint` for traceability |
| `post { always / success / failure / cleanup }` | Runs after the stages, regardless of outcome |
| `junit` | Parses the JUnit XML into Jenkins' test-trend UI |

```bash
git add Jenkinsfile
git commit -m "ci: add Jenkins declarative pipeline

Mirrors .github/workflows/ci.yml so the two CI models can be compared
directly: same lint, same tests, same coverage, same artefact."
git push -u origin ci/add-jenkinsfile
```
Open and merge the PR — note that **your GitHub Actions CI gates this Jenkinsfile change**,
which is a neat illustration of pipeline-as-code being just code.

---

## Step 4 — Create the Jenkins job

In Jenkins: **New Item** → name `paytrack-api` → **Multibranch Pipeline** → OK.

| Section | Setting |
|---|---|
| Branch Sources | **Add source → Git** |
| Project Repository | `https://github.com/<your-username>/paytrack-api.git` |
| Credentials | *none* for a public repo (for a private one: **Add → Username with password**, using a GitHub PAT) |
| Behaviours | *Discover branches* (default) |
| Build Configuration | Mode **by Jenkinsfile**, Script Path `Jenkinsfile` |
| Scan Multibranch Pipeline Triggers | ☑ Periodically if not otherwise run → **1 minute** |

**Save.**

**Why Multibranch?** Jenkins scans the repository, finds every branch containing a
`Jenkinsfile`, and creates a job for each automatically — including PR branches. It is the
closest Jenkins gets to the GitHub Actions model, where the pipeline simply exists wherever
the file does.

**What "Periodically if not otherwise run" does:** polls GitHub every minute. A **webhook**
(GitHub → Settings → Webhooks → `http://<your-public-url>/github-webhook/`) is the correct
production answer — instant instead of up-to-60-seconds — but it requires Jenkins to be
reachable from the internet, which your laptop is not. **Note this: it is one of the real
operational costs of self-hosting.**

---

## Step 5 — Watch the build

Jenkins scans and starts building `main` within a minute (or click **Scan Multibranch
Pipeline Now**).

Open `paytrack-api → main`:
- **Stage View** — a column per stage, with durations. Find the slowest stage.
- **Console Output** — the full log, timestamped.
- **Test Result Trend** — appears from the second build; the graph that makes flakiness
  visible.

✅ **Checkpoint:** a green build with all stages passed and 19 tests recorded.

```bash
docker exec jenkins ls -la /var/jenkins_home/jobs/paytrack-api/branches/
```
**What this does:** shows Jenkins' on-disk job state — one directory per discovered branch.
Useful for understanding that a Jenkins controller is a **stateful server**, not a stateless
runner. That single fact drives most of the operational cost.

---

## Step 6 — Compare, honestly

Fill this in from what you have just experienced, not from what you have read:

```bash
cat > ~/devops-course/paytrack-api-team/docs/ci-comparison.md <<'EOF'
# CI Comparison — GitHub Actions vs Jenkins

| Dimension | GitHub Actions | Jenkins | Notes from the lab |
|---|---|---|---|
| Time to first green build |  |  |  |
| Lines of config |  |  |  |
| Infrastructure I now operate |  |  |  |
| Who patches it |  |  |  |
| Secret handling |  |  |  |
| Works with a private network / on-prem hardware |  |  |  |
| Cost at 50 developers |  |  |  |
| What happens if the server dies |  |  |  |

## What Jenkins does that Actions cannot
-

## What Actions does that Jenkins cannot (or not without effort)
-

## Which would I choose for my organisation, and why
EOF
nano ~/devops-course/paytrack-api-team/docs/ci-comparison.md
```

**The honest summary:**

| | **GitHub Actions** | **Jenkins** |
|---|---|---|
| Setup | Minutes | Hours, then ongoing |
| Config | YAML, declarative | Groovy DSL, more expressive |
| Hosting | Managed | **You operate a stateful, security-sensitive server** |
| Cost | Free (public) / minutes (private) | Free licence + real infrastructure + engineer time |
| Extensibility | Marketplace Actions | ~1 900 plugins — power *and* a maintenance burden |
| Best at | Anything already on GitHub | Air-gapped networks, hardware-in-the-loop, complex legacy orchestration, existing investment |
| Main risk | Vendor coupling; unpinned Actions | Plugin sprawl; an unpatched controller; snowflake job config |

**Neither is wrong.** Choose Jenkins when you *must* run inside your own network, or when you
already run it well. Choose a hosted runner when you can, because the cheapest server to
operate is the one you do not have.

---

## Step 7 — Clean up (or keep it)

```bash
docker stop jenkins            # keeps the container and the volume
# docker start jenkins         # bring it back later
```
**What this does:** stops the container without deleting it. To remove it entirely:
```bash
# docker rm -f jenkins && docker volume rm jenkins_home    # ⚠️ deletes ALL Jenkins state
```
**What this does:** `rm -f` force-removes the running container; `volume rm` deletes the
volume — **all jobs, history and credentials, unrecoverable.** Left commented deliberately.

---

## 🧩 Stretch (homework)

1. **Configuration as Code (JCasC).** Define the whole controller in a `jenkins.yaml` and
   mount it, so a rebuilt Jenkins comes back identical. This is what stops a controller
   becoming a snowflake.
2. **Add an agent** and set the controller's executors to **0**, so builds never run on the
   controller — the isolation practice from Module 2 §2.9.
3. **Shared library.** Extract the venv setup into a `vars/setupPython.groovy` in a shared
   library repository, so twenty pipelines stop duplicating it.

---

## 🎯 Outcome

A local Jenkins running the same pipeline from a versioned `Jenkinsfile`, plus a written,
evidence-based comparison in `docs/ci-comparison.md`.

**Next:** [Lab 06 — Building Docker Images](../lab-06-docker-images/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Timing is tight at 20 minutes.** Start the `docker build` at the beginning of the
  *previous* lab's wrap-up so the image is ready. If short, demo Steps 4–5 from the front.
- **The three things that go wrong:**
  1. Port 8081 already in use. `sudo lsof -i :8081` and pick another.
  2. Each `sh` step is a new shell, so `source .venv/bin/activate` in one step does not
     apply to the next. A genuinely instructive failure — let it happen, then explain.
  3. Multibranch scan finds nothing because the `Jenkinsfile` PR was not merged to `main`
     yet. Check the merge first.
- **Make the elapsed-time comparison explicit.** Ask the room to note the clock at the start
  of Step 1 and again at the first green build. Then compare with Lab 04.
- **Debrief question:** "Jenkins is free. Cost it properly for 50 developers: server, backup,
  plugin upgrades, patching, and the engineer who owns it. Now compare with 2 000
  Actions minutes a month."
</details>
