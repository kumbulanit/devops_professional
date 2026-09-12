# Module 9 — Enterprise DevOps Best Practices

> **Day 6 · ~20 minutes of lecture · Lab 19 (Capstone)**
>
> **Learning outcomes.** You can define and calculate the four DORA metrics and place a team
> against the performance bands; explain what SRE adds to DevOps; describe platform
> engineering and the internal developer platform; recognise the common scaling
> anti-patterns; and produce a concrete 30-60-90 day improvement plan for your own
> organisation.

---

## 9.1 DevOps governance

> **DevOps governance** — the set of controls that ensure delivery is compliant, secure and
> auditable **without reintroducing the manual gates that DevOps removed**. In practice:
> replacing document-and-approval controls with automated, evidenced controls.

The traditional model puts a human gate at the end. The DevOps model **encodes the control
into the pipeline**, where it is applied to 100 % of changes rather than to the ones that
reached the CAB agenda.

| Control objective | Traditional | DevOps-native |
|---|---|---|
| Segregation of duties | A different person deploys | **PR review + branch protection**; nobody merges their own change; the pipeline deploys |
| Change approval | Weekly CAB meeting | Peer review + automated tests; the merge commit **is** the approval record |
| Change record | A ticket typed by hand after the fact | Generated from the commit, PR, pipeline run and image digest |
| Vulnerability management | Quarterly scan report | Every build scanned; policy gates; SBOM per artefact |
| Access control | Standing admin accounts | Least-privilege RBAC, short-lived OIDC credentials, just-in-time access |
| Audit evidence | Screenshots collected before the audit | Immutable pipeline logs, signed artefacts, git history |
| Configuration control | A CMDB updated manually | Git is the CMDB; drift detection alerts on divergence |

> **Policy as code** — expressing governance rules in a machine-evaluable form (OPA/Rego,
> Kyverno, Conftest) so they are applied automatically and consistently, and so the policy
> itself is versioned and reviewed.

**The argument to make to a risk officer:** a control applied automatically to every change
is stronger than a control applied by a committee to a sample of changes. DORA's data
supports it — external approval boards showed no improvement in stability and a clear
negative effect on speed.

> 🏦 **Do not try to abolish your CAB.** ITIL 4 already allows a **standard change** —
> pre-authorised because it is repeatable, well-understood and automated. Ask for *one
> low-risk service* to be reclassified, run it for a quarter, and bring back the DORA
> numbers. [Appendix A §A.4](appendix-a-devops-in-a-regulated-bank.md#a4-from-cab-to-automated-change-management)
> has the CAB-question-to-pipeline-answer table to take into that meeting, and
> [§A.9](appendix-a-devops-in-a-regulated-bank.md#a9-control-objective-mapping) the
> control-objective mapping to hand to Risk.

> 🔑 **DORA means two things in your world.** The *metrics* (here) and the EU **Digital
> Operational Resilience Act**. Unrelated origins, aligned in substance — change failure rate
> and recovery time are direct measures of operational resilience, so **your DevOps metrics
> are resilience evidence**.

---

## 9.2 DORA metrics

The four key metrics from *Accelerate* and the DORA research programme. They are
deliberately few, outcome-based, and hard to game in isolation because **speed and stability
are measured together**.

```
        THROUGHPUT (speed)                          STABILITY (quality)
 ┌────────────────────────────────┐       ┌────────────────────────────────────┐
 │ 1. DEPLOYMENT FREQUENCY        │       │ 3. CHANGE FAILURE RATE             │
 │    How often you deploy to prod│       │    % of deploys causing degraded   │
 │                                │       │    service needing remediation     │
 ├────────────────────────────────┤       ├────────────────────────────────────┤
 │ 2. LEAD TIME FOR CHANGE        │       │ 4. FAILED DEPLOYMENT RECOVERY TIME │
 │    Commit → running in prod    │       │    How long to restore service     │
 └────────────────────────────────┘       └────────────────────────────────────┘

   The central finding: these do NOT trade off. High performers are better at BOTH.
   Speed comes FROM the practices that create stability (small batches, automation, tests).
```

### The performance bands

| Metric | **Elite** | **High** | **Medium** | **Low** |
|---|---|---|---|---|
| Deployment frequency | On demand, multiple/day | Weekly → monthly | Monthly → every 6 months | Fewer than every 6 months |
| Lead time for change | Under 1 hour | 1 day → 1 week | 1 month → 6 months | Over 6 months |
| Change failure rate | 0–15 % | 16–30 % | 16–30 % | 16–30 % |
| Failed-deployment recovery | Under 1 hour | Under 1 day | 1 day → 1 week | Over 6 months |

*(Band definitions have shifted between DORA report years; use them as a coarse position
finder, not a certification.)*

### A fifth, added later: **Reliability**

Operational performance against user expectations — availability, latency, performance.
This is where SLOs plug into the DORA model. More recent reports also examine developer
experience, documentation quality and AI adoption as drivers.

### How to measure them without buying anything

| Metric | Source |
|---|---|
| Deployment frequency | Count successful production deploy pipeline runs |
| Lead time for change | Deploy timestamp − commit timestamp of the earliest commit in that deploy |
| Change failure rate | (incidents linked to a deploy + rollbacks) ÷ total deploys |
| Recovery time | Incident start → service restored, from your incident tracker |

### Using them well — and the ways teams misuse them

✅ Trend over time for **one team**; identify the constraint; make improvement visible.
✅ Pair speed with stability, always — never report one alone.

❌ **Comparing teams against each other.** A platform team and a mobile team have
structurally different metrics.
❌ **Making deployment frequency a target.** Goodhart's Law applies: teams will split one
change into ten deploys and learn nothing.
❌ **Measuring individuals.** Guaranteed to destroy the collaboration the metrics exist to
encourage.
❌ Ignoring reliability and treating DORA as a speed scoreboard.

---

## 9.3 Site Reliability Engineering

> **SRE** — Google's discipline of applying software-engineering practice to operations
> problems, with reliability treated as a feature that is explicitly measured, budgeted and
> traded off against feature velocity.

> *"SRE is what happens when you ask a software engineer to design an operations team."*
> — Ben Treynor Sloss

| | **DevOps** | **SRE** |
|---|---|---|
| Nature | A movement / set of principles | A **specific, prescriptive implementation** |
| Origin | Community, 2009 | Google, ~2003 |
| Reliability | "Important" | **Quantified: SLIs, SLOs, error budgets** |
| Ops work | "Automate it" | **Toil capped at 50 %** of an SRE's time, by policy |
| Failure | Blameless learning | Blameless learning + an error-budget policy with teeth |

*"class SRE implements interface DevOps"* is the standard formulation, and it is accurate.

### The practices worth stealing even if you never create an SRE team

| Practice | Definition |
|---|---|
| **SLO-driven decisions** | Reliability targets set from user need, not from ambition |
| **Error budget policy** | An **agreed, written** consequence for exhausting the budget (feature freeze) |
| **Toil budget** | Toil = manual, repetitive, automatable, tactical, scales with growth. **Cap it at 50 %**; the rest is engineering |
| **Blameless post-mortems** | Systems-focused reviews with owned action items |
| **Production readiness review** | A checklist a service must pass before SREs will support it |
| **Graduated engagement** | SRE support is earned by meeting standards, and can be **handed back** if the service degrades |
| **Game days / chaos engineering** | Deliberately inject failure to validate resilience and runbooks |
| **Capacity planning from demand models** | Forecast, not react |

**The error-budget policy is the mechanism that makes SRE more than a rename.** If there is
no written, pre-agreed consequence for exhausting the budget, you have monitoring with
extra vocabulary.

---

## 9.4 Platform engineering

> **Platform engineering** — the discipline of designing and running an **Internal
> Developer Platform (IDP)**: a self-service product, built by a dedicated team, that
> provides golden paths for building, deploying and operating software, in order to reduce
> the cognitive load on stream-aligned teams.

### The problem it addresses

The "you build it, you run it" model succeeded — and then asked every developer to master
Kubernetes, Terraform, Prometheus, CI/CD, networking and security. That is not a reasonable
expectation, and the observed results are shadow ops, inconsistency and burnout.

```
    WITHOUT A PLATFORM                          WITH A PLATFORM
 ┌──────────────────────────────┐        ┌────────────────────────────────────┐
 │ Every team invents its own:  │        │ Golden path (opinionated default):  │
 │ • CI pipeline                │        │ • templated pipeline                │
 │ • k8s manifests              │        │ • generated manifests               │
 │ • monitoring setup           │        │ • observability wired in by default │
 │ • secret handling            │        │ • secrets injected automatically    │
 │ 12 teams × 6 weeks of setup  │        │ new service running in 30 minutes   │
 │ 12 different failure modes   │        │ one hardened, patched, supported path│
 └──────────────────────────────┘        └────────────────────────────────────┘
```

### Principles

1. **Treat the platform as a product** — it has users (developers), a roadmap, a backlog,
   documentation and satisfaction metrics.
2. **Golden paths, not golden cages.** Make the paved road the *easiest* route; allow escape
   hatches for teams with genuinely different needs. Mandating a platform produces
   circumvention.
3. **Self-service.** If a developer must raise a ticket and wait, it is not a platform — it
   is the old ops team with a new name.
4. **Reduce cognitive load**, do not merely relocate it. A platform that requires learning a
   bespoke DSL to avoid learning Kubernetes has moved the problem.
5. **Measure adoption and developer experience.** Voluntary adoption is the only honest
   success signal.

**Typical IDP components:** service catalogue and scaffolding (Backstage), templated
pipelines, environment provisioning, GitOps deployment, observability defaults, secret
management, policy guardrails, and a developer portal tying it together.

---

## 9.5 Continuous improvement

| Practice | Description |
|---|---|
| **Kaizen** | Small, continuous, incremental improvement by the people doing the work |
| **Improvement work in the backlog** | Explicitly budgeted (e.g. 20 % of capacity), not "when things calm down" — they never do |
| **Retrospectives with follow-through** | Actions owned, dated and reviewed at the next retro |
| **Value stream re-mapping** | Quarterly. The constraint moves; re-measure |
| **Blameless post-mortems** | Every incident is free information you already paid for |
| **Communities of practice / guilds** | Cross-team sharing so a local fix becomes a global improvement |
| **Internal open source (InnerSource)** | Any team may contribute to the platform via PR |
| **Game days** | Rehearse failure and rollback before production rehearses them for you |

**The Improvement Kata** in one line: *where are we now → where do we want to be → what is
the one obstacle in the way → what small experiment tests removing it → measure → repeat.*

---

## 9.6 Scaling DevOps across an organisation

```
   STAGE 1 — PILOT           STAGE 2 — EXPAND         STAGE 3 — SCALE       STAGE 4 — EMBED
 ┌───────────────────┐    ┌───────────────────┐    ┌──────────────────┐  ┌────────────────┐
 │ One motivated team│───►│ 3-5 teams         │───►│ Platform team +  │──►│ Default way of │
 │ Real workload     │    │ Extract patterns  │    │ golden paths     │  │ working        │
 │ Measure baseline  │    │ Enabling team     │    │ Communities of   │  │ Continuous     │
 │ DORA metrics      │    │ coaches           │    │ practice         │  │ improvement    │
 │ Prove value with  │    │ Build reusable    │    │ Governance as    │  │ New teams      │
 │ NUMBERS           │    │ pipeline templates│    │ code             │  │ onboard in days│
 └───────────────────┘    └───────────────────┘    └──────────────────┘  └────────────────┘
```

### What actually works

- **Start with a real workload, not a pilot toy.** Nobody is convinced by a proof of concept
  that never had users.
- **Measure the baseline before you change anything.** Without it you cannot demonstrate
  improvement, and the initiative dies at the first budget review.
- **Find the constraint and fix that.** Not the thing you find most interesting.
- **Make the new way easier than the old way.** Adoption follows convenience, not mandates.
- **Executive air cover for the structural changes** — incentives, team boundaries, on-call.
  Culture change without this is theatre.
- **Grow enabling capability**, do not centralise delivery into one heroic team.

### What does not work

- A "DevOps transformation programme" with a two-year plan and no shipped software.
- Buying a toolchain and declaring victory.
- Mandating adoption without removing the friction that caused the old behaviour.
- Renaming Operations to "SRE" or "Platform" with no change to how work flows.

---

## 9.7 Common DevOps anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **DevOps team as a silo** | A third team between Dev and Ops | Stream-aligned teams + a platform team |
| **DevOps = tools** | Big licence spend, unchanged lead time | Change the metrics, structure and incentives |
| **Automating a broken process** | Faster chaos, same outcomes | Map the value stream, fix the process, *then* automate |
| **Vanity metrics** | Deploys per day up, incidents up | Pair speed with stability, always |
| **No rollback plan** | "We'll fix forward" said during an outage | Practise rollback; make it one command |
| **Manual, undocumented deploys** | One person can deploy | Automate and remove the dependency on that person |
| **Snowflake environments** | "It works in staging" | IaC + immutable infrastructure |
| **Ignoring security until the end** | Pen test blocks the release | Shift left; gate on real risk |
| **Alert fatigue** | Pages ignored; incidents missed | Delete non-actionable alerts; alert on symptoms/burn rate |
| **Long-lived branches** | Merge hell every sprint | Trunk-based, short-lived branches, feature flags |
| **Change freezes** | Batched risk at the least-staffed time | Continuous small changes; progressive delivery |
| **Hero culture** | One person fixes everything | Runbooks, shared on-call, documentation, blamelessness |
| **No slack in the system** | 100 % utilisation, nothing improves | Budget improvement capacity explicitly |
| **Copying Netflix/Google** | Chaos engineering before you have tests | Solve *your* constraint at *your* scale |

---

## 9.8 Future trends

| Trend | What it is | Why it matters |
|---|---|---|
| **GitOps** | Declarative state in git, reconciled by an in-cluster agent | Better security model (no external credentials), automatic drift correction, git as the audit log |
| **Platform engineering** | IDPs and golden paths as a product | The mainstream answer to cognitive overload; strongly represented in current DORA and industry research |
| **AI-assisted DevOps** | Code and test generation, PR review, log/alert summarisation, anomaly detection, incident-timeline drafting, IaC generation | Real productivity gains; but AI-generated code raises review, licensing and security questions. DORA's recent work is explicit that **AI amplifies whatever your delivery system already is** — good practice gets faster, bad practice gets faster too |
| **Progressive delivery** | Canary/blue-green/flags automated by controllers (Argo Rollouts, Flagger) | Metric-driven, automatic promotion and abort |
| **eBPF-based observability & security** | Kernel-level instrumentation with no code changes (Cilium, Pixie, Falco) | Deep visibility, near-zero overhead, no re-instrumentation |
| **Supply-chain security (SLSA, sigstore)** | Provenance, signing, attestation, SBOM | Increasingly a regulatory and procurement requirement |
| **FinOps** | Cost as a first-class engineering metric, visible per team and per service | Cloud spend is now an engineering design constraint |
| **WebAssembly / Wasm workloads** | Sub-millisecond, sandboxed, portable runtimes | Emerging complement to containers at the edge |
| **Green/Sustainable software** | Carbon-aware scheduling and efficiency as an objective | Rising regulatory and reporting pressure |

---

## 9.9 Key terms

| Term | Definition |
|---|---|
| **DORA metrics** | Deployment frequency, lead time for change, change failure rate, recovery time |
| **Elite/High/Medium/Low** | DORA performance bands |
| **Goodhart's Law** | "When a measure becomes a target, it ceases to be a good measure" |
| **SRE** | Software engineering applied to operations; reliability quantified and budgeted |
| **Toil** | Manual, repetitive, automatable, tactical work that scales with the service |
| **Error budget policy** | The pre-agreed consequence of exhausting the error budget |
| **Production readiness review** | Standards a service must meet to be supported |
| **Platform engineering / IDP** | Self-service internal platform as a product |
| **Golden path** | The opinionated, supported, easiest route to production |
| **Cognitive load** | The total mental burden a team carries; the thing platforms reduce |
| **InnerSource** | Open-source collaboration practices applied inside an organisation |
| **Policy as code** | Governance rules expressed in machine-evaluable form |
| **GitOps** | Git as the source of truth, reconciled by an in-cluster agent |
| **Progressive delivery** | Automated, metric-driven gradual rollout |
| **FinOps** | Cloud financial management as an engineering practice |
| **Improvement Kata** | A structured routine for continuous improvement experiments |

---

## 9.10 Module 9 self-check

1. Calculate all four DORA metrics for your own team, from real data, right now. If you
   cannot, that is the finding — what is missing?
2. A director asks you to publish a DORA league table ranking all 14 teams. Give your
   response and the reasoning.
3. What single practice makes SRE more than a rename of Operations?
4. Differentiate a platform team from a traditional ops team in three concrete ways.
5. What is a golden cage, and how do you tell whether you have built one?
6. Name three anti-patterns present in your organisation today and the first step for each.
7. Why does AI adoption tend to amplify existing delivery performance rather than fix it?
8. You have three months and one team. Where do you start, and what will you measure?

---

## 9.11 The capstone

Lab 19 asks you to build the entire chain from an empty directory: source control → CI →
image build → security gates → registry → IaC-provisioned cluster → Kubernetes deployment →
progressive rollout → monitoring and alerting. Then you will break it deliberately and
recover it, and finish by writing a 30-60-90 day plan for your own organisation.

**Go to:** [Lab 19 — Capstone](../../labs/lab-19-capstone/README.md)

---

**Reference material:** [`reference/`](../../reference/) — Git, Docker, kubectl, Terraform
and Ansible cheat sheets, plus the DevOps best-practices checklist.
