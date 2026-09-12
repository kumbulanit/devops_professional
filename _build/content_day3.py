# -*- coding: utf-8 -*-
"""Day 3 — Containers with Docker.  Module 3."""
import diagrams as dg

DAY3 = [
 ('title', 3, 'Containers with Docker',
  'Build once, run identically, everywhere — and measure the difference',
  ['Containerisation concepts · Docker architecture · images and layers',
   'Dockerfile craft · multi-stage builds · hardening',
   'Compose · networking · volumes',
   'Labs 06–08 — Build and publish · A full stack · Prove the isolation'],
  'By the end of today PayTrack API is a signed, scanned, 150 MB artefact in a registry'),

 ('section', '1', 'Concepts & Images', 'What a container actually is, and how images are built',
  ['Containers vs virtual machines', 'The Docker architecture', 'Images, layers and the cache',
   'Dockerfile instructions that matter']),

 ('diagram', 'Containers are not small virtual machines', dg.vm_vs_container, 'MODULE 3 §3.1'),

 ('define', 'Container',
  'A process (or process group) running on the host kernel, isolated by Linux NAMESPACES — which '
  'control what it can see — and constrained by CGROUPS — which control what it can use.',
  [('Namespaces: pid, net, mnt, uts, ipc, user', 'Its own process tree, network stack and filesystem view'),
   ('cgroups: CPU, memory, I/O, pids', 'Bounded resources — and a security control, not just a performance one'),
   ('No guest kernel', 'Which is why it starts in milliseconds and costs megabytes'),
   ('Isolation is weaker than a VM', 'A kernel vulnerability crosses the boundary — that is the trade-off')],
  'MODULE 3 §3.1',
  ('THE PROBLEM IT SOLVES', '"It works on my machine." The image contains the application AND its '
   'dependencies AND its runtime, so the thing you tested is bit-for-bit the thing that runs.')),

 ('bullets', 'The Docker architecture',
  [('Docker CLI', 'Sends REST calls to the daemon. It does nothing itself'),
   ('dockerd (the daemon)', 'Builds images, manages containers, networks and volumes'),
   ('containerd', 'The high-level runtime — the CNCF standard, also used by Kubernetes'),
   ('runc', 'Creates the namespaces and cgroups. The actual container-creating program'),
   ('Registry', 'Stores and distributes images — GHCR, Docker Hub, Harbor, ECR'),
   ('The socket is root-equivalent',
    'Membership of the docker group means root on the host. Treat it as a privilege grant')],
  'MODULE 3 §3.2',
  {'note': ('WHY THE LAYERING MATTERS', 'Kubernetes talks to containerd directly — Docker the daemon is '
            'not involved in a modern cluster. The IMAGE FORMAT (OCI) is the standard that connects them, '
            'which is why an image you build today runs anywhere tomorrow.')}),


 ('predict', 'How big is your image, really?',
  'PayTrack API is about 500 lines of Python with four dependencies. Built the way most people '
  'write their first Dockerfile, how large is the resulting image?',
  ['Write down a number in megabytes.',
   'Then write down how long you think a rebuild takes after a ONE-LINE source change.',
   'We will build it both ways in Lab 06 and measure.'],
  'The naive build is ~1.1 GB and re-runs pip install on every source change — 2–3 minutes, on '
  'every commit, for every engineer. The multi-stage build is ~150 MB and rebuilds in under 5 '
  'seconds. Same application, same behaviour.', 3),
 ('diagram', 'Image layers and the build cache', dg.image_layers, 'MODULE 3 §3.3'),

 ('table', 'Dockerfile — the traps and the fixes',
  ['Trap', 'Consequence', 'Fix'],
  [['COPY . . before pip install', 'Cache invalidated on every source change', 'Copy the dependency manifest first'],
   ['apt install then apt remove in a later RUN', 'Image does not shrink — layers are additive',
    'Same RUN, && rm -rf /var/lib/apt/lists/*'],
   ['Shell-form CMD', 'sh -c swallows SIGTERM — 10 s to stop, dropped requests', 'Exec form: CMD ["gunicorn", …]'],
   ['Secrets in ARG or ENV', 'Visible in docker history to anyone who can pull', 'BuildKit --mount=type=secret'],
   ['No USER instruction', 'Runs as root', 'USER 10001 — a numeric, non-root UID'],
   ['No .dockerignore', 'Ships .git, .venv and possibly .env', 'Write it BEFORE the first build'],
   ['FROM python:3.12 (full)', '~1 GB of compilers you never run', 'python:3.12-slim, multi-stage']],
  'MODULE 3 §3.5', {'widths': [2.7, 3.5, 3.2]}),

 ('bullets', 'Why not Alpine?',
  [('Alpine uses musl libc, not glibc', 'Python manylinux wheels are built for glibc'),
   ('So pip falls back to building from source', 'Slower builds, bigger toolchain, subtle runtime differences'),
   ('Known DNS-resolution and thread-stack differences under load', None),
   ('-slim gives you most of the size benefit with none of the surprises',
    '~150 MB vs ~1 GB, and everything still behaves as it did on your laptop'),
   ('Distroless goes further still', 'No shell, no package manager — smallest attack surface, hardest to debug')],
  'MODULE 3 §3.4',
  {'note': ('THE RULE', 'Smaller is better only until it costs you correctness or debuggability. '
            'For Python services, -slim is the sensible default and distroless the deliberate upgrade.')}),

 ('lab', '06', 'Containerising PayTrack API',
  'Build the same application three times and measure the difference at each step.',
  ['Write .dockerignore FIRST — the build context is everything Docker receives',
   'Build it naively, then measure: ~1.1 GB, runs as root, 10 seconds to stop',
   'Write the production multi-stage Dockerfile: slim base, non-root, healthcheck, OCI labels',
   'Measure again: ~150 MB, uid 10001, instant graceful shutdown',
   'Harden the runtime: --read-only, --cap-drop=ALL, --memory, --security-opt',
   'Scan both with Trivy and compare, then let CI publish to GHCR tagged with the commit SHA'],
  'A hardened image under 200 MB, published by CI, tagged with its commit — the artefact days 4–6 deploy'),

 ('section', '2', 'Compose, Networking & Volumes', 'A whole stack in one file',
  ['Docker Compose', 'Service-name DNS', 'Port publishing and its dangers', 'Volumes and persistence']),

 ('diagram', 'The PayTrack stack in one file', dg.compose_stack, 'MODULE 3 §3.6'),

 ('two', 'started ≠ ready — the most common Compose bug',
  ('depends_on: [db]', ['✗ Waits only for the CONTAINER to start',
                        '✗ Postgres may need 5–10 s more to accept connections',
                        '✗ The API crashes on its first query',
                        '✗ Usually "fixed" with sleep 10 in an entrypoint'], 'red'),
  ('condition: service_healthy', ['✔ Waits for the HEALTHCHECK to pass',
                                  '✔ The API starts only when the ledger can answer',
                                  '✔ Deterministic startup, every time',
                                  '✔ Same idea as Kubernetes readiness probes tomorrow'], 'green'),
  'MODULE 3 §3.6',
  ('YOU WILL BREAK THIS ON PURPOSE', 'Lab 07 removes the health condition, destroys the volume so '
   'Postgres must initialise from scratch, and shows you the race. It is the clearest possible '
   'introduction to tomorrow\'s liveness-vs-readiness distinction.')),

 ('bullets', 'Networking facts that bite',
  [('User-defined bridge networks give you container-name DNS', 'An embedded resolver at 127.0.0.11'),
   ('The default bridge network has NO DNS', 'Always create your own network'),
   ('localhost inside a container is THAT container',
    'Each container has its own network namespace — use the service name for siblings'),
   ('Docker writes iptables rules AHEAD of UFW',
    'Publishing "5432:5432" exposes your database even with ufw deny 5432 active'),
   ('Bind to loopback explicitly: "127.0.0.1:5432:5432"', 'Or do not publish the port at all'),
   ('Containers on different user-defined networks cannot reach each other', 'Real segmentation, not convention')],
  'MODULE 3 §3.7',
  {'note': ('SAY THIS OUT LOUD', 'The UFW bypass has caused real breaches and it surprises experienced '
            'Linux administrators. If you take one operational fact home from day 3, make it this one.')}),

 ('table', 'Where data lives — and what survives what',
  ['Storage', 'Survives restart', 'Survives recreate', 'Use for'],
  [['Container writable layer', '✔ Yes', '✗ No — destroyed', 'Nothing you care about'],
   ['Named volume', '✔ Yes', '✔ Yes', 'Production data — databases, uploads'],
   ['Bind mount', '✔ Yes', '✔ Yes', 'Dev source, config files'],
   ['tmpfs', '✗ No — RAM only', '✗ No', 'Secrets, scratch space']],
  'MODULE 3 §3.8', {'widths': [3.0, 2.4, 2.4, 3.0],
   'note': ('THE COMMANDS TO KNOW COLD', 'docker compose down keeps volumes. docker compose down -v '
            'DELETES them — every row in your database, no prompt, no recovery. And Kubernetes recreates '
            'pods constantly, so nothing durable may live on a container filesystem.')}),


 ('compare', 'Alpine or slim?',
  'Alpine is 5 MB and python:3.12-slim is 150 MB. Alpine is obviously the better base image. '
  'Argue the other side.',
  ['Two minutes in pairs. What does Alpine change about how Python packages are installed?',
   'What would you notice first — at build time, or in production at 3 a.m.?'],
  'Alpine uses musl libc, so manylinux wheels do not apply and pip builds from source: slower '
  'builds, a bigger toolchain, and known DNS and thread-stack differences under load. -slim '
  'gives most of the size benefit with none of the surprises. Smaller is better only until it '
  'costs you correctness.', 3),
 ('lab', '07 + 08', 'A Full Local Stack · Prove the Isolation',
  'Three tiers in one file, then verify every claim from the lecture on your own machine.',
  ['Compose: nginx → PayTrack API ×2 → PostgreSQL, with a named volume',
   'Use condition: service_healthy — then BREAK it deliberately and watch the race',
   'Prove service-name DNS, and that localhost inside a container is that container',
   'Prove network isolation, then attach a container to a second network and watch it change',
   'Prove the writable layer dies on recreate but the volume survives',
   'Back up and restore the ledger — a backup you have never restored is a hypothesis'],
  'A three-tier stack started with one command, and demonstrated understanding of DNS, isolation and persistence'),

 ('bank', 'Two banking decisions encoded in the schema',
  [('amount_minor BIGINT — integer minor units',
    'NUMERIC is acceptable; a floating-point type never is. A rounding error in a ledger is a reconciliation break, then an audit finding'),
   ('No column for a primary account number',
    'Storing a PAN pulls this database, its backups, its replicas and everything reading them into PCI-DSS scope'),
   ('The container runs as uid 10001 with a read-only root filesystem',
    'The same controls become Kubernetes securityContext tomorrow, and systemd hardening on day 5'),
   ('OCI labels tie the image to its commit',
    'org.opencontainers.image.revision answers "what exactly is in production?" — the audit question')],
  {'lead': 'Compliance scope is something you design OUT at the boundary, not something you secure later. '
           'The cheapest PCI control is not accepting the data in the first place.',
   'ref': 'Appendix A §A.6 · Lab 07'}),

 ('check', 'Day 3 — check your understanding',
  ['Your image is 1.2 GB and every commit rebuilds all dependencies. Name the two Dockerfile '
   'changes that fix both problems.',
   'Why does a shell-form CMD cause dropped requests during a Kubernetes rolling update?',
   'You publish Postgres as "5432:5432" on a cloud VM with ufw deny 5432 active. Is the database '
   'exposed? Why?',
   'Explain the difference between docker compose restart and up --force-recreate, in terms of what survives.',
   'Why is depends_on without a health condition the most common Compose bug?']),

 ('close', 3, 'Day 3 complete',
  ['A multi-stage image: 1.1 GB → ~150 MB, root → uid 10001, 10 s → instant shutdown',
   'CI publishing that image to GHCR, tagged with the commit SHA',
   'A three-tier stack — proxy, API ×2, ledger — started with one command',
   'Demonstrated understanding of container DNS, isolation, port binding and persistence'],
  'Day 4 takes that image to Kubernetes. You will build a real three-node cluster on your laptop, '
  'deploy PayTrack with correct probes and limits, then deliberately break it three ways — delete pods, '
  'kill a node, deploy a broken image — and watch the platform cope.'),
]
