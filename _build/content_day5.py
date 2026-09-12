# -*- coding: utf-8 -*-
"""Day 5 — Infrastructure as Code + Continuous Delivery.  Modules 5 and 6."""
import diagrams as dg

DAY5 = [
 ('title', 5, 'IaC & Continuous Delivery',
  'Stop doing it by hand — and stop being the person who holds the credentials',
  ['Infrastructure as Code · Terraform · state · drift',
   'Ansible · idempotency · configuration management',
   'Continuous Delivery · deployment strategies · rollback · GitOps',
   'Labs 13–16 — Terraform · Ansible · CD pipeline · Blue-green and canary'],
  'By the end of today, a commit reaches the cluster with nobody typing kubectl'),

 ('section', '1', 'Infrastructure as Code', 'Terraform and Ansible — and where each one belongs',
  ['IaC principles', 'Terraform: plan, apply, state', 'Drift', 'Ansible and idempotency']),

 ('define', 'Infrastructure as Code',
  'Defining and managing infrastructure through versioned, machine-readable definition files that '
  'are applied by automation — so that infrastructure is reviewed, tested, repeatable and auditable '
  'in exactly the way application code is.',
  [('Declarative', 'Describe the END STATE; the tool works out the steps'),
   ('Idempotent', 'Applying the same definition twice changes nothing the second time'),
   ('Versioned', 'Every change reviewed in a PR, with a full history of who and why'),
   ('Reproducible', 'The same definition produces the same environment, every time'),
   ('It kills the SNOWFLAKE', 'The uniquely hand-configured server nobody dares touch or rebuild')],
  'MODULE 5 §5.1'),

 ('diagram', 'The Terraform workflow — and the two things that bite', dg.terraform_flow,
  'MODULE 5 §5.2'),


 ('predict', 'Someone scaled production by hand last night',
  'Your Terraform says 2 replicas. At 23:40 an engineer ran kubectl scale --replicas=5 to get '
  'through an incident, and told nobody. You run terraform plan the next morning.',
  ['What does the plan say?',
   'What happens if you apply it — and is that the right outcome?',
   'How would you have found out WITHOUT running plan by hand?',
   'And how does your organisation find out today?'],
  'The plan shows ~ replicas 5 -> 2, and applying it reverts the manual change — which is '
  'correct, and is exactly why "just this once" SSH fixes are so damaging. Run '
  'terraform plan -detailed-exitcode on a schedule: exit 2 means drift, and you alert on it.', 4),
 ('table', 'Reading a plan — learn these four symbols',
  ['Symbol', 'Meaning', 'What to do'],
  [['+ create', 'A new resource', 'Normal'],
   ['~ update in-place', 'Modified, no replacement', 'Normal — but read what changed'],
   ['-/+ destroy and then create', 'REPLACEMENT', 'STOP. On a database this is data loss'],
   ['- destroy', 'Removed', 'Confirm it is intended']],
  'MODULE 5 §5.2', {'widths': [2.8, 3.4, 3.6], 'emph': [2],
   'note': ('THE PROFESSIONAL WORKFLOW', 'plan runs automatically on every PR and is posted as a comment; '
            'a human reads it; only then does CI run apply on the SAVED plan. Nobody runs '
            'apply -auto-approve from a laptop.')}),

 ('bullets', 'State — the part that causes real incidents',
  [('State is the map from your code to real resources', 'Without it Terraform cannot tell create from update'),
   ('It contains SECRETS IN PLAINTEXT',
    'sensitive = true masks CLI output only. The password is still in the file'),
   ('Never commit it', 'Every clone, every fork, forever'),
   ('Remote backend, encrypted, with LOCKING',
    'Two concurrent applies against one state corrupts it. The lock table is not optional'),
   ('Restrict read access to state as tightly as production', 'Because it is equivalent to production'),
   ('terraform plan -detailed-exitcode on a schedule', 'exit 2 = someone changed production by hand')],
  'MODULE 5 §5.2',
  {'note': ('IN THE LAB', 'You will grep the database password out of terraform.tfstate in plain text — '
            'after declaring the variable sensitive. Delegates remember that one.')}),

 ('two', 'Terraform and Ansible are complements, not competitors',
  ('TERRAFORM', ['→ CREATE cloud, network and cluster resources',
                 '→ Anything with a lifecycle you must track and destroy',
                 '→ Dependency graphs across many APIs',
                 '→ Environments as reusable modules',
                 'Unit of reuse: the MODULE'], 'teal'),
  ('ANSIBLE', ['→ CONFIGURE what is inside a machine',
               '→ Packages, users, files, services',
               '→ Ordered operational runbooks',
               '→ Orchestrating a rolling restart across a fleet',
               'Unit of reuse: the ROLE'], 'green'),
  'MODULE 5 §5.4',
  ('THE HONEST BOUNDARY', 'In a fully containerised platform Ansible\'s classic role shrinks — the '
   'IMAGE is the configuration management. It stays valuable for node baselines, appliances, network '
   'devices, legacy VMs and runbooks. Your delegates will meet both worlds.')),

 ('define', 'Idempotency',
  'An operation that produces the same result whether applied once or many times. In Ansible it is '
  'the property that makes a playbook safe to re-run at any moment — and it is measurable.',
  [('First run: ok=9 changed=7', 'The playbook converged the host'),
   ('SECOND RUN: ok=9  changed=0', 'THAT is the definition. Nothing needed doing'),
   ('changed on every run means a raw command or shell task',
    'Fix it with a module, or creates: / changed_when:'),
   ('--check --diff is Ansible\'s dry run', 'The equivalent of terraform plan'),
   ('no_log: true on any task handling a secret', 'Or it lands in the CI log store forever')],
  'MODULE 5 §5.3'),

 ('lab', '13 + 14', 'Terraform · Ansible',
  'Everything you built by hand yesterday becomes reviewed, versioned, reproducible code.',
  ['Write a reusable Terraform module and instantiate it TWICE — prod and staging',
   'Pin providers; commit the lock file; pin the kubeconfig context explicitly',
   'Read a plan properly, then apply the SAVED plan',
   'Grep the password out of the state file — and discuss what that means',
   'Scale a deployment by hand, run plan, watch Terraform DETECT the drift and revert it',
   'Ansible: a baseline role and an app role — and prove changed=0 on the second run'],
  'Two environments from one reviewed module, plus idempotent configuration management'),

 ('section', '2', 'Continuous Delivery', 'From a commit to production, safely',
  ['Delivery vs Deployment', 'Deployment strategies', 'Rollback', 'GitOps']),

 ('two', 'Continuous Delivery vs Continuous Deployment',
  ('CONTINUOUS DELIVERY', ['Every change is always in a RELEASABLE state',
                           'Any passing version COULD go to production at any moment',
                           'A human decides WHEN — a business decision',
                           'This is a CAPABILITY'], 'teal'),
  ('CONTINUOUS DEPLOYMENT', ['Every change that passes every gate IS deployed',
                             'No human in the loop',
                             'The pipeline is the only gate',
                             'This is a POLICY CHOICE'], 'green'),
  'MODULE 6 §6.1',
  ('FOR A REGULATED BANK', 'Achieving Continuous Delivery and deliberately declining Continuous '
   'Deployment is a legitimate, mature position — not a failure. But you cannot choose the second '
   'without first having the first.')),

 ('diagram', 'Three deployment strategies', dg.deployment_strategies, 'MODULE 6 §6.3'),

 ('table', 'Choosing a strategy',
  ['Strategy', 'Downtime', 'Extra capacity', 'Rollback speed', 'Risk exposure'],
  [['Recreate', '✗ Yes', 'None', 'Slow — redeploy old', 'All users, immediately'],
   ['Rolling', 'No', '~ +1 pod', 'Minutes — reverse the roll', 'Grows gradually'],
   ['Blue-Green', 'No', '2× at cut-over', '✔ Instant — flip back', 'All users at once, but reversible'],
   ['Canary', 'No', '+ small', 'Fast — shift weight back', '✔ Smallest — a few % of users'],
   ['Shadow', 'No', '2× compute', 'N/A — no user traffic', '✔ Zero — responses discarded']],
  'MODULE 6 §6.3', {'widths': [2.0, 1.7, 2.2, 2.8, 2.8],
   'note': ('THE DECIDING QUESTION', 'Can the two versions coexist against the same database schema? '
            'If not, no deployment strategy saves you — fix the migration first with expand/contract.')}),

 ('bullets', 'Database changes — the part that breaks "we do continuous delivery"',
  [('Code rolls back in seconds. DATA DOES NOT', None),
   ('EXPAND / CONTRACT is the only safe pattern',
    'Three backwards-compatible releases instead of one breaking change'),
   ('Release 1 — EXPAND', 'Add the new nullable column. Old code is unaffected'),
   ('Release 2 — MIGRATE', 'Deploy code that writes both and reads the new one. Backfill'),
   ('Release 3 — CONTRACT', 'Only once no rollback target needs the old column: drop it'),
   ('Never rename or drop in the same release that stops using something', 'Wait a release'),
   ('During a rolling update, N and N+1 are BOTH live', 'Both must work against the schema simultaneously')],
  'MODULE 6 §6.6',
  {'note': ('TEST AT PRODUCTION SCALE', 'ALTER TABLE on 200 million rows behaves nothing like it does on '
            'your laptop. And the first irreversible migration is your point of no return — know where it is.')}),

 ('table', 'Rollback — five methods, measured',
  ['Method', 'Typical time', 'Scope', 'Note'],
  [['Feature flag off', '✔ Instant', 'One feature', 'The fastest rollback that exists. No deployment at all'],
   ['Blue-green selector flip', '< 1 second', 'All traffic', 'The alternative is already running and warm'],
   ['Canary abort', '< 5 seconds', 'Only the canary share', 'Smallest blast radius throughout'],
   ['kubectl rollout undo', '20–60 seconds', 'The Deployment', 'The old ReplicaSet still exists at desired 0'],
   ['git revert + pipeline', '3–10 minutes', 'Everything', '✔ Slowest but most auditable — the prod default']],
  'MODULE 6 §6.4', {'widths': [2.6, 2.0, 2.3, 4.1],
   'note': ('ROLL BACK FIRST, DIAGNOSE SECOND', 'The incident is the priority; root cause is important but '
            'not urgent. And an untested rollback is a hope, not a plan — rehearse it in a game day.')}),


 ('compare', 'Who holds the keys to production?',
  'Model A: your CI pipeline holds a kubeconfig with deploy rights and runs kubectl apply. '
  'Model B: CI commits a new image tag to git, and an agent inside the cluster pulls it. '
  'Same outcome. Which would you rather defend to an auditor, and why?',
  ['Two minutes in pairs. List what an attacker gains by compromising the CI system in each model.',
   'Then: in which model can you answer "what is running in production?" without cluster access?'],
  'In Model A, compromising CI gives production write access. In Model B there is no external '
  'credential to steal, drift is corrected continuously, and git history is the change record. '
  'Pull beats push on both security and evidence.', 3),
 ('diagram', 'GitOps — and why a bank should care', dg.gitops, 'MODULE 6 §6.7'),

 ('lab', '15 + 16', 'CD Pipeline to Kubernetes · Deployment Strategies',
  'Join everything from days 1–5 into one automated path, then move traffic and watch it happen.',
  ['Build the pipeline: test → build once → scan → publish → PROMOTE by committing the new tag',
   'Run an in-cluster reconciler that pulls the change and applies it — the GitOps mechanism, visible',
   'Merge a real change and watch it reach the cluster with NO ONE running kubectl',
   'Deploy a broken image and watch the reconciler ROLL BACK automatically',
   'Blue-green: patch one Service selector and watch the banner flip blue → green in the browser',
   'Canary: sample 100 requests and measure the 90/10 split, then promote progressively'],
  'A complete GitOps delivery pipeline, plus working blue-green and canary you can see'),

 ('bank', 'Why pull-based GitOps is the stronger control',
  [('No human and no external system holds production write access',
    'The credential never leaves the cluster. Compare with a CI server holding a kubeconfig'),
   ('Git history IS the deployment record',
    'Commit, approver, image digest, pipeline run — generated, not typed into a ticket afterwards'),
   ('Drift is corrected continuously, not discovered at audit',
    'The agent reconciles; a manual console change is reverted and visible'),
   ('Rollback is git revert', 'Same review, same audit trail, same mechanism as any other change'),
   ('Deployment becomes a STANDARD CHANGE candidate',
    'Repeatable, well-understood, automated — exactly the ITIL definition')],
  {'lead': 'The question an auditor asks is not "how fast do you deploy?" but "who could change '
           'production, and how would you know?" GitOps has a better answer than any manual process.',
   'ref': 'Appendix A §A.3–A.5 · Lab 15'}),

 ('check', 'Day 5 — check your understanding',
  ['Your team applies Terraform from laptops with -auto-approve. Name three risks and describe '
   'the target workflow.',
   'A plan shows -/+ replace on a production database. What do you do next?',
   'An Ansible playbook reports changed=6 on every run. What is wrong, and how do you fix it?',
   'You must rename a database column with zero downtime. Describe the releases.',
   'Blue-green gives instant rollback. Name three things it does NOT roll back.']),

 ('close', 5, 'Day 5 complete',
  ['Two environments provisioned from one reviewed Terraform module, with drift detection proven',
   'Idempotent Ansible roles — changed=0 on the second run',
   'A GitOps pipeline: commit → test → build once → scan → promote → reconcile → verify',
   'Automatic rollback on a failed deployment, with no human involved',
   'Working blue-green and canary, with the traffic split visible in a browser'],
  'Day 6 makes the pipeline prove it is safe, and makes the platform prove it is healthy. Five security '
  'gates you will watch block your own merge, an SBOM, secrets encrypted into git — then Prometheus, '
  'Grafana, SLO burn-rate alerts, a real incident, and the capstone.'),
]
