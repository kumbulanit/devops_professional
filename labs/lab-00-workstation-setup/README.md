# Lab 00 — Workstation Setup

| | |
|---|---|
| **Day** | 1 |
| **Duration** | 25 minutes (5 if run before the course — please do), plus 15 for the accounts in Step 8 |
| **Module** | 1 — DevOps Foundations |
| **You will produce** | An Ubuntu 24.04 machine with the complete course toolchain, verified, and the GitHub (and optionally GitLab) accounts the labs push to |
| **Feeds into** | Every subsequent lab |

---

## Objective

Install and verify every tool used in the next six days, in one pass, so that no later lab
loses time to installation. You will finish with a `toolcheck.sh` script that proves the
environment is correct — and that you can re-run at the start of any day.

## Prerequisites

- Ubuntu 24.04 LTS (bare metal, VM, WSL2 or a cloud VM), **4 vCPU / 8 GB RAM / 40 GB disk**
- `sudo` rights
- Outbound HTTPS

> **No Ubuntu machine?** Two free options:
> - **Multipass** (local VM, works on Windows/macOS/Linux):
>   `multipass launch 24.04 --name devops --cpus 4 --memory 8G --disk 40G` then
>   `multipass shell devops`
> - **GitHub Codespaces** — 60 free core-hours/month. Create a Codespace on any repo,
>   choose a 4-core machine. Docker is preinstalled; skip step 2.

---

## The fast path — one script

If you just want a working machine, run the installer and skip to Step 7:

```bash
git clone https://github.com/kumbulanit/devops_professional.git ~/devops-course/course-material
sudo ~/devops-course/course-material/scripts/install-ubuntu24.sh
```
**What this does:** installs and verifies **everything the six days need** — base packages
(including `ss`, `lsof`, `dig` and `nc`, which the labs use), Docker + Compose, the GitHub CLI,
kubectl, k3d, Helm, kubeseal, Terraform, Ansible, Trivy, Gitleaks, Syft, pre-commit and **act** (which runs
GitHub Actions workflows on your machine, for Lab 04A). It also
does the *setup* the labs assume: the kernel limits k3s needs, the seven `/etc/hosts` entries
Ingress routes on, your `~/devops-course` workspace with the course material cloned into it,
the Helm repositories day 6 uses, and a pre-pull of the week's container images.
It is **idempotent**: re-run it any time and it only does what is missing.

**Two things it deliberately leaves to you**, because they are your credentials:
`git config --global user.name`/`user.email` (Step 6), and your **accounts** — GitHub, `gh auth login`
and, if you will do Lab 04B, GitLab (Step 8). Do Step 8 even if the script did everything else.

| Flag | Does |
|---|---|
| `--verify` | Check everything, install nothing. Use this at the start of each day |
| `--dry-run` | Print what would happen. Needs no root |
| `--tofu` | Install OpenTofu instead of Terraform (MPL rather than BUSL) |
| `--only base,k8s` | Install just those components |
| `--skip prepull` | Skip the image pre-pull (useful on a slow connection) |

> **Trainers:** send this to delegates three days before the course, and ask them to paste the
> output of `sudo ./scripts/install-ubuntu24.sh --verify`. A green run gives you back 25
> minutes on day 1 — which day 5 will need.

**The rest of this lab does the same work by hand.** Work through it anyway if you want to
understand what the script did — particularly the signed-repository pattern in Step 2, which
is how you should add *any* third-party apt source, and the `curl | bash` discussion, which is
the supply-chain lesson from Module 7 arriving four days early.

---

## Step 1 — Confirm the base system

```bash
lsb_release -a
```
**What this does:** prints the distribution and release. You must see `Ubuntu 24.04`. If you
see 22.04 the labs still work, but package names and the `docker compose` plugin path may
differ from what is written here.

```bash
nproc && free -h && df -h /
```
**What this does:** three checks in one line — `nproc` prints the CPU count, `free -h` prints
memory in human-readable units, `df -h /` prints free space on the root filesystem.
You need **≥ 4 CPUs, ≥ 8 GB RAM (or ≥ 4 GB with swap), ≥ 40 GB free**. Day 4 runs a
three-node Kubernetes cluster and day 6 adds Prometheus and Grafana; under-provisioning here
surfaces as unexplained pod evictions on day 6.

```bash
sudo apt-get update && sudo apt-get install -y \
  curl wget git jq unzip ca-certificates gnupg lsb-release apt-transport-https \
  build-essential python3 python3-pip python3-venv tree htop net-tools
```
**What this does:**
- `apt-get update` refreshes the package index (the local list of what is available). Without
  it, `install` may fail on a stale index.
- `install -y` installs without prompting. Each package earns its place: `curl`/`wget`
  download things; `jq` parses JSON (used constantly with `kubectl -o json`); `gnupg` and
  `ca-certificates` verify repository signatures; `build-essential` compiles Python wheels;
  `python3-venv` creates isolated Python environments; `tree` renders directory structure in
  lab checkpoints.

✅ **Checkpoint**
```bash
python3 --version && git --version && jq --version
```
Expect Python **3.12.x**, git **2.43+**, jq **1.7+**.

---

## Step 2 — Docker Engine

Install from Docker's own repository, **not** from Ubuntu's `docker.io` package — the Ubuntu
package lags badly and ships an old Compose.

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```
**What this does:** creates the directory for third-party repository signing keys, downloads
Docker's public GPG key (`-fsSL` = fail on error, silent, show errors, follow redirects),
converts it from ASCII-armoured to binary (`--dearmor`) which is what `apt` expects, and
makes it world-readable so `apt` can read it as a non-root process.

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
**What this does:** writes the Docker apt repository definition.
`$(dpkg --print-architecture)` resolves to `amd64` or `arm64`; `signed-by=` binds this
repository to that one key so it cannot sign packages for any other repo;
`$(. /etc/os-release && echo "$VERSION_CODENAME")` resolves to `noble` on 24.04.

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```
**What this does:** installs the daemon (`docker-ce`), the CLI, the container runtime
(`containerd.io`), BuildKit's `docker buildx`, and `docker compose` **v2 as a plugin** —
which is why every command in this course is `docker compose` (space) and never
`docker-compose` (hyphen, the deprecated Python v1).

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```
**What this does:** adds you to the `docker` group so you can talk to
`/var/run/docker.sock` without `sudo`, and `newgrp` starts a subshell with the new group
applied immediately instead of making you log out and back in.

> ⚠️ **Gotcha & security note.** If `docker ps` still says *permission denied*, log out and
> back in fully. And understand what you just did: **membership of the `docker` group is
> equivalent to root on this host** — a member can `docker run -v /:/host --privileged` and
> take over the machine. That is acceptable on a personal lab box; on a shared server it is
> a privilege grant that belongs in your access-control policy.

✅ **Checkpoint**
```bash
docker run --rm hello-world && docker compose version
```
**What this does:** `--rm` deletes the container as soon as it exits so it does not
accumulate. Seeing "Hello from Docker!" proves the daemon runs, the socket is reachable as
your user, and outbound access to Docker Hub works. Compose should report **v2.x**.

---

## Step 3 — Kubernetes tooling: kubectl, k3d, Helm

```bash
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl
```
**What this does:** the inner `curl` fetches the current stable version string (e.g.
`v1.31.1`) and substitutes it into the download URL, so you always get the current release.
`install` copies the binary into place while setting owner, group and mode in one atomic
step — safer than `cp` followed by `chmod`.

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```
**What this does:** installs **k3d**, which runs Rancher's lightweight Kubernetes
distribution **k3s inside Docker containers**. This gives you a genuine multi-node cluster on
one laptop in about 30 seconds.

> ⚠️ **`curl | bash` runs code from the internet as you.** It is used here because it is the
> vendor's documented install path and this is a lab machine. In production you fetch,
> **read**, checksum, and then execute. Say this out loud in class — it is a live example of
> the supply-chain risk you will formalise in Module 7.

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
**What this does:** installs **Helm**, the Kubernetes package manager. Day 6 uses it to
install the Prometheus + Grafana stack in one command instead of forty manifests.

✅ **Checkpoint**
```bash
kubectl version --client && k3d version && helm version --short
```

---

## Step 4 — Infrastructure as Code: Terraform and Ansible

```bash
wget -O- https://apt.releases.hashicorp.com/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install -y terraform
```
**What this does:** the same signed-repository pattern as Docker, for HashiCorp's apt repo.

> **Licence note.** Terraform is BUSL-licensed; it is free for this course and for internal
> enterprise use. If your organisation's policy prefers the MPL-licensed fork, install
> **OpenTofu** instead — every command in Lab 13 works with `tofu` in place of `terraform`:
> `curl -fsSL https://get.opentofu.org/install-opentofu.sh -o /tmp/t.sh && sudo bash /tmp/t.sh --install-method deb`

```bash
sudo apt-get install -y ansible ansible-lint
```
**What this does:** installs Ansible and its linter. On Ubuntu 24.04 this gives you
`ansible-core` plus the bundled community collections, which is everything Lab 14 needs.

```bash
pip3 install --user --break-system-packages docker
```
**What this does:** installs the Python Docker SDK for your user only. Ansible's
`community.docker` modules need it. `--break-system-packages` is required on Ubuntu 24.04
because PEP 668 marks the system Python as externally managed; `--user` keeps the install
inside `~/.local` so it cannot damage system packages.

✅ **Checkpoint**
```bash
terraform version && ansible --version | head -1
```

---

## Step 5 — Security tooling

```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sudo sh -s -- -b /usr/local/bin
```
**What this does:** installs **Trivy**, which scans container images, filesystems, git repos
and IaC files for vulnerabilities, misconfigurations and secrets. `-b /usr/local/bin` sets
the install directory.

```bash
GL_VER=$(curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | jq -r .tag_name | tr -d v)
curl -sSL "https://github.com/gitleaks/gitleaks/releases/download/v${GL_VER}/gitleaks_${GL_VER}_linux_x64.tar.gz" \
  | sudo tar -xz -C /usr/local/bin gitleaks
```
**What this does:** asks the GitHub API for the latest release tag, strips the leading `v`
with `tr -d v`, downloads that release's tarball, and pipes it straight into `tar` which
extracts **only** the `gitleaks` binary into `/usr/local/bin` — no temporary file.
**Gitleaks** finds secrets in code and in git history.

```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
  | sudo sh -s -- -b /usr/local/bin
```
**What this does:** installs **Syft**, which generates an SBOM (Software Bill of Materials)
from an image or directory. Used in Lab 17.

✅ **Checkpoint**
```bash
trivy --version && gitleaks version && syft version | head -2
```

---

## Step 6 — Configure git

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.editor nano
```
**What this does, line by line:**
- `user.name` / `user.email` — stamped into **every commit you make** and used by GitHub to
  attribute commits. Use the email attached to your GitHub account or your commits will not
  link to your profile.
- `init.defaultBranch main` — new repositories start on `main` instead of `master`.
- `pull.rebase false` — `git pull` performs a merge. Explicit, and safest for beginners; you
  will meet the rebase alternative in Lab 03.
- `core.editor nano` — the editor git opens for commit messages. Use `vim` if you prefer.

✅ **Checkpoint**
```bash
git config --global --list
```

---

## Step 7 — Create the course workspace and the verification script

```bash
mkdir -p ~/devops-course && cd ~/devops-course
```
**What this does:** creates the single directory that every lab in this course works inside.
`-p` makes it a no-op if it already exists.

```bash
cat > toolcheck.sh <<'EOF'
#!/usr/bin/env bash
# Verifies the full course toolchain. Re-run this at the start of any day.
set -u
fail=0
check() {                       # check <label> <command...>
  local label="$1"; shift
  if out=$("$@" 2>&1); then                     # the TOOL's exit code, not a pipe's
    printf '  \033[32m✔\033[0m %-12s %s\n' "$label" "${out%%$'\n'*}"
  else
    printf '  \033[31m✗\033[0m %-12s NOT FOUND or FAILED\n' "$label"; fail=1
  fi
}
echo "── DevOps Professional toolchain ──"
check git        git --version
check docker     docker --version
check compose    docker compose version
check kubectl    kubectl version --client -o yaml
check k3d        k3d version
check helm       helm version --short
check terraform  terraform version
check ansible    ansible --version
check trivy      trivy --version
check gitleaks   gitleaks version
check syft       syft version
check python     python3 --version
check gh         gh --version
echo "── optional (Lab 04A) ──"
if command -v act >/dev/null 2>&1; then
  printf '  \033[32m✔\033[0m %-12s %s\n' act "$(act --version)"
else
  printf '  - %-12s not installed — only needed for Lab 04A (Step 8.4)\n' act
fi
echo "── daemon check ──"
if docker info >/dev/null 2>&1; then
  printf '  \033[32m✔\033[0m docker daemon reachable without sudo\n'
else
  printf '  \033[31m✗\033[0m docker daemon NOT reachable — log out and back in\n'; fail=1
fi
echo
[ "$fail" -eq 0 ] && echo "ALL CHECKS PASSED — you are ready." \
                  || { echo "SOME CHECKS FAILED — fix before continuing."; exit 1; }
EOF
chmod +x toolcheck.sh
./toolcheck.sh
```
**What this does:** writes a verification script and runs it.
- `<<'EOF'` — the **quoted** heredoc delimiter is important: it stops the shell expanding
  `$1`, `$@` and the escape sequences while writing the file, so the script is stored
  literally.
- `set -u` makes the script fail on an undefined variable.
- `if out=$("$@" 2>&1)` tests the **tool's own** exit code. (Piping it through `head` first would
  test `head`'s exit code instead — which is always success, so a missing tool would get a green
  tick.) `${out%%$'\n'*}` keeps only the first line of the output.
- `chmod +x` makes it executable; `./toolcheck.sh` runs it from the current directory.

✅ **Final checkpoint:** the script must print **ALL CHECKS PASSED**.

---

## Step 8 — Accounts and collaboration tools (15 min — do this before the course)

From Day 2 your code lives on GitHub, and the optional Labs 04A and 04B use `act` and GitLab.
**Accounts are the slowest thing to set up** — confirmation emails, two-factor codes, identity
checks — and the one thing a trainer cannot do for you in the room.

| Step | Needed for | Required? |
|---|---|---|
| 8.1 GitHub account + `gh` sign-in | Labs 03 onwards | **Yes** |
| 8.2 SSH key | Lab 04B (GitLab); optional for GitHub | Recommended |
| 8.3 GitLab account | Lab 04B | Optional |
| 8.4 act | Lab 04A | Optional |

### Step 8.1 — Your GitHub account

1. **Sign up** at **https://github.com/signup** (skip if you already have an account). Use an
   email address you will keep after the course, and choose the **Free** plan. Your **username**
   appears in every repository URL — `github.com/<username>/paytrack-api` — so pick one you are
   happy for a colleague to see.
2. **Verify your email address** from the message GitHub sends.
3. **Turn on two-factor authentication:** your avatar (top right) → **Settings** → **Password and
   authentication** → **Enable two-factor authentication** → use an authenticator app. **Download
   the recovery codes** and keep them somewhere safe. GitHub requires 2FA from people who contribute
   code, so it will ask you sooner or later — better now than halfway through Lab 03.
4. **Keep your email address private:** **Settings** → **Emails** → tick **Keep my email addresses
   private**. GitHub shows you a private address such as
   `12345678+your-username@users.noreply.github.com`. Copy it, and use it for your commits:

```bash
git config --global user.email "12345678+your-username@users.noreply.github.com"
git config --global user.email
```
**What this does:** replaces the email you set in Step 6 with GitHub's private "noreply" address,
then prints it so you can check it. Every commit you push is public on a public repository; this
way your commits still link to your GitHub profile, but your real address is not published.
(Paste **your** address from the Emails page — the number is different for everyone.)

Back on the Emails page, also tick **Block command line pushes that expose my email**. From now
on GitHub refuses a push containing a commit with your private address, with the error `GH007`,
instead of publishing it.

```bash
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
```
**What this does:** signs the GitHub CLI **and git** in to your account, with no password or token
to copy by hand.
- Answer **Y** to *Authenticate Git with your GitHub credentials?* — `gh` then acts as git's
  credential helper, so `git push` to GitHub just works.
- `gh` prints a **one-time code** and opens a browser (on a machine with no browser, open
  **https://github.com/login/device** on your laptop or phone). Enter the code and approve.
- `--scopes workflow` adds permission to push changes to `.github/workflows/`. Without it, Lab 04's
  push fails with `refusing to allow an OAuth App to create or update workflow`.

```bash
gh auth status
git config --global --get-regexp '^credential'
```
**What this does:** `gh auth status` shows `✓ Logged in to github.com account <your-username>` and
the token's scopes, which must include `'workflow'`. The second command shows that git now asks
`gh auth git-credential` for GitHub passwords.

> **Already signed in without `workflow`?** Run `gh auth refresh -s workflow`.
> **Prefer a token?** Lab 03 Step 1.2 explains a fine-grained personal access token instead.

### Step 8.2 — An SSH key

```bash
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -C "$(git config --global user.email)" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```
**What this does:** creates an SSH key pair **only if you do not already have one**, labelled with
your git email, then prints the **public** half.
- `ssh-keygen` asks for a **passphrase**. Use one: it protects the key if your laptop is stolen, and
  `ssh-agent` remembers it for the session so you do not type it on every push.
- `~/.ssh/id_ed25519` is the **private** key — it never leaves this machine and you never paste it
  anywhere. `~/.ssh/id_ed25519.pub` is the **public** key — safe to give to GitHub and GitLab.

**GitHub (optional — `gh` already handles HTTPS).** To use SSH as well: **Settings** → **SSH and GPG
keys** → **New SSH key** → paste the `.pub` line → **Add SSH key**. Then:

```bash
ssh -T git@github.com
```
**What this does:** tests the key against GitHub. The first time, SSH shows GitHub's fingerprint.
**Compare it** with GitHub's published value before typing `yes`:
`SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`. Success reads
`Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.`
The exit code is 1 even when it works — that is normal.

### Step 8.3 — A GitLab account (optional — for Lab 04B)

If you will do Lab 04B, **open the account now**: GitLab.com may ask new users to verify their
identity with a phone number or a card (checked, not charged) before they can run pipelines, and
that can take time. Follow **[Lab 04B, Part 1](../lab-04b-gitlab-ci/README.md#part-1--open-a-gitlab-account-and-secure-it-10-min)**:
sign up, verify, turn on two-factor authentication, add the SSH key from Step 8.2, and run
`ssh -T git@gitlab.com`.

### Step 8.4 — act (optional — for Lab 04A)

Skip this if the course installer ran: it installs act for you.

```bash
ACT_VERSION=0.2.89
ACT_ARCH=$(uname -m | sed 's/aarch64/arm64/')
cd /tmp
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/act_Linux_${ACT_ARCH}.tar.gz"
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/checksums.txt"
grep " act_Linux_${ACT_ARCH}.tar.gz\$" checksums.txt | sha256sum -c -
sudo tar -xzf "act_Linux_${ACT_ARCH}.tar.gz" -C /usr/local/bin act
act --version
cd ~/devops-course
```
**What this does:** downloads a pinned act release **and the project's checksum list**, and checks
the download against it — you must see `act_Linux_x86_64.tar.gz: OK` (or `arm64`) — before
extracting the single `act` binary into `/usr/local/bin`. Download, **verify**, then install: the
responsible version of the `curl | bash` pattern from Step 3. Lab 04A explains how to use it.

✅ **Checkpoint**
```bash
~/devops-course/toolcheck.sh
gh auth status
```
`toolcheck.sh` passes (with `act` either ticked or marked optional), and `gh` is logged in with the
`workflow` scope.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `permission denied … docker.sock` | Group membership not applied to this shell | Log out and back in, or `newgrp docker` |
| `k3d` cluster fails later with `too many open files` | Default inotify limits are too low for k3s | `echo -e "fs.inotify.max_user_watches=524288\nfs.inotify.max_user_instances=512" | sudo tee /etc/sysctl.d/99-k3d.conf && sudo sysctl --system` |
| `pip3 install` → "externally-managed-environment" | PEP 668 on Ubuntu 24.04 | Add `--user --break-system-packages`, or use a venv |
| Corporate TLS interception breaks `curl` | Proxy re-signs certificates | Add the corporate CA to `/usr/local/share/ca-certificates/` then `sudo update-ca-certificates` |
| Docker Hub `toomanyrequests` | Anonymous pull limit (100 / 6 h) | `docker login` with a free Docker Hub account |
| `gh auth login` cannot open a browser | A server or VM with no desktop | Open **https://github.com/login/device** on any device and type the code `gh` printed |
| `GH007: Your push would publish a private email address` | A commit carries the email you asked GitHub to keep private | `git config --global user.email` with your noreply address, then `git commit --amend --reset-author --no-edit` on the unpushed commit |
| `Permission denied (publickey)` | The SSH key is not on your account, or a different key is offered | `ssh -vT git@github.com` shows which key is tried |
| Low on disk later in the week | Images and volumes accumulate | `docker system df` to see usage, `docker system prune -a --volumes` to reclaim (**deletes unused volumes**) |

---

## 🎯 Outcome

A verified Ubuntu 24.04 workstation with git, Docker + Compose, kubectl, k3d, Helm,
Terraform, Ansible, Trivy, Gitleaks, Syft, the GitHub CLI and (optionally) act, plus
`~/devops-course/toolcheck.sh` — and a GitHub account with two-factor authentication, a private
commit email and `gh` signed in (plus, optionally, a verified GitLab account).

**Next:** [Lab 01 — Value Stream Mapping](../lab-01-value-stream-mapping/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Send this lab out 3 days before the course.** Delegates who arrive with a green
  `toolcheck.sh` give you back 25 minutes on day 1 — which day 5 will need.
- **Put Step 8 in the pre-course email, in bold.** A delegate who meets GitHub's 2FA prompt or
  GitLab's identity check during Lab 03 loses the lab. Ask for a screenshot of `gh auth status`.
- **The three failures that actually happen:**
  1. Docker group not applied — they did not log out. Fix with `newgrp docker`.
  2. Corporate proxy / TLS interception kills every `curl`. Have the CA certificate
     instructions ready before the room starts.
  3. 4 GB VMs. They survive to day 4 and then fail with evictions on day 6. Check RAM
     explicitly; do not take "it's fine" for an answer.
- **Teaching moment:** pause on the `curl | bash` steps and ask the room what could go wrong.
  It sets up Module 7 four days early and they will remember it.
- **Debrief question:** "How long would it take a new joiner at your organisation to reach a
  working development environment? What is that number costing you?"
</details>
