# -*- coding: utf-8 -*-
"""Day 2 — Working Together on Code: branches, everyday Git, pull requests and Continuous Integration.

Beginner edition for a 3-HOUR session. Every technical word is explained the first time it appears.
DAY2 is the taught deck (~46 slides). DAY2_EXTRA builds a separate optional reading deck,
Day2_Version_Control_and_CI_Going_Further.pptx, holding everything that is not taught in the session.
Labs 03–05 are started together at the end of the session and finished after class.
"""
import diagrams as dg

DAY2 = [
 ('title',
  2,
  'Working Together on Code',
  "How a team saves, shares and checks changes — so mistakes don't reach the live system",
  ['What Git is, in plain English — and the everyday commands you will use',
   'Branches: working on a change without disturbing anyone else',
   'Pull requests: a colleague checks your work before it goes in',
   'Continuous Integration: a computer tests every change automatically',
   'After class — Labs 03–05: a shared project, a merge conflict, an automatic check'],
  "Today your project stops being yours alone and becomes the team's"),

 ('agenda',
  'Day 2 at a glance',
  [('theory',
    'Words you will hear today · the journey of one change'),
   ('theory',
    'Branches — and how teams use them'),
   ('theory',
    'Everyday Git: the commands you need'),
   ('theory',
    'Combining work: merge, rebase and conflicts · COMPARE exercise'),
   ('demo',
    'A merge conflict, start to finish'),
   ('break',
    'Break · 15 minutes'),
   ('theory',
    'Pull requests: a second pair of eyes on every change'),
   ('theory',
    'Continuous Integration · PREDICT exercise'),
   ('theory',
    'The tools that run the checks: GitHub Actions and Jenkins'),
   ('demo',
    'Watch the merge button go grey'),
   ('practical',
    'Start Lab 03 together'),
   ('after',
    'Finish Labs 03–05 after class · optional reading: Day 2 Going Further')],
  'TODAY',
  {'speaker': 'Three hours, pitched for beginners. Every new word is explained the first time it appears. Anything deeper is in the separate Going Further deck and the Git Command Guide — point keen delegates there instead of going deeper in class.'}),

 ('table',
  'Words you will hear today',
  ['Word',
   'What it means in plain English'],
  [['Repository (repo)',
    'A project folder plus the full history of every change made to it'],
   ['Commit',
    'A saved snapshot of your changes, with a short note saying why'],
   ['Branch',
    'A separate line of work, so you can change things without touching the main version'],
   ['main',
    'The official version of the project that everyone builds on'],
   ['Merge',
    'Bringing the changes from one branch into another'],
   ['Merge conflict',
    'Two people changed the same line — Git asks a person to decide'],
   ['Remote · GitHub',
    'The shared copy of the repository, on a server the whole team can reach'],
   ['Push · pull',
    "Upload your commits to the shared copy · download everyone else's"],
   ['Pull request (PR)',
    'A request to merge your branch, where colleagues review it first'],
   ['CI (Continuous Integration)',
    'A computer that builds and tests every change automatically']],
  'START HERE',
  {'widths': [3.0,
    7.0],
   'speaker': 'Read the list aloud once. Tell the room these ten words cover most of today, and that the recap at the end of the day comes back to them.'}),

 ('flow',
  'The journey of one change',
  [('You edit files in your project folder',
    'Nothing is saved in Git yet — this is your working copy'),
   ('git add — choose which changes to save',
    'Like putting items in a basket before you pay'),
   ('git commit — save them as a snapshot, with a note',
    'A save point you can always go back to'),
   ('git push — upload your commits to GitHub',
    'Now the team can see your work'),
   ('Open a pull request — ask for a review',
    'A colleague reads it; a computer runs the tests'),
   ('Merge — your change joins main',
    'It is now part of the official version')],
  'GIT IN PLAIN ENGLISH'),

 ('section',
  '1',
  'Branches',
  "Working on a change without getting in anyone's way",
  ['What a branch is',
   'Three ways teams use branches — and the one this course uses',
   'Naming your branch']),

 ('define',
  'Branch',
  'A separate line of work inside the same project. You make your changes on the branch; the main version stays untouched until your work is checked and merged back in.',
  [('Think of a copy of a document you can scribble on',
    'The original stays clean until you bring the changes back'),
   ('Every change gets its own branch',
    'Two people can work at the same time without overwriting each other'),
   ('A branch is cheap',
    'Git creates one instantly, however big the project is'),
   ('The team agrees how branches are used',
    'That agreement is called a branching strategy — next slide')],
  'MODULE 2 §2.4'),

 ('diagram',
  'Three ways teams use branches',
  dg.branching_compare,
  'MODULE 2 §2.4',
  {'speaker': 'Keep this at the level of habits, not tools. The only thing delegates must take away: this course uses GitHub Flow — one short branch per change, reviewed, then merged.'}),

 ('code',
  'Naming your branch',
  '''feature/PAY-142-add-readiness-probe
bugfix/PAY-158-null-latency
hotfix/PAY-160-crash-on-empty-body
chore/bump-flask-3.0.3

$ git switch -c feature/PAY-142-add-readiness-probe
$ git push -u origin HEAD
# ... pull request reviewed and squash-merged ...
$ git switch main && git pull
$ git branch -d feature/PAY-142-add-readiness-probe''',
  [('Pattern: type / ticket - short description',
    'Anyone can tell what the branch is for, and find the ticket'),
   ('Types: feature · bugfix · hotfix · chore',
    'New work · a fix · an urgent fix · housekeeping'),
   ('git push -u origin HEAD',
    'Uploads your branch to GitHub for the first time'),
   ('Delete the branch once it is merged',
    'Old branches pile up and confuse everyone'),
   ('Never work directly on main',
    'Once main is protected GitHub refuses it — you will see that in Lab 03')],
  {'lang': 'branch names  ·  bash',
   'kicker': 'MODULE 2 §2.4',
   'split': 0.55}),

 ('section',
  '2',
  'Everyday Git',
  'The commands you will actually use',
  ['A normal day with Git',
   'Get a project · see what changed · save your work',
   'Branches · stay in sync with GitHub',
   'Undo safely',
   'Which command do I need?'],
  {'speaker': 'About three minutes per slide. Say the plain-English meaning first, then the Git word. Other commands (stash, log in depth, reset, reflog, cherry-pick, tag, bisect, clean) are in the Going Further deck and the Git Command Guide — not today.'}),

 ('code',
  'A normal day with Git, in order',
  '''$ git switch main && git pull             # get the latest official version
$ git switch -c feature/PAY-142            # start a branch for your change
  ... edit app/src/app.py ...
$ git status                               # which files did I change?
$ git diff                                 # what exactly did I change?
$ git add app/src/app.py                   # pick the changes to save
$ git diff --staged                        # double-check what will be saved
$ git commit -m "feat: add readiness probe"
$ git push -u origin HEAD                  # upload the branch to GitHub
  ... open a pull request, get a review ...
$ git switch main && git pull              # after the merge: update again''',
  [('Start from the latest main',
    "So you build on top of everyone else's work"),
   ('One branch per change',
    'Small, focused changes are easier to review and to undo'),
   ('Look before you save',
    'git status and git diff show exactly what is about to go in'),
   ('Save with a clear note',
    'Say WHY — the change itself already shows what'),
   ('Share it and ask for a review',
    'Nothing reaches main without a second pair of eyes')],
  {'lang': 'bash',
   'kicker': 'EVERYDAY GIT',
   'split': 0.6,
   'speaker': 'Tell it as a story. Each line is explained on its own slide next.'}),

 ('code',
  'git init · git clone — get a project',
  '''$ mkdir paytrack-api && cd paytrack-api
$ git init
Initialized empty Git repository in /home/you/devops-course/paytrack-api/.git/

$ git clone https://github.com/kumbulanit/devops_professional.git course-material
Cloning into 'course-material'...
remote: Enumerating objects: 140, done.
remote: Counting objects: 100% (140/140), done.
remote: Compressing objects: 100% (87/87), done.
remote: Total 140 (delta 22), reused 136 (delta 21), pack-reused 0 (from 0)
Receiving objects: 100% (140/140), 386.04 KiB | 10.16 MiB/s, done.
Resolving deltas: 100% (22/22), done.
$ cd course-material && git remote -v
origin    https://github.com/kumbulanit/devops_professional.git (fetch)
origin    https://github.com/kumbulanit/devops_professional.git (push)''',
  [('What — start a new project, or copy an existing one',
    'init: Git starts tracking a folder · clone: download a project with all its history'),
   ('How — git clone <address> <folder-name>',
    'Copy the address from the green "Code" button on GitHub'),
   ('When — clone to join a project · init to start a new one',
    'In this course you clone the course material and init your own project'),
   ('Careful — never run git init inside an existing project',
    'A project inside a project confuses Git; run git status first to check'),
   ('Good to know — clone remembers where it came from',
    'That address is called "origin"; git remote -v shows it')],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git status · git diff — what have I changed?',
  '''$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
    modified:   README.md

Changes not staged for commit:
    modified:   app/src/config.py

Untracked files:
    app/src/probes.py

$ git status -s
M  README.md
 M app/src/config.py
?? app/src/probes.py
$ git diff
@@ -3,5 +3,5 @@ import os
-    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "30"))
+    TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "45"))
$ git diff --staged
@@ -1 +1,3 @@
+Card authorisation service.''',
  [('What — status lists your changes · diff shows them line by line',
    'Nothing is changed by either command, so they are always safe'),
   ('How — read the three groups in git status',
    '"to be committed" = picked for your next save · "not staged" = changed, not picked · "untracked" = new file Git doesn\'t know'),
   ('How — git status -s is the short version',
    'M = modified · A = added · ?? = a new file Git is not tracking yet'),
   ('When — before every save, and whenever you are unsure',
    'Make it a habit: status, then diff, then add'),
   ('Careful — git diff goes blank once everything is picked',
    'Use git diff --staged to see what you are about to save')],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git add · git commit — save your work',
  '''$ git status -s
 M app/src/probes.py
?? config/
$ git add app/src/probes.py
$ git status -s
M  app/src/probes.py
?? config/
$ git commit -m "feat: report the store in /ready"
[main c6b1cae] feat: report the store in /ready
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline
c6b1cae feat: report the store in /ready
2ccf1a2 feat: add PayTrack API service''',
  [('What — add picks changes; commit saves them',
    'Like a basket: add puts things in, commit pays for them'),
   ('How — git add <file> · git commit -m "what changed"',
    'Each commit gets a unique ID — here c6b1cae — and your note'),
   ('Careful — pick only what you mean to save',
    'config/ holds a password file: it was deliberately NOT added. git add . would have picked it'),
   ('Good to know — git log lists your commits',
    'Newest first, with the note you wrote'),
   ('Good to know — a commit is only on YOUR computer',
    'Nobody else has it until you git push')],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git branch · git switch — work on a branch',
  '''$ git switch -c feature/PAY-150-region-header
Switched to a new branch 'feature/PAY-150-region-header'
$ git branch
* feature/PAY-150-region-header
  main
# ...one commit on the branch...
$ git switch main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
$ git branch -d feature/PAY-150-region-header
error: the branch 'feature/PAY-150-region-header' is not fully merged
$ git branch -D feature/PAY-150-region-header
Deleted branch feature/PAY-150-region-header (was d48abee).''',
  [('What — branch lists branches · switch moves you to one',
    'Your files change to match the branch you are on'),
   ('How — git switch -c <name> creates a branch and moves onto it',
    'git switch <name> moves to one that exists · * marks where you are'),
   ('When — at the start of every new piece of work',
    'Always from an up-to-date main'),
   ('Tidy up — git branch -d <name> once it is merged',
    'Git refuses if the work is not merged yet — that is a safety net'),
   ('Careful — git branch -D deletes even unmerged work',
    "Only use the capital D when you are sure you don't need it")],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git pull · git push — stay in sync with GitHub',
  '''$ git pull
From https://github.com/<your-username>/paytrack-api
   c6b1cae..eceac51  main       -> origin/main
Updating c6b1cae..eceac51
Fast-forward
 docs/CONTRIBUTING.md | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 docs/CONTRIBUTING.md
$ git switch -c feature/PAY-170
Switched to a new branch 'feature/PAY-170'
$ git commit -qm "feat: supported currency list"
$ git push -u origin HEAD
To https://github.com/<your-username>/paytrack-api.git
 * [new branch]      HEAD -> feature/PAY-170
branch 'feature/PAY-170' set up to track 'origin/feature/PAY-170'.''',
  [("What — pull downloads your team's work · push uploads yours",
    '"origin" is Git\'s name for the copy on GitHub'),
   ('How — git pull before you start work',
    "Here a colleague's new file arrives: docs/CONTRIBUTING.md"),
   ('How — the first push of a branch: git push -u origin HEAD',
    'After that, a plain git push is enough'),
   ('If a push is rejected — someone pushed before you',
    'Run git pull, then push again'),
   ('Careful — never force-push to main',
    "It would overwrite other people's work — GitHub can block it (Lab 03)")],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git restore · git revert — undo safely',
  '''$ git status -s
 M app/src/config.py
$ git restore app/src/config.py
$ git status -s
$ git log --oneline -2
5467d18 perf: cut settlement timeout to 5s
eceac51 docs: add contributing guide
$ git revert HEAD --no-edit
[main e436a04] Revert "perf: cut settlement timeout to 5s"
 Date: Thu Sep 17 09:18:01 2026 +0200
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline -3
e436a04 Revert "perf: cut settlement timeout to 5s"
5467d18 perf: cut settlement timeout to 5s
eceac51 docs: add contributing guide
$ git push
   5467d18..e436a04  main -> main''',
  [('restore — throw away an edit you have NOT committed',
    'The file goes back to how it was at the last commit'),
   ('Careful — restore cannot be undone',
    'Those edits were never saved anywhere'),
   ('revert — cancel a commit that is ALREADY shared',
    'It adds a new commit that does the opposite'),
   ('Why revert is safe',
    'Nothing is deleted: the mistake and the fix are both in the history, and everyone just pulls'),
   ('In a bank — the record stays complete',
    'You can see what was undone, by whom, and why')],
  {'lang': 'bash  ·  real output',
   'kicker': 'EVERYDAY GIT',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('table',
  'Which command do I need?',
  ['I want to…',
   'Command',
   'Safe?'],
  [['See what I have changed',
    'git status · git diff',
    '✔ Only looks'],
   ['Start a new piece of work',
    'git switch main · git pull · git switch -c <name>',
    '✔'],
   ['Save my work',
    'git add <file> · git commit -m "note"',
    '✔'],
   ['See my saved commits',
    'git log --oneline',
    '✔ Only looks'],
   ["Share my work · get my team's work",
    'git push · git pull',
    '✔'],
   ["Throw away an edit I haven't saved",
    'git restore <file>',
    '✗ Cannot be undone'],
   ['Undo a change that is already shared',
    'git revert <ID>',
    '✔ Keeps the history']],
  'EVERYDAY GIT',
  {'widths': [3.6,
    4.6,
    2.1],
   'emph': [1]}),

 ('section',
  '3',
  'Combining Work',
  'Merge, rebase — and what to do when two people change the same line',
  ['Ways to bring a branch into main',
   'What rebase means, and how to do it',
   'Merge or rebase? — and the golden rule',
   'Merge conflicts, calmly']),

 ('diagram',
  'Ways to bring a branch into main',
  dg.merge_strategies,
  'MODULE 2 §2.5',
  {'speaker': 'Each circle is a commit (a save). Walk the four boxes left to right, top to bottom. The one to remember is SQUASH MERGE, because that is what the course uses on GitHub.'}),

 ('define',
  'Rebase',
  'Moving your branch so it starts from the latest version of main — as if you had begun your work today. Git replays your saves, one by one, on top of the new main.',
  [('Why — main moved on while you were working',
    'Rebase brings your branch up to date without an extra "merge" commit'),
   ('The result — a neat, straight-line history',
    "Your saves sit on top of everyone else's"),
   ('The catch — your saves get NEW IDs',
    'They are copies, so anyone who already has the old ones gets confused'),
   ('The rule — only rebase work nobody else is using',
    'Your own branch: fine. main or a shared branch: never')],
  'MODULE 2 §2.5',
  {'speaker': 'Say the word slowly: re-BASE — change what your branch is based on. Everything about when it is safe follows from one fact: the saves get new IDs.'}),

 ('code',
  'How to rebase your branch',
  '''$ git switch feature/PAY-142
$ git fetch origin
   039ad72..6fcdcba  main       -> origin/main
$ git rebase origin/main
Successfully rebased and updated refs/heads/feature/PAY-142.
$ python -m pytest -q                  # test the REBASED code
$ git push
 ! [rejected]        feature/PAY-142 -> feature/PAY-142 (non-fast-forward)
hint: use 'git pull' before pushing again.   # do NOT follow this hint
$ git push --force-with-lease
 + f1c7cab...a39d691 feature/PAY-142 -> feature/PAY-142 (forced update)''',
  [('1 · git fetch origin — download the latest main',
    'You can only move on top of what you have downloaded'),
   ('2 · git rebase origin/main — move your branch on top',
    'Git replays your saves one at a time'),
   ('3 · run the tests',
    'Your work now sits on new code — check it still works'),
   ('4 · git push --force-with-lease',
    'A plain push is refused because the IDs changed. This replaces YOUR branch only, and stops if anyone else pushed to it'),
   ("Ignore Git's hint to run git pull here",
    'It would bring the old copies back in and double everything')],
  {'lang': 'bash  ·  real output',
   'kicker': 'MODULE 2 §2.5',
   'split': 0.58}),

 ('table',
  'Merge or rebase?',
  ['Situation',
   'Use',
   'Why'],
  [['Your own branch, and main has moved on',
    'Rebase',
    'Only you have these commits — safe to move them'],
   ['A branch you share with a colleague',
    'Merge',
    'Rebasing would change commits they already have'],
   ['Your pull request is being reviewed',
    'Merge, or add new commits',
    'Reviewers can see what changed since they last looked'],
   ['main, or any branch the team uses',
    'Never rebase',
    'It rewrites history everyone depends on'],
   ['Finishing a pull request on GitHub',
    'Squash and merge',
    'One tidy commit per change on main']],
  'MODULE 2 §2.5',
  {'widths': [3.8,
    2.6,
    4.1],
   'emph': [0],
   'note': ('THE GOLDEN RULE',
    'Never rebase commits that other people already have. Rebase to update YOUR OWN work; merge to combine SHARED work.')}),

 ('compare',
  'Rebase or merge?',
  'For each situation, decide: rebase or merge — and say why in one sentence.',
  ['1 · Your branch is three commits behind main, and only you have worked on it.',
   '2 · You and a colleague both push to the same branch.',
   "3 · The team's release branch needs a fix that is already in main.",
   '4 · Your pull request has two real commits and four called "fix typo".'],
  '1 Rebase — only you have those saves. 2 Merge — rebasing would break your colleague\'s copy. 3 Merge, or copy just that one fix — a release branch is shared by the team. 4 Let "squash and merge" combine them into one — or tidy them first with an interactive rebase (optional section).',
  3),

 ('code',
  'A merge conflict is a question, not an error',
  '''def settlement_timeout():
<<<<<<< HEAD
    timeout = 30
=======
    timeout = 60
>>>>>>> feature/raise-timeout
    return timeout''',
  [('<<<<<<< HEAD',
    'Start of the version on the branch you are on'),
   ('=======',
    'The divider between the two versions'),
   ('>>>>>>> feature/raise-timeout',
    'End of the version coming from the other branch'),
   ('Fix it by deciding what the line SHOULD say',
    'Often a mix of both. Delete the three marker lines, run the tests, then git add and git commit'),
   ('Stuck? git merge --abort',
    'Puts everything back exactly as it was before the merge')],
  {'lang': 'app/src/config.py',
   'kicker': 'MODULE 2 §2.5',
   'split': 0.46}),

 ('demo',
  'A merge conflict, start to finish',
  '''$ git switch -c feature/raise-timeout
$ sed -i 's/timeout = 30/timeout = 60/' config.py
$ git commit -qam "feat: raise settlement timeout"
$ git switch main
$ sed -i 's/timeout = 30/timeout = 45/' config.py
$ git commit -qam "fix: interim timeout"
$ git merge feature/raise-timeout
Auto-merging config.py
CONFLICT (content): Merge conflict in config.py
Automatic merge failed; fix conflicts and then commit the result.
$ git status --short
UU config.py
$ nano config.py                  # decide the correct value
$ python -m pytest -q && git add config.py
$ git commit --no-edit''',
  [('Two branches changed the same line',
    'Git cannot guess which value is right, so it stops and asks'),
   ('git status shows UU — both sides changed it',
    'git status always tells you where you are and what to do next'),
   ('Decide, edit, and delete the markers',
    'Then run the tests before you save'),
   ('git commit --no-edit finishes the merge',
    'It keeps the message Git has already prepared')],
  {'minutes': 6,
   'speaker': 'Do this live and slowly. The goal is calm: a conflict is Git asking a question. Delegates create one on purpose with a partner in Lab 03.'}),

 ('section',
  '4',
  'Pull Requests',
  'A second pair of eyes on every change',
  ['What a pull request is',
   'The life of a pull request',
   'The old way and the automatic way',
   'Protecting main']),

 ('define',
  'Pull request (PR)',
  'A request to merge your branch into main. It shows your changes, lets colleagues comment and approve, runs the automatic tests — and keeps a permanent record of all of it.',
  [('It catches mistakes',
    'A colleague reads the change; a computer runs the tests'),
   ('It shares knowledge',
    'The reviewer learns what changed and why'),
   ('It is a rule, not a favour',
    'GitHub can refuse to merge anything that is not approved'),
   ('It is evidence',
    'Who wrote it, who approved it and which tests passed — recorded automatically')],
  'MODULE 2 §2.6'),

 ('flow',
  'The life of a pull request',
  [('You push your branch and open a pull request',
    'Describe what you changed and why'),
   ('The automatic checks start',
    'GitHub runs the tests on your change'),
   ('The results appear on the pull request',
    'Green tick = passed · red cross = something is broken'),
   ('The right reviewers are asked automatically',
    'A file called CODEOWNERS decides who'),
   ('Reviewers comment; you fix and push again',
    'The tests run again on every push'),
   ('A DIFFERENT person approves',
    "GitHub won't let you approve your own change"),
   ('Squash and merge',
    'Your change joins main as one commit'),
   ('The branch is deleted',
    'And the change can move on towards release')],
  'MODULE 2 §2.6'),

 ('two',
  'Checking changes: the old way and the automatic way',
  ('THE OLD WAY — A MEETING',
   ['• A developer finishes a change',
    '• A form is filled in; a meeting approves it',
    '• Someone copies the change to the live system by hand',
    '• Evidence: a signed form in a folder',
    '✗ Covers only the changes that reached the meeting'],
   'grey'),
  ('THE AUTOMATIC WAY — A PULL REQUEST',
   ['• GitHub refuses to merge until a DIFFERENT person approves',
    '• The tests must pass before the merge button works',
    '• The pipeline releases it — nobody copies files by hand',
    '• Who wrote it, who approved it, which tests passed: all recorded',
    '✔ Covers every change, and produces the evidence an auditor asks for'],
   'green'),
  'APPENDIX A §A.3',
  ('SAY IT THIS WAY',
   'Two people check every change — and the system, not a meeting, makes sure of it.')),

 ('table',
  'Protecting main — rules GitHub enforces for you',
  ['Setting on main',
   'What it means in practice'],
  [['Require a pull request before merging',
    'Nobody — not even an admin — can change main directly'],
   ['Require an approval',
    'A second person must say yes; you cannot approve your own work'],
   ['Dismiss old approvals when new changes arrive',
    'An approval covers the final version, not an early draft'],
   ['Require the checks to pass',
    'If the tests are red, the merge button stays grey'],
   ['Block force-pushes and deletion',
    "Nobody can rewrite or delete main's history"]],
  'MODULE 2 §2.6',
  {'widths': [4.2,
    5.8],
   'note': ('YOU DO THIS IN LAB 03',
    'Then you try to push straight to main — and watch GitHub refuse.')}),

 ('lab',
  '03',
  'Branching, Pull Requests and Team Collaboration',
  'Put your project on GitHub, protect main, and deliberately change the same line as a colleague — then sort it out.',
  ['Create the shared project on GitHub and add your teammates',
   'Protect main: an approval is required, and nobody can push straight in',
   'Try to push straight to main — and watch GitHub refuse',
   'Two people change the same line, on different branches',
   'Resolve the conflict, run the tests, and merge',
   "Add a pull request template and CODEOWNERS; see everyone's branches as a picture"],
  'A shared, protected GitHub project with two merged pull requests and one resolved conflict',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('section',
  '5',
  'Continuous Integration',
  'Letting a computer check every change',
  ['What CI means',
   'The simple rules',
   'From your change to the live system']),

 ('define',
  'Continuous Integration (CI)',
  'Everyone adds their work to main often — at least once a day — and every time they do, a computer automatically builds the project and runs the tests, where the whole team can see the result.',
  [('"Often" is the key word',
    'Small changes combined every day rarely clash'),
   ('"Automatically" means nobody has to remember',
    'Every push starts the tests'),
   ('"The whole team can see" makes it matter',
    'A red result gets noticed and fixed straight away'),
   ('A build server alone is not CI',
    'CI is the habit of small, frequent, tested changes')],
  'MODULE 2 §2.7'),

 ('table',
  'The simple rules that make CI work',
  ['Rule',
   'Why'],
  [['Add your work to main every day',
    'Small changes are easy to combine'],
   ['One command builds and tests everything',
    'Anyone — or any computer — gets the same result'],
   ['Fix a failing build immediately',
    'A broken main blocks the whole team'],
   ['Keep the checks under 10 minutes',
    'If people have to wait longer, they stop waiting'],
   ['Build once, and use that same build everywhere',
    'Otherwise what you tested is not what you release']],
  'MODULE 2 §2.7',
  {'widths': [4.3,
    5.7],
   'note': ('A QUICK TEST',
    'Does everyone add work to main daily? Does every change run the tests? Is a red build fixed first? Three yeses = Continuous Integration.')}),

 ('diagram',
  'From your change to the live system',
  dg.ci_pipeline,
  'INTRODUCED TODAY · MORE ON DAY 5',
  {'speaker': 'Walk left to right. The earlier a problem is caught, the cheaper it is: minutes to fix in step 1, an incident if it reaches the live system. That is why step 1 must be fast and strict.'}),

 ('predict',
  'What happens when someone pushes a broken change?',
  'In YOUR organisation today, what actually stops a change that breaks the tests from reaching the live system?',
  ['Write down what really happens — not what the policy says.',
   'Is it a person, a habit, or something the system enforces?',
   'Does it apply to every change, or only the ones someone happens to look at?'],
  'In Lab 04 you break the app on purpose, open a pull request, and watch the merge button go grey. The system stops it — for every change, with no meeting.',
  3),

 ('section',
  '6',
  'The Tools That Run the Checks',
  'GitHub Actions and Jenkins',
  ['Four words: event · workflow · job · step',
   'A workflow file, line by line',
   'GitHub Actions or Jenkins?']),

 ('table',
  'GitHub Actions in four words',
  ['Word',
   'What it means',
   'Example'],
  [['Event',
    'What starts it',
    'Someone pushes, or opens a pull request'],
   ['Workflow',
    'The whole set of checks, in one file',
    '.github/workflows/ci.yml'],
   ['Job',
    'A group of steps that run on one computer',
    '"test": install, check style, run the tests'],
   ['Step',
    'One single command',
    'pytest']],
  'MODULE 2 §2.10',
  {'widths': [2.0,
    4.2,
    4.0],
   'note': ('WHAT GITHUB ACTIONS IS',
    'The automation built into GitHub. You describe the checks in a file; GitHub runs them on its own computers at every event — event → workflow → jobs → steps.')}),

 ('code',
  'A CI workflow, line by line',
  '''name: CI
on:
  push:         { branches: [main] }
  pull_request: { branches: [main] }
permissions:
  contents: read                       # may only read the code
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-24.04
    strategy:
      matrix: { python-version: ["3.11", "3.12"] }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}", cache: pip }
      - run: pip install -r app/requirements-dev.txt
      - run: flake8 app/src app/tests      # any error stops the job
      - run: pytest --cov=src''',
  [('on: — when it runs',
    'Every push to main, and every pull request to main'),
   ('jobs: → test: — one job, called "test"',
    'runs-on picks the computer: a fresh Ubuntu machine'),
   ('matrix — run the same job twice',
    'Once with Python 3.11 and once with 3.12'),
   ('steps: — the commands, in order',
    'Get the code · set up Python · install · check the style · run the tests'),
   ('If any step fails, the job fails',
    'And the pull request shows a red cross')],
  {'lang': '.github/workflows/ci.yml',
   'kicker': 'LAB 04',
   'split': 0.58}),

 ('two',
  'GitHub Actions or Jenkins?',
  ('GITHUB ACTIONS',
   ['• Built into GitHub',
    '✔ Working in minutes — nothing to install',
    '✔ Free on public projects',
    '✗ Tied to GitHub, runs outside your network'],
   'teal'),
  ('JENKINS',
   ['• A free automation server your company runs itself',
    '✔ Runs inside your own network',
    '✔ Very flexible — thousands of plugins',
    '✗ Your team must run, update and secure it'],
   'orange'),
  'MODULE 2 §2.9–2.10',
  ('THE REAL QUESTION',
   '"Must this run inside our own network?" If not, the tool you don\'t have to look after is usually the cheaper one. Lab 05 builds the same checks in Jenkins, as a Jenkinsfile.')),

 ('demo',
  'Watch the merge button go grey',
  '''$ git switch -c test/deliberately-break-ci
$ python3 break_health.py         # /health now returns "BROKEN"
broke the /health contract
$ git commit -qam "test: deliberately break the health contract"
$ git push -u origin HEAD
$ gh pr create --fill
$ gh pr checks                     # wait for the run to finish
# test (3.11) and test (3.12) fail, so "CI passed" fails
# the PR page now says merging is blocked''',
  [('A small change that looks harmless',
    '/health now answers "BROKEN" instead of "ok"'),
   ('The tests know what /health must answer',
    'So they fail — on both Python versions'),
   ('The merge button goes grey',
    'GitHub will not let anyone merge it'),
   ('Ask the room',
    '"In your organisation, what would have stopped this change?"')],
  {'minutes': 5,
   'speaker': 'Lab 04 Step 6 does exactly this. The teaching moment is the grey button: a check that applies to every change, with no meeting. break_health.py stands for the small Python patch in the lab README.'}),

 ('lab',
  '04 + 05',
  'GitHub Actions CI · Jenkins on localhost',
  'Build an automatic check that makes it impossible to merge a broken change — then build the same check in Jenkins and compare.',
  ['Write a workflow file that checks the style and runs the tests',
   'Push it, watch it run, and merge it',
   'Make "CI passed" required before anything can be merged',
   'Break the app on purpose and open a pull request',
   'Watch the checks go red and the merge button go grey',
   'Run Jenkins on your laptop, write a Jenkinsfile, and compare the two'],
  'A project where every change is tested automatically before it can be merged'),

 ('check',
  'Day 2 — check your understanding',
  ['In your own words: what is a branch, and why would you use one?',
   'You changed two files but only want to save one of them. Which commands do you use?',
   'Your change is already in main and it is wrong. Which command undoes it safely — and why?',
   'What is a merge conflict, and what are the steps to resolve one?',
   'When is it safe to rebase, and when should you merge instead?',
   'Why must a DIFFERENT person approve a pull request — and what makes the merge button go grey?']),

 ('close',
  2,
  'Day 2 complete',
  ['What Git is, and the everyday commands: status, add, commit, switch, pull, push, restore, revert',
   'Branches, merge and rebase — and the golden rule',
   'Pull requests: a second person checks every change, and GitHub enforces it',
   'Continuous Integration: every change is tested automatically',
   'AFTER CLASS: finish Labs 03–05 · optional: the Going Further deck, and Labs 03A, 04A and 04B'],
  'Day 3 packages PayTrack API into a container — a box that runs the same way on every computer. You will see why that matters, how to build a small and safe one, and how to run the whole application with a single command.'),

]

DAY2_EXTRA = [
 ('title',
  2,
  'Day 2 — Going Further',
  'Optional reading, for after class — once the everyday commands feel comfortable',
  ['A: more everyday Git — history in depth, stash, one command per slide',
   'B: more Git commands — reset, reflog, cherry-pick, tag, bisect, clean',
   'C: more on branches and rebasing',
   'D: more on pull requests, CI and the tools'],
  'Not taught in the 3-hour session — read it, then practise it in Labs 03A, 04A and 04B'),

 ('section',
  'A',
  'More Everyday Git',
  "The single-command versions of today's slides, and two more commands",
  ['git log · git show · git blame',
   'git add and git commit in detail',
   'git fetch · git pull · git push in detail',
   'git stash · git restore · git revert in detail',
   'Words recap']),

 ('code',
  'git log · git show · git blame — look at the history',
  '''$ git log --oneline --graph --decorate
* 8159e94 (HEAD -> main, origin/main) feat: default region eu-west
* cf09014 fix: raise settlement timeout to 45s
* e901672 feat: add PayTrack API service
$ git log --oneline -- app/src/config.py
8159e94 feat: default region eu-west
cf09014 fix: raise settlement timeout to 45s
e901672 feat: add PayTrack API service
$ git log --oneline --grep=timeout
cf09014 fix: raise settlement timeout to 45s
$ git show --stat HEAD~1
commit cf09014a132e3fb76f3d590efa68c14b0f04556a
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:25:01 2026 +0200

    fix: raise settlement timeout to 45s

 app/src/config.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git blame --date=short -L 5,7 app/src/config.py
^e901672 (Your Name 2026-09-17 5)     VERSION = os.getenv("APP_VERSION", "1.0.0")
cf09014a (Your Name 2026-09-17 6)     TIMEOUT = int(os.getenv("SETTLEMENT_TIMEOUT", "45"))
8159e940 (Your Name 2026-09-17 7)     REGION = os.getenv("APP_REGION", "eu-west")''',
  [('What — log lists past saves · show opens one of them',
    'Newest first: the ID, and the note that was written'),
   ('How — git log --oneline · git show <ID>',
    'git log -- <file> shows only the saves that touched that file'),
   ('How — git blame <file>',
    'Shows, line by line, which save last changed each line'),
   ('When — you need to know what changed, when, and why',
    'Tracking down a bug, reviewing a release, answering an auditor'),
   ('Good to know — good notes make the history useful',
    'A log full of "fix" and "update" answers nothing')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git add — choose what to save',
  '''$ git status -s
 M app/src/config.py
?? app/src/probes.py
$ git add app/src/config.py app/src/probes.py
$ git status -s
M  app/src/config.py
A  app/src/probes.py
$ git commit -qm "feat: add readiness probe; raise settlement timeout to 45s"
$ git add .
$ git status -s
A  config/local.env
$ git rm --cached config/local.env
rm 'config/local.env'
$ echo 'config/local.env' >> .gitignore''',
  [('What — add picks changes to go into your next save',
    'Think of a basket: add puts things in, commit pays for them'),
   ('How — git add <file> · git add . picks everything',
    'git add -p lets you pick part of a file, piece by piece'),
   ('When — a piece of work is ready to be saved',
    'Pick only related changes, so each save does one job'),
   ("Careful — git add . also picks files you didn't mean to",
    'Here a file containing a password was picked by mistake'),
   ('Fix — git rm --cached <file>, then list it in .gitignore',
    'Git un-picks it but leaves it on your disk; .gitignore stops it being picked again')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git commit — save a snapshot',
  '''$ git switch -c feature/PAY-160
$ git status -s
 M app/src/probes.py
$ git commit -am "feat: report the store in /ready"
[feature/PAY-160 b8c506c] feat: report the store in /ready
 1 file changed, 1 insertion(+), 1 deletion(-)''',
  [('What — commit saves the picked changes as a snapshot',
    'Each snapshot gets a unique ID — here b8c506c — and your note'),
   ('How — git commit -m "type: what changed"',
    '-a also picks every file Git already knows about (but not new files)'),
   ('When — a small piece of work is done and the tests pass',
    'Many small saves are easier to review and to undo than one big one'),
   ('Write a note someone else will understand',
    '"fix: raise settlement timeout to 45s" — not "changes" or "stuff"'),
   ('Good to know — a commit is only on YOUR computer',
    'Nobody else has it until you git push')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  "git fetch · git pull — get your team's work",
  '''$ git remote -v
origin    https://github.com/<your-username>/paytrack-api.git (fetch)
origin    https://github.com/<your-username>/paytrack-api.git (push)
$ git fetch origin
From https://github.com/<your-username>/paytrack-api
   1ecd14b..4949c99  main       -> origin/main
$ git status -sb
## main...origin/main [behind 1]
$ git log --oneline main..origin/main
4949c99 docs: add contributing guide
$ git pull
Updating 1ecd14b..4949c99
Fast-forward
 docs/CONTRIBUTING.md | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 docs/CONTRIBUTING.md''',
  [('What — pull downloads new work and adds it to your branch',
    'fetch only downloads it, so you can look before you combine'),
   ('How — git pull',
    'Or git fetch, then git log main..origin/main to see what is new'),
   ('When — before you start work, and before you share yours',
    'So you always build on the latest version'),
   ('Good to know — "origin" is the name of the GitHub copy',
    'git remote -v shows its address'),
   ('Careful — save or set aside your own edits first',
    "Git won't pull over unsaved edits to the same files (see git stash)")],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git push — share your work',
  '''$ git switch -c feature/PAY-170
$ git commit -qm "feat: supported currency list"
$ git push
fatal: The current branch feature/PAY-170 has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin feature/PAY-170

$ git push -u origin HEAD
To https://github.com/<your-username>/paytrack-api.git
 * [new branch]      HEAD -> feature/PAY-170
branch 'feature/PAY-170' set up to track 'origin/feature/PAY-170'.
$ git status -sb
## feature/PAY-170...origin/feature/PAY-170
$ git push origin --delete feature/PAY-170
To https://github.com/<your-username>/paytrack-api.git
 - [deleted]         feature/PAY-170''',
  [('What — push uploads your saved commits to GitHub',
    "Only committed work goes — not edits you haven't saved"),
   ('How — the first time: git push -u origin HEAD',
    'After that just git push. HEAD means "the branch I am on"'),
   ('When — as soon as you want a review, or a backup',
    'Push early: work that only exists on a laptop is easy to lose'),
   ('If the push is rejected — someone pushed before you',
    'Run git pull first, then push again'),
   ('Careful — never force-push to main',
    "It overwrites other people's work. GitHub can block it (Lab 03)")],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git stash — put work aside for a moment',
  '''$ git status -s
 M app/src/app.py
$ git stash push -m "wip: retry budget"
Saved working directory and index state On main: wip: retry budget
$ git status -s
$ git stash list
stash@{0}: On main: wip: retry budget
$ git switch -c hotfix/PAY-160
Switched to a new branch 'hotfix/PAY-160'
# ...fix, commit and push the hotfix...
$ git switch main
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
$ git stash pop
On branch main
Changes not staged for commit:
    modified:   app/src/app.py
Dropped refs/stash@{0} (fe5910451df5361b311fb3370d6ef5808673fc5c)''',
  [('What — stash puts unsaved changes aside and clears your folder',
    'Like sweeping your desk into a drawer'),
   ('How — git stash push -m "note" · git stash pop brings it back',
    'git stash list shows what is in the drawer'),
   ('When — something urgent interrupts your work',
    'For example: switch branch to fix a bug, then come back'),
   ('Careful — brand-new files stay behind unless you add -u',
    'git stash push -u -m "note"'),
   ("Careful — don't leave things in the stash",
    'It is easy to forget and never uploaded — commit to a branch instead')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git restore — throw away changes to a file',
  '''$ git status -s
 M app/src/app.py
 M app/src/config.py
$ git restore app/src/config.py
$ git add app/src/app.py
$ git status -s
M  app/src/app.py
$ git restore --staged app/src/app.py
$ git status -s
 M app/src/app.py''',
  [('What — restore puts a file back as it was at the last save',
    'Unsaved edits to that file are thrown away'),
   ('How — git restore <file>',
    'git restore --staged <file> only un-picks it — your edits stay'),
   ("When — an experiment didn't work out",
    'Or you picked (git add) the wrong file by mistake'),
   ('Careful — there is no undo',
    'Edits that were never committed cannot be brought back'),
   ('Not sure? Use git stash instead',
    'Then the changes are put aside, not lost')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('code',
  'git revert — safely undo a change that is already shared',
  '''$ git log --oneline -3
6862196 perf: cut settlement timeout to 5s
c479b91 feat: report the store in /ready
b3b21c8 docs: move README under docs/; ignore local env
# ...pushed an hour ago — and settlements start timing out
$ git revert HEAD --no-edit
[main b4a1a93] Revert "perf: cut settlement timeout to 5s"
 Date: Thu Sep 17 08:22:25 2026 +0200
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline -3
b4a1a93 Revert "perf: cut settlement timeout to 5s"
6862196 perf: cut settlement timeout to 5s
c479b91 feat: report the store in /ready
$ git show --stat HEAD
commit b4a1a930a94acfbe4b8aaa8f8ab61251c2e1f1b0
Author: Your Name <you@example.com>
Date:   Thu Sep 17 08:22:25 2026 +0200

    Revert "perf: cut settlement timeout to 5s"

    This reverts commit 68621963449596b4f6056a595649c7ca2a33690e.

 app/src/config.py | 2 +-''',
  [('What — revert makes a NEW commit that cancels an old one',
    'The history keeps both: the mistake, and the fix'),
   ('How — git revert <ID>',
    'git log --oneline shows the ID of the commit to cancel'),
   ('When — the change is already pushed, or already in main',
    'Everyone else simply pulls one more commit — nothing breaks for them'),
   ('In a bank — the record stays complete',
    'You can see what was undone, by whom, and why'),
   ('Careful — later changes may depend on it',
    'Run the tests after reverting')],
  {'lang': 'bash  ·  real output',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.58,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal first, then the five points in the same order every time: what it does, how, when, what to be careful of, and one thing good to know. Say the plain-English word before the Git word. The full example is in docs/theory/git-command-guide.md.'}),

 ('table',
  'Day 2 words — a recap',
  ['Word',
   'What it means'],
  [['Repository · commit',
    'A project with its history · one saved snapshot, with a note'],
   ['Branch · main',
    'A separate line of work · the official version everyone builds on'],
   ['Stage (git add)',
    'Pick the changes that will go into your next commit'],
   ['Push · pull · fetch',
    'Upload your commits · download and combine · download only'],
   ['Merge · merge conflict',
    'Combine two branches · the same line was changed on both — a person decides'],
   ['Rebase',
    'Move your own branch on top of the latest main (new commit IDs)'],
   ['Revert',
    'Undo a shared change with a new commit that cancels it'],
   ['Pull request',
    'A request to merge, reviewed and tested before it is accepted'],
   ['Branch protection',
    'GitHub rules: no direct pushes, an approval required, tests must pass'],
   ['CODEOWNERS',
    'A file that decides who must review which files'],
   ['Continuous Integration',
    'Small changes added daily, each one tested automatically'],
   ['Workflow · job · step',
    'The checks file · a group of steps on one computer · one command']],
  'GOING FURTHER · OPTIONAL',
  {'widths': [3.0,
    7.0]}),

 ('section',
  'B',
  'More Git Commands',
  'Powerful — and some of them can lose work, so read the warnings',
  ['git reset · git reflog',
   'git cherry-pick · git tag',
   'git bisect · git clean']),

 ('code', 'git reset — move the branch back (soft · mixed · hard)',
  '$ git log --oneline -2\nc26a67d chore: note the retry budget\n8159e94 feat: default region eu-west\n$ git reset --soft HEAD~1\n$ git status -s\nM  app/src/app.py\n$ git commit -qm "chore: note the retry budget"\n$ git reset HEAD~1\nUnstaged changes after reset:\nM    app/src/app.py\n$ git status -s\n M app/src/app.py\n$ git commit -qam "chore: note the retry budget"\n$ git reset --hard HEAD~1\nHEAD is now at 8159e94 feat: default region eu-west\n$ git status -s\n$ git log --oneline -1\n8159e94 feat: default region eu-west',
  [('Means: reset moves the branch pointer to another commit', 'Later commits fall off the branch; the mode decides what happens to their changes'), ('--soft keeps the changes STAGED', 'Redo the last commit: split it, or change what goes into it'), ('--mixed (the default) keeps them UNSTAGED', 'Start the staging again, for example with git add -p'), ('--hard DISCARDS the commit AND the edits', 'Committed work is recoverable through the reflog; uncommitted edits are not'), ('Avoid: reset on anything already pushed', 'It rewrites shared history — use git revert instead')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('code', 'git reflog — find a commit you thought you had lost',
  '$ git reset --hard HEAD~1\nHEAD is now at 8159e94 feat: default region eu-west\n# ..."wait — I needed that commit"\n$ git reflog -4\n8159e94 HEAD@{0}: reset: moving to HEAD~1\nc26a67d HEAD@{1}: commit: chore: note the retry budget\n8159e94 HEAD@{2}: reset: moving to HEAD~1\nc26a67d HEAD@{3}: commit: chore: note the retry budget\n$ git reset --hard HEAD@{1}\nHEAD is now at c26a67d chore: note the retry budget\n$ git log --oneline -2\nc26a67d chore: note the retry budget\n8159e94 feat: default region eu-west',
  [('Means: the reflog is a diary of every place HEAD has been', 'Commits, resets, switches and rebases — including commits no branch points at'), ('How: git reflog, then reset or switch to HEAD@{n}', 'Or keep it on a new branch: git switch -c rescue HEAD@{1}'), ('Use when: a reset, amend, rebase or branch -D went wrong', 'Anything that was once COMMITTED can be found again'), ('Watch out: it is local, and it expires', 'Only your clone has it, entries age out after about 90 days, and uncommitted edits were never in it')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('code', 'git cherry-pick — copy one commit to another branch',
  "$ git log --oneline -1\n1ecd14b fix: default currency to EUR\n$ git switch release/2026.10\nSwitched to branch 'release/2026.10'\nYour branch is up to date with 'origin/release/2026.10'.\n$ git cherry-pick -x 1ecd14b\n[release/2026.10 3d690ff] fix: default currency to EUR\n Date: Thu Sep 17 08:22:26 2026 +0200\n 1 file changed, 1 insertion(+)\n$ git log --oneline -2\n3d690ff fix: default currency to EUR\nc479b91 feat: report the store in /ready\n$ git log -1 --format=%B\nfix: default currency to EUR\n\n(cherry picked from commit 1ecd14bd10ed4f148fec87bd9e69e0a7fe973d8d)",
  [('Means: cherry-pick copies ONE commit onto the current branch', 'Same change, new SHA: 1ecd14b on main becomes 3d690ff on the release'), ('How: switch to the target branch, then cherry-pick <sha>', '-x records where it came from — the audit trail for a back-port'), ('Use when: a fix must reach a release branch without the rest of main', 'The classic hotfix back-port'), ('Avoid: moving whole features between branches this way', 'You get duplicate commits with different SHAs — merge instead'), ('Watch out: it can conflict like a merge', 'Fix the file, git add, git cherry-pick --continue — or --abort')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('code', 'git tag · git describe — name a release',
  '$ git tag -a v1.1.0 -m "PayTrack API 1.1.0"\n$ git tag -n\nv1.1.0          PayTrack API 1.1.0\n$ git push origin v1.1.0\nTo https://github.com/<your-username>/paytrack-api.git\n * [new tag]         v1.1.0 -> v1.1.0\n# ...one more commit lands on main...\n$ git describe --tags\nv1.1.0-1-g32fc9b7\n$ git show v1.1.0 --no-patch\ntag v1.1.0\nTagger: Your Name <you@example.com>\nDate:   Thu Sep 17 08:22:26 2026 +0200\n\nPayTrack API 1.1.0\n\ncommit 4949c99cf69f1aa1c760ce18063c92880f2f1581\nAuthor: Your Name <you@example.com>\nDate:   Thu Sep 17 08:22:26 2026 +0200\n\n    docs: add contributing guide',
  [('Means: a tag is a permanent name for one commit', 'Unlike a branch it never moves — v1.1.0 always means exactly this code'), ('How: tag -a <name> -m "message" — annotated: tagger, date, message', 'A lightweight tag (no -a) is a bare pointer with no audit data'), ('Tags are NOT pushed with your commits', 'git push origin v1.1.0 — or git push origin --tags'), ('describe --tags names any commit from its nearest tag', 'v1.1.0-1-g32fc9b7 = one commit after v1.1.0, at commit 32fc9b7'), ('Avoid: moving or re-using a published tag', 'Someone has already built and deployed from it — cut v1.1.1 instead')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('code', 'git bisect — find the commit that broke it',
  "$ git bisect start\nstatus: waiting for both good and bad commits\n$ git bisect bad\nstatus: waiting for good commit(s), bad commit known\n$ git bisect good v1.0.0\nBisecting: 3 revisions left to test after this (roughly 2 steps)\n[7bfd8d959e5f653ae56caa21fabb5f72a8b3af37] chore: bump flask to 3.0.3\n$ git bisect run python3 test_fee.py\nrunning 'python3' 'test_fee.py'\nok\nBisecting: 1 revision left to test after this (roughly 1 step)\n[ca37b9aca84d73133b3e4630d9f7c508762a2969] feat: fee for GBP cards\nrunning 'python3' 'test_fee.py'\nAssertionError: 46\nBisecting: 0 revisions left to test after this (roughly 0 steps)\n[4f79a0c204e4d74a1ed2417bc369756c88713493] refactor: simplify fee rounding\nrunning 'python3' 'test_fee.py'\nAssertionError: 46\n4f79a0c204e4d74a1ed2417bc369756c88713493 is the first bad commit\nbisect found first bad commit\n$ git bisect reset",
  [('Means: bisect binary-searches history for the breaking commit', 'Seven suspect commits took three tests; a thousand would take about ten'), ('How: start · bad (it is broken now) · good <last good version>', 'Git checks out a commit in the middle; you say good or bad; repeat'), ('bisect run <test> does the answering for you', 'Exit 0 = good · 1–127 = bad · 125 = skip this commit'), ('Use when: "it worked in 1.0.0" and nobody knows what changed', 'Here a harmless-looking refactor changed how the card fee is rounded'), ('Always finish with git bisect reset', 'Otherwise you are left on a detached HEAD somewhere in the past')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('code', 'git clean — delete files Git is not tracking',
  '$ git status -s\n?? build/\n?? scratch.txt\n$ git clean -n\nWould remove scratch.txt\n$ git clean -nd\nWould remove build/\nWould remove scratch.txt\n$ git clean -fd\nRemoving build/\nRemoving scratch.txt\n$ git status -s',
  [('Means: clean deletes untracked files from the disk', 'The opposite of git add — they are removed, not merely ignored'), ('How: ALWAYS -n first (dry run), then -f to really delete', '-d includes directories · -x also deletes ignored files'), ('Use when: build output or scratch files clutter the tree', 'Getting back to exactly what is in the repository'), ('Avoid: git clean -fdx in a project you are working in', '-x also deletes .venv and .env — ignored does not mean unimportant'), ('Watch out: there is no undo', 'Untracked files were never in Git, so even the reflog cannot bring them back')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Real output, captured from a scripted PayTrack repository. Read the terminal top to bottom first, then the '
   'five points in order: what it means, how, when to use it, when not to, what to watch for. The same example, '
   'with more options, is in docs/theory/git-command-guide.md.'}),

 ('section',
  'C',
  'More on Branches and Rebasing',
  "The detail behind today's simple rules",
  ['Choosing a branching approach',
   'Merging in detail · the golden rule',
   'Rebase conflicts, tidying commits, undoing a rebase']),

 ('table',
  'Which approach fits which team?',
  ['Question',
   'GitFlow',
   'GitHub Flow',
   'Trunk-based'],
  [['Do you look after several versions at once (say 2.0 and 3.0)?',
    '✔ Suits you',
    '✗ Not really',
    '✗ Not really'],
   ['Do you release small changes often?',
    '✗ Slow',
    '✔ Yes',
    '✔ Yes'],
   ['Do you have good automatic tests?',
    'Helpful',
    'Needed',
    'Essential'],
   ['How long does a branch usually live?',
    'Weeks',
    'Hours to days',
    'Under a day'],
   ["How hard is combining everyone's work?",
    'Often painful',
    'Usually easy',
    'Very easy']],
  'GOING FURTHER · OPTIONAL',
  {'widths': [4.3,
    1.9,
    1.9,
    1.9],
   'note': ('THIS COURSE USES',
    'GitHub Flow: one short-lived branch per change, reviewed in a pull request, then merged into main.')}),

 ('table', 'Four strategies in detail',
  ['Strategy', 'Branches and rules', 'Use when', 'The cost'],
  [['GitFlow (Driessen, 2010)', 'main, develop, feature/*, release/*, hotfix/*',
    'Versioned releases; several versions supported at once', 'Long-lived branches, merge hell, slowest feedback'],
   ['GitHub Flow', 'main + short-lived branches; PR, CI green, review, deploy on merge',
    'Web services, one production version, continuous delivery', 'Needs genuinely good automated tests'],
   ['GitLab Flow', 'GitHub Flow + environment branches: main → staging → production',
    'Regulated teams that want CD AND a promotion trail', 'Environment branches can drift if misused'],
   ['Trunk-based', 'Commit to trunk daily; branches under 24 h; flags hide unfinished work',
    'The highest delivery performance, with the automation to match', 'Demands strong CI, flags and discipline']],
  'GOING FURTHER · OPTIONAL', {'widths': [2.1, 3.3, 3.1, 2.6],
   'note': ('THE COURSE USES', 'GitHub Flow — because it is the one that fits CI/CD. Driessen himself later '
            'added a note: if you deliver continuously to a web app, use something simpler than GitFlow.')}),

 ('compare',
  'Two teams, two habits',
  'Team A adds its work to main twice a day. Team B works separately for three weeks, then combines everything at once. Same people, same product. Which team has the harder time — and when does the trouble start?',
  ['Two minutes with your neighbour: when exactly does Team B feel the pain?',
   'What would Team B need before it could safely work like Team A?'],
  'Team B feels it on the day it combines three weeks of work: lots of conflicts at once, usually just before a release. To work like Team A it needs good automatic tests and a way to hide unfinished features. Small, frequent changes are easier to combine than big, rare ones.',
  3),

 ('define',
  'Merge',
  'Bringing the changes from one branch into another — usually your finished branch into main — so both sets of work end up together.',
  [('Git does most merges on its own',
    'If people changed different lines or files, there is nothing to decide'),
   ('On GitHub you merge with a button',
    'At the end of a reviewed pull request'),
   ('If two people changed the same line, Git stops and asks',
    'That is a merge conflict — you will resolve one today'),
   ('This course uses "squash and merge"',
    "All your branch's saves go into main as ONE tidy commit")],
  'GOING FURTHER · OPTIONAL'),

 ('code',
  'Merge or rebase — the same branch, two results',
  '''# before: the branch and main have diverged
* f1c7cab (HEAD -> feature/PAY-142, origin/feature/PAY-142) docs: explain readiness
* f7c4490 feat: add readiness probe
| * 6fcdcba (origin/main, origin/HEAD) fix: raise settlement timeout
|/
* 039ad72 (main) feat: add PayTrack API service

# option 1:  git merge origin/main
*   a15f32e Merge remote-tracking branch 'origin/main' into feature/PAY-142
|\\
| * 6fcdcba fix: raise settlement timeout
* | f1c7cab docs: explain readiness
* | f7c4490 feat: add readiness probe
|/
* 039ad72 feat: add PayTrack API service

# option 2:  git rebase origin/main
* a39d691 docs: explain readiness
* 0b25573 feat: add readiness probe
* 6fcdcba fix: raise settlement timeout
* 039ad72 feat: add PayTrack API service''',
  [("Before — main has a commit your branch doesn't",
    'A colleague fixed the settlement timeout while you worked'),
   ('Option 1, merge — adds a joining commit',
    'a15f32e ties the two lines together; your saves keep their IDs'),
   ('Option 2, rebase — moves your saves on top',
    'Same changes, new IDs (0b25573, a39d691) — one straight line'),
   ('The files end up exactly the same',
    'Only the shape of the history is different')],
  {'lang': 'git log --oneline --graph',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.56}),

 ('define',
  'The golden rule of rebasing',
  'Never rebase commits that other people already have.',
  [('Why — rebase replaces commits with new copies',
    'Anyone who downloaded the old ones now has a different history'),
   ('What they see',
    'Duplicate commits and confusing conflicts the next time they pull'),
   ('Safe — your own branch that nobody else uses',
    'Even if you have already pushed it'),
   ('Protection — GitHub can block force-pushes to main',
    'You switch this on in Lab 03, so the mistake becomes impossible')],
  'GOING FURTHER · OPTIONAL'),

 ('code', 'When a rebase stops for a conflict',
  '''$ git rebase origin/main
Rebasing (1/4)
CONFLICT (content): Merge conflict in app/src/config.py
error: could not apply d92986f... feat: raise settlement timeout to 60s
$ git status
interactive rebase in progress; onto 02cf66b
  (fix conflicts and then run "git rebase --continue")
  (use "git rebase --skip" to skip this patch)
  (use "git rebase --abort" to check out the original branch)
$ cat app/src/config.py
<<<<<<< HEAD
TIMEOUT = 45
=======
TIMEOUT = 60
>>>>>>> d92986f (feat: raise settlement timeout to 60s)
$ nano app/src/config.py       # make it correct, delete the markers
$ git add app/src/config.py
$ git rebase --continue
Successfully rebased and updated refs/heads/feature/PAY-150-raise-timeout.''',
  [('Conflicts arrive one commit at a time', '"Rebasing (1/4)": you may resolve the same area more than once'),
   ('HEAD is the OTHER side during a rebase', 'HEAD = main plus what has been replayed so far; the lower half is YOUR commit'),
   ('git add marks it resolved, then --continue', 'Do not run git commit in the middle of a rebase'),
   ('--skip drops this one commit', 'Only when main already contains the same change'),
   ('--abort puts everything back', 'The branch returns exactly to where it was before the rebase')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'The HEAD inversion catches almost everyone: in a merge HEAD is your branch, in a rebase HEAD is '
   'the branch you are rebasing ONTO. Read the label after >>>>>>> — it names your own commit.'}),

 ('code', 'Interactive rebase — tidy the branch before review',
  '''$ git log --oneline
eb5906b fix typo
0f428b6 wip
15d34da feat: add readiness probe
080168c feat: raise settlement timeout to 60s
$ git rebase -i main
# the editor opens with the plan, OLDEST first:
pick 080168c feat: raise settlement timeout to 60s
pick 15d34da feat: add readiness probe
pick 0f428b6 wip
pick eb5906b fix typo
# you edit it, save and close:
pick  080168c feat: raise settlement timeout to 60s
fixup 0f428b6 wip
fixup eb5906b fix typo
pick  15d34da feat: add readiness probe
Successfully rebased and updated refs/heads/feature/PAY-150-raise-timeout.
$ git log --oneline
3dafa34 feat: add readiness probe
51d5488 feat: raise settlement timeout to 60s''',
  [('-i turns the replay into a plan you can edit', 'The list is oldest-first — the reverse of git log'),
   ('pick keeps · reword renames · drop deletes', 'squash melds into the line above and combines the messages'),
   ('fixup melds in and discards the message', 'Here "wip" and "fix typo" join the commit they belong to'),
   ('Move a line to reorder commits', 'Four noisy commits become two that each tell one story'),
   ('Shortcut: git commit --fixup <sha>', 'Later, git rebase -i --autosquash main lines the fixups up for you')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.60,
   'speaker': 'Point out that the editor list runs oldest-first, the opposite of git log — the most common '
   'source of "I squashed the wrong commit". If that happens, the next-but-one slide undoes it.'}),

 ('code', 'Undo a rebase — ORIG_HEAD and the reflog',
  '''$ git rebase origin/main
Successfully rebased and updated refs/heads/feature/PAY-142.
$ git reflog -5
a39d691 HEAD@{0}: rebase (finish): returning to refs/heads/feature/PAY-142
a39d691 HEAD@{1}: rebase (pick): docs: explain readiness
0b25573 HEAD@{2}: rebase (pick): feat: add readiness probe
6fcdcba HEAD@{3}: rebase (start): checkout origin/main
f1c7cab HEAD@{4}: commit: docs: explain readiness
$ git reset --hard ORIG_HEAD
HEAD is now at f1c7cab docs: explain readiness''',
  [('ORIG_HEAD = where the branch was before the rebase', 'git reset --hard ORIG_HEAD undoes the whole rebase in one step'),
   ('The reflog records every move of HEAD', 'The line just below "rebase (start)" is your old branch tip'),
   ('git reset --hard HEAD@{4} does the same', 'Use the reflog once ORIG_HEAD has moved on'),
   ('--hard discards uncommitted edits', 'Commit or stash first'),
   ('Local only, and not for ever', 'The reflog lives in your clone and expires after about 90 days')],
  {'lang': 'bash  ·  real output', 'kicker': 'GOING FURTHER · OPTIONAL', 'split': 0.62,
   'speaker': 'This is the confidence slide: nothing a local rebase does is permanent. Ask the room to read '
   'the reflog bottom-up — the line below "rebase (start)" is the branch as it was.'}),

 ('predict', 'A colleague rebased and force-pushed main',
  'At 11:00 a colleague rebased main to "tidy the history" and force-pushed it. Six people had already '
  'pulled main that morning and have work in progress on top of it. What happens next for them — '
  'and what do you do?',
  ['Predict what each of the six sees on their next git pull.',
   'Then: how do you get main back, and what stops it happening again?'],
  'Their next pull tries to combine the old commits with the rewritten ones: duplicated commits and conflicts '
  'on code nobody changed. Recover by finding the pre-rebase tip in any clone\'s reflog and restoring it with '
  '--force-with-lease. Prevent it with branch protection that blocks force-push — then it cannot recur.', 3),

 ('lab', '03A', 'Git, Going Further — on a practice repository',
  'Run every command from sections B and C on a copy of PayTrack API built to be broken — no GitHub, no Docker, no network.',
  ['Read the history: log, show, blame, and the pickaxe (log -S)',
   'Stash an interruption, commit part of a file with add -p, then amend',
   'Reset three ways — then rescue the "deleted" commit from the reflog',
   'Let git bisect find a hidden bug in three steps, then revert it',
   'Tag a release and cherry-pick a hot-fix onto release/1.0',
   'Merge vs rebase, a rebase conflict, autosquash, undo — and a lease that saves a colleague'],
  'You have watched every advanced Git command work, and fail, where a mistake costs nothing',
  {'kicker': 'GOING FURTHER  ·  HANDS-ON',
   'speaker': 'Lab guide: labs/lab-03-branching-and-collaboration/README-03A-git-going-further.md. Optional and self-paced; about 80 minutes '
   'in eight parts. setup-gym.sh builds the practice repository and rebuilds it in two seconds, so '
   'delegates can break it freely. Demo Part 5 (bisect) or Part 8 (the stale-info rejection) if you have time.'}),

 ('section',
  'D',
  'More on Pull Requests, CI and the Tools',
  'Reviews, CODEOWNERS, testing, Jenkins and security',
  ['Good reviews · CODEOWNERS · the bank angle',
   'Kinds of tests · build automation · version numbers',
   'GitHub Actions in depth · Jenkins · securing the pipeline']),

 ('table',
  'Good reviews — and reviews that only look good',
  ['Do',
   "Don't"],
  [['Keep pull requests small — under about 400 changed lines',
    'Send a huge change nobody can really read'],
   ['Review within a day',
    'Leave a colleague waiting for a week'],
   ['Let tools check the formatting, so people check the logic',
    'Argue about spaces and brackets'],
   ['Ask questions: "What happens if the amount is zero?"',
    'Write "this is wrong."'],
   ['Actually read the change before approving',
    'Click Approve thirty seconds after it opens']],
  'GOING FURTHER · OPTIONAL',
  {'widths': [5.4,
    4.6],
   'first_bold': False}),

 ('code',
  'CODEOWNERS — the right reviewer, automatically',
  '''# The LAST matching rule wins, so order matters.

# Default owners for everything
*                     @paytrack/developers

# The application
/app/                 @paytrack/developers

# Anything that changes how code reaches production
/.github/workflows/   @paytrack/platform @paytrack/security
/k8s/                 @paytrack/platform
/terraform/           @paytrack/platform

# Protect the protection
/.github/CODEOWNERS   @paytrack/platform''',
  [('A simple list: which files → which people',
    'GitHub asks those people to review any change to those files'),
   ('The last matching line wins',
    'Put the general rule first and the specific ones after it'),
   ('Protect the pipeline files most carefully',
    'They control how every change is tested and released'),
   ('Switch it on in the branch protection settings',
    'Tick "Require review from Code Owners"')],
  {'lang': '.github/CODEOWNERS',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.56}),

 ('bank',
  'The pull request IS your change control',
  [('"Prove the author did not approve their own change"',
    'The protection settings plus the pull request record — for every change, in seconds'),
   ('"Prove it was tested"',
    'The test results are attached to the pull request'),
   ('"Prove what went live"',
    'Each release links back to the exact change that was approved'),
   ('Ask for "standard change" status',
    'Change-management rules already allow automated, repeatable changes without a meeting'),
   ('Keep the records',
    "The pipeline's logs are audit evidence — keep them as long as your rules require")],
  {'lead': 'A regulator does not require a meeting. It requires a check that works, happens every time and leaves evidence. A protected pull request does all three.',
   'ref': 'Appendix A §A.3–A.5'}),

 ('bullets',
  'Are we really doing CI? Three questions',
  [('1 · Does everyone add their work to main at least once a day?',
    None),
   ('2 · Does every change run the tests automatically?',
    None),
   ("3 · When the tests fail, is fixing them the team's first job?",
    None),
   ('Three yeses = Continuous Integration',
    'Anything less is "we have a build server"'),
   ('Example: a build server, three-week branches, tests once a night',
    'That fails questions 1 and 2')],
  'GOING FURTHER · OPTIONAL'),

 ('diagram',
  'Different kinds of tests',
  dg.test_pyramid,
  'GOING FURTHER · OPTIONAL',
  {'speaker': 'Unit test: checks one small piece, like the fee calculation. Integration test: checks pieces working together, like the app and its database. End-to-end: clicks through the whole system like a user.'}),

 ('define', 'Build automation',
  'Scripting the transformation of source code into a deployable artefact, so that any person or '
  'machine can run it identically, from a clean checkout, with a single command.',
  [('REPRODUCIBLE — same source, same artefact', 'Pinned dependency versions; pinned base-image digests'),
   ('HERMETIC — depends only on declared inputs', 'Build inside a container, not on whatever is installed'),
   ('FAST — under 10 minutes', 'Layer caching, dependency caching, parallel jobs'),
   ('SELF-TESTING — fails on a defect', 'pytest runs in the same command'),
   ('VERSIONED — every artefact uniquely identified', 'Tag images with the git SHA, never only latest')],
  'GOING FURTHER · OPTIONAL'),

 ('table', 'Versioning: SemVer for humans, the SHA for deployments',
  ['Tag', 'Meaning', 'Use it for'],
  [['MAJOR (2.0.0)', 'A breaking change for consumers', 'Libraries and APIs others depend on'],
   ['MINOR (1.5.0)', 'A backwards-compatible feature', 'Libraries and APIs others depend on'],
   ['PATCH (1.4.3)', 'A backwards-compatible fix', 'Libraries and APIs others depend on'],
   ['paytrack-api:9f3e2a1', 'The immutable commit SHA', '✔ What a deployment manifest references'],
   ['paytrack-api:1.4.2 · :main', 'Moving aliases for humans', 'Finding a build; never for deploying'],
   ['paytrack-api:latest', 'Whatever was pushed last', '✗ Never in a manifest: unpinned, unreproducible']],
  'GOING FURTHER · OPTIONAL', {'widths': [3.0, 3.3, 3.7],
   'note': ('WHY LATEST HURTS', 'It makes rollback ambiguous — "go back to the previous latest" has no '
            'answer. It is an outage waiting for a quiet week.')}),

 ('define',
  'GitHub Actions',
  'The automation built into GitHub. You describe the checks in a small text file inside your project, and GitHub runs them on its own computers every time something happens — for example, when you push.',
  [('Nothing to install',
    'It is part of GitHub'),
   ('It runs on events',
    'A push, a pull request, a schedule, or a button you press'),
   ('Free on public projects',
    'Private projects on the free plan get 2 000 minutes a month'),
   ('The file lives in .github/workflows/',
    'It is code, so it is reviewed like any other change')],
  'GOING FURTHER · OPTIONAL'),

 ('table', 'GitHub Actions — the concepts that matter',
  ['Concept', 'Meaning'],
  [['Runner', 'The machine running a job: GitHub-hosted (ubuntu-24.04) or self-hosted'],
   ['Action', 'A reusable unit: uses: owner/repo@ref. Pin it — @main lets an outsider change your pipeline'],
   ['needs:', 'Declares job dependencies, turning parallel jobs into a graph'],
   ['strategy.matrix', 'Runs one job across combinations, such as two Python versions'],
   ['Secrets', '${{ secrets.NAME }} — encrypted, masked in logs, never given to PRs from forks'],
   ['GITHUB_TOKEN', 'An automatic, short-lived token, scoped by the permissions: block'],
   ['OIDC', 'Swap a short-lived GitHub identity token for cloud credentials — no stored secret at all'],
   ['Required status check', 'Branch protection refuses the merge until this check is green']],
  'GOING FURTHER · OPTIONAL', {'widths': [2.6, 7.4]}),

 ('define',
  'Jenkins',
  'A free automation server that your company installs and runs itself. It does the same job as GitHub Actions — build and test every change — using a file called a Jenkinsfile.',
  [('It runs inside your own network',
    'Sometimes a requirement in a bank'),
   ('Very flexible',
    'Thousands of add-ons, called plugins'),
   ('Someone has to look after it',
    "Updates, backups, security and plugins are your team's job"),
   ('Pipelines are written as code',
    'A Jenkinsfile in the project, reviewed like any other change')],
  'GOING FURTHER · OPTIONAL'),

 ('diagram', 'Jenkins architecture', dg.jenkins_architecture, 'GOING FURTHER · OPTIONAL',
  {'speaker': 'In Lab 05 the pipeline runs on the controller, because a laptop has only one node. Say so '
   'explicitly: that shortcut is for the classroom only — never in a real installation.'}),

 ('code',
  'A Jenkinsfile, line by line',
  '''pipeline {
    agent any                              // where to run
    options { timeout(time: 20, unit: 'MINUTES') }
    environment { IMAGE = "paytrack-api" }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Lint')     { steps { sh 'flake8 src tests' } }
        stage('Test')     { steps { sh 'pytest --junitxml=report.xml' } }
        stage('Build')    { steps { sh 'docker build -t $IMAGE:$GIT_COMMIT .' } }
    }
    post {
        always  { junit 'report.xml' }     // publish results either way
        failure { echo 'Stop the line: fix the build first' }
    }
}''',
  [('pipeline { } wraps everything',
    'Jenkins checks the file is valid before it starts'),
   ('agent any — which computer runs it',
    '"any" means any computer that is free'),
   ('stages — the steps you see on the screen',
    'Checkout · Lint (check the style) · Test · Build'),
   ('post — what to do at the end',
    'always, or only after success or failure'),
   ('The same idea as GitHub Actions',
    'A different file, the same checks')],
  {'lang': 'Jenkinsfile',
   'kicker': 'GOING FURTHER · OPTIONAL',
   'split': 0.6}),

 ('myth',
  'Four things teams say about CI',
  [('We have Jenkins, so we do CI.',
    'CI is a habit: small changes added daily and tested automatically. A tool on its own is not CI.'),
   ('A 45-minute build is fine.',
    'People stop waiting, pile up changes, and push while it is red. Slow checks get ignored.'),
   ('That test is just flaky — run it again.',
    'A test that fails at random teaches everyone to ignore red. Fix it or remove it.'),
   ('We rebuild it specially for the live system.',
    'Then the live system runs something nobody tested. Build once and use it everywhere.')],
  'GOING FURTHER · OPTIONAL'),

 ('bullets', 'Securing the pipeline itself',
  [('Pin third-party Actions to a full commit SHA, not a tag',
    'A tag is mutable: whoever controls it can change what runs with YOUR token'),
   ('Least-privilege permissions: block', 'The default GITHUB_TOKEN scope is broader than you need'),
   ('Short-lived OIDC tokens instead of long-lived secrets',
    'The ideal is a credential that does not exist long enough to be stolen'),
   ('Never expose secrets to pull requests from forks', 'Use pull_request, not pull_request_target'),
   ('CODEOWNERS on .github/workflows/', 'Pipeline changes need the strictest review'),
   ('Ephemeral runners — one job per runner', 'A reused runner leaks state between jobs')],
  'GOING FURTHER · OPTIONAL',
  {'note': ('WHY THIS MATTERS NOW', 'Your CI system holds credentials to everything and executes code by '
            'design. SolarWinds, Codecov and the xz-utils backdoor were all supply-chain compromises.')}),

 ('lab', '04A', 'act — Run CI on Your Laptop, Then Harden It',
  'Run the Lab 04 pipeline locally in seconds, then watch the pipeline-security slides happen for real.',
  ['Install act, verified by checksum, and run lint and tests on your machine',
   'Break the code and see CI fail before you push anything',
   'See a secret masked as *** — then leak in plain sight once it is base64-encoded',
   'Open a "pull request" whose title runs a command, then close the hole',
   'Audit with actionlint and zizmor, and pin every action to a commit SHA',
   'Build one versioned, checksummed artefact and release it from a tag'],
  'A pinned, time-boxed, least-privilege pipeline that the audit tools pass with no findings',
  {'kicker': 'GOING FURTHER  ·  HANDS-ON',
   'speaker': 'Lab guide: labs/lab-04-github-actions-ci/README-04A-act-and-pipeline-security.md. Optional; about 90 minutes; needs Lab 04, '
   'Docker and about 6 GB of disk. Ask delegates to pre-pull catthehacker/ubuntu:act-24.04. Part 5 (script '
   'injection) is the one to demo from the front.'}),

 ('lab', '04B', 'The Same Pipeline on GitLab CI',
  "Open a GitLab account and rebuild Lab 04 in GitLab's language — the controls are the same, the names are not.",
  ['Sign up, verify your identity, turn on 2FA and add your SSH key',
   'Push PayTrack API to a new GitLab project as a second remote',
   'Translate ci.yml into .gitlab-ci.yml: stages, templates, a matrix, test reports',
   'Open a merge request straight from git push',
   'Protect main and switch on "Pipelines must succeed"',
   'Push a broken change and watch the merge get blocked'],
  'A GitLab project where a red pipeline cannot be merged, and a GitHub-to-GitLab translation table',
  {'kicker': 'GOING FURTHER  ·  HANDS-ON',
   'speaker': 'Lab guide: labs/lab-04-github-actions-ci/README-04B-gitlab-ci.md. Optional; about 60 minutes plus account set-up. '
   'GitLab.com may ask new accounts for phone or card verification before pipelines run, so point delegates at '
   'Lab 00 Step 8.3 before the course. Debrief on the side-by-side table, especially required review on Free.'}),

]


# ─────────────────────────────────────────────────────────────────────────────
# Per-lab ADVANCED decks.
#
# The same Going Further material, split so each lab folder ships only the
# slides for its own optional lab. Sections A-C (Git) go with Lab 03A; section D
# (reviews, CI, Jenkins, pipeline security) goes with Labs 04A and 04B. They are
# slices of DAY2_EXTRA, so editing a slide there updates both decks.
#
#   cd _build && python build.py 2      (also writes these two)
#   cd _build && python build.py labs   (only these two)
# ─────────────────────────────────────────────────────────────────────────────

_GIT_ADVANCED = DAY2_EXTRA[1:30]        # sections A, B, C + the Lab 03A slide
_PIPE_ADVANCED = DAY2_EXTRA[30:]        # section D + the Lab 04A and 04B slides

LAB03_ADVANCED = [
  ('title', 2,
   'Lab 03A — Git, Going Further',
   'The advanced Git slides, for after class — everything Lab 03A puts your hands on',
   ['A: more everyday Git — history in depth, stash, restore, revert',
    'B: reset, reflog, cherry-pick, tag, bisect, clean',
    'C: merging, rebasing, conflicts and the golden rule',
    'Optional. Nothing on Day 3 onwards depends on it'],
   'Practise it: labs/lab-03-branching-and-collaboration/README-03A-git-going-further.md'),
] + _GIT_ADVANCED

LAB04_ADVANCED = [
  ('title', 2,
   'Labs 04A and 04B — Pipelines, Going Further',
   'The advanced pipeline slides, for after class — reviews, CI in depth, Jenkins and security',
   ['Good reviews · CODEOWNERS · the change-control argument',
    'Kinds of tests · build automation · version numbers',
    'GitHub Actions in depth · Jenkins · securing the pipeline',
    'Optional. Nothing on Day 3 onwards depends on it'],
   'Practise it: README-04A-act-and-pipeline-security.md and README-04B-gitlab-ci.md'),
] + _PIPE_ADVANCED
