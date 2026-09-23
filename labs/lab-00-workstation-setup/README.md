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

## Before you start — how to use a terminal

**This course assumes no Linux experience.** Everything below is **one command in one grey box**,
numbered in the order you run it. Read this table once and you have all you need:

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. (Or press the ⊞ key, type `terminal`, press `Enter`.) A window opens showing a line that ends in `$` — the **prompt**. |
| **How do I run a command?** | Click into the terminal window, type or paste the contents of one box, then press `Enter`. |
| **How do I paste?** | Copy from this page with `Ctrl` + `C`, then paste into the terminal with **`Ctrl` + `Shift` + `V`**. In a terminal, plain `Ctrl` + `V` does nothing. |
| **When is it finished?** | When the `$` prompt comes back. Some commands here download hundreds of megabytes — wait for the prompt before running the next box. |
| **Nothing was printed!** | Normal. Many commands say nothing when they succeed: in Linux, silence means "done". |
| **It asked for a password** | Any command starting with `sudo` does. Type your **login** password. **Nothing appears as you type** — not even dots. Press `Enter`. |
| **The screen filled up and the last line is `:` or `(END)`** | You are in a scrollable view. Press `q` to get back to the prompt. |
| **It seems stuck** | Press `Ctrl` + `C` to cancel and get the prompt back. |
| **An editor opened and I am trapped** | It is **nano**. Save and leave with `Ctrl` + `O`, `Enter`, then `Ctrl` + `X`. |
| **I typed it wrong** | Nothing is broken. Read the error, then type it again. Upper and lower case matter, and so do spaces. |

**Symbols you will meet in the boxes:**

| Symbol | Means |
|---|---|
| `sudo` | Run this one command as the machine's administrator. Needed to install software |
| `~` | Your home folder — `/home/<your-name>`. `~/devops-course` is a folder inside it |
| `cd` | **C**hange **D**irectory: move into a folder. Everything you type afterwards happens there |
| `\|` | "Pipe": send what the first command prints into the second command |
| `>` / `>>` | Put what the command prints **into** a file / **onto the end of** a file |
| `$(…)` | Run the command in the brackets first, and use its answer here |
| `&&` | Only run the next part if this part succeeded |
| `\` at the end of a line | The command continues on the next line. Copy **all** the lines of the box |
| `#` | A note for humans; the computer ignores the rest of the line |

---

## The fast path — one script

If you just want a working machine, run these two commands and skip to Step 7.

**1. Download the course material.**

```bash
git clone https://github.com/kumbulanit/devops_professional.git ~/devops-course/course-material
```
**What this does:** `git clone` copies a project from the internet onto your machine — here into
the folder `~/devops-course/course-material`. It prints a few progress lines and ends with the
prompt.

**2. Run the installer.**

```bash
sudo ~/devops-course/course-material/scripts/install-ubuntu24.sh
```
**What this does:** runs the installer script as administrator (so it may install software). It
prints a line per tool and takes 10–20 minutes the first time.
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

**1. Check which Ubuntu you are on.**

```bash
lsb_release -a
```
**What this does:** prints the distribution and release. You must see `Ubuntu 24.04`. If you
see 22.04 the labs still work, but package names and the `docker compose` plugin path may
differ from what is written here.

**2. Count your CPUs.**

```bash
nproc
```
**What this does:** prints the number of processor cores as a single number. You need **4 or
more**.

**3. Check your memory.**

```bash
free -h
```
**What this does:** prints memory in human-readable units (`-h`). Read the `Mem:` row, `total`
column: you need **8 GB**, or 4 GB plus swap.

**4. Check your free disk space.**

```bash
df -h /
```
**What this does:** **d**isk **f**ree for `/`, the main filesystem. The `Avail` column must show
**40 GB or more**. Day 4 runs a three-node Kubernetes cluster and day 6 adds Prometheus and
Grafana; under-provisioning here surfaces as unexplained pod evictions on day 6.

**5. Refresh the list of available software.**

```bash
sudo apt-get update
```
**What this does:** `apt-get` is Ubuntu's software installer; `update` refreshes its local
catalogue of what is available. Without it, an install can fail on a stale list. It prints a
page of `Hit:`/`Get:` lines.

**6. Install the base packages.**

```bash
sudo apt-get install -y \
  curl wget git jq unzip ca-certificates gnupg lsb-release apt-transport-https \
  build-essential python3 python3-pip python3-venv tree htop net-tools
```
**What this does:** installs all of those packages in one go. The box is **one command** spread
over three lines — the `\` at the end of a line means "continues below", so copy all three lines.
`-y` answers "yes" to the confirmation prompt. Each package earns its place: `curl`/`wget`
download things; `jq` reads JSON (used constantly with `kubectl -o json`); `gnupg` and
`ca-certificates` verify repository signatures; `build-essential` compiles Python packages;
`python3-venv` creates isolated Python environments; `tree` draws folder structures in lab
checkpoints.

✅ **Checkpoint** — three commands, each printing one version.

```bash
python3 --version
```
**What this does:** expect **3.12.x**.

```bash
git --version
```
**What this does:** expect **2.43** or newer.

```bash
jq --version
```
**What this does:** expect **1.7** or newer.

---

## Step 2 — Docker Engine

Install from Docker's own repository, **not** from Ubuntu's `docker.io` package — the Ubuntu
package lags badly and ships an old Compose.

**1. Make the folder that holds repository signing keys.**

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```
**What this does:** `install -d` creates a directory and sets its permissions in one step;
`-m 0755` means "everyone can read it, only the administrator can change it". Nothing is printed.

**2. Download Docker's signing key into that folder.**

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```
**What this does:** one command over two lines. `curl` downloads Docker's public key (`-fsSL` =
fail on error, stay silent, still show errors, follow redirects), the `|` passes it to `gpg`,
which converts it from text to the binary form apt expects (`--dearmor`) and saves it (`-o`).

**3. Let apt read the key.**

```bash
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```
**What this does:** `chmod a+r` gives **a**ll users **r**ead permission, so apt can use the key
without being root.

**4. Add Docker's software repository.**

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
**What this does:** one command over three lines — copy all of it. It writes a line telling apt
where Docker's packages live. `$(dpkg --print-architecture)` fills in `amd64` or `arm64`;
`signed-by=` ties this repository to that one key, so it cannot vouch for any other;
`$(. /etc/os-release && echo "$VERSION_CODENAME")` fills in `noble` on 24.04. `tee` writes the
line to a file as administrator, and `> /dev/null` throws away the copy it would print.

**5. Refresh the catalogue so apt sees the new repository.**

```bash
sudo apt-get update
```
**What this does:** as in Step 1 — but now the list includes Docker's packages.

**6. Install Docker.**

```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```
**What this does:** one command over two lines. It installs the engine (`docker-ce`), the command
you type (`docker-ce-cli`), the container runtime (`containerd.io`), the image builder
(`docker-buildx-plugin`) and `docker compose` **v2 as a plugin** — which is why every command in
this course is `docker compose` (with a space) and never `docker-compose` (with a hyphen, the
retired version). This downloads a few hundred megabytes.

**7. Give your user permission to use Docker.**

```bash
sudo usermod -aG docker "$USER"
```
**What this does:** adds you (`"$USER"` is your login name) to the `docker` group, so you can use
Docker without typing `sudo` every time. Nothing is printed, and it does not take effect yet.

**8. Make the new group apply right now.**

```bash
newgrp docker
```
**What this does:** starts a fresh shell that has the new group, so you do not have to log out and
back in. The prompt comes back looking the same — that is expected.

> ⚠️ **Gotcha & security note.** If `docker ps` still says *permission denied*, log out and
> back in fully. And understand what you just did: **membership of the `docker` group is
> equivalent to root on this host** — a member can `docker run -v /:/host --privileged` and
> take over the machine. That is acceptable on a personal lab box; on a shared server it is
> a privilege grant that belongs in your access-control policy.

✅ **Checkpoint** — two commands.

```bash
docker run --rm hello-world
```
**What this does:** downloads a tiny test image and runs it; `--rm` deletes the container the
moment it finishes, so nothing is left behind. Seeing **"Hello from Docker!"** proves three
things at once: the Docker service is running, your user may talk to it, and the machine can
reach Docker Hub.

```bash
docker compose version
```
**What this does:** prints the Compose version. It must start with **v2**.

---

## Step 3 — Kubernetes tooling: kubectl, k3d, Helm

**1. Download kubectl, the command that talks to Kubernetes.**

```bash
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```
**What this does:** the `curl` inside the brackets asks Kubernetes which version is current (for
example `v1.31.1`), and that answer is dropped into the download address. `-O` saves the file
under its own name, `-L` follows redirects. You get a progress bar and a file called `kubectl` in
the current folder.

**2. Install it.**

```bash
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```
**What this does:** copies the file into `/usr/local/bin` (where programs everyone can run live)
while setting its owner, group and permissions in one step — safer than copying and then changing
them. Nothing is printed.

**3. Delete the downloaded copy.**

```bash
rm kubectl
```
**What this does:** `rm` removes the file you downloaded; the installed copy stays. There is no
recycle bin, so only ever `rm` something you meant to.

**4. Install k3d.**

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

**5. Install Helm.**

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
**What this does:** downloads Helm's install script and runs it (`| bash`). **Helm** is the
package manager for Kubernetes: day 6 uses it to install Prometheus and Grafana with one command
instead of forty configuration files.

✅ **Checkpoint** — three commands, each naming the tool you just installed.

```bash
kubectl version --client
```
**What this does:** prints kubectl's own version (`--client` means "do not try to contact a
cluster" — you have not built one yet).

```bash
k3d version
```
**What this does:** prints the k3d and k3s versions.

```bash
helm version --short
```
**What this does:** prints Helm's version on one line. Expect something starting `v3`.

---

## Step 4 — Infrastructure as Code: Terraform and Ansible

This is the same four-move pattern as Docker: **key → repository → refresh → install**.

**1. Download HashiCorp's signing key.**

```bash
wget -O- https://apt.releases.hashicorp.com/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
```
**What this does:** one command over two lines. `wget -O-` downloads and prints the key, the `|`
hands it to `gpg`, which converts and saves it. Nothing else is printed.

**2. Add HashiCorp's repository.**

```bash
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list
```
**What this does:** one command over three lines. It writes the repository line, tied to the key
from the previous command. `$(lsb_release -cs)` fills in your Ubuntu codename (`noble`). `tee`
prints the line as well as writing it, so you can check it.

**3. Refresh the catalogue.**

```bash
sudo apt-get update
```
**What this does:** apt now knows about HashiCorp's packages.

**4. Install Terraform.**

```bash
sudo apt-get install -y terraform
```
**What this does:** installs Terraform, the tool Lab 13 uses to create infrastructure from code.

> **Licence note.** Terraform is BUSL-licensed; it is free for this course and for internal
> enterprise use. If your organisation's policy prefers the MPL-licensed fork, install
> **OpenTofu** instead — every command in Lab 13 works with `tofu` in place of `terraform`:
> `curl -fsSL https://get.opentofu.org/install-opentofu.sh -o /tmp/t.sh && sudo bash /tmp/t.sh --install-method deb`

**5. Install Ansible.**

```bash
sudo apt-get install -y ansible ansible-lint
```
**What this does:** installs Ansible and its linter (a tool that checks your Ansible files for
mistakes). On Ubuntu 24.04 this gives you `ansible-core` plus the bundled community collections,
which is everything Lab 14 needs.

**6. Install the Python library Ansible needs for Docker.**

```bash
pip3 install --user --break-system-packages docker
```
**What this does:** installs the Python Docker SDK for your user only. Ansible's
`community.docker` modules need it. `--break-system-packages` is required on Ubuntu 24.04
because PEP 668 marks the system Python as externally managed; `--user` keeps the install
inside `~/.local` so it cannot damage system packages.

✅ **Checkpoint** — two commands.

```bash
terraform version
```
**What this does:** prints Terraform's version. Expect **1.x**.

```bash
ansible --version | head -1
```
**What this does:** Ansible prints a dozen lines; `| head -1` keeps only the first, which carries
the version.

---

## Step 5 — Security tooling

**1. Install Trivy.**

```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sudo sh -s -- -b /usr/local/bin
```
**What this does:** one command over two lines. It downloads Trivy's install script and runs it as
administrator, telling it to install into `/usr/local/bin` (`-b`). **Trivy** scans container
images, folders, git repositories and infrastructure code for known vulnerabilities,
misconfigurations and leaked secrets.

**2. Find the newest Gitleaks version.**

```bash
GL_VER=$(curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | jq -r .tag_name | tr -d v)
```
**What this does:** asks GitHub for the latest release, `jq -r .tag_name` picks the version out of
the JSON answer, `tr -d v` deletes the leading "v", and `GL_VER=` stores the result under that
name for the next command. Nothing is printed.

**3. Download and install Gitleaks.**

```bash
curl -sSL "https://github.com/gitleaks/gitleaks/releases/download/v${GL_VER}/gitleaks_${GL_VER}_linux_x64.tar.gz" \
  | sudo tar -xz -C /usr/local/bin gitleaks
```
**What this does:** one command over two lines. `${GL_VER}` is replaced by the version you just
stored; the download is piped straight into `tar`, which unpacks **only** the `gitleaks` program
into `/usr/local/bin` — no leftover file. **Gitleaks** finds secrets in code and in git history.

**4. Install Syft.**

```bash
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
  | sudo sh -s -- -b /usr/local/bin
```
**What this does:** the same install pattern as Trivy. **Syft** lists everything inside an image
or folder as an SBOM (Software Bill of Materials). Lab 17 uses it.

✅ **Checkpoint** — three commands.

```bash
trivy --version
```
**What this does:** prints Trivy's version and the age of its vulnerability database.

```bash
gitleaks version
```
**What this does:** prints one version number.

```bash
syft version | head -2
```
**What this does:** prints Syft's details; `| head -2` keeps the first two lines.

---

## Step 6 — Configure git

Five settings, one command each. `--global` means "for every repository on this machine". None of
them prints anything.

**1. Your name.**

```bash
git config --global user.name  "Your Name"
```
**What this does:** stamps this name into **every commit you make**. Replace `Your Name` with your
own, keeping the quotes.

**2. Your email address.**

```bash
git config --global user.email "you@example.com"
```
**What this does:** the address GitHub uses to attribute commits to you. Use the one attached to
your GitHub account, or your commits will not link to your profile. (Step 8.1 replaces this with a
private GitHub address.)

**3. The name of the first branch in a new repository.**

```bash
git config --global init.defaultBranch main
```
**What this does:** new repositories start on `main` instead of the older `master`.

**4. What `git pull` should do.**

```bash
git config --global pull.rebase false
```
**What this does:** makes `git pull` join histories with a merge — explicit, and the safest
default. You meet the alternative, rebase, in Lab 03.

**5. Which editor git opens.**

```bash
git config --global core.editor nano
```
**What this does:** when git needs a message from you it opens **nano**, which tells you its keys
along the bottom of the screen (`^O` means `Ctrl`+`O` to save, `^X` to exit). Use `vim` instead if
you already know it.

✅ **Checkpoint**

```bash
git config --global --list
```
**What this does:** prints all five settings back to you. Check the spelling of your email.

---

## Step 7 — Create the course workspace and the verification script

**1. Create the course folder.**

```bash
mkdir -p ~/devops-course
```
**What this does:** `mkdir` **m**a**k**es a **dir**ectory; `-p` means "do nothing if it already
exists". This one folder holds every lab's work for the whole week.

**2. Go into it.**

```bash
cd ~/devops-course
```
**What this does:** makes it your current folder, so the file you write next lands there.

**3. Write the verification script.**

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
```
**What this does:** this whole box is **one command** — copy every line of it, including the last
`EOF`, and press `Enter` once. `cat > toolcheck.sh <<'EOF'` means "write everything that follows,
up to the line that says `EOF`, into the file `toolcheck.sh`". Nothing is printed. Inside the
script:
- `<<'EOF'` in **quotes** stops the shell replacing `$1`, `$@` and the colour codes as it writes,
  so the script is stored exactly as you see it.
- `set -u` makes the script stop if it uses a name that was never set.
- `if out=$("$@" 2>&1)` tests the **tool's own** success. (Piping it through `head` first would
  test `head` instead — which always succeeds, so a missing tool would get a green tick.)
  `${out%%$'\n'*}` keeps only the first line of what the tool printed.

**4. Make the script runnable.**

```bash
chmod +x toolcheck.sh
```
**What this does:** `chmod +x` marks the file as a program you may run. Without it, Linux refuses
with *Permission denied*. Nothing is printed.

**5. Run it.**

```bash
./toolcheck.sh
```
**What this does:** runs the script. `./` means "the one in this folder" — Linux does not look in
the current folder unless you say so. You get one line per tool.

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

**a. Tell git to use that address.**

```bash
git config --global user.email "12345678+your-username@users.noreply.github.com"
```
**What this does:** replaces the email you set in Step 6 with GitHub's private "noreply" address.
Nothing is printed. **Paste your own address** from the Emails page — the number is different for
everyone.

**b. Check it took.**

```bash
git config --global user.email
```
**What this does:** asking for a setting without giving it a value prints the current one. Every
commit you push is public on a public repository; this way your commits still link to your GitHub
profile, but your real address is not published.

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

**a. Check you are signed in.**

```bash
gh auth status
```
**What this does:** shows `✓ Logged in to github.com account <your-username>` and the token's
scopes, which must include `'workflow'`.

**b. Check git will use that sign-in.**

```bash
git config --global --get-regexp '^credential'
```
**What this does:** prints every setting whose name starts with `credential`. You should see git
asking `gh auth git-credential` for GitHub passwords — which is why `git push` will not prompt you.

> **Already signed in without `workflow`?** Run `gh auth refresh -s workflow`.
> **Prefer a token?** Lab 03 Step 1.2 explains a fine-grained personal access token instead.

### Step 8.2 — An SSH key

**a. Create the key pair (only if you have none).**

```bash
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -C "$(git config --global user.email)" -f ~/.ssh/id_ed25519
```
**What this does:** `[ -f <file> ]` asks "does this file exist?" and `||` means "if not, do the
next thing" — so an existing key is never overwritten. `ssh-keygen` then makes a new pair, labelled
with your git email.
- It asks for a **passphrase**. Use one: it protects the key if your laptop is stolen, and
  `ssh-agent` remembers it for the session so you do not type it on every push. **Nothing appears
  as you type** — that is normal.
- `~/.ssh/id_ed25519` is the **private** key — it never leaves this machine and you never paste it
  anywhere. `~/.ssh/id_ed25519.pub` is the **public** key — safe to give to GitHub and GitLab.

**b. Print the public half.**

```bash
cat ~/.ssh/id_ed25519.pub
```
**What this does:** `cat` prints a file. You get one line starting `ssh-ed25519` — this is what you
paste into GitHub and GitLab. Copy it with `Ctrl` + `Shift` + `C`.

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

Eight commands, one at a time. They download a pinned release, **check it is genuine**, and only
then install it — the responsible version of the `curl | bash` pattern from Step 3.

**a. Choose the version.**

```bash
ACT_VERSION=0.2.89
```
**What this does:** remembers the version number under that name for this terminal window. Nothing
is printed.

**b. Work out which build your machine needs.**

```bash
ACT_ARCH=$(uname -m | sed 's/aarch64/arm64/')
```
**What this does:** `uname -m` prints your processor type; `sed` rewrites `aarch64` as `arm64`,
which is what act calls it. The answer is stored under the name `ACT_ARCH`.

**c. Move to the scratch folder.**

```bash
cd /tmp
```
**What this does:** `/tmp` is emptied when the machine restarts — the right place for a download.

**d. Download the release.**

```bash
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/act_Linux_${ACT_ARCH}.tar.gz"
```
**What this does:** `curl` fetches a file from the internet; `-O` saves it under its own name and
`-fsL` keep it quiet and follow redirects.

**e. Download the project's checksum list.**

```bash
curl -fsSLO "https://github.com/nektos/act/releases/download/v${ACT_VERSION}/checksums.txt"
```
**What this does:** fetches the fingerprints the act project published for this release.

**f. Check the download is genuine.**

```bash
grep " act_Linux_${ACT_ARCH}.tar.gz\$" checksums.txt | sha256sum -c -
```
**What this does:** `grep` picks out the line about your file, and `sha256sum -c` re-calculates the
fingerprint of what you downloaded and compares them. You must see
`act_Linux_x86_64.tar.gz: OK` (or `arm64`). **If it says FAILED, stop and do not install it.**

**g. Install it.**

```bash
sudo tar -xzf "act_Linux_${ACT_ARCH}.tar.gz" -C /usr/local/bin act
```
**What this does:** unpacks just the `act` program into `/usr/local/bin`, where programs everyone
can run live — which is why it needs `sudo` and your password.

**h. Check it runs.**

```bash
act --version
```
**What this does:** prints `act version 0.2.89`.

**i. Go back to your course folder.**

```bash
cd ~/devops-course
```
**What this does:** leaves the scratch folder. Lab 04A explains how to use act.

✅ **Checkpoint** — two commands.

```bash
~/devops-course/toolcheck.sh
```
**What this does:** re-runs the tool check from Step 7. Every line should carry a green ✔, with
`act` either ticked or marked optional.

```bash
gh auth status
```
**What this does:** confirms `gh` is logged in and its scopes include `'workflow'`.

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
