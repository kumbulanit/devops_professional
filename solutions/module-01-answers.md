# Module 1 — Self-check answers

**1. Jenkins, Docker and Kubernetes, yet six weeks to ship a one-line change. Which CALMS
dimension is the constraint?**

Almost certainly **Culture** or **Lean**, not Automation. They have the tools, so the delay is
not technical capability — it is hand-offs, approvals and queueing. Map the value stream: the
time will be in wait states (approval boards, environment booking, waiting for QA capacity),
not in process time. The diagnostic question is "how many humans must type something, or say
yes, for that one line to reach production?" This is the classic *automating a broken process*
anti-pattern: automated build steps bolted onto an unchanged manual governance process.

**2. Team A: 40 deploys/day, 30 % change failure rate. Team B: weekly, 2 %. Who is better?**

**Neither answer is defensible from these numbers alone.** DORA measures four metrics for a
reason, and speed must always be reported with stability.

You would need: **MTTR** (A's 30 % failure rate is much less alarming if recovery takes 90
seconds and no user notices — 12 failures a day recovered in 90 seconds may cost less
availability than one weekly failure taking four hours); **blast radius** (are A's deploys
canaried?); **what "failure" means** to each team (definitions vary wildly); and **context**
(a payments ledger and a marketing site are not comparable).

The honest summary: A's failure rate is high enough to investigate, but B's weekly cadence
means every release is a large batch, which is its own risk. Elite performers achieve *both*
high frequency and low failure rate — they do not trade one for the other.

**3. 22 h process time, 340 h lead time.**

Flow efficiency = 22 / 340 = **6.5 %**.

**93.5 % of the time, the change was sitting in a queue.** So optimising the *work* — faster
builds, more developers, better IDEs — attacks 6.5 % of the problem. Even making all work
instantaneous would only cut lead time from 340 h to 318 h. The investment belongs in
**removing queues**: hand-offs, approvals, environment waits, review latency. This is the
single most common misallocation of DevOps investment.

**4. Release vs deploy.**

**Deploy** is technical: place version 2.1 onto the infrastructure. **Release** is a business
decision: make 2.1's behaviour visible to users.

Separating them lets you deploy 20 times a day while releasing on a marketing schedule, and it
makes rollback a config change rather than a deployment.

Techniques: **feature flags** (the code ships dormant and is enabled by a toggle), **dark
launching** (the new path runs and its output is discarded), **traffic weighting** (canary),
and **blue-green** (deployed and warm, but receiving no traffic).

**5. Why is a dedicated "DevOps team" usually an anti-pattern?**

Because DevOps exists to remove the wall between Dev and Ops, and inserting a third team
between them creates **two** walls plus a translation layer. It also concentrates the
knowledge and the pager in a team that did not write the code, which is precisely the
incentive misalignment DevOps set out to fix.

**When a separate team is correct:** a **platform team** building an internal product —
paved-road pipelines, a cluster, an observability stack — consumed **self-service** by
stream-aligned teams. The test is directional: if teams raise tickets and wait, it is the old
ops silo renamed. If teams help themselves and the platform team's success is measured by
their adoption and satisfaction, it is platform engineering.

**6. Little's Law: WIP 30, throughput 3/week.**

`Lead Time = WIP ÷ Throughput = 30 ÷ 3 = ` **10 weeks**.

Cut WIP to 10 at the same throughput: `10 ÷ 3 = ` **3.3 weeks** — a 67 % reduction in lead
time with **no new tools, no new people and no process redesign.** In practice throughput
usually *rises* too, because less context-switching means less waste.

This is why "limit WIP" is the highest-leverage, lowest-cost intervention in Lean, and why it
is almost always the first thing to try.
