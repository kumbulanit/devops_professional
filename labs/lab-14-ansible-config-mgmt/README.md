# Lab 14 — Configuration Management with Ansible

| | |
|---|---|
| **Day** | 5 |
| **Duration** | 30 minutes |
| **Module** | 5 — Infrastructure as Code |
| **You will produce** | An `ansible/` tree: inventory, a baseline role, a deploy role, Vault-encrypted secrets |
| **Feeds into** | Lab 19 (capstone), and directly applicable to any VM estate you run |

---

## Objective

Configure servers declaratively and idempotently. You will use **Docker containers as managed
nodes** — real Ubuntu 24.04 systems with systemd, configured over Ansible's Docker connection
plugin. No SSH keys, no VMs, no cost, and every Ansible concept is identical to managing a
real fleet.

> **Prefer real VMs?** `multipass launch 24.04 --name node1 --cpus 1 --memory 1G` twice, then
> swap the inventory to `ansible_connection=ssh`. Everything else is unchanged.

> **Trainer:** the fourth lab to demote to a demo if the room is behind (`docs/run-sheet.md`).

## Prerequisites

- Lab 00 (Ansible + the Python Docker SDK)
- Verify: `ansible --version && python3 -c "import docker; print('docker SDK ok')"`

---

## Step 1 — Create the managed nodes

```bash
cd ~/devops-course/paytrack-api-team
mkdir -p ansible/{inventory,roles,group_vars,playbooks}
cat > ansible/nodes.sh <<'EOF'
#!/usr/bin/env bash
# Creates three Ubuntu 24.04 containers running systemd, to act as managed nodes.
set -euo pipefail

docker network create ansible-lab 2>/dev/null || true

for n in web1 web2 db1; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$n"; then
    echo "  $n already exists"; continue
  fi
  docker run -d --name "$n" \
    --network ansible-lab \
    --hostname "$n" \
    --cgroupns=host \
    --tmpfs /run --tmpfs /run/lock \
    -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
    ubuntu:24.04 \
    /bin/bash -c "apt-get update -qq && \
                  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 systemd systemd-sysv >/dev/null && \
                  exec /lib/systemd/systemd"
  echo "  created $n"
done
echo "Waiting for systemd to come up…"; sleep 25
docker ps --filter network=ansible-lab --format "table {{.Names}}\t{{.Status}}"
EOF
chmod +x ansible/nodes.sh && ./ansible/nodes.sh
```
**What this does:** creates three containers that behave like servers.
- `--cgroupns=host` and the cgroup mount let **systemd** run inside, so the `service` module
  works exactly as it would on a VM.
- `--tmpfs /run` gives systemd its runtime directory.
- The command installs **python3** — Ansible's only requirement on a managed node — then
  `exec`s systemd as PID 1.

---

## Step 2 — Inventory

```bash
cat > ansible/inventory/hosts.yml <<'EOF'
# Ansible inventory: which machines exist, how to reach them, how they are grouped.
all:
  vars:
    ansible_connection: community.docker.docker   # talk over the Docker API, not SSH
    ansible_python_interpreter: /usr/bin/python3

  children:
    web:
      hosts:
        web1:
        web2:
      vars:
        app_port: 8080
        node_role: application

    database:
      hosts:
        db1:
      vars:
        app_port: 5432
        node_role: database

    # A group of groups. `production` targets everything below it.
    production:
      children:
        web:
        database:
EOF
```
**What this does:** defines hosts, groups, group-of-groups, and variables at each level.
`ansible_connection: community.docker.docker` makes Ansible use `docker exec` instead of SSH
— the **only** line that differs from a real VM inventory.

```bash
cat > ansible/ansible.cfg <<'EOF'
[defaults]
inventory            = inventory/hosts.yml
roles_path           = roles
host_key_checking    = False
# readable multi-line output instead of one long line
stdout_callback      = yaml
# timer + profile_tasks show which tasks are slow
callbacks_enabled    = timer, profile_tasks
interpreter_python   = auto_silent
retry_files_enabled  = False
# configure up to 10 hosts in parallel
forks                = 10

[privilege_escalation]
become        = True
become_method = sudo
become_user   = root
EOF
```
**What this does:** sets defaults so you stop passing flags. `profile_tasks` prints a
per-task duration summary — the first thing you need when a playbook takes 40 minutes.

> ⚠️ **Every comment is on its own line, and that is not a style choice.** Ansible's INI
> parser takes **the entire rest of the line** as the value, so
> `forks = 10   # ten at a time` sets forks to the string `"10   # ten at a time"` and every
> later command dies with
> `Invalid value provided for 'integer'`. The same trap silently breaks `stdout_callback`
> and `callbacks_enabled` — they just stop working, with no error at all.

```bash
cd ansible
ansible-inventory --graph
ansible all -m ping
```
**What this does:** `--graph` renders the group tree. `-m ping` runs the `ping` module
against every host — **not ICMP**: it verifies Ansible can connect, find Python, and execute
a module. Expect three `SUCCESS` results.

```bash
ansible web -m setup -a 'filter=ansible_distribution*'
```
**What this does:** the `setup` module gathers **facts** — everything Ansible can discover
about a host. `filter` narrows the output. Facts are how a playbook adapts to what it finds
(`when: ansible_distribution == "Ubuntu"`).

---

## Step 3 — The baseline role

```bash
mkdir -p roles/baseline/{tasks,handlers,templates,defaults}

cat > roles/baseline/defaults/main.yml <<'EOF'
# defaults/ is the role's PUBLIC API: documented, overridable, lowest precedence.
baseline_packages:
  - curl
  - ca-certificates
  - tzdata
  - logrotate

baseline_timezone: "UTC"
app_user: paytrack
app_group: paytrack
app_uid: 10001
app_dirs:
  - /opt/paytrack
  - /etc/paytrack
  - /var/log/paytrack
EOF

cat > roles/baseline/tasks/main.yml <<'EOF'
- name: Update the apt cache if it is older than an hour
  ansible.builtin.apt:
    update_cache: true
    cache_valid_time: 3600      # skip entirely if the cache is fresh -> IDEMPOTENT
  changed_when: false           # a cache refresh is not a change to the system

- name: Ensure baseline packages are present
  ansible.builtin.apt:
    name: "{{ baseline_packages }}"
    state: present              # DESIRED STATE, not "run apt install"
  # Second run reports "ok", not "changed", because the module checks first.

- name: Ensure the application group exists
  ansible.builtin.group:
    name: "{{ app_group }}"
    gid: "{{ app_uid }}"
    state: present

- name: Ensure the application user exists
  ansible.builtin.user:
    name: "{{ app_user }}"
    uid: "{{ app_uid }}"
    group: "{{ app_group }}"
    shell: /usr/sbin/nologin     # a service account cannot log in
    system: true
    create_home: false
    state: present

- name: Ensure application directories exist with correct ownership
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: "{{ app_user }}"
    group: "{{ app_group }}"
    mode: "0750"
  loop: "{{ app_dirs }}"         # one task, three directories

- name: Set the system timezone
  ansible.builtin.file:
    src: "/usr/share/zoneinfo/{{ baseline_timezone }}"
    dest: /etc/localtime
    state: link
    force: true

- name: Install log rotation for the application
  ansible.builtin.template:
    src: logrotate.j2
    dest: /etc/logrotate.d/paytrack
    owner: root
    group: root
    mode: "0644"
  notify: Validate logrotate     # fires the handler ONLY IF this task changed something

- name: Record which node this is (facts rendered into a file)
  ansible.builtin.template:
    src: node-info.j2
    dest: /etc/paytrack/node-info
    owner: "{{ app_user }}"
    mode: "0640"
EOF

cat > roles/baseline/handlers/main.yml <<'EOF'
- name: Validate logrotate
  ansible.builtin.command: logrotate -d /etc/logrotate.d/paytrack
  changed_when: false
  # Handlers run ONCE, at the END of the play, only if notified.
  # Ten tasks notifying "restart nginx" produce exactly ONE restart.
EOF

cat > roles/baseline/templates/logrotate.j2 <<'EOF'
/var/log/paytrack/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 {{ app_user }} {{ app_group }}
}
EOF

cat > roles/baseline/templates/node-info.j2 <<'EOF'
# Managed by Ansible - manual edits will be overwritten.
hostname={{ ansible_hostname }}
role={{ node_role | default('unassigned') }}
distribution={{ ansible_distribution }} {{ ansible_distribution_version }}
architecture={{ ansible_architecture }}
cpus={{ ansible_processor_vcpus | default('unknown') }}
memory_mb={{ ansible_memtotal_mb | default('unknown') }}
configured_at={{ ansible_date_time.iso8601 }}
group_members={{ groups[node_role | default('all')] | default([]) | join(',') }}
EOF
```
**Why the role structure exists:**

| Directory | Purpose |
|---|---|
| `defaults/main.yml` | Overridable variables — **the role's documented interface** |
| `vars/main.yml` | Internal variables, high precedence, not meant to be overridden |
| `tasks/main.yml` | The entry point |
| `handlers/main.yml` | Tasks that run once, at the end, only when notified |
| `templates/` | Jinja2 (`.j2`) rendered with variables and facts |
| `files/` | Static files copied verbatim |

**The idempotency techniques in use:**

| Technique | Effect |
|---|---|
| `state: present` | Declares desired state; the module checks before acting |
| `cache_valid_time` | Skips a refresh that has already happened recently |
| `changed_when: false` | Tells Ansible "this task never changes the system" — stops false `changed` counts |
| `notify` + handlers | Batches restarts to one per play |
| `loop` | One task, many items, still idempotent per item |

---

## Step 4 — Run it, then run it again

```bash
cat > playbooks/site.yml <<'EOF'
- name: Baseline configuration for all managed nodes
  hosts: production
  gather_facts: true
  roles:
    - baseline
EOF

ansible-playbook playbooks/site.yml
```
**What this does:** applies the role to every host in `production`. Read the `PLAY RECAP`:

```
web1 : ok=9   changed=7   unreachable=0   failed=0
web2 : ok=9   changed=7   unreachable=0   failed=0
db1  : ok=9   changed=7   unreachable=0   failed=0
```

```bash
ansible-playbook playbooks/site.yml
```
✅ **The checkpoint that defines this lab:**
```
web1 : ok=9   changed=0   unreachable=0   failed=0
```

> 🔑 **`changed=0` on the second run IS idempotency.** Nothing was modified because nothing
> needed to be. If any task reports `changed` every time, it is almost always a raw
> `command`/`shell` — fix it with a proper module, or with `creates:`, `removes:` or
> `changed_when:`.

```bash
ansible-playbook playbooks/site.yml --check --diff
```
**What this does:** `--check` is Ansible's dry run — the equivalent of `terraform plan`.
`--diff` shows the exact file content that *would* change. **Use both before touching
production.**

```bash
ansible web1 -m command -a 'cat /etc/paytrack/node-info'
ansible web -m command -a 'id paytrack'
```
**What this does:** verifies the rendered template (note the facts substituted in) and that
the service account exists with uid 10001 on both web nodes.

---

## Step 5 — Prove convergence after manual tampering

```bash
docker exec web1 rm -f /etc/paytrack/node-info
docker exec web1 userdel paytrack 2>/dev/null || true
ansible-playbook playbooks/site.yml --limit web1
```
**What this does:** breaks the node by hand — someone "just quickly" deleted things — then
re-runs against that host only (`--limit`). Ansible reports `changed=2` and **restores exactly
what was missing, and nothing else.**

That selectivity is the difference between a configuration-management tool and a shell
script: a script would redo everything, or fail because things already existed.

---

## Step 6 — Secrets with Ansible Vault

```bash
mkdir -p group_vars/production
cat > group_vars/production/vault.yml <<'EOF'
vault_db_password: "S3cur3-Ansible-Pass!"
vault_api_token: "tok_live_do_not_use_in_production"
EOF

echo 'lab-vault-password' > .vault_pass
chmod 600 .vault_pass
echo 'ansible/.vault_pass' >> ../.gitignore

ansible-vault encrypt group_vars/production/vault.yml --vault-password-file .vault_pass
head -3 group_vars/production/vault.yml
```
**What this does:** encrypts the file with AES-256. `head` shows
`$ANSIBLE_VAULT;1.1;AES256` followed by ciphertext.

> 🔑 **The encrypted file is safe to commit.** The *password* must come from outside git — a
> CI secret, a password manager, or a KMS. Here it is in `.vault_pass`, which is git-ignored.

```bash
ansible-vault view group_vars/production/vault.yml --vault-password-file .vault_pass
```
**What this does:** decrypts to stdout without ever writing plaintext to disk. `edit` opens
it in your editor and re-encrypts on save.

```bash
cat > playbooks/secrets-demo.yml <<'EOF'
- name: Demonstrate Vault-sourced secrets
  hosts: web
  gather_facts: false
  vars_files:
    - ../group_vars/production/vault.yml
  tasks:
    - name: Write the application credentials file
      ansible.builtin.copy:
        content: |
          DB_PASSWORD={{ vault_db_password }}
          API_TOKEN={{ vault_api_token }}
        dest: /etc/paytrack/credentials
        owner: paytrack
        group: paytrack
        mode: "0600"          # owner read/write ONLY
      no_log: true            # ← do NOT print the content, even with -vvv

    - name: Confirm the file exists without revealing it
      ansible.builtin.stat:
        path: /etc/paytrack/credentials
      register: cred

    - name: Report
      ansible.builtin.debug:
        msg: "credentials present={{ cred.stat.exists }} mode={{ cred.stat.mode }}"
EOF
ansible-playbook playbooks/secrets-demo.yml --vault-password-file .vault_pass
```
**What this does:** decrypts at run time and writes a `0600` credentials file.
**`no_log: true` is the critical line** — without it, Ansible prints the task arguments
(including your secret) into the log, which then lands in your CI system's log store forever.

---

## Step 7 — Deploy the application

```bash
mkdir -p roles/paytrack_app/{tasks,templates,defaults,handlers}

cat > roles/paytrack_app/defaults/main.yml <<'EOF'
paytrack_version: "1.0.0"
paytrack_port: 8080
paytrack_color: "blue"
paytrack_log_level: "INFO"
EOF

cat > roles/paytrack_app/tasks/main.yml <<'EOF'
- name: Render the application environment file
  ansible.builtin.template:
    src: paytrack.env.j2
    dest: /etc/paytrack/paytrack.env
    owner: paytrack
    group: paytrack
    mode: "0640"
  notify: Restart paytrack

- name: Install the systemd unit
  ansible.builtin.template:
    src: paytrack.service.j2
    dest: /etc/systemd/system/paytrack.service
    owner: root
    mode: "0644"
  notify:
    - Reload systemd
    - Restart paytrack

- name: Ensure the service is enabled and running
  ansible.builtin.systemd_service:
    name: paytrack
    enabled: true
    state: started
    daemon_reload: true
  register: svc
  failed_when: false          # this lab's containers have no Python app installed;
                              # we are demonstrating the MECHANISM, not running Flask

- name: Report service state
  ansible.builtin.debug:
    msg: "paytrack unit installed on {{ inventory_hostname }} (state: {{ svc.state | default('n/a') }})"
EOF

cat > roles/paytrack_app/handlers/main.yml <<'EOF'
- name: Reload systemd
  ansible.builtin.systemd_service:
    daemon_reload: true

- name: Restart paytrack
  ansible.builtin.systemd_service:
    name: paytrack
    state: restarted
  failed_when: false
EOF

cat > roles/paytrack_app/templates/paytrack.env.j2 <<'EOF'
# Managed by Ansible - do not edit by hand.
APP_VERSION={{ paytrack_version }}
APP_COLOR={{ paytrack_color }}
APP_ENV={{ node_role | default('unknown') }}
LOG_LEVEL={{ paytrack_log_level }}
PORT={{ paytrack_port }}
{% if 'database' in group_names %}
DATABASE_URL=postgresql://paytrack@localhost:5432/paytrack
{% else %}
DATABASE_URL=postgresql://paytrack@{{ groups['database'] | first }}:5432/paytrack
{% endif %}
EOF

cat > roles/paytrack_app/templates/paytrack.service.j2 <<'EOF'
[Unit]
Description=PayTrack API {{ paytrack_version }}
After=network-online.target

[Service]
Type=exec
User=paytrack
Group=paytrack
EnvironmentFile=/etc/paytrack/paytrack.env
WorkingDirectory=/opt/paytrack
ExecStart=/opt/paytrack/.venv/bin/gunicorn --bind 0.0.0.0:{{ paytrack_port }} wsgi:app
Restart=on-failure
RestartSec=5
# Hardening - the systemd equivalent of a container securityContext
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/paytrack

[Install]
WantedBy=multi-user.target
EOF

cat >> playbooks/site.yml <<'EOF'

- name: Deploy PayTrack API to the web tier
  hosts: web
  gather_facts: true
  roles:
    - paytrack_app
EOF

ansible-playbook playbooks/site.yml
ansible web1 -m command -a 'cat /etc/paytrack/paytrack.env'
```
**The Jinja2 features on show:**

| Feature | Purpose |
|---|---|
| `{{ variable }}` | Substitution |
| `{% if %}` / `{% else %}` / `{% endif %}` | Conditional content — the DB host differs on database nodes |
| `groups['database'] \| first` | **Cross-host awareness**: a web node's config references the database host from the inventory. This is what makes templating better than static files |
| `\| default('unknown')` | A filter supplying a fallback |
| `group_names` | The groups the *current* host belongs to |

**Note the systemd hardening directives** — `NoNewPrivileges`, `ProtectSystem=strict`,
`PrivateTmp` — they are the direct equivalents of the container `securityContext` from
Lab 10. The same security principles, expressed in whichever platform you are on.

---

## Step 8 — Lint, then commit

```bash
ansible-lint playbooks/site.yml roles/ 2>&1 | tail -20
```
**What this does:** checks against community best practice — missing task names,
`command` where a module exists, deprecated syntax, missing FQCNs, unsafe permissions.
**Put this in CI**, exactly like `flake8`.

```bash
cd ..
git add ansible/ .gitignore
git commit -m "feat(ansible): baseline and app-deploy roles with Vault

Three Ubuntu 24.04 containers as managed nodes over the Docker connection
plugin - identical semantics to SSH-managed VMs.

- baseline role: packages, service account (uid 10001), directories,
  timezone, logrotate; idempotent (changed=0 on the second run)
- paytrack_app role: templated env file and hardened systemd unit
- secrets in an ansible-vault encrypted group_vars file; no_log on the task
  that consumes them so they never reach a CI log"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
cd ansible
ansible-playbook playbooks/site.yml | tail -8
```
**Every host must show `changed=0`.** That single number is the deliverable.

---

## 🧩 Stretch (homework)

1. **Rolling restarts.** Add `serial: 1` and `max_fail_percentage: 0` to the web play, so
   Ansible configures one host at a time and stops on the first failure. That is a
   zero-downtime deployment on VMs.
2. **Ansible Galaxy.** `ansible-galaxy collection install community.general` and use a
   community role instead of writing one.
3. **Dynamic inventory.** Replace the static file with the `community.docker.docker_containers`
   inventory plugin, so the host list comes from the Docker API. This is what makes Ansible
   work with autoscaling estates.
4. **Molecule.** Look up `molecule` — it tests roles by converging a container and asserting
   the result, including an idempotence check. Testing infrastructure code is the practice
   most teams skip.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'docker'` | Python Docker SDK missing | `pip3 install --user --break-system-packages docker` |
| `Failed to connect … python3 not found` | The node has no Python | Re-run `ansible/nodes.sh` |
| `System has not been booted with systemd` | systemd not PID 1 in the container | Recreate the nodes; check `--cgroupns=host` |
| `changed` on every run | A raw `command`/`shell` task | Use a module, or add `creates:` / `changed_when:` |
| `Decryption failed` | Wrong Vault password | Check `--vault-password-file` |
| `Config 'DEFAULT_FORKS' … has an invalid value` | An inline `#` comment in `ansible.cfg` | Move the comment to its own line |
| Secrets appear in the log | Missing `no_log` | Add `no_log: true` to that task |

**Clean up:** `docker rm -f web1 web2 db1 && docker network rm ansible-lab`

---

## 🎯 Outcome

Three managed nodes converged from code, provably idempotent, with encrypted secrets, cross-host
templating and a hardened systemd unit — plus a clear view of where Ansible fits alongside
Terraform and Kubernetes.

**Next:** [Lab 15 — End-to-End CI/CD Pipeline](../lab-15-cd-pipeline-to-k8s/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Run `ansible/nodes.sh` before the lab** — the apt install inside three containers takes
  a couple of minutes and will otherwise eat the session.
- **The three things that go wrong:**
  1. Python Docker SDK missing. Have the `pip3 --break-system-packages` line ready.
  2. systemd will not start in the containers on some kernels or in WSL2. Fall back to
     `ansible_connection: docker` without the systemd tasks, or use Multipass VMs.
  3. Delegates edit files inside a container and expect them to persist — a fine moment to
     revisit day 3's writable-layer lesson.
- **The `changed=0` second run is the whole lab.** Put both PLAY RECAPs side by side on the
  projector. Then ask what their current server build script does on a second run.
- **Be honest about scope.** In a fully containerised platform Ansible's classic role
  shrinks — the image *is* the configuration management. It stays valuable for node
  baselines, appliances, network gear, legacy VMs and operational runbooks. Delegates will
  meet both worlds and deserve the straight answer.
- **Debrief question:** "How many of your servers could be rebuilt from code tonight? For the
  rest — what happens if one dies?"
</details>
