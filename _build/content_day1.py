# -*- coding: utf-8 -*-
"""Day 1 — DevOps Foundations + Git Fundamentals.  Modules 1 and 2a.

Theory-first edition: the session is mostly theory with exercises and one live demo;
the labs are started together at the end and finished after class.
"""
import diagrams as dg

DAY1 = [
 ('title', 1, 'DevOps Foundations',
  'Why DevOps exists, what it actually is, and how work really flows',
  ['Module 1 — definition, culture, CALMS, the lifecycle, value streams, DORA',
   'Module 2a — Git fundamentals: the object model, the four areas, undo',
   'After class — Labs 00–02: toolchain · your own value stream map · first repository'],
  'PayTrack API — the card-authorisation service you will carry for six days'),

 ('agenda', 'Day 1 at a glance',
  [('theory', 'How the six days run · what DevOps is · the wall · the Three Ways'),
   ('theory', 'Culture, Westrum, blameless reviews · principles · CALMS'),
   ('exercise', 'COMPARE — rewrite a post-mortem finding  ·  AUDIT — score your CALMS'),
   ('theory', 'Agile vs DevOps · the lifecycle · deploy is not release'),
   ('break', 'Break · 15 minutes'),
   ('theory', 'Flow: value streams, flow efficiency, Little\'s Law, the constraint'),
   ('exercise', 'PREDICT — where does the time go, and where is the constraint?'),
   ('theory', 'DORA metrics · team topologies · anti-patterns · the toolchain'),
   ('demo', 'Git fundamentals — look inside .git, the four areas, undo safely'),
   ('practical', 'Start Lab 00 and Lab 02 together, then check your understanding'),
   ('after', 'Finish Labs 00–02 · Lab 01 maps YOUR organisation\'s value stream')],
  'TODAY', {'speaker': 'Say how the week works before anything else: each day is mostly theory with '
            'exercises and a live demo; the last half hour starts the labs together; the labs are '
            'finished after class. Every lab has a RECOVER block, so nobody is ever permanently behind.'}),

 ('bullets', 'What today gives you',
  [('DevOps defined precisely — and distinguished from the tooling',
    'You will be able to answer "are we doing DevOps?" with evidence rather than a tool list'),
   ('Culture you can actually change', 'The three levers, Westrum\'s typology, and blameless reviews'),
   ('The CALMS framework as a diagnostic you can score your own team against', None),
   ('Value stream mapping — where your delivery time ACTUALLY goes',
    'Most teams discover that 85–95 % of lead time is queue time, not work'),
   ('The DORA metrics, and why speed and stability are not a trade-off', None),
   ('Git\'s object model — so every command stops being magic', None)],
  'TODAY', {'speaker': 'Day 1 is the most conceptual day, and everything later rests on it. The '
            'value-stream map in Lab 01 is what justifies every automation decision for the rest of the week.'}),

 ('flow', 'Six days, one thread — PayTrack API',
  [('Day 1 · Foundations and Git', 'A value stream map of YOUR organisation, and a repository containing PayTrack API'),
   ('Day 2 · Branching, pull requests, CI', 'A protected GitHub repository where a broken change cannot be merged'),
   ('Day 3 · Containers', 'A hardened multi-stage image in a registry, and a full local stack with Compose'),
   ('Day 4 · Kubernetes', 'PayTrack on a 3-node cluster: probes, config, secrets, storage, ingress, autoscaling'),
   ('Day 5 · Infrastructure as code and delivery', 'Terraform and Ansible, a GitOps pipeline, blue-green, canary, rollback'),
   ('Day 6 · DevSecOps, observability, enterprise', 'Security gates, SLO alerts, an injected incident, your 30-60-90 plan')],
  'HOW THE COURSE FITS TOGETHER',
  {'note': ('THE RULE', 'Each lab consumes what the previous lab produced. If you fall behind, every lab '
            'README has a RECOVER block that puts you back on the thread in a few commands.'),
   'speaker': 'PayTrack API is a card-authorisation service: small enough to understand in ten minutes, '
              'realistic enough to carry the banking arguments — PCI scope, money as integers, audit evidence.'}),

 ('section', '1', 'What DevOps Is', 'A definition you can defend, and the problem it solves',
  ['The definition, clause by clause', 'The wall of confusion', 'What DevOps is not',
   'The Three Ways']),

 ('define', 'DevOps',
  'A set of cultural practices, engineering practices and tools that shortens the time between '
  'committing a change to a system and that change being placed into normal production, while '
  'ensuring high quality.',
  [('Bass, Weber and Zhu, 2015', 'The most useful definition in circulation, because every clause is testable'),
   ('It names no tool, no cloud, no container, no job title', 'Those are implementation details'),
   ('The clock starts at COMMIT and stops at PRODUCTION', 'Not at "dev complete", and not at "passed QA"'),
   ('Success is measured in OUTCOMES', 'Lead time, failure rate, recovery time — never tool adoption')],
  'MODULE 1 §1.1',
  ('WATCH FOR', 'If the answer to "are we doing DevOps?" is a list of tools, the answer is no. '
   'Ask instead: who carries the pager for the code your developers write?')),

 ('table', 'The definition, clause by clause',
  ['Clause', 'Why it is there', 'How you measure it'],
  [['"cultural practices … and tools"', 'Tools without cultural change produce automated dysfunction',
    'Team shape, incentives, on-call rota'],
   ['"shortens the time"', 'The objective is FLOW, not automation for its own sake', 'Lead time for change'],
   ['"committing a change … into production"', 'The clock runs commit → production, nothing shorter',
    'Commit timestamp → deploy timestamp'],
   ['"normal production"', 'The routine path — not a heroic weekend release', 'Deployment frequency'],
   ['"high quality"', 'Speed without stability is a faster way to break things',
    'Change failure rate, recovery time']],
  'MODULE 1 §1.1', {'widths': [2.9, 3.9, 2.8],
   'speaker': 'Every clause maps to one of the four DORA metrics you will meet later today. That is '
              'why this definition is worth learning word for word: it tells you what to measure.'}),

 ('diagram', 'The problem DevOps was invented to solve', dg.wall_of_confusion, 'THE WALL',
  {'speaker': 'Development is rewarded for change, operations for the absence of change — then both are '
   'asked to cooperate. It is a system problem, not a people problem. The name comes from DevOpsDays, '
   'Ghent, October 2009, prompted by the Flickr talk "10+ Deploys Per Day". Ask the room: when '
   'production last broke, what was the FIRST question asked?'}),

 ('myth', 'What DevOps is not',
  [('DevOps is a job title.',
    'It is a way of working. A separate "DevOps team" between Dev and Ops is a third silo.'),
   ('DevOps means no operations.',
    'Operational concerns become SHARED; ops specialists build the platform that makes that possible.'),
   ('DevOps is CI/CD tooling.',
    'CI/CD is a practice it depends on. A Jenkins server can still take six weeks to ship one line.'),
   ('DevOps means deploying 100 times a day.',
    'Frequency is an indicator, not a target. Weekly with a 0.5 % failure rate can be excellent.'),
   ('DevOps means no process or documentation.',
    'It means LIGHT, AUTOMATED, ENFORCED process instead of heavy, manual, ignored process.')],
  'MODULE 1 §1.1'),

 ('diagram', 'The Three Ways', dg.three_ways, 'MODULE 1 §1.1 — GENE KIM',
  {'speaker': 'The order matters. You cannot get feedback from a system that releases twice a year — no '
   'Flow, no Feedback. And you cannot learn from feedback you never collect. An organisation that jumps '
   'to chaos engineering while its lead time is measured in months is optimising the wrong thing.'}),

 ('section', '2', 'Culture, Principles & CALMS', 'The part that decides whether any tool helps',
  ['Culture, defined', 'Westrum\'s three cultures', 'Blameless post-mortems',
   'The core principles', 'CALMS as a diagnostic']),

 ('define', 'Culture',
  'The set of behaviours that the organisation\'s incentives, structures and rituals actually reward — '
  'as opposed to the behaviours its value statements claim to reward.',
  [('Lever 1 — change the METRIC',
    'Measure teams on story points and they optimise story points. Measure lead time and failure rate instead'),
   ('Lever 2 — change who carries the PAGER',
    '"You build it, you run it." Developers woken at 03:00 by their own code write observable, resilient code'),
   ('Lever 3 — change what is EASY',
    'If the compliant path is also the fastest path, people take it. That is the whole thesis of platform engineering')],
  'MODULE 1 §1.2',
  ('YOU CANNOT WORKSHOP IT', 'Culture changes when what gets rewarded and what gets made easy changes. '
   'A values poster changes nothing.')),

 ('table', 'Westrum\'s three cultures — and which one predicts performance',
  ['', 'Pathological (power)', 'Bureaucratic (rules)', 'Generative (performance)'],
  [['Cooperation', 'Low', 'Modest', '✔ High'],
   ['Messengers', 'Shot', 'Neglected', '✔ Trained'],
   ['Responsibilities', 'Shirked', 'Narrow', '✔ Shared'],
   ['Bridging between teams', 'Discouraged', 'Tolerated', '✔ Encouraged'],
   ['Failure leads to', 'Scapegoating', 'Justice-seeking', '✔ Inquiry'],
   ['Novelty', 'Crushed', 'Problematic', '✔ Implemented']],
  'MODULE 1 §1.2', {'widths': [2.3, 2.4, 2.4, 2.6],
   'note': ('WHY IT MATTERS', 'DORA research found Westrum\'s typology PREDICTIVE of software delivery '
            'performance. Culture is not the soft part of DevOps — it is a measurable input.'),
   'speaker': 'Most large banks are bureaucratic, and that is fine as a starting point: rules can be '
              'changed. Ask which row the room recognises most — "messengers neglected" is a common answer.'}),

 ('define', 'Blameless post-mortem',
  'An incident review that assumes every person acted rationally given the information they had at '
  'the time, and asks what about the SYSTEM made the failure possible.',
  [('Psychological safety (Amy Edmondson)',
    'A shared belief that the team is safe for interpersonal risk — you can say "I broke production"'),
   ('Blame produces silence', 'People hide near-misses, and the next incident arrives with no warning'),
   ('Counterfactuals are banned', '"Ahmed should have checked the config" is not a finding'),
   ('Findings become backlog items', 'A review with no change to the system was a meeting, not a review'),
   ('Publish them organisation-wide', 'A lesson that stays in one team is a local optimum')],
  'MODULE 1 §1.2'),

 ('compare', 'Rewrite the finding',
  'A payment batch failed at 02:10 because a configuration change set the settlement cut-off to 25:00. '
  'The draft post-mortem says: "Ahmed should have checked the config before deploying." '
  'Rewrite that finding so it is blameless AND leads to a change in the system.',
  ['Two minutes in pairs. Your finding must not contain a person\'s name.',
   'It must name something about the system that allowed the failure.',
   'Then name one concrete action that would make the same mistake impossible next time.'],
  'A good rewrite: "The deployment tool accepted a configuration value that could not possibly be valid, '
  'and nothing validated it before production." The actions follow from it — schema-validate config in CI, '
  'and fail the pipeline on an impossible time. The next person cannot make the mistake at all.', 3),

 ('table', 'The core principles',
  ['Principle', 'Meaning', 'What it looks like'],
  [['Shared responsibility', 'One team owns the service from idea to retirement', 'Devs on call; ops in planning'],
   ['Small batch size', 'Reduce the size of each change', 'Trunk-based, PRs under 400 lines'],
   ['Automate the repeatable', 'Humans do judgement; machines do repetition', 'CI, IaC, auto-rollback'],
   ['Everything as code', 'Infra, config, pipelines, policy, dashboards in git', 'terraform/, .github/workflows/'],
   ['Fail fast, recover faster', 'Optimise recovery time over time-between-failures', 'Feature flags, canaries'],
   ['Measure everything', 'Decisions from telemetry, not opinion', 'DORA metrics, SLOs'],
   ['Continuous improvement', 'Improvement work is real work', 'Improvement items in the backlog']],
  'MODULE 1 §1.2', {'widths': [2.4, 3.8, 3.2]}),

 ('diagram', 'CALMS — the diagnostic framework', dg.calms, 'MODULE 1 §1.3',
  {'speaker': 'Coined by Damon Edwards and John Willis; Jez Humble added the M. Use it as an assessment, '
   'not a checklist: score each dimension and attack the lowest.'}),

 ('table', 'CALMS, dimension by dimension',
  ['Dimension', 'What you are looking for', 'The diagnostic question'],
  [['Culture', 'Shared goals; failure investigated, not punished',
    'When production last broke, what was the FIRST question asked?'],
   ['Automation', 'build → test → deploy → provision → configure → recover',
    'How many humans must type something for a one-line change to ship?'],
   ['Lean', 'Small batches, limited WIP, the seven wastes removed',
    'What share of lead time does a change spend waiting for a human?'],
   ['Measurement', 'Outcomes (lead time, failure rate), not outputs (tickets)',
    'What is your change failure rate? If nobody knows, that is the answer'],
   ['Sharing', 'Runbooks, dashboards and post-mortems discoverable by all',
    'Can another team find and read your last incident review?']],
  'MODULE 1 §1.3', {'widths': [1.8, 3.8, 4.1],
   'note': ('SCORING', '1 Initial (heroic, undocumented) · 2 Repeatable (documented, manual) · 3 Defined '
            '(standardised, partly automated) · 4 Managed (automated and measured) · 5 Optimising (self-service, data-driven)')}),

 ('audit', 'Score your own organisation',
  'Give each CALMS dimension a mark out of 5, using the scale on the previous slide. '
  'Be honest: this only works if the number is real.',
  ['CULTURE — when production last broke, what was the FIRST question asked in the room?',
   'AUTOMATION — how many humans must type something for a one-line change to reach production?',
   'LEAN — what percentage of your lead time is queue time? (If you do not know: that is a 1.)',
   'MEASUREMENT — what is your change failure rate? If nobody knows, that IS the answer.',
   'SHARING — can another team find and read your last incident review?'],
  'Your LOWEST score is where the next investment belongs — not the dimension you find most '
  'interesting. Most rooms score highest on Automation and lowest on Measurement. Keep your scores: '
  'Lab 01 records them, and the day 6 capstone asks you to score again.', 4),

 ('section', '3', 'Agile, the Lifecycle & Release', 'Where DevOps starts and where Agile stops',
  ['Agile vs DevOps', 'Water-scrum-fall', 'The lifecycle, phase by phase', 'Deploy is not release']),

 ('two', 'Agile and DevOps are not the same thing',
  ('AGILE', ['Optimises: idea → working software',
             'Unit: the iteration / sprint',
             'Ends at "done" — often at the deployment boundary',
             'Answers: are we building the right thing?'], 'teal'),
  ('DEVOPS', ['Optimises: working software → running in production → feedback',
              'Unit: the change',
              'Includes operating the thing you built',
              'Answers: can we deliver it safely, repeatedly, fast?'], 'green'),
  'MODULE 1 §1.4',
  ('THE TRAP', 'A team can be perfectly Agile and still take six weeks to deploy. Agile without '
   'DevOps produces a fast-moving development team feeding a slow, manual delivery pipeline.')),

 ('table', 'Agile and DevOps, side by side',
  ['', 'Agile', 'DevOps'],
  [['Origin', 'Agile Manifesto, 2001', 'DevOpsDays, 2009'],
   ['Primary concern', 'Building the right thing, iteratively', 'Delivering and running it, reliably and fast'],
   ['Scope', 'Dev team + product owner', 'Dev + Ops + Security + the platform'],
   ['Batch', 'Sprint (1–4 weeks)', 'Individual change (minutes to hours)'],
   ['Feedback source', 'Sprint review, customer demo', 'Production telemetry, real users'],
   ['Key artefact', 'Working software at the end of a sprint', 'Working software IN PRODUCTION, continuously'],
   ['Fails when', 'The increment is never actually released', 'Culture is unchanged and only tools are bought']],
  'MODULE 1 §1.4', {'widths': [2.0, 3.8, 3.9],
   'note': ('WATER-SCRUM-FALL', 'Two-week sprints producing increments that queue for a quarterly release: '
            'Agile at the front, waterfall at the back, lead time unchanged. Lean sits upstream of both.')}),

 ('diagram', 'The DevOps lifecycle', dg.lifecycle, 'MODULE 1 §1.5',
  {'speaker': 'The infinity loop is useful as long as you remember that real systems run MANY loops at '
   'different speeds, not one. The next slide says what good looks like in each phase.'}),

 ('table', 'The lifecycle, phase by phase',
  ['Phase', 'What "good" looks like', 'Where you build it'],
  [['Plan', 'WIP limits; work visible on one board; slices under 2 days', 'Lab 01'],
   ['Code', 'Short-lived branches; PR reviewed within 24 hours', 'Git, GitHub — Labs 02–03'],
   ['Build', 'One build per commit; the artefact is built ONCE and promoted', 'Actions, Jenkins, Docker — 04–06'],
   ['Test', 'Test pyramid; suite under 10 minutes; no manual regression gate', 'pytest, Trivy — 04, 17'],
   ['Release', 'A business decision, decoupled from deploying', 'GHCR, tags — 06, 15'],
   ['Deploy', 'Automated, repeatable, reversible in one command', 'Kubernetes, GitOps — 10, 15, 16'],
   ['Operate', 'Runbooks as code; toil measured and reduced', 'Terraform, Ansible — 13, 14'],
   ['Monitor', 'SLOs; alerts on symptoms; dashboards as code', 'Prometheus, Grafana — 18'],
   ['Learn', 'Blameless reviews; findings become backlog items', 'Capstone debrief — 19']],
  'MODULE 1 §1.5', {'widths': [1.4, 5.3, 3.3]}),

 ('define', 'Deploy ≠ Release',
  'DEPLOY is a technical event: place version 2.1 onto the infrastructure. '
  'RELEASE is a business decision: make 2.1\'s behaviour visible to users. '
  'Separating them is what lets you deploy twenty times a day and release on a business schedule.',
  [('Feature flags', 'The code ships dormant; a toggle enables it. The fastest rollback that exists'),
   ('Dark launching', 'The new path runs; its output is discarded'),
   ('Canary / traffic weighting', 'A defined percentage sees the new behaviour'),
   ('Blue-green', 'Deployed, warm and tested — but receiving no traffic yet')],
  'MODULE 1 §1.5',
  {'speaker': 'In a bank this is how a risk threshold changes without a code release — PayTrack\'s '
   'referral limit is configuration, so Risk can move it in minutes. Delegates build all four techniques in Lab 16.'}),

 ('section', '4', 'Flow & Value Streams', 'Where delivery time actually goes',
  ['Value stream, lead time, flow efficiency', 'A worked value stream map',
   'Little\'s Law', 'The Theory of Constraints']),

 ('define', 'Value stream',
  'The complete sequence of activities required to deliver a change from initial request to '
  'running in production and delivering value to a user — including every queue, hand-off and '
  'approval between them.',
  [('PROCESS TIME (PT)', 'Hands-on-keyboard time actually spent working the item'),
   ('WAIT TIME (WT)', 'Time the item sits in a queue between steps — where the surprises live'),
   ('%C/A', 'Percentage arriving complete and accurate, needing no rework'),
   ('FLOW EFFICIENCY = ΣPT ÷ Lead Time', 'Typical unimproved enterprise: 5–15 %')],
  'MODULE 1 §1.6'),

 ('table', 'Seven terms you must be able to state precisely',
  ['Term', 'Definition', 'Why it matters'],
  [['Lead time', 'Request accepted → value delivered, wall-clock', 'What the customer experiences'],
   ['Lead time for change', 'Commit → running in production', 'The DORA metric'],
   ['Process / cycle time', 'Time actually spent working the item in a step', 'Usually the small number'],
   ['Wait / queue time', 'Time the item sits idle between steps', 'Usually the big number'],
   ['Work in progress (WIP)', 'Items started but not finished', 'Drives lead time directly'],
   ['Rolled %C/A', 'The %C/A of every step multiplied together', 'Usually shockingly low'],
   ['Constraint', 'The step that limits throughput of the whole stream', 'The only place improvement counts']],
  'MODULE 1 §1.6', {'widths': [2.3, 4.2, 3.0]}),

 ('predict', 'Before we look at the numbers',
  'A typical enterprise change takes 340 hours of lead time. Of those 340 hours, how many do '
  'you think anyone is actually WORKING on the change?',
  ['Write your guess down now — a single number, in hours.',
   'Then write what you think the biggest single queue is in YOUR process.',
   'We will compare against real data, and against your own map in Lab 01.'],
  'About 22 hours. Flow efficiency of 6.5 %. For 93.5 % of its life the change was sitting in '
  'a queue — which is why buying faster build servers changes almost nothing.', 3),
 ('diagram', 'Where delivery time actually goes', dg.flow_efficiency, 'VALUE STREAM MAPPING',
  {'speaker': 'The single most important idea of day 1. Let the 6.5 % sit in silence for a moment. '
   'Then: "after class, in Lab 01, you will calculate your own number."'}),

 ('predict', 'Where is the constraint?',
  'A change passes through six steps. Wait times: backlog refinement 40 h · development 4 h · code review 26 h · '
  'QA testing 60 h · CAB approval 120 h · deployment 48 h. The team is certain the bottleneck is QA, '
  'because QA is where the pain is felt. Where is it really?',
  ['Pick the step you think limits the whole stream.',
   'Then decide: if the team spends a quarter automating tests, how much faster does a change ship?'],
  'The constraint is CAB approval — 120 hours of pure queue for 0.5 hours of work. Automating QA improves a '
  'step that is not the constraint, so lead time barely moves. The gap between the PERCEIVED and the '
  'ACTUAL bottleneck is the entire point of drawing the map.', 3),
 ('diagram', 'A worked value stream map', dg.vsm_example, 'MODULE 1 §1.6',
  {'speaker': 'Walk the arithmetic once, slowly: process 29.5 h, wait 298 h, lead 327.5 h — about eight '
   'working weeks. Flow efficiency 9 %. And the rolled %C/A: only a third of changes pass through '
   'without rework somewhere. That number is usually a bigger shock than flow efficiency.'}),

 ('define', 'Little\'s Law',
  'Lead Time = Work in Progress ÷ Throughput. At constant throughput, halving the work in progress '
  'halves the lead time.',
  [('A worked example', '30 items in progress, 3 finished per week → 10 weeks average lead time'),
   ('Cut WIP to 10, same people, same tools', '10 ÷ 3 → 3.3 weeks. A two-thirds cut in lead time'),
   ('Why it works', 'Every extra item in progress adds context-switching and waiting to all the others'),
   ('What it looks like in practice', 'WIP limits on the board; finish before you start; stop starting')],
  'MODULE 1 §1.6',
  ('THE MOST ACTIONABLE EQUATION IN DEVOPS', 'It needs no budget, no tool and no reorganisation — only '
   'the discipline to stop starting new work.')),

 ('flow', 'The Theory of Constraints — the improvement algorithm',
  [('IDENTIFY the constraint', 'The largest wait time, or the step where the queue keeps growing'),
   ('EXPLOIT it', 'Make sure the constraint is never idle and never doing non-constraint work'),
   ('SUBORDINATE everything else to it', 'Stop feeding it faster than it can consume'),
   ('ELEVATE it', 'Add capacity, automate it, or remove the step altogether'),
   ('REPEAT', 'The constraint always moves. Do not let inertia become the new one')],
  'MODULE 1 §1.6 — GOLDRATT',
  {'note': ('DORA\'S FINDING', 'Automated change approval outperforms external approval boards on BOTH '
            'speed and stability. A CAB is very often the constraint, and it provides no measurable risk reduction.')}),

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

 ('section', '5', 'Measurement & Teams', 'What to measure, and how to organise around it',
  ['The four DORA metrics', 'Team topologies', 'Anti-patterns', 'The toolchain']),

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

 ('table', 'Team topologies — the four shapes that work',
  ['Team type', 'Purpose', 'Example in a bank'],
  [['Stream-aligned', 'Owns a slice of the business end to end. The default — most teams',
    'The payments team owns payments code AND its production behaviour'],
   ['Platform', 'Builds internal products that reduce the load on stream-aligned teams',
    'Paved-road CI templates, the cluster, the observability stack'],
   ['Enabling', 'Coaches a team to acquire a capability, then leaves',
    'A test-automation coach embedded for six weeks'],
   ['Complicated-subsystem', 'Owns a component needing deep specialist knowledge',
    'The pricing or fraud-scoring model']],
  'MODULE 1 §1.7 — SKELTON & PAIS', {'widths': [2.2, 4.0, 3.8],
   'note': ('INTERACTION MODES', 'Collaboration (high-bandwidth, temporary, for discovery) · X-as-a-Service '
            '(low-bandwidth, predictable consumption) · Facilitating (one team helps another improve).')}),

 ('table', 'Common DevOps anti-patterns — score yourself honestly',
  ['Anti-pattern', 'What it looks like', 'First step out'],
  [['DevOps team as a third silo', 'A new wall between Dev and Ops, plus a translation layer', 'Stream-aligned teams + a platform team'],
   ['DevOps = tools', 'Big licence spend, unchanged lead time', 'Change the metrics and the incentives'],
   ['SRE as renamed Ops', 'Same team, same hand-off, new logo, no error budgets', 'Error budgets agreed with the business'],
   ['Automating a broken process', 'Faster chaos, same outcomes', 'Map the value stream first'],
   ['No tested rollback', '"We\'ll fix forward" — said during an outage', 'Rehearse one this week'],
   ['Change freezes', 'Batched risk at the least-staffed time', 'Risk-proportionate freezing'],
   ['Hero culture', 'One person fixes everything', 'Runbooks, shared on-call, blamelessness']],
  'MODULE 1 §1.7 · MODULE 9', {'widths': [2.5, 3.6, 3.2],
   'speaker': 'Ask each table to pick the one anti-pattern they recognise most. In a bank, change freezes '
              'and hero culture usually win. The practices that fix them: you build it you run it, shared '
              'on-call, one backlog, and a definition of done that includes operability.'}),

 ('myth', 'Four things you will hear in a bank',
  [('We are regulated, so we cannot deploy frequently.',
    'Regulation demands evidenced control, not slow delivery. Small changes are EASIER to evidence and roll back.'),
   ('Moving faster means breaking more things.',
    'DORA has measured the opposite for a decade: elite performers are faster AND more stable.'),
   ('The CAB is what keeps production safe.',
    'DORA found external approval boards slow delivery with no measurable stability benefit.'),
   ('Many small changes mean more risk than one big release.',
    'Risk scales with batch size. A small change has a small blast radius and is trivial to roll back.')],
  'MYTH vs REALITY', {'speaker': 'Do not argue these — ask for the evidence behind the left-hand column. '
                      'Appendix A §A.4 and §A.7 carry the full arguments on CABs and change freezes.'}),

 ('diagram', 'The toolchain, drawn as the pipeline you will build', dg.toolchain_pipeline, 'MODULE 1 §1.8'),

 ('bullets', 'Choosing tools — the four questions',
  [('Does it integrate with what we already run?', 'An orphan tool is a future migration'),
   ('Can it be driven from code and an API?', 'If it needs a human clicking a GUI, it cannot be part of a pipeline'),
   ('What is the total cost — licence PLUS the engineers to run it?',
    'Self-hosted is "free" until you cost the two people maintaining it'),
   ('Can we leave?', 'Export formats, open standards, and how much logic is trapped in a vendor\'s language'),
   ('Choose per CATEGORY first, vendor second', 'Plan · source · CI · registry · orchestration · IaC · security · monitoring')],
  'MODULE 1 §1.8'),

 ('lab', '00 + 01', 'Workstation Setup · Value Stream Mapping',
  'Get a verified toolchain, then map how a change really travels through YOUR organisation.',
  ['Install and verify the full six-day toolchain on Ubuntu 24.04 (Lab 00)',
   'Choose one real, ordinary change your team shipped recently',
   'Walk the stream BACKWARDS — from production to the original request',
   'Record process time, wait time and %C/A for every step',
   'Calculate flow efficiency and rolled %C/A, and name the constraint'],
  'docs/value-stream.md and calms-assessment.md — the baseline you revisit in the day-6 capstone',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('section', '6', 'Version Control & Git', 'The object model that makes every command make sense',
  ['Why version control comes first', 'Blobs, trees, commits, tags', 'Branches and HEAD',
   'The four areas', 'Undo, safely']),

 ('bullets', 'Version control is the foundation of everything else',
  [('A single source of truth', 'The answer to "what is running?" is a git SHA'),
   ('Auditability', 'Who changed what, when and why — cryptographically chained'),
   ('Reversibility', 'Any state can be recreated; rollback is git revert plus a redeploy'),
   ('A trigger', 'CI/CD is event-driven off repository events. No VCS, no pipeline'),
   ('Everything is a file', 'Code, pipelines, infrastructure, manifests, dashboards, alert rules, policy')],
  'MODULE 2 §2.1',
  {'note': ('WHY GIT WON', 'Centralised systems (Subversion, Perforce) keep history on one server; every Git '
            'clone is a full repository. Branching is cheap, history is tamper-evident, and almost every '
            'operation is local.')}),

 ('diagram', 'Git\'s four areas and four object types', dg.git_areas, 'MODULE 2 §2.2–2.3',
  {'speaker': 'The staging area is Git\'s most misunderstood feature and its best one: it lets you commit '
   'PART of your changes, so each commit is one logical change even when you worked on three things. '
   'git add -p is the command.'}),

 ('define', 'Commit',
  'An immutable, content-addressed snapshot: a tree hash, zero or more parent commits, an author '
  'and committer with timestamps, and a message. Its identity is the hash of all of that.',
  [('Immutable', 'You never change a commit — you create a new one. "Amending" makes a new object'),
   ('Content-addressed', 'Change one byte and every hash from that point forward changes'),
   ('Parents make it a DAG', 'A merge commit has two parents; that is the whole of branching'),
   ('The message is the only record of WHY', 'The diff already shows what changed')],
  'MODULE 2 §2.2'),

 ('define', 'Branch and HEAD',
  'A branch is a movable pointer to a commit — a 41-byte file in .git/refs/heads. HEAD is a pointer '
  'to the branch you are on. Neither contains any code.',
  [('Creating a branch is instant, whatever the repository size', 'It writes one small file. "Branching is expensive" is a Subversion-era belief'),
   ('History is a graph, not a line', 'A merge commit simply has two parents'),
   ('Rewriting is replacing', 'amend, rebase and cherry-pick create NEW commits — force-pushing a shared branch replaces commits others already have'),
   ('Detached HEAD', 'HEAD points at a commit instead of a branch; new commits belong to no branch. Fix: git switch -c <name>')],
  'MODULE 2 §2.2'),

 ('demo', 'Look inside .git',
  '''$ git init -q demo && cd demo
$ echo "PayTrack" > README.md && git add README.md
$ find .git/objects -type f
.git/objects/97/82e7e6e0e7bc940b7fcebae75dbeb9ab5a02eb
$ git cat-file -t 9782e7e
blob
$ git commit -qm "docs: add readme"
$ git cat-file -p HEAD
tree 3020aa2a9fead3fb23de9e11225eff5d0894ffd6
author Demo <demo@example.com> 1789491961 +0200

docs: add readme
$ cat .git/HEAD
ref: refs/heads/main
$ wc -c .git/refs/heads/main
41 .git/refs/heads/main''',
  [('git add already wrote an object', 'The blob exists before any commit — named by the hash of its content'),
   ('A blob has no filename', 'The name lives in the TREE that the commit points at'),
   ('HEAD names a branch', 'And the branch is a 41-byte file holding one commit hash'),
   ('Run it yourself', 'The same content gives the same blob hash on every machine in the room')],
  {'minutes': 6, 'speaker': 'Type it live; do not paste. The moment people see a branch is a 41-byte '
   'file, the fear of branching goes. Ask someone to predict the blob hash on their own laptop — it matches.'}),

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

 ('code', 'A commit message worth reading in two years',
  '''feat(api): add readiness endpoint for the ledger

/ready returns 503 until the database answers, so
Kubernetes stops sending traffic to a pod that cannot
serve it. /health stays dependency-free, so a database
blip never restarts the pod.

Refs: PAY-142''',
  [('type(scope): subject', 'feat, in the api — imperative, under 50 characters'),
   ('A blank line', 'Tools treat line 1 as the title and the rest as the body'),
   ('The body explains WHY', 'Wrapped at 72 characters; the diff already says what'),
   ('A footer links the authorisation', 'Refs: PAY-142 — or BREAKING CHANGE: for incompatible changes')],
  {'lang': 'git commit message', 'kicker': 'MODULE 2 §2.2', 'split': 0.56}),

 ('code', '.gitignore — written BEFORE the first commit',
  '''# Python
__pycache__/
.venv/
.pytest_cache/

# Secrets - never commit
.env
*.pem
*.key

# Terraform
.terraform/
*.tfstate
*.tfstate.*

# OS and editors
.DS_Store
.vscode/''',
  [('Secrets first', 'A secret committed once is in history forever — deleting it later does not remove it'),
   ('Terraform state holds secrets in plain text', 'It never belongs in git; it belongs in a locked remote backend'),
   ('Too late? Ignoring is not untracking', 'git rm --cached <file> stops tracking a file already committed'),
   ('And rotate anything that leaked', 'Day 6 covers why rotating comes before cleaning history')],
  {'lang': '.gitignore', 'kicker': 'LAB 02', 'split': 0.46}),

 ('bank', 'What PayTrack API teaches before you write a line of code',
  [('Money is an integer in MINOR units', 'amount_minor: 4599 is £45.99. 0.1 + 0.2 ≠ 0.3 in binary floating point'),
   ('A full card number is REFUSED at the API edge', 'Accepting it would pull the service, its logs, replicas and backups into PCI-DSS scope'),
   ('Only the last four digits are stored', 'Not sensitive on their own'),
   ('No customer identifier reaches the logs', 'Logs are widely readable and long-retained'),
   ('The referral limit is configuration, not code', 'Risk can change a threshold without a release')],
  {'lead': 'Scope is something you design OUT at the API boundary — not something you secure '
           'afterwards.',
   'ref': 'Appendix A §A.6 · app/src/app.py'}),

 ('lab', '02', 'Git Fundamentals',
  'Turn a directory into a repository containing PayTrack API, with a clean, meaningful history.',
  ['git init, and look inside .git to see the object database',
   'Bring in the PayTrack API source and RUN IT before committing it — never commit code you have not run',
   'Write .gitignore BEFORE the first commit (secrets, .venv, tfstate)',
   'Stage selectively, review git diff --staged, and write two properly-scoped commits',
   'Practise all three undos: restore, restore --staged, and revert',
   'Tag an annotated release'],
  'A local repository with four commits, an annotated tag, and a tested Flask application',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('table', 'Day 1 key terms',
  ['Term', 'Definition'],
  [['DevOps', 'Cultural + engineering practices that shorten commit-to-production time at high quality'],
   ['The Three Ways', 'Flow, Feedback, Continual learning and experimentation'],
   ['CALMS', 'Culture, Automation, Lean, Measurement, Sharing — a diagnostic'],
   ['Value stream', 'Every activity AND every queue from request to delivered value'],
   ['Flow efficiency', 'Process time ÷ lead time'],
   ['Little\'s Law', 'Lead time = WIP ÷ throughput'],
   ['Constraint', 'The step that limits the throughput of the whole stream'],
   ['Deploy / release', 'A technical event / a business decision'],
   ['Lead time for change', 'Commit → running in production'],
   ['Commit / branch / HEAD', 'An immutable snapshot / a movable pointer / the pointer to where you are']],
  'REFERENCE', {'widths': [2.6, 7.4]}),

 ('check', 'Day 1 — check your understanding',
  ['Your organisation has Jenkins, Docker and Kubernetes, yet a one-line change takes six weeks. '
   'Which CALMS dimension is your constraint, and how would you prove it?',
   'Team A deploys 40× a day with a 30 % change failure rate. Team B deploys weekly with 2 %. '
   'Who is better — and what else do you need to know?',
   'A team has 30 items in progress and finishes 3 a week. What is the lead time, and what happens if WIP drops to 10?',
   'Explain the difference between deploy and release, and name three techniques that separate them.',
   'Your teammate says they will "just reset main back to yesterday". What do you say?']),

 ('close', 1, 'Day 1 complete',
  ['A definition of DevOps you can defend, and the Three Ways behind it',
   'CALMS scores for your own organisation, and a feel for Westrum\'s three cultures',
   'Value streams, flow efficiency, Little\'s Law and the constraint',
   'Git\'s object model — and the difference between revert and reset',
   'AFTER CLASS: finish Labs 00–02 — the toolchain, your value stream map, your first repository'],
  'Day 2 takes that repository to GitHub and makes it a TEAM artefact: branching strategies, the four '
  'merge strategies, pull requests as a segregation-of-duties control — and then Continuous Integration, '
  'so that a broken change can no longer be merged at all.'),
]
