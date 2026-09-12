# Module 3 — Containers with Docker

> **Day 3 · ~65 minutes of lecture · Labs 06, 07, 08**
>
> **Learning outcomes.** You can explain what a container actually is at the kernel level,
> describe Docker's architecture and the image layer model, write a production-grade
> multi-stage Dockerfile, compose a multi-service stack, reason about container networking
> and data persistence, and apply the security practices that separate a demo image from a
> shippable one.

---

## 3.1 Containerisation concepts

### The definition

> **Container** — an isolated process (or process group) running on a shared host kernel,
> whose visible filesystem, network, process tree, users and resource limits are restricted
> by kernel features, and whose filesystem is supplied by an immutable image.

Read that again and notice what is **not** there: no hypervisor, no guest operating system,
no virtual hardware. **A container is a process.** `ps aux` on the host shows it. This is
the single most important sentence in the module — almost every container misconception
comes from imagining a tiny VM.

### The problem containers solve

```
        "It works on my machine"                 The dependency matrix from hell
 ┌──────────────────────────────────┐    ┌────────────────────────────────────────────┐
 │ dev:     Python 3.12, glibc 2.39 │    │           dev  test  staging  prod          │
 │ CI:      Python 3.10, glibc 2.35 │    │ app A      ✓     ✓      ✓       ✗          │
 │ staging: Python 3.11, musl       │    │ app B      ✓     ✗      ✓       ✓          │
 │ prod:    Python 3.9  (!!)        │    │ app C      ✗     ✓      ✓       ✓          │
 └──────────────────────────────────┘    └────────────────────────────────────────────┘
        ↓                                                    ↓
   Containers ship the application AND its entire userspace as one immutable artefact.
   The only shared surface left is the kernel's system-call interface.
```

### Virtual machines vs containers

```
        VIRTUAL MACHINES                          CONTAINERS
 ┌───────┬───────┬───────┐                ┌───────┬───────┬───────┐
 │ App A │ App B │ App C │                │ App A │ App B │ App C │
 ├───────┼───────┼───────┤                ├───────┼───────┼───────┤
 │ Bins  │ Bins  │ Bins  │                │ Bins  │ Bins  │ Bins  │  ← from the image
 ├───────┼───────┼───────┤                ├───────┴───────┴───────┤
 │Guest  │Guest  │Guest  │  ← 1-4 GB      │  Container runtime    │  ← containerd + runc
 │  OS   │  OS   │  OS   │     each       ├───────────────────────┤
 ├───────┴───────┴───────┤                │       HOST OS         │  ← ONE shared kernel
 │      HYPERVISOR       │                ├───────────────────────┤
 ├───────────────────────┤                │       HARDWARE        │
 │       HOST OS         │                └───────────────────────┘
 ├───────────────────────┤
 │       HARDWARE        │
 └───────────────────────┘
```

| | **Virtual machine** | **Container** |
|---|---|---|
| Isolation boundary | Hardware virtualisation (very strong) | Kernel namespaces + cgroups (strong, but *shared kernel*) |
| Guest OS | Full OS per VM | None — shares the host kernel |
| Size | Gigabytes | Megabytes |
| Start time | 30 s – minutes | **10–200 ms** |
| Density per host | Tens | Hundreds to thousands |
| Kernel choice | Any OS | Must be compatible with the host kernel (Linux containers need a Linux kernel) |
| Blast radius of a kernel exploit | One VM | Potentially **every container on the host** |

**They are not competitors.** In production you almost always run containers *inside* VMs:
the VM gives you a hard multi-tenant boundary, the container gives you density and
packaging speed.

### The three kernel features that make a container

**1. Namespaces — what the process can *see*.** (Linux, `unshare(2)`, `clone(2)`)

| Namespace | Isolates | Effect inside the container |
|---|---|---|
| `pid` | Process IDs | Your app is PID 1; it cannot see host processes |
| `net` | Network stack | Own interfaces, IPs, routes, ports, iptables |
| `mnt` | Mount points | Own filesystem tree (the image) |
| `uts` | Hostname/domain | Own hostname |
| `ipc` | SysV IPC, POSIX queues | Cannot talk to host shared memory |
| `user` | UID/GID mapping | Can be root *inside* while unprivileged outside |
| `cgroup` | Cgroup root | Cannot see the host's cgroup hierarchy |

**2. Control groups (cgroups v2) — what the process can *use*.** Hard and soft limits on
CPU, memory, block I/O, PIDs and devices. `--memory=512m` writes to `memory.max`; when the
process exceeds it the kernel OOM-kills it. Without limits, one container can starve every
other container on the host — this is why resource limits are not optional in production.

**3. Union filesystem (OverlayFS) — how images stay small.** Multiple read-only layers are
stacked and presented as one tree, with a thin writable layer on top. Writing to an existing
file triggers **copy-up**: the file is copied into the writable layer and modified there.

```
 ┌────────────────────────────────────────┐
 │  CONTAINER WRITABLE LAYER  (ephemeral) │ ← dies with the container. Never store data here.
 ├────────────────────────────────────────┤
 │  L4  COPY . /app                       │ ┐
 ├────────────────────────────────────────┤ │
 │  L3  RUN pip install -r requirements   │ │ read-only, content-addressed,
 ├────────────────────────────────────────┤ │ SHARED between all containers
 │  L2  RUN apt-get install …             │ │ from the same image
 ├────────────────────────────────────────┤ │
 │  L1  FROM python:3.12-slim             │ ┘
 └────────────────────────────────────────┘
```

Ten containers from one image consume the image's disk **once**, plus ten small writable
layers. That is why container density is so high.

### Standards — why this is not Docker-specific

The **OCI (Open Container Initiative)** defines three specifications: the **image-spec**
(the format of an image), the **runtime-spec** (how to run a bundle) and the
**distribution-spec** (how registries serve images). Because of the OCI, an image built by
Docker runs on containerd, CRI-O or Podman, and pushes to any compliant registry. You are
learning a **standard**, not a product.

---

## 3.2 Docker architecture

```
  ┌──────────────┐        REST over            ┌──────────────────────────────────────┐
  │ docker CLI   │ ─── /var/run/docker.sock ──►│         dockerd  (daemon)            │
  │ (client)     │                             │  images · containers · networks ·    │
  └──────────────┘                             │  volumes · builds (BuildKit)         │
  ┌──────────────┐                             └───────────────┬──────────────────────┘
  │ docker       │ ────────────────────────────────────────────┤ gRPC
  │ compose      │                             ┌───────────────▼──────────────────────┐
  └──────────────┘                             │  containerd  (container lifecycle)   │
                                               └───────────────┬──────────────────────┘
  ┌──────────────┐   pull / push               ┌───────────────▼──────────────────────┐
  │  REGISTRY    │◄────────────────────────────│  runc  (OCI runtime: makes the actual │
  │ ghcr.io /    │                             │  namespaces + cgroups syscalls)      │
  │ docker.io    │                             └───────────────┬──────────────────────┘
  └──────────────┘                                             ▼
                                                        ┌──────────────┐
                                                        │  LINUX KERNEL │
                                                        └──────────────┘
```

| Component | Responsibility |
|---|---|
| **docker CLI** | Sends REST calls to the daemon. Holds no state. |
| **dockerd** | The daemon: builds images, manages containers/networks/volumes, talks to registries |
| **BuildKit** | The modern build engine — parallel stages, better caching, build secrets, mount caches |
| **containerd** | Industry-standard container lifecycle manager (also what Kubernetes uses) |
| **runc** | The reference OCI runtime; actually creates namespaces and cgroups |
| **Registry** | Stores and serves images (Docker Hub, GHCR, Harbor, ECR…) |

> ⚠️ **`/var/run/docker.sock` is root.** The daemon runs as root, and the socket is its API.
> Membership of the `docker` group is **equivalent to root on the host** — a user in that
> group can `docker run -v /:/host --privileged` and own the machine. Treat it as a
> privilege grant, not a convenience. Rootless mode and Podman exist to address this.

---

## 3.3 Images

> **Image** — an immutable, layered, content-addressed template containing a filesystem and
> metadata (entrypoint, env, exposed ports, user). Images are *built*; containers are
> *instantiated from* them.

### Naming

```
   ghcr.io / my-org / paytrack-api : 1.4.2 @sha256:9f3e2a…
   ───────   ──────   ─────────   ─────  ──────────────
   registry  namespace  repo      tag      digest (immutable)
```

- Omit the registry and Docker Hub (`docker.io`) is assumed.
- Omit the tag and `:latest` is assumed — **`latest` is just a default string, not a
  promise**. It is a mutable pointer that can change under you.
- The **digest** is the only truly immutable reference. Pin base images by digest in any
  build you care about reproducing.

### Layers and the build cache

Each Dockerfile instruction that changes the filesystem creates a layer. Docker caches
layers and reuses them if the instruction **and all preceding layers** are unchanged.

```
 SLOW  (cache busted on every source change)      FAST  (dependencies cached)
 ─────────────────────────────────────────       ────────────────────────────────────────
 FROM python:3.12-slim                            FROM python:3.12-slim
 COPY . /app          ← any file change …         COPY requirements.txt .
 RUN pip install -r requirements.txt              RUN pip install -r requirements.txt   ← cached
                      ← … re-runs pip             COPY . /app          ← only this rebuilds
```

**The rule: order instructions from least-frequently-changed to most-frequently-changed.**
Getting this one thing right typically takes a 3-minute build to 15 seconds.

### Layers are additive — deletions do not shrink an image

```dockerfile
RUN apt-get install -y build-essential      # layer 1: +300 MB
RUN apt-get remove  -y build-essential      # layer 2: marks files deleted; image is STILL +300 MB
```
The bytes remain in layer 1 and **remain extractable by anyone who pulls the image.** This
is also how secrets leak: `COPY id_rsa .` followed by `RUN rm id_rsa` leaves the key in the
image forever. The fixes are **a single `RUN` with cleanup in the same layer**, and
**multi-stage builds**.

---

## 3.4 Containers

> **Container** — a runnable instance of an image: the image's layers, plus a writable
> layer, plus namespace/cgroup configuration, plus a process.

### Lifecycle

```
                docker create              docker start
   [image] ──────────────────► [created] ──────────────► [running] ──────┐
                                                        │  ▲  │         │
                                        docker pause ───┘  │  └── docker stop  (SIGTERM,
                                                           │          then SIGKILL after 10 s)
                                        docker unpause ────┘                    │
                                                                                ▼
   [removed] ◄──── docker rm ──── [exited]  ◄─────────── process exits ────── [stopping]
                                      │
                                      └── docker start (restart, same writable layer)
```

**`docker stop` sends `SIGTERM`, waits (default 10 s), then `SIGKILL`.** Your PID 1 must
handle `SIGTERM` and shut down gracefully, or every deployment drops in-flight requests.
This matters enormously in Kubernetes, where pods are terminated constantly.

### The PID 1 problem

In a container your process is PID 1, which in Linux has special duties: it must reap
orphaned child processes and it does **not** get default signal handlers. A shell-form
`CMD python app.py` runs under `/bin/sh -c`, and `sh` does not forward `SIGTERM` to the
child — so your app never receives the shutdown signal. Fixes: use **exec form**
(`CMD ["python", "app.py"]`), or add an init (`docker run --init`, or `tini`).

---

## 3.5 Dockerfile — instruction reference

| Instruction | Purpose | Notes and traps |
|---|---|---|
| `FROM image:tag@digest` | Base image; starts a build stage | Pin by digest for reproducibility. `FROM scratch` = empty |
| `ARG name=default` | **Build-time** variable | Only available during build. **Visible in image history — never put secrets here** |
| `ENV KEY=value` | **Runtime** environment variable | Persists into the running container and into `docker inspect` |
| `WORKDIR /app` | Set (and create) the working directory | Always prefer this to `RUN cd` — `cd` does not persist across layers |
| `COPY src dst` | Copy files from the build context | **Preferred.** Respects `.dockerignore` |
| `ADD src dst` | Copy, plus auto-extract tarballs and fetch URLs | Avoid — the magic is surprising. Use `COPY`, or `RUN curl` |
| `RUN cmd` | Execute during build, creating a layer | Chain with `&&` and clean up **in the same instruction** |
| `CMD ["a","b"]` | Default command, **overridable** by `docker run` args | Exec form (JSON array) — not shell form |
| `ENTRYPOINT ["a"]` | The executable; `CMD` becomes its default arguments | Use for "this image *is* a program" |
| `EXPOSE 8080` | **Documentation only.** Publishes nothing | Actual publishing is `-p` / `ports:` |
| `USER appuser` | Drop privileges for all subsequent instructions and at runtime | **Do this. Default is root.** |
| `VOLUME /data` | Declare a mount point | Prefer declaring volumes at run time; `VOLUME` in a Dockerfile can surprise |
| `HEALTHCHECK` | Command Docker runs to judge container health | Compose can wait on it; Kubernetes ignores it (use probes) |
| `LABEL k=v` | Metadata | Use OCI labels: `org.opencontainers.image.source`, `.revision` |
| `STOPSIGNAL` | Signal sent on stop | Change only if your app expects something other than SIGTERM |

### `CMD` vs `ENTRYPOINT` — the table that settles it

| Dockerfile | `docker run img` | `docker run img echo hi` |
|---|---|---|
| `CMD ["python","app.py"]` | `python app.py` | `echo hi` (CMD replaced) |
| `ENTRYPOINT ["python","app.py"]` | `python app.py` | `python app.py echo hi` (appended) |
| `ENTRYPOINT ["python"]` + `CMD ["app.py"]` | `python app.py` | `python echo hi` |

### `.dockerignore` — do not skip this

The **build context** is everything sent to the daemon before the build starts. Without a
`.dockerignore`, you ship `.git/`, `.venv/`, `node_modules/`, `*.log` and possibly `.env`
into the build — slowing builds, busting cache and risking secret leakage.

```
.git
.venv
__pycache__
*.pyc
.env
.pytest_cache
terraform/.terraform
```

---

## 3.6 Multi-stage builds

> **Multi-stage build** — a Dockerfile with several `FROM` instructions, where later stages
> copy only the *artefacts* they need from earlier stages. Everything else — compilers,
> headers, build caches, source, credentials — is discarded.

```
 ┌──────────────── STAGE 1: builder ────────────────┐    ┌──────── STAGE 2: runtime ────────┐
 │ FROM python:3.12-slim AS builder                 │    │ FROM python:3.12-slim            │
 │  • build-essential, gcc, headers                 │    │  • NO compiler                   │
 │  • pip wheel / install into /install             │───►│  • COPY --from=builder /install  │
 │  • test dependencies                             │    │  • COPY src/                     │
 │  ≈ 900 MB                                        │    │  • USER 10001                    │
 │  DISCARDED — never shipped, never scanned        │    │  ≈ 120 MB  ← this is the artefact│
 └──────────────────────────────────────────────────┘    └──────────────────────────────────┘
```

Three wins, all of them significant:

1. **Size** — smaller images pull faster, which directly reduces deployment and
   autoscaling latency.
2. **Security** — no compiler, no package manager, no source in the shipped image means a
   dramatically smaller attack surface and far fewer CVEs to triage in Lab 17.
3. **Secret hygiene** — build-time credentials live only in the discarded stage.

You will measure the difference yourself in Lab 06 (expect roughly an 8× reduction).

### Base image choice

| Base | Size | Trade-off |
|---|---|---|
| `python:3.12` | ~1 GB | Everything included; large attack surface |
| `python:3.12-slim` | ~150 MB | **Good default.** Debian, glibc, apt available |
| `python:3.12-alpine` | ~50 MB | musl libc — breaks manylinux wheels, forces slow source builds, and has caused real DNS and timing bugs. Small is not free. |
| `gcr.io/distroless/python3` | ~50 MB | No shell, no package manager. Excellent security, harder to debug |
| `scratch` | 0 | Static binaries only (Go, Rust) |

**Recommendation for this course and for most Python services: `-slim`.** Alpine's size win
is usually erased by the wheel-compilation problem.

---

## 3.7 Docker Compose

> **Docker Compose** — a tool for defining and running a multi-container application from a
> single declarative YAML file, so that an entire local environment starts with one command.

Compose is where "works on my machine" is finally killed for *the whole stack*, not just
one process. It is also where new joiners go from "three days of setup" to `docker compose
up`.

```yaml
services:
  api:
    build: { context: ./app, dockerfile: Dockerfile }   # build from source, or use image:
    image: paytrack-api:local
    environment:
      DATABASE_URL: postgresql://paytrack:paytrack@db:5432/paytrack   # "db" = the service name = DNS
    ports: ["8080:8080"]                                # host:container
    depends_on:
      db: { condition: service_healthy }                # WAIT for the healthcheck, not just start
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s
    restart: unless-stopped
  db:
    image: postgres:16-alpine
    environment: { POSTGRES_USER: paytrack, POSTGRES_PASSWORD: paytrack, POSTGRES_DB: paytrack }
    volumes: ["pgdata:/var/lib/postgresql/data"]        # named volume → data survives
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paytrack"]
      interval: 5s
      retries: 10
volumes:
  pgdata:
networks:
  default: { name: paytrack-net }
```

| Key | Meaning |
|---|---|
| `services` | Each becomes one container, reachable from the others **by service name** |
| `build` vs `image` | Build from a Dockerfile, or pull a published image (use `image:` in production) |
| `depends_on` | Start ordering. **`condition: service_healthy` is what you want** — plain `depends_on` waits only for *start*, not for *ready*, which is the #1 Compose bug |
| `healthcheck` | How Compose decides a service is ready |
| `ports` | `"HOST:CONTAINER"`. Omit to keep a service private to the network |
| `volumes` | Named volume (managed by Docker) or bind mount (`./src:/app/src`) |
| `restart` | `no` / `on-failure` / `always` / `unless-stopped` |
| `profiles` | Optional services (e.g. `--profile debug`) |

Essential commands: `docker compose up -d --build`, `ps`, `logs -f api`, `exec api sh`,
`down` (keeps volumes), `down -v` (**deletes volumes — destroys your data**).

> **Compose is not an orchestrator.** It runs on one host: no rescheduling on node failure,
> no rolling updates, no horizontal autoscaling, no multi-host networking. That gap is
> exactly what Module 4 fills.

---

## 3.8 Docker networking

### The drivers

| Driver | Behaviour | Use for |
|---|---|---|
| **bridge** (default) | Private virtual L2 network on the host; containers get an IP; outbound is NAT'd | Single-host apps. **This is what Compose creates** |
| **host** | No network namespace — the container uses the host's stack directly | Latency-critical or when you need many ports. No isolation; `-p` is ignored |
| **none** | Only loopback | Batch jobs that must not touch the network |
| **overlay** | Multi-host VXLAN network | Swarm / multi-host |
| **macvlan** | Container gets a MAC and an IP on the physical LAN | Legacy apps that must appear as physical hosts |

### The critical distinction: default bridge vs user-defined bridge

```
 DEFAULT BRIDGE ("docker0")            USER-DEFINED BRIDGE (what Compose makes)
 ┌────────────────────────┐            ┌──────────────────────────────────────┐
 │ ✗ NO automatic DNS     │            │ ✓ Automatic DNS by container/service │
 │   between containers   │            │   name  →  "db" resolves to db's IP  │
 │ ✗ Legacy --link only   │            │ ✓ Containers attach/detach live      │
 │ ✓ All containers share │            │ ✓ Better isolation between stacks    │
 │   one flat network     │            │ ✓ Custom subnets                     │
 └────────────────────────┘            └──────────────────────────────────────┘
```

**Always create a user-defined network.** Service-name DNS is the mechanism that lets
`DATABASE_URL=postgresql://…@db:5432/…` work with no IP addresses anywhere in your config
— and it is what makes the same config work unchanged in Kubernetes, where Services provide
the identical name-based discovery.

### Port publishing

```
 docker run -p 8080:8080 paytrack-api      # host 8080 → container 8080, ALL host interfaces
 docker run -p 127.0.0.1:8080:8080 …    # bound to loopback only — safer on a shared box
 docker run -P paytrack-api                # publish every EXPOSEd port to random high ports
 (no -p at all)                          # unreachable from the host; reachable from siblings
```

⚠️ **Docker writes iptables rules directly and bypasses UFW.** A `-p 0.0.0.0:5432:5432` on
a cloud VM exposes your database to the internet even with `ufw deny 5432` active. Bind
sensitive ports to `127.0.0.1` explicitly. This has caused real breaches.

### Inside a container, `localhost` is the container

The most common beginner error: `DATABASE_URL=postgresql://…@localhost:5432/…` inside the
API container refers to *the API container's own loopback*, where nothing is listening. Use
the **service name** (`db`). From the host to a container, use `localhost:<published port>`.
From a container to the host, use `host.docker.internal` (add
`--add-host=host.docker.internal:host-gateway` on Linux).

---

## 3.9 Storage: volumes and bind mounts

**The container writable layer is ephemeral.** `docker rm` destroys it. Any data that must
outlive a container needs to be outside the union filesystem.

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  CONTAINER                                                                   │
 │   /app          ← image layers (read-only)                                   │
 │   /tmp          ← writable layer   ✗ DESTROYED on docker rm                  │
 │   /var/lib/postgresql/data  ──────► NAMED VOLUME "pgdata"  ✓ survives        │
 │   /app/src      ──────────────────► BIND MOUNT ./app/src   ✓ live host files │
 │   /run/secrets  ──────────────────► TMPFS  (RAM only, never on disk)         │
 └──────────────────────────────────────────────────────────────────────────────┘
```

| Type | Syntax | Stored | Use for |
|---|---|---|---|
| **Named volume** | `-v pgdata:/var/lib/postgresql/data` | Docker-managed (`/var/lib/docker/volumes/`) | **Production data.** Portable, backup-able, no host-path coupling, correct permissions |
| **Bind mount** | `-v $(pwd)/app/src:/app/src` | Any host path | **Development.** Edit on the host, see it live in the container |
| **tmpfs** | `--tmpfs /run/secrets` | Host RAM only | Secrets and scratch data that must never touch disk |
| **Anonymous volume** | `-v /data` | Docker-managed, random name | Almost never — you will lose track of it |

**Backing up a named volume** (no dedicated command exists — this is the idiom):

```bash
docker run --rm -v pgdata:/data -v "$PWD":/backup alpine \
  tar czf /backup/pgdata-$(date +%F).tar.gz -C /data .
```
A throwaway container mounts the volume read-write and your current directory, and tars one
into the other.

---

## 3.10 Container best practices

### Image hygiene

1. **Pin base images by digest**, not by a floating tag.
2. **Multi-stage builds** — ship runtime only.
3. **One concern per container.** Not "one process" dogmatically, but one job.
4. **Order layers cache-friendly**: dependencies before source.
5. **Chain `RUN` + clean up in the same layer**
   (`apt-get install … && rm -rf /var/lib/apt/lists/*`).
6. **Always ship a `.dockerignore`.**
7. **Exec-form `CMD`/`ENTRYPOINT`**, so signals reach your process.
8. **Add OCI labels** (`org.opencontainers.image.source`, `.revision`) so an image can be
   traced back to the commit that built it.
9. **Tag with the git SHA.** Never deploy `:latest`.

### Security

10. **`USER` a non-root, numeric, high UID** (e.g. `10001`) — numeric so Kubernetes'
    `runAsNonRoot` can verify it without resolving `/etc/passwd`.
11. **Read-only root filesystem** (`--read-only`) plus a `tmpfs` for anything that must be
    written.
12. **Drop all capabilities** and add back only what is needed:
    `--cap-drop=ALL --cap-add=NET_BIND_SERVICE`.
13. **`--security-opt=no-new-privileges`** blocks setuid escalation inside the container.
14. **Never bake secrets into images.** Use BuildKit `--mount=type=secret` at build time,
    and env/files/secret-managers at run time. `docker history` shows every `ARG` and `ENV`.
15. **Set resource limits** (`--memory`, `--cpus`) always.
16. **Scan images in CI** and fail the build on HIGH/CRITICAL — Lab 17.
17. **Never mount `/var/run/docker.sock`** into a container you do not fully trust; it is
    root on the host.

### Operability

18. **Log to stdout/stderr**, structured JSON. The platform collects it; do not write log
    files inside a container.
19. **Config from the environment.** One image, many environments.
20. **Handle `SIGTERM`** and shut down gracefully.
21. **Expose a health endpoint** that is cheap and dependency-aware.
22. **Keep containers stateless**; push state to volumes or a database.

---

## 3.11 Key terms

| Term | Definition |
|---|---|
| **Image** | Immutable layered template a container is created from |
| **Layer** | One read-only filesystem diff, content-addressed |
| **Container** | A running (or stopped) instance of an image; a process with isolation |
| **Registry / Repository / Tag / Digest** | Where images live / the named collection / a mutable alias / the immutable content hash |
| **Build context** | Files sent to the daemon at build time; filtered by `.dockerignore` |
| **Multi-stage build** | Build in one stage, ship only artefacts in another |
| **Namespace** | Kernel feature isolating what a process can see |
| **cgroup** | Kernel feature limiting what a process can use |
| **OverlayFS / copy-up** | Union filesystem; copying a file into the writable layer to modify it |
| **OCI** | Open Container Initiative — the image, runtime and distribution standards |
| **containerd / runc** | Lifecycle manager / low-level OCI runtime |
| **Bind mount / Named volume / tmpfs** | Host path / Docker-managed storage / RAM-backed storage |
| **User-defined bridge** | Docker network providing container-name DNS |
| **Compose** | Declarative multi-container definition for a single host |
| **Distroless** | Base image with no shell or package manager |
| **Rootless mode** | Running the daemon and containers as an unprivileged user |

---

## 3.12 Module 3 self-check

1. A colleague says "a container is a lightweight VM." Give a two-sentence correction that
   also explains the security implication.
2. Your image is 1.2 GB. Name the three changes most likely to have the largest effect.
3. Your Dockerfile has `COPY . /app` before `RUN pip install`. What is the consequence, and
   what is the fix?
4. `RUN apt-get install x` then `RUN apt-get remove x` — what is the image size impact, and
   why?
5. Your app in a container connects to `localhost:5432` for Postgres running in a sibling
   container. Why does it fail? Give the fix.
6. `docker compose down -v` — what exactly is destroyed, and why is this dangerous?
7. Your container ignores `docker stop` and takes 10 seconds to die every time. Give the
   two most likely causes.
8. Why is `USER 10001` better than `USER appuser` for a Kubernetes workload?

---

**Next:** [Module 4 — Kubernetes for DevOps](module-04-kubernetes.md)
· Labs: [06](../../labs/lab-06-docker-images/README.md) ·
[07](../../labs/lab-07-docker-compose-stack/README.md) ·
[08](../../labs/lab-08-docker-networking-volumes/README.md)
