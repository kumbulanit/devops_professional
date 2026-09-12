# Lab 19 — Capstone: Build It All, Break It, Recover It

| | |
|---|---|
| **Day** | 6 |
| **Duration** | 25 minutes + 15-minute debrief |
| **Module** | 9 — Enterprise DevOps |
| **You will produce** | A verified end-to-end platform, a game-day incident report, and your own 30-60-90 day plan |

---

## Objective

Three parts:

1. **Verify** the complete chain you have built over six days, end to end.
2. **Game day** — break it in ways you have not yet seen, and recover it against the clock.
3. **Plan** — write the 30-60-90 day improvement plan you will take back to work.

## Prerequisites

All labs 00–18. Cluster and monitoring stack running.

```bash
cd ~/devops-course/paytrack-api-team && git switch main && git pull
k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev
kubectl get pods -n paytrack-dev && kubectl get pods -n monitoring | head -5
```

---

## Part 1 — Verify the whole chain (10 min)

```bash
cat > scripts/verify-platform.sh <<'EOF'
#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  End-to-end verification of everything built in this course.
#  Every check maps to the lab that produced it.
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail
pass=0; fail=0
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
head() { printf '\n\033[1m%s\033[0m\n' "$1"; }

head "1 · SOURCE CONTROL  (Labs 02-03)"
git rev-parse --git-dir >/dev/null 2>&1 && ok "git repository" || bad "git repository"
git remote get-url origin >/dev/null 2>&1 && ok "remote configured: $(git remote get-url origin)" || bad "no remote"
[ -f .gitignore ] && grep -q '.venv' .gitignore && ok ".gitignore excludes build artefacts" || bad ".gitignore"
[ -f .github/CODEOWNERS ] && ok "CODEOWNERS routes reviews" || bad "CODEOWNERS missing"

head "2 · CONTINUOUS INTEGRATION  (Labs 04-05)"
[ -f .github/workflows/ci.yml ] && ok "CI workflow" || bad "CI workflow missing"
[ -f Jenkinsfile ] && ok "Jenkinsfile (comparison)" || bad "Jenkinsfile missing"
[ -f .github/dependabot.yml ] && ok "Dependabot enabled" || bad "Dependabot missing"

head "3 · CONTAINERS  (Labs 06-08)"
[ -f app/Dockerfile ] && grep -q 'AS builder' app/Dockerfile && ok "multi-stage Dockerfile" || bad "multi-stage build"
grep -q '^USER 10001' app/Dockerfile && ok "runs as non-root (uid 10001)" || bad "non-root user"
[ -f .dockerignore ] && ok ".dockerignore present" || bad ".dockerignore missing"
[ -f compose.yaml ] && grep -q 'service_healthy' compose.yaml && ok "Compose waits on healthchecks" || bad "Compose depends_on condition"

head "4 · KUBERNETES  (Labs 09-12)"
kubectl get ns paytrack-dev >/dev/null 2>&1 && ok "namespace paytrack-dev" || bad "namespace"
R=$(kubectl get deploy paytrack-api -n paytrack-dev -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
[ "${R:-0}" -ge 1 ] && ok "deployment ready ($R replicas)" || bad "deployment not ready"
kubectl get svc paytrack-api -n paytrack-dev >/dev/null 2>&1 && ok "service" || bad "service"
kubectl get ingress -n paytrack-dev 2>/dev/null | grep -q paytrack && ok "ingress" || bad "ingress"
kubectl get hpa -n paytrack-dev 2>/dev/null | grep -q paytrack && ok "HPA" || bad "HPA"
kubectl get pdb -n paytrack-dev 2>/dev/null | grep -q paytrack && ok "PodDisruptionBudget" || bad "PDB"
kubectl get pvc -n paytrack-dev 2>/dev/null | grep -q Bound && ok "PVC bound" || bad "no bound PVC"
kubectl get deploy paytrack-api -n paytrack-dev -o jsonpath='{.spec.strategy.rollingUpdate.maxUnavailable}' 2>/dev/null \
  | grep -q '^0$' && ok "maxUnavailable=0 (zero-downtime rollout)" || bad "maxUnavailable not 0"

head "5 · INFRASTRUCTURE AS CODE  (Labs 13-14)"
[ -d terraform ] && ok "terraform/ present" || bad "terraform/ missing"
[ -f terraform/.terraform.lock.hcl ] && ok "provider lock file committed" || bad "lock file missing"
git check-ignore -q terraform/terraform.tfstate 2>/dev/null && ok "tfstate is git-ignored" || bad "tfstate NOT ignored"
[ -d ansible/roles ] && ok "ansible roles" || bad "ansible roles missing"

head "6 · CONTINUOUS DELIVERY  (Labs 15-16)"
[ -f .github/workflows/cd.yml ] && ok "CD workflow" || bad "CD workflow missing"
grep -q 'paths-ignore' .github/workflows/cd.yml 2>/dev/null && ok "promote loop guarded (paths-ignore)" || bad "loop guard missing"
[ -f k8s/overlays/dev/image.yaml ] && ok "desired-state overlay" || bad "overlay missing"
[ -x scripts/gitops-sync.sh ] && ok "GitOps reconciler" || bad "reconciler missing"
IMG=$(kubectl get deploy paytrack-api -n paytrack-dev -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)
case "$IMG" in *:latest) bad "image is :latest — not pinned" ;; "") bad "no image" ;;
               *) ok "image pinned: $IMG" ;; esac

head "7 · DEVSECOPS  (Lab 17)"
[ -f .github/workflows/security.yml ] && ok "security workflow" || bad "security workflow missing"
[ -f .pre-commit-config.yaml ] && ok "pre-commit hooks" || bad "pre-commit missing"
[ -f .trivyignore ] && ok ".trivyignore (owned, expiring exceptions)" || bad ".trivyignore missing"
kubectl get sealedsecret -n paytrack-dev >/dev/null 2>&1 && ok "SealedSecret in use" || bad "no SealedSecret"
kubectl get deploy paytrack-api -n paytrack-dev -o jsonpath='{.spec.template.spec.securityContext.runAsNonRoot}' 2>/dev/null \
  | grep -q true && ok "pods run as non-root" || bad "runAsNonRoot not set"
command -v gitleaks >/dev/null && gitleaks detect --source . --no-banner >/dev/null 2>&1 \
  && ok "no secrets detected in repo or history" || bad "gitleaks found something (or is missing)"

head "8 · OBSERVABILITY  (Lab 18)"
kubectl get pods -n monitoring 2>/dev/null | grep -q prometheus && ok "Prometheus running" || bad "Prometheus missing"
kubectl get pods -n monitoring 2>/dev/null | grep -q grafana && ok "Grafana running" || bad "Grafana missing"
kubectl get servicemonitor -n paytrack-dev 2>/dev/null | grep -q paytrack && ok "ServiceMonitor" || bad "ServiceMonitor missing"
kubectl get prometheusrule -n paytrack-dev 2>/dev/null | grep -q paytrack && ok "SLO alert rules" || bad "alert rules missing"
[ -f k8s/monitoring/dashboards/paytrack-red.json ] && ok "dashboard as code" || bad "dashboard JSON missing"
ls docs/runbooks/*.md >/dev/null 2>&1 && ok "runbooks written" || bad "no runbooks"

head "9 · LIVE SERVICE"
curl -sf --max-time 5 http://paytrack.localhost:8080/health >/dev/null 2>&1 && ok "/health via ingress" || bad "/health unreachable"
curl -sf --max-time 5 http://paytrack.localhost:8080/ready  >/dev/null 2>&1 && ok "/ready via ingress"  || bad "/ready failing"
curl -sf --max-time 5 http://paytrack.localhost:8080/metrics >/dev/null 2>&1 && ok "/metrics exposed"   || bad "/metrics unreachable"

printf '\n═══════════════════════════════════════════\n'
printf '  PASSED: %d    FAILED: %d\n' "$pass" "$fail"
printf '═══════════════════════════════════════════\n'
[ "$fail" -eq 0 ] && echo "🎉 Complete platform verified." || echo "Review the ✗ items above."
exit $(( fail > 0 ))
EOF
chmod +x scripts/verify-platform.sh
./scripts/verify-platform.sh
```
**What this does:** checks all nine layers you built. Each check names the lab it came from, so
a failure tells you exactly where to look.

**Then prove the full loop still works, from an edit:**

```bash
git switch -c capstone/final-verification
python3 - <<'PY'
import pathlib, re
p = pathlib.Path("app/src/app.py")
s = p.read_text()

m = re.search(r'(def info\(\):\n        return jsonify\(\n)(.*?)(        \)\n)', s, re.S)
assert m, "could not find the info() endpoint in app/src/app.py"

if "capstone" not in m.group(2):
    s = s[:m.end(2)] + '            capstone="verified",\n' + s[m.end(2):]
    p.write_text(s)
    print("added capstone marker to /api/v1/info")
else:
    print("already present - nothing to do")
PY
cd app && source .venv/bin/activate 2>/dev/null && pytest -q && deactivate; cd ..
git add app/src/app.py && git commit -m "feat(api): capstone verification marker"
git push -u origin capstone/final-verification
```

Merge the PR, then watch the whole chain: CI → security gates → build → scan → SBOM → push →
promote → reconcile → rollout → Prometheus scrapes the new pods.

```bash
sleep 180
curl -s http://paytrack.localhost:8080/api/v1/info | jq
```
**`"capstone": "verified"` in the response means every layer worked**, from your editor to a
monitored production workload, with no `kubectl` typed by a human.

---

## Part 2 — Game day (10 min)

> **Rules.** Work in pairs. One person injects, the other is on call and **must not watch the
> injection**. Use only your dashboards, alerts and runbooks. **Record the clock times.**

```bash
cat > scripts/gameday.sh <<'EOF'
#!/usr/bin/env bash
# Injects one of five failures. The on-call engineer must diagnose it from telemetry.
#   usage: ./scripts/gameday.sh <1-5>   |   ./scripts/gameday.sh reset
set -uo pipefail
NS=paytrack-dev
case "${1:-}" in
  1) echo "[injected]"; kubectl set image deployment/paytrack-api paytrack-api=ghcr.io/nope/nope:v1 -n $NS >/dev/null ;;
  2) echo "[injected]"; kubectl set resources deployment/paytrack-api --limits=memory=20Mi -n $NS >/dev/null ;;
  3) echo "[injected]"; kubectl patch deployment paytrack-api -n $NS --type=json \
       -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/does-not-exist"}]' >/dev/null ;;
  4) echo "[injected]"; kubectl patch service paytrack-api -n $NS --type=json \
       -p='[{"op":"replace","path":"/spec/selector","value":{"app.kubernetes.io/name":"wrong-label"}}]' >/dev/null ;;
  5) echo "[injected]"; kubectl scale statefulset/postgres --replicas=0 -n $NS >/dev/null 2>&1 || \
       kubectl set env deployment/paytrack-api DB_HOST=unreachable-host READINESS_REQUIRES_DB=true -n $NS >/dev/null ;;
  reset)
     kubectl rollout undo deployment/paytrack-api -n $NS >/dev/null 2>&1
     kubectl apply -f k8s/base/ >/dev/null 2>&1
     kubectl scale statefulset/postgres --replicas=1 -n $NS >/dev/null 2>&1
     kubectl rollout status deployment/paytrack-api -n $NS --timeout=120s
     echo "[reset complete]" ;;
  *) echo "usage: $0 <1|2|3|4|5|reset>"; exit 1 ;;
esac
EOF
chmod +x scripts/gameday.sh
```

| # | What breaks | The signal to look for | Difficulty |
|---|---|---|---|
| 1 | Image does not exist | `ImagePullBackOff` in pod events | ★ |
| 2 | Memory limit far too low | `OOMKilled`, exit code 137 | ★★ |
| 3 | Readiness probe points at a bad path | Pods `Running` but `0/1 READY`; **empty EndpointSlice** | ★★★ |
| 4 | Service selector no longer matches any pod | Pods healthy, **service returns nothing** | ★★★★ |
| 5 | Database unreachable | `/ready` 503, `/health` still 200 | ★★★ |

**The on-call procedure — follow it in order:**

```bash
# 1 DETECT — what do the symptoms say?
curl -s -o /dev/null -w 'health=%{http_code}\n' http://paytrack.localhost:8080/health
curl -s -o /dev/null -w 'ready =%{http_code}\n' http://paytrack.localhost:8080/ready

# 2 TRIAGE — how bad, and for how many?
kubectl get pods -n paytrack-dev
kubectl get endpointslices -n paytrack-dev -l kubernetes.io/service-name=paytrack-api \
  -o jsonpath='{.items[*].endpoints[*].addresses[*]}{"\n"}'

# 3 DIAGNOSE — describe first, ALWAYS read Events
kubectl describe pod -l app.kubernetes.io/name=paytrack-api -n paytrack-dev | tail -25
kubectl get events -n paytrack-dev --sort-by=.lastTimestamp | tail -10
kubectl logs -l app.kubernetes.io/name=paytrack-api -n paytrack-dev --tail=30 --previous 2>/dev/null

# 4 MITIGATE — restore service BEFORE you fully understand it
kubectl rollout undo deployment/paytrack-api -n paytrack-dev

# 5 VERIFY with data
kubectl rollout status deployment/paytrack-api -n paytrack-dev --timeout=90s
curl -s http://paytrack.localhost:8080/ready | jq
```

> 💡 **Failure 4 is the instructive one.** Every pod is healthy, logs are clean, `describe`
> shows nothing wrong — and the service returns nothing. The **empty EndpointSlice** is the
> only signal, and `rollout undo` will not fix it because the Deployment was never touched.
> This is why "check the endpoints" belongs in every Kubernetes runbook.

```bash
cat > docs/postmortems/gameday-$(date +%Y-%m-%d).md <<'EOF'
# Game Day Report

| | |
|---|---|
| Failure injected | # |
| Time to **detect** (impact → noticed) | |
| Time to **diagnose** (noticed → cause known) | |
| Time to **mitigate** (cause known → service restored) | |
| **Total MTTR** | |

## What told you something was wrong?
<An alert, a dashboard, or manual poking? If manual — that is the finding.>

## Which command identified the cause?
<And how many did you try before it?>

## What would have made this faster?
1.
2.

## Was your runbook usable?
<What was missing? Update `docs/runbooks/` NOW, while it is fresh.>
EOF
./scripts/gameday.sh reset
```

---

## Part 3 — Your 30-60-90 day plan (debrief, 15 min)

```bash
cat > docs/improvement-plan.md <<'EOF'
# DevOps Improvement Plan — <your name / team>

## 1 · Where we are (from Lab 01, revisited)

| Measure | Day 1 estimate | Better estimate now | DORA band |
|---|---|---|---|
| Deployment frequency | | | |
| Lead time for change | | | |
| Change failure rate | | | |
| Failed-deployment recovery time | | | |
| Flow efficiency (Lab 01) | | | |

**Our constraint is:** ___________________
**Evidence:** ___________________

## 2 · CALMS, re-scored after six days

| Dimension | Day 1 | Today | Biggest single gap |
|---|---|---|---|
| Culture | | | |
| Automation | | | |
| Lean | | | |
| Measurement | | | |
| Sharing | | | |

**Lowest score = where we invest.**

---

## 3 · FIRST 30 DAYS — measure, and win something small

*Criteria: needs no budget, no reorganisation, and no permission outside the team.*

| # | Action | Why (link to the constraint) | Owner | Done when |
|---|--------|------------------------------|-------|-----------|
| 1 | Start measuring the four DORA metrics | You cannot improve what you do not measure | | A dashboard exists |
| 2 | | | | |
| 3 | | | | |

**Candidates:** put CI on one repository · turn on branch protection · add secret scanning ·
write one runbook · one blameless post-mortem · pin `:latest` images · add resource limits.

## 4 · DAYS 30-60 — automate the constraint

| # | Action | Expected effect on lead time | Owner | Done when |
|---|--------|------------------------------|-------|-----------|
| 1 | | | | |
| 2 | | | | |

**Candidates:** containerise one service · full CI/CD for one service · IaC for one
environment · Prometheus + one SLO · replace one manual approval with an automated gate.

## 5 · DAYS 60-90 — make it the default

| # | Action | Owner | Done when |
|---|--------|-------|-----------|
| 1 | | | |
| 2 | | | |

**Candidates:** a paved-road pipeline template other teams can copy · GitOps for one
environment · security gates on all repos · an error-budget policy agreed **in writing** with
the business · a second team onboarded to the pattern.

---

## 6 · Anti-patterns we have, and the first step on each

| Anti-pattern (Module 9 §9.7) | Present? | First step |
|---|---|---|
| DevOps team as a silo | | |
| DevOps = tools | | |
| Automating a broken process | | |
| No tested rollback | | |
| Long-lived branches | | |
| Change freezes | | |
| Alert fatigue | | |
| Hero culture | | |
| Snowflake environments | | |
| Security only at the end | | |

## 7 · What I need from my organisation

| Need | From whom | The argument I will make |
|---|---|---|
| | | |

## 8 · How I will know this worked

**In 90 days, this number will have moved from ___ to ___:** ___________________
EOF
nano docs/improvement-plan.md
```

```bash
git add scripts/ docs/
git commit -m "docs: capstone verification, game day report and 30-60-90 plan"
git push -u origin HEAD
```

---

## Debrief — discussion questions

1. **Which single practice from this week would most reduce your lead time?** Why that one?
2. **What could you implement on Monday** with no budget and no permission?
3. Look at your Lab 01 value stream map. **Would the constraint you found still be the
   constraint** if you had everything you built this week? What becomes the new one?
4. Which of the ten anti-patterns is most present in your organisation, and what is the first
   step?
5. **The uncomfortable one:** which of these practices will your organisation *not* adopt, and
   what is the real reason? Is it technical, or is it structural?

---

## What you built in six days

```
 Day 1  git repo · value stream map · CALMS baseline
 Day 2  GitHub · branch protection · PRs · CI (Actions + Jenkins) · Dependabot
 Day 3  multi-stage image 1.1 GB → 150 MB · non-root · Compose stack · GHCR
 Day 4  3-node cluster · Deployment · probes · Service · ConfigMap/Secret · PVC
        · Ingress · HPA · PDB · NetworkPolicy
 Day 5  Terraform module × 2 environments · Ansible roles · GitOps pipeline
        · blue-green · canary · weighted routing · auto-rollback
 Day 6  5 security gates · SBOM · Sealed Secrets · Prometheus · Grafana
        · SLO burn-rate alerts · runbook · post-mortem · game day
```

**Every one of these is running on a laptop, cost £0, and is defined in a git repository that
anyone can clone and reproduce.**

---

## Keeping the environment

```bash
k3d cluster stop paytrack          # frees RAM, keeps everything
k3d cluster start paytrack         # back, identical
# k3d cluster delete paytrack      # then rebuild: k3d cluster create --config k8s/k3d-cluster.yaml
#                                 followed by kubectl apply -f k8s/base/ and terraform apply
```
**You can delete the whole cluster without fear** — that is what the last six days were for.

---

## Where to go next

| Direction | Start with |
|---|---|
| **Kubernetes depth** | CKA / CKAD certification; operators and CRDs |
| **GitOps** | Argo CD or Flux properly; Argo Rollouts for progressive delivery |
| **Platform engineering** | Backstage; *Team Topologies* (Skelton & Pais) |
| **SRE** | Google's *SRE Book* and *SRE Workbook* (free online) |
| **Security** | OWASP Top 10 CI/CD Risks; SLSA; cosign and sigstore |
| **Observability** | OpenTelemetry; distributed tracing; Loki |
| **The theory** | *Accelerate* (Forsgren, Humble, Kim) — read this one first |
| **Cloud** | Take your Terraform to a real cloud; add OIDC federation and remote state |

---

## 🎯 Outcome

A verified end-to-end DevOps platform, a game-day incident worked against the clock with your
own runbook, and a written 30-60-90 day plan grounded in your own measurements.

**Congratulations — course complete.**

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Timing:** 10 min verify, 10 min game day, 15 min debrief. **Protect the debrief** — it is
  what converts a week of labs into something delegates act on.
- **Run the game day in pairs**, with the on-call person genuinely not watching the injection.
  The dynamic changes completely when someone cannot see what was done.
- **Failure 4 (Service selector) is the one to save for the strongest pair.** Everything looks
  healthy and `rollout undo` does not help. The lesson — check the EndpointSlice — is worth
  more than the other four combined.
- **Make the improvement plan concrete.** Push back on "improve our CI". Ask: which repository,
  by when, and what number moves?
- **Close with question 5.** The honest answer is usually structural, not technical, which
  loops straight back to day 1: DevOps is a culture and systems problem that happens to have
  excellent tooling.
- **Send the repository home with them.** It is theirs; it works; it cost nothing. That is the
  most durable deliverable of the week.
</details>
