# Appendix A — DevOps in a Regulated Bank

> **Woven through all six days · referenced from Modules 2, 6, 7 and 9**
>
> **Why this appendix exists.** Every delegate on this course works in a bank. The single
> most common objection to DevOps in banking is *"we can't do that — we're regulated."*
> That objection is usually **half right and half an excuse**, and being able to tell which
> half is which is the most valuable thing you can take back to your team.
>
> ⚠️ **This is engineering guidance, not legal advice.** Regulatory interpretation belongs to
> your Compliance, Risk and Internal Audit functions. Use this to have a better-informed
> conversation with them — not to replace it.

---

## A.1 What is actually different about a bank

Strip away the folklore and four things genuinely differ:

| | Ordinary software company | Bank |
|---|---|---|
| **Blast radius of a bad change** | Users see errors | Customers lose access to their money; payments fail; a regulator is notified |
| **Who else has a say** | The team | Risk, Compliance, Internal Audit, the regulator, and often a group parent |
| **Evidence burden** | "It works" | "Prove, months later, who approved this, what was tested, and that the tester was not the author" |
| **Reversibility** | Roll back the code | Money has moved. A payment cannot be un-sent; a ledger entry is corrected by a further entry, never deleted |

**Everything else people claim is special usually is not.** "We can't deploy often", "we need
a CAB for every change", "developers can't see production" — those are *implementations* of
controls, not the controls themselves, and almost all of them have a better automated form.

> 🔑 **The reframe that wins the argument:** a regulator does not require a meeting. It
> requires a **control** that is **designed effectively**, **operating effectively**, and
> **evidenced**. A meeting is one way to achieve that — and, measurably, a poor one.

---

## A.2 The regulations that actually shape a delivery pipeline

| Regime | Scope | What it means for your pipeline |
|---|---|---|
| **PCI-DSS v4.0** | Anything touching cardholder data | Secure development (Req. 6), change control, segregation of duties, vulnerability management with defined remediation windows, no production PANs in test. **Scope is the whole game** — design systems so they never touch a PAN |
| **EU DORA** (Reg. 2022/2554, applying since **17 Jan 2025**) | EU financial entities | ICT risk management, **major-incident reporting on regulatory clocks**, resilience testing including threat-led penetration testing, and **ICT third-party risk** — including your cloud and your CI vendor |
| **EBA Guidelines** (ICT & security risk; outsourcing) | EU banks | Change management, logging, access control, exit strategies for critical providers |
| **GDPR** | Personal data | Data minimisation, purpose limitation — **directly why you must not copy production data into UAT unmasked**, and why logs must not carry customer identifiers |
| **PSD2 / SCA** | Payments | Strong customer authentication, transaction risk analysis, availability reporting for account access |
| **BCBS 239** | Risk data at G-SIBs | Accuracy, completeness, timeliness and **lineage** of risk data — data pipelines are in scope, not just applications |
| **SOX / ICFR** | US-listed groups | Change management and access controls over financially-significant systems. **Segregation of duties is the control auditors test hardest** |
| **MiFID II** | Investment services | Record keeping and clock synchronisation |
| **Local regulator** (PRA/FCA · BaFin · Banca d'Italia · ECB SSM) | Everything | Operational resilience, important business services, impact tolerances |

### The name collision worth clearing up on day 1

> **DORA the regulation** — the EU **Digital Operational Resilience Act**.
> **DORA the metrics** — the **DevOps Research and Assessment** programme (Module 9 §9.2):
> deployment frequency, lead time, change failure rate, recovery time.
>
> Unrelated origins — and, usefully, aligned in substance. Two of the four DORA *metrics*
> (change failure rate and recovery time) are direct measures of what DORA the *regulation*
> calls operational resilience. **You can report your DevOps metrics as resilience
> evidence**, and that is a genuinely strong card to play with your risk function.

---

## A.3 Segregation of duties without a manual gate

This is the control that generates the most pushback, so it is worth getting exactly right.

> **Segregation of duties (SoD)** — no single individual can both *initiate* and *approve* a
> change to a production system, so that error or fraud requires collusion to succeed.

Note what the definition does **not** say: it does not say "a different team deploys", it does
not say "a committee meets", and it does not say "a human types the deployment command".

```
 TRADITIONAL IMPLEMENTATION                 DEVOPS-NATIVE IMPLEMENTATION
 ─────────────────────────────              ────────────────────────────────────────
 Developer writes the change                Developer opens a pull request
        │                                          │
 Hands to a release team                    CODEOWNERS routes it; branch protection
        │                                   REFUSES a self-approval
 Release team deploys manually              Reviewer (a different person) approves
        │                                          │
 Evidence: a signed form, filed             Pipeline — no human — deploys the artefact
                                                   │
                                            Evidence: the merge commit, the approving
                                            identity, the pipeline run, the image digest
                                            — immutable, timestamped, automatic

 Applies to: the changes that reached       Applies to: 100% of changes, always
             the meeting
```

**The four things that make this hold up in an audit:**

1. **Branch protection with required approvals, and self-approval disabled.** The *system*
   enforces two people, not a policy document. (Lab 03)
2. **The deploying identity is not a human.** The pipeline holds the credential; no engineer
   has standing production write access. **Pull-based GitOps is stronger still** — no
   credential leaves the cluster at all. (Lab 15)
3. **`CODEOWNERS` covers the pipeline itself.** A change to `.github/workflows/` can bypass
   every other control, so it needs the *strictest* review, not the loosest. (Lab 03 Part 5)
4. **Break-glass is a separate, alarmed, time-boxed path** — just-in-time elevated access,
   auto-expiring, with every session logged and reviewed afterwards. It exists, it is rare,
   and every use is a ticket.

> 🏦 **Say this to your auditor:** *"Under the old process, two people reviewed the changes
> that reached the CAB agenda. Under this one, the system makes it impossible to merge
> without a second named approver, on every change, and produces the evidence itself."*
> That is a **stronger** control, and it is easier to test.

---

## A.4 From CAB to automated change management

ITIL 4 already provides the language: not every change needs a change advisory board.

| Change type | Definition | Approval | Example |
|---|---|---|---|
| **Standard** | Pre-authorised, low-risk, **repeatable, well-understood, automated** | **Pre-approved — no CAB** | A reviewed, tested, canaried deployment of a stateless service through the pipeline |
| **Normal** | Needs assessment | Peer/technical approval; CAB only if material | A schema change; a new third-party dependency |
| **Emergency** | Restoring service | Expedited, retrospectively reviewed | A rollback during a SEV1 |

**The strategic move is to get your standard deployment path classified as a *standard
change*.** Everything in this course is the evidence you need to argue for it:

| CAB asks | Your pipeline answers | Lab |
|---|---|---|
| What is changing? | The diff, the commit, the ticket in the message | 02, 03 |
| Who reviewed it? | The PR approval, by a named non-author | 03 |
| Was it tested? | The CI run — lint, unit, coverage floor | 04 |
| Is it secure? | Secret, SAST, SCA, IaC and image scans, all gating | 17 |
| What exactly is deployed? | An immutable image digest, labelled with its commit | 06 |
| Can you back it out? | `git revert`, or a tested `rollout undo` | 15, 16 |
| How would you know it broke? | SLO burn-rate alerts and a linked runbook | 18 |
| Who deployed it? | The pipeline. No human had production write access | 15 |

> 🔑 **Do not try to abolish the CAB.** Ask it to *reclassify one low-risk service*, run that
> for a quarter, and bring back the DORA numbers. Evidence moves risk functions; arguments
> do not.

---

## A.5 Audit evidence, generated rather than assembled

The traditional pattern is an engineer collecting screenshots the week before an audit. It is
expensive, it is retrospective, and — because it is a sample — it proves very little.

| Evidence required | Where it comes from, automatically |
|---|---|
| Change was authorised | GitHub PR: approver identity, timestamp, required review satisfied |
| Author ≠ approver | Branch protection configuration + the PR record |
| Change was tested | CI run, retained artefacts, JUnit results, coverage report |
| Security assessed | Scan results and the SBOM stored per build (Lab 17) |
| What is running in production | Deployed image **digest**, plus the OCI `revision` label → the commit |
| When it was deployed, and by what | Pipeline run id; the git history of the deployment overlay (Lab 15) |
| Rollback capability | Rollout history; a rehearsed and documented procedure |
| Incidents and remediation | Alert history, incident record, blameless post-mortem with owned actions (Lab 18) |
| Access control | RBAC as code, reviewed in PRs; no standing production access |

**Retention is the part teams forget.** Pipeline logs and scan artefacts are audit evidence:
set retention to match your regulatory requirement (often 5–7 years for change records),
not to your CI tool's 90-day default. Decide this deliberately and write it down.

---

## A.6 Production data must not be in your lower environments

The most common real compliance failure in bank engineering, and it is entirely avoidable.

**Why it happens:** "we need realistic data to test properly." Legitimate need, wrong solution.

**What it costs:** every UAT database, every developer laptop, every backup and every log of
those environments now contains customer personal data — usually with weaker access control
than production, and often outside the intended jurisdiction. That is a GDPR breach waiting
to be discovered, and under PCI-DSS a PAN in a test system pulls that system into scope.

| Approach | Suitable for |
|---|---|
| **Synthetic data generation** | The default. Volume and shape without any real customer |
| **Irreversible masking / tokenisation** | When you need production-shaped distributions. Must be **irreversible** and applied *before* the data leaves production |
| Subsetting + masking | Large estates where full volume is impractical |
| **Raw production copy** | ✗ Essentially never. If it is genuinely unavoidable, the target environment inherits production's *full* control set — access, encryption, retention, monitoring — and is treated as production |

**In this course:** PayTrack API never accepts a PAN (it is rejected at the edge with a 400),
stores only the last four digits, and logs no customer identifier. **Scope is something you
design out at the API boundary, not something you secure afterwards.**

---

## A.7 Change freezes, and the evidence against them

Almost every bank freezes: year-end, quarter-end, Black Friday, regulatory reporting dates.

**The intent is sound** — reduce risk when the business is most exposed and staffing thinnest.
**The effect is usually the opposite:**

```
      FREEZE PERIOD                            THE DAY THE FREEZE LIFTS
  ┌──────────────────────────┐            ┌────────────────────────────────┐
  │ 6 weeks of changes       │            │ 6 weeks of changes deploy      │
  │ accumulate, untested     │  ───────►  │ together, in one batch         │
  │ against each other       │            │ Large batch = hard to diagnose │
  │ Urgent fixes go through  │            │ = slow to recover              │
  │ the EMERGENCY path,      │            │ Skills are rusty               │
  │ with LESS scrutiny       │            │ Change failure rate SPIKES     │
  └──────────────────────────┘            └────────────────────────────────┘
```

Three specific harms worth naming to your risk function:

1. **Batch size is the strongest predictor of change failure.** Freezes manufacture large
   batches, deliberately.
2. **Freezes push urgent work onto the emergency path**, which by design has *less* review —
   so the freeze increases the proportion of your changes that are poorly controlled.
3. **Capability decays.** A team that has not deployed for six weeks is measurably worse at
   it, and the first post-freeze deployment is the riskiest of the year.

**The mature alternative — risk-proportionate, not calendar-proportionate:**
- Freeze **changes to the systems under seasonal stress**, not the whole estate.
- Keep deploying everything else, in small batches, with canaries.
- Require a canary and a tested rollback for anything in the sensitive window.
- Track your change failure rate *inside* and *outside* freeze windows and **show the
  comparison**. In most banks that measurement ends the argument on its own.

---

## A.8 Legacy: the honest part

You will not containerise the core banking platform this year, and nobody expects you to.

| Reality | The DevOps that still applies |
|---|---|
| Core banking on a mainframe | Version-control the JCL and COBOL; automate build and unit test; deploy via pipeline. The tooling exists and is mature |
| Overnight batch windows | You cannot deploy mid-batch — so **automate the deployment and shrink the window**, rather than accepting a manual all-nighter |
| A vendor package you cannot modify | Automate its *configuration*, its *environment* and its *deployment*. Ansible earns its place here (Lab 14) |
| Systems that cannot be tested in isolation | Contract testing and service virtualisation at the boundary |
| An integration layer nobody fully understands | **Start here.** Instrument it first (Lab 18). You cannot improve what you cannot see |

> 🔑 **The pattern that works in banks is the strangler fig**, not the big-bang rewrite:
> put a modern, well-instrumented, well-tested service in front of the legacy system, move
> one capability at a time, and let the old system shrink. Every capability you move gets
> the full pipeline. **PayTrack API is exactly that shape** — a small, fast, observable
> service in front of something older and slower.

---

## A.9 Control-objective mapping

The one-page translation to hand to your risk function.

| Control objective | Traditional implementation | DevOps-native implementation | Automatic evidence |
|---|---|---|---|
| Segregation of duties | Separate release team deploys | PR review, self-approval blocked, pipeline deploys | PR record, branch-protection config |
| Change authorisation | Weekly CAB | Peer review + automated gates; standard-change classification | Merge commit, CI run |
| Change testing | Manual test sign-off | Automated test suite gating the merge | Test results, coverage report |
| Vulnerability management | Quarterly scan report | Every build scanned; risk-tiered gates; SBOM per artefact | Scan output, SBOM, `.trivyignore` with owner + expiry |
| Access control | Standing privileged accounts | Least-privilege RBAC as code; short-lived OIDC; JIT break-glass | RBAC manifests in git, token audit log |
| Configuration management | A manually-updated CMDB | Git is the source of truth; drift detection alerts | `terraform plan -detailed-exitcode` on a schedule |
| Backup and recovery | Documented procedure | Automated, and **restore-tested** | Restore drill records (Lab 08) |
| Incident management | Ticket + post-hoc report | SLO alerts, runbooks, blameless post-mortems with owned actions | Alert history, incident timeline, action tracker |
| Operational resilience (DORA) | Annual DR test | Continuous: canaries, auto-rollback, game days, measured MTTR | DORA metrics, game-day reports (Lab 19) |
| Data protection | Policy document | Synthetic/masked data; no PII in logs; PAN refused at the API edge | Code, tests, secret-scan results |

---

## A.10 Where each course day pays off in a bank

| Day | Lab | The banking control it strengthens |
|---|---|---|
| 1 | 01 VSM | Finds the queue in *your* change process — usually the approval gate |
| 2 | 03 Branch protection, CODEOWNERS | **Segregation of duties, enforced by the system** |
| 2 | 04 CI gates | Change testing evidence on 100 % of changes |
| 3 | 06 Image build | Immutable, traceable artefact — "what exactly is in production?" |
| 4 | 11 Secrets, NetworkPolicy | Access control and network segmentation |
| 5 | 13 Terraform | Configuration management and drift detection |
| 5 | 15 GitOps | **No human holds production credentials**; git is the change record |
| 5 | 16 Canary, rollback | Operational resilience; bounded blast radius |
| 6 | 17 Security gates, SBOM | PCI-DSS Req. 6, DORA third-party/ICT risk, supply chain |
| 6 | 18 SLOs, business alerts | Operational resilience, impact tolerances, incident reporting clocks |
| 6 | 19 Game day | DORA resilience testing; MTTR evidence |

---

## A.11 Self-check

1. Your CAB meets weekly and reviews every change. Design a **stronger** segregation-of-duties
   control that requires no meeting — and name the evidence it produces.
2. An auditor asks: *"Prove that the code running in production today was reviewed by someone
   other than its author."* Answer it from your current systems. How long does it take?
3. Your UAT database is a nightly restore of production. Name the specific regulatory exposures
   and the migration path off it.
4. Your organisation freezes changes for six weeks around year-end. Make the case to change
   that — with the two measurements you would present.
5. DORA the regulation and DORA the metrics: which two metrics map most directly onto
   operational resilience, and how would you present them as evidence?
6. Your CI pipeline holds a credential with production deployment rights. State the risk in
   audit language, and describe the GitOps alternative.
7. PayTrack API refuses a full card number at the edge. Explain the compliance argument for
   designing it that way rather than encrypting the PAN and storing it.
8. Every technical metric is green and customers cannot pay. Which alert catches this, and why
   would a purely RED-based dashboard miss it?

---

**Back to:** [Module 9 — Enterprise DevOps](module-09-enterprise-devops.md) ·
[Course home](../../README.md)
