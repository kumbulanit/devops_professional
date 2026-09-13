# Trainer Run Sheet — 6 Days × 3 h 30 m (210 minutes/day, 21 contact hours)

Each day is **210 minutes** with one **15-minute break** at roughly the two-thirds point,
leaving **195 minutes of teaching**. The split across the course is deliberately
**35 % lecture / 55 % hands-on / 10 % discussion & recap** — this is a *Professional*
course, so the keyboard time is the point.

Timings below are cumulative minutes from the start of the day.

---

## Day 1 — Foundations and Source Control

**Modules:** 1 (DevOps Foundations) · 2a (Git Fundamentals)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | Welcome, introductions, course map, what "done" looks like on day 6 | Talk |
| 0:10 | 0:35 | 25 | **M1** What DevOps is and is not · the three ways · CALMS | Lecture |
| 0:35 | 0:55 | 20 | **M1** Agile vs DevOps · the DevOps lifecycle (the "infinity loop", honestly) | Lecture |
| 0:55 | 1:20 | 25 | **Lab 00** — Workstation setup (Ubuntu 24.04 toolchain) | Lab |
| 1:20 | 1:45 | 25 | **M1** Value Stream Management · lead time, cycle time, flow efficiency | Lecture |
| 1:45 | 2:00 | 15 | ☕ **Break** | — |
| 2:00 | 2:35 | 35 | **Lab 01** — Map a value stream, find the bottleneck | Lab + discuss |
| 2:35 | 2:55 | 20 | **M1** Dev/Ops collaboration models · toolchain overview | Lecture |
| 2:55 | 3:20 | 25 | **Lab 02** — Git fundamentals: repo, commits, history, undo | Lab |
| 3:20 | 3:30 | 10 | Recap · tomorrow's pre-read · homework: finish Lab 02 stretch | Talk |

**Day 1 exit state:** every delegate has a working toolchain, a value-stream map of their
own delivery process, and a local git repository containing PayTrack API.

---

## Day 2 — Branching, Collaboration and Continuous Integration

**Modules:** 2b (Branching strategies, PRs, merges, CI, Jenkins, GitHub Actions)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:05 | 5 | Recap · check everyone's Lab 02 repo is green *(do this while the room settles)* | Talk |
| 0:05 | 0:35 | 30 | **M2** Branching strategies: GitFlow · GitHub Flow · trunk-based — and when each is wrong | Lecture |
| 0:35 | 0:50 | 15 | **M2** Merge strategies: merge commit · squash · rebase · fast-forward | Lecture |
| 0:50 | 1:35 | 45 | **Lab 03** — Shared GitHub repo, branch protection, PRs, a deliberate merge conflict, **and the team Network graph on the projector** | Lab (pairs) |
| 1:35 | 1:50 | 15 | ☕ **Break** | — |
| 1:50 | 2:15 | 25 | **M2** CI principles · the build pipeline · fast feedback · test pyramid | Lecture |
| 2:15 | 2:50 | 35 | **Lab 04** — GitHub Actions CI: lint, test, coverage, status checks | Lab |
| 2:50 | 3:05 | 15 | **M2** Jenkins architecture · declarative pipelines · agents · when to self-host | Lecture |
| 3:05 | 3:25 | 20 | **Lab 05** — Jenkins on localhost running the same pipeline | Lab |
| 3:25 | 3:30 | 5 | Recap · discussion: hosted vs self-hosted CI | Talk |

**Day 2 exit state:** a protected GitHub repository where every PR is gated by an
automated build, running both in GitHub Actions and in a local Jenkins — and a room that has
seen its own collective branch history drawn in one picture.

> **Projector note for Lab 03 Part 6.** Keep
> `https://github.com/<maintainer>/paytrack-api/network` open on the shared screen and refresh it as
> delegates push. Five minutes, no setup, and it is the moment branching stops being
> abstract for most of the room.

---

## Day 3 — Containers with Docker

**Module:** 3

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | Recap · CI pipelines still green? | Talk |
| 0:10 | 0:40 | 30 | **M3** Why containers · namespaces, cgroups, union filesystems · VM vs container | Lecture |
| 0:40 | 1:00 | 20 | **M3** Docker architecture · images, layers, registries · the Dockerfile instruction set | Lecture |
| 1:00 | 1:40 | 40 | **Lab 06** — Containerise PayTrack API: naive build → multi-stage → non-root → 8× smaller | Lab |
| 1:40 | 1:55 | 15 | ☕ **Break** | — |
| 1:55 | 2:15 | 20 | **M3** Docker Compose · service dependencies · healthchecks | Lecture |
| 2:15 | 2:50 | 35 | **Lab 07** — Full local stack: app + Postgres + Redis + Nginx | Lab |
| 2:50 | 3:05 | 15 | **M3** Networking (bridge/host/none, DNS) · volumes vs bind mounts · best practices | Lecture |
| 3:05 | 3:25 | 20 | **Lab 08** — Prove network isolation and data persistence | Lab |
| 3:25 | 3:30 | 5 | Recap · image hygiene checklist | Talk |

**Day 3 exit state:** a hardened multi-stage image pushed to GHCR by CI, and a
reproducible local stack started with one `docker compose up`.

---

## Day 4 — Kubernetes for DevOps

**Module:** 4

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | Recap · why an orchestrator at all — the problems Compose cannot solve | Talk |
| 0:10 | 0:45 | 35 | **M4** Control plane and node internals · the reconciliation loop · objects and controllers | Lecture |
| 0:45 | 1:05 | 20 | **Lab 09** — Stand up a real 3-node cluster with k3d | Lab |
| 1:05 | 1:30 | 25 | **M4** Pods · ReplicaSets · Deployments · rollout mechanics · Services and kube-proxy | Lecture |
| 1:30 | 1:45 | 15 | ☕ **Break** | — |
| 1:45 | 2:20 | 35 | **Lab 10** — Deploy PayTrack API, scale it, break it, watch it self-heal | Lab |
| 2:20 | 2:35 | 15 | **M4** ConfigMaps · Secrets (and their real security level) · PV/PVC/StorageClass | Lecture |
| 2:35 | 3:00 | 25 | **Lab 11** — Externalise config, add a Secret, give Postgres a PVC | Lab |
| 3:00 | 3:10 | 10 | **M4** Ingress · HPA and the scaling control loop | Lecture |
| 3:10 | 3:27 | 17 | **Lab 12** — Ingress routing + autoscaling under load | Lab |
| 3:27 | 3:30 | 3 | Recap | Talk |

**Day 4 exit state:** PayTrack API running on Kubernetes behind an Ingress, backed by a
persistent Postgres, config and secrets externalised, autoscaling proven under load.

---

## Day 5 — Infrastructure as Code and Continuous Delivery

**Modules:** 5 (IaC) · 6 (CD & release automation)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:08 | 8 | Recap | Talk |
| 0:08 | 0:33 | 25 | **M5** IaC principles · declarative vs imperative · idempotency · drift · state | Lecture |
| 0:33 | 0:48 | 15 | **M5** Terraform: providers, resources, the plan/apply cycle, state, variables, modules | Lecture |
| 0:48 | 1:25 | 37 | **Lab 13** — Terraform provisions the whole platform (Docker + Kubernetes providers) | Lab |
| 1:25 | 1:40 | 15 | ☕ **Break** | — |
| 1:40 | 1:55 | 15 | **M5** Ansible: inventory, playbooks, modules, roles · push vs pull · CM vs provisioning | Lecture |
| 1:55 | 2:25 | 30 | **Lab 14** — Ansible configures node baseline + deploys the app | Lab |
| 2:25 | 2:45 | 20 | **M6** CD vs continuous deployment · deployment strategies · rollback · artifact repos | Lecture |
| 2:45 | 3:10 | 25 | **Lab 15** — End-to-end pipeline: commit → build → scan → push → deploy to k8s | Lab |
| 3:10 | 3:27 | 17 | **Lab 16** — Blue/green cut-over, canary weighting, one-command rollback | Lab |
| 3:27 | 3:30 | 3 | Recap | Talk |

**Day 5 exit state:** the platform is reproducible from code, and a git push deploys to
Kubernetes with a rollback that takes one command.

> **Density warning.** Day 5 is the heaviest day. Labs 13 and 15 are *core*; Lab 14
> (Ansible) and Lab 16 (strategies) are marked **CORE** and **STRETCH** section-by-section
> inside their READMEs. If the room is running slow, teach Lab 16 as a demo and set it as
> homework — do **not** cut Lab 15, because Lab 17 and Lab 19 build on its pipeline.

---

## Day 6 — DevSecOps, Observability and Enterprise Practice

**Modules:** 7 (DevSecOps) · 8 (Monitoring & Observability) · 9 (Enterprise DevOps)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:08 | 8 | Recap | Talk |
| 0:08 | 0:33 | 25 | **M7** Shift-left · the secure pipeline · SAST/DAST/SCA/SBOM · secret management | Lecture |
| 0:33 | 1:10 | 37 | **Lab 17** — Add gitleaks, bandit, pip-audit, Trivy and SBOM gates to the pipeline | Lab |
| 1:10 | 1:35 | 25 | **M8** Monitoring vs observability · the three pillars · RED/USE · SLI/SLO/error budget | Lecture |
| 1:35 | 1:50 | 15 | ☕ **Break** | — |
| 1:50 | 2:30 | 40 | **Lab 18** — Prometheus + Grafana + Alertmanager on the cluster, dashboard, alert, incident | Lab |
| 2:30 | 2:50 | 20 | **M9** DORA metrics · SRE · platform engineering · anti-patterns · GitOps & AI-assisted DevOps | Lecture |
| 2:50 | 3:15 | 25 | **Lab 19** — Capstone: rebuild the whole chain from scratch, then break it and recover | Lab |
| 3:15 | 3:30 | 15 | Capstone debrief · DORA self-assessment · 30-60-90 day plan · close | Discussion |

**Day 6 exit state:** a secured, monitored, reproducible delivery platform, and a written
30-60-90 day improvement plan for the delegate's own organisation.

---

## Contingency and cut-lines

If you are running behind, cut in **this order** — these are the pieces nothing downstream
depends on:

1. Lab 08 (Docker networking deep-dive) → demo it in 5 minutes instead of 20.
2. Lab 05 (Jenkins) → demo only; GitHub Actions carries the CI thread from here on.
3. Lab 16 stretch sections (canary weighting) → homework.
4. Lab 14 (Ansible) → demo the playbook run rather than having delegates write it.

**Never cut:** Lab 00, 02, 03, 04, 06, 07, 09, 10, 15, 17, 18. The chain breaks without them.

## Materials to have ready before day 1

- [ ] **Theory decks are in [`slides/`](../slides/)** — one .pptx per day, 16:9, NobleProg
      template. They are GENERATED from `_build/`; if you hand-edit a deck, say so in
      `slides/README.md` or the next rebuild overwrites it.
- [ ] **Read [Appendix A — DevOps in a Regulated Bank](theory/appendix-a-devops-in-a-regulated-bank.md)
      before day 1.** This cohort is from a bank; §A.3 (segregation of duties), §A.4 (CAB →
      standard change) and §A.7 (change freezes) are the three arguments they will raise, and
      you want the answers ready rather than improvised.
- [ ] A shared GitHub **organisation** with delegates invited (Lab 03 needs shared write access).
- [ ] Repositories set to **Public** — free unlimited Actions minutes, free GHCR, and the
      Insights → **Network graph** used in Lab 03 Part 6 (not available on private repos on
      the Free plan).
- [ ] `reference/access-card.md` **printed, one per delegate** — every URL, port, password
      and start/stop command in the course on one page.
- [ ] Verified internet egress to `github.com`, `ghcr.io`, `registry-1.docker.io`, `pypi.org`,
      `releases.hashicorp.com`, `get.k3s.io`.
- [ ] Each delegate machine passing `labs/lab-00-workstation-setup` **before** day 1 if possible —
      it saves 25 minutes of day 1.
- [ ] A projector-friendly terminal: font ≥ 16 pt, light-on-dark, `PS1` shortened.
