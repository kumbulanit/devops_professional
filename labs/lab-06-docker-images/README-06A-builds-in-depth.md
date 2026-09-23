# Lab 06A — Builds in Depth: the Cache, BuildKit and Multi-Architecture

| | |
|---|---|
| **Day** | 3 — **optional**, after class or as homework |
| **Duration** | About 60 minutes, in nine parts |
| **Module** | 3 — Containers with Docker (the Day 3 *Going Further* slides, section A) |
| **Slides** | `Lab06A_Advanced_Builds.pptx` — in this folder, 11 slides, read it first |
| **Parent lab** | [Lab 06 — Containerising PayTrack API](README.md) |
| **You will produce** | Two extra Dockerfiles (`Dockerfile.cache`, `Dockerfile.pinned`) and measurements that explain every second of your build time |
| **Feeds into** | Nothing. Labs 07–19 keep using the `paytrack-api:1.0.0` image from Lab 06 |

---

## Objective

Lab 06 made the image small. This one makes the **build** fast, repeatable and traceable — and
teaches you to prove each claim with a measurement rather than a belief.

You will time three rebuilds and watch exactly what each one invalidates, read where the
megabytes went, keep the package cache between builds without putting it in the image, build one
stage of a multi-stage file on its own, pin a base image to a digest, watch a HEALTHCHECK turn a
container `(healthy)`, and build an image for a processor that is not yours.

## Prerequisites

- **Lab 06 complete** — `app/Dockerfile` exists and `paytrack-api:1.0.0` builds
- **Docker running** — `docker version` must answer without `sudo`
- About **3 GB free disk**: this lab builds the same image several times under different tags

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction is **one command in one grey box**, numbered in
the order you run it.

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. It shows a line ending in `$` — the prompt. |
| **How do I run a command?** | Click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, and wait for the prompt to come back. |
| **Some of these take minutes** | Builds do. Wait for the prompt rather than pressing `Enter` again. |
| **Nothing was printed!** | Normal — many commands say nothing when they succeed. |
| **The last line is `:` or `(END)`** | A scrollable view. Press `q`. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel. |

**Symbols in the boxes:** `~` your home folder · `cd` move into a folder · `|` pass output to the
next command · `>` write a file · `>>` add to the end of a file · `$(…)` run this first and use its
answer · `#` a note the computer ignores. A box that begins `python3 - <<'PY'` and ends with `PY`
is **one** command that writes or edits a file — copy all of it.

**`time` in front of a command** measures how long it took and prints three lines afterwards;
**`real`** is the one you care about — wall-clock seconds.

🔁 **RECOVER — if you do not have the Lab 06 image**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project.

```bash
cd app && docker build -t paytrack-api:1.0.0 . && cd ..
```
**What this does:** rebuilds the Lab 06 image from `app/Dockerfile` and returns to the project
root. If `app/Dockerfile` is missing, finish Lab 06 first.

---

## Part 1 — Start a branch for this work (2 min)

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command in this lab runs from here or from `app/` inside it.

**2. Go to the main branch.**

```bash
git switch main
```
**What this does:** start from the reviewed code.

**3. Update it.**

```bash
git pull
```
**What this does:** brings in whatever was merged since your last pull.

**4. Create a branch.**

```bash
git switch -c docker/06a-builds-in-depth
```
**What this does:** the two Dockerfiles you write later are a change like any other, so they go on
a branch.

**5. Check Docker is up.**

```bash
docker version --format 'Docker {{.Server.Version}} is running'
```
**What this does:** asks the Docker service for its version. If it says it cannot connect, start
Docker and try again — nothing below works without it.

---

## Part 2 — What the build cache actually keys on (12 min)

Three experiments, each one a rebuild you time.

**1. Move into the application folder.**

```bash
cd ~/devops-course/paytrack-api-team/app
```
**What this does:** the `Dockerfile` and the build context live here.

**2. Warm the cache.**

```bash
docker build -t paytrack-api:1.0.0 .
```
**What this does:** builds the image so that every layer is in the cache. The final `.` is the
**build context** — the folder Docker receives. This first run may take a few minutes.

**3. Experiment 1 — rebuild with nothing changed.**

```bash
time docker build -t paytrack-api:1.0.0 .
```
**What this does:** every step prints `CACHED` and `real` is well under a second. Docker compared
each instruction and its inputs, found them unchanged, and reused the layers.

**4. Experiment 2 — change the source code.**

```bash
touch src/app.py
```
**What this does:** `touch` updates the file's timestamp without changing a character. That alone
is **not** enough to break the cache for a `COPY` — Docker compares file contents and metadata, so
a timestamp change does invalidate it. Nothing is printed.

**5. Rebuild and time it.**

```bash
time docker build -t paytrack-api:1.0.0 .
```
**What this does:** the dependency layers still say `CACHED`; the rebuild starts at
`COPY --chown=10001:10001 src/ ./src/` and runs everything after it. A few seconds — because the
source copy is **last**.

**6. Experiment 3 — change the dependency list.**

```bash
printf '\n# a comment, to change the file\n' >> requirements.txt
```
**What this does:** adds a comment line to the end of `requirements.txt`. The packages are
identical; only the file's contents changed.

**7. Rebuild and time it.**

```bash
time docker build -t paytrack-api:1.0.0 .
```
**What this does:** `COPY requirements.txt .` is no longer cached, so **`pip install` runs
again** — and so does every instruction after it. Minutes, not seconds. This is the cost the
ordering rule exists to control: dependencies first and alone, source last.

**8. Put the file back.**

```bash
git restore requirements.txt
```
**What this does:** restores the committed version, removing your comment.

**9. Rebuild once more.**

```bash
time docker build -t paytrack-api:1.0.0 .
```
**What this does:** fast again — the layer built from the *original* `requirements.txt` is still in
the cache, so Docker reuses it. The cache is keyed on content, not on time.

✅ **Checkpoint:** you have three numbers — roughly *under a second*, *a few seconds*, and *minutes*
— and you can say exactly which change causes which.

---

## Part 3 — Read where the megabytes went (8 min)

**1. List the layers of the production image.**

```bash
docker history paytrack-api:1.0.0 --human --format "table {{.Size}}\t{{.CreatedBy}}" | head -14
```
**What this does:** one row per layer, newest first: its size and the instruction that created it.
`--human` prints `412MB` rather than a byte count; `| head -14` keeps it to a screenful. The two
large rows are the `apt-get` line and the copied `/install` directory.

**2. Build the naive image again for comparison.**

```bash
docker build -f Dockerfile.naive -t paytrack-api:naive .
```
**What this does:** `-f` selects a different Dockerfile — the deliberately bad one from Lab 06. It
is cached from that lab, so this is quick unless you have pruned since.

**3. Compare the two.**

```bash
docker images paytrack-api --format "table {{.Tag}}\t{{.Size}}"
```
**What this does:** the naive image is roughly **1.2 GB**; the production one is **under 200 MB**.
Same application.

**4. Look at what the naive build shipped.**

```bash
docker history paytrack-api:naive --human --format "table {{.Size}}\t{{.CreatedBy}}" | head -8
```
**What this does:** the compiler toolchain (`build-essential`) and the pip download cache are
**inside the image**, because nothing discarded them. A multi-stage build leaves them in the stage
that is thrown away.

**5. Count the layers.**

```bash
docker image inspect paytrack-api:1.0.0 --format '{{len .RootFS.Layers}} layers'
```
**What this does:** `inspect --format` asks one question of the image's metadata. Fewer, well-ordered
layers cache better; very many tiny layers usually means a `RUN` that should have been combined.

**6. See what Docker is storing overall.**

```bash
docker system df
```
**What this does:** four buckets — Images, Containers, Local Volumes and **Build Cache** — with a
`RECLAIMABLE` column. On a working machine the build cache is usually the biggest, and it is the
safest thing to delete.

---

## Part 4 — Watch the build instead of the spinner (5 min)

**1. Rebuild with full output.**

```bash
docker build --progress=plain -t paytrack-api:1.0.0 . 2>&1 | tail -25
```
**What this does:** `--progress=plain` prints every line each step produced instead of the tidy
animated view; `2>&1` merges the error stream into the normal one so `tail -25` can keep the last
25 lines of both. This is the flag to reach for when a build fails and the tidy view has hidden
the compiler's message.

**2. Read the step numbers.** In that output each `#N` is one build step, and `#N CACHED` is a
step Docker skipped. BuildKit — the builder Docker uses by default — runs independent stages in
parallel, which is why the numbers are not in the order you wrote them.

---

## Part 5 — A cache mount: keep the downloads, not the megabytes (10 min)

The builder stage sets `PIP_NO_CACHE_DIR=1`, which tells pip to throw its downloads away so they
cannot bloat the layer. A **cache mount** is the better answer: the downloads live outside the
image and survive between builds.

**1. Write a variant Dockerfile.** One command — copy the whole box, including the final `PY`:

```bash
python3 - <<'PY'
import pathlib
src = pathlib.Path("Dockerfile").read_text()
old_env = "ENV PIP_NO_CACHE_DIR=1 \\\n    PIP_DISABLE_PIP_VERSION_CHECK=1"
new_env = "ENV PIP_DISABLE_PIP_VERSION_CHECK=1"
old_run = "RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt"
new_run = ("RUN --mount=type=cache,target=/root/.cache/pip \\\n"
           "    pip install --prefix=/install --no-warn-script-location -r requirements.txt")
assert old_env in src and old_run in src, "Dockerfile is not the one from Lab 06"
out = src.replace(old_env, new_env).replace(old_run, new_run)
pathlib.Path("Dockerfile.cache").write_text(out)
print("wrote Dockerfile.cache")
PY
```
**What this does:** copies your production Dockerfile, **stops pip discarding its cache**, and
mounts a cache directory for the install step. It prints `wrote Dockerfile.cache`. The
`# syntax=docker/dockerfile:1.7` line already at the top of your Dockerfile is what makes
`--mount` available.

**2. Look at the two lines you changed.**

```bash
grep -n -A1 "mount=type=cache" Dockerfile.cache
```
**What this does:** `grep -n` shows line numbers and `-A1` adds the line after each match, so you
see the mount and the `pip install` it applies to.

**3. Build it once to fill the cache.**

```bash
docker build -f Dockerfile.cache -t paytrack-api:cache .
```
**What this does:** downloads the packages and keeps them in the build cache mount. This first
build is not faster — it is the one paying for the later ones.

**4. Change the dependency list again.**

```bash
printf '\n# a comment, to change the file\n' >> requirements.txt
```
**What this does:** the same change as Part 2, which forced a full re-download there.

**5. Rebuild and time it.**

```bash
time docker build -f Dockerfile.cache -t paytrack-api:cache .
```
**What this does:** pip runs again — it must, the file changed — but the wheels come from the
cache mount instead of the internet. Compare `real` with the number from Part 2 command 7.

**6. Put the file back.**

```bash
git restore requirements.txt
```
**What this does:** removes the comment again.

**7. Prove the cache is not in the image.**

```bash
docker images paytrack-api --format "table {{.Tag}}\t{{.Size}}"
```
**What this does:** `cache` and `1.0.0` are the same size. The downloads live in Docker's build
cache, not in a layer — which is the whole point.

> 🔑 **A cache mount is not a layer.** It is scratch space the build can read and write, discarded
> from the result. `type=secret` works the same way for credentials: available during one `RUN`,
> never written into the image.

---

## Part 6 — Build only part of the file (5 min)

**1. Build the builder stage on its own.**

```bash
docker build --target builder -t paytrack-api:builder .
```
**What this does:** `--target` stops at the named stage. You get an image of the *intermediate*
stage — compiler and all — which is exactly what you want when a dependency fails to build and you
need to poke around.

**2. Look inside it.**

```bash
docker run --rm paytrack-api:builder ls /install/bin
```
**What this does:** runs one command in a throw-away container (`--rm` deletes it afterwards) and
lists the programs the install produced — `gunicorn`, `flask` and friends.

**3. See what that stage weighs.**

```bash
docker images paytrack-api --format "table {{.Tag}}\t{{.Size}}"
```
**What this does:** the `builder` tag is several hundred megabytes heavier than `1.0.0`. That
difference is precisely what the multi-stage build discards.

---

## Part 7 — Say what the image is: digests and build metadata (10 min)

**1. Find the digest of the base image.**

```bash
docker image inspect python:3.12-slim --format '{{index .RepoDigests 0}}'
```
**What this does:** prints the base image's immutable content address, like
`python@sha256:6f7e2b…`. A **tag** such as `3.12-slim` moves when the publisher rebuilds it; a
**digest** cannot move.

**2. Store it for the next command.**

```bash
BASE=$(docker image inspect python:3.12-slim --format '{{index .RepoDigests 0}}')
```
**What this does:** keeps that answer under the name `BASE` for this terminal window. Nothing is
printed.

**3. Check what you stored.**

```bash
echo "$BASE"
```
**What this does:** prints the `python@sha256:…` string. If it is empty, run command 2 again in
this window.

**4. Write a pinned Dockerfile.** One command, ending at `PY`:

```bash
python3 - <<'PY'
import os, pathlib
base = os.environ["BASE"]
src = pathlib.Path("Dockerfile").read_text()
assert src.count("FROM python:3.12-slim") == 2, "expected two FROM lines"
out = src.replace("FROM python:3.12-slim", f"FROM {base}")
pathlib.Path("Dockerfile.pinned").write_text(out)
print("pinned both stages to", base.split("@")[1][:19] + "...")
PY
```
**What this does:** replaces both `FROM` lines with the digest you just looked up. It fails loudly
if the file is not the one it expects, rather than writing something wrong.

> **If that command says `KeyError: 'BASE'`**, the variable did not reach Python. Run
> `export BASE="$BASE"` and try again — `export` makes a shell variable visible to programs the
> shell starts.

**5. Build it with real build metadata.**

```bash
docker build -f Dockerfile.pinned --build-arg GIT_SHA=$(git rev-parse --short HEAD) --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) -t paytrack-api:pinned .
```
**What this does:** `--build-arg` supplies the values the Dockerfile's `ARG` lines expect:
`$(git rev-parse --short HEAD)` is the commit you are on, and `$(date -u …)` is the time in UTC in
the format the OCI label standard uses.

**6. Read the labels back.**

```bash
docker inspect paytrack-api:pinned --format '{{json .Config.Labels}}' | python3 -m json.tool
```
**What this does:** prints the image's labels as formatted JSON (`python3 -m json.tool` is `jq`
without installing anything). `org.opencontainers.image.revision` now answers "which commit is
this?" for anyone holding the image.

**7. See the security cost of build arguments.**

```bash
docker history paytrack-api:pinned --no-trunc | grep -c "GIT_SHA"
```
**What this does:** counts the lines of build history mentioning `GIT_SHA` — it is **not** zero.
Build arguments are recorded in the image. They are fine for a commit hash; **never** pass a
password or token this way. Use `--mount=type=secret`, as in Part 5.

---

## Part 8 — Watch a HEALTHCHECK do its job (5 min)

**1. Start the pinned image.**

```bash
docker run -d --name paytrack-health -p 8080:8080 paytrack-api:pinned
```
**What this does:** `-d` runs it in the background and prints the container id; `-p 8080:8080`
publishes the port.

**2. Look at the status immediately.**

```bash
docker ps --filter name=paytrack-health --format "table {{.Names}}\t{{.Status}}"
```
**What this does:** the status reads `Up 2 seconds (health: starting)`. The Dockerfile's
`--start-period=10s` is a grace window in which a failing check does not count against the
container.

**3. Wait, then ask again.**

```bash
sleep 20 && docker inspect paytrack-health --format '{{.State.Health.Status}}'
```
**What this does:** `sleep 20` waits twenty seconds, then `&&` runs the inspect. It prints
`healthy` — the `curl -fsS http://localhost:8080/health` inside the container succeeded.

**4. Read the last check's output.**

```bash
docker inspect paytrack-health --format '{{json .State.Health}}' | python3 -m json.tool | tail -12
```
**What this does:** shows the failure count and the log of recent checks, including what each one
printed. This is the first place to look when a container is stuck `unhealthy`.

**5. Clean it up.**

```bash
docker rm -f paytrack-health
```
**What this does:** `rm -f` stops and removes the container in one step.

> 🔑 **This is what Compose gates on.** In Lab 07A, `depends_on: condition: service_healthy` waits
> for exactly this status. Without a `HEALTHCHECK` there is nothing to wait for.

---

## Part 9 — Build for a machine that is not yours (8 min, optional)

Your laptop builds for its own processor. If you are on Apple silicon or an ARM VM, the image you
just built **will not run** on the amd64 servers most CI and cloud hosts use.

**1. See which builders you have.**

```bash
docker buildx ls
```
**What this does:** lists build drivers and the platforms each can target. The default `docker`
driver usually shows only your own architecture.

**2. Create a builder that can do several.**

```bash
docker buildx create --name multi --driver docker-container --bootstrap --use
```
**What this does:** creates a builder that runs inside a container (that driver is the one that
supports multi-platform and remote caching), starts it (`--bootstrap`), and makes it the default
(`--use`).

**3. Check what it can target.**

```bash
docker buildx inspect multi | grep -i platforms
```
**What this does:** lists the platforms, including emulated ones such as `linux/amd64` on an ARM
machine.

**4. Build both architectures without pushing.**

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t paytrack-api:multi .
```
**What this does:** builds the image twice, once per platform. It ends with a warning that the
result was **not loaded** anywhere — that is expected and is the next point.

> 🔑 **A multi-platform image cannot live in your local image list.** The local store holds one
> image per name; a multi-platform result is a *manifest list* pointing at several. It has to go to
> a registry. The next two commands do that and need you to be logged in to GHCR (Lab 06 Step 7).
> **If you are not, skip to command 7.**

**5. Push it to your registry.**

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/<your-username>/paytrack-api:multi --push .
```
**What this does:** builds both and pushes them under one tag. Replace `<your-username>` with your
GitHub username, in lower case — GHCR rejects capitals.

**6. Look at what the tag really points to.**

```bash
docker buildx imagetools inspect ghcr.io/<your-username>/paytrack-api:multi
```
**What this does:** prints the manifest list: one digest per architecture under a single name. A
machine pulling that tag gets the entry matching its own processor, automatically.

**7. Switch back to your normal builder.**

```bash
docker buildx use default
```
**What this does:** makes plain `docker build` behave as it did before.

**8. Remove the temporary builder.**

```bash
docker buildx rm multi
```
**What this does:** stops and deletes the builder container. Its cache goes with it.

---

## Part 10 — Commit, and tidy up (5 min)

**1. Go back to the project root.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** git commands run from here.

**2. Stage the two new Dockerfiles.**

```bash
git add app/Dockerfile.cache app/Dockerfile.pinned
```
**What this does:** stages them by name, so nothing else can slip in.

**3. Check what is staged.**

```bash
git status -s
```
**What this does:** two `A` lines — added. If `requirements.txt` still shows as modified, run
`git restore app/requirements.txt`.

**4. Commit.**

```bash
git commit -m "build: add cache-mount and digest-pinned Dockerfile variants

Dockerfile.cache keeps the pip download cache in a BuildKit cache mount
instead of discarding it, so a dependency change re-resolves without
re-downloading. Dockerfile.pinned pins both stages to the base image digest
so a rebuild cannot silently pick up a different python:3.12-slim."
```
**What this does:** one command over several lines — copy all of it, both quote marks included.

**5. Remove the extra images.**

```bash
docker rmi paytrack-api:builder paytrack-api:cache paytrack-api:multi 2>/dev/null; docker images paytrack-api --format "table {{.Tag}}\t{{.Size}}"
```
**What this does:** deletes the tags this lab created (`2>/dev/null` hides errors for any that do
not exist), then lists what is left. Keep `1.0.0` — Labs 07 onwards use it.

**6. See how much the experiments cost you.**

```bash
docker system df
```
**What this does:** the build cache will have grown. `docker builder prune` reclaims it safely; the
next build is then slower once.

---

## What you measured

| Change | What rebuilt | Why |
|---|---|---|
| Nothing | nothing — every step `CACHED` | Same instructions, same inputs |
| `touch src/app.py` | the source `COPY` and everything after it | The source copy is last, deliberately |
| One comment in `requirements.txt` | `pip install` and everything after it | The dependency layer is keyed on that file's contents |
| The same comment, with a cache mount | `pip install` re-ran, but downloads came from cache | The mount survives builds and is not a layer |
| `git restore requirements.txt` | nothing — `CACHED` again | The cache is keyed on content, not on time |

---

## 🧩 Stretch (homework)

1. **Registry cache for CI.** Add `--cache-to type=registry,ref=ghcr.io/<you>/paytrack-api:buildcache,mode=max`
   and `--cache-from` to a buildx build, then delete your local cache with `docker builder prune -af`
   and rebuild. A cold CI runner can now hit a warm cache.
2. **Attestations.** Build with `--sbom=true --provenance=true --push`, then run
   `docker buildx imagetools inspect <ref> --format '{{json .SBOM}}'`. Compare what it lists with
   the Trivy output from Lab 06 Step 6.
3. **Prove the digest pin matters.** Run `docker pull python:3.12-slim` in a month, compare
   `docker image inspect python:3.12-slim --format '{{index .RepoDigests 0}}'` with the digest in
   `Dockerfile.pinned`, and note which of your two Dockerfiles would have changed behaviour.
4. **`dive`.** Install [dive](https://github.com/wagoodman/dive) and open `paytrack-api:1.0.0`.
   Find the layer with the worst "wasted space" score.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running, or your user is not in the `docker` group | Start Docker; log out and back in (Lab 00 Step 2) |
| `unknown flag: --mount` | The `# syntax=docker/dockerfile:1.7` line is missing from the file | It must be the **first** line; re-create `Dockerfile.cache` from Part 5 |
| `KeyError: 'BASE'` in Part 7 | The shell variable did not reach Python | `export BASE="$BASE"`, then run the box again |
| `docker image inspect python:3.12-slim` says *No such image* | The base was never pulled on its own | `docker pull python:3.12-slim`, then retry |
| `RepoDigests` is empty | The image was built locally and never pulled or pushed | Same fix — pull it from Docker Hub |
| Multi-platform build fails on an action or wheel | No build for that architecture | Build only your own platform, or use `--platform linux/amd64` alone |
| `denied: permission_denied` pushing to GHCR | Not logged in, or capitals in the name | `echo $(gh auth token) \| docker login ghcr.io -u <your-username> --password-stdin`; use lower case |
| The disk fills up | Several tagged copies plus build cache | `docker system df`, then `docker builder prune` |

---

## 🎯 Outcome

You can explain and **prove** what makes a Docker build slow, keep a package cache without shipping
it, build one stage of a multi-stage file for debugging, pin a base image so a rebuild is
repeatable, read the metadata that ties an image back to a commit, and produce an image that runs
on a processor different from your own.

**Next:** [Lab 07A — Compose in Depth](../lab-07-docker-compose-stack/README-07A-compose-in-depth.md),
or carry on with [Lab 07](../lab-07-docker-compose-stack/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 2 is the whole lab.** If you have ten minutes, do the three timed rebuilds on the
  projector and let the room call out which will be slow. The numbers land far harder than the
  ordering rule stated as advice.
- **Part 5 catches people out** because the Lab 06 Dockerfile deliberately sets
  `PIP_NO_CACHE_DIR=1`. Ask why removing that line is safe *here* and not in the original — the
  answer is that the cache now lives in a mount, not a layer.
- **Things that go wrong:**
  1. A stale `requirements.txt` left modified after Part 2 or 5 — `git status -s` before committing.
  2. Part 9 on a machine with no GHCR login. It is written so commands 5 and 6 can be skipped.
  3. Delegates run out of disk after tagging four copies. `docker system df` in Part 10 is there
     for that reason.
- **Debrief question:** "Your CI build takes eleven minutes. Before you buy a bigger runner, which
  measurement from this lab tells you whether that is the dependency layer or the source layer?"
</details>
