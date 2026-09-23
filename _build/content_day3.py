# -*- coding: utf-8 -*-
"""Day 3 — Containers with Docker.  Module 3.

Theory-first edition: mostly theory with exercises and two live demos; Labs 06–08 are
started together at the end of the session and finished after class.
"""
import diagrams as dg

DAY3 = [
 ('title', 3, 'Containers with Docker',
  'Build once, run identically, everywhere — and measure the difference',
  ['What a container really is: namespaces, cgroups, OverlayFS · the Docker architecture',
   'Images, layers and the cache · Dockerfile craft · multi-stage builds · hardening',
   'Compose · networking · volumes and persistence',
   'After class — Labs 06–08: build and publish · a full stack · prove the isolation'],
  'By the end of Lab 06 PayTrack API is a non-root, multi-stage image under 200 MB, published by CI'),

 ('agenda', 'Day 3 at a glance',
  [('theory', 'What a container is · VMs vs containers · namespaces, cgroups, OverlayFS'),
   ('demo', 'A container is just a process'),
   ('theory', 'The Docker architecture · images, naming, layers and the build cache'),
   ('exercise', 'PREDICT — how big is your image, really?'),
   ('theory', 'The container lifecycle · the PID 1 problem · Dockerfile instructions'),
   ('break', 'Break · 15 minutes'),
   ('theory', 'Multi-stage builds · base images · security and operability practices'),
   ('demo', 'Does PID 1 hear SIGTERM?'),
   ('theory', 'Docker Compose · networking and the UFW bypass · volumes and backups'),
   ('practical', 'Start Lab 06 together: .dockerignore and the naive build'),
   ('check', 'Check-in 2 — the halfway pulse (5 minutes)'),
   ('after', 'Finish Labs 06–08 · Day 4 starts from your Lab 06 image')],
  'TODAY', {'speaker': 'Day 3 closes with check-in 2. Day 4 needs the Lab 06 image and the Lab 07 stack, '
            'so make sure everyone knows the RECOVER blocks exist.'}),

 ('bullets', 'What today gives you',
  [('A precise answer to "what is a container?"', 'A process with kernel isolation — not a small virtual machine'),
   ('The mental model behind every Docker command', 'Client, daemon, containerd, runc, the kernel, the registry'),
   ('Dockerfiles that build fast and ship small', 'Layer ordering, multi-stage builds, the right base image'),
   ('Images that are safe to run in a bank', 'Non-root, no secrets in layers, minimal attack surface'),
   ('A whole stack on one laptop', 'Compose, service-name DNS, and data that survives'),
   ('The two operational facts people get burned by', 'localhost inside a container, and Docker bypassing UFW')],
  'TODAY'),

 ('section', '1', 'What a Container Is', 'A process, not a small virtual machine',
  ['The definition', 'Containers vs virtual machines', 'Namespaces and cgroups',
   'OverlayFS and copy-up', 'The OCI standards']),

 ('define', 'Container',
  'An isolated process, or process group, running on a shared host kernel — whose view of the filesystem, '
  'network, process tree and users, and whose resource use, are restricted by kernel features, and whose '
  'filesystem comes from an immutable image.',
  [('No hypervisor, no guest operating system, no virtual hardware', 'Almost every container misconception comes from imagining a tiny VM'),
   ('A container IS a process', 'ps aux on the host shows it — you will see that in the demo'),
   ('NAMESPACES control what it can SEE', 'Its own process tree, network stack, mounts and hostname'),
   ('CGROUPS control what it can USE', 'CPU, memory, I/O and process count — a security control, not only a performance one')],
  'MODULE 3 §3.1'),

 ('two', 'The problem containers solve',
  ('"IT WORKS ON MY MACHINE"', ['dev: Python 3.12 on glibc 2.39',
                               'CI: Python 3.10 on glibc 2.35',
                               'staging: Python 3.11 on musl',
                               'production: Python 3.9 (!)',
                               '✗ Every environment is a different program'], 'red'),
  ('THE CONTAINER ANSWER', ['✔ Ship the application AND its entire userspace',
                            '✔ One immutable artefact, identical everywhere',
                            '✔ The only shared surface is the kernel system-call interface',
                            '✔ What you tested is bit-for-bit what runs',
                            '→ Which is why we build once and promote'], 'green'),
  'MODULE 3 §3.1'),

 ('diagram', 'Containers are not small virtual machines', dg.vm_vs_container, 'MODULE 3 §3.1'),

 ('table', 'Virtual machines and containers, side by side',
  ['', 'Virtual machine', 'Container'],
  [['Isolation boundary', 'Hardware virtualisation — very strong', 'Namespaces + cgroups — strong, but a SHARED kernel'],
   ['Guest OS', 'A full OS in every VM', 'None — shares the host kernel'],
   ['Size', 'Gigabytes', 'Megabytes'],
   ['Start time', '30 seconds to minutes', '10–200 milliseconds'],
   ['Density per host', 'Tens', 'Hundreds to thousands'],
   ['Kernel choice', 'Any operating system', 'Must match the host kernel (Linux containers need Linux)'],
   ['A kernel exploit reaches', 'One VM', '✗ Potentially every container on the host']],
  'MODULE 3 §3.1', {'widths': [2.3, 3.6, 4.4],
   'note': ('NOT COMPETITORS', 'In production you almost always run containers INSIDE virtual machines: '
            'the VM gives a hard multi-tenant boundary, the container gives density and packaging speed.')}),

 ('table', 'Namespaces — what the process can see',
  ['Namespace', 'Isolates', 'Effect inside the container'],
  [['pid', 'Process IDs', 'Your application is PID 1 and cannot see host processes'],
   ['net', 'The network stack', 'Its own interfaces, IP addresses, routes, ports and iptables'],
   ['mnt', 'Mount points', 'Its own filesystem tree — the image'],
   ['uts', 'Hostname and domain', 'Its own hostname'],
   ['ipc', 'SysV IPC, POSIX queues', 'Cannot reach host shared memory'],
   ['user', 'UID/GID mapping', 'Can be root inside while unprivileged outside'],
   ['cgroup', 'The cgroup root', 'Cannot see the host\'s cgroup hierarchy']],
  'MODULE 3 §3.1', {'widths': [1.6, 3.0, 5.4]}),

 ('define', 'Control groups (cgroups v2)',
  'The kernel feature that limits what a process can USE: CPU, memory, block I/O, the number of processes, '
  'and device access.',
  [('--memory=512m writes to memory.max', 'Exceed it and the kernel OOM-kills the process — exit code 137'),
   ('--cpus=0.5 throttles, it does not kill', 'A CPU-limited container gets slower, not dead'),
   ('A pids limit stops a fork bomb', 'One runaway container cannot exhaust the host\'s process table'),
   ('Without limits, one container can starve every other', 'Which is why limits are not optional in production'),
   ('The same mechanism sits under Kubernetes', 'Day 4\'s requests and limits are cgroups with a scheduler on top')],
  'MODULE 3 §3.1'),

 ('demo', 'A container is just a process',
  '''$ docker run -d --name demo --memory 256m nginx:1.27
$ docker top demo               # the container's processes...
$ ps -o pid,user,cmd -C nginx   # ...are host processes
$ PID=$(docker inspect -f '{{.State.Pid}}' demo)
$ sudo ls -l /proc/$PID/ns      # its namespaces
$ docker exec demo cat /sys/fs/cgroup/memory.max
268435456
$ docker rm -f demo''',
  [('docker top and ps show the same processes', 'There is no hidden VM — the host kernel runs them'),
   ('/proc/<pid>/ns lists pid, net, mnt, uts, ipc…', 'Each link is a namespace the process has joined'),
   ('memory.max is 268435456', '256 MiB in bytes — --memory is literally a cgroup file'),
   ('Nothing here is Docker-specific', 'It is Linux; Docker is a friendly way to ask for it')],
  {'minutes': 6, 'speaker': 'The goal is to replace the "tiny VM" picture for good. Pause on the ps output: '
   'the nginx processes are visible from the host with host PIDs.'}),

 ('define', 'Union filesystem (OverlayFS) and copy-up',
  'Several read-only image layers are stacked and presented as one directory tree, with a thin writable layer '
  'on top that belongs to one container.',
  [('The image layers are read-only and SHARED', 'Ten containers from one image use its disk space once'),
   ('The writable layer is ephemeral', 'It dies with the container — never store data there'),
   ('Copy-up', 'Modifying an existing file first copies it into the writable layer'),
   ('Deletion hides a file, it does not remove it', 'A "whiteout" in the top layer — the bytes stay below')],
  'MODULE 3 §3.1'),

 ('bullets', 'The OCI standards — why this is not Docker-specific',
  [('Image specification', 'The format of an image: layers, config, manifest'),
   ('Runtime specification', 'How to run a filesystem bundle as a container'),
   ('Distribution specification', 'How registries store and serve images'),
   ('The practical result', 'An image built by Docker runs on containerd, CRI-O or Podman, and pushes to any compliant registry'),
   ('You are learning a standard, not a product', 'The same images run on Kubernetes tomorrow')],
  'MODULE 3 §3.1'),

 ('section', '2', 'Docker Architecture & Images', 'Who does what, and how images are built',
  ['Client, daemon, containerd, runc', 'Image names and digests', 'Layers and the build cache',
   'Why deleting does not shrink an image']),

 ('diagram', 'The Docker architecture', dg.docker_architecture, 'MODULE 3 §3.2',
  {'speaker': 'Stress the red box. In a bank, "add the build user to the docker group" is a root grant, and '
   'should be reviewed as one.'}),

 ('define', 'Image',
  'An immutable, layered, content-addressed template containing a filesystem and metadata — entrypoint, '
  'environment, exposed ports, user. Images are BUILT; containers are INSTANTIATED from them.',
  [('Immutable', 'You never change an image — you build a new one with a new digest'),
   ('Layered', 'Each filesystem-changing instruction adds a layer, shared and cached'),
   ('Content-addressed', 'The digest is a hash of the content — the only reference that cannot move'),
   ('Carries metadata', 'The command to run, the user to run it as, labels that link it to a commit')],
  'MODULE 3 §3.3'),

 ('code', 'Reading an image reference',
  '''ghcr.io/my-org/paytrack-api:1.4.2@sha256:9f3e2a...

ghcr.io          registry    (omit it: docker.io is assumed)
my-org           namespace
paytrack-api     repository
1.4.2            tag         (omit it: latest is assumed)
sha256:9f3e2a... digest      the immutable content hash''',
  [('A tag is a mutable pointer', 'Anyone who can push can move 1.4.2 — or latest — to different content'),
   ('latest is just a default string', 'It promises nothing about being new, tested or stable'),
   ('The digest cannot move', 'Pin base images by digest in any build you want to reproduce'),
   ('Deploy by SHA tag or digest', 'So "what exactly is running?" has one answer')],
  {'lang': 'image reference', 'kicker': 'MODULE 3 §3.3', 'split': 0.55}),

 ('predict', 'How big is your image, really?',
  'PayTrack API is a few hundred lines of Python with a handful of dependencies. Built the way most people '
  'write their first Dockerfile, how large is the resulting image?',
  ['Write down a number in megabytes.',
   'Then write down how long you think a rebuild takes after a ONE-LINE source change.',
   'You will build it both ways in Lab 06 and measure.'],
  'The naive build is about 1.2 GB and re-runs pip install on every source change. The multi-stage build is '
  'under 200 MB — roughly 190 MB on arm64, about 150 MB on amd64 — and a source-only change rebuilds in '
  'seconds because the dependency layer is cached. Same application, same behaviour.', 3),

 ('diagram', 'Image layers and the build cache', dg.image_layers, 'MODULE 3 §3.3',
  {'speaker': 'The rule: order instructions from least-frequently to most-frequently changed. Getting this '
   'one thing right typically takes a three-minute build to a few seconds.'}),

 ('code', 'Layers are additive — deleting does not shrink an image',
  '''# Two RUNs: the compiler is still in the image
RUN apt-get install -y build-essential    # layer: +300 MB
RUN apt-get remove -y build-essential     # layer: marks files deleted

# How secrets leak
COPY id_rsa /root/.ssh/id_rsa             # layer: the key
RUN rm /root/.ssh/id_rsa                  # layer: hides it

# The fix: one RUN, cleanup in the same layer
RUN apt-get update \\
 && apt-get install -y --no-install-recommends curl \\
 && rm -rf /var/lib/apt/lists/*''',
  [('The +300 MB layer is still shipped', 'The removal only adds a layer that hides the files'),
   ('The key is extractable by anyone who can pull', 'docker save, untar, and read the earlier layer'),
   ('Clean up in the SAME RUN', 'Then the bytes never land in any layer'),
   ('Better still: multi-stage builds', 'The toolchain lives in a stage that is never shipped at all')],
  {'lang': 'Dockerfile', 'kicker': 'MODULE 3 §3.3', 'split': 0.60}),

 ('section', '3', 'Containers & Dockerfiles', 'Lifecycle, signals and the instruction set',
  ['The container lifecycle', 'The PID 1 problem', 'Dockerfile instructions', 'CMD vs ENTRYPOINT',
   '.dockerignore']),

 ('flow', 'The container lifecycle',
  [('docker create', 'Image layers + a new writable layer + namespace and cgroup configuration'),
   ('docker start → running', 'The process starts as PID 1 inside its namespaces'),
   ('docker pause / unpause', 'Freezes and thaws every process through the cgroup freezer'),
   ('docker stop', 'Sends SIGTERM, waits (10 s by default), then SIGKILL'),
   ('exited', 'The process has ended; the writable layer still exists — docker start reuses it'),
   ('docker rm', 'The writable layer is destroyed. Anything not in a volume is gone')],
  'MODULE 3 §3.4',
  {'note': ('WHY IT MATTERS', 'Kubernetes terminates pods constantly — every rolling update, scale-down and '
            'node drain sends SIGTERM first. An application that ignores it drops in-flight requests every time.')}),

 ('define', 'The PID 1 problem',
  'Inside a container your process is PID 1, which in Linux gets no default signal handlers and must reap '
  'orphaned children. A shell-form CMD makes /bin/sh PID 1 — and sh does not forward SIGTERM to your application.',
  [('Shell form: CMD python -m src.app', 'Runs /bin/sh -c "python -m src.app" — sh is PID 1, python is a child'),
   ('Exec form: CMD ["gunicorn", "wsgi:app"]', 'gunicorn is PID 1 and receives SIGTERM directly'),
   ('Or add an init process', 'docker run --init, or tini as the entrypoint, forwards signals and reaps zombies'),
   ('The symptom', 'Graceful shutdown never happens; the platform eventually SIGKILLs mid-request')],
  'MODULE 3 §3.4'),

 ('demo', 'Does PID 1 hear SIGTERM?',
  '''$ docker exec paytrack-naive cat /proc/1/cmdline | tr '\\0' ' '
/bin/sh -c python -m src.app
$ docker kill --signal=TERM paytrack-naive
$ sleep 2
$ docker inspect -f '{{.State.Running}}' paytrack-naive
true
$ docker kill --signal=TERM paytrack
$ sleep 2
$ docker inspect -f '{{.State.Running}}' paytrack 2>/dev/null \\
    || echo "gone — it shut down cleanly"
gone — it shut down cleanly''',
  [('The naive image\'s PID 1 is /bin/sh', 'Your application is a child that never hears the signal'),
   ('SIGTERM to the naive container: still running', 'sh has no handler, and PID 1 ignores unhandled signals'),
   ('The same signal to the exec-form image: it exits', 'gunicorn is PID 1 and drains its workers'),
   ('A deterministic test', 'docker stop timings vary by platform; this result does not')],
  {'minutes': 5, 'speaker': 'This is Lab 06 Step 5. Do not rely on "docker stop takes ten seconds" — on Docker '
   'Desktop it often does not. The Running=true result is the proof.'}),

 ('table', 'Dockerfile instructions that shape the build',
  ['Instruction', 'Purpose', 'Notes and traps'],
  [['FROM image:tag@digest', 'Base image; starts a build stage', 'Pin by digest to reproduce a build. FROM scratch is empty'],
   ['ARG name=default', 'A BUILD-time variable', '✗ Visible in image history — never a secret'],
   ['ENV KEY=value', 'A RUNTIME environment variable', 'Persists into the container and docker inspect'],
   ['WORKDIR /app', 'Sets and creates the working directory', 'Prefer it to RUN cd — cd does not persist between layers'],
   ['COPY src dst', 'Copies files from the build context', '✔ Preferred. Respects .dockerignore'],
   ['ADD src dst', 'COPY plus tar extraction and URL fetching', 'Avoid the magic: use COPY, or RUN curl'],
   ['RUN cmd', 'Runs a command at build time, creating a layer', 'Chain with && and clean up in the same RUN']],
  'MODULE 3 §3.5', {'widths': [2.6, 3.3, 4.3]}),

 ('table', 'Dockerfile instructions that shape the running container',
  ['Instruction', 'Purpose', 'Notes and traps'],
  [['CMD ["a","b"]', 'The default command — overridable', 'Exec form (a JSON array), not shell form'],
   ['ENTRYPOINT ["a"]', 'The executable; CMD becomes its arguments', 'For images that ARE a program'],
   ['EXPOSE 8080', 'Documentation only', 'Publishes nothing — that is -p or ports:'],
   ['USER 10001', 'Drops privileges for later instructions and at runtime', '✔ Do this. The default is root'],
   ['HEALTHCHECK', 'A command Docker runs to judge health', 'Compose can wait on it; Kubernetes ignores it and uses probes'],
   ['LABEL k=v', 'Metadata', 'Use OCI labels: image.source and image.revision'],
   ['STOPSIGNAL', 'The signal sent on stop', 'Change only if the application expects something other than SIGTERM']],
  'MODULE 3 §3.5', {'widths': [2.4, 3.6, 4.2]}),

 ('table', 'CMD vs ENTRYPOINT — the table that settles it',
  ['Dockerfile', 'docker run img', 'docker run img echo hi'],
  [['CMD ["python", "app.py"]', 'python app.py', 'echo hi — CMD is replaced'],
   ['ENTRYPOINT ["python", "app.py"]', 'python app.py', 'python app.py echo hi — appended'],
   ['ENTRYPOINT ["python"] + CMD ["app.py"]', 'python app.py', 'python echo hi — CMD replaced, entrypoint kept']],
  'MODULE 3 §3.5', {'widths': [3.9, 2.6, 3.5],
   'note': ('RULE OF THUMB', 'CMD for services where the command is a sensible default; ENTRYPOINT when the '
            'image is a tool and arguments are its input.')}),

 ('table', 'Dockerfile — the traps and the fixes',
  ['Trap', 'Consequence', 'Fix'],
  [['COPY . . before pip install', 'Cache invalidated on every source change', 'Copy the dependency manifest first'],
   ['apt install then apt remove in a later RUN', 'The image does not shrink — layers are additive',
    'Same RUN, && rm -rf /var/lib/apt/lists/*'],
   ['Shell-form CMD', 'sh swallows SIGTERM — dropped requests on every deploy', 'Exec form: CMD ["gunicorn", …]'],
   ['Secrets in ARG or ENV', 'Visible in docker history to anyone who can pull', 'BuildKit --mount=type=secret'],
   ['No USER instruction', 'Runs as root', 'USER 10001 — a numeric, non-root UID'],
   ['No .dockerignore', 'Ships .git, .venv and possibly .env', 'Write it BEFORE the first build'],
   ['FROM python:3.12 (full)', '~1 GB of compilers you never run', 'python:3.12-slim, multi-stage']],
  'MODULE 3 §3.5', {'widths': [2.9, 3.6, 3.3]}),

 ('code', '.dockerignore — do not skip this',
  '''.git
.venv
__pycache__
*.pyc
.pytest_cache
.env
*.pem
terraform/.terraform''',
  [('The build context is EVERYTHING in the directory', 'Sent to the daemon before the first instruction runs'),
   ('.git and .venv make builds slow', 'Hundreds of megabytes transferred on every build'),
   ('They also bust the cache', 'COPY . . sees a change whenever .git changes'),
   ('.env is the dangerous one', 'A secret in the context can end up in a layer'),
   ('Write it before the first build', 'Lab 06 Step 1 — before the naive Dockerfile')],
  {'lang': 'app/.dockerignore', 'kicker': 'LAB 06', 'split': 0.42}),

 ('section', '4', 'Multi-stage Builds & Hardening', 'Ship the runtime, nothing else',
  ['Multi-stage builds', 'The production Dockerfile', 'Choosing a base image',
   'Security practices', 'Operability practices']),

 ('define', 'Multi-stage build',
  'A Dockerfile with several FROM instructions, where later stages copy only the ARTEFACTS they need from '
  'earlier ones. Compilers, headers, build caches, source and credentials stay behind.',
  [('Win 1 — size', 'Smaller images pull faster, which directly cuts deployment and autoscaling time'),
   ('Win 2 — security', 'No compiler, no package manager, no build source: far fewer CVEs to triage in Lab 17'),
   ('Win 3 — secret hygiene', 'Build-time credentials live only in the discarded stage'),
   ('Measured in Lab 06', 'About 1.2 GB down to under 200 MB — roughly six to eight times smaller')],
  'MODULE 3 §3.6'),

 ('code', 'The production Dockerfile, condensed',
  '''# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \\
      build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY requirements.txt .                  # dependencies FIRST
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
ARG GIT_SHA=local
LABEL org.opencontainers.image.revision="${GIT_SHA}"
RUN groupadd --gid 10001 appuser \\
 && useradd --uid 10001 --gid 10001 --no-create-home appuser
COPY --from=builder /install /install    # packages, not the compiler
WORKDIR /app
COPY --chown=10001:10001 src/ ./src/
USER 10001
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:app"]''',
  [('Two stages: builder and runtime', 'build-essential never reaches the shipped image'),
   ('requirements.txt copied alone, first', 'The dependency layer stays cached until requirements change'),
   ('The revision label records the commit', 'Any running container can be traced to its source'),
   ('A numeric, non-root UID', '10001 — Kubernetes runAsNonRoot can verify a number'),
   ('Exec-form CMD', 'gunicorn is PID 1 and handles SIGTERM')],
  {'lang': 'app/Dockerfile', 'kicker': 'LAB 06 STEP 3', 'split': 0.62}),

 ('table', 'Choosing a base image',
  ['Base', 'Size', 'Trade-off'],
  [['python:3.12', '~1 GB', 'Everything included — and a large attack surface'],
   ['python:3.12-slim', '~150 MB', '✔ The sensible default: Debian, glibc, apt available'],
   ['python:3.12-alpine', '~50 MB', 'musl libc: manylinux wheels do not apply, slow source builds, real DNS and timing bugs'],
   ['gcr.io/distroless/python3', '~50 MB', 'No shell, no package manager — excellent security, harder to debug'],
   ['scratch', '0', 'Static binaries only: Go, Rust']],
  'MODULE 3 §3.6', {'widths': [3.0, 1.3, 5.7], 'emph': [1]}),

 ('compare', 'Alpine or slim?',
  'Alpine is 5 MB and python:3.12-slim is 150 MB. Alpine is obviously the better base image. '
  'Argue the other side.',
  ['Two minutes in pairs. What does Alpine change about how Python packages are installed?',
   'What would you notice first — at build time, or in production at 3 a.m.?'],
  'Alpine uses musl libc, so manylinux wheels do not apply and pip builds from source: slower '
  'builds, a bigger toolchain, and known DNS and thread-stack differences under load. -slim '
  'gives most of the size benefit with none of the surprises. Smaller is better only until it '
  'costs you correctness.', 3),

 ('table', 'Container security practices',
  ['Practice', 'How', 'Why'],
  [['Run as a non-root, numeric UID', 'USER 10001', 'A compromise inside is not root outside'],
   ['Read-only root filesystem', '--read-only plus --tmpfs /tmp', 'An attacker cannot drop tools on disk'],
   ['Drop every capability', '--cap-drop=ALL, add back only what is needed', 'Removes most kernel attack surface'],
   ['Block privilege escalation', '--security-opt=no-new-privileges', 'setuid binaries cannot escalate'],
   ['Never bake in secrets', 'BuildKit --mount=type=secret; runtime secrets', 'docker history shows every ARG and ENV'],
   ['Always set limits', '--memory, --cpus, --pids-limit', 'One container cannot starve the host'],
   ['Scan in CI and fail on HIGH/CRITICAL', 'Trivy — Lab 17', 'Known vulnerabilities never ship'],
   ['Never mount docker.sock', 'Not into anything you do not fully trust', 'It is root on the host']],
  'MODULE 3 §3.10', {'widths': [3.1, 3.7, 3.4]}),

 ('bullets', 'Operability practices — images the platform can run',
  [('Log to stdout and stderr, as structured JSON', 'The platform collects it; never write log files inside a container'),
   ('Take configuration from the environment', 'One image, many environments — the build-once rule in practice'),
   ('Handle SIGTERM and shut down gracefully', 'Finish in-flight requests, then exit'),
   ('Expose a cheap health endpoint', 'And a separate readiness check that knows about dependencies'),
   ('Keep containers stateless', 'Push state to volumes or a database'),
   ('Tag with the git SHA and add OCI labels', 'An image you cannot trace to a commit is an audit gap')],
  'MODULE 3 §3.10'),

 ('lab', '06', 'Containerising PayTrack API',
  'Build the same application twice, measure the difference, harden it, and let CI publish it.',
  ['Write .dockerignore FIRST — the build context is everything Docker receives',
   'Build it naively, then measure: about 1.2 GB, running as root, PID 1 is /bin/sh',
   'Write the production multi-stage Dockerfile: slim base, non-root, healthcheck, OCI labels',
   'Measure again: under 200 MB, uid 10001, and SIGTERM now actually stops it',
   'Harden the runtime: --read-only, --cap-drop=ALL, --memory, --security-opt',
   'Let CI build and publish to GHCR, tagged with the commit SHA'],
  'A hardened image under 200 MB, published by CI, tagged with its commit — the artefact days 4–6 deploy',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('section', '5', 'Docker Compose', 'A whole stack, one file, one command',
  ['What Compose is — and is not', 'The PayTrack stack', 'started ≠ ready', 'The commands to know']),

 ('define', 'Docker Compose',
  'A tool for defining and running a multi-container application from one declarative YAML file, so an '
  'entire local environment starts with a single command.',
  [('It kills "works on my machine" for the whole STACK', 'Not only for one process'),
   ('New joiners go from days of setup to docker compose up', 'The stack definition lives in git with the code'),
   ('Each service is reachable by its NAME', 'Compose creates a user-defined network with DNS'),
   ('It is NOT an orchestrator', 'One host: no rescheduling on node failure, no rolling updates, no autoscaling — Day 4 fills that gap')],
  'MODULE 3 §3.7'),

 ('diagram', 'The PayTrack stack in one file', dg.compose_stack, 'MODULE 3 §3.7'),

 ('code', 'The Lab 07 compose file, condensed',
  '''services:
  db:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    ports: ["127.0.0.1:5432:5432"]        # loopback only
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paytrack -d paytrack"]
  api:
    build: { context: ./app }
    environment:
      DATABASE_URL: postgresql://paytrack:...@db:5432/paytrack
    depends_on:
      db: { condition: service_healthy }
    deploy: { replicas: 2 }               # no ports: nginx only
  proxy:
    image: nginx:1.27-alpine
    ports: ["8080:80"]                    # the only public entry
volumes:
  pgdata: { name: paytrack-pgdata }''',
  [('@db:5432 — the service name is the hostname', 'No IP address anywhere in the configuration'),
   ('condition: service_healthy', 'The API waits until Postgres can actually answer'),
   ('The API publishes no ports', 'All traffic goes through nginx — defence in depth'),
   ('Postgres bound to 127.0.0.1', 'Reachable from your laptop, never from the network'),
   ('A named volume', 'The ledger survives docker compose down')],
  {'lang': 'compose.yaml', 'kicker': 'LAB 07', 'split': 0.60}),

 ('two', 'started ≠ ready — the most common Compose bug',
  ('depends_on: [db]', ['✗ Waits only for the CONTAINER to start',
                        '✗ Postgres may need several more seconds to accept connections',
                        '✗ The API fails on its first query',
                        '✗ Usually "fixed" with sleep 10 in an entrypoint'], 'red'),
  ('condition: service_healthy', ['✔ Waits for the HEALTHCHECK to pass',
                                  '✔ The API starts only when the ledger can answer',
                                  '✔ Deterministic startup, every time',
                                  '✔ Same idea as Kubernetes readiness probes tomorrow'], 'green'),
  'MODULE 3 §3.7',
  ('YOU WILL BREAK THIS ON PURPOSE', 'Lab 07 removes the health condition and destroys the volume so Postgres '
   'must initialise from scratch — the clearest introduction to tomorrow\'s liveness-vs-readiness distinction.')),

 ('table', 'Compose commands to know cold',
  ['Command', 'What it does', 'Watch out'],
  [['docker compose up -d --build', 'Build what changed, start everything in the background', 'Add --build or you run stale images'],
   ['docker compose ps', 'Every service, its state and its health', 'Look at the health column, not only "Up"'],
   ['docker compose logs -f api', 'Follow one service\'s logs', 'Logs go to stdout — no files to find'],
   ['docker compose exec api sh', 'A shell inside a running service', 'Distroless images have no shell'],
   ['docker compose restart api', 'Restart the same container', 'The writable layer survives'],
   ['docker compose up -d --force-recreate', 'Replace containers with new ones', 'The writable layer is destroyed'],
   ['docker compose down', 'Stop and remove containers and networks', 'Volumes are kept'],
   ['docker compose down -v', 'Also DELETE the volumes', '✗ Every row in the database — no prompt, no undo']],
  'MODULE 3 §3.7', {'widths': [3.6, 3.6, 3.0], 'emph': [7], 'first_bold': True}),

 ('section', '6', 'Networking & Storage', 'The facts people get burned by',
  ['Network drivers', 'Default vs user-defined bridge', 'Port publishing and the UFW bypass',
   'localhost inside a container', 'Volumes, bind mounts, tmpfs and backups']),

 ('table', 'Docker network drivers',
  ['Driver', 'Behaviour', 'Use for'],
  [['bridge (default)', 'A private virtual network on the host; outbound traffic is NAT\'d', '✔ Single-host apps — what Compose creates'],
   ['host', 'No network namespace — the host\'s stack directly; -p is ignored', 'Latency-critical cases; no isolation'],
   ['none', 'Loopback only', 'Batch jobs that must not touch the network'],
   ['overlay', 'A multi-host VXLAN network', 'Swarm and multi-host setups'],
   ['macvlan', 'The container gets its own MAC and IP on the physical LAN', 'Legacy apps that must look like hosts']],
  'MODULE 3 §3.8', {'widths': [2.2, 4.6, 3.4]}),

 ('two', 'Default bridge vs user-defined bridge',
  ('DEFAULT BRIDGE (docker0)', ['✗ NO automatic DNS between containers',
                                '✗ Legacy --link is the only name resolution',
                                '✗ Every container on one flat network',
                                '→ What you get with a bare docker run'], 'red'),
  ('USER-DEFINED BRIDGE', ['✔ DNS by container and service name',
                           '✔ Containers attach and detach live',
                           '✔ Separate networks isolate separate stacks',
                           '✔ What Compose creates for you'], 'green'),
  'MODULE 3 §3.8',
  ('WHY IT MATTERS TOMORROW', 'Name-based discovery is what lets DATABASE_URL say @db:5432 — and Kubernetes '
   'Services provide exactly the same thing, so the configuration moves unchanged.')),

 ('code', 'Port publishing — and the UFW bypass',
  '''$ docker run -p 8080:8080 paytrack-api
  # host 8080 → container 8080, on ALL host interfaces

$ docker run -p 127.0.0.1:8080:8080 paytrack-api
  # loopback only — safe on a shared machine

$ docker run -P paytrack-api
  # every EXPOSEd port to a random high port

$ docker run paytrack-api
  # no -p: unreachable from the host, reachable from siblings''',
  [('Docker writes iptables rules directly', 'They are evaluated before the rules UFW manages'),
   ('So -p 5432:5432 punches through ufw deny 5432', 'On a cloud VM, the database is on the internet'),
   ('Bind sensitive ports to 127.0.0.1', 'Or do not publish them at all'),
   ('This has caused real breaches', 'It surprises experienced Linux administrators')],
  {'lang': 'bash', 'kicker': 'MODULE 3 §3.8', 'split': 0.56,
   'note': ('SAY THIS OUT LOUD', 'If you take one operational fact home from day 3, make it the UFW bypass.')}),

 ('bullets', 'Networking facts that bite',
  [('localhost inside a container is THAT container',
    'Each container has its own network namespace — use the service name for siblings'),
   ('From the host to a container', 'localhost:<published port>'),
   ('From a container to the host', 'host.docker.internal — on Linux add --add-host=host.docker.internal:host-gateway'),
   ('User-defined networks resolve names through an embedded DNS server', 'At 127.0.0.11 inside every container'),
   ('Containers on different user-defined networks cannot reach each other', 'Real segmentation, not a convention — Lab 08 proves it')],
  'MODULE 3 §3.8'),

 ('table', 'Where data lives — and what survives what',
  ['Storage', 'Syntax', 'Survives docker rm?', 'Use for'],
  [['Container writable layer', '(default)', '✗ No — destroyed', 'Nothing you care about'],
   ['Named volume', '-v pgdata:/var/lib/postgresql/data', '✔ Yes', 'Production data — portable, backup-able'],
   ['Bind mount', '-v $(pwd)/src:/app/src', '✔ Yes (it is a host path)', 'Development: edit on the host, see it live'],
   ['tmpfs', '--tmpfs /run/secrets', '✗ No — RAM only', 'Secrets and scratch data that must never touch disk'],
   ['Anonymous volume', '-v /data', 'Kept, but nameless', 'Almost never — you will lose track of it']],
  'MODULE 3 §3.9', {'widths': [2.3, 3.2, 2.2, 2.9],
   'note': ('KUBERNETES TOO', 'Pods are recreated constantly, so nothing durable may live on a container '
            'filesystem there either. The volume idea returns as the PersistentVolumeClaim on day 4.')}),

 ('code', 'Backing up a named volume',
  '''$ docker run --rm \\
    -v paytrack-pgdata:/data:ro \\
    -v "$PWD":/backup \\
    alpine \\
    tar czf /backup/pgdata-$(date +%F).tar.gz -C /data .''',
  [('There is no docker volume backup command', 'This throwaway-container idiom is the standard answer'),
   ('--rm removes the helper when it finishes', 'Nothing is left running'),
   ('The volume is mounted read-only', 'The backup cannot damage the data it copies'),
   ('A backup you have never restored is a hypothesis', 'Lab 08 restores it into a fresh volume and checks the rows')],
  {'lang': 'bash', 'kicker': 'MODULE 3 §3.9 · LAB 08', 'split': 0.55,
   'speaker': 'For a consistent Postgres backup in production, use pg_dump or stop the database first — '
              'copying live data files is only safe when nothing is writing.'}),

 ('bank', 'Two banking decisions encoded in the schema',
  [('amount_minor BIGINT — integer minor units',
    'NUMERIC is acceptable; a floating-point type never is. A rounding error in a ledger is a reconciliation break, then an audit finding'),
   ('No column for a primary account number',
    'Storing a PAN pulls this database, its backups, its replicas and everything reading them into PCI-DSS scope'),
   ('The container runs as uid 10001 with a read-only root filesystem',
    'The same controls become the Kubernetes securityContext tomorrow'),
   ('OCI labels tie the image to its commit',
    'org.opencontainers.image.revision answers "what exactly is in production?" — the audit question')],
  {'lead': 'Compliance scope is something you design OUT at the boundary, not something you secure later. '
           'The cheapest PCI control is not accepting the data in the first place.',
   'ref': 'Appendix A §A.6 · Lab 07'}),

 ('lab', '07 + 08', 'A Full Local Stack · Prove the Isolation',
  'Three tiers in one file, then verify every claim from today on your own machine.',
  ['Compose: nginx → PayTrack API ×2 → PostgreSQL, with a named volume',
   'Use condition: service_healthy — then BREAK it deliberately and watch the race',
   'Prove service-name DNS, and that localhost inside a container is that container',
   'Prove network isolation, then attach a container to a second network and watch it change',
   'Prove the writable layer dies on recreate but the volume survives',
   'Back up and restore the ledger — a backup you have never restored is a hypothesis'],
  'A three-tier stack started with one command, and demonstrated understanding of DNS, isolation and persistence'),

 ('table', 'Day 3 key terms',
  ['Term', 'Definition'],
  [['Container', 'An isolated process on a shared kernel, with its filesystem from an image'],
   ['Namespace / cgroup', 'What a process can see / what it can use'],
   ['Image / layer / digest', 'Immutable template / one read-only filesystem diff / the immutable content hash'],
   ['OverlayFS / copy-up', 'The union filesystem / copying a file into the writable layer to change it'],
   ['OCI', 'The image, runtime and distribution standards that make images portable'],
   ['Build context', 'The files sent to the daemon, filtered by .dockerignore'],
   ['Multi-stage build', 'Build in one stage, ship only the artefacts from another'],
   ['PID 1 problem', 'A shell as PID 1 swallows SIGTERM; use exec form or an init'],
   ['User-defined bridge', 'A Docker network with name-based DNS'],
   ['Named volume / bind mount / tmpfs', 'Docker-managed storage / a host path / RAM-backed storage']],
  'REFERENCE', {'widths': [3.3, 6.7]}),

 ('check', 'Day 3 — check your understanding',
  ['A colleague says "a container is a lightweight VM." Give a two-sentence correction that includes the security implication.',
   'Your image is 1.2 GB and every commit rebuilds all dependencies. Name the two Dockerfile changes that fix both problems.',
   'RUN apt-get install x, then RUN apt-get remove x. What happens to the image size, and why?',
   'Why does a shell-form CMD cause dropped requests during a Kubernetes rolling update?',
   'You publish Postgres as "5432:5432" on a cloud VM with ufw deny 5432 active. Is the database exposed? Why?',
   'Why is USER 10001 better than USER appuser for a Kubernetes workload?']),

 ('close', 3, 'Day 3 complete',
  ['A container is a process: namespaces, cgroups and OverlayFS — not a small VM',
   'Layers, the cache and multi-stage builds: about 1.2 GB down to under 200 MB, root down to uid 10001',
   'The PID 1 problem, and why exec form matters on every deployment',
   'Compose, service-name DNS, the UFW bypass, and data that survives',
   'AFTER CLASS: finish Labs 06–08 — day 4 deploys the image you publish in Lab 06'],
  'Day 4 takes that image to Kubernetes. You will see why Compose could not take you further, how the '
  'control plane reconciles desired and actual state, why the three probes decide whether a database blip '
  'becomes an outage — and how Services, Ingress, ConfigMaps, Secrets and storage fit together.'),
]


# ═════════════════════════════════════════════════════════════════════════════
# DAY 3 — GOING FURTHER (optional reading, not taught in the session)
#
# Three sections, each with a hands-on lab that lives inside the lab folder it
# extends:  A → Lab 06A,  B → Lab 07A,  C → Lab 08A.
# ═════════════════════════════════════════════════════════════════════════════

DAY3_EXTRA = [
  ('title', 3,
   'Day 3 — Going Further',
   'Optional reading, for after class — once images, Compose and volumes feel comfortable',
   ['A: builds in depth — the cache, BuildKit, multi-architecture, provenance',
    'B: Compose in depth — merging, profiles, health gating, limits',
    'C: runtime hardening and troubleshooting — capabilities, limits, the network path'],
   'Not taught in the session — read it, then practise it in Labs 06A, 07A and 08A'),

  # ── A ──────────────────────────────────────────────────────────────────────
  ('section', 'A', 'Builds in Depth',
   'What the build cache actually keys on, and how to control it',
   ['Reading a build: BuildKit and --progress=plain',
    'docker history — where the megabytes went',
    'Cache invalidation, cache mounts and --target',
    'Multi-architecture images, digests and attestations']),

  ('code', 'Watch the build, not the spinner',
   'docker build --progress=plain -t paytrack-api:plain app/\n'
   '\n'
   '#1 [internal] load build definition from Dockerfile\n'
   '#5 [builder 2/4] COPY requirements.txt .\n'
   '#6 [builder 3/4] RUN pip install -r requirements.txt\n'
   '#6 CACHED                      <-- the line that decides your build time\n'
   '#9 [stage-1 4/5] COPY --from=builder /opt/venv /opt/venv',
   [('BuildKit is the builder', 'Parallel stages, better caching, and secrets that never land in a layer'),
    ('--progress=plain prints every line', 'The default tidy view hides the command output you need when a build fails'),
    ('CACHED is the word to look for', 'A build that says CACHED on the dependency step is a build nobody waits for'),
    ('Each numbered step is one layer', 'The numbers tell you the order BuildKit actually chose')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  real output', 'split': 0.58}),

  ('code', 'docker history — where the megabytes went',
   'docker history paytrack-api:naive --no-trunc --format \\\n'
   '  "table {{.Size}}\\t{{.CreatedBy}}"\n'
   '\n'
   'SIZE      CREATED BY\n'
   '412MB     RUN pip install -r requirements.txt\n'
   '298MB     RUN apt-get install -y build-essential\n'
   '  1.1kB   COPY . .\n'
   '  0B      ENV PYTHONUNBUFFERED=1',
   [('Every line is a layer, and layers only add', 'Deleting a file in a later layer hides it; it still ships'),
    ('Install and clean in ONE RUn', 'apt-get install && rm -rf /var/lib/apt/lists/* must be one instruction'),
    ('Build tools are the usual culprit', 'They belong in the builder stage, never in the final image'),
    ('Compare two tags side by side', 'The difference IS your Dockerfile review')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  real output', 'split': 0.58}),

  ('table', 'What invalidates the cache — and what does not',
   ['Change', 'Rebuilds from', 'Cost'],
   [['Edit app/src/app.py', 'the COPY that brings in the source', 'Seconds — if the source COPY is LAST'],
    ['Edit requirements.txt', 'the dependency install, and everything after it', 'Minutes — unavoidable, and correct'],
    ['Change a build argument', 'the first instruction that uses it', 'Depends where ARG is consumed'],
    ['New base image digest (docker build --pull)', 'everything', 'Full rebuild — do it on a schedule, not by accident'],
    ['Reorder two independent RUN lines', 'the first line you moved', 'Free to avoid: put the stable things first'],
    ['Touch a file that .dockerignore excludes', 'nothing', 'Zero — the file never entered the context']],
   'MODULE 3 §3.3',
   {'note': ('THE ORDERING RULE',
             'Copy the dependency manifest, install, and only then copy the source. Every Dockerfile in '
             'this course does that, and it is the single biggest build-time win available.'),
    'widths': [3.8, 3.4, 3.1]}),

  ('code', 'Cache mounts — keep the package cache between builds',
   '# syntax=docker/dockerfile:1\n'
   'FROM python:3.12-slim AS builder\n'
   'COPY requirements.txt .\n'
   'RUN --mount=type=cache,target=/root/.cache/pip \\\n'
   '    pip install --prefix=/opt/venv -r requirements.txt\n'
   '\n'
   '# and for a secret that must NOT become a layer:\n'
   'RUN --mount=type=secret,id=netrc,target=/root/.netrc \\\n'
   '    pip install -r private-requirements.txt',
   [('The syntax line is required', 'It selects the Dockerfile frontend that understands --mount'),
    ('A cache mount is not a layer', 'Wheels survive between builds; nothing is added to the image'),
    ('Even a changed requirements.txt is then fast', 'You re-resolve, but you do not re-download'),
    ('type=secret is how credentials enter a build', 'Passed with --secret; never written into the image')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'Dockerfile', 'split': 0.60}),

  ('code', 'One Dockerfile, many outputs: --target and --platform',
   '# stop at the builder stage, for a debug shell\n'
   'docker build --target builder -t paytrack-api:builder app/\n'
   '\n'
   '# build for a machine that is not yours\n'
   'docker buildx build --platform linux/amd64,linux/arm64 \\\n'
   '  -t ghcr.io/<you>/paytrack-api:1.0.0 --push app/\n'
   '\n'
   'docker buildx imagetools inspect ghcr.io/<you>/paytrack-api:1.0.0',
   [('--target builds part of the file', 'The fastest way to inspect what the builder stage produced'),
    ('Multi-arch needs buildx and a registry', 'A multi-platform result cannot be --load-ed into the local store'),
    ('Your laptop may not be your servers', 'Apple silicon builds arm64 by default; most CI runners are amd64'),
    ('imagetools inspect shows the manifest list', 'One tag, one digest per architecture underneath it')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.60}),

  ('code', 'Say what the image is: labels, healthcheck, digest pinning',
   'FROM python:3.12-slim@sha256:6f7e2b...      # pinned by DIGEST, not by tag\n'
   '\n'
   'LABEL org.opencontainers.image.source="https://github.com/<you>/paytrack-api" \\\n'
   '      org.opencontainers.image.revision="$GIT_SHA" \\\n'
   '      org.opencontainers.image.licenses="MIT"\n'
   '\n'
   'HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\\n'
   '  CMD python -c "import urllib.request;urllib.request.urlopen(\'http://localhost:8080/health\')"',
   [('A digest cannot be moved', 'Pin the base image where a rebuild must produce the same thing'),
    ('image.source links the image to the repo', 'GHCR shows the package against the repository automatically'),
    ('image.revision answers "what is running?"', 'One command from a running container back to a commit'),
    ('HEALTHCHECK is what Compose gates on', 'Without it, depends_on can only wait for "started"')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'Dockerfile', 'split': 0.62}),

  ('predict', 'Which change makes the next build slow?',
   'Your Dockerfile copies requirements.txt, installs, then copies the source. You make each of these '
   'changes, one at a time, and rebuild.',
   ['Fix a typo in a docstring in app/src/app.py.',
    'Add one package to requirements.txt.',
    'Run the same build again on a colleague\'s laptop, for the first time.',
    'Which of the three is slow, and which is slow only once?'],
   'The docstring rebuilds only the source COPY and everything after it: seconds. The new package '
   're-runs pip install: minutes, and correctly so. The colleague\'s first build is slow because their '
   'cache is empty — a cache mount or a registry cache makes the second one fast. You measure all three '
   'in Lab 06A.',
   3),

  ('lab', '06A',
   'Builds in Depth — cache, BuildKit, multi-arch',
   'Take the image you built in Lab 06 apart: measure the cache, keep it with a cache mount, read the '
   'layers, and build for an architecture that is not yours.',
   ['Time three rebuilds and see exactly what each one invalidates',
    'Read docker history and find the megabytes',
    'Add a cache mount and measure the difference again',
    'Build a --target stage for debugging',
    'Pin the base image by digest, add OCI labels and a HEALTHCHECK',
    'Build multi-architecture with buildx and inspect the manifest list'],
   'A Dockerfile whose builds are fast for the right reasons, and an image that says what it is',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-06-docker-images/README-06A-builds-in-depth.md. Optional; about 60 '
               'minutes; needs Docker and the image from Lab 06. The multi-arch part needs a registry '
               'login, and is written so it can be skipped.'}),

  # ── B ──────────────────────────────────────────────────────────────────────
  ('section', 'B', 'Compose in Depth',
   'The file you run is not always the file you wrote',
   ['docker compose config — see what was actually merged',
    'Override files, profiles and environments',
    'Health-gated startup, restart policies and limits',
    'One-off commands, scaling and logs']),

  ('code', 'The merged file is the truth',
   'docker compose config            # the file Compose will actually run\n'
   'docker compose config --services\n'
   '\n'
   '# base, then the override, then a per-environment file:\n'
   'docker compose -f compose.yaml -f compose.override.yaml \\\n'
   '               -f compose.uat.yaml config',
   [('compose.override.yaml is picked up automatically', 'That is why "it works for me" and CI can differ'),
    ('Later -f wins, key by key', 'Scalars replace; most lists append — check with config, do not assume'),
    ('config resolves variables too', 'You see the real values, which is also how secrets leak into a screenshot'),
    ('Run it in CI before you deploy', 'A merged file that does not parse should never reach an environment')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.58}),

  ('code', 'Profiles — one file, several stacks',
   'services:\n'
   '  api:        { image: paytrack-api:1.0.0 }\n'
   '  db:         { image: postgres:16-alpine }\n'
   '  pgadmin:\n'
   '    image: dpage/pgadmin4\n'
   '    profiles: ["tools"]        # only starts when asked for\n'
   '  loadtest:\n'
   '    image: grafana/k6\n'
   '    profiles: ["perf"]\n'
   '\n'
   'docker compose up -d                  # api + db only\n'
   'docker compose --profile tools up -d  # adds pgadmin',
   [('A service with a profile is opt-in', 'Developer tooling stops leaking into the default stack'),
    ('Profiles beat commenting services out', 'The file stays one file, and git stops showing churn'),
    ('COMPOSE_PROFILES sets it per machine', 'An environment variable, so CI and a laptop can differ safely'),
    ('Name them after intent', 'tools, perf, debug — not "extra1"')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'compose.yaml  ·  bash', 'split': 0.60}),

  ('code', 'Start in the right order — actually',
   'services:\n'
   '  db:\n'
   '    image: postgres:16-alpine\n'
   '    healthcheck:\n'
   '      test: ["CMD-SHELL", "pg_isready -U paytrack"]\n'
   '      interval: 5s\n'
   '      timeout: 3s\n'
   '      retries: 10\n'
   '      start_period: 10s\n'
   '  api:\n'
   '    depends_on:\n'
   '      db: { condition: service_healthy }   # not just "started"\n'
   '    restart: unless-stopped',
   [('Plain depends_on waits for STARTED', 'Lab 07 shows the crash that comes from trusting it'),
    ('service_healthy waits for the healthcheck', 'The container must define one, or there is nothing to wait for'),
    ('start_period stops early failures counting', 'Slow first-start databases stop being marked unhealthy'),
    ('restart: unless-stopped is the sane default', 'Survives a reboot; respects a deliberate docker stop')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'compose.yaml', 'split': 0.60}),

  ('table', 'Operating a stack: the commands people miss',
   ['Command', 'What it does', 'When you want it'],
   [['docker compose run --rm api pytest', 'A one-off container, removed afterwards', 'Tests and migrations — not `exec`'],
    ['docker compose up -d --scale api=3', 'Three API containers behind the proxy', 'Seeing load balancing on a laptop'],
    ['docker compose logs -f --since 10m api', 'Follow one service, recent lines only', 'Incident triage'],
    ['docker compose ps --format json', 'Machine-readable state', 'Scripting a smoke test'],
    ['docker compose stop / start', 'Keeps the containers and their data', 'Pausing work for the day'],
    ['docker compose down', 'Removes containers and networks — keeps named volumes', 'A clean restart'],
    ['docker compose down -v', '🔴 Also deletes named volumes', 'Only when you mean to lose the database']],
   'MODULE 3 §3.5',
   {'note': ('THE ONE TO BE CAREFUL WITH',
             '`down -v` is the command that deletes the data. It is one character away from the command '
             'people run every day — which is why Lab 07A makes you prove a backup first.'),
    'widths': [4.0, 3.3, 3.0]}),

  ('code', 'Limits and logs belong in the file',
   'services:\n'
   '  api:\n'
   '    deploy:\n'
   '      resources:\n'
   '        limits:   { cpus: "0.50", memory: 256M }\n'
   '        reservations: { memory: 128M }\n'
   '    logging:\n'
   '      driver: json-file\n'
   '      options: { max-size: "10m", max-file: "3" }',
   [('Unlimited containers are a laptop killer', 'One runaway service should not take the machine with it'),
    ('Compose v2 honours deploy.resources', 'No Swarm required — it maps to the same cgroup limits'),
    ('Unbounded logs fill the disk quietly', 'max-size and max-file are the two-line fix'),
    ('It is the same conversation as Kubernetes', 'requests and limits tomorrow are this idea, with a scheduler')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'compose.yaml', 'split': 0.58}),

  ('lab', '07A',
   'Compose in Depth — overrides, profiles, health gating',
   'Split the Lab 07 stack into a base file and environment overrides, gate startup on health, put '
   'limits on it, and back the database up before you destroy it.',
   ['Read the merged file with docker compose config — and find a value you did not expect',
    'Split into compose.yaml + compose.override.yaml, then a UAT file',
    'Put developer tooling behind a profile',
    'Replace depends_on with a health-gated dependency and prove the crash is gone',
    'Add CPU, memory and log limits, then watch them bite',
    'Back up the volume, run down -v, and restore it'],
   'A stack that starts in the right order, cannot eat the laptop, and whose data you can restore',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-07-docker-compose-stack/README-07A-compose-in-depth.md. Optional; '
               'about 60 minutes; needs Docker and the Lab 07 stack. The backup-and-restore part is the '
               'one to demo if you only have five minutes.'}),

  # ── C ──────────────────────────────────────────────────────────────────────
  ('section', 'C', 'Hardening and Troubleshooting the Runtime',
   'The flags that decide what a compromised container can do — and how to see inside one',
   ['Capabilities, no-new-privileges and a read-only root filesystem',
    'Memory and CPU limits, and the OOM kill',
    'Where published ports really go, and why UFW does not see them',
    'stats, events, inspect — and getting a shell into a distroless image']),

  ('table', 'The runtime flags that matter',
   ['Flag', 'What it stops', 'Cost of using it'],
   [['--cap-drop ALL --cap-add NET_BIND_SERVICE', 'Almost every privileged syscall path', 'None, once you know which caps you need'],
    ['--security-opt no-new-privileges:true', 'A setuid binary escalating inside the container', 'None'],
    ['--read-only --tmpfs /tmp', 'Malware writing to the image filesystem', 'You must know where the app writes'],
    ['--user 10001:10001', 'Root inside the container being root on a mounted volume', 'File ownership must match'],
    ['--memory 256m --cpus 0.5', 'One container starving the host', 'The app must survive an OOM kill'],
    ['--pids-limit 200', 'A fork bomb taking the machine down', 'None for normal workloads'],
    ['(not) -v /var/run/docker.sock:…', '🔴 Root on the host, handed over', 'Never mount it into a build or an agent']],
   'MODULE 3 §3.4 · MODULE 7 §7.4',
   {'note': ('DEFENCE IN DEPTH, NOT A BOUNDARY',
             'These are kernel-enforced limits on a SHARED kernel. They make an escape much harder; they '
             'do not make a container a virtual machine. Multi-tenant isolation still needs a VM.'),
    'widths': [4.2, 3.2, 2.9]}),

  ('code', 'Prove the limits, do not trust them',
   '# capabilities actually granted to the process\n'
   'docker run --rm --cap-drop ALL alpine sh -c \\\n'
   '  "grep CapEff /proc/self/status"\n'
   'CapEff:\t0000000000000000        <-- none\n'
   '\n'
   '# memory limit and the kill that follows\n'
   'docker run -d --name hog --memory 64m python:3.12-slim \\\n'
   '  python -c "b=bytearray(); [b.extend(bytes(10**7)) for _ in range(50)]"\n'
   'docker inspect hog --format "{{.State.OOMKilled}} {{.State.ExitCode}}"\n'
   'true 137',
   [('CapEff 0 is the proof', 'The kernel, not the documentation, telling you what the process may do'),
    ('Exit 137 is SIGKILL (128+9)', 'The OOM killer, not your application, ended it'),
    ('OOMKilled: true is the one to alert on', 'A restarting container with 137 is a limits conversation'),
    ('Same numbers in Kubernetes tomorrow', 'CrashLoopBackOff with exit 137 means exactly this')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  real output', 'split': 0.60}),

  ('code', 'Where a published port really goes',
   'docker run -d -p 8080:8080 paytrack-api:1.0.0\n'
   '\n'
   'sudo iptables -t nat -L DOCKER -n | head\n'
   'DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:8080\n'
   '\n'
   '# the chain YOUR rules must go in:\n'
   'sudo iptables -I DOCKER-USER -i eth0 -p tcp --dport 8080 -j DROP',
   [('Docker writes NAT rules for every -p', 'Traffic is redirected before a host firewall policy sees it'),
    ('UFW does not filter published ports', 'A "firewalled" laptop can be publishing a database to the LAN'),
    ('DOCKER-USER is evaluated first', 'It is the supported place for your own rules — Docker will not rewrite it'),
    ('Or do not publish at all', 'Bind to 127.0.0.1:8080:8080, or keep the service on an internal network')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  real output', 'split': 0.60}),

  ('code', 'Seeing inside a container that has no shell',
   'docker stats --no-stream\n'
   'docker events --since 10m --filter container=paytrack-api\n'
   'docker inspect paytrack-api \\\n'
   '  --format "{{.State.Status}} {{.RestartCount}} {{.HostConfig.Memory}}"\n'
   '\n'
   '# a distroless image has no sh - borrow one:\n'
   'docker run -it --rm --pid container:paytrack-api \\\n'
   '  --network container:paytrack-api --cap-add SYS_PTRACE \\\n'
   '  nicolaka/netshoot bash',
   [('stats reads the cgroup counters', 'Live memory and CPU per container, no agent required'),
    ('events is the container audit log', 'Create, start, die, oom, health_status — with timestamps'),
    ('inspect --format asks one question', 'Scriptable; the whole JSON is rarely what you want'),
    ('Join namespaces instead of adding tools', 'A debug container with the app\'s network and PID view keeps the image small')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.62}),

  ('table', 'Reclaiming disk — what each prune deletes',
   ['Command', 'Deletes', 'Safe on a working machine?'],
   [['docker container prune', 'Stopped containers', 'Yes'],
    ['docker image prune', 'Dangling (untagged) images', 'Yes'],
    ['docker image prune -a', 'Every image no container uses', 'Costs a re-pull, nothing more'],
    ['docker builder prune', 'The build cache', 'Yes — next build is slower'],
    ['docker volume prune', '🔴 Volumes no container references', 'NO — a stopped stack\'s database qualifies'],
    ['docker system prune', 'Containers, networks, dangling images, build cache', 'Yes'],
    ['docker system prune -a --volumes', '🔴 All of the above plus every unused volume', 'Only on a machine you can rebuild']],
   'MODULE 3 §3.6',
   {'note': ('THE HABIT',
             'Run `docker system df` first — it tells you which of the four buckets is actually large. '
             'Most "I am out of disk" cases are the build cache, which is the safest thing to delete.'),
    'widths': [4.0, 3.4, 2.9]}),

  ('myth', 'Four things teams say about containers',
   [('"It is isolated, so it is secure."',
     'It shares your kernel. One kernel bug, and --privileged or a mounted docker.sock, is the whole host.'),
    ('"The image is small, so the attack surface is small."',
     'Size and vulnerability count are different measurements. A 90 MB image can carry a critical CVE; scan it.'),
    ('"We can always rebuild it from the Dockerfile."',
     'Not if it says FROM python:3.12-slim and apt-get install with no pins. Rebuild it next year and see.'),
    ('"Our firewall protects the database container."',
     'Publishing a port writes a NAT rule that UFW never evaluates. Test it from another machine.')],
   'MODULE 3 · MODULE 7'),

  ('lab', '08A',
   'Hardening and Troubleshooting the Runtime',
   'Run the same image locked down, prove each control with the kernel\'s own output, then debug a '
   'container that has no shell.',
   ['Drop every capability and read CapEff to prove it',
    'Run read-only with a tmpfs, and find what the app really writes',
    'Set a memory limit, trigger the OOM kill, and read exit 137',
    'Find the NAT rule a published port creates, and block it in DOCKER-USER',
    'Debug with stats, events and inspect --format',
    'Back up and restore a volume, then prune safely with docker system df'],
   'A container you can defend in a review, and the commands to investigate one at 3 a.m.',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-08-docker-networking-volumes/README-08A-hardening-and-troubleshooting.md. '
               'Optional; about 60 minutes; needs Docker. The iptables part needs sudo and is Linux-only — '
               'it is marked so delegates on Docker Desktop can read it instead.'}),
]


# Per-lab ADVANCED decks: slices of DAY3_EXTRA, each shipped in the lab folder it belongs to.
_D3_A = DAY3_EXTRA[1:10]      # section A + Lab 06A
_D3_B = DAY3_EXTRA[10:17]     # section B + Lab 07A
_D3_C = DAY3_EXTRA[17:]       # section C + Lab 08A

LAB06A_ADVANCED = [
  ('title', 3, 'Lab 06A — Builds in Depth',
   'The advanced build slides, for after class — the cache, BuildKit, multi-architecture',
   ['What the build cache keys on, and what invalidates it',
    'docker history, cache mounts, --target, --platform',
    'Digest pinning, OCI labels and HEALTHCHECK',
    'Optional. Nothing on Day 4 onwards depends on it'],
   'Practise it: labs/lab-06-docker-images/README-06A-builds-in-depth.md'),
] + _D3_A

LAB07A_ADVANCED = [
  ('title', 3, 'Lab 07A — Compose in Depth',
   'The advanced Compose slides, for after class — merging, profiles, health gating, limits',
   ['docker compose config, override files and profiles',
    'Health-gated startup and restart policies',
    'CPU, memory and log limits — and down -v',
    'Optional. Nothing on Day 4 onwards depends on it'],
   'Practise it: labs/lab-07-docker-compose-stack/README-07A-compose-in-depth.md'),
] + _D3_B

LAB08A_ADVANCED = [
  ('title', 3, 'Lab 08A — Hardening and Troubleshooting',
   'The advanced runtime slides, for after class — capabilities, limits, the network path',
   ['Capabilities, no-new-privileges, read-only root, non-root user',
    'Memory limits and the OOM kill · exit 137',
    'Published ports, NAT and DOCKER-USER · stats, events, inspect',
    'Optional. Nothing on Day 4 onwards depends on it'],
   'Practise it: labs/lab-08-docker-networking-volumes/README-08A-hardening-and-troubleshooting.md'),
] + _D3_C
