# Trainer Run Sheet — 6 Days (Day 2: 3 h · Days 1 and 3–6: 3 h 30 m · 20 h 30 m contact time)

**This course is delivered theory-first.** Each session is mostly theory — taught from the day's
deck, with exercises and live demos built in — followed by a short guided practical that starts
the day's labs together. **The labs are finished after class.** Every lab README carries the
full command list, a "What this does" explanation for each step, and a 🔁 RECOVER block, so a
delegate working alone is never stuck and never permanently behind.

| Across the six days | Share of contact time |
|---|---|
| Theory, with exercises and live demos | about 70 % |
| Guided practical (starting the labs together) | about 10 % |
| Recap, check-ins, questions and breaks | about 20 % |

**After class:** the labs take roughly **1½–2 hours per day**, less whatever the guided practical
covered (per-lab estimates are in [labs/README.md](../labs/README.md)). Say this plainly in the
joining instructions, so delegates can protect the time.

Each day has one **15-minute break**. Timings are cumulative from the start of the session.
Section numbers (§1, §2…) refer to the section divider slides in that day's deck.

---

## Day 1 — Foundations and Source Control

**Modules:** 1 (DevOps Foundations) · 2a (Git Fundamentals) · **Deck:** `Day1_DevOps_Foundations.pptx` (63 slides)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | Welcome, introductions · how the six days run: theory in class, labs after · PayTrack API | Talk |
| 0:10 | 0:40 | 30 | **§1** What DevOps is · the definition, clause by clause · the wall · myths · the Three Ways | Theory |
| 0:40 | 1:15 | 35 | **§2** Culture · Westrum · blameless reviews · **COMPARE** rewrite the finding · principles · CALMS · **AUDIT** | Theory + exercises |
| 1:15 | 1:35 | 20 | **§3** Agile vs DevOps · water-scrum-fall · the lifecycle · deploy ≠ release | Theory |
| 1:35 | 1:50 | 15 | ☕ **Break** | — |
| 1:50 | 2:25 | 35 | **§4** Value streams · **PREDICT** where the time goes · **PREDICT** the constraint · Little's Law · Theory of Constraints | Theory + exercises |
| 2:25 | 2:45 | 20 | **§5** DORA metrics · team topologies · anti-patterns · the toolchain | Theory |
| 2:45 | 3:10 | 25 | **§6** Git's object model · **LIVE DEMO** look inside .git · undo · commit messages · .gitignore | Theory + demo |
| 3:10 | 3:25 | 15 | **Guided practical** — Lab 00 `--verify`, then the first steps of Lab 02, together | Practical |
| 3:25 | 3:30 | 5 | Check your understanding · **after class:** Labs 00–02 | Talk |

**After class:** a verified toolchain (Lab 00), a value-stream map of your own organisation
(Lab 01), and a local repository containing PayTrack API (Lab 02).

---

## Day 2 — Working Together on Code  ·  **3 hours**

**Module:** 2b · **Deck:** `Day2_Version_Control_and_CI.pptx` (46 slides) · **Optional reading deck:**
`Day2_Version_Control_and_CI_Going_Further.pptx` (49 slides, not taught; hands-on in Labs 03A/04A/04B) · **Handout:** [Git Command Guide](theory/git-command-guide.md)

**Pitched for beginners, in a 3-hour session.** Every technical word is explained the first time it
appears, and the day opens with a plain-English glossary. Related commands share a slide (add + commit,
pull + push, restore + revert). Everything that does not fit — single-command slides, stash, reset,
reflog, cherry-pick, tag, bisect, clean, rebase in depth, reviews and CODEOWNERS in depth, test types,
Jenkins internals, pipeline security — is in the Going Further deck and the Git Command Guide, for
self-study and Q&A.

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | Welcome back · **Words you will hear today** · the journey of one change (edit → add → commit → push → pull request → merge) | Talk + theory |
| 0:10 | 0:25 | 15 | **§1** Branches: what a branch is · three ways teams use them, and the one this course uses · naming your branch | Theory |
| 0:25 | 0:55 | 30 | **§2** Everyday Git — a normal day · init/clone · status/diff · add + commit · branch/switch · pull + push · restore + revert · *which command do I need?* | Theory |
| 0:55 | 1:25 | 30 | **§3** Combining work: ways to bring a branch into main · what rebase means · how to rebase · merge or rebase? and the golden rule · **COMPARE** · reading a conflict · **LIVE DEMO** a merge conflict | Theory + exercise + demo |
| 1:25 | 1:40 | 15 | ☕ **Break** | — |
| 1:40 | 1:55 | 15 | **§4** Pull requests: what one is · the life of a pull request · the old way and the automatic way · protecting main | Theory |
| 1:55 | 2:10 | 15 | **§5** Continuous Integration: what it means · the simple rules · from your change to the live system · **PREDICT** | Theory + exercise |
| 2:10 | 2:30 | 20 | **§6** The tools: GitHub Actions in four words · a workflow line by line · GitHub Actions or Jenkins? · **LIVE DEMO** the merge button goes grey | Theory + demo |
| 2:30 | 2:55 | 25 | **Guided practical** — Lab 03 together: the shared repository, branch protection, and the **team Network graph on the projector** | Practical (pairs) |
| 2:55 | 3:00 | 5 | Check your understanding · **after class:** finish Lab 03, then Labs 04–05 · optional: Going Further deck, Git Command Guide, Labs 03A / 04A / 04B | Talk |

**Pacing.** 46 slides in about two hours of teaching is roughly three minutes a slide, which suits a
beginner room. On the command slides say the plain-English meaning first, then the Git word. If a delegate
asks about a command that is not taught today, point them to the Going Further deck or the Git Command
Guide rather than going deeper in class.

Lab 03 is the one lab that needs the whole room at once, which is why it gets the longest
guided practical.

**Going Further, hands-on (optional, after class).** Each section of the Going Further deck has a lab
that makes delegates *run* what the slides show:

| Going Further deck | Lab | Needs | About |
|---|---|---|---|
| B — reset, reflog, cherry-pick, tag, bisect, clean · C — merge vs rebase, conflicts, interactive rebase, force-push | [03A — Git, Going Further](../labs/lab-03a-git-going-further/README.md) | Nothing but git and Python — works offline | 80 min |
| D — Actions concepts, securing the pipeline, build automation, versioning | [04A — act and pipeline security](../labs/lab-04a-act-and-pipeline-security/README.md) | Lab 04, Docker, ~6 GB disk | 90 min |
| D — the same pipeline on another platform | [04B — GitLab CI](../labs/lab-04b-gitlab-ci/README.md) | Lab 04, a verified GitLab account | 60 min |

None of them is needed by a later lab. Accounts are the usual blocker, so the pre-course email must
point at **Lab 00 Step 8** (GitHub account, `gh auth login --scopes workflow`, SSH key, and GitLab for
anyone planning Lab 04B).

> **Projector note for Lab 03 Part 6.** Keep
> `https://github.com/<maintainer>/paytrack-api/network` open on the shared screen and refresh it as
> delegates push. It is the moment branching stops being abstract for most of the room.

---

## Day 3 — Containers with Docker

**Module:** 3 · **Deck:** `Day3_Containers_with_Docker.pptx` (57 slides)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:05 | 5 | Recap · CI pipelines still green? *(check while the room settles)* | Talk |
| 0:05 | 0:40 | 35 | **§1** What a container is · VMs vs containers · namespaces · cgroups · **LIVE DEMO** a container is a process · OverlayFS · OCI | Theory + demo |
| 0:40 | 1:05 | 25 | **§2** The Docker architecture · images and digests · layers and the cache · **PREDICT** image size | Theory + exercise |
| 1:05 | 1:30 | 25 | **§3** The lifecycle · the PID 1 problem · **LIVE DEMO** does PID 1 hear SIGTERM? · Dockerfile instructions | Theory + demo |
| 1:30 | 1:45 | 15 | ☕ **Break** | — |
| 1:45 | 2:10 | 25 | **§4** Multi-stage builds · base images · **COMPARE** Alpine or slim · security and operability practices | Theory + exercise |
| 2:10 | 2:30 | 20 | **§5** Docker Compose · the Lab 07 stack · started ≠ ready · commands | Theory |
| 2:30 | 2:55 | 25 | **§6** Network drivers · the UFW bypass · localhost inside a container · volumes and backups | Theory |
| 2:55 | 3:15 | 20 | **Guided practical** — Lab 06 together: `.dockerignore` and the naive build | Practical |
| 3:15 | 3:30 | 15 | Check your understanding · **[Check-in 2 — Halfway pulse](check-ins/README.md#check-in-2--halfway-pulse)** (5 min) · **after class:** Labs 06–08 | Talk + survey |

**After class:** a hardened multi-stage image published by CI (Lab 06), and a full local stack —
nginx, two API replicas, PostgreSQL — started with one `docker compose up` (Labs 07–08).
**Day 4 needs the Lab 06 image.**

---

## Day 4 — Kubernetes for DevOps

**Module:** 4 · **Deck:** `Day4_Kubernetes.pptx` (57 slides)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:10 | 10 | **You said, we did** — the one change from check-in 2 · recap · why an orchestrator | Talk |
| 0:10 | 0:40 | 30 | **§1** Kubernetes defined · control plane and nodes · the reconciliation loop · what `kubectl apply` does · namespaces | Theory |
| 0:40 | 1:30 | 50 | **§2** Pods and patterns · **PREDICT** a node dies · the three probes · **COMPARE** · **LIVE DEMO** a probe takes a pod out of traffic · requests, limits, QoS · Deployments and rolling updates | Theory + exercises + demo |
| 1:30 | 1:45 | 15 | ☕ **Break** | — |
| 1:45 | 2:10 | 25 | **§3** Services and EndpointSlices · service types · cluster DNS · Ingress | Theory |
| 2:10 | 2:35 | 25 | **§4** ConfigMaps and Secrets, honestly · env vars vs files · persistent storage · databases | Theory |
| 2:35 | 3:00 | 25 | **§5** HPA · scalers and PodDisruptionBudgets · debugging in order · banking controls · myths | Theory |
| 3:00 | 3:20 | 20 | **Guided practical** — Lab 09 together: build the three-node cluster | Practical |
| 3:20 | 3:30 | 10 | Check your understanding · **after class:** Labs 09–12 | Talk |

**After class:** PayTrack API on Kubernetes behind an Ingress, with a persistent Postgres,
externalised config and secrets, and autoscaling under load.

---

## Day 5 — Infrastructure as Code and Continuous Delivery

**Modules:** 5 (IaC) · 6 (CD and release automation) · **Deck:** `Day5_IaC_and_Continuous_Delivery.pptx` (57 slides)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:05 | 5 | Recap | Talk |
| 0:05 | 0:25 | 20 | **§1** IaC principles · snowflakes and drift · declarative vs imperative · mutable vs immutable | Theory |
| 0:25 | 1:00 | 35 | **§2** Terraform: blocks · the workflow · reading a plan · **PREDICT** drift · state · variables and modules | Theory + exercise |
| 1:00 | 1:30 | 30 | **§3** Ansible: inventory · playbooks · idempotency · roles and Vault · Terraform + Ansible · anti-patterns | Theory |
| 1:30 | 1:45 | 15 | ☕ **Break** | — |
| 1:45 | 2:20 | 35 | **§4** Delivery vs Deployment · what CD requires · environments · strategies · **LIVE DEMO** a blue-green cut-over | Theory + demo |
| 2:20 | 2:50 | 30 | **§5** Rollback · expand/contract · artefacts · **COMPARE** who holds the keys · GitOps · release management | Theory + exercise |
| 2:50 | 3:20 | 30 | **Guided practical** — Lab 13 together: the module, the plan, and the drift | Practical |
| 3:20 | 3:30 | 10 | Check your understanding · **after class:** Labs 13–16 | Talk |

> **Density warning.** Day 5 carries two modules and the most after-class work. Lab 15 is
> **core** — Labs 17 and 19 build on its pipeline — so tell delegates to do Lab 15 before Lab 16
> if they run short of time. Lab 14 and Lab 16 mark their CORE and STRETCH sections.

---

## Day 6 — DevSecOps, Observability and Enterprise Practice

**Modules:** 7 · 8 · 9 · Appendix A · **Deck:** `Day6_DevSecOps_Observability_Enterprise.pptx` (60 slides)

| From | To | Min | Block | Type |
|---|---|---|---|---|
| 0:00 | 0:05 | 5 | Recap · who still needs a RECOVER block before Lab 17? | Talk |
| 0:05 | 0:50 | 45 | **§1** DevSecOps · testing classes and SBOMs · **PREDICT** which gate · gating on risk · securing the pipeline · secrets · hardening | Theory + exercise |
| 0:50 | 1:30 | 40 | **§2a** Monitoring vs observability · pillars · metric types · RED/USE · Prometheus · PromQL · structured logs | Theory |
| 1:30 | 1:45 | 15 | ☕ **Break** | — |
| 1:45 | 2:20 | 35 | **§2b** **DISCUSS** everything green, nobody can pay · SLOs and error budgets · burn-rate alerting · incident response | Theory + exercise |
| 2:20 | 2:55 | 35 | **§3** Governance · the two DORAs · SRE · platform engineering · scaling · what comes next | Theory |
| 2:55 | 3:10 | 15 | **Guided practical** — Lab 17 together: plant a secret and watch the gate fail | Practical |
| 3:10 | 3:25 | 15 | **AUDIT** what will you actually change? · start your 30-60-90 plan from your Lab 01 baseline | Discussion |
| 3:25 | 3:30 | 5 | Thank-yous and close · **then** **[Check-in 3 — What you're taking back](check-ins/README.md#check-in-3--what-youre-taking-back)** | Survey |

**After class:** security gates and sealed secrets (Lab 17), monitoring with SLO alerts and a
worked incident (Lab 18), and the capstone game day and finished 30-60-90 plan (Lab 19).

> **If the client can add a short follow-up session** (an hour, a week later), use it for the
> Lab 19 game-day debrief and to review the 30-60-90 plans. It is the highest-value hour you can
> add to this course.

---

## Contingency and cut-lines

**If the theory is running long**, compress in this order — the deck still works without them:

1. The **key terms** slide near the end of each deck → leave it for self-study.
2. **Myth vs reality** slides → one sentence each, or skip.
3. The deeper **reference tables** (for example the Dockerfile instruction tables on day 3,
   Terraform meta-arguments on day 5, the future-trends table on day 6) → "it is in the deck and
   the module notes".
4. A **live demo** → talk through the expected output already printed on the slide.

Never compress the exercises marked PREDICT, COMPARE, DISCUSS or AUDIT to nothing: they are
what keeps a theory-heavy session participatory.

**If delegates are falling behind on the after-class labs**, these are safe to defer:
Lab 05 (Jenkins comparison), Lab 08 (networking deep-dive), Lab 14's STRETCH sections, and
Lab 16's canary section. **Never skip:** Labs 00, 02, 03, 04, 06, 07, 09, 10, 15, 17, 18 —
the chain breaks without them.

## Materials to have ready before day 1

- [ ] **Theory decks are in [`slides/`](../slides/)** — one .pptx per day, 16:9, NobleProg
      template. They are GENERATED from `_build/`; if you hand-edit a deck, say so in
      `slides/README.md` or the next rebuild overwrites it.
- [ ] **Read [Appendix A — DevOps in a Regulated Bank](theory/appendix-a-devops-in-a-regulated-bank.md)
      before day 1.** This cohort is from a bank; §A.3 (segregation of duties), §A.4 (CAB →
      standard change) and §A.7 (change freezes) are the three arguments they will raise, and
      you want the answers ready rather than improvised.
- [ ] **Joining instructions say the labs are done after class** — roughly 1½–2 hours a day —
      and name a channel for lab questions between sessions.
- [ ] A shared GitHub **organisation** with delegates invited (Lab 03 needs shared write access).
- [ ] Repositories set to **Public** — free unlimited Actions minutes, free GHCR, and the
      Insights → **Network graph** used in Lab 03 Part 6 (not available on private repos on
      the Free plan).
- [ ] **[Check-in 1](check-ins/README.md#check-in-1--where-youre-starting-from) sent with the
      joining instructions**, and its results read before day 1 — see the
      [trainer key](check-ins/trainer-key.md) for what to do with each answer. Build check-ins 2
      and 3 at the same time, and test all three links on the client's network.
- [ ] `reference/access-card.md` **printed, one per delegate** — every URL, port, password
      and start/stop command in the course on one page.
- [ ] Verified internet egress to `github.com`, `ghcr.io`, `registry-1.docker.io`, `pypi.org`,
      `releases.hashicorp.com`, `get.k3s.io`.
- [ ] Each delegate machine passing `labs/lab-00-workstation-setup` **before** day 1 if possible.
- [ ] A projector-friendly terminal for the live demos: font ≥ 16 pt, light-on-dark, `PS1` shortened.
