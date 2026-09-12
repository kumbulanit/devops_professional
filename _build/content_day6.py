# -*- coding: utf-8 -*-
"""Day 6 — DevSecOps, Observability, Enterprise DevOps.  Modules 7, 8, 9 + Appendix A."""
import diagrams as dg

DAY6 = [
 ('title', 6, 'DevSecOps, Observability & Enterprise DevOps',
  'Prove it is safe. Prove it is healthy. Then take it home.',
  ['DevSecOps — shifting security into the pipeline',
   'Monitoring, logging and observability · SLOs and error budgets',
   'Enterprise DevOps — governance, DORA, SRE, platform engineering',
   'Labs 17–19 — Security gates · Observability · Capstone and game day'],
  'Today ends with a plan you can act on next Monday'),

 ('section', '1', 'DevSecOps', 'Security as a continuous, automated, shared responsibility',
  ['Why security must move into the pipeline', 'The classes of testing', 'Gating on risk',
   'Secrets', 'Container and Kubernetes hardening']),

 ('diagram', 'The cost curve — and the arithmetic that forces the change', dg.shift_left,
  'MODULE 7 §7.1'),

 ('table', 'The classes of security testing — they are complementary, not alternatives',
  ['Type', 'Examines', 'Finds', 'Misses'],
  [['Secret scanning', 'Repo contents AND history', 'Hard-coded keys, tokens, certificates', 'Already-rotated secrets'],
   ['SAST', 'Your source code, not running', 'Injection, weak crypto, unsafe deserialisation', 'Runtime and config issues'],
   ['SCA', 'Your DEPENDENCIES', 'Known CVEs in libraries, licence violations', 'Bugs in your own code'],
   ['Container scan', 'Image layers: OS + app packages', 'Vulnerable base image, misconfig, leaked secrets', 'Logic flaws'],
   ['IaC scan', 'Terraform, Kubernetes, Dockerfile', 'Privileged containers, public buckets', 'Runtime drift'],
   ['DAST', 'The RUNNING application', 'Auth flaws, real injection, misconfiguration', 'Unreachable surfaces']],
  'MODULE 7 §7.2', {'widths': [2.1, 2.9, 3.6, 2.9],
   'note': ('THE POINT OF THE TABLE', 'In a typical service 70–90 % of the shipped bytes are dependencies. '
            'A pipeline with only SAST is carefully checking the small part.')}),


 ('predict', 'Which gate catches it?',
  'Five things are about to be committed. For each one, name the gate that catches it — and say '
  'whether it should FAIL the build or just warn.',
  ['An AWS access key pasted into a config file',
   'A dependency with a known CVE that has a patched version available',
   'A dependency with a CRITICAL CVE and no fix published anywhere',
   'A Kubernetes manifest with privileged: true',
   'A base image that was fine when built six months ago and now has 40 new CVEs'],
  'Secret scan (FAIL, and rotate first) · SCA (FAIL) · SCA again (WARN — gating on the '
  'unfixable teaches people to bypass the gate) · IaC scan (FAIL) · the scheduled re-scan, which '
  'is why you store SBOMs and rebuild base images on a cadence.', 4),
 ('diagram', 'The secure pipeline — and how to gate it', dg.secure_pipeline, 'MODULE 7 §7.3'),

 ('bullets', 'Secrets — the hierarchy, worst to best',
  [('✗✗✗ Hard-coded in source, or a committed .env', 'In git forever, in every clone and fork'),
   ('✗ Baked into a container image', 'docker history shows every ARG and ENV'),
   ('~ CI/CD platform secrets', 'Encrypted, masked, scoped — an acceptable baseline'),
   ('✓ Sealed Secrets / SOPS', 'Encrypted in git; decryptable only in the target cluster'),
   ('✓✓ External secret manager', 'Vault, cloud KMS, External Secrets Operator'),
   ('✓✓✓ Short-lived dynamic credentials', 'OIDC — a secret that does not exist long enough to steal')],
  'MODULE 7 §7.5',
  {'note': ('IF A SECRET IS COMMITTED', 'ROTATE IT FIRST — public repos are scraped within seconds. '
            'Scrubbing history is cosmetic: it does not reach forks, existing clones or CI caches. '
            'Teams routinely get this backwards and spend two days rewriting history without rotating the key.')}),

 ('lab', '17', 'Shift Security Left',
  'Add every class of gate — then plant real flaws and watch all five block your own merge.',
  ['Scan the repository you have built over five days — gitleaks, bandit, pip-audit, Trivy',
   'PLANT real flaws: AWS keys, command injection, MD5, eval, a vulnerable dependency',
   'Watch five jobs go red and the merge button go grey',
   'Remediate — and discuss why removing the file is NOT enough',
   'Generate an SBOM per build, and store it for re-scanning when new CVEs appear',
   'Replace the plaintext Secret with a SealedSecret that is safe to commit'],
  'A pipeline with secret, SAST, SCA, IaC and image gates you have watched fire — plus an SBOM and sealed secrets'),

 ('section', '2', 'Observability', 'Knowing what your system is doing — and whether users are suffering',
  ['Monitoring vs observability', 'The three pillars', 'RED and USE', 'SLOs and error budgets',
   'Alerting that people do not ignore']),

 ('diagram', 'The three pillars', dg.three_pillars, 'MODULE 8 §8.1'),

 ('table', 'Metrics that matter — pick a framework and use it',
  ['Framework', 'For', 'The metrics'],
  [['RED', 'Request-driven services — use this for PayTrack', 'Rate · Errors · Duration'],
   ['USE', 'Resources: nodes, disks, pools', 'Utilisation · Saturation · Errors'],
   ['Four Golden Signals', 'Google SRE\'s formulation', 'Latency · Traffic · Errors · Saturation'],
   ['BUSINESS metrics', 'Whether the service is doing its JOB', 'Decline rate · value declined · throughput']],
  'MODULE 8 §8.2', {'widths': [2.6, 4.4, 4.0], 'emph': [3],
   'note': ('NEVER AVERAGE A PERCENTILE', 'The mean of ten p95s is not the p95. Use histograms, not '
            'summaries, so Prometheus can compute a true aggregate quantile across pods. This mistake '
            'makes dashboards confidently wrong.')}),

 ('bullets', 'Prometheus — the things that actually catch people out',
  [('It PULLS over HTTP', 'So the scrape is itself a health check — up is a free metric'),
   ('Every unique label COMBINATION is a separate time series', None),
   ('CARDINALITY is the number-one way to destroy a Prometheus',
    'Never label with a user id, request id, card number or full URL with parameters'),
   ('Always use rate() on a counter', 'A raw counter only goes up; rate() also handles restarts'),
   ('sum by (le) BEFORE histogram_quantile', 'Or you get NaN, or a meaningless number'),
   ('Recording rules pre-compute expensive queries', 'Dashboards and alerts then read a cheap series'),
   ('ServiceMonitor = monitoring as code', 'Adding a service to monitoring becomes a pull request')],
  'MODULE 8 §8.3'),


 ('discuss', 'Everything is green and nobody can pay',
  'It is 14:00. Every pod is healthy, latency is normal, there are zero 5xx errors, and every '
  'probe is passing. Your card decline rate has gone from 4 % to 40 %. How long before anyone '
  'notices — and what tells them?',
  ['Which of your current alerts would fire? Be specific.',
   'Who would find out first — you, or a customer on the phone?',
   'What would you have to instrument to catch this in under five minutes?',
   'Which business metric would do the same job for YOUR service?'],
  'No technical alert fires, because nothing is technically wrong. Only a BUSINESS metric — '
  'decline rate, authorisation throughput, value declined — catches this. Every dashboard needs '
  'at least one metric that measures the job, not the machinery.', 5),
 ('diagram', 'SLIs, SLOs and the error budget', dg.error_budget, 'MODULE 8 §8.5'),

 ('bullets', 'Alerting that survives contact with an on-call rota',
  [('Alert on SYMPTOMS, not causes', '"Error ratio > 2 %" beats "CPU > 80 %" — one hurts users, one may not'),
   ('Every alert must be actionable', 'If there is nothing to do, it is a dashboard entry, not a page'),
   ('Every alert needs a runbook link', '03:00 is not the time to reason from first principles'),
   ('Alert on SLO BURN RATE, not raw thresholds', 'Ties urgency to actual budget consumption'),
   ('Multi-window: long window says it is real, short window says it is still happening', None),
   ('Review alerts monthly and DELETE what nobody acted on',
    'Alert fatigue is a safety failure, not an annoyance — 50 pages a night means missing the one that mattered')],
  'MODULE 8 §8.6'),

 ('bank', 'Every technical metric green — and customers cannot pay',
  [('Pods healthy · latency fine · zero 5xx · all probes passing', 'And the decline rate has gone from 4 % to 40 %'),
   ('An upstream scheme link failing closed produces NO technical alert', 'The service is working perfectly. It is refusing everyone'),
   ('paytrack_authorisations_total{status="declined"} / total', 'The single most important number on a card platform'),
   ('"No authorisations for 10 minutes" is a SEV1', 'And no RED-based alert will fire — the service is simply idle'),
   ('Value declined per second turns degraded into £4 200 a minute',
    'Which is the sentence that gets an incident the attention it needs')],
  {'lead': 'Technical metrics tell you the system is unwell. BUSINESS metrics tell you it matters. '
           'Put at least one of each on every dashboard.',
   'ref': 'Lab 18 · Module 8 §8.2'}),

 ('lab', '18', 'Monitoring, Dashboards, Alerts and an Incident',
  'Instrument it, watch it, define what "good" means — then break production and run the incident.',
  ['Install Prometheus, Grafana and Alertmanager; scrape PayTrack via a ServiceMonitor',
   'Write the RED queries in PromQL — plus decline rate and value declined',
   'Build a dashboard AS CODE and import it — dashboards belong in git, not clicked together',
   'Define an SLO and write multi-window burn-rate alerts at 14.4× (page) and 6× (ticket)',
   'INJECT A FAILURE, then detect → triage → diagnose → mitigate → verify → learn',
   'Write the runbook and the blameless post-mortem while it is fresh'],
  'A monitored platform with SLO alerts, a runbook, and one incident worked end to end'),

 ('section', '3', 'Enterprise DevOps', 'Governance, metrics, SRE and platform engineering',
  ['DevOps governance in a regulated bank', 'DORA metrics revisited', 'SRE',
   'Platform engineering', 'Scaling and anti-patterns']),

 ('diagram', 'Segregation of duties — the argument to take to Risk', dg.sod_control,
  'APPENDIX A §A.3'),

 ('table', 'Control objectives — traditional vs DevOps-native',
  ['Control objective', 'Traditional', 'DevOps-native', 'Automatic evidence'],
  [['Segregation of duties', 'A release team deploys', 'PR review; self-approval blocked', 'PR record, protection config'],
   ['Change authorisation', 'Weekly CAB', 'Peer review + automated gates', 'Merge commit, CI run'],
   ['Change testing', 'Manual sign-off', 'Automated suite gating the merge', 'Test results, coverage'],
   ['Vulnerability mgmt', 'Quarterly scan report', 'Every build scanned, risk-tiered gates', 'Scan output, SBOM'],
   ['Access control', 'Standing admin accounts', 'Least-privilege RBAC, short-lived OIDC', 'RBAC in git, token audit'],
   ['Config management', 'A manual CMDB', 'Git is the source of truth', 'plan -detailed-exitcode']],
  'APPENDIX A §A.9', {'widths': [2.6, 2.6, 3.2, 3.1]}),

 ('bullets', 'The two DORAs — and why the collision is useful',
  [('DORA the METRICS', 'DevOps Research and Assessment: deploy frequency, lead time, change failure rate, recovery time'),
   ('DORA the REGULATION', 'EU Digital Operational Resilience Act — applying since 17 January 2025'),
   ('Unrelated origins. Aligned in substance', None),
   ('Change failure rate and recovery time ARE measures of operational resilience',
    'So your DevOps metrics are resilience evidence — a strong card to play with your risk function'),
   ('DORA the regulation also covers ICT THIRD-PARTY risk',
    'Which includes your cloud provider and your CI vendor'),
   ('And incident reporting on regulatory clocks', 'Which is why MTTD and MTTR stop being engineering trivia')],
  'MODULE 9 §9.2 · APPENDIX A §A.2'),

 ('two', 'SRE and platform engineering — what to steal',
  ('SRE', ['Reliability quantified: SLIs, SLOs, error budgets',
           'An error-budget POLICY with agreed consequences',
           'Toil capped at 50 % of an engineer\'s time',
           'Blameless post-mortems with owned actions',
           'Production readiness review before support'], 'teal'),
  ('PLATFORM ENGINEERING', ['The platform is a PRODUCT with users and a roadmap',
                            'Golden paths, not golden cages',
                            'Self-service — a ticket-and-wait platform is ops renamed',
                            'Reduce cognitive load, do not relocate it',
                            'Voluntary adoption is the only honest metric'], 'green'),
  'MODULE 9 §9.3–9.4',
  ('THE TEST FOR EACH', 'SRE without a written error-budget policy is monitoring with extra vocabulary. '
   'A platform teams must be mandated to use is a golden cage, and they will route around it.')),

 ('diagram', 'Platform engineering — the problem it solves', dg.platform_engineering,
  'MODULE 9 §9.4'),

 ('lab', '19', 'Capstone — Verify, Break, Recover, Plan',
  'Prove the whole chain works, run a game day against the clock, then write the plan you take home.',
  ['Run verify-platform.sh — nine layers, every check tied to the lab that produced it',
   'Ship one more change and watch it travel from your editor to a monitored workload',
   'GAME DAY in pairs: one person injects a failure, the other is on call and must not watch',
   'Diagnose using only your dashboards, alerts and runbooks — and record the clock times',
   'Reset, then write your 30-60-90 day plan against your own Lab 01 baseline',
   'Name three anti-patterns you have, and the first step out of each'],
  'A verified platform, a measured MTTR, and a written improvement plan with owners and dates'),


 ('audit', 'What will you actually change?',
  'Before the capstone, commit to one thing. The test is simple: it needs no budget, no new '
  'headcount and no permission from outside your team.',
  ['Name the ONE change you will make in the next 30 days.',
   'Name the number it should move — and where that number comes from today.',
   'Name the person who owns it. (If that is you, say so out loud.)',
   'Name what you will STOP doing to make room for it.',
   'Name the one thing you will ask for that you cannot do alone — and who you will ask.'],
  'Evidence moves risk functions; arguments do not. Pick one low-risk service, run the new way '
  'for a quarter, and bring the DORA numbers back. That is how a standard-change reclassification '
  'gets approved — and how the second team gets permission.', 5),
 ('check', 'Day 6 — check your understanding',
  ['An API key was committed and pushed to a public repo 20 minutes ago. List your actions in order.',
   'Why is failing the build on every MEDIUM finding usually counter-productive? What do you do instead?',
   'Your team gets 60 pages a night. Give four concrete changes, in priority order.',
   'Explain multi-window burn-rate alerting, and why BOTH windows are needed.',
   'A director asks you to publish a DORA league table ranking all 14 teams. What is your response?',
   'Which single practice makes SRE more than a rename of Operations?']),

 ('close', 6, 'Course complete',
  ['Day 1–2: a governed repository where 100 % of changes are reviewed and automatically tested',
   'Day 3–4: a hardened 150 MB image running on a self-healing Kubernetes cluster',
   'Day 5: two environments from one Terraform module, and a GitOps pipeline with auto-rollback',
   'Day 6: five security gates, an SBOM, sealed secrets, SLO alerting and a worked incident',
   'All of it on a laptop, at zero cost, in a git repository you can clone and reproduce'],
  'Start with your Lab 01 constraint, not with the most interesting technology. Pick the one '
  'improvement that needs no budget and no permission outside your team, do it this month, and measure '
  'it. Then ask for ONE service to be reclassified as a standard change and bring back the numbers — '
  'evidence moves risk functions; arguments do not.'),
]
