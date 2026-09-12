# -*- coding: utf-8 -*-
"""Day 2 — Branching, Pull Requests and Continuous Integration.  Module 2b."""
import diagrams as dg

DAY2 = [
 ('title', 2, 'Version Control & CI',
  'Making it impossible to merge a broken change',
  ['Branching strategies — and when each one is wrong',
   'Merge strategies · pull requests · CODEOWNERS',
   'Continuous Integration principles · Jenkins vs GitHub Actions',
   'Labs 03–05 — Team collaboration · CI pipeline · Jenkins comparison'],
  'Today the repository stops being yours and becomes the team\'s'),

 ('bullets', 'Where we left off, and where today goes',
  [('Yesterday: a local repository, four commits, one annotated tag', None),
   ('Today: that repository becomes a shared, governed, automated artefact', None),
   ('You will deliberately create and resolve a merge conflict',
    'The first time you meet one should not be in production at 17:45 on a Friday'),
   ('You will make the merge button go grey', 'And that is the point of the whole day'),
   ('You will see the whole room\'s branches in one picture', None)],
  'DAY 2'),

 ('section', '1', 'Branching & Merging', 'Strategies, pull requests and the golden rule',
  ['Three branching strategies', 'Four merge strategies', 'Pull requests as a control', 'CODEOWNERS']),

 ('diagram', 'Three branching strategies', dg.branching_compare, 'MODULE 2 §2.4'),


 ('compare', 'Two teams, two branching habits',
  'Team A merges to main twice a day. Team B works on feature branches for three weeks, then '
  'merges. Both have the same tests, the same people and the same product. Which team has the '
  'harder job, and where exactly does the pain show up?',
  ['Two minutes in pairs. Name the specific moment the pain arrives for Team B.',
   'Then: what would Team B have to build BEFORE it could safely work like Team A?'],
  'Team B\'s pain arrives at merge — three weeks of unintegrated divergence landing at once, '
  'usually the day before a release. The prerequisites for Team A are trustworthy tests and '
  'feature flags. Batch size is the mechanism, and DORA measures it consistently.', 3),
 ('table', 'Choosing a branching strategy honestly',
  ['Use', 'When', 'The cost you accept'],
  [['Trunk-based', 'Mature test automation, feature flags, high deploy frequency',
    'You must have the discipline and the flags'],
   ['GitHub Flow', 'Most teams, most of the time. Web services, continuous delivery',
    'Slightly longer-lived branches than trunk'],
   ['GitFlow', 'Versioned software shipped to customers who choose when to upgrade',
    'Heavy process; routine merge pain'],
   ['Release branches', 'You must support several versions in production at once',
    'Cherry-pick maintenance across branches']],
  'MODULE 2 §2.4', {'widths': [1.9, 4.2, 3.4],
   'note': ('THE COMMON MISTAKE', 'Adopting GitFlow because it appears in a diagram, for a web service '
            'deployed continuously from one production version. You inherit all of its cost and none of '
            'its benefit.')}),

 ('table', 'Merge strategies — what each one does to history',
  ['Strategy', 'Result', 'Use it when'],
  [['Fast-forward', 'Moves the pointer. No merge commit', 'Linear history, scripted merges'],
   ['Merge commit', 'A commit with two parents. Preserves everything', 'Shared branches; full history matters'],
   ['Squash merge', 'One tidy commit on main per PR', 'GitHub Flow — THE DEFAULT HERE'],
   ['Rebase', 'Replays your commits on a new base — NEW SHAs', 'Your own un-pushed branch only']],
  'MODULE 2 §2.5', {'widths': [2.0, 4.0, 3.5], 'emph': [2],
   'note': ('THE GOLDEN RULE OF REBASING', 'Never rebase commits that exist outside your own machine. '
            'Rebasing rewrites history; anyone who has pulled those commits now has a divergent copy, '
            'and the recovery is manual and unpleasant.')}),

 ('define', 'Pull request',
  'A request to merge one branch into another, carrying a diff, a discussion, automated check '
  'results and an explicit approval decision — and, crucially, a permanent record of all four.',
  [('It is a QUALITY gate', 'A second pair of eyes before code reaches the mainline'),
   ('It is a KNOWLEDGE mechanism', 'The fastest way to spread context across a team'),
   ('It is a CONTROL', 'Enforced by branch protection, not by a policy document'),
   ('It is EVIDENCE', 'Approver identity, timestamp, checks — generated automatically')],
  'MODULE 2 §2.6'),

 ('diagram', 'Segregation of duties, two ways', dg.sod_control, 'APPENDIX A §A.3',
  {'speaker': 'This is the slide to linger on with a banking audience. Ask: how would your organisation '
   'answer "prove the code in production today was reviewed by someone other than its author"? '
   'And how long would it take?'}),

 ('bullets', 'What good code review actually looks like',
  [('Keep PRs under ~400 lines', 'Review quality falls off a cliff beyond that; large PRs get rubber-stamped'),
   ('Review within hours, not days', 'Review latency is usually the largest queue in the value stream'),
   ('Comment on the code, never the person', '"This could deadlock if…" not "you always forget…"'),
   ('Ask questions rather than issue orders', '"What happens if target is null?" teaches; "add a null check" does not'),
   ('Automate everything a machine can check', 'Formatting, style and lint must never be a human comment'),
   ('Approve with a real read', 'A "LGTM" 30 seconds after opening is a control that is not operating')],
  'MODULE 2 §2.6',
  {'note': ('CODEOWNERS', 'Route reviews automatically by path. The critical entries are '
            '.github/workflows/ and your deployment manifests — a change there can bypass every other '
            'control, so it deserves the STRICTEST review, not the loosest.')}),

 ('lab', '03', 'Branching, Pull Requests and Team Collaboration',
  'Put your repository on GitHub, enforce the strategy with server-side rules, and collide with a colleague on purpose.',
  ['Create the shared repository; push; add your teammates',
   'Protect main: required approvals, no self-approval, no force-push, squash-only',
   'Prove it works — try to push directly to main and watch it be REJECTED',
   'Two contributors change the SAME lines on different branches',
   'Resolve the resulting conflict properly, run the tests, and merge',
   'Add CODEOWNERS — and see the whole team\'s branches on the Network graph'],
  'A governed GitHub repository with branch protection, two merged PRs and one resolved conflict'),

 ('bank', 'The pull request IS your change control',
  [('"Prove the author did not approve their own change"',
    'Branch protection configuration + the PR record. Answered in seconds, for 100 % of changes'),
   ('"Prove it was tested"', 'The CI run attached to the merge commit, with retained artefacts'),
   ('"Prove what exactly went to production"', 'The merge commit → the image digest → the OCI revision label'),
   ('Standard change, not a CAB item',
    'ITIL 4 already allows pre-authorised, repeatable, automated changes. Ask for ONE service'),
   ('Retention is the part teams forget',
    'Pipeline logs ARE audit evidence — set retention to your regulation, not the CI default')],
  {'lead': 'A regulator does not require a meeting. It requires a control that is designed effectively, '
           'operating effectively, and evidenced. A meeting is one way to do that — measurably a poor one.',
   'ref': 'Appendix A §A.3–A.5'}),

 ('section', '2', 'Continuous Integration', 'Principles, pipelines and the two platforms',
  ['What CI actually means', 'The deployment pipeline', 'Build automation',
   'GitHub Actions', 'Jenkins']),

 ('define', 'Continuous Integration',
  'A practice in which every developer integrates their work into the shared mainline at least '
  'daily, and every integration is verified by an automated build and test run that anyone can see.',
  [('"Integrates daily" is the part teams skip', 'A CI server running against week-old branches is not CI'),
   ('"Automated build AND TEST"', 'A build that only compiles tells you almost nothing'),
   ('"Anyone can see"', 'Visibility is the mechanism that makes a red build matter'),
   ('The goal is not the tool — it is SMALL BATCHES, integrated constantly', None)],
  'MODULE 2 §2.7'),

 ('diagram', 'The deployment pipeline', dg.ci_pipeline, 'MODULE 6 §6.2 — INTRODUCED TODAY'),

 ('bullets', 'The rules that make CI work',
  [('Keep the build fast — under 10 minutes', 'Beyond that people stop waiting and start batching'),
   ('A red mainline STOPS THE LINE', 'Fixing it takes priority over new work. No exceptions'),
   ('Never comment out a failing test', 'Fix it or delete it — a disabled test is a lie'),
   ('Fix or delete flaky tests', 'One flaky test teaches the whole team to ignore red'),
   ('Everyone commits to the mainline daily', None),
   ('Build ONCE; promote the same artefact', 'Rebuilding per environment invalidates every earlier test'),
   ('Run the same checks locally that CI runs', '3 seconds of feedback beats 3 minutes')],
  'MODULE 2 §2.7', {'cols': 2}),

 ('two', 'GitHub Actions vs Jenkins — the honest comparison',
  ('GITHUB ACTIONS', ['✔ Working pipeline in minutes',
                      '✔ No server to operate, patch or back up',
                      '✔ Free and unlimited on public repos',
                      '✔ Secrets, OIDC and artefacts built in',
                      '✗ Vendor coupling',
                      '✗ Unpinned third-party Actions are a supply-chain risk'], 'teal'),
  ('JENKINS', ['✔ Runs inside your own network — air-gapped, on-prem, hardware',
               '✔ ~1 900 plugins; extremely flexible',
               '✔ No per-minute cost',
               '✗ You operate a STATEFUL, security-sensitive server',
               '✗ Plugin sprawl and snowflake job config',
               '✗ A webhook needs Jenkins reachable from the internet'], 'orange'),
  'MODULE 2 §2.9–2.10',
  ('THE DECIDING QUESTION', 'Not "which is better" but "must this run inside our network?" '
   'The cheapest server to operate is the one you do not have — but a bank with on-prem '
   'constraints may have no choice, and that is a legitimate answer.')),

 ('bullets', 'Securing the pipeline itself',
  [('Pin third-party Actions to a full commit SHA, not a tag',
    'A tag is mutable: whoever controls it can change what runs with YOUR token'),
   ('Least-privilege permissions: block', 'Default GITHUB_TOKEN scope is broader than you need'),
   ('Short-lived OIDC tokens instead of long-lived secrets',
    'The ideal is a credential that does not exist long enough to be stolen'),
   ('Never expose secrets to pull requests from forks', 'Use pull_request, not pull_request_target'),
   ('CODEOWNERS on .github/workflows/', 'Pipeline changes need the strictest review'),
   ('Ephemeral runners — one job per runner', 'A reused runner leaks state between jobs')],
  'MODULE 7 §7.4 — PREVIEW',
  {'note': ('WHY THIS MATTERS NOW', 'Your CI system holds credentials to everything and executes code by '
            'design. SolarWinds, Codecov and the xz-utils backdoor were all supply-chain compromises. '
            'You will harden this properly on day 6.')}),


 ('predict', 'What happens when you push a broken change?',
  'You are about to add a pipeline that runs on every pull request. Before you build it: '
  'in YOUR organisation today, what stops a change that breaks the tests from reaching main?',
  ['Write down the actual mechanism — not the policy, the mechanism.',
   'Is it a person, a convention, or something the system enforces?',
   'How many changes last month did it apply to? All of them, or the ones somebody looked at?'],
  'In Lab 04 you will break the health endpoint deliberately, open a PR, and watch the merge '
  'button go grey. That is a control that applies to 100 % of changes, with no meeting — and it '
  'is the argument you take to your risk function.', 3),
 ('lab', '04 + 05', 'GitHub Actions CI · Jenkins on localhost',
  'Build a pipeline that makes it impossible to merge a broken change — then build the same thing in Jenkins and compare.',
  ['Write ci.yml: lint, test across two Python versions, enforce a coverage floor',
   'Push it, watch it run, and merge it',
   'Make "CI passed" a REQUIRED status check in branch protection',
   'Deliberately break the health endpoint and open a PR',
   'Watch the checks go red and the merge button go GREY — this is the lesson',
   'Run Jenkins in Docker, write a Jenkinsfile, and record an honest comparison'],
  'A repository where 100 % of changes are gated by an automated build, in both CI models'),

 ('check', 'Day 2 — check your understanding',
  ['Your team uses GitFlow for a web service deployed continuously from one production version. '
   'What are you paying for, and what would you change?',
   'Explain the golden rule of rebasing, and what goes wrong if you break it.',
   'Why must the artefact be built once and promoted, rather than rebuilt per environment?',
   'uses: some-org/deploy@main — state the risk in one sentence and the fix in one sentence.',
   'Design a segregation-of-duties control that needs no meeting — and name the evidence it produces.']),

 ('close', 2, 'Day 2 complete',
  ['A GitHub repository with enforced branch protection and squash-only merges',
   'A resolved merge conflict, done properly, with tests re-run afterwards',
   'A CI pipeline that blocks any merge that breaks it — you saw the button go grey',
   'The same pipeline in Jenkins, and an evidence-based comparison',
   'CODEOWNERS routing review on the paths that matter most'],
  'Day 3 containerises PayTrack API. You will build the image three times — naively, multi-stage, '
  'then hardened — and MEASURE the difference: 1.1 GB to 150 MB, root to uid 10001, and a ten-second '
  'shutdown down to instant. Then a full local stack with Compose.'),
]
