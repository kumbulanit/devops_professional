# Module 6 — Continuous Delivery and Release Automation

> **Day 5 · ~20 minutes of lecture · Labs 15, 16**
>
> **Learning outcomes.** You can state the difference between Continuous Delivery and
> Continuous Deployment and defend it; describe the deployment pipeline and the artefact
> promotion rule; choose between rolling, blue-green, canary and recreate strategies with
> reasons; design a rollback that actually works, including for database changes; and
> explain the role of an artefact repository and GitOps in release management.

---

## 6.1 The three continuouses

```
 CONTINUOUS INTEGRATION          CONTINUOUS DELIVERY            CONTINUOUS DEPLOYMENT
 ──────────────────────          ───────────────────            ─────────────────────
 commit ─► build ─► test         … ─► deployable artefact       … ─► deployed to PROD
                                     in every environment            automatically
 Every change is merged to       Every change that passes       Every change that passes
 the mainline and verified       the pipeline COULD go to       the pipeline DOES go to
 automatically, daily.           production at any moment.      production, with no human
                                 A human decides WHEN.          in the loop.

 Gate: the build                 Gate: a business decision      Gate: the pipeline itself
                                       (a button)
```

> **Continuous Delivery** — a discipline in which software is built so that it is **always
> in a releasable state**, and any version that has passed the pipeline can be deployed to
> production at the push of a button.
>
> **Continuous Deployment** — Continuous Delivery with the button removed: every change
> that passes every automated gate is deployed to production automatically.

**Continuous Delivery is the capability. Continuous Deployment is a policy choice.** Most
regulated organisations should achieve the first and may deliberately decline the second —
and that is a legitimate, mature position, not a failure. But you cannot choose Continuous
Deployment without first having Continuous Delivery.

### What Continuous Delivery actually requires

| Requirement | Why |
|---|---|
| Comprehensive automated tests you trust | The pipeline is the only quality gate left |
| **Build once, promote the same artefact** | Otherwise you test one binary and ship another |
| Environment parity | A pass in staging must mean something for production |
| Config externalised from the artefact | One image, many environments (day 3's lesson) |
| Automated, repeatable deployment | Manual steps break the chain |
| **Tested rollback** | An untested rollback is a hope, not a plan |
| Database changes decoupled from code changes | The hardest part; see §6.6 |
| Monitoring that can tell you the deploy went well | Otherwise "success" means "the script exited 0" |

---

## 6.2 The deployment pipeline

> **Deployment pipeline** — an automated implementation of the path from version control to
> the user, in which each stage gives increasing confidence and any failure stops the change.

```
 ┌──────────────┐  ┌──────────────────┐  ┌───────────────┐  ┌───────────┐  ┌───────────┐
 │ COMMIT STAGE │─►│ ACCEPTANCE STAGE │─►│ STAGING       │─►│ APPROVAL  │─►│PRODUCTION │
 │  < 5 min     │  │  < 20 min        │  │ prod-like     │  │ (CDelivery│  │           │
 ├──────────────┤  ├──────────────────┤  ├───────────────┤  │  only)    │  ├───────────┤
 │ lint         │  │ integration tests│  │ smoke tests   │  └───────────┘  │ rolling / │
 │ unit tests   │  │ contract tests   │  │ perf baseline │                 │ blue-green│
 │ SAST/secrets │  │ image scan (SCA) │  │ security scan │                 │ / canary  │
 │ BUILD IMAGE  │  │ SBOM             │  │ manual QA if  │                 │ + smoke   │
 │  ── ONCE ──  │  │                  │  │ genuinely     │                 │ + watch   │
 │ push to GHCR │  │                  │  │ needed        │                 │ SLOs      │
 └──────┬───────┘  └──────────────────┘  └───────────────┘                 └─────┬─────┘
        │                                                                         │
        └────────── THE SAME IMAGE DIGEST FLOWS ALL THE WAY THROUGH ──────────────┘
                    sha256:9f3e2a… — never rebuilt, only re-tagged
```

### Principles

1. **Build binaries once.** Rebuilding per environment invalidates every earlier test.
2. **Deploy the same way to every environment.** If production uses a different mechanism,
   production is untested. Same manifests, different values.
3. **Smoke-test every deployment.** Prove the thing you deployed responds correctly.
4. **Fail fast, fail loudly.** A red pipeline stops the line.
5. **Everyone can see the pipeline.** Visibility is the mechanism that makes it matter.
6. **If anything fails, stop.** No manual promotion "just this once".

### Environments

| Environment | Purpose | Data | Who deploys |
|---|---|---|---|
| **Dev** | Fast iteration | Synthetic | Automatic on merge |
| **Test/QA** | Automated acceptance | Anonymised or synthetic | Automatic |
| **Staging** | Prod-like final check, perf, DR rehearsal | Anonymised production-shaped | Automatic |
| **Production** | Real users | Real | Automatic (CDep) or button (CDel) |

**Never use real production data in lower environments** without anonymisation — it is the
most common way training environments become a data-protection incident.

---

## 6.3 Deployment strategies

### Comparison

| Strategy | Downtime | Extra capacity | Rollback speed | Cost | Risk exposure |
|---|---|---|---|---|---|
| **Recreate** | **Yes** | None | Redeploy old (slow) | Lowest | All users, immediately |
| **Rolling** | No | ~ +1 pod | Reverse the roll (minutes) | Low | Grows gradually |
| **Blue-Green** | No | **2× for the cut-over** | **Instant — flip back** | High | All users at once, but reversible in seconds |
| **Canary** | No | +small | Fast — shift weight back | Medium | **Smallest — a few % of users** |
| **A/B testing** | No | +small | Instant | Medium | Segment-scoped (this is a *product* technique) |
| **Shadow / dark launch** | No | 2× compute | N/A — no user traffic | High | **Zero** — traffic is mirrored, responses discarded |

### Rolling update (Kubernetes default)

```
 v1 v1 v1 v1   ──►   v1 v1 v1 v2   ──►   v1 v1 v2 v2   ──►   v2 v2 v2 v2
 Replace pods incrementally, waiting for readiness at each step.
 ✅ No extra infrastructure, built into Deployments, zero downtime with maxUnavailable:0
 ❌ Both versions serve traffic simultaneously → the API must be backward compatible
 ❌ Rollback takes as long as the roll took
```

### Blue-Green

```
        ┌──────────── ROUTER / SERVICE SELECTOR ────────────┐
        │            selector: version=blue                 │
        └───────────────┬──────────────────┬────────────────┘
                 100 % │                   │ 0 %
              ┌────────▼────────┐  ┌────────▼────────┐
              │  BLUE  (v1)     │  │  GREEN (v2)     │
              │  live           │  │  deployed, warm,│
              │                 │  │  smoke-tested   │
              └─────────────────┘  └─────────────────┘

  CUT-OVER = change the Service selector to version=green.  One atomic edit.
  ROLLBACK = change it back.  Seconds, not minutes.
  Keep blue running for one "bake" period, then decommission it.
```

✅ Instant, atomic cut-over and rollback; the new version is fully tested in the real
environment before receiving traffic.
❌ Double the resources during cut-over; **shared state (the database) is the hard part** —
both colours must work against the same schema; long-lived connections and in-flight
sessions need handling.

### Canary

```
   ┌───────────── INGRESS with weighted routing ─────────────┐
   │   90 %  ──────────────► STABLE (v1)   9 replicas        │
   │   10 %  ──────────────► CANARY (v2)   1 replica         │
   └─────────────────────────────────────────────────────────┘
        watch: error rate · p95 latency · saturation · business KPIs
                    │
     ┌──────────────┴───────────────┐
     ▼                              ▼
  metrics healthy               metrics degraded
  → 25 % → 50 % → 100 %         → shift weight to 0 %  (automatic rollback)
```

✅ The smallest possible blast radius; real production traffic and real data validate the
change; supports **automated, metric-driven promotion or abort**.
❌ Needs weighted routing (Ingress annotations, a service mesh, or Argo Rollouts/Flagger),
good metrics, and patience — a canary is only meaningful if you wait long enough to collect
significant data.

**Canary ≠ A/B test.** A canary asks *"is this release safe?"* (an engineering question, a
random slice of traffic). An A/B test asks *"is this variant better?"* (a product question,
a deliberately chosen cohort, statistical significance required).

### Choosing

```
 Can the two versions coexist against the same schema?
   ├── NO  ──► Recreate (accept downtime) or a strict expand/contract migration first
   └── YES ─► Do you need instant rollback for the whole population?
                ├── YES ──► Blue-Green (if you can afford 2× capacity)
                └── NO  ──► Is this change risky or hard to test offline?
                              ├── YES ──► Canary
                              └── NO  ──► Rolling (the sensible default)
```

---

## 6.4 Rollback strategies

> **Rollback** — returning the system to a previously known-good state.
> **Roll-forward** — fixing the problem with a new deployment.

Both are valid. **Roll back first, diagnose second** is almost always the right instinct:
the incident is the priority, and a rollback restores the customer immediately.

| Mechanism | Command | Speed |
|---|---|---|
| Kubernetes rollout undo | `kubectl rollout undo deployment/paytrack-api` | Seconds — the old ReplicaSet still exists |
| Blue-green flip | Change the Service selector back | **Seconds** |
| Canary abort | Shift weight to 0 % | Seconds |
| Redeploy a previous image digest | `kubectl set image … @sha256:…` | A minute |
| Git revert + pipeline | `git revert <sha> && git push` | Full pipeline duration — but **auditable and correct** |
| Feature flag off | Toggle in the flag service | **Instant, and no deployment at all** |

**Feature flags are the fastest rollback that exists**, because they separate *deploy* from
*release*: the code is already in production but dormant, and disabling it is a
configuration change, not a deployment. The cost is flag debt — every flag is a branch in
your code. Set an expiry date on each one and delete it after the release lands.

### Rollback rules

1. **Practise it.** An untested rollback is not a rollback. Rehearse it in a game day.
2. **Automate the trigger.** Smoke tests and SLO burn-rate alerts should be able to abort a
   deployment without a human.
3. **Keep the previous artefact available.** Never delete the image you might roll back to.
4. **Know your point of no return** — usually the first irreversible database migration.
5. **Communicate.** A rollback is an incident event; it belongs in the timeline.

---

## 6.5 Artefact repositories

> **Artefact repository** — a versioned, access-controlled store of build outputs (binaries,
> container images, packages, charts), which serves as the single source of deployable
> artefacts and the boundary between build and deploy.

| Repository | Stores | Used here |
|---|---|---|
| **GHCR** (GitHub Container Registry) | OCI images | **Yes — free for public images** |
| Docker Hub | OCI images | Base images |
| Nexus / Artifactory / Harbor | Everything (Maven, npm, PyPI, OCI, Helm) | Enterprise |
| Cloud-native (ECR, ACR, GAR) | OCI images | Cloud production |

**What a good artefact store gives you:** immutability (a published version is never
overwritten), traceability (which commit produced this?), retention policies, vulnerability
scanning, access control, and **caching of upstream dependencies** so an upstream outage or
a deleted package does not break your builds.

**Tagging convention used in this course:**

```
 ghcr.io/<org>/paytrack-api:9f3e2a1        ← immutable, the git SHA. DEPLOY THIS.
 ghcr.io/<org>/paytrack-api:1.4.2          ← SemVer alias for humans
 ghcr.io/<org>/paytrack-api:main           ← moving pointer to the latest main build
 ghcr.io/<org>/paytrack-api@sha256:…       ← the digest. Strongest possible pin.
 ghcr.io/<org>/paytrack-api:latest         ← ✗ never referenced by a deployment manifest
```

Add OCI labels at build time so any running image can be traced back to its source:

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/<your-username>/paytrack-api" \
      org.opencontainers.image.revision="$GIT_SHA" \
      org.opencontainers.image.version="$VERSION"
```

---

## 6.6 Database changes — the hard part

Code rolls back in seconds. **Data does not.** This is where most "we do continuous
delivery" claims break down.

### Expand / Contract (parallel change)

The only safe pattern for zero-downtime schema change. It splits one breaking change into
three backwards-compatible releases:

```
 RELEASE 1 — EXPAND            RELEASE 2 — MIGRATE          RELEASE 3 — CONTRACT
 ────────────────────          ───────────────────          ────────────────────
 ADD the new nullable column   Deploy code that WRITES       Once all code uses the new
 (or new table). Old code is   both old and new, and READS   column and no rollback
 completely unaffected.        the new one. Backfill data.   target needs the old one:
                                                             DROP the old column.
 ✓ rollback-safe               ✓ rollback-safe               ✓ point of no return
```

Rules that keep this workable:

- **Migrations run separately from the application deploy** — a Kubernetes `Job` or an init
  container, not on every pod start.
- **Migrations are forward-only and additive** wherever possible. "Down" migrations that
  drop data are a trap.
- **Never rename or drop in the same release that stops using something.** Wait a release.
- **Every migration must be tested against a production-sized dataset.** `ALTER TABLE` on
  200 million rows behaves nothing like it does on your laptop.
- **Decouple**: `N` and `N+1` of the application must both work against the schema at any
  moment during a rolling update — because during a roll, both are live simultaneously.

---

## 6.7 Release management and GitOps

### Release management practices

| Practice | Purpose |
|---|---|
| **Release notes generated from commits** | Free, accurate, and forces good commit messages (Conventional Commits) |
| **Semantic versioning for consumers** | Signals compatibility |
| **Release train** (fixed cadence) | Predictability for coordinated organisations |
| **Change freeze** | ⚠️ Usually an anti-pattern: it batches risk into the least-staffed period. DORA shows freezes correlate with *worse* stability |

> 🏦 **Banks freeze more than anyone** — year-end, quarter-end, regulatory reporting dates.
> The intent is sound; the effect is usually a six-week batch deployed on the riskiest day of
> the year, plus urgent work diverted onto the *emergency* path where there is **less**
> review. [Appendix A §A.7](appendix-a-devops-in-a-regulated-bank.md#a7-change-freezes-and-the-evidence-against-them)
> gives the risk-proportionate alternative and the two measurements that win the argument.
| **Progressive rollout by region/tenant** | Bounds the blast radius geographically |
| **Automated change records** | Satisfies audit without a manual CAB — the pipeline *is* the evidence |

### GitOps

> **GitOps** — an operating model in which the **desired state of the system is declared in
> git**, and an in-cluster **agent continuously reconciles** the running system to match it.
> Git is the single source of truth; the deployment mechanism is *pull*, not push.

```
 PUSH-BASED CD                              PULL-BASED (GitOps)
 ┌──────────────┐                           ┌──────────────┐
 │ CI pipeline  │                           │ CI pipeline  │
 │ holds cluster│                           │ builds image │
 │ CREDENTIALS  │                           │ commits new  │
 │      │       │                           │ tag to the   │
 │      ▼       │                           │ config repo  │
 │  kubectl     │                           └──────┬───────┘
 │  apply ──────┼──► cluster                       │ git
 └──────────────┘                                  ▼
                                            ┌──────────────┐
  ✗ CI needs prod credentials               │ CONFIG REPO  │
  ✗ Drift is invisible                      └──────┬───────┘
  ✗ No automatic self-heal                         │ agent PULLS
                                            ┌──────▼──────────────┐
                                            │ Argo CD / Flux      │
                                            │ inside the cluster  │
                                            │ reconciles forever  │
                                            └──────┬──────────────┘
                                                   ▼   cluster
  ✓ No external credentials  ✓ Drift auto-corrected  ✓ Git = audit log  ✓ Revert = rollback
```

The four GitOps principles: the desired state is **declarative**; it is **versioned and
immutable** in git; changes are **pulled automatically** by an agent; and the agent
**continuously reconciles**, correcting any drift.

Lab 15 implements a simplified GitOps flow — the pipeline commits a new image tag to the
manifests directory, and the deployment follows from that commit — so that you see the
mechanism without needing to install Argo CD.

---

## 6.8 Key terms

| Term | Definition |
|---|---|
| **Continuous Delivery** | Every change is always in a releasable state; a human chooses when |
| **Continuous Deployment** | Every passing change is deployed automatically |
| **Deployment pipeline** | The automated path from commit to user, with increasing confidence |
| **Commit stage** | The fast first stage; builds the artefact **once** |
| **Artefact promotion** | Moving one built artefact through environments unchanged |
| **Rolling update** | Replace instances incrementally |
| **Blue-Green** | Two full environments; cut over by flipping a router |
| **Canary** | Route a small percentage to the new version, watch metrics, then promote or abort |
| **Shadow / dark launch** | Mirror production traffic to the new version, discard responses |
| **Feature flag** | Runtime toggle separating deploy from release |
| **Rollback / Roll-forward** | Return to a known-good state / fix with a new deploy |
| **Expand-contract** | Three-release pattern for backwards-compatible schema change |
| **Artefact repository** | Versioned, immutable store of deployable outputs |
| **Immutable tag** | A tag that always refers to the same content (a SHA or digest) |
| **GitOps** | Declarative state in git, pulled and reconciled by an in-cluster agent |
| **Change freeze** | A period during which deployment is prohibited (usually harmful) |
| **Bake time** | The interval a new version is observed before promotion |

---

## 6.9 Module 6 self-check

1. Your organisation says "we do continuous deployment" but a release manager approves each
   production deploy. What do they actually have, and is it wrong?
2. Why must the artefact be built once and promoted rather than rebuilt per environment?
3. You must deploy a change that renames a database column with zero downtime. Describe the
   releases.
4. Blue-green gives instant rollback. Name two things it does **not** roll back.
5. When is a canary the wrong choice?
6. Give three reasons a change freeze can make stability worse.
7. A rollback has never been tested in your organisation. Give three ways this fails at
   03:00.
8. In GitOps, what replaces "the pipeline has production credentials", and why is that
   better?

---

**Next:** [Module 7 — DevSecOps](module-07-devsecops.md)
· Labs: [15](../../labs/lab-15-cd-pipeline-to-k8s/README.md) ·
[16](../../labs/lab-16-deployment-strategies/README.md)
