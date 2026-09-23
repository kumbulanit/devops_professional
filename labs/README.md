# Labs — the chain

Twenty labs, worked in order. **Each lab consumes what the previous one produced.** Work
straight down the list; the numbering is the dependency order.

Nine more labs — **03A, 04A, 04B, 06A, 07A, 08A, 10A, 11A and 12A** — are **optional "Going Further"
labs** that turn the Day 2, 3 and 4 *Going Further* slides into hands-on practice. Nothing depends on them; do them after class, as
homework, or when you finish a lab early.

**They live inside the lab they extend, not in folders of their own**, each beside the slides that
teach it:

| Folder | Advanced page | Advanced deck |
|---|---|---|
| `lab-03-branching-and-collaboration/` | `README-03A-git-going-further.md` | `Lab03A_Advanced_Git.pptx` (32 slides) |
| `lab-04-github-actions-ci/` | `README-04A-act-and-pipeline-security.md` · `README-04B-gitlab-ci.md` | `Lab04AB_Advanced_Pipelines.pptx` (18 slides) |
| `lab-06-docker-images/` | `README-06A-builds-in-depth.md` | `Lab06A_Advanced_Builds.pptx` (11 slides) |
| `lab-07-docker-compose-stack/` | `README-07A-compose-in-depth.md` | `Lab07A_Advanced_Compose.pptx` (8 slides) |
| `lab-08-docker-networking-volumes/` | `README-08A-hardening-and-troubleshooting.md` | `Lab08A_Advanced_Hardening.pptx` (9 slides) |
| `lab-10-k8s-deploy-app/` | `README-10A-debugging-and-rollouts.md` | `Lab10A_Advanced_Debugging.pptx` (10 slides) |
| `lab-11-k8s-config-secrets-storage/` | `README-11A-access-and-storage.md` | `Lab11A_Advanced_Access_and_Storage.pptx` (8 slides) |
| `lab-12-k8s-ingress-scaling/` | `README-12A-scaling-and-scheduling.md` | `Lab12A_Advanced_Scaling.pptx` (8 slides) |

Every advanced deck is a slice of its day's *Going Further* deck, rebuilt by
`cd _build && python build.py labs`.

| # | Lab | Day | Min | Produces | Consumed by |
|---|-----|-----|-----|----------|-------------|
| 00 | [Workstation Setup](lab-00-workstation-setup/) | 1 | 25 (+15) | Verified Ubuntu 24.04 toolchain; GitHub account + `gh` sign-in (optional: GitLab, act) | everything |
| 01 | [Value Stream Mapping](lab-01-value-stream-mapping/) | 1 | 35 | `docs/value-stream.md`, CALMS + DORA baseline | 02, 19 |
| 02 | [Git Fundamentals](lab-02-git-fundamentals/) | 1 | 25 | Local repo with PayTrack API | 03 |
| 03 | [Branching & Collaboration](lab-03-branching-and-collaboration/) | 2 | 45 | GitHub repo, branch protection, merged PRs, **team Network graph** | 04, 15 |
| 03A | [Git, Going Further](lab-03-branching-and-collaboration/README-03A-git-going-further.md) *(optional)* | 2 | 80 | A practice repo where you use reset, reflog, bisect, revert, cherry-pick, tags, interactive rebase and safe force-pushing | — |
| 04 | [GitHub Actions CI](lab-04-github-actions-ci/) | 2 | 35 | `ci.yml` as a required status check | 06, 15, 17 |
| 04A | [act & Pipeline Security](lab-04-github-actions-ci/README-04A-act-and-pipeline-security.md) *(optional)* | 2 | 90 | `act` locally; secret masking and script injection seen live; SHA-pinned, audited `ci.yml` with a build job; `Makefile`; tag-triggered `release.yml` | — |
| 04B | [GitLab CI](lab-04-github-actions-ci/README-04B-gitlab-ci.md) *(optional)* | 2 | 60 | GitLab account + project, `.gitlab-ci.yml`, protected `main` with *Pipelines must succeed* | — |
| 05 | [Jenkins CI](lab-05-jenkins-ci/) | 2 | 20 | `Jenkinsfile` + a written comparison | *(comparison only)* |
| 06 | [Docker Images](lab-06-docker-images/) | 3 | 40 | Multi-stage image on GHCR | 07, 10, 15 |
| 06A | [Builds in Depth](lab-06-docker-images/README-06A-builds-in-depth.md) *(optional)* | 3 | 60 | Cache measurements, a BuildKit cache mount, a digest-pinned Dockerfile, a multi-arch image | — |
| 07 | [Compose Stack](lab-07-docker-compose-stack/) | 3 | 35 | `compose.yaml`: proxy + API ×2 + Postgres | 08, 11 |
| 07A | [Compose in Depth](lab-07-docker-compose-stack/README-07A-compose-in-depth.md) *(optional)* | 3 | 60 | Dev/UAT overlays, a tooling profile, CPU/memory/log limits, and a database restore you have tested | — |
| 08 | [Networking & Volumes](lab-08-docker-networking-volumes/) | 3 | 20 | Verified DNS, isolation, persistence | 11 |
| 08A | [Hardening & Troubleshooting](lab-08-docker-networking-volumes/README-08A-hardening-and-troubleshooting.md) *(optional)* | 3 | 60 | A defensible `docker run` line, proved with kernel output, and the commands to investigate a container | — |
| 09 | [Kubernetes Setup](lab-09-kubernetes-setup/) | 4 | 20 | 3-node k3d cluster, namespaces, quotas | 10–19 |
| 10 | [Deploy to Kubernetes](lab-10-k8s-deploy-app/) | 4 | 35 | Deployment, Service, probes, PDB | 11–19 |
| 10A | [Debugging & Rollouts](lab-10-k8s-deploy-app/README-10A-debugging-and-rollouts.md) *(optional)* | 4 | 70 | Six diagnosed failures, `kubectl debug`, a liveness restart storm, pause/undo | — |
| 11 | [Config, Secrets, Storage](lab-11-k8s-config-secrets-storage/) | 4 | 25 | ConfigMap, Secret, Postgres StatefulSet + PVC | 12, 17 |
| 11A | [Access, Config & Storage in Depth](lab-11-k8s-config-secrets-storage/README-11A-access-and-storage.md) *(optional)* | 4 | 70 | RBAC proved with `auth can-i`, an egress policy that keeps DNS, config that actually reaches the process | — |
| 12 | [Ingress & Autoscaling](lab-12-k8s-ingress-scaling/) | 4 | 17 | Ingress, HPA | 16, 18 |
| 12A | [Scaling, Scheduling & Disruption](lab-12-k8s-ingress-scaling/README-12A-scaling-and-scheduling.md) *(optional)* | 4 | 70 | HPA step sizes, taints and topology spread, a drain that keeps serving — and the PDB deadlock | — |
| 13 | [Terraform](lab-13-terraform-iac/) | 5 | 37 | Reusable module → prod + staging | 19 |
| 14 | [Ansible](lab-14-ansible-config-mgmt/) | 5 | 30 | Baseline + deploy roles, Vault | 19 |
| 15 | [CD Pipeline to Kubernetes](lab-15-cd-pipeline-to-k8s/) | 5 | 25 | GitOps pipeline + reconciler | 16, 17, 19 |
| 16 | [Deployment Strategies](lab-16-deployment-strategies/) | 5 | 17 | Blue-green, canary, weighted routing | 19 |
| 17 | [DevSecOps Pipeline](lab-17-devsecops-pipeline/) | 6 | 37 | 5 security gates, SBOM, Sealed Secrets | 19 |
| 18 | [Observability](lab-18-observability/) | 6 | 40 | Prometheus, Grafana, SLO alerts, runbook | 19 |
| 19 | [Capstone](lab-19-capstone/) | 6 | 25 | Verified platform, game day, 30-60-90 plan | — |

---

## The dependency chain

```
 00 setup
  └─ 01 VSM ──► 02 git ──► 03 GitHub+PRs ──► 04 CI ─────────────┐
                                              ├─ 05 Jenkins      │
                                              └─ 03A · 04A · 04B │   ← optional
                                                                 ▼
                              06 image ──► 07 compose ──► 08 net/vol
                                └─ 06A        └─ 07A        └─ 08A   ← optional
                                  │                          │
                                  ▼                          ▼
              09 cluster ──► 10 deploy ──► 11 config/storage ──► 12 ingress/HPA
                                └─ 10A         └─ 11A               └─ 12A   ← optional
                                  │                                    │
                 13 terraform ────┼──── 14 ansible                     │
                                  ▼                                    ▼
                              15 CD pipeline ──► 16 strategies         │
                                  │                                    │
                                  ├──► 17 devsecops                    │
                                  └──► 18 observability ◄──────────────┘
                                              │
                                              ▼
                                         19 capstone
```

---

## Banking context

**[`../docs/theory/appendix-a-devops-in-a-regulated-bank.md`](../docs/theory/appendix-a-devops-in-a-regulated-bank.md)**
— segregation of duties, CAB → standard change, audit evidence, PCI-DSS/EU DORA, production
data in test, change freezes, legacy core banking. §A.10 maps each lab to the banking control
it strengthens.

## Where do I go? What is the password?

**[`../reference/access-card.md`](../reference/access-card.md)** — every URL, port,
credential, `/etc/hosts` entry and start/stop command in the course, on one page.

## If you fall behind

Every lab README has a **🔁 RECOVER** section near the top — a short block of commands that
fast-forwards your environment to that lab's starting state. Use it rather than trying to
catch up on the previous lab while the room moves on.

## Conventions

| Marker | Meaning |
|---|---|
| **What this does** | Plain-English explanation printed under each command |
| ✅ **Checkpoint** | Prove the step worked before continuing |
| ⚠️ **Gotcha** | A failure mode we know you will hit |
| 🔴 | Something that causes real production incidents — read it twice |
| 🔑 | The key idea of the section |
| 🔁 **RECOVER** | Fast-forward to this lab's starting state |
| 🧩 **Stretch** | Optional / homework |
| 🎯 **Outcome** | What this lab hands to the next |

Every fenced `bash` block is meant to be run as-is. There are no `$` prompts to strip.
