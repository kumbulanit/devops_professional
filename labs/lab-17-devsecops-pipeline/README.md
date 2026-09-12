# Lab 17 — Shift Security Left: Gate the Pipeline

| | |
|---|---|
| **Day** | 6 |
| **Duration** | 37 minutes |
| **Module** | 7 — DevSecOps |
| **You will produce** | A pipeline with secret, SAST, SCA, IaC and image gates, an SBOM, and Sealed Secrets |
| **Feeds into** | Lab 19 (capstone) |

---

## Objective

Add every class of security testing to the pipeline you built in Lab 15 — and, more
importantly, **plant real problems and watch the gates catch them**. A gate you have never
seen fire is a gate you do not trust.

## Prerequisites

- Lab 15 (pipeline) and Lab 06 (Trivy, Gitleaks, Syft from Lab 00)
- Stop the reconciler for now (`Ctrl+C`)

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && git switch main && git pull
k3d cluster start paytrack 2>/dev/null; kubectl config set-context --current --namespace=paytrack-dev
```

---

## Step 1 — Baseline: scan what you already have

```bash
cd ~/devops-course/paytrack-api-team
gitleaks detect --source . --no-banner --redact -v 2>&1 | tail -20
```
**What this does:** scans **the working tree and the entire git history** for credentials
using ~150 rules plus entropy analysis. `--redact` prints findings without echoing the secret
into your terminal (which would then be in your shell history — the tool being careful with
you).

```bash
cd app && source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install -q -r requirements-dev.txt)
bandit -r src -ll 2>&1 | tail -25
```
**What this does:** **SAST** — Bandit parses the Python AST looking for insecure patterns
(`eval`, `subprocess` with `shell=True`, hard-coded passwords, weak hashes, `assert` used as
a control). `-ll` reports MEDIUM and above.

```bash
pip-audit -r requirements.txt 2>&1 | tail -20
```
**What this does:** **SCA** — checks your dependencies against the Python Advisory Database.
**This is the category that matters most**: 70–90 % of the code you ship is somebody else's.

```bash
deactivate; cd ..
trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL . 2>&1 | tail -30
```
**What this does:** Trivy in filesystem mode — dependencies, secrets and **misconfiguration**
(Dockerfile and Kubernetes manifests) in one pass.

```bash
trivy config k8s/ terraform/ app/Dockerfile 2>&1 | tail -30
```
**What this does:** **IaC scanning.** Expect findings even on your hardened manifests — a
missing `automountServiceAccountToken: false`, an unset `seccompProfile`. **Read them; they
are mostly right.**

---

## Step 2 — Plant real problems

A gate you have not seen fire is a gate you do not trust.

```bash
git switch -c security/demonstrate-gates

cat > app/src/danger.py <<'EOF'
"""DELIBERATELY INSECURE — planted to prove the pipeline gates work.
This file is deleted at the end of the lab."""
import hashlib
import subprocess

# 1. Hard-coded credentials  → gitleaks + bandit
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_PASSWORD = "SuperSecret123!"
GITHUB_TOKEN = "ghp_16CharsOfNonsenseFollowedByMoreNonsense1234"


def run_user_command(user_input: str):
    # 2. Command injection  → bandit B602
    return subprocess.check_output(user_input, shell=True)


def hash_password(pw: str) -> str:
    # 3. Weak hash  → bandit B324
    return hashlib.md5(pw.encode()).hexdigest()


def evaluate(expr: str):
    # 4. Arbitrary code execution  → bandit B307
    return eval(expr)
EOF

python3 - <<'PY'
import pathlib
p = pathlib.Path("app/requirements.txt")
s = p.read_text()
# 5. A dependency with known CVEs  → pip-audit + trivy
p.write_text(s + "requests==2.19.1\n")
print("pinned a vulnerable requests version")
PY
```

**Now watch every gate fire:**

```bash
gitleaks detect --source . --no-banner --redact -v 2>&1 | tail -25; echo "gitleaks exit: $?"
```
**Expect:** AWS keys and the GitHub token found, with file and line. **Exit code 1.**

```bash
cd app && source .venv/bin/activate
bandit -r src -ll 2>&1 | tail -35
```
**Expect:** B602 (subprocess with shell), B324 (MD5), B307 (eval), B105 (hard-coded password),
each with a severity, a confidence and a CWE reference.

```bash
pip install -q -r requirements.txt 2>/dev/null
pip-audit -r requirements.txt 2>&1 | tail -20
```
**Expect:** several CVEs against `requests 2.19.1`, each naming the fixed version.

```bash
deactivate; cd ..
trivy fs --scanners secret --severity HIGH,CRITICAL app/src/ 2>&1 | tail -20
```
**Expect:** Trivy independently finds the same secrets. **Overlapping tools are a feature** —
different rule sets catch different things.

> 🔑 **Every one of these is a real, common production mistake.** The AWS key format is the
> exact pattern that gets repositories scraped within seconds of a public push.

---

## Step 3 — Turn the scans into gates

```bash
cat > .github/workflows/security.yml <<'EOF'
name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'        # Mondays 06:00 — CVEs are published after you merged

permissions:
  contents: read
  security-events: write        # upload SARIF to the Security tab

jobs:
  # ═══════════════════════════════════════════════════════════════════
  secrets:
    name: Secret scanning
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }        # FULL history - a secret may be in an old commit
      - name: gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        # NO continue-on-error. A leaked credential ALWAYS fails the build.

  # ═══════════════════════════════════════════════════════════════════
  sast:
    name: SAST (bandit)
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install bandit[sarif]
      - name: Run bandit
        run: bandit -r app/src -ll -f sarif -o bandit.sarif || true
      - name: Upload results to the Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with: { sarif_file: bandit.sarif }
      - name: Fail on HIGH severity
        run: bandit -r app/src -lll        # -lll = HIGH only → blocking

  # ═══════════════════════════════════════════════════════════════════
  dependencies:
    name: SCA (pip-audit)
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pip-audit
      - name: Audit dependencies
        run: pip-audit -r app/requirements.txt --desc
        # Blocking: a known-vulnerable dependency with a fix available is not shippable.

  # ═══════════════════════════════════════════════════════════════════
  iac:
    name: IaC misconfiguration
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - name: Trivy config scan
        uses: aquasecurity/trivy-action@0.24.0
        with:
          scan-type: config
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: '1'
          trivy-config: .trivy.yaml

  # ═══════════════════════════════════════════════════════════════════
  image:
    name: Image scan + SBOM
    runs-on: ubuntu-24.04
    permissions: { contents: read, packages: read, security-events: write }
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t paytrack-api:scan ./app

      - name: Trivy image scan (GATE)
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: paytrack-api:scan
          severity: HIGH,CRITICAL
          ignore-unfixed: true       # do not block on CVEs with no available fix
          exit-code: '1'             # ← THE GATE
          format: table

      - name: Generate SBOM (CycloneDX)
        uses: anchore/sbom-action@v0
        with:
          image: paytrack-api:scan
          format: cyclonedx-json
          output-file: sbom.cyclonedx.json

      - name: Publish the SBOM as a build artefact
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.cyclonedx.json
          retention-days: 90
EOF
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/security.yml'));print('YAML valid')"
```

```bash
cat > .trivy.yaml <<'EOF'
# Trivy configuration, versioned with the code it scans.
severity:
  - HIGH
  - CRITICAL
misconfiguration:
  # Findings we have consciously accepted for THIS lab environment.
  # Every entry needs an owner and an expiry date, reviewed at each release.
  exclude-rules: []
scan:
  skip-dirs:
    - .venv
    - .git
    - node_modules
EOF

cat > .trivyignore <<'EOF'
# Accepted risks. FORMAT: CVE-ID  # owner · reason · EXPIRES yyyy-mm-dd
#
# Rules for this file:
#   1. Every line has an owner and an expiry date.
#   2. Expired entries are reviewed at release, not silently renewed.
#   3. "It is noisy" is not a reason. "No fix exists and the code path is
#      unreachable because X" is a reason.
#
# Example:
# CVE-2024-99999   # platform-team · no upstream fix; path unreachable · EXPIRES 2026-12-31
EOF
```
**The gating policy, and why it is tiered:**

| Finding | Action | Rationale |
|---|---|---|
| **Secret in code or history** | **Always fail** | Non-negotiable. Rotate immediately |
| **HIGH-severity SAST** | Fail | High confidence, exploitable |
| MEDIUM SAST | Report to the Security tab | Triage in planned work |
| **Vulnerable dependency with a fix** | Fail | Someone else already fixed it; take the fix |
| Vulnerable dependency, **no fix** | Report (`ignore-unfixed`) | Blocking on the unfixable teaches people to bypass the gate |
| **HIGH/CRITICAL in the image, fixable** | Fail | Usually one base-image rebuild away |
| **HIGH/CRITICAL IaC misconfig** | Fail | Privileged containers, public buckets, open groups |

> 🔴 **The most important design decision in this lab: fail on *actionable* findings only.**
> A pipeline that is always red gets bypassed, and a bypassed gate is worse than no gate —
> because you believe you are protected.

---

## Step 4 — Watch the gates block the merge

```bash
git add app/src/danger.py app/requirements.txt .github/workflows/security.yml .trivy.yaml .trivyignore
git commit -m "test: add deliberately insecure code to prove the security gates fire"
git push -u origin security/demonstrate-gates
```
Open the PR.

✅ **Checkpoint — watch every job go red:**

| Job | Finds |
|---|---|
| `Secret scanning` | ❌ AWS keys, GitHub token |
| `SAST (bandit)` | ❌ shell injection, MD5, eval |
| `SCA (pip-audit)` | ❌ CVEs in `requests 2.19.1` |
| `IaC misconfiguration` | ❌ / ⚠️ manifest findings |
| `Image scan + SBOM` | ❌ vulnerable packages in the image |

**The merge button is disabled.** Add these to branch protection (Settings → Branches →
Require status checks) so they gate permanently.

Check the **Security → Code scanning alerts** tab: Bandit's SARIF findings appear there,
annotated on the exact lines of the diff.

---

## Step 5 — Remediate

```bash
git rm app/src/danger.py
python3 - <<'PY'
import pathlib
p = pathlib.Path("app/requirements.txt")
p.write_text(p.read_text().replace("requests==2.19.1\n", ""))
print("removed the vulnerable dependency")
PY
gitleaks detect --source . --no-banner --redact 2>&1 | tail -5; echo "exit=$?"
git add -A
git commit -m "fix(security): remove insecure demo code and vulnerable dependency

Gates verified working: gitleaks, bandit, pip-audit, trivy config, trivy image.
Every finding was a real, common production mistake."
git push
```
**Every check goes green and the merge button returns.** Merge the PR.

> 🔴 **In reality, removing the file is NOT enough.** Those credentials are in the git
> history, in every clone, in every fork, and in the CI cache. The correct order is:
>
> 1. **Rotate the credential first.** Assume it is compromised the moment it is pushed.
> 2. Then, optionally, scrub history (`git filter-repo`, BFG) — which rewrites history and
>    still does not reach forks or existing clones.
> 3. Add pre-commit detection so it cannot recur.
> 4. Check the credential's access logs for use.
>
> **Rotating is mandatory; scrubbing is cosmetic.** Teams routinely get this backwards.

---

## Step 6 — Catch secrets before they are ever committed

```bash
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict        # blocks committing <<<<<<< markers
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
        args: ['--allow-multiple-documents']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ['-ll', '-r', 'app/src']
EOF
pip3 install --user --break-system-packages pre-commit 2>/dev/null
~/.local/bin/pre-commit install 2>/dev/null || pre-commit install
```
**What this does:** installs a git hook that runs these checks on **staged files before the
commit is created**. The feedback loop shrinks from three minutes (CI) to three seconds.

```bash
echo 'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"' > /tmp/leak.py
cp /tmp/leak.py app/src/leak.py && git add app/src/leak.py
git commit -m "test: this commit should be blocked" || echo "✅ pre-commit BLOCKED the commit"
git restore --staged app/src/leak.py && rm app/src/leak.py
```
**What this does:** proves the hook. **The commit never happens**, so the secret never enters
history — the only truly clean outcome.

> ⚠️ **Pre-commit hooks are local and bypassable** (`git commit --no-verify`). They are a
> **convenience for the developer**, not a control. **The CI gate is the control**, because it
> cannot be skipped.

---

## Step 7 — Sealed Secrets: secrets safely in git

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets 2>/dev/null
helm repo update >/dev/null
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system --set-string fullnameOverride=sealed-secrets-controller
kubectl rollout status deployment/sealed-secrets-controller -n kube-system --timeout=120s
```
**What this does:** installs the controller, which generates a keypair inside the cluster.
The **public** key encrypts; only the **private** key in this cluster can decrypt.

```bash
KUBESEAL_VERSION=0.27.1
curl -sSL "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz" \
  | tar -xz -C /tmp kubeseal
sudo install -m 0755 /tmp/kubeseal /usr/local/bin/kubeseal
kubeseal --version
```

```bash
kubectl create secret generic paytrack-db-secret \
  --namespace=paytrack-dev \
  --from-literal=POSTGRES_USER=paytrack \
  --from-literal=POSTGRES_PASSWORD='Pr0d-Str0ng-Passw0rd!' \
  --dry-run=client -o yaml > /tmp/plain-secret.yaml

kubeseal --controller-name=sealed-secrets-controller \
         --controller-namespace=kube-system \
         --format yaml < /tmp/plain-secret.yaml > k8s/base/sealed-secret.yaml

rm /tmp/plain-secret.yaml          # the plaintext never persists
cat k8s/base/sealed-secret.yaml
```
**What this does:** generates the Secret **without creating it**, encrypts it with the
cluster's public key, writes the `SealedSecret`, and deletes the plaintext.

**Look at the output**: `encryptedData` contains long base64 ciphertext. **This file is safe
to commit to a public repository.** Only this cluster's controller can decrypt it.

```bash
kubectl apply -f k8s/base/sealed-secret.yaml
sleep 5
kubectl get sealedsecret,secret paytrack-db-secret -n paytrack-dev
kubectl get secret paytrack-db-secret -n paytrack-dev -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo
```
**What this does:** the controller sees the `SealedSecret`, decrypts it, and creates a normal
`Secret` — which your Deployment consumes with no changes at all.

```
  DEVELOPER LAPTOP              GIT (public!)              CLUSTER
  ┌──────────────┐   kubeseal   ┌──────────────┐  apply   ┌────────────────────┐
  │ plain Secret │─────────────►│ SealedSecret │─────────►│ controller decrypts│
  │ (never       │   public key │ ciphertext   │          │ with the PRIVATE   │
  │  committed)  │              │ SAFE to      │          │ key → real Secret  │
  └──────────────┘              │ commit       │          └────────────────────┘
                                └──────────────┘
```

> **Back up the controller's private key.** Without it, a rebuilt cluster cannot decrypt any
> committed SealedSecret:
> ```bash
> kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key \
>   -o yaml > ~/devops-course/backups/sealed-secrets-key.yaml
> ```
> **That backup file is the master key. Treat it accordingly.**

---

## Step 8 — Harden the workload

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("k8s/base/deployment.yaml")
s = p.read_text()
if "automountServiceAccountToken" not in s:
    s = s.replace("    spec:\n      # Security:",
                  "    spec:\n      automountServiceAccountToken: false   # this pod needs no API access\n      # Security:")
p.write_text(s)
print("added automountServiceAccountToken: false")
PY

cat > k8s/base/policy-check.sh <<'EOF'
#!/usr/bin/env bash
# Minimal admission-policy check. In production this is Kyverno or OPA Gatekeeper
# enforcing the same rules at the API server, so a bad manifest cannot be applied.
set -uo pipefail
NS="${1:-paytrack-dev}"
fail=0
chk() { if [ "$2" = "true" ] || [ -n "${2//null/}" ] && [ "$2" != "null" ]; then
          printf '  ✔ %s\n' "$1"; else printf '  ✗ %s\n' "$1"; fail=1; fi }

echo "── Pod security policy check: namespace $NS ──"
for pod in $(kubectl get pods -n "$NS" -o jsonpath='{.items[*].metadata.name}'); do
  echo "$pod"
  chk "runAsNonRoot"          "$(kubectl get pod "$pod" -n "$NS" -o jsonpath='{.spec.securityContext.runAsNonRoot}')"
  chk "readOnlyRootFilesystem" "$(kubectl get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].securityContext.readOnlyRootFilesystem}')"
  chk "no privilege escalation" "$(kubectl get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].securityContext.allowPrivilegeEscalation}' | sed 's/false/true/')"
  chk "memory limit set"      "$(kubectl get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].resources.limits.memory}')"
  IMG=$(kubectl get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].image}')
  case "$IMG" in *:latest|*[!:]) printf '  ✗ image is not pinned: %s\n' "$IMG"; fail=1 ;;
                 *) printf '  ✔ image pinned: %s\n' "$IMG" ;; esac
done
exit "$fail"
EOF
chmod +x k8s/base/policy-check.sh
kubectl apply -f k8s/base/deployment.yaml
kubectl rollout status deployment/paytrack-api -n paytrack-dev --timeout=90s
./k8s/base/policy-check.sh paytrack-dev
```
**What this does:** verifies the security posture of every **running** pod, not just the
manifest. In production, **Kyverno** or **OPA Gatekeeper** enforce these rules at admission —
so a non-compliant pod is *rejected* rather than reported. Rules worth enforcing: no
`:latest`, no privileged, `runAsNonRoot` required, resource limits required, images only from
approved registries, and signature verification.

---

## Step 9 — Wire the gates into CD, and commit

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path(".github/workflows/cd.yml")
s = p.read_text()
s = s.replace("          exit-code: '0'              # Lab 17 changes this to '1' — a real gate",
              "          exit-code: '1'              # GATE: a fixable HIGH/CRITICAL blocks the deploy")
p.write_text(s)
print("CD image scan is now a blocking gate")
PY

git add -A
git commit -m "feat(security): shift-left gates, SBOM and Sealed Secrets

- security.yml: gitleaks (full history), bandit SAST + SARIF, pip-audit SCA,
  trivy config for IaC, trivy image + CycloneDX SBOM; weekly schedule so newly
  published CVEs are found after merge
- cd.yml image scan promoted from advisory to a blocking gate
- .trivyignore requires an owner and an expiry date per accepted risk
- pre-commit hooks for fast local feedback (a convenience, not the control)
- SealedSecret replaces the plaintext Secret; safe to commit
- automountServiceAccountToken: false; policy-check.sh verifies running pods"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
gitleaks detect --source . --no-banner 2>&1 | tail -3
trivy fs --scanners vuln --severity CRITICAL --quiet app/ | tail -3
kubectl get sealedsecret -n paytrack-dev
./k8s/base/policy-check.sh paytrack-dev && echo "✅ all pods compliant"
```

---

## 🧩 Stretch (homework)

1. **Sign your images.** Install `cosign`, sign with keyless OIDC in CI, and verify at
   admission. That is SLSA provenance in practice.
2. **Kyverno.** Install it and write a `ClusterPolicy` that rejects any pod with `:latest` or
   without resource limits. Then try to deploy one and watch it be **refused**, not reported.
3. **DAST.** Run OWASP ZAP baseline against the running app:
   `docker run --rm -t --network host ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://paytrack.localhost:8080`
4. **Re-scan the SBOM.** Download last week's SBOM artefact and run `grype sbom:./sbom.json`.
   You will find CVEs that did not exist when it was built — that is why SBOMs are stored.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| gitleaks finds nothing after you removed the file | Only scanned the working tree | Use `fetch-depth: 0` in CI; locally `gitleaks detect` covers history |
| bandit fails on test files | Test asserts flagged as B101 | `--exclude tests` or `# nosec` **with a reason** |
| Trivy config floods with LOW findings | No severity filter | `--severity HIGH,CRITICAL` |
| `kubeseal` cannot find the controller | Name/namespace mismatch | Pass `--controller-name` and `--controller-namespace` |
| SealedSecret does not produce a Secret | Wrong namespace, or sealed for a different cluster | Sealed secrets are **cluster- and namespace-scoped**; re-seal |
| Pipeline always red | Gating on unfixable CVEs | Set `ignore-unfixed: true`; use `.trivyignore` with expiries |

---

## 🎯 Outcome

A pipeline with secret, SAST, SCA, IaC and image gates that you have **watched block a
merge**; an SBOM published per build; pre-commit hooks for fast local feedback; secrets
encrypted safely into git with Sealed Secrets; and a running workload verified against a
security policy.

**Next:** [Lab 18 — Monitoring and Observability](../lab-18-observability/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Step 2 (planting the flaws) is the lab.** Do not let anyone skip to the fixed state.
  Watching five gates go red on their own PR is what makes this stick.
- **The three things that go wrong:**
  1. `pre-commit` is not on `PATH` after a `--user` install. Use `~/.local/bin/pre-commit`.
  2. `kubeseal` version skew with the controller. Both are pinned above — keep them matched.
  3. Delegates "fix" a red pipeline by adding `continue-on-error`. Catch this and make it a
     discussion: it is exactly how real teams end up with theatre instead of controls.
- **Spend two minutes on Step 5's rotation point.** The instinct is always to scrub history
  first. Correct it firmly: rotate first, always.
- **Debrief question:** "If an AWS key were committed to your main repository right now, how
  long until someone noticed — and what is your first action?"
</details>
