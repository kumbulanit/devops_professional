# Lab 06 — Containerising PayTrack API: from 1 GB to 130 MB

| | |
|---|---|
| **Day** | 3 |
| **Duration** | 40 minutes |
| **Module** | 3 — Containers with Docker |
| **You will produce** | A production-grade multi-stage `Dockerfile`, and CI that builds and pushes to GHCR |
| **Feeds into** | Lab 07 (Compose uses this image), Labs 10–19 (Kubernetes runs it) |

---

## Objective

Build the same application three times — naively, then with a multi-stage build, then
hardened — and **measure the difference at each step**. You will finish with the image every
remaining lab deploys, published to a free registry by your CI pipeline.

## Prerequisites

- Lab 00 (Docker) and Lab 04 (CI pipeline)

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && git switch main && git pull
```

---

## Step 1 — The build context, and why `.dockerignore` comes first

```bash
cd ~/devops-course/paytrack-api-team
du -sh app/
du -sh app/.venv 2>/dev/null || echo "(no venv yet)"
```
**What this does:** `du -sh` reports total size, human-readable. Notice how much of `app/` is
`.venv/` — hundreds of megabytes of installed packages that must **never** enter an image.

```bash
cat > .dockerignore <<'EOF'
# Everything here is EXCLUDED from the build context sent to the Docker daemon.
.git
.github
.venv
venv
__pycache__
*.py[cod]
.pytest_cache
.coverage
coverage.xml
junit.xml
*.md
!README.md
.env
*.pem
*.key
k8s
terraform
ansible
docs
Jenkinsfile
EOF
```
**What this does:** the **build context** is every file Docker sends to the daemon *before*
the build begins. Without a `.dockerignore` you would ship `.git/` (your entire history),
`.venv/` (hundreds of MB), and possibly `.env` (your secrets) across that boundary. Three
concrete consequences: slow builds, a busted layer cache (any change to any file invalidates
`COPY .`), and **secret leakage**.

Note `!README.md` — a `!` prefix **re-includes** a path excluded by an earlier pattern.

---

## Step 2 — Build it naively, then measure

Everyone writes this Dockerfile first. Build it so you can see exactly what is wrong with it.

```bash
cat > app/Dockerfile.naive <<'EOF'
FROM python:3.12

WORKDIR /app
COPY . .
RUN pip install -r requirements-dev.txt
EXPOSE 8080
CMD python -m src.app
EOF
```

```bash
cd app
time docker build -f Dockerfile.naive -t paytrack-api:naive .
cd ..
docker images paytrack-api:naive --format "{{.Repository}}:{{.Tag}}\t{{.Size}}"
```
**What this does:** `-f` selects the Dockerfile, `-t` tags the result, and the trailing `.`
is the **build context** (the current directory). `time` reports how long it took.
`--format` with a Go template prints just the columns you want.

**Expect roughly 1.0–1.3 GB.** Now count the problems:

| # | Problem | Consequence |
|---|---|---|
| 1 | `FROM python:3.12` (full image) | ~1 GB of compilers, headers and tooling you will never run |
| 2 | `COPY . .` **before** `pip install` | Any source change invalidates the cache → pip re-runs every build |
| 3 | Installs `requirements-**dev**.txt` | pytest, flake8, bandit shipped to production |
| 4 | No `USER` | **Runs as root** |
| 5 | Shell-form `CMD` | Runs under `/bin/sh -c`, which does not forward `SIGTERM` → your app never shuts down gracefully |
| 6 | No healthcheck, no labels, no version | Unoperable and untraceable |

**Prove problem 2:**
```bash
cd app && touch src/app.py && time docker build -f Dockerfile.naive -t paytrack-api:naive . ; cd ..
```
**What this does:** `touch` updates the file's timestamp without changing content — enough to
invalidate the `COPY` layer. The rebuild re-runs `pip install` from scratch. **In CI this is
2–3 minutes wasted on every single commit.**

**Prove problem 4:**
```bash
docker run --rm paytrack-api:naive whoami
```
**What this does:** overrides `CMD` with `whoami`. It prints **`root`**. A container escape or
a mounted volume now has root-level reach.

---

## Step 3 — The production Dockerfile

```bash
cat > app/Dockerfile <<'EOF'
# syntax=docker/dockerfile:1.7
# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — builder.  Compilers and headers live here and are DISCARDED.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Dependencies FIRST and ALONE: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — runtime.  No compiler, no source of the build, no dev dependencies.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Build metadata, passed in by CI. ARGs are NOT secrets - they appear in image history.
ARG GIT_SHA=local
ARG APP_VERSION=1.0.0
ARG BUILD_DATE

LABEL org.opencontainers.image.title="paytrack-api" \
      org.opencontainers.image.description="Health-check recording service" \
      org.opencontainers.image.source="https://github.com/<your-username>/paytrack-api" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages" \
    APP_VERSION="${APP_VERSION}" \
    PORT=8080

# Minimal runtime extras: curl only for the HEALTHCHECK.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --gid 10001 appuser \
 && useradd  --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser

# Only the installed packages come across from the builder - not the compiler.
COPY --from=builder /install /install

WORKDIR /app
COPY --chown=10001:10001 src/ ./src/
COPY --chown=10001:10001 wsgi.py ./

USER 10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8080/health || exit 1

# Exec form: gunicorn becomes PID 1 and receives SIGTERM directly.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", \
     "--workers", "2", "--threads", "4", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--graceful-timeout", "30", \
     "wsgi:app"]
EOF
```

**Why each decision:**

| Line | Reason |
|---|---|
| `# syntax=docker/dockerfile:1.7` | Opts into modern BuildKit features (cache mounts, build secrets) |
| `python:3.12-slim` | ~150 MB instead of ~1 GB. Not Alpine: musl libc breaks manylinux wheels and forces slow source builds |
| `AS builder` / `AS runtime` | **Multi-stage.** The builder is thrown away entirely |
| `COPY requirements.txt` before `COPY src/` | **Cache ordering.** Source changes no longer re-run pip |
| `--prefix=/install` | Installs into one relocatable directory that can be copied wholesale into stage 2 |
| `requirements.txt`, not `-dev` | pytest and flake8 are build-time tools, not runtime dependencies |
| `apt-get … && rm -rf /var/lib/apt/lists/*` in one `RUN` | Deleting in a *later* layer would not shrink the image (Module 3 §3.3) |
| `groupadd`/`useradd` with **numeric** 10001 | Kubernetes' `runAsNonRoot` can verify a numeric UID without resolving `/etc/passwd` |
| `COPY --chown=10001:10001` | Correct ownership without an extra `RUN chown` layer |
| `USER 10001` | **Drops root.** The single highest-value line in the file |
| `LABEL org.opencontainers.image.*` | Standard labels; `revision` ties a running container back to its commit |
| `HEALTHCHECK` | Docker and Compose use it to decide readiness. (Kubernetes ignores it and uses probes) |
| `gunicorn`, exec form | A production WSGI server, as PID 1, receiving `SIGTERM` directly for graceful shutdown |

```bash
cd app
time docker build \
  --build-arg GIT_SHA="$(git rev-parse --short HEAD)" \
  --build-arg APP_VERSION=1.0.0 \
  --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -t paytrack-api:1.0.0 -t paytrack-api:latest .
cd ..
```
**What this does:** `--build-arg` passes values into `ARG` declarations.
`git rev-parse --short HEAD` prints the current commit's short SHA, stamping the image with
its exact provenance. `-t` twice applies two tags to one image.

---

## Step 4 — Measure the difference

```bash
docker images paytrack-api --format "table {{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"
```
**Expect roughly:**

| Tag | Size (measured) |
|---|---|
| `naive` | **1.2 GB** |
| `1.0.0` | **~190 MB** |

*(Measured on Docker 28 / arm64. On amd64 expect roughly 1.1 GB and ~150 MB — the ratio holds,
the absolute numbers move a little with architecture and base-image revision.)*

**That is a 6–8× reduction, and it is not cosmetic.** Every pull is 7× faster: cluster
autoscaling, rolling updates and node replacement all get proportionally faster, and your
registry bill and CI minutes fall.

```bash
docker history paytrack-api:1.0.0 --human --format "table {{.CreatedBy}}\t{{.Size}}" | head -15
```
**What this does:** shows the layers and their sizes — where the megabytes actually are.
**Note that `docker history` also shows every `ARG` and `ENV` value**, which is precisely why
a secret must never be passed as a build argument.

```bash
docker run --rm paytrack-api:1.0.0 whoami 2>/dev/null || docker run --rm paytrack-api:1.0.0 id
```
**What this does:** the slim image has no `whoami`, so `id` prints
`uid=10001 gid=10001`. **Not root.**

**Prove the cache fix:**
```bash
cd app && touch src/app.py && time docker build -t paytrack-api:1.0.0 . ; cd ..
```
**Expect under 5 seconds** — dependencies came from cache, only the source layer rebuilt.
Compare with Step 2's rebuild. **This is the single highest-value habit in Dockerfile
authoring.**

---

## Step 5 — Run it, and test the isolation

```bash
docker run -d --name paytrack -p 8080:8080 paytrack-api:1.0.0
docker ps --filter name=paytrack
```
**What this does:** runs detached and publishes container port 8080 on host port 8080.
`docker ps` shows the status — after ~10 seconds it reads `(healthy)`, because the
`HEALTHCHECK` has succeeded three times.

```bash
curl -s localhost:8080/health | jq
curl -s localhost:8080/api/v1/info | jq
docker logs paytrack | tail -5
```
**What this does:** confirms the app answers, and shows gunicorn's access log on stdout —
**the correct place for container logs**, because the platform collects stdout.

**Test signal handling — the reason exec form matters:**

```bash
docker exec paytrack cat /proc/1/cmdline | tr '\0' ' '; echo
```
**What this does:** prints the command line of **PID 1** inside the container (`/proc/1/cmdline`
uses NUL separators, so `tr` makes it readable). With the exec-form `CMD` you see
`python … gunicorn … wsgi:app` — **gunicorn itself is PID 1**, so it receives signals directly.

```bash
docker run -d --name paytrack-naive paytrack-api:naive
sleep 3
docker exec paytrack-naive cat /proc/1/cmdline | tr '\0' ' '; echo
docker exec paytrack-naive ps -eo pid,comm
```
**What this does:** the naive image shows **`/bin/sh -c python -m src.app`** as PID 1, with
python as a *child* at a different PID. That is the whole problem in one line.

**Now prove it matters:**
```bash
docker kill --signal=TERM paytrack-naive
sleep 2
docker inspect -f '{{.State.Running}}' paytrack-naive
```
**What this does:** sends **`SIGTERM` to PID 1** — exactly what an orchestrator sends when it
wants a container to shut down gracefully. The result is **`true`: the container is still
running.** `sh` has no signal handler, and PID 1 ignores signals it has no handler for, so the
shutdown request never reaches your application.

```bash
docker kill --signal=TERM paytrack
sleep 2
docker inspect -f '{{.State.Running}}' paytrack 2>/dev/null || echo "gone — it shut down cleanly"
```
**What this does:** the same signal to the exec-form container. It **exits**, because gunicorn
is PID 1 and handles `SIGTERM` by draining its workers.

```bash
docker rm -f paytrack paytrack-naive 2>/dev/null
```

> 🔑 **Why this matters in Kubernetes.** Every rolling update, every scale-down, every node
> drain sends `SIGTERM` and then waits `terminationGracePeriodSeconds` before `SIGKILL`. With a
> shell-form `CMD`, your application never hears the request: it is killed mid-request, and
> **in-flight work is dropped on every single deployment.**
>
> ⚠️ **A note on timing.** You may have seen this demonstrated as "`docker stop` takes the full
> 10 seconds on the naive image". That depends on your platform: Docker Desktop's VM often
> reaps the container far faster, so the stopwatch shows no dramatic difference even though the
> signal was genuinely ignored. **The `docker kill --signal=TERM` test above is deterministic
> everywhere** — which is why this lab uses it.

**Now harden the runtime as well as the image:**
```bash
docker run -d --name paytrack-hardened -p 8080:8080 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --memory=256m --cpus=0.5 \
  paytrack-api:1.0.0
sleep 5 && curl -s localhost:8080/health | jq
```
**What each flag does:**

| Flag | Effect |
|---|---|
| `--read-only` | Root filesystem is read-only. Malware cannot write a payload |
| `--tmpfs /tmp:...` | Gives back one writable, RAM-backed path. `noexec,nosuid` stop it being used to run code |
| `--cap-drop=ALL` | Removes every Linux capability. The app only needs to bind a high port |
| `--security-opt=no-new-privileges` | Blocks setuid privilege escalation inside the container |
| `--memory` / `--cpus` | Bounds the blast radius of a leak or a runaway loop |

```bash
docker exec paytrack-hardened sh -c 'touch /forbidden' || echo "✅ read-only filesystem enforced"
docker rm -f paytrack-hardened
```
**What this does:** proves the read-only root. The write fails; the guard clause prints the
confirmation. These same settings become Kubernetes' `securityContext` in Lab 17.

---

## Step 6 — Scan the image

```bash
trivy image --severity HIGH,CRITICAL paytrack-api:naive | head -25
trivy image --severity HIGH,CRITICAL paytrack-api:1.0.0 | head -25
```
**What this does:** Trivy inspects every layer, extracts the OS package database and the
Python packages, and matches them against vulnerability feeds. `--severity` filters the noise.

**Compare the counts.** The slim multi-stage image typically has **an order of magnitude
fewer findings** than the naive one — because it contains an order of magnitude less
software. *Not shipping something is the most reliable way to secure it.* This is the
preview of Lab 17.

---

## Step 7 — CI builds and publishes the image

```bash
git switch -c ci/add-docker-build
cat > .github/workflows/build.yml <<'EOF'
name: Build & Publish Image

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

permissions:
  contents: read
  packages: write            # required to push to GHCR

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        if: github.event_name != 'pull_request'      # never push from a PR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}      # auto-provisioned, short-lived

      - name: Derive tags and labels
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=,format=short
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./app
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            GIT_SHA=${{ github.sha }}
            BUILD_DATE=${{ github.event.repository.updated_at }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan the built image
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          severity: HIGH,CRITICAL
          exit-code: '0'          # advisory today; Lab 17 turns this into a gate
          format: table
EOF
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/build.yml'));print('YAML valid')"
```
**What the key parts do:**

| Element | Purpose |
|---|---|
| `packages: write` | Grants the automatic `GITHUB_TOKEN` permission to push to GHCR. **No secret to create or rotate** |
| `if: … != 'pull_request'` | PRs build but never push — a fork PR must not be able to publish an image |
| `docker/metadata-action` | Generates the tag set: short SHA (immutable), branch name, SemVer from a tag, and `latest` on the default branch |
| `type=sha` | **The immutable tag you will actually deploy** |
| `cache-from/to: type=gha` | Uses GitHub's cache backend so layers survive between runs — often 3–5× faster |
| `trivy-action` | Scans the pushed image. `exit-code: '0'` reports without blocking, for now |

```bash
git add .github/workflows/build.yml .dockerignore app/Dockerfile app/Dockerfile.naive
git commit -m "build: add multi-stage Dockerfile and GHCR publish workflow

Multi-stage build cuts the image from ~1.1 GB to ~150 MB and drops root.
CI publishes to ghcr.io tagged with the commit SHA, which is what the
Kubernetes manifests will reference from Lab 10 onward."
git push -u origin ci/add-docker-build
```
Open the PR (CI runs, image builds but does not push), then **merge**.

After the merge, the `main` build pushes. Make the package public:
**GitHub → your profile → Packages → `paytrack-api` → Package settings → Change visibility →
Public.**

```bash
docker pull ghcr.io/<your-username>/paytrack-api:latest
docker run --rm -p 8080:8080 -d --name pulled ghcr.io/<your-username>/paytrack-api:latest
sleep 5 && curl -s localhost:8080/api/v1/info | jq && docker rm -f pulled
```
**What this does:** pulls **your CI-built image from the internet** and runs it. This is the
artefact that days 4, 5 and 6 deploy.

---

## ✅ Final checkpoint

```bash
docker images | grep paytrack-api
docker run --rm paytrack-api:1.0.0 id
trivy image --severity CRITICAL --quiet paytrack-api:1.0.0 | tail -3
```
- Multi-stage image is **under 200 MB**
- It runs as **uid 10001**
- Your CI publishes to GHCR on every merge to `main`

---

## ⭐ Advanced — optional, in this folder

The image is small and CI publishes it. If you want to go further with **builds**, the page and
its slides are beside this one — nothing on Day 4 onwards depends on them.

| In this folder | What it is | Time | Needs |
|---|---|---|---|
| **[README-06A — Builds in Depth](README-06A-builds-in-depth.md)** | Time three rebuilds and see exactly what each invalidates; read `docker history`; keep the pip cache in a BuildKit cache mount without shipping it; build one stage with `--target`; pin the base image by digest and pass real build metadata; watch a HEALTHCHECK turn a container `(healthy)`; build multi-architecture with buildx | 60 min, nine parts | Docker, ~3 GB disk. The multi-arch part is skippable |
| **`Lab06A_Advanced_Builds.pptx`** | The 11 slides behind it: what the cache keys on, BuildKit, cache mounts, digests and attestations | Read it first | PowerPoint |

---

## 🧩 Stretch (homework)

1. **Try distroless.** Change stage 2 to `gcr.io/distroless/python3-debian12`. Measure the
   size and CVE count. Then try to `docker exec … sh` into it — you cannot, because there is
   no shell. That is the trade-off.
2. **Multi-architecture.** Add `platforms: linux/amd64,linux/arm64` to `build-push-action` so
   the image runs on Apple Silicon and Graviton.
3. **BuildKit secrets.** Use `RUN --mount=type=secret,id=pip_token` for a private index —
   the secret is available during the `RUN` and **never enters a layer**.
4. Delete `Dockerfile.naive` and write a two-paragraph note in `docs/` on what it taught you.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `permission denied` writing at runtime | `USER 10001` + read-only FS | Mount a `tmpfs`, or `chown` the path in the build |
| `ModuleNotFoundError` in the container | `PYTHONPATH` does not match the `--prefix` | Ensure the Python minor version in `PYTHONPATH` matches the base image |
| Build cache never hits | `COPY . .` before `pip install` | Copy `requirements.txt` first |
| GHCR push → `denied` | Missing `packages: write` | Add the permission; check Settings → Actions → Workflow permissions |
| `docker pull` from GHCR → not found | Package is private | Change package visibility to Public |
| Healthcheck never healthy | `curl` missing from the runtime stage | It is installed above — confirm the `apt-get` line survived edits |

---

## 🎯 Outcome

A hardened, multi-stage, non-root, labelled, health-checked image under 200 MB, published to
GHCR by CI on every merge and tagged with its commit SHA.

**Next:** [Lab 07 — Multi-Container Stack with Docker Compose](../lab-07-docker-compose-stack/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **The measurement is the lesson.** Do not let anyone skip Step 2 to "save time" — the
  1.1 GB → 150 MB number is what they will repeat to their colleagues next week.
- **The three things that go wrong:**
  1. Build context confusion: running `docker build` from the repo root instead of `app/`.
     The trailing `.` is the context, not the Dockerfile location.
  2. Docker Hub rate limits mid-lab (`toomanyrequests`). Have delegates `docker login` with
     a free account beforehand.
  3. Wrong Python minor version in `PYTHONPATH` after someone edits the base image. Show
     them how the error names the missing module.
- **Highest-impact demo:** the two `docker stop` timings in Step 5. Ten seconds versus
  instant, explained by exec form versus shell form. It lands, and it pays off on day 4.
- **Debrief question:** "Your production images: how many run as root? How many reference
  `:latest` in a deployment manifest? Who could tell you which commit built the image
  currently serving your customers?"
</details>
