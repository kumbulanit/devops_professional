# Learner Check-ins — ready to paste into Google Forms

Three check-ins, **10 multiple-choice questions each**, taken at the start, middle and end of the
course.

| | When | Takes |
|---|---|---|
| [**Check-in 1 — Where you're starting from**](#check-in-1--where-youre-starting-from) | Before day 1 | ~4 min |
| [**Check-in 2 — Halfway pulse**](#check-in-2--halfway-pulse) | End of day 3 | ~3 min |
| [**Check-in 3 — What you're taking back**](#check-in-3--what-youre-taking-back) | End of day 6 | ~4 min |

**Questions that come back on purpose.** The last five questions of check-in 1 are the first
five of check-in 3, word for word. Comparing the answers shows what the course changed. The
confidence question is also asked in check-in 2.

> 🧑‍🏫 The answers, and what to do with each result, are in [trainer-key.md](trainer-key.md).

---

## Building a form (about 10 minutes each)

1. Go to **[forms.google.com](https://forms.google.com)** and click **Blank form**.
2. Copy the **Title** and **Description** blocks below into the top of the form.
3. For each question:
   1. Copy the **Question** block into the *Untitled question* box. The type is already
      **Multiple choice**, which is the one you want.
   2. Click into **Option 1** and paste the whole **Options** block in one go. Google Forms turns
      each line into its own option. (If your browser pastes it as one long line, paste the
      options one at a time.)
   3. Switch on **Required** at the bottom right of the question.
   4. Click **⊕ Add question** for the next one.
4. Open the **Settings** tab:
   - **Responses → Collect email addresses: _Do not collect_.** The check-ins are anonymous.
   - Leave **Limit to 1 response** *off*. It forces delegates to sign in with a Google
     account, which many bank staff don't have or aren't allowed to use at work.
   - Leave **Make this a quiz** *off*. Quiz mode is built to show people their score and the
     right answers, which would spoil the day 6 comparison.
5. Leave **Shuffle option order** *off* (in each question's **⋮** menu; it is off by default).
   The day 1 and day 6 versions must look identical.
6. Click **Send → 🔗** and tick **Shorten URL**. To make a QR code for the projector, open the
   link in Chrome and choose **Share → Create QR code**.
7. **Open the link on the bank's network before day 1.** Corporate proxies sometimes block
   Google Forms.

> ⚡ **Shortcut for check-in 3:** build check-in 1 first. Then open it, choose **⋮ → Make a
> copy**, replace the title and description, delete the first five questions, and add
> check-in 3's questions 6–10 at the end. The settings come across too, and the repeated
> questions are then guaranteed to be identical.

**Reading responses:** the **Responses → Summary** tab draws a chart for every question. Click
**Link to Sheets** to get one row per delegate for comparing day 1 with day 6.

---

## Check-in 1 — Where you're starting from

*Send with the joining instructions · due the evening before day 1*

**Title**
```
DevOps Professional · Check-in 1: Where you're starting from
```

**Description**
```
Ten quick multiple-choice questions, about 4 minutes.

This is not a test. Nothing is marked, and we don't collect your name or email.

Some of these questions come back on the last day. If you don't know an answer, choose "Not sure yet" rather than guessing. That is what lets us see what you learned.
```

### Question 1

**Question**
```
Which best describes your role?
```
**Options**
```
Software developer or engineer
Operations, infrastructure or platform engineer
Test or QA engineer
Security, risk or compliance
Architect
Release or change management
Team lead or delivery manager
Other
```

### Question 2

**Question**
```
Which best describes your hands-on experience with DevOps tools such as Git, CI pipelines, Docker and Kubernetes?
```
**Options**
```
None yet
I've tried one or two of them
I use one or two of them regularly at work
I use most of them regularly at work
I build or run these tools for other teams
```

### Question 3

**Question**
```
How comfortable are you working in a Linux terminal: moving between folders, editing files and running commands?
```
**Options**
```
I've rarely or never used one
I can run commands if someone tells me what to type
I'm comfortable with everyday commands
I use one every day and can troubleshoot problems
```

### Question 4

**Question**
```
What do you most want to get from this course?
```
**Options**
```
Practical skills I can use at work straight away
A clear picture of how everything fits together, from a code change to production
How to make DevOps work inside a bank's controls: audit, change approval and security
Depth in one area, such as Kubernetes, CI/CD, security or monitoring
I was asked to attend, and I'm open to whatever is useful
```

### Question 5

**Question**
```
Where does a change wait longest in your team before it reaches production?
```
**Options**
```
Waiting for approval from a change board, CAB or sign-off
Waiting for a test environment
Manual testing or UAT
Manual deployment steps, or waiting for a deployment window
Waiting for another team, such as infrastructure, network, security or DBAs
Rework after late security or audit findings
Merging long-lived branches
I don't know
```

### Question 6 · *repeated in check-ins 2 and 3*

**Question**
```
How confident are you that you could take an application from source code to running in production, with automated tests, a container image, a Kubernetes deployment, security checks and monitoring?
```
**Options**
```
I couldn't do this yet
Only with a lot of help
With notes and documentation in front of me
On my own
On my own, and I could teach a colleague
```

### Question 7 · *repeated in check-in 3*

**Question**
```
A new instant-payments feature has to be in production two weeks before marketing announces it. Which statement is true?
```
**Options**
```
It can't be done: putting code into production is what releases it to customers
It has to wait in the test environment until announcement day, and be deployed then
It can be deployed to production switched off, behind a feature flag, and released on the day by turning the flag on
It needs its own separate production environment that customers can't reach
Not sure yet
```

### Question 8 · *repeated in check-in 3*

**Question**
```
Internal audit requires segregation of duties on every production change: nobody may both make a change and approve it. The team also wants to deploy several times a day. Which approach meets both?
```
**Options**
```
Branch protection requires a second person to approve every pull request, a pipeline deploys it rather than a person, and the approval and pipeline run are kept as evidence
A weekly Change Advisory Board reviews and approves each change before it is released
Developers raise a ticket, and a separate operations team carries out the deployment by hand
It can't be done with automated deployment; the bank would need an exception from its regulator
Not sure yet
```

### Question 9 · *repeated in check-in 3*

**Question**
```
A payments API runs on Kubernetes. Its database becomes unreachable for two minutes. What should happen to the running API pods?
```
**Options**
```
Their liveness check fails and Kubernetes restarts them, because a fresh process re-establishes the database connection
Nothing changes: health checks only confirm that the container's process is still running
The autoscaler adds more pods to absorb the retries, then removes them once the database is back
They keep running but fail their readiness check, so traffic stops reaching them; when the database returns they rejoin without restarting
Not sure yet
```

### Question 10 · *repeated in check-in 3*

**Question**
```
A developer pushes a commit containing a production database password. Ten minutes later they notice, and push a second commit that deletes it. What should happen next?
```
**Options**
```
Nothing more: the latest version of the code no longer contains the password
Treat the password as compromised: change (rotate) it first, then clean it out of the Git history
Rewrite the Git history and force-push; once the password is gone from history, the problem is solved
Make the repository private, so nobody else can see the old commit
Not sure yet
```

---

## Check-in 2 — Halfway pulse

*End of day 3 · in the last 10 minutes*

**Title**
```
DevOps Professional · Check-in 2: Halfway pulse
```

**Description**
```
Ten quick multiple-choice questions, about 3 minutes. Anonymous, as before.

Please be honest. Your answers change how days 4 to 6 are run.
```

### Question 1

**Question**
```
How has the pace felt so far?
```
**Options**
```
Too slow
A little slow
About right
A little fast
Too fast
```

### Question 2

**Question**
```
How is the balance between theory and hands-on labs?
```
**Options**
```
I'd like more theory and fewer labs
About right
I'd like more lab time and less theory
```

### Question 3

**Question**
```
Which best describes your experience of the labs so far?
```
**Options**
```
The tools worked and the instructions were clear
The instructions were clear, but I hit setup or tool problems
The tools worked, but the instructions were hard to follow
I hit tool problems and also struggled with the instructions
```

### Question 4

**Question**
```
How far have you got with Labs 00 to 08? If more than one answer fits, choose the first one that is true.
```
**Options**
```
Lab 00 or Lab 02 isn't finished yet
Lab 03, 04, 06 or 07 isn't finished yet
Everything is finished except Lab 01, 05 or 08
I've finished all of Labs 00 to 08
```

### Question 5

**Question**
```
How much are you enjoying the course so far?
```
**Options**
```
Really enjoying it
Enjoying it
It's OK
Not enjoying it much
Not enjoying it at all
```

### Question 6 · *same as check-in 1, question 6*

**Question**
```
How confident are you that you could take an application from source code to running in production, with automated tests, a container image, a Kubernetes deployment, security checks and monitoring?
```
**Options**
```
I couldn't do this yet
Only with a lot of help
With notes and documentation in front of me
On my own
On my own, and I could teach a colleague
```

### Question 7

**Question**
```
Which topic from days 1 to 3 is still the least clear to you?
```
**Options**
```
DevOps principles, value streams and DORA metrics
Git basics: commits, history and undoing mistakes
Branching, merging and pull requests
CI pipelines with GitHub Actions and Jenkins
Docker images and writing Dockerfiles
Docker Compose, networking and volumes
Nothing, it's all clear so far
```

### Question 8

**Question**
```
You merged a commit to main that broke the build, and three colleagues have already pulled it. What is the safest way to undo it?
```
**Options**
```
git reset --hard HEAD~1, then git push --force, so main looks as if the commit never happened
git revert on the commit, then push: a new commit that undoes the change and leaves history intact
git commit --amend to correct the commit in place, then push it again
Delete main on GitHub and recreate it from the last good commit
Not sure yet
```

### Question 9

**Question**
```
The pipeline built a container image for commit 9f3e2a1, and it passed every test in the test environment. What should be deployed to production?
```
**Options**
```
An image the release manager builds and uploads separately, as an independent control
A fresh image built from the same commit, with the production settings built in
Whichever image is tagged "latest" in the registry, because it is the newest build
That exact image, with the same digest, with production settings supplied when it starts
Not sure yet
```

### Question 10

**Question**
```
In the Compose stack, psql on your laptop connects to localhost:5432 without a problem. But when the api container's DATABASE_URL points at localhost:5432, it can't reach the database. Why?
```
**Options**
```
Inside a container, localhost means that container itself; the API should use the service name, db
The port has to be published a second time for traffic between containers
Containers can't talk to each other until they run on Kubernetes
Postgres accepts connections from the psql client but not from applications
Not sure yet
```

---

## Check-in 3 — What you're taking back

*End of day 6 · the last 5 minutes, after the thank-yous*

**Title**
```
DevOps Professional · Check-in 3: What you're taking back
```

**Description**
```
Ten quick multiple-choice questions, about 4 minutes. Anonymous, as before.

The first five questions are the same ones you answered before day 1. Answer them as you would now, not as you remember answering them then.
```

### Question 1 · *same as check-in 1, question 6*

**Question**
```
How confident are you that you could take an application from source code to running in production, with automated tests, a container image, a Kubernetes deployment, security checks and monitoring?
```
**Options**
```
I couldn't do this yet
Only with a lot of help
With notes and documentation in front of me
On my own
On my own, and I could teach a colleague
```

### Question 2 · *same as check-in 1, question 7*

**Question**
```
A new instant-payments feature has to be in production two weeks before marketing announces it. Which statement is true?
```
**Options**
```
It can't be done: putting code into production is what releases it to customers
It has to wait in the test environment until announcement day, and be deployed then
It can be deployed to production switched off, behind a feature flag, and released on the day by turning the flag on
It needs its own separate production environment that customers can't reach
Not sure yet
```

### Question 3 · *same as check-in 1, question 8*

**Question**
```
Internal audit requires segregation of duties on every production change: nobody may both make a change and approve it. The team also wants to deploy several times a day. Which approach meets both?
```
**Options**
```
Branch protection requires a second person to approve every pull request, a pipeline deploys it rather than a person, and the approval and pipeline run are kept as evidence
A weekly Change Advisory Board reviews and approves each change before it is released
Developers raise a ticket, and a separate operations team carries out the deployment by hand
It can't be done with automated deployment; the bank would need an exception from its regulator
Not sure yet
```

### Question 4 · *same as check-in 1, question 9*

**Question**
```
A payments API runs on Kubernetes. Its database becomes unreachable for two minutes. What should happen to the running API pods?
```
**Options**
```
Their liveness check fails and Kubernetes restarts them, because a fresh process re-establishes the database connection
Nothing changes: health checks only confirm that the container's process is still running
The autoscaler adds more pods to absorb the retries, then removes them once the database is back
They keep running but fail their readiness check, so traffic stops reaching them; when the database returns they rejoin without restarting
Not sure yet
```

### Question 5 · *same as check-in 1, question 10*

**Question**
```
A developer pushes a commit containing a production database password. Ten minutes later they notice, and push a second commit that deletes it. What should happen next?
```
**Options**
```
Nothing more: the latest version of the code no longer contains the password
Treat the password as compromised: change (rotate) it first, then clean it out of the Git history
Rewrite the Git history and force-push; once the password is gone from history, the problem is solved
Make the repository private, so nobody else can see the old commit
Not sure yet
```

### Question 6

**Question**
```
How well did the course deliver what you most wanted from it?
```
**Options**
```
Completely
Mostly
Partly
Very little
Not at all
```

### Question 7

**Question**
```
Which part of the course was most valuable for your job?
```
**Options**
```
DevOps foundations, value streams and DORA metrics
Git, branching and pull requests
Continuous integration with GitHub Actions and Jenkins
Docker and Compose
Kubernetes
Terraform and Ansible
Continuous delivery: deployment strategies and rollback
DevSecOps: security gates and secrets
Observability: Prometheus, Grafana and SLOs
DevOps in a regulated bank: segregation of duties, change management and audit evidence
The capstone game day
```

### Question 8

**Question**
```
Which of these will you try first in your team, in the next 30 days?
```
**Options**
```
Start measuring our DORA metrics, such as lead time and deployment frequency
Turn on branch protection and required reviews
Add automated tests in CI to a repository
Containerise a service
Add security scanning for secrets, dependencies or images to a pipeline
Define an SLO and an alert for a service
Put an environment's infrastructure into code
Propose replacing a manual approval step with an automated control
Nothing yet: I need to agree it with my manager or team first
```

### Question 9

**Question**
```
What is most likely to get in the way of using what you learned?
```
**Options**
```
The change-approval process
Security or compliance sign-off
The tools aren't approved or available inside the bank
No time: delivery pressure comes first
My manager or team isn't bought in yet
Skills: I need more practice first
Legacy systems these practices don't fit
Another team owns the part that needs to change
Nothing: I can start straight away
```

### Question 10

**Question**
```
Would you recommend this course to a colleague?
```
**Options**
```
Definitely
Probably
Not sure
Probably not
Definitely not
```
