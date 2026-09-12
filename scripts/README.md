# scripts/

## `install-ubuntu24.sh` — workstation setup

One command to get an Ubuntu 24.04 machine ready for all six days.

```bash
sudo ./install-ubuntu24.sh
```

**Idempotent.** Every step checks before it acts, so re-running only fills in what is missing.

| Flag | Effect |
|---|---|
| *(none)* | Install and verify everything |
| `--verify` | Check only, install nothing. **Run this at the start of each day** |
| `--dry-run` | Print what would happen. Needs no root, changes nothing |
| `--tofu` | OpenTofu instead of Terraform (MPL rather than BUSL) |
| `--only base,k8s` | Only those components |
| `--skip prepull` | Skip the image pre-pull (slow connections) |
| `--help` | Usage |

Components: `base` · `docker` · `sysctl` · `k8s` · `iac` · `security` · `gitcfg` · `prepull`

### What it installs

| Group | Tools |
|---|---|
| base | git, curl, wget, jq, gnupg, tree, htop, dnsutils, build-essential, python3 + venv + pip |
| docker | Docker Engine, CLI, containerd, buildx, **compose v2 plugin**; adds you to the `docker` group |
| sysctl | Raises `fs.inotify` limits — k3s fails in confusing ways without this |
| k8s | kubectl (latest stable), k3d, Helm, kubeseal |
| iac | Terraform (or OpenTofu), Ansible + ansible-lint, Python Docker SDK |
| security | Trivy, Gitleaks, Syft, pre-commit |
| gitcfg | `init.defaultBranch=main`, `pull.rebase=false`, a `git lg` alias |
| prepull | python:3.12-slim, postgres:16-alpine, nginx:1.27-alpine, busybox, curl, alpine, the pinned k3s image |

Versions are **pinned at the top of the script** so a classroom is reproducible. `kubectl`
tracks latest stable deliberately — it must match whatever cluster a delegate later connects to.

### After it runs

1. **Log out and back in.** Docker group membership does not apply to your current session.
2. Set your git identity — the script cannot invent it:
   ```bash
   git config --global user.name  "Your Name"
   git config --global user.email "you@example.com"
   ```
3. Re-check any time: `sudo ./install-ubuntu24.sh --verify`

Log: `/var/log/devops-course-install.log` (or `$TMPDIR` if `/var/log` is not writable).

### Notes

- **Architecture-aware.** Handles amd64 and arm64. Each upstream names its release assets
  differently and the mappings in the script are checked against the real releases —
  gitleaks calls amd64 `x64`, Trivy calls it `64bit` and arm64 `ARM64`. Do not "tidy" those
  into one variable.
- **Per-tool failures are non-fatal.** One dead upstream URL is reported at the end rather
  than stopping everything after it.
- **`sudo` is not required to exist.** Falls back to `runuser`, or runs directly if you are
  already the target user.
- **Membership of the `docker` group is equivalent to root on the host.** Fine on a lab
  machine; on a shared server it is an access-control decision.

### Trainer checklist

Send this to delegates **three days before** the course and ask for the output of:

```bash
sudo ./install-ubuntu24.sh --verify
```

A green run gives you back ~25 minutes on day 1 — which day 5 will need.

---

## Scripts the labs generate

These are created by delegates during the labs and are documented there, not here:

| Script | Lab | Purpose |
|---|---|---|
| `toolcheck.sh` | 00 | Quick toolchain check (the installer's `--verify` supersedes it) |
| `gitops-sync.sh` | 15 | The in-cluster reconciler — a 40-line Argo CD |
| `verify-platform.sh` | 19 | Nine-layer end-to-end verification of everything built |
| `gameday.sh` | 19 | Injects one of five failures for the capstone game day |
