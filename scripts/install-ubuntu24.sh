#!/usr/bin/env bash
# =============================================================================
#  DevOps Professional — workstation installer for Ubuntu 24.04 LTS
#
#  Installs and verifies every tool used across the six days.
#
#    sudo ./install-ubuntu24.sh                  # install everything
#    sudo ./install-ubuntu24.sh --verify         # check only, install nothing
#    sudo ./install-ubuntu24.sh --only docker,k8s
#    sudo ./install-ubuntu24.sh --skip jenkins-img
#    sudo ./install-ubuntu24.sh --tofu           # OpenTofu instead of Terraform
#    ./install-ubuntu24.sh --dry-run             # print what would happen
#
#  Safe to re-run: every step checks before it acts.
# =============================================================================
set -Eeuo pipefail

# ── versions: pinned so a classroom is reproducible ──────────────────────────
K3D_VERSION="v5.7.4"
HELM_VERSION="v3.16.2"
KUBESEAL_VERSION="0.27.1"
GITLEAKS_VERSION="8.21.2"
TRIVY_VERSION="0.74.0"
SYFT_VERSION="1.14.0"
K3S_IMAGE="rancher/k3s:v1.31.2-k3s1"      # matches k8s/k3d-cluster.yaml
COURSE_REPO="https://github.com/kumbulanit/devops_professional.git"

LOG="/var/log/devops-course-install.log"
[[ -w /var/log ]] || LOG="${TMPDIR:-/tmp}/devops-course-install.log"

RED=$'\e[31m'; GRN=$'\e[32m'; YLW=$'\e[33m'; BLU=$'\e[36m'; BLD=$'\e[1m'; RST=$'\e[0m'
DRY=0; VERIFY_ONLY=0; USE_TOFU=0; ONLY=""; SKIP=""; ASSUME_YES=0
FAILED=(); INSTALLED=(); SKIPPED=()

say()  { printf '%s\n' "$*" | tee -a "$LOG" >/dev/null; printf '%s\n' "$*"; }
info() { say "${BLU}::${RST} $*"; }
ok()   { say "  ${GRN}✔${RST} $*"; }
warn() { say "  ${YLW}!${RST} $*"; }
err()  { say "  ${RED}✘${RST} $*"; }
hdr()  { say ""; say "${BLD}$*${RST}"; }

run() {
  if (( DRY )); then say "    ${YLW}[dry-run]${RST} $*"; return 0; fi
  echo "+ $*" >>"$LOG"
  "$@" >>"$LOG" 2>&1
}

die() { err "$*"; say "Full log: $LOG"; exit 1; }
trap 'err "unexpected failure on line $LINENO — see $LOG"' ERR

# tarball_install <label> <url> <member> [version]
# Downloads a .tar.gz, extracts one member, installs it to /usr/local/bin.
# Returns non-zero on failure INSTEAD of aborting, so one dead upstream URL
# cannot stop a delegate installing everything else.
tarball_install() {
  local label="$1" url="$2" member="$3" ver="${4:-}"
  local tmp="/tmp/${label}.tgz"
  if (( DRY )); then
    say "    ${YLW}[dry-run]${RST} curl -fsSLo $tmp $url"
    say "    ${YLW}[dry-run]${RST} tar -xzf $tmp -C /tmp $member && install -m0755 /tmp/$member /usr/local/bin/"
    ok "${label} ${ver} installed"; return 0
  fi
  {
    curl -fsSLo "$tmp" "$url" \
      && tar -xzf "$tmp" -C /tmp "$member" \
      && install -o root -g root -m 0755 "/tmp/${member}" "/usr/local/bin/${label}"
  } >>"$LOG" 2>&1 || {
    err "${label}: install failed — ${url}"
    FAILED+=("$label"); rm -f "$tmp" "/tmp/${member}"; return 1
  }
  rm -f "$tmp" "/tmp/${member}"
  ok "${label} ${ver} installed"; INSTALLED+=("$label"); return 0
}

want() {   # want <component> -> should we do this one?
  local c="$1"
  [[ -n "$SKIP" && ",$SKIP," == *",$c,"* ]] && { SKIPPED+=("$c"); return 1; }
  [[ -n "$ONLY" && ",$ONLY," != *",$c,"* ]] && return 1
  return 0
}

have() { command -v "$1" >/dev/null 2>&1; }

# Run a command as the target (non-root) user. Prefers sudo, falls back to
# runuser, and just runs it directly if we are already that user — so the
# script works from a root shell, from sudo, and inside a bare container.
as_user() {
  if [[ "$(id -un)" == "$TARGET_USER" ]]; then "$@"
  elif have sudo;    then sudo -u "$TARGET_USER" "$@"
  elif have runuser; then runuser -u "$TARGET_USER" -- "$@"
  else warn "cannot drop to $TARGET_USER (no sudo/runuser) — running as $(id -un)"; "$@"
  fi
}

# ── argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY=1 ;;
    --verify)   VERIFY_ONLY=1 ;;
    --tofu)     USE_TOFU=1 ;;
    --yes|-y)   ASSUME_YES=1 ;;
    --only)     ONLY="${2:-}"; shift ;;
    --skip)     SKIP="${2:-}"; shift ;;
    -h|--help)  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)          die "unknown option: $1  (try --help)" ;;
  esac
  shift
done

# ── preconditions ────────────────────────────────────────────────────────────
ARCH_DEB="$(dpkg --print-architecture)"          # amd64 | arm64
# Every project names its release assets differently. These mappings are checked
# against the real releases — do not "tidy" them into one variable.
case "$ARCH_DEB" in
  amd64) ARCH_ALT="x86_64";  ARCH_GL="x64";   ARCH_TRIVY="64bit" ;;
  arm64) ARCH_ALT="aarch64"; ARCH_GL="arm64"; ARCH_TRIVY="ARM64" ;;
  *) die "unsupported architecture: $ARCH_DEB (expected amd64 or arm64)" ;;
esac
#   deb:    amd64      | arm64      (docker, kubectl, helm, kubeseal, syft)
#   gitleaks: x64      | arm64
#   trivy:  64bit      | ARM64

# $USER can be unset (bare container, cron, some CI); fall back to id -un.
TARGET_USER="${SUDO_USER:-${USER:-$(id -un)}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6 || true)"
: "${TARGET_HOME:=/root}"

preflight() {
  hdr "Preflight"
  if [[ -r /etc/os-release ]]; then . /etc/os-release; else die "cannot read /etc/os-release"; fi
  if [[ "${ID:-}" != "ubuntu" ]]; then
    warn "this is '${ID:-unknown}', not Ubuntu — the script may still work but is untested"
  elif [[ "${VERSION_ID:-}" != "24.04" ]]; then
    warn "Ubuntu ${VERSION_ID:-?} detected; the course targets 24.04"
  else
    ok "Ubuntu 24.04 (${VERSION_CODENAME:-noble})"
  fi
  ok "architecture: $ARCH_DEB"

  local cores mem_gb disk_gb
  cores=$(nproc)
  mem_gb=$(awk '/MemTotal/ {printf "%.1f", $2/1048576}' /proc/meminfo)
  disk_gb=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
  (( cores >= 4 ))    && ok "CPU: ${cores} cores"      || warn "CPU: ${cores} cores — 4 recommended (day 4 runs a cluster)"
  (( ${mem_gb%.*} >= 8 )) && ok "RAM: ${mem_gb} GB"    || warn "RAM: ${mem_gb} GB — 8 GB recommended; day 6 adds Prometheus + Grafana"
  (( disk_gb >= 40 )) && ok "disk: ${disk_gb} GB free" || warn "disk: ${disk_gb} GB free — 40 GB recommended"

  if (( ! DRY && ! VERIFY_ONLY )) && [[ $EUID -ne 0 ]]; then
    die "run with sudo (or use --dry-run / --verify)"
  fi
  ok "installing for user: $TARGET_USER"
}

# ── steps ────────────────────────────────────────────────────────────────────
step_base() {
  want base || return 0
  hdr "Base packages"
  run apt-get update -qq
  run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
      ca-certificates curl wget gnupg lsb-release apt-transport-https software-properties-common \
      git jq unzip tree htop \
      iproute2 net-tools dnsutils lsof iputils-ping netcat-openbsd \
      gettext-base procps ca-certificates openssl \
      build-essential python3 python3-pip python3-venv
  # ss (iproute2) is used in Lab 08, lsof in the port-conflict troubleshooting.
  ok "base packages present (incl. ss, lsof, ping, nc, dig)"
  INSTALLED+=("base")
}

step_docker() {
  want docker || return 0
  hdr "Docker Engine + Compose plugin"
  if have docker && docker compose version >/dev/null 2>&1; then
    ok "docker $(docker --version | awk '{print $3}' | tr -d ,) already installed"
  else
    run install -m 0755 -d /etc/apt/keyrings
    if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
      if (( DRY )); then say "    ${YLW}[dry-run]${RST} fetch docker gpg key"; else
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
          | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
      fi
    fi
    local codename; codename="$( . /etc/os-release && echo "${VERSION_CODENAME:-noble}" )"
    if (( ! DRY )); then
      echo "deb [arch=${ARCH_DEB} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${codename} stable" \
        > /etc/apt/sources.list.d/docker.list
    fi
    run apt-get update -qq
    run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ok "docker installed"
    INSTALLED+=("docker")
  fi

  # the docker group is root-equivalent; say so once, clearly
  if ! id -nG "$TARGET_USER" | tr ' ' '\n' | grep -qx docker; then
    run usermod -aG docker "$TARGET_USER"
    warn "added '$TARGET_USER' to the 'docker' group — LOG OUT AND BACK IN for it to apply"
    warn "note: membership of 'docker' is equivalent to root on this host"
  else
    ok "'$TARGET_USER' already in the docker group"
  fi
  run systemctl enable --now docker || true
}

step_gh() {
  want gh || return 0
  hdr "GitHub CLI"
  if have gh; then ok "gh $(gh --version 2>/dev/null | head -1 | awk '{print $3}') already installed"; return 0; fi
  if [[ ! -f /usr/share/keyrings/githubcli-archive-keyring.gpg ]]; then
    if (( DRY )); then say "    ${YLW}[dry-run]${RST} fetch github-cli keyring"; else
      curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /usr/share/keyrings/githubcli-archive-keyring.gpg
      chmod a+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    fi
  fi
  if (( ! DRY )); then
    echo "deb [arch=${ARCH_DEB} signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list
  fi
  run apt-get update -qq
  if run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gh; then
    ok "gh installed — delegates authenticate with 'gh auth login'"
    INSTALLED+=("gh")
  else
    err "gh install failed (non-fatal)"; FAILED+=("gh")
  fi
}

step_k8s() {
  want k8s || return 0
  hdr "Kubernetes tooling (kubectl, k3d, helm)"

  if have kubectl; then ok "kubectl $(kubectl version --client -o json 2>/dev/null | jq -r .clientVersion.gitVersion 2>/dev/null || echo present) already installed"
  else
    local ver
    if (( DRY )); then ver="v1.31.x"; else ver="$(curl -fsSL https://dl.k8s.io/release/stable.txt)"; fi
    run curl -fsSLo /tmp/kubectl "https://dl.k8s.io/release/${ver}/bin/linux/${ARCH_DEB}/kubectl"
    run install -o root -g root -m 0755 /tmp/kubectl /usr/local/bin/kubectl
    run rm -f /tmp/kubectl
    ok "kubectl ${ver} installed"; INSTALLED+=("kubectl")
  fi

  if have k3d; then ok "k3d $(k3d version 2>/dev/null | head -1 | awk '{print $3}') already installed"
  else
    run curl -fsSLo /tmp/k3d.sh https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh
    if (( DRY )); then say "    ${YLW}[dry-run]${RST} run k3d installer ${K3D_VERSION}"; else
      TAG="$K3D_VERSION" bash /tmp/k3d.sh >>"$LOG" 2>&1
    fi
    run rm -f /tmp/k3d.sh
    ok "k3d ${K3D_VERSION} installed"; INSTALLED+=("k3d")
  fi

  if have helm; then ok "helm $(helm version --short 2>/dev/null) already installed"
  else
    run curl -fsSLo "/tmp/helm.tgz" "https://get.helm.sh/helm-${HELM_VERSION}-linux-${ARCH_DEB}.tar.gz"
    run tar -xzf /tmp/helm.tgz -C /tmp
    run install -o root -g root -m 0755 "/tmp/linux-${ARCH_DEB}/helm" /usr/local/bin/helm
    run rm -rf /tmp/helm.tgz "/tmp/linux-${ARCH_DEB}"
    ok "helm ${HELM_VERSION} installed"; INSTALLED+=("helm")
  fi

  if have kubeseal; then ok "kubeseal already installed"
  else
    tarball_install kubeseal \
      "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-${ARCH_DEB}.tar.gz" \
      kubeseal "${KUBESEAL_VERSION}" || true
  fi
}

step_sysctl() {
  want sysctl || return 0
  hdr "Kernel limits for k3s"
  # k3s watches a very large number of files. Ubuntu's defaults are too low and the
  # symptom appears 20 minutes later as pods stuck in ContainerCreating.
  if (( ! DRY )); then
    cat > /etc/sysctl.d/99-devops-course.conf <<'EOF'
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=512
EOF
    sysctl --system >>"$LOG" 2>&1 || true
  fi
  ok "inotify limits raised (watches=524288, instances=512)"
  INSTALLED+=("sysctl")
}

step_hosts() {
  want hosts || return 0
  hdr "Local DNS for the lab hostnames"
  # Ingress routes on the HTTP Host header, so these must resolve to loopback.
  local marker="# >>> devops-course <<<"
  if grep -qF "$marker" /etc/hosts 2>/dev/null; then
    ok "/etc/hosts entries already present"
    return 0
  fi
  if (( DRY )); then
    say "    ${YLW}[dry-run]${RST} append 7 lab hostnames to /etc/hosts"
    ok "/etc/hosts entries added"; return 0
  fi
  cp /etc/hosts "/etc/hosts.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
  cat >> /etc/hosts <<'EOF'

# >>> devops-course <<<
127.0.0.1  paytrack.localhost api.paytrack.localhost
127.0.0.1  grafana.localhost
127.0.0.1  bg.paytrack.localhost canary.paytrack.localhost weighted.paytrack.localhost
127.0.0.1  prod.paytrack.localhost staging.paytrack.localhost
# <<< devops-course >>>
EOF
  ok "/etc/hosts entries added (backup written alongside)"
  INSTALLED+=("hosts")
}

step_workspace() {
  want workspace || return 0
  hdr "Course workspace"
  local ws="${TARGET_HOME}/devops-course"
  if (( DRY )); then
    say "    ${YLW}[dry-run]${RST} mkdir -p $ws and clone the course material"
    ok "workspace ready"; return 0
  fi
  mkdir -p "$ws"
  chown -R "$TARGET_USER":"$TARGET_USER" "$ws" 2>/dev/null || true
  ok "workspace: $ws"
  if [[ -d "$ws/course-material/.git" ]]; then
    ok "course material already cloned"
  else
    if as_user git clone -q "$COURSE_REPO" "$ws/course-material" >>"$LOG" 2>&1; then
      ok "course material cloned into $ws/course-material"
      INSTALLED+=("course-material")
    else
      warn "could not clone $COURSE_REPO — clone it by hand, or ask your trainer for a zip"
    fi
  fi
}

step_helmrepos() {
  want helmrepos || return 0
  hdr "Helm repositories (day 6 pre-warm)"
  if ! have helm; then warn "helm not installed — skipping"; return 0; fi
  if (( DRY )); then say "    ${YLW}[dry-run]${RST} helm repo add prometheus-community / sealed-secrets"; return 0; fi
  as_user helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >>"$LOG" 2>&1 || true
  as_user helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets >>"$LOG" 2>&1 || true
  as_user helm repo update >>"$LOG" 2>&1 || true
  ok "helm repos added and indexed"
}

step_iac() {
  want iac || return 0
  hdr "Infrastructure as Code (Terraform/OpenTofu, Ansible)"

  if (( USE_TOFU )); then
    if have tofu; then ok "opentofu already installed"
    else
      run curl -fsSLo /tmp/tofu.sh https://get.opentofu.org/install-opentofu.sh
      run chmod +x /tmp/tofu.sh
      run /tmp/tofu.sh --install-method deb
      run rm -f /tmp/tofu.sh
      ok "opentofu installed (use 'tofu' wherever the labs say 'terraform')"; INSTALLED+=("opentofu")
    fi
  else
    if have terraform; then ok "terraform $(terraform version | head -1 | awk '{print $2}') already installed"
    else
      if [[ ! -f /usr/share/keyrings/hashicorp-archive-keyring.gpg ]]; then
        if (( DRY )); then say "    ${YLW}[dry-run]${RST} fetch hashicorp gpg key"; else
          wget -qO- https://apt.releases.hashicorp.com/gpg \
            | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        fi
      fi
      if (( ! DRY )); then
        echo "deb [arch=${ARCH_DEB} signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
          > /etc/apt/sources.list.d/hashicorp.list
      fi
      run apt-get update -qq
      run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq terraform
      ok "terraform installed (BUSL licence — use --tofu for the MPL fork)"; INSTALLED+=("terraform")
    fi
  fi

  if have ansible; then ok "ansible $(ansible --version | head -1 | awk '{print $3}' | tr -d ']') already installed"
  else
    run env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ansible ansible-lint
    ok "ansible installed"; INSTALLED+=("ansible")
  fi

  # Ansible's community.docker modules need the Python Docker SDK.
  # PEP 668 marks Ubuntu 24.04's system python as externally managed.
  if (( ! DRY )); then
    as_user python3 -c 'import docker' >/dev/null 2>&1 \
      || as_user pip3 install --user --break-system-packages -q docker >>"$LOG" 2>&1 || true
  fi
  ok "python docker SDK available to $TARGET_USER"
}

step_security() {
  want security || return 0
  hdr "Security tooling (trivy, gitleaks, syft)"

  if have trivy; then ok "trivy already installed"
  else
    tarball_install trivy \
      "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-${ARCH_TRIVY}.tar.gz" \
      trivy "${TRIVY_VERSION}" || true
  fi

  if have gitleaks; then ok "gitleaks already installed"
  else
    tarball_install gitleaks \
      "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${ARCH_GL}.tar.gz" \
      gitleaks "${GITLEAKS_VERSION}" || true
  fi

  if have syft; then ok "syft already installed"
  else
    tarball_install syft \
      "https://github.com/anchore/syft/releases/download/v${SYFT_VERSION}/syft_${SYFT_VERSION}_linux_${ARCH_DEB}.tar.gz" \
      syft "${SYFT_VERSION}" || true
  fi

  if (( ! DRY )); then
    as_user bash -lc 'command -v pre-commit' >/dev/null 2>&1 \
      || as_user pip3 install --user --break-system-packages -q pre-commit >>"$LOG" 2>&1 || true
  fi
  ok "pre-commit available to $TARGET_USER (~/.local/bin)"
}

step_git_config() {
  want gitcfg || return 0
  hdr "Git defaults"
  if (( ! DRY )); then
    as_user git config --global init.defaultBranch main || true
    as_user git config --global pull.rebase false || true
    as_user git config --global alias.lg "log --oneline --graph --decorate --all" || true
    if ! as_user git config --global user.email >/dev/null 2>&1; then
      warn "git user.name/user.email NOT set — each delegate must run:"
      warn "    git config --global user.name  \"Your Name\""
      warn "    git config --global user.email \"you@example.com\""
    else
      ok "git identity already configured"
    fi
  fi
  ok "git defaults set (main, merge-pull, 'git lg' alias)"
}

step_prepull() {
  want prepull || return 0
  hdr "Pre-pulling images (saves classroom bandwidth)"
  if ! docker info >/dev/null 2>&1; then
    warn "docker daemon not reachable yet — skipping pre-pull (re-run after logging back in)"
    return 0
  fi
  local imgs=(
    "python:3.12-slim" "postgres:16-alpine" "nginx:1.27-alpine"
    "busybox:1.36" "curlimages/curl:8.10.1" "alpine:latest"
    "$K3S_IMAGE"
  )
  for i in "${imgs[@]}"; do
    if docker image inspect "$i" >/dev/null 2>&1; then ok "$i (cached)"
    else
      if run docker pull -q "$i"; then ok "$i"; else warn "could not pull $i (continuing)"; fi
    fi
  done
}

# ── verification ─────────────────────────────────────────────────────────────
verify() {
  hdr "Verification"
  local fail=0
  # check_str <label> <already-computed version string>
  check_str() {
    local label="$1" val="${2:-}"
    if [[ -n "$val" ]]; then
      printf '  %s✔%s %-12s %s\n' "$GRN" "$RST" "$label" "${val:0:64}"
    else
      printf '  %s✘%s %-12s NOT WORKING\n' "$RED" "$RST" "$label"; fail=1; FAILED+=("$label")
    fi
  }
  check() {
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then
      printf '  %s✔%s %-12s %s\n' "$GRN" "$RST" "$label" "$("$@" 2>&1 | head -1 | cut -c1-64)"
    else
      printf '  %s✘%s %-12s NOT WORKING\n' "$RED" "$RST" "$label"; fail=1; FAILED+=("$label")
    fi
  }
  check git       git --version
  check docker    docker --version
  check compose   docker compose version
  check_str kubectl "$(kubectl version --client 2>/dev/null | head -1)"
  check k3d       k3d version
  check helm      helm version --short
  check kubeseal  kubeseal --version
  if (( USE_TOFU )); then check tofu tofu version; else check terraform terraform version; fi
  check ansible   ansible --version
  check trivy     trivy --version
  check gitleaks  gitleaks version
  check syft      syft version
  check python    python3 --version
  check gh        gh --version
  check lsof      lsof -v
  check ss        ss -V

  say ""
  if grep -qF "# >>> devops-course <<<" /etc/hosts 2>/dev/null; then
    ok "/etc/hosts lab entries present"
  else
    warn "/etc/hosts lab entries missing — Ingress hostnames will not resolve (run without --verify)"
  fi
  if docker info >/dev/null 2>&1; then
    ok "docker daemon reachable by $(whoami)"
  elif as_user docker info >/dev/null 2>&1; then
    ok "docker daemon reachable by $TARGET_USER"
  else
    warn "docker daemon not reachable as $TARGET_USER yet — LOG OUT AND BACK IN"
  fi
  return $fail
}

# ── main ─────────────────────────────────────────────────────────────────────
main() {
  : > "$LOG" 2>/dev/null || true
  say "${BLD}DevOps Professional — Ubuntu 24.04 workstation installer${RST}"
  say "log: $LOG"
  preflight

  if (( VERIFY_ONLY )); then
    verify && { hdr "ALL CHECKS PASSED"; exit 0; } || { hdr "${RED}SOME CHECKS FAILED${RST}"; exit 1; }
  fi

  step_base
  step_docker
  step_sysctl
  step_gh
  step_k8s
  step_iac
  step_security
  step_hosts
  step_git_config
  step_workspace
  step_helmrepos
  step_prepull

  if (( DRY )); then hdr "Dry run complete — nothing was changed"; exit 0; fi

  if verify; then
    hdr "${GRN}ALL CHECKS PASSED — you are ready for day 1${RST}"
  else
    hdr "${YLW}Installed, but some checks failed:${RST} ${FAILED[*]:-}"
    say "  See $LOG"
  fi

  say ""
  say "${BLD}Next steps${RST}"
  say "  1. ${YLW}Log out and back in${RST} so docker group membership applies."
  say "  2. Set your git identity:"
  say "       git config --global user.name  \"Your Name\""
  say "       git config --global user.email \"you@example.com\""
  say "  3. Re-check any time with:  sudo $0 --verify"
  say ""
  (( ${#SKIPPED[@]} )) && say "  skipped: ${SKIPPED[*]}"
  say "  Full log: $LOG"
}

main "$@"
