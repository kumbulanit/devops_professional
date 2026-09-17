# Learner Check-ins — Trainer Key

> 🔒 **Trainer only.** Don't project or share this file. The scenario questions are asked on
> day 1 and again on day 6. A delegate who sees the answers early turns the comparison into
> noise. (The repository is public, so it can be found. Nothing is graded, so there is little
> reason to look. Don't point anyone to it.)

The paste-ready questions and the Google Forms steps are in [README.md](README.md). This file
covers **the answers, why each question is there, and what to do with each result**.

---

## How the three check-ins connect

| What is measured | Check-in 1 (before day 1) | Check-in 2 (end of day 3) | Check-in 3 (end of day 6) |
|---|---|---|---|
| Confidence (the same question each time) | Q6 | Q6 | Q1 |
| Scenario: deploy ≠ release | Q7 | — | Q2 |
| Scenario: segregation of duties | Q8 | — | Q3 |
| Scenario: probes when the database is down | Q9 | — | Q4 |
| Scenario: a leaked password | Q10 | — | Q5 |
| What they wanted → whether they got it | Q4 | — | Q6 |
| Scenarios on days 1–3 only | — | Q8–Q10 | — |

Answers are anonymous and no names are collected, so **day 1 and day 6 are compared across
the whole room, not person by person**. With 12–20 delegates that is enough to see what
changed. *Within* a single check-in, Google Sheets keeps each delegate's answers on one row,
so you can still compare one person's answers to each other. The over-confidence check below
relies on that.

### When each check-in runs ([run sheet](../run-sheet.md))

| Check-in | Slot | Notes |
|---|---|---|
| **1** | **Sent with the joining instructions**, due the evening before day 1 | Read the results before you start. Anyone who hasn't done it can do it on day 1 while the Lab 00 installer runs. |
| **2** | **Day 3, 3:15–3:30**: check your understanding, then check-in 2 | Read it that evening. Open day 4 with *"you said, so we're changing…"* |
| **3** | **Day 6, 3:25–3:30**, after the 30-60-90 plan | **Say your thank-yous before you put the QR code up.** Once people are answering, nobody is listening. |

---

## Check-in 1 — Where you're starting from

**Goal:** know the room before you meet it.

**Q1 — Role.** Plan the Lab 03 pairs so developers sit with ops or infrastructure people; each
covers the other's blind spots. If **two or more** delegates choose *security, risk or
compliance* or *release or change management*, re-read Appendix A §A.3, §A.4 and §A.7 before
day 1. They will raise those arguments early.

**Q2 — Tool experience.**
- **Most choose *None yet* or *I've tried one or two*:** plan for the slow end of every lab
  timing, and use the run sheet's cut-lines early rather than late.
- **Anyone choosing *I build or run these tools for other teams*:** that person can help others
  in the labs, and will want the **STRETCH** sections.
- On day 1, **ask the room which CI tool and which container platform they use.** Azure
  Pipelines or GitLab CI: map GitHub Actions terms as you go. OpenShift: say on day 4 that Labs
  09–12 all transfer; the main differences are Routes instead of Ingress, and stricter default
  security (SCCs).

**Q3 — Linux terminal.** This predicts lab pace better than anything else. If **a quarter of
the room or more** choose one of the first two answers, pair each of them with a confident
delegate for Labs 00–02, and slow the first few commands down on the projector.

**Q4 — What they most want.** Adjust your day 1 welcome to the biggest group:

| Most common answer | What to do |
|---|---|
| Practical skills | Keep lectures to their timings and protect lab time above everything else |
| How it all fits together | Show the course's "one thread" diagram (the repository README) at the start of every day |
| Working inside a bank's controls | Bring Appendix A forward: raise §A.3 on day 2 with pull requests, not only on day 6 |
| Depth in one area | **Say on day 1** that this course covers the whole pipeline across six days, and point people to the STRETCH sections for depth. Unmet expectations found out on day 6 lower the score. |
| Asked to attend | A motivation risk. Tie day 1 to their own delivery problems, using Q5 |

Check-in 3 Q6 asks whether the course delivered it.

**Q5 — Where change waits longest.** Lead with the top two answers on day 1, and use this table
to decide which material to emphasise:

| Top answer | Lean on |
|---|---|
| Approval / CAB / sign-off | Appendix A §A.3–A.4, Lab 03 branch protection |
| Test environment | Day 5 Terraform (environments from code), Appendix A §A.6 |
| Manual testing / UAT | Module 2 §2.7 test pyramid, Lab 04 |
| Manual deployment / windows | Labs 15–16, Appendix A §A.7 (change freezes) |
| Another team | Module 1 §1.7 team topologies, Module 9 §9.4 platform engineering |
| Late security or audit findings | Module 7 §7.3 the secure pipeline, Lab 17 |
| Long-lived branches | Module 2 §2.4 trunk-based development |
| I don't know | Is itself a finding: nobody measures it. That is the **M** in CALMS, and Lab 19's plan starts by measuring the DORA metrics. |

**Q6 — Confidence.** The baseline. On day 1 most people should choose one of the first two
answers; the course covers all five parts of that sentence.

**Q7–Q10 — Scenarios.** Answers are in the [scenario answer key](#scenario-answer-key) below.
Expect a lot of **Not sure yet**; that is the honest baseline. **Don't go over these answers
before day 6.** A room that already gets them right needs less foundation time. A cluster on
one particular wrong answer is a misconception you will need to tackle directly.

---

## Check-in 2 — Halfway pulse

**Goal:** find out what to change for days 4–6 while there is still time. Read it the evening of
day 3.

**Q1 — Pace** and **Q2 — Theory/labs balance.** Rules of thumb for a room of 12–20:
- **A third or more choose *A little fast* or *Too fast*:** apply the run sheet's
  [cut-lines](../run-sheet.md#contingency-and-cut-lines) now. For example, make Lab 16's canary
  section homework today, instead of finding out at 3:15 on day 5 that you are behind.
- **A third or more choose a *slow* answer:** point people at the STRETCH sections, and give the
  fastest delegates Lab 19's game-day failures to try early.
- **Answers at both ends:** that is a split room, not a pace problem. Sit fast delegates next to
  slow ones for days 4–5.
- **More lab time requested:** shorten the day 4–5 lectures, and leave the detail to the "What
  this does" notes in the lab READMEs.

**Q3 — Lab experience.**

| Answer | What it means | What to do |
|---|---|---|
| Tools worked, instructions clear | Fine | — |
| Setup or tool problems | An environment problem, not a teaching one | Everyone runs `scripts/install-ubuntu24.sh --verify` at the start of day 4, and fixes failures **before** Lab 09. The 3-node cluster will be worse on a shaky machine. |
| Instructions hard to follow | The READMEs need work | Do the first step of each day 4 lab on the projector. Q7 shows which topics to look at; fix those READMEs after the course. |
| Both | That person is at risk of dropping behind | Sit with them at the day 4 break |

**Q4 — Lab progress.** The labs build on each other, so this is the most important answer in
check-in 2.

| Answer | Blocks | What to do |
|---|---|---|
| **Lab 00 or 02 unfinished** | Everything | Fix the same evening; don't wait. |
| **Lab 03, 04, 06 or 07 unfinished** | Labs 10–11 on day 4 need the Lab 06 image and Lab 07 settings; Labs 15 and 17 need the Lab 03 repo and Lab 04 CI | **Must** be done before day 4's Lab 10. Share the lab's 🔁 RECOVER block, or work through it at the start of day 4. |
| **Only Lab 01, 05 or 08 unfinished** | Lab 01 feeds the Lab 19 plan; 05 and 08 feed nothing directly | Fine for now. Finish Lab 01 before day 6. Say out loud that 05 and 08 can wait, to take the pressure off. |
| All finished | — | — |

**Q5 — Enjoyment.** If **a third or more** choose *It's OK* or lower, Q1–Q3 usually show why
(pace, balance or broken labs). Fix the biggest cause and tell the room on day 4.

**Q6 — Confidence.** Compare with check-in 1 Q6. The question covers Kubernetes, security and
monitoring, which haven't been taught yet, so *On my own* is not expected by day 3. You want
people moving out of *I couldn't do this yet* and towards *With notes and documentation*.

**Q7 — Least clear topic.** Take the **top two** into the day 4 recap. If one topic is chosen by
a third of the room, give it five minutes on its own.

**Q8 — Undo a pushed commit.** ✅ **"git revert on the commit, then push…"** (2nd option)

| Chose | Probably believes | Put it right with |
|---|---|---|
| reset --hard + force-push | "Undo means making history look clean" | Module 2 §2.5, the golden rule of rebasing. Colleagues who already pulled end up with duplicate commits and phantom conflicts. |
| commit --amend | "Amend fixes a commit" | Amend makes a *new* commit with a new hash, so it rewrites shared history too. Module 2 §2.2: commits are immutable. |
| Delete main | "Start again from the last good state" | The most destructive answer, and branch protection blocks it anyway (Lab 03). |

**Q9 — What goes to production.** ✅ **"That exact image, with the same digest…"** (4th option)

| Chose | Probably believes | Put it right with |
|---|---|---|
| Release manager builds it | "Someone else building it is a control" | That confuses segregation of duties with *who builds*. The control is who *approves* (Appendix A §A.3), and a hand-built image is one nothing tested. |
| A fresh image from the same commit | "Same source means the same artefact" | Not guaranteed: base images and unpinned dependencies change between builds, so you would ship something untested. Module 2 §2.7, *build the artefact exactly once*; Module 6 §6.2. |
| "latest" | "Newest is best" | `latest` is a moving label, not a version. Module 6 §6.5: deploy the SHA or digest, never `latest`. |

**Q10 — localhost in a container.** ✅ **"Inside a container, localhost means that container itself…"** (1st option)

| Chose | Probably believes | Put it right with |
|---|---|---|
| Publish the port again | Ports have to be published for containers to reach each other | Publishing (`-p`) is for the **host**. Containers on the same Compose network reach each other by service name, and publishing Postgres is where Lab 08's UFW-bypass risk starts. |
| Needs Kubernetes | Containers can't talk to each other | Compose's built-in DNS already does it: Lab 07's `api` reaches `db:5432`. |
| Postgres rejects applications | A database permissions problem | It is a networking problem. Lab 08 Step 1.3, and checkpoint Q2 in the [answers](../../solutions/lab-08-answers.md). |

If more than a quarter of the room gets Q10 wrong, **repeat Lab 08 Step 1.3 as a two-minute demo
at the start of day 4**. Kubernetes Services rely on the same "use the name, not localhost"
idea.

### Tell the room what you changed

Pick **one** change based on check-in 2 and announce it at the start of day 4:

> *"Yesterday most of you said the labs were fast, and Docker networking was the least clear
> topic. So this morning I'm starting with a two-minute networking demo, and the canary part
> of Lab 16 is now homework."*

When delegates see their answers change something, they answer check-in 3 honestly. Don't skip
this, even if the change is small.

---

## Check-in 3 — What you're taking back

**Goal:** find out what they learned, how the course went, and what happens next. Read it after
the course; it feeds your report to the client.

**Q1 — Confidence.** Compare with check-in 1 Q6 and check-in 2 Q6. See
[Reading the results](#reading-the-results).

**Q2–Q5 — Scenarios.** Compare with check-in 1 Q7–Q10, using the answer key below.

**Q6 — Did it deliver what they wanted.** Read it next to the spread of answers to check-in 1
Q4. If *Partly* or lower is common, look at what the biggest group wanted on day 1. The usual
cause is *depth in one area* that a six-day breadth course was never going to provide, which is
why check-in 1 tells you to say so on day 1.

**Q7 — Most valuable.** The top two show the client what the course was worth to them.

**Q8 — First action in 30 days.** Count how many chose **"Nothing yet: I need to agree it with
my manager or team first"**. A large share means the barrier is permission, not skills. Read it
together with Q9.

**Q9 — Biggest barrier.** This result is for **the client's sponsor**, more than for the
delegates. If *the change-approval process* or *tools aren't approved* leads, the barrier is
organisational, and more training won't fix it. Say so in your report, and point to Appendix A
§A.4 (from a CAB to automated change management) as the conversation to have.

**Q10 — Would you recommend it.** Report the actual counts ("14 Definitely, 5 Probably, 1 Not
sure"), not a percentage; with 12–20 people, one delegate moves a percentage by 5–8 points. For
each *Probably not* or *Definitely not*, open that delegate's row in Sheets. Their Q6 answer
usually shows what went wrong.

---

## Scenario answer key

These four questions appear in check-in 1 (Q7–Q10) and again in check-in 3 (Q2–Q5).

### Deploy ≠ release · ✅ **"It can be deployed to production switched off, behind a feature flag…"** (3rd option)

| Chose | Probably believes | Where the course fixes it |
|---|---|---|
| Can't be done | Deploying and releasing are the same act | Module 1 §1.5 *Release ≠ Deploy*: deploying is a technical act, releasing is a business one |
| Wait in the test environment | Unreleased code has to be held back in a lower environment | The large-batch habit Module 1 §1.2 argues against; two weeks in UAT is two weeks of drift |
| Separate production environment | Hiding a feature needs separate infrastructure | Feature flags, dark launches and traffic weighting (Module 6 §6.3–6.4, **Lab 16**) do it with one production environment |

### Segregation of duties · ✅ **"Branch protection requires a second person to approve every pull request…"** (1st option)

| Chose | Probably believes | Where the course fixes it |
|---|---|---|
| Weekly CAB | Segregation of duties means a committee | A CAB *does* meet the control, but not "several times a day". Appendix A §A.3: the definition says nothing about a committee, and a CAB only reviews the changes that reach its agenda. §A.4 covers moving to standard changes. |
| Ops team deploys by hand | Segregation of duties means another team deploys | Also meets the control, also fails on speed. §A.3 says the definition *"does not say a different team deploys"*. A pipeline deploying, rather than a person, is the stronger control (Lab 15). |
| Needs a regulatory exception | Automation and regulation can't coexist | The myth this course sets out to break: §A.3's four controls and the §A.9 control-objective mapping |

*CAB* and *ops team* answers are likely to be common on day 1 in a bank. **If they are still
common on day 6**, give Appendix A more time with the next group. This question says the most
about whether the course changed how people think, not only what they know.

### Probes when the database is down · ✅ **"They keep running but fail their readiness check…"** (4th option)

| Chose | Probably believes | Where the course fixes it |
|---|---|---|
| Liveness fails, pods restart | "A restart fixes connection problems" | **The restart storm.** Module 4 §4.3: *liveness must not depend on anything external; readiness should.* Restarting every pod during a database blip turns a two-minute database problem into an application outage. Lab 10 (why `/health` never touches the database) and Lab 19 game-day failure 5. |
| Nothing changes | Probes only check that the process is alive | That describes a deployment with **no readiness probe**, where traffic keeps reaching pods that can't serve it. Module 4 §4.3. |
| Autoscaler adds pods | Scaling fixes failures | More pods that can't reach the database are just more failing pods. The autoscaler (HPA) scales on load, not health (Lab 12). |

This is **the course's central Kubernetes lesson**, and PayTrack API is built to show it:
`/health` stays 200 while `/ready` returns 503. A delegate who chooses the liveness answer on
day 6 missed Lab 10's probe discussion.

### A leaked password · ✅ **"Treat the password as compromised: change (rotate) it first…"** (2nd option)

| Chose | Probably believes | Where the course fixes it |
|---|---|---|
| Nothing more | Deleting it in a later commit removes it | Git keeps every commit; the password is one `git log -p` away. Module 7 §7.5; Lab 17's gitleaks scans the *whole history*. |
| Rewrite history, done | Scrubbing the history is the fix | Module 7 §7.5: ***"Rotating is mandatory; scrubbing history is cosmetic."*** Clones, forks and CI caches already have the old commit. |
| Make the repo private | Hiding it undoes the exposure | Anyone who cloned it still has the password. Changing it is the only real fix. |

**Watch the "rewrite history" answer.** It appeals to people who know a bit of Git, so it can go
*up* between day 1 and day 6. If it does, Lab 17's history-cleaning steps are getting more
attention than *rotate first*.

---

## Reading the results

In Google Forms, open **Responses → Link to Sheets** for each check-in. Every delegate is one
row, and every question is one column.

### Confidence (check-in 1 Q6 → check-in 2 Q6 → check-in 3 Q1)

Count each answer in each check-in, then write the counts side by side:

| | Check-in 1 | Check-in 2 | Check-in 3 |
|---|---|---|---|
| I couldn't do this yet | | | |
| Only with a lot of help | | | |
| With notes and documentation in front of me | | | |
| On my own | | | |
| On my own, and I could teach a colleague | | | |

The number to quote to the client is **how many ended on *On my own* or higher**. *With notes
and documentation* is also a good day 6 result: it is how most engineers really work.

### Scenarios (check-in 1 Q7–Q10 → check-in 3 Q2–Q5)

For each of the four questions, count three things on day 1 and on day 6:

| | Day 1 | Day 6 | What a good change looks like |
|---|---|---|---|
| Correct | | | Up, clearly |
| Not sure yet | | | Down, close to zero |
| The most common wrong answer | | | Down, and not replaced by another wrong answer |

To count the correct answers to one question, use COUNTIF on that question's column. The `*`
means "anything after this", so you only need the start of the answer. In each sheet, column A
is the timestamp and each question follows in order: the probes question is **column J** in
check-in 1 (Q9) and **column E** in check-in 3 (Q4).

```
=COUNTIF(E:E, "They keep running but fail their readiness check*")
```

If a wrong answer **goes up** between day 1 and day 6, look at that first. It usually means a
slide or lab step is teaching the opposite of what it meant to.

### Over-confidence (check-in 3 only)

Look at check-in 3 in Sheets. Count the delegates who answered Q1 **On my own** or higher but
got **two or more** of Q2–Q5 wrong (not counting *Not sure yet*). They feel ready and would
still, say, set up a restart storm. It is the most useful thing this data can show, and nothing
else in the course measures it.

### What this data can't tell you

- Confidence reported at the end of an enjoyable week **overstates** what people can still do a
  month later. Treat the day 6 figure as a ceiling.
- Four scenario questions indicate, rather than prove, what people learned. They show whether
  the **four ideas** the course is built around landed.
- People who skip a check-in are rarely the happiest ones, so a low response rate flatters the
  results. Keep check-ins 2 and 3 in class, where almost everyone answers.

### A one-paragraph summary for the client

> *<N> delegates completed the course. Before day 1, <n> said they could take an application
> from source code to production on their own; by day 6, <n> could. On four scenario questions
> covering deployment, segregation of duties, Kubernetes resilience and handling a leaked
> password, correct answers rose from <a> to <b> out of <4N>, and "not sure" answers fell from
> <c> to <d>. The biggest shift was on <question>. For the next 30 days, the most common first
> action is <Q8>; the most common barrier is <Q9>, which is <organisational / technical>
> rather than a skills gap. <n> of <N> would definitely recommend the course.*
