# -*- coding: utf-8 -*-
"""Day 5 — Infrastructure as Code + Continuous Delivery.  Modules 5 and 6.

Theory-first edition: mostly theory with exercises and two live demos; Labs 13–16 are
started together at the end of the session and finished after class.
"""
import diagrams as dg

DAY5 = [
 ('title', 5, 'IaC & Continuous Delivery',
  'Stop doing it by hand — and stop being the person who holds the credentials',
  ['Infrastructure as Code principles · Terraform: plan, state, drift, modules',
   'Ansible: inventory, playbooks, roles, idempotency, Vault',
   'Continuous Delivery · deployment strategies · rollback · database changes · GitOps',
   'After class — Labs 13–16: Terraform · Ansible · CD pipeline · blue-green and canary'],
  'By the end of the labs, a commit reaches the cluster with nobody typing kubectl'),

 ('agenda', 'Day 5 at a glance',
  [('theory', 'IaC principles: declarative, idempotent, immutable · snowflakes and drift'),
   ('theory', 'Terraform: blocks, the workflow, reading a plan, state, variables, modules'),
   ('exercise', 'PREDICT — someone scaled production by hand last night'),
   ('theory', 'Ansible: agentless, inventory, playbooks, idempotency, roles, Vault'),
   ('break', 'Break · 15 minutes'),
   ('theory', 'Continuous Delivery vs Deployment · the pipeline · environments'),
   ('theory', 'Rolling, blue-green, canary · rollback · expand/contract · artefacts'),
   ('demo', 'A blue-green cut-over in one line'),
   ('exercise', 'COMPARE — who holds the keys to production?  ·  GitOps'),
   ('practical', 'Start Lab 13 together: the module, the plan, the drift'),
   ('after', 'Finish Labs 13–16 · Lab 15 is core — Labs 17 and 19 build on it')],
  'TODAY', {'speaker': 'Day 5 is the densest day. If time is short, teach Lab 16 as the demo only — but never '
            'let anyone skip Lab 15: Lab 17 and the capstone build on its pipeline.'}),

 ('bullets', 'What today gives you',
  [('Why "infrastructure as code" is a control, not a convenience', 'Reviewed, versioned, reproducible, auditable'),
   ('Terraform well enough to read a plan and spot the dangerous line', 'And to treat state as the sensitive file it is'),
   ('Ansible playbooks you can prove are idempotent', 'changed=0 on the second run'),
   ('The difference between Continuous Delivery and Continuous Deployment', 'And why a bank may legitimately choose only the first'),
   ('A way to choose a deployment strategy — and a rollback that works', 'Including the database, where most plans fail'),
   ('GitOps, and why pull beats push for security and evidence', None)],
  'TODAY'),

 ('section', '1', 'Infrastructure as Code', 'Principles before tools',
  ['What IaC is', 'Snowflakes and drift', 'The principles', 'Declarative vs imperative',
   'Mutable vs immutable']),

 ('define', 'Infrastructure as Code',
  'Defining and managing infrastructure — networks, machines, clusters, load balancers, DNS, policy — in '
  'machine-readable definition files that are version-controlled and applied by automation, rather than '
  'through manual configuration or interactive tools.',
  [('The key phrase is VERSION-CONTROLLED', 'A script that builds a server is automation; a reviewed, versioned definition is IaC'),
   ('The repository is the source of truth', 'And a difference from reality is detectable — drift'),
   ('Reviewed like application code', 'Every change is a pull request, with the plan attached'),
   ('It kills the SNOWFLAKE', 'The uniquely hand-configured server nobody dares patch or rebuild')],
  'MODULE 5 §5.1'),

 ('two', 'Without IaC, and with it',
  ('WITHOUT', ['A wiki page: "How to build prod" — last edited years ago, wrong',
               'Manual console clicks',
               '"Ask Thabo — he built it"',
               'Rebuild time: three days, if ever',
               '✗ Dev ≠ staging ≠ production, and no audit trail'], 'red'),
  ('WITH', ['terraform/ and ansible/ in git',
            'Every change reviewed in a pull request, the plan attached',
            'Applied only by the pipeline',
            'Rebuild time: one apply',
            '✔ Same modules, different variables — git history is the audit trail'], 'green'),
  'MODULE 5 §5.1',
  ('TWO DEFINITIONS', 'SNOWFLAKE: a server whose configuration is unique, undocumented and unreproducible. '
   'DRIFT: the gradual divergence of reality from its definition — manual changes, failed runs, emergency fixes.')),

 ('table', 'The principles of Infrastructure as Code',
  ['Principle', 'Definition', 'Why it matters'],
  [['Declarative over imperative', 'Describe the desired END STATE, not the steps', 'The tool computes the difference; one file creates or updates'],
   ['Idempotency', 'Applying N times gives the same result as once', 'Safe to re-run after a partial failure'],
   ['Immutable infrastructure', 'Never modify a running server — replace it', 'Drift becomes impossible'],
   ['Version control everything', 'Definitions live in git, changed by pull request', 'Review, audit, blame, revert'],
   ['Reproducibility', 'Same inputs → same infrastructure', 'Comparable environments; recoverable disasters'],
   ['Composition and reuse', 'Modules and roles with inputs and outputs', 'One reviewed network module, used ten times'],
   ['Test infrastructure code', 'Validate, lint, plan, policy-check, integration-test', 'Its bugs are outages']],
  'MODULE 5 §5.1', {'widths': [2.6, 3.8, 3.8]}),

 ('code', 'Imperative (how) vs declarative (what)',
  '''# IMPERATIVE - you own every guard and edge case
if ! id appuser; then useradd appuser; fi
mkdir -p /opt/app && chown appuser /opt/app
docker run -d --name paytrack-api paytrack-api:1.4.2

# DECLARATIVE - describe the end state
resource "docker_container" "app" {
  name    = "paytrack-api"
  image   = "paytrack-api:1.4.2"
  restart = "unless-stopped"
}''',
  [('Imperative re-runs are unsafe', 'Unless you wrote every guard correctly — run docker run twice and it fails'),
   ('Declarative re-runs are safe by construction', 'The tool reads current state and does only what is missing'),
   ('One file for create AND update', 'Change the image tag and the tool computes the difference'),
   ('Ansible sits in between', 'Its syntax is a list of steps, but each module is declarative: state: present')],
  {'lang': 'bash  ·  HCL', 'kicker': 'MODULE 5 §5.1', 'split': 0.56}),

 ('table', 'Mutable ("pets") vs immutable ("cattle")',
  ['', 'Mutable', 'Immutable'],
  [['How you update', 'SSH in, patch, restart', 'Build a new image, replace, delete the old'],
   ['Drift', 'Accumulates', 'Impossible — nothing is ever modified'],
   ['Rollback', 'Undo the change, and hope', 'Redeploy the previous artefact'],
   ['Debugging', 'Log in and poke around', 'Reproduce from the definition'],
   ['Fits', 'Long-lived stateful hosts', '✔ Containers, Kubernetes, cloud instances']],
  'MODULE 5 §5.1', {'widths': [2.2, 3.6, 4.4],
   'note': ('WHY THIS ORDER', 'Containers made immutable infrastructure the default — which is why days 3 and 4 '
            'came before this module. Terraform PROVISIONS (makes things exist); Ansible CONFIGURES (makes them correct inside).')}),

 ('section', '2', 'Terraform', 'Plan, apply, and the most dangerous file you own',
  ['Blocks and providers', 'The workflow', 'Reading a plan', 'State and drift', 'Variables and modules']),

 ('define', 'Terraform',
  'An IaC tool that uses a declarative language (HCL) and a plugin architecture of PROVIDERS to create, '
  'update and destroy infrastructure, tracking what it manages in a STATE file.',
  [('Providers talk to APIs', 'docker, kubernetes, aws, azurerm — thousands of them'),
   ('It builds a dependency graph', 'Things are created and destroyed in the right order, in parallel where possible'),
   ('The licence changed in 2023 (BUSL)', 'Free for this course and almost all internal enterprise use'),
   ('OpenTofu is the open-source fork', 'Linux Foundation, command-compatible — every Lab 13 command works with tofu')],
  'MODULE 5 §5.2'),

 ('table', 'Terraform\'s building blocks',
  ['Block', 'Purpose', 'Example'],
  [['terraform { }', 'Required versions, required providers, the backend', 'Pin everything'],
   ['provider "x" { }', 'Configures a plugin that talks to an API', 'kubernetes, docker'],
   ['resource "type" "name" { }', 'A thing Terraform CREATES and OWNS', 'kubernetes_deployment.api'],
   ['data "type" "name" { }', 'READS something Terraform does not own', 'An existing image or network'],
   ['variable "name" { }', 'A typed input, with default and validation', 'replica_count'],
   ['output "name" { }', 'A value exposed after apply, and to parent modules', 'The service URL'],
   ['locals { }', 'Named intermediate expressions', 'local.common_labels'],
   ['module "name" { }', 'A reusable group of resources', 'module.paytrack_prod']],
  'MODULE 5 §5.2', {'widths': [3.0, 4.2, 3.0]}),

 ('diagram', 'The Terraform workflow — and the two things that bite', dg.terraform_flow,
  'MODULE 5 §5.2',
  {'speaker': 'plan -out=tfplan then apply tfplan: the apply executes EXACTLY the plan that was reviewed, with no '
   're-evaluation. That is what makes the plan a meaningful approval artefact.'}),

 ('table', 'Reading a plan — learn these four symbols',
  ['Symbol', 'Meaning', 'What to do'],
  [['+ create', 'A new resource', 'Normal'],
   ['~ update in-place', 'Modified, no replacement', 'Normal — but read what changed'],
   ['-/+ destroy and then create', 'REPLACEMENT', 'STOP. On a database this is data loss'],
   ['- destroy', 'Removed', 'Confirm it is intended']],
  'MODULE 5 §5.2', {'widths': [2.8, 3.4, 3.6], 'emph': [2],
   'note': ('THE PROFESSIONAL WORKFLOW', 'plan runs automatically on every PR and is posted as a comment; '
            'a human reads it; only then does CI run apply on the SAVED plan. Nobody runs '
            'apply -auto-approve from a laptop against production.')}),

 ('predict', 'Someone scaled production by hand last night',
  'Your Terraform says 2 replicas. At 23:40 an engineer ran kubectl scale --replicas=5 to get '
  'through an incident, and told nobody. You run terraform plan the next morning.',
  ['What does the plan say?',
   'What happens if you apply it — and is that the right outcome?',
   'How would you have found out WITHOUT running plan by hand?',
   'And how does your organisation find out today?'],
  'The plan shows ~ replicas = 5 -> 2, and applying it reverts the manual change — which is '
  'correct, and is exactly why "just this once" fixes are so damaging. Run '
  'terraform plan -detailed-exitcode on a schedule: exit 2 means drift, and you alert on it.', 4),

 ('code', 'What drift looks like',
  '''$ kubectl scale deployment/paytrack-api -n paytrack-prod --replicas=5
$ terraform plan

  # module.paytrack_prod.kubernetes_deployment.api will be updated in-place
  ~ resource "kubernetes_deployment" "api" {
      ~ replicas = 5 -> 2
    }

Plan: 0 to add, 1 to change, 0 to destroy.

$ terraform plan -detailed-exitcode; echo "exit=$?"
exit=2''',
  [('Terraform refreshes before it plans', 'It reads reality, finds 5, and compares with the code\'s 2'),
   ('~ means update in place', 'No replacement — safe to apply'),
   ('-detailed-exitcode', '0 = no changes · 1 = error · 2 = non-empty plan'),
   ('Schedule it and alert on exit 2', 'You find out within the hour, not at the audit')],
  {'lang': 'bash', 'kicker': 'LAB 13 · DRIFT', 'split': 0.60}),

 ('bullets', 'State — the part that causes real incidents',
  [('State is the map from your code to real resources', 'Without it Terraform cannot tell create from update'),
   ('Never edit it by hand', 'Use terraform state mv, state rm, and import'),
   ('It contains SECRETS IN PLAINTEXT', 'sensitive = true masks CLI output only. The password is still in the file'),
   ('Never commit it', 'Every clone, every fork, forever'),
   ('Remote backend, encrypted, with LOCKING', 'Two concurrent applies against one state corrupt it'),
   ('Restrict read access to state as tightly as production', 'Because reading it is close to reading production')],
  'MODULE 5 §5.2',
  {'note': ('IN THE LAB', 'You will grep the database password out of terraform.tfstate in plain text — '
            'after declaring the variable sensitive. Delegates remember that one.')}),

 ('two', 'Local state and remote state',
  ('LOCAL — ./terraform.tfstate', ['✗ One laptop is the source of truth',
                                   '✗ No locking',
                                   '✗ Secrets on a laptop disk',
                                   '✗ Lost laptop = lost control of the infrastructure',
                                   '→ Fine for learning in Lab 13'], 'red'),
  ('REMOTE — a backend', ['✔ Shared by the team and the pipeline',
                          '✔ Locked during every apply',
                          '✔ Versioned — recover a previous state',
                          '✔ Encrypted at rest, access-controlled, auditable',
                          '→ S3 + DynamoDB, Azure Storage, GCS, Postgres, Terraform Cloud'], 'green'),
  'MODULE 5 §5.2'),

 ('code', 'Variables, validation and outputs',
  '''variable "replica_count" {
  description = "Number of PayTrack API replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 20
    error_message = "replica_count must be between 1 and 20."
  }
}

variable "db_password" {
  type      = string
  sensitive = true      # masks CLI output - NOT the state file
}

output "app_url" {
  value = "http://paytrack.localhost"
}''',
  [('Typed inputs with validation', 'A bad value fails at plan time, not in production'),
   ('sensitive = true', 'Hides the value in output — it is still in plain text in state'),
   ('Precedence, lowest → highest', 'default · terraform.tfvars · *.auto.tfvars · -var-file · -var'),
   ('TF_VAR_name environment variables', 'How a pipeline passes a secret without writing it to a file')],
  {'lang': 'variables.tf · outputs.tf', 'kicker': 'MODULE 5 §5.2', 'split': 0.58}),

 ('code', 'Modules — one definition, two environments',
  '''terraform/
├── main.tf                  # the ROOT module
├── variables.tf
└── modules/
    └── paytrack-app/        # a child module
        ├── main.tf
        ├── variables.tf     # its inputs
        └── outputs.tf       # its outputs

module "paytrack_prod" {
  source        = "./modules/paytrack-app"
  environment   = "prod"
  replica_count = 3
}
module "paytrack_staging" {
  source        = "./modules/paytrack-app"
  environment   = "staging"
  replica_count = 1
}''',
  [('One reviewed definition', 'Two environments that cannot silently diverge'),
   ('Differences are only variables', 'Never hard-code an environment name inside a module'),
   ('Version shared modules', 'source = "git::…?ref=v1.2.0" for anything used across teams'),
   ('Pin required_version and required_providers', 'And commit .terraform.lock.hcl')],
  {'lang': 'terraform/', 'kicker': 'MODULE 5 §5.2 · LAB 13', 'split': 0.54}),

 ('table', 'Meta-arguments worth knowing',
  ['Argument', 'Purpose'],
  [['count = 3', 'N copies, indexed [0], [1]… — removing one re-indexes and can destroy the WRONG resource'],
   ['for_each = toset([...])', '✔ One per stable key — prefer it to count'],
   ['depends_on', 'Explicit ordering when Terraform cannot infer it'],
   ['lifecycle { prevent_destroy = true }', 'Refuse to destroy — put it on databases'],
   ['lifecycle { create_before_destroy = true }', 'Build the replacement first, avoiding downtime'],
   ['lifecycle { ignore_changes = [tags] }', 'Tolerate out-of-band changes to named attributes']],
  'MODULE 5 §5.2', {'widths': [4.0, 6.0]}),

 ('section', '3', 'Ansible', 'Configuration management, agentless and idempotent',
  ['Agentless, and why it matters', 'Building blocks and inventory', 'An annotated playbook',
   'Proving idempotency', 'Roles and Vault']),

 ('define', 'Ansible',
  'An agentless configuration-management and automation tool that connects to managed nodes over SSH, pushes '
  'small programs called MODULES, runs them to bring each node to a described state, and removes them.',
  [('Needs only SSH and Python on the target', 'Already present on Ubuntu — nothing to install or patch'),
   ('The control node PUSHES on demand', 'No master server, no agent bootstrap problem'),
   ('Modules are idempotent by design', 'state: present, not "install"'),
   ('The trade-off', 'Pull-based tools self-correct drift continuously; Ansible corrects it when it runs — so schedule it or run it from CI')],
  'MODULE 5 §5.3'),

 ('table', 'Ansible\'s building blocks',
  ['Concept', 'Definition'],
  [['Control node', 'The machine you run ansible-playbook from'],
   ['Managed node', 'A host being configured — needs SSH and Python, no agent'],
   ['Inventory', 'The list of managed nodes, in groups, with variables — static or dynamic'],
   ['Module', 'A unit of work: apt, copy, template, service, user — idempotent by design'],
   ['Task / play / playbook', 'One module call / hosts mapped to tasks / a YAML file of plays'],
   ['Handler', 'A task that runs only when NOTIFIED, and only once, at the end of the play'],
   ['Role', 'A standard directory packaging tasks, handlers, templates, files and defaults'],
   ['Facts', 'Data gathered from the target: OS, IP addresses, memory, CPU'],
   ['Vault', 'Built-in encryption for secrets stored in the repository']],
  'MODULE 5 §5.3', {'widths': [2.8, 7.2]}),

 ('code', 'An inventory',
  '''# inventory/hosts.ini
[web]
web1 ansible_host=192.168.56.11
web2 ansible_host=192.168.56.12

[db]
db1 ansible_host=192.168.56.21

[production:children]
web
db

[all:vars]
ansible_user=ubuntu
ansible_python_interpreter=/usr/bin/python3''',
  [('Groups', 'web and db — plays target groups, not individual hosts'),
   ('Groups of groups', 'production:children contains both'),
   ('Variables at any level', 'all:vars, group_vars/, host_vars/'),
   ('Dynamic inventory', 'A plugin queries the cloud or the Docker API for the live host list — essential with autoscaling')],
  {'lang': 'inventory/hosts.ini', 'kicker': 'MODULE 5 §5.3', 'split': 0.50}),

 ('code', 'An annotated playbook',
  '''- name: Baseline for PayTrack API hosts
  hosts: web
  become: true
  tasks:
    - name: Ensure required packages are present
      ansible.builtin.apt:
        name: [curl, jq, ca-certificates]
        state: present              # desired state, not "install"
        update_cache: true
        cache_valid_time: 3600

    - name: Render the application config
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/paytrack/app.conf
        mode: "0640"
      notify: Restart paytrack      # only if this task CHANGED

  handlers:
    - name: Restart paytrack
      ansible.builtin.service:
        name: paytrack
        state: restarted''',
  [('hosts and become', 'Which group, and escalate with sudo'),
   ('ansible.builtin.apt', 'Fully-qualified module names — best practice'),
   ('state: present', 'Second run: "ok", not "changed"'),
   ('notify → handler', 'Restart only when config actually changed — once, at the end of the play')],
  {'lang': 'playbook.yml', 'kicker': 'MODULE 5 §5.3', 'split': 0.60}),

 ('define', 'Idempotency',
  'An operation that produces the same result whether applied once or many times. In Ansible it is '
  'the property that makes a playbook safe to re-run at any moment — and it is measurable.',
  [('First run: ok=9 changed=7', 'The playbook converged the host'),
   ('SECOND RUN: ok=9 changed=0', 'THAT is the definition. Nothing needed doing'),
   ('changed on every run means a raw command or shell task', 'Fix it with a module, or creates: / changed_when:'),
   ('--check --diff is Ansible\'s dry run', 'The equivalent of terraform plan'),
   ('no_log: true on any task handling a secret', 'Or it lands in the CI log store forever')],
  'MODULE 5 §5.3'),

 ('code', 'Proving it, and fixing a task that always changes',
  '''PLAY RECAP  (first run)
web1 : ok=9  changed=7  unreachable=0  failed=0

PLAY RECAP  (second run)
web1 : ok=9  changed=0  unreachable=0  failed=0

# A raw command reports "changed" every time...
- name: Initialise the database schema
  ansible.builtin.command: /opt/paytrack/migrate.sh
  args:
    creates: /var/lib/paytrack/.migrated   # ...unless told when to skip''',
  [('changed=0 on the second run', 'The proof you show an auditor that the baseline is enforced, not drifting'),
   ('command and shell cannot know what they did', 'So they always report changed'),
   ('creates: and removes:', 'Skip the task when a file already exists or is already gone'),
   ('changed_when:', 'Decide from the command\'s output whether anything changed')],
  {'lang': 'ansible-playbook output  ·  YAML', 'kicker': 'LAB 14', 'split': 0.58}),

 ('table', 'Roles, Vault and the flags you will use',
  ['Item', 'What it is for'],
  [['roles/<name>/defaults/main.yml', 'Lowest-precedence variables — the role\'s documented public interface'],
   ['roles/<name>/tasks · handlers · templates · files', 'The work, the restarts, the Jinja2 templates, static files'],
   ['ansible-vault encrypt group_vars/production/secrets.yml', 'Encrypt a file so it is safe to commit'],
   ['--ask-vault-pass · --vault-password-file', 'The password comes from OUTSIDE git — a CI secret or a key manager'],
   ['--check --diff', 'Dry run, showing file-content differences'],
   ['--limit web1 · --tags deploy', 'A subset of hosts · only tagged tasks'],
   ['ansible-lint · --syntax-check', 'Catch bad practice and broken YAML before a host sees it']],
  'MODULE 5 §5.3', {'widths': [4.6, 5.4]}),

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
   'devices, legacy VMs and runbooks. You will meet both worlds.')),

 ('flow', 'Terraform and Ansible together — the reference pipeline',
  [('git push to terraform/ and ansible/', 'Both reviewed like application code'),
   ('CI: terraform fmt, validate, plan', 'The plan is posted to the pull request'),
   ('A human reviews the plan', 'Looking for -/+ replace and unexpected destroys'),
   ('Approved: the pipeline applies the saved plan', 'Networks, machines, clusters now exist'),
   ('terraform output -json becomes the inventory', 'No hand-maintained host list'),
   ('ansible-playbook site.yml configures the machines', 'Converged — and changed=0 on a re-run'),
   ('A scheduled terraform plan checks for drift', 'A non-empty plan alerts the platform team')],
  'MODULE 5 §5.4'),

 ('table', 'IaC anti-patterns',
  ['Anti-pattern', 'What goes wrong'],
  [['ClickOps, then "import it later"', 'It is never imported; the drift is permanent'],
   ['Local state on one laptop', 'A lost laptop means losing control of production'],
   ['State committed to git', 'Plaintext secrets in every clone, forever'],
   ['One giant root module', 'A 40-minute plan, and a typo can destroy everything'],
   ['No plan review before apply', 'You learn what changed by reading the incident report'],
   ['Unpinned provider and module versions', 'A provider release silently changes your infrastructure'],
   ['apply -auto-approve from a laptop', 'No review, no audit trail, no second pair of eyes'],
   ['A manual "just this once" fix', 'Not in code — so the next apply reverts it'],
   ['✔ The target', 'Small modules · remote locked state · plan in the PR · apply only from CI · pin everything']],
  'MODULE 5 §5.5', {'widths': [3.6, 6.4], 'emph': [8]}),

 ('bank', 'Infrastructure as Code in a regulated bank',
  [('The reviewed plan IS the change record', 'What will change, who approved it, when it was applied — generated, not typed'),
   ('Apply only from the pipeline identity', 'No engineer needs standing write access to production infrastructure'),
   ('State access is production access', 'Treat terraform.tfstate readers as privileged users'),
   ('Scheduled drift detection is continuous control monitoring', 'Evidence that production matches its approved definition — every hour'),
   ('Reproducible environments make recovery testable', 'A rebuild you can run is a resilience test you can evidence')],
  {'lead': 'An auditor wants to know that production is what was approved, and that nobody changed it '
           'outside the process. IaC with drift detection answers both, continuously.',
   'ref': 'Appendix A §A.4–A.5 · Labs 13–14'}),

 ('lab', '13 + 14', 'Terraform · Ansible',
  'Everything you built by hand yesterday becomes reviewed, versioned, reproducible code.',
  ['Write a reusable Terraform module and instantiate it TWICE — prod and staging',
   'Pin providers; commit the lock file; pin the kubeconfig context explicitly',
   'Read a plan properly, then apply the SAVED plan',
   'Grep the password out of the state file — and discuss what that means',
   'Scale a deployment by hand, run plan, watch Terraform DETECT the drift and revert it',
   'Ansible: a baseline role and an app role — and prove changed=0 on the second run'],
  'Two environments from one reviewed module, plus idempotent configuration management',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('section', '4', 'Continuous Delivery', 'From a commit to production, safely',
  ['Delivery vs Deployment', 'What CD requires', 'The pipeline and environments',
   'Deployment strategies', 'Blue-green and canary']),

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

 ('table', 'What Continuous Delivery actually requires',
  ['Requirement', 'Why'],
  [['Automated tests you trust', 'The pipeline is the only quality gate left'],
   ['Build once, promote the same artefact', 'Otherwise you test one binary and ship another'],
   ['Environment parity', 'A pass in staging must mean something for production'],
   ['Configuration outside the artefact', 'One image, many environments — day 3\'s lesson'],
   ['Automated, repeatable deployment', 'Every manual step breaks the chain'],
   ['A TESTED rollback', 'An untested rollback is a hope, not a plan'],
   ['Database changes decoupled from code changes', 'The hardest part — expand/contract, later today'],
   ['Monitoring that can tell a deploy went well', 'Otherwise "success" means the script exited 0']],
  'MODULE 6 §6.1', {'widths': [3.8, 6.2]}),

 ('table', 'Environments, and what belongs in each',
  ['Environment', 'Purpose', 'Data', 'Who deploys'],
  [['Dev', 'Fast iteration', 'Synthetic', 'Automatic on merge'],
   ['Test / QA', 'Automated acceptance', 'Anonymised or synthetic', 'Automatic'],
   ['Staging', 'Production-like final check, performance, DR rehearsal', 'Anonymised, production-shaped', 'Automatic'],
   ['Production', 'Real users', 'Real', 'Automatic (deployment) or a button (delivery)']],
  'MODULE 6 §6.2', {'widths': [1.9, 4.0, 2.5, 2.8],
   'note': ('THE PIPELINE RULES', 'Build once · deploy the same way to every environment · smoke-test every '
            'deployment · stop on any failure. And never copy real production data into a lower environment '
            'without anonymising it — Appendix A §A.6.')}),

 ('diagram', 'Three deployment strategies', dg.deployment_strategies, 'MODULE 6 §6.3',
  {'speaker': 'Canary is not an A/B test. A canary asks "is this release safe?" with a random slice of traffic. '
   'An A/B test asks "is this variant better?" with a chosen cohort and statistics. Different questions.'}),

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

 ('flow', 'A blue-green cut-over, step by step',
  [('Blue serves 100 % of traffic', 'The Service selector says version: blue'),
   ('Deploy green alongside it', 'Warm, fully running — and receiving no traffic at all'),
   ('Smoke-test green in the real cluster', 'Real configuration, real infrastructure, zero user risk'),
   ('Cut over: change ONE field on the Service', 'selector version: blue → green — atomic'),
   ('Bake, then decommission blue', 'Keep blue until you are confident; rollback is flipping the selector back')],
  'MODULE 6 §6.3',
  {'note': ('THE HARD PART', 'Shared state. Both colours talk to the same database, so both must work with the '
            'same schema — and blue-green cannot roll back data, schema changes or messages already sent.')}),

 ('demo', 'A blue-green cut-over in one line',
  '''$ kubectl get deploy -l app=paytrack-api -L version
# (columns trimmed)
NAME                  READY  VERSION
paytrack-api-blue     2/2    blue
paytrack-api-green    2/2    green
$ curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r .color
blue
$ kubectl patch service paytrack-bg \\
    -p '{"spec":{"selector":{"version":"green"}}}'
service/paytrack-bg patched
$ curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r .color
green''',
  [('Both colours are running before the switch', 'Green was smoke-tested while serving nobody'),
   ('One field changes', 'The Service selector — nothing is restarted, nothing is rebuilt'),
   ('Every new request goes to green', 'The EndpointSlice swaps to green\'s ready pods'),
   ('Rollback is the same command with "blue"', 'Seconds, and nothing to redeploy')],
  {'minutes': 5, 'speaker': 'This is Lab 16 Step 1.4. In the lab a watch loop shows the colour flip live in the '
   'terminal; in the room, a browser on the banner makes the same point. The label list is illustrative.'}),

 ('section', '5', 'Rollback, Data, Artefacts & GitOps', 'The parts that make or break delivery',
  ['Rollback methods and rules', 'Expand / contract', 'Artefact repositories',
   'GitOps: pull vs push', 'Release management and freezes']),

 ('table', 'Rollback — methods, measured',
  ['Method', 'Typical time', 'Scope', 'Note'],
  [['Feature flag off', '✔ Instant', 'One feature', 'The fastest rollback that exists. No deployment at all'],
   ['Blue-green selector flip', 'Seconds', 'All traffic', 'The alternative is already running and warm'],
   ['Canary abort', 'Seconds', 'Only the canary share', 'Smallest blast radius throughout'],
   ['kubectl rollout undo', 'Under a minute', 'The Deployment', 'The old ReplicaSet still exists at desired 0'],
   ['Redeploy a previous digest', 'About a minute', 'The workload', 'kubectl set image … @sha256:…'],
   ['git revert + pipeline', 'The pipeline duration', 'Everything', '✔ Slowest, but auditable and correct — the default']],
  'MODULE 6 §6.4', {'widths': [2.6, 2.0, 2.2, 4.2],
   'note': ('ROLL BACK FIRST, DIAGNOSE SECOND', 'The incident is the priority; root cause is important but not '
            'urgent. Feature flags cost flag debt — give each one an expiry date and delete it after the release.')}),

 ('bullets', 'Rollback rules',
  [('Practise it', 'An untested rollback is not a rollback — rehearse it in a game day'),
   ('Automate the trigger', 'Smoke tests and SLO burn-rate alerts should abort a deployment without a human'),
   ('Keep the previous artefact', 'Never delete the image you might need to roll back to'),
   ('Know your point of no return', 'Usually the first irreversible database migration'),
   ('Communicate', 'A rollback is an incident event — it belongs in the timeline')],
  'MODULE 6 §6.4'),

 ('flow', 'Expand / contract — changing a schema with zero downtime',
  [('Release 1 — EXPAND', 'Add the new nullable column or table. Old code is completely unaffected. Rollback-safe'),
   ('Release 2 — MIGRATE', 'Code WRITES both old and new, READS the new. Backfill existing rows. Rollback-safe'),
   ('Release 3 — CONTRACT', 'Once no code and no rollback target uses the old column: drop it. The point of no return')],
  'MODULE 6 §6.6',
  {'note': ('THE RULES', 'Run migrations separately from the app (a Job or init container) · forward-only and additive · '
            'never rename or drop in the release that stops using something · test on production-sized data · '
            'N and N+1 are BOTH live during a rolling update.')}),

 ('define', 'Artefact repository',
  'A versioned, access-controlled store of build outputs — binaries, container images, packages, charts — '
  'that is the single source of deployable artefacts and the boundary between build and deploy.',
  [('Immutability', 'A published version is never overwritten'),
   ('Traceability', 'Which commit produced this image? The revision label answers it'),
   ('Retention, scanning and access control', 'Policies you can evidence'),
   ('Upstream caching', 'A deleted package or a registry outage does not break your builds'),
   ('In this course: GHCR', 'Enterprise equivalents: Nexus, Artifactory, Harbor, or a cloud registry')],
  'MODULE 6 §6.5'),

 ('compare', 'Who holds the keys to production?',
  'Model A: your CI pipeline holds a kubeconfig with deploy rights and runs kubectl apply. '
  'Model B: CI commits a new image tag to git, and an agent inside the cluster pulls it. '
  'Same outcome. Which would you rather defend to an auditor, and why?',
  ['Two minutes in pairs. List what an attacker gains by compromising the CI system in each model.',
   'Then: in which model can you answer "what is running in production?" without cluster access?'],
  'In Model A, compromising CI gives production write access. In Model B there is no external '
  'credential to steal, drift is corrected continuously, and git history is the change record. '
  'Pull beats push on both security and evidence.', 3),

 ('diagram', 'GitOps — and why a bank should care', dg.gitops, 'MODULE 6 §6.7',
  {'speaker': 'The four principles: the desired state is declarative; it is versioned and immutable in git; '
   'changes are pulled automatically by an agent; and the agent continuously reconciles. Lab 15 builds a '
   'simplified reconciler so the mechanism is visible without installing Argo CD.'}),

 ('bank', 'Why pull-based GitOps is the stronger control',
  [('No human and no external system holds production write access',
    'The credential never leaves the cluster. Compare with a CI server holding a kubeconfig'),
   ('Git history IS the deployment record',
    'Commit, approver, image digest, pipeline run — generated, not typed into a ticket afterwards'),
   ('Drift is corrected continuously, not discovered at audit',
    'The agent reconciles; a manual change is reverted and visible'),
   ('Rollback is git revert', 'Same review, same audit trail, same mechanism as any other change'),
   ('Deployment becomes a STANDARD CHANGE candidate',
    'Repeatable, well-understood, automated — exactly the ITIL definition')],
  {'lead': 'The question an auditor asks is not "how fast do you deploy?" but "who could change '
           'production, and how would you know?" GitOps has a better answer than any manual process.',
   'ref': 'Appendix A §A.3–A.5 · Lab 15'}),

 ('table', 'Release management practices',
  ['Practice', 'Purpose', 'Verdict'],
  [['Release notes generated from commits', 'Accurate notes for free — and a reason to write good commit messages', '✔ Do it'],
   ['Semantic versioning for consumers', 'Signals compatibility to whoever depends on you', '✔ For libraries and APIs'],
   ['Release train (fixed cadence)', 'Predictability for coordinated organisations', 'Useful while you shrink batch size'],
   ['Progressive rollout by region or tenant', 'Bounds the blast radius geographically', '✔ Do it'],
   ['Automated change records', 'The pipeline IS the evidence — no manual CAB write-up', '✔ Do it'],
   ['Change freeze', 'Batches risk into the least-staffed period; urgent work moves to the emergency path', '✗ Usually harmful']],
  'MODULE 6 §6.7', {'widths': [3.2, 4.8, 2.2],
   'note': ('BANKS FREEZE MORE THAN ANYONE', 'Year-end, quarter-end, reporting dates. The intent is sound; the effect '
            'is usually a six-week batch on the riskiest day of the year. Appendix A §A.7 has the risk-proportionate alternative.')}),

 ('lab', '15 + 16', 'CD Pipeline to Kubernetes · Deployment Strategies',
  'Join everything from days 1–5 into one automated path, then move traffic and watch it happen.',
  ['Build the pipeline: test → build once → scan → publish → PROMOTE by committing the new tag',
   'Run an in-cluster reconciler that pulls the change and applies it — the GitOps mechanism, visible',
   'Merge a real change and watch it reach the cluster with NO ONE running kubectl',
   'Deploy a broken image and watch the reconciler ROLL BACK automatically',
   'Blue-green: patch one Service selector and watch the banner flip blue → green',
   'Canary: sample 100 requests and measure the 90/10 split, then promote progressively'],
  'A complete GitOps delivery pipeline, plus working blue-green and canary you can see'),

 ('table', 'Day 5 key terms',
  ['Term', 'Definition'],
  [['IaC', 'Infrastructure defined in versioned, machine-readable files applied by automation'],
   ['Declarative / idempotent', 'Describe the end state / repeating changes nothing'],
   ['Snowflake / drift', 'An unreproducible server / reality diverging from its definition'],
   ['Plan / apply / state', 'Read-only diff / execute it / Terraform\'s record of what it manages'],
   ['Module (Terraform) / role (Ansible)', 'The unit of reuse in each tool'],
   ['Inventory / handler / Vault', 'Hosts and groups / a task run only when notified / repository encryption'],
   ['Continuous Delivery / Deployment', 'Always releasable, a human chooses when / every passing change ships'],
   ['Blue-green / canary', 'Flip a selector between two full versions / route a small share, watch, promote'],
   ['Expand / contract', 'A three-release pattern for backwards-compatible schema change'],
   ['GitOps', 'Declarative state in git, pulled and reconciled by an in-cluster agent']],
  'REFERENCE', {'widths': [3.5, 6.5]}),

 ('check', 'Day 5 — check your understanding',
  ['Your team applies Terraform from laptops with -auto-approve. Name three risks and describe '
   'the target workflow.',
   'A plan shows -/+ replace on a production database. What do you do next?',
   'Why must terraform.tfstate never be committed to git? Give two distinct reasons.',
   'An Ansible playbook reports changed=6 on every run. What is wrong, and how do you fix it?',
   'You must rename a database column with zero downtime. Describe the releases.',
   'Blue-green gives instant rollback. Name three things it does NOT roll back.']),

 ('close', 5, 'Day 5 complete',
  ['IaC principles: declarative, idempotent, immutable — and why drift is a control failure',
   'Terraform: reading a plan, protecting state, modules for identical environments',
   'Ansible: agentless configuration you can prove is idempotent',
   'Continuous Delivery, deployment strategies, rollback, expand/contract and GitOps',
   'AFTER CLASS: finish Labs 13–16 — Lab 15\'s pipeline is what day 6 secures'],
  'Day 6 makes the pipeline prove it is safe, and makes the platform prove it is healthy. Security '
  'gates you will watch block your own merge, an SBOM, secrets encrypted into git — then Prometheus, '
  'Grafana, SLOs and burn-rate alerts, incident response, enterprise DevOps, and the capstone.'),
]
