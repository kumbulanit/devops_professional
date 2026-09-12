# Terraform & Ansible Reference

# ── TERRAFORM ──────────────────────────────────────────────────────────────

## Workflow
```bash
terraform init                      # download providers, init backend, write the lock file
terraform fmt -recursive            # canonical formatting (in CI: -check)
terraform validate                  # syntax + types + references. No API calls
terraform plan -out=tfplan          # READ-ONLY diff. THE important command
terraform apply tfplan              # apply EXACTLY the reviewed plan
terraform destroy                   # ⚠️ read `plan -destroy` first, every time
terraform output [-json]
```

## Reading a plan
| Symbol | Meaning |
|---|---|
| `+ create` | New |
| `~ update in-place` | Modified, no replacement |
| `-/+ destroy and then create replacement` | **⚠️ REPLACEMENT. On a database this is data loss** |
| `- destroy` | Removed |

## State
```bash
terraform state list
terraform state show <addr>
terraform state mv <src> <dst>          # after refactoring a module
terraform state rm <addr>               # stop managing (does NOT delete the real resource)
terraform import <addr> <real-id>       # adopt an existing resource
terraform force-unlock <lock-id>        # ONLY after confirming nothing else is running
terraform plan -detailed-exitcode       # 0 = no change, 2 = drift, 1 = error → DRIFT DETECTOR
```
> **State contains secrets in plaintext.** Never commit it. Use a remote backend with
> encryption **and locking**. `sensitive = true` masks CLI output only.

## Language
```hcl
terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"
    }
  }
  backend "s3" {
    bucket         = "tfstate"
    key            = "prod.tfstate"
    dynamodb_table = "locks"      # THE LOCK
    encrypt        = true
  }
}

variable "n" {
  type    = number
  default = 2
  validation {
    condition     = var.n > 0
    error_message = "n must be positive."
  }
}

locals {
  name = "paytrack-${var.env}"
}

output "url" {
  value     = "http://${local.name}"
  sensitive = false
}

module "app" {
  source = "./modules/app"
  env    = "prod"
}
```

| Meta-argument | Use |
|---|---|
| `for_each = toset([...])` | **Preferred.** Stable keys |
| `count = 3` | Indexed. Removing an element **re-indexes and can destroy the wrong resource** |
| `depends_on` | Only when Terraform cannot infer the dependency |
| `lifecycle { prevent_destroy = true }` | Databases. Refuses to plan a destroy |
| `lifecycle { create_before_destroy = true }` | Avoid downtime on replacement |
| `lifecycle { ignore_changes = [tags] }` | Tolerate out-of-band changes |

## Variable precedence (low → high)
`default` → `terraform.tfvars` → `*.auto.tfvars` → `-var-file` → `-var` → `TF_VAR_name`

## Rules
1. Pin `required_version` and every provider; **commit `.terraform.lock.hcl`**
2. Remote backend **with locking** for anything shared
3. `plan` in the PR, `apply` only from CI
4. Small, single-purpose, versioned modules
5. Never hand-edit state
6. One tool per resource — never let Terraform and kubectl manage the same object

---

# ── ANSIBLE ────────────────────────────────────────────────────────────────

## Commands
```bash
ansible all -m ping                          # connectivity + Python + module execution
ansible web -m setup -a 'filter=ansible_dist*'   # gather facts
ansible-inventory --graph
ansible-playbook site.yml
ansible-playbook site.yml --check --diff     # DRY RUN + show file differences
ansible-playbook site.yml --limit web1 --tags deploy
ansible-playbook site.yml --start-at-task "Install packages"
ansible-playbook site.yml -vvv               # verbose: module args + SSH commands
ansible-lint playbook.yml roles/
ansible-galaxy collection install community.docker
```

## Vault
```bash
ansible-vault create|encrypt|decrypt|view|edit|rekey file.yml
ansible-playbook site.yml --vault-password-file .vault_pass
```
The **encrypted file is safe to commit**; the password must come from outside git.

## Playbook shape
```yaml
- name: Configure web tier
  hosts: web
  become: true
  serial: 1                       # ONE host at a time → rolling, zero-downtime
  max_fail_percentage: 0
  vars: { app_port: 8080 }
  tasks:
    - name: Ensure packages present
      ansible.builtin.apt:        # FQCN — best practice
        name: [curl, jq]
        state: present            # DESIRED STATE
        update_cache: true
        cache_valid_time: 3600
    - name: Render config
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/app.conf
        mode: "0640"
      notify: Restart app         # handler fires ONLY if this changed something
  handlers:
    - name: Restart app
      ansible.builtin.service:
        name: app
        state: restarted
```

## Idempotency
| Technique | Effect |
|---|---|
| `state: present/absent` | The module checks before acting |
| `creates:` / `removes:` on `command` | Skip entirely if the path exists/does not |
| `changed_when: false` | "This never changes the system" |
| `notify` + handlers | One restart per play, not one per task |
| `no_log: true` | **Keep secrets out of logs.** Mandatory on any task handling credentials |

**`changed=0` on a second run is the definition of an idempotent playbook.**

## Common modules
`apt` `yum` `package` · `copy` `template` `file` `lineinfile` `blockinfile` `replace` ·
`user` `group` · `service` `systemd_service` · `git` · `uri` · `command` `shell` (last resort) ·
`stat` · `wait_for` · `docker_container` · `k8s`

## Jinja2
```jinja
{{ var }} · {{ var | default('x') }} · {{ list | join(',') }}
{% if 'db' in group_names %}…{% endif %}
{% for h in groups['web'] %}{{ hostvars[h].ansible_host }}{% endfor %}
{{ groups['database'] | first }}          {# cross-host awareness from the inventory #}
```

## Variable precedence (low → high, abridged)
role `defaults/` → inventory group_vars → inventory host_vars → `group_vars/all` →
`group_vars/<group>` → `host_vars/<host>` → play `vars` → role `vars/` → `-e` (**highest**)
