# -*- coding: utf-8 -*-
"""Day 1 — DevOps Foundations + Git Fundamentals.  Modules 1 and 2a."""
import diagrams as dg

DAY1 = [
 ('title', 1, 'DevOps Foundations',
  'Why DevOps exists, what it actually is, and how work really flows',
  ['Module 1 — DevOps culture, CALMS, the lifecycle, value streams',
   'Module 2a — Git fundamentals: the object model and the four areas',
   'Labs 00–02 — Toolchain · Value stream map · Your first repository'],
  'PayTrack API — the card-authorisation service you will carry for six days'),

 ('bullets', 'What today gives you',
  [('DevOps defined precisely — and distinguished from the tooling',
    'You will be able to answer "are we doing DevOps?" with evidence rather than a tool list'),
   ('The CALMS framework as a diagnostic you can score your own team against', None),
   ('Value stream mapping — where your delivery time ACTUALLY goes',
    'Most teams discover 90 %+ of lead time is queue time, not work'),
   ('The DORA metrics, and why speed and stability are not a trade-off', None),
   ('Git\'s object model — so every command stops being magic', None),
   ('A working Ubuntu toolchain and your first repository', None)],
  'TODAY', {'speaker': 'Set expectations: today is the only day that is mostly conceptual. '
            'Everything after this is hands-on. But the value-stream map in Lab 01 is what '
            'justifies every automation decision for the rest of the week.'}),

 ('section', '1', 'DevOps Foundations', 'Culture, principles and the shape of the work',
  ['What DevOps is, and what it is not', 'CALMS', 'The lifecycle',
   'Value stream management', 'DORA metrics']),

 ('define', 'DevOps',
  'A set of cultural philosophies, practices and tools that increases an organisation\'s '
  'ability to deliver applications and services at high velocity — by removing the barriers '
  'between development and operations.',
  [('It is primarily about CULTURE and INCENTIVES', 'Tools follow; they do not lead'),
   ('The unit of ownership is the SERVICE, not the phase', '"You build it, you run it"'),
   ('Success is measured in OUTCOMES', 'Lead time, failure rate, recovery time — not tool adoption'),
   ('It is a continuous practice, not a project with an end date', None)],
  'MODULE 1',
  ('WATCH FOR', 'If the answer to "are we doing DevOps?" is a list of tools, the answer is no. '
   'Ask instead: who carries the pager for the code your developers write?')),

 ('diagram', 'The problem DevOps was invented to solve', dg.wall_of_confusion, 'THE WALL',
  {'speaker': 'Ask the room: when production last broke, what was the FIRST question asked? '
   '"What changed?" is a healthy culture. "Who did it?" is the wall, still standing.'}),

 ('bullets', 'The core principles',
  [('Systems thinking', 'Optimise the whole flow, never one department\'s local efficiency'),
   ('Amplify feedback loops', 'Shorten the distance between an action and knowing its effect'),
   ('Culture of continual experimentation and learning', 'Failure is information you have already paid for'),
   ('Shared ownership and shared incentives', 'Dev and Ops succeed or fail on the same numbers'),
   ('Automate everything repeatable', 'Humans do judgement; machines do repetition'),
   ('Small batches, flowing continuously', 'Batch size is the strongest predictor of change failure')],
  'THE THREE WAYS + PRACTICE'),

 ('diagram', 'CALMS — the diagnostic framework', dg.calms, 'MODULE 1 §1.4'),

 ('diagram', 'The DevOps lifecycle', dg.lifecycle, 'MODULE 1 §1.5'),

 ('two', 'Agile and DevOps are not the same thing',
  ('AGILE', ['Optimises: idea → working software',
             'Unit: the iteration / sprint',
             'Ends at "done" — often at the deployment boundary',
             'Answers: are we building the right thing?'], 'teal'),
  ('DEVOPS', ['Optimises: working software → running in production → feedback',
              'Unit: the change',
              'Includes operating the thing you built',
              'Answers: can we deliver it safely, repeatedly, fast?'], 'green'),
  'MODULE 1 §1.3',
  ('THE TRAP', 'A team can be perfectly Agile and still take six weeks to deploy. Agile without '
   'DevOps produces a fast-moving development team feeding a slow, manual delivery pipeline — '
   'and the sprint review demo that nobody can actually use.')),

 ('define', 'Value stream',
  'The complete sequence of activities required to deliver a change from initial request to '
  'running in production and delivering value to a user — including every queue, hand-off and '
  'approval between them.',
  [('PROCESS TIME (PT)', 'Hands-on-keyboard time actually spent working the item'),
   ('WAIT TIME (WT)', 'Time the item sits in a queue between steps — where the surprises live'),
   ('%C/A', 'Percentage arriving complete and accurate, needing no rework'),
   ('FLOW EFFICIENCY = ΣPT ÷ Lead Time', 'Typical unimproved enterprise: 5–15 %')],
  'MODULE 1 §1.6'),


 ('predict', 'Before we look at the numbers',
  'A typical enterprise change takes 340 hours of lead time. Of those 340 hours, how many do '
  'you think anyone is actually WORKING on the change?',
  ['Write your guess down now — a single number, in hours.',
   'Then write what you think the biggest single queue is in YOUR process.',
   'We will compare against real data, and against your own map in Lab 01.'],
  'About 22 hours. Flow efficiency of 6.5 %. For 93.5 % of its life the change was sitting in '
  'a queue — which is why buying faster build servers changes almost nothing.', 3),
 ('diagram', 'Where delivery time actually goes', dg.flow_efficiency, 'VALUE STREAM MAPPING',
  {'speaker': 'This is the single most important slide of day 1. Let the 6.5 % sit in silence '
   'for a moment before moving on. Then: "in Lab 01 you will calculate your own number."'}),

 ('bank', 'Mapping a value stream in a bank',
  [('The engineering steps are rarely the constraint',
    'Coding and testing are usually 10–20 % of lead time; the queues are the rest'),
   ('Record the DEADLINE effects, not just the durations',
    '"CAB meets Thursday, submissions close Tuesday" means a change ready on Wednesday waits six days'),
   ('Bank-specific steps that belong on your map',
    'Risk assessment · architecture review · InfoSec sign-off · DPIA · vendor approval · '
    'pen-test slot · CAB · release window · business sign-off'),
   ('Map an ORDINARY change, not the heroic one',
    'And avoid core banking or a vendor package release for your first map — different economics')],
  {'lead': 'The objection you will hear is "we are regulated, so it has to take this long." '
           'The map is how you find out which parts of the delay are the regulation and which '
           'parts are habit wearing the regulation\'s uniform.',
   'ref': 'Appendix A §A.1 · Lab 01'}),


 ('myth', 'Four things everyone says about DevOps',
  [('DevOps means developers do operations.',
    'It means ONE team owns building AND running the service — supported by a platform team.'),
   ('We already do DevOps — we have Jenkins and Kubernetes.',
    'Tools are the easy part. If lead time has not moved, nothing has changed.'),
   ('We are regulated, so we cannot deploy frequently.',
    'Regulation demands evidenced control, not slow delivery. Small changes are EASIER to evidence.'),
   ('Moving faster means breaking more things.',
    'DORA has measured the opposite for a decade: elite performers are faster AND more stable.')]),
 ('define', 'Deploy ≠ Release',
  'DEPLOY is a technical event: place version 2.1 onto the infrastructure. '
  'RELEASE is a business decision: make 2.1\'s behaviour visible to users. '
  'Separating them is what lets you deploy twenty times a day and release on a business schedule.',
  [('Feature flags', 'The code ships dormant; a toggle enables it. The fastest rollback that exists'),
   ('Dark launching', 'The new path runs; its output is discarded'),
   ('Canary / traffic weighting', 'A defined percentage sees the new behaviour'),
   ('Blue-green', 'Deployed, warm and tested — but receiving no traffic yet')],
  'MODULE 1 §1.2',
  ('WHY IT MATTERS HERE', 'In a bank this is how a risk threshold changes without a code release — '
   'PayTrack\'s referral limit is configuration, so Risk can move it in minutes, not in a release cycle.')),

 ('diagram', 'The four DORA metrics', dg.dora_quadrant, 'MODULE 9 §9.2 — INTRODUCED TODAY',
  {'speaker': 'Introduce them now so delegates can estimate their baseline in Lab 01, and revisit '
   'properly on day 6. Stress: never rank teams with these.'}),

 ('two', 'Using DORA metrics well — and the ways teams ruin them',
  ('USE THEM FOR', ['✔ Trending ONE team over time',
                    '✔ Finding the constraint in your own flow',
                    '✔ Making improvement visible to leadership',
                    '✔ Always reporting speed WITH stability'], 'green'),
  ('NEVER', ['✗ Ranking teams against each other',
             '✗ Making deployment frequency a target (Goodhart\'s Law)',
             '✗ Measuring individuals',
             '✗ Reporting speed alone'], 'red'),
  'MODULE 9 §9.2',
  ('GOODHART\'S LAW', '"When a measure becomes a target, it ceases to be a good measure." '
   'Set deployment frequency as a target and teams will split one change into ten deploys and learn nothing.')),

 ('table', 'Common DevOps anti-patterns — score yourself honestly',
  ['Anti-pattern', 'What it looks like', 'First step out'],
  [['DevOps team as a silo', 'A third team between Dev and Ops', 'Stream-aligned teams + a platform team'],
   ['DevOps = tools', 'Big licence spend, unchanged lead time', 'Change the metrics and the incentives'],
   ['Automating a broken process', 'Faster chaos, same outcomes', 'Map the value stream first'],
   ['No tested rollback', '"We\'ll fix forward" — said during an outage', 'Rehearse one this week'],
   ['Long-lived branches', 'Merge hell every sprint', 'Trunk-based + feature flags'],
   ['Change freezes', 'Batched risk at the least-staffed time', 'Risk-proportionate freezing'],
   ['Hero culture', 'One person fixes everything', 'Runbooks, shared on-call, blamelessness']],
  'MODULE 9 §9.7', {'widths': [2.2, 3.0, 3.0]}),


 ('audit', 'Score your own organisation — now, before Lab 01',
  'Give each CALMS dimension a mark out of 5. Be honest: this only works if the number is real.',
  ['CULTURE — when production last broke, what was the FIRST question asked in the room?',
   'AUTOMATION — how many humans must type something for a one-line change to reach production?',
   'LEAN — what percentage of your lead time is queue time? (If you do not know: that is a 1.)',
   'MEASUREMENT — what is your change failure rate? If nobody knows, that IS the answer.',
   'SHARING — can another team find and read your last incident review?'],
  'Your LOWEST score is where the next investment belongs — not the dimension you find most '
  'interesting. Most rooms score highest on Automation and lowest on Measurement.', 4),
 ('lab', '00 + 01', 'Workstation Setup · Value Stream Mapping',
  'Get a verified toolchain, then map how a change really travels through YOUR organisation.',
  ['Install and verify the full six-day toolchain on Ubuntu 24.04 (Lab 00)',
   'Choose one real, ordinary change your team shipped recently',
   'Walk the stream BACKWARDS — from production to the original request',
   'Record process time, wait time and %C/A for every step',
   'Calculate flow efficiency and rolled %C/A, and name the constraint'],
  'docs/value-stream.md and calms-assessment.md — the baseline you revisit in the day-6 capstone'),

 ('section', '2', 'Version Control', 'Git\'s object model, and the four areas',
  ['Why version control is the foundation', 'Blobs, trees, commits, tags',
   'Working tree · index · repository · remote', 'Undo, safely']),

 ('bullets', 'Version control is the foundation of everything else',
  [('CI has nothing to integrate without it', None),
   ('Infrastructure as Code is just code — it needs the same history and review', None),
   ('GitOps makes the repository the SOURCE OF TRUTH for production', None),
   ('The commit graph is tamper-evident',
    'Which is why, in a bank, it is admissible change evidence'),
   ('Every control you build this week hangs off the pull request',
    'Segregation of duties, testing evidence, security gates — all of it')],
  'MODULE 2 §2.1'),

 ('diagram', 'Git\'s four areas and four object types', dg.git_areas, 'MODULE 2 §2.2–2.3'),

 ('define', 'Commit',
  'An immutable, content-addressed snapshot: a tree hash, zero or more parent commits, an author '
  'and committer with timestamps, and a message. Its identity is the hash of all of that.',
  [('Immutable', 'You never change a commit — you create a new one. "Amending" makes a new object'),
   ('Content-addressed', 'Change one byte and every hash from that point forward changes'),
   ('Parents make it a DAG', 'A merge commit has two parents; that is the whole of branching'),
   ('The message is the only record of WHY', 'The diff already shows what changed')],
  'MODULE 2 §2.2'),

 ('table', 'Undo — choose by what has already happened',
  ['Situation', 'Command', 'Destructive?'],
  [['Discard unstaged edits to a file', 'git restore <file>', '✗ Yes — unrecoverable'],
   ['Unstage a file, keep the edits', 'git restore --staged <file>', 'No'],
   ['Fix the last commit (UNPUSHED only)', 'git commit --amend', 'Rewrites history'],
   ['Undo a commit that is already PUSHED', 'git revert <sha>', '✔ No — safe on shared branches'],
   ['Move the branch back (UNPUSHED only)', 'git reset --hard <sha>', '✗ Yes'],
   ['Park work temporarily', 'git stash push / pop', 'No'],
   ['Recover a "lost" commit', 'git reflog → git checkout <sha>', 'No — your safety net']],
  'MODULE 2 §2.2',
  {'widths': [3.0, 2.6, 1.8], 'emph': [3],
   'note': ('THE RULE THAT SAVES CAREERS',
            'revert ADDS a commit that undoes a change — history is preserved and every clone stays '
            'consistent. reset MOVES the branch pointer, discarding commits — it rewrites history and '
            'needs a force-push. Never reset a branch other people have.')}),

 ('bullets', 'Commit messages are a professional skill',
  [('Conventional Commits: type: subject', 'feat · fix · docs · test · refactor · chore · ci · build · perf'),
   ('Subject: imperative, ≤ 50 characters, no full stop', '"add readiness probe", not "added readiness probe."'),
   ('Blank line, then a body explaining WHY', 'The diff shows what; only you can record why'),
   ('Reference the ticket', 'PAY-142 — this is how a change links to its authorisation'),
   ('feat! or BREAKING CHANGE: marks an incompatible change', None),
   ('The payoff is automatic release notes — and a readable git log', None)],
  'MODULE 2 §2.2',
  ('IN A BANK', 'The commit message plus the PR approval IS your change record. Generated, timestamped '
   'and immutable — no ticket typed by hand after the fact.')),

 ('lab', '02', 'Git Fundamentals',
  'Turn a directory into a repository containing PayTrack API, with a clean, meaningful history.',
  ['git init, and look inside .git to see the object database',
   'Bring in the PayTrack API source and RUN IT before committing it — never commit code you have not run',
   'Write .gitignore BEFORE the first commit (secrets, .venv, tfstate)',
   'Stage selectively, review git diff --staged, and write two properly-scoped commits',
   'Practise all three undos: restore, restore --staged, and revert',
   'Tag an annotated release'],
  'A local repository with four commits, an annotated tag, and a tested Flask application'),

 ('bank', 'What PayTrack API teaches before you write a line of code',
  [('Money is an integer in MINOR units', 'amount_minor: 4599 is £45.99. 0.1 + 0.2 ≠ 0.3 in binary floating point'),
   ('A full card number is REFUSED at the API edge', 'Accepting it would pull the service, its logs, replicas and backups into PCI-DSS scope'),
   ('Only the last four digits are stored', 'Not sensitive on their own'),
   ('No customer identifier reaches the logs', 'Logs are widely readable and long-retained'),
   ('The referral limit is configuration, not code', 'Risk can change a threshold without a release')],
  {'lead': 'Scope is something you design OUT at the API boundary — not something you secure '
           'afterwards.',
   'ref': 'Appendix A §A.6 · app/src/app.py'}),

 ('check', 'Day 1 — check your understanding',
  ['Your organisation has Jenkins, Docker and Kubernetes, yet a one-line change takes six weeks. '
   'Which CALMS dimension is your constraint, and how would you prove it?',
   'Team A deploys 40× a day with a 30 % change failure rate. Team B deploys weekly with 2 %. '
   'Who is better — and what else do you need to know?',
   'A change takes 22 hours of work and 340 hours of lead time. What is the flow efficiency, '
   'and where should the investment go?',
   'Explain the difference between deploy and release, and name three techniques that separate them.',
   'Your teammate says they will "just reset main back to yesterday". What do you say?']),

 ('close', 1, 'Day 1 complete',
  ['A verified Ubuntu 24.04 toolchain for the whole week',
   'Your own value stream map, flow efficiency and CALMS baseline',
   'A git repository containing PayTrack API, with a clean history and an annotated tag',
   'The vocabulary: CALMS, value stream, flow efficiency, DORA, deploy vs release'],
  'Day 2 takes that repository to GitHub and makes it a TEAM artefact: branch protection, pull '
  'requests, a deliberate merge conflict — and the moment you see the whole room\'s branches in '
  'one picture. Then we make it impossible to merge a broken change.'),
]
