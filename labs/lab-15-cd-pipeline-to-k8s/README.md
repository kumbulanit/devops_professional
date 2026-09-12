# Lab 15 — End-to-End CI/CD: Commit to Kubernetes

| | |
|---|---|
| **Day** | 5 |
| **Duration** | 25 minutes |
| **Module** | 6 — Continuous Delivery |
| **You will produce** | A GitOps pipeline: `git push` → build → scan → push → manifest update → cluster reconciles |
| **Feeds into** | Lab 16 (deployment strategies), Lab 17 (security gates), Lab 19 (capstone) |

---

## Objective

Join everything from days 1–5 into one automated path. A code change reaches Kubernetes with
no human touching `kubectl`, and the git history is the complete record of what is deployed.

**The architecture problem, and how we solve it honestly.** GitHub's hosted runners cannot
reach your laptop's k3d cluster. Rather than pretend otherwise, we use the **pull-based
GitOps model**, which is the better pattern anyway:

```
  PUSH-BASED (what we avoid)            PULL-BASED GitOps (what you will build)
  ┌────────────────┐                    ┌────────────────┐
  │ CI holds       │                    │ CI builds the  │
  │ CLUSTER        │                    │ image and      │
  │ CREDENTIALS    │                    │ COMMITS the    │
  │      │         │                    │ new tag        │
  │  kubectl apply ├──► cluster         └───────┬────────┘
  └────────────────┘                            │ git
   ✗ CI needs prod credentials          ┌───────▼────────┐
   ✗ Drift is invisible                 │  CONFIG REPO   │
   ✗ No self-healing                    └───────┬────────┘
                                                │ agent PULLS
                                        ┌───────▼─────────────┐
                                        │ reconciler INSIDE   │
                                        │ the cluster         │
                                        └───────┬─────────────┘
                                                ▼  cluster
   ✓ No credentials leave the cluster  ✓ Drift auto-corrected  ✓ git = the audit log
```

In production this agent is **Argo CD** or **Flux**. Here you will build a 40-line
reconciler so the mechanism is visible rather than magic.

## Prerequisites

- Labs 09–13 complete; cluster running; CI and image build working

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev && kubectl apply -f k8s/base/
```

---

## Step 1 — Separate desired state from the base manifests

```bash
cd ~/devops-course/paytrack-api-team
mkdir -p k8s/overlays/dev
cat > k8s/overlays/dev/image.yaml <<'EOF'
# ═══════════════════════════════════════════════════════════════════════════
#  DESIRED STATE — the single file CI updates and the reconciler reads.
#  Everything the cluster runs is determined by what is committed here.
#  Its git history is the deployment history.
# ═══════════════════════════════════════════════════════════════════════════
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paytrack-api
  namespace: paytrack-dev
spec:
  template:
    spec:
      containers:
        - name: paytrack-api
          image: paytrack-api:1.0.0     # ← CI rewrites this line, and only this line
EOF
```
**What this does:** creates a **strategic-merge patch**. It is not a whole Deployment — it
names the object and the one field to change. `kubectl patch` merges it into the live object,
so the base manifest stays authoritative for everything else.

---

## Step 2 — The reconciler

```bash
mkdir -p scripts
cat > scripts/gitops-sync.sh <<'EOF'
#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  A minimal GitOps reconciler.
#  Loop forever: fetch the repo → if the desired state changed, apply it.
#  This is what Argo CD and Flux do, minus the UI, RBAC, health assessment,
#  multi-tenancy, drift dashboards and pruning.
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

REPO_DIR="${REPO_DIR:-$HOME/devops-course/paytrack-api-team}"
BRANCH="${BRANCH:-main}"
INTERVAL="${INTERVAL:-15}"
NAMESPACE="${NAMESPACE:-paytrack-dev}"
OVERLAY="k8s/overlays/dev/image.yaml"

log() { printf '%s  %s\n' "$(date +%H:%M:%S)" "$*"; }

cd "$REPO_DIR" || { log "FATAL: $REPO_DIR not found"; exit 1; }
log "reconciler started — watching $BRANCH every ${INTERVAL}s"

LAST_APPLIED=""

while true; do
  git fetch origin "$BRANCH" --quiet 2>/dev/null

  REMOTE_SHA=$(git rev-parse "origin/$BRANCH" 2>/dev/null)
  LOCAL_SHA=$(git rev-parse HEAD 2>/dev/null)

  if [ "$REMOTE_SHA" != "$LOCAL_SHA" ]; then
    log "new commit on origin/$BRANCH: ${REMOTE_SHA:0:7} — pulling"
    git pull --ff-only origin "$BRANCH" --quiet || { log "pull failed (diverged?)"; sleep "$INTERVAL"; continue; }
  fi

  DESIRED_IMAGE=$(grep -E '^\s+image:' "$OVERLAY" | awk '{print $2}')

  if [ "$DESIRED_IMAGE" != "$LAST_APPLIED" ]; then
    log "desired image: $DESIRED_IMAGE"

    # Pre-pull into the cluster so pods do not wait on a registry round-trip.
    if [[ "$DESIRED_IMAGE" == ghcr.io/* ]]; then
      docker pull "$DESIRED_IMAGE" --quiet >/dev/null 2>&1 \
        && k3d image import "$DESIRED_IMAGE" -c paytrack >/dev/null 2>&1 \
        && log "imported image into the cluster"
    fi

    kubectl apply -f k8s/base/ >/dev/null
    kubectl patch deployment paytrack-api -n "$NAMESPACE" \
      --patch-file "$OVERLAY" >/dev/null

    if kubectl rollout status deployment/paytrack-api -n "$NAMESPACE" --timeout=120s >/dev/null; then
      LIVE=$(kubectl get deployment paytrack-api -n "$NAMESPACE" \
              -o jsonpath='{.spec.template.spec.containers[0].image}')
      log "✅ SYNCED — live image: $LIVE"
      LAST_APPLIED="$DESIRED_IMAGE"
    else
      log "❌ ROLLOUT FAILED — rolling back"
      kubectl rollout undo deployment/paytrack-api -n "$NAMESPACE"
      kubectl rollout status deployment/paytrack-api -n "$NAMESPACE" --timeout=90s >/dev/null
      log "rolled back; will retry when the desired state changes"
      LAST_APPLIED="$DESIRED_IMAGE"     # do not loop on a known-bad image
    fi
  fi

  sleep "$INTERVAL"
done
EOF
chmod +x scripts/gitops-sync.sh
```
**What the reconciler does, and why each part is there:**

| Behaviour | Purpose |
|---|---|
| `git fetch` then compare SHAs | Detects a new desired state without a webhook — **pull, not push** |
| Apply only when the image changed | Avoids pointless rollouts every 15 seconds |
| `k3d image import` | Pre-loads the image so pods start immediately (a lab optimisation) |
| `kubectl patch --patch-file` | Merges the one changed field into the live object |
| `rollout status --timeout` | **Turns "applied" into "verified".** Applying is not deploying |
| **Automatic `rollout undo` on failure** | A failed deployment self-heals. This is the automated rollback from Module 6 §6.4 |
| `LAST_APPLIED` after a failure | Prevents an infinite retry loop on a known-bad image |

> **What Argo CD adds:** a UI showing sync and health status, RBAC and multi-tenancy,
> automatic pruning of deleted resources, drift correction (not just change detection),
> sync waves and hooks, and notifications. The *concept* is exactly what you just wrote.

---

## Step 3 — The deploy pipeline

```bash
git switch -c ci/add-cd-pipeline
cat > .github/workflows/cd.yml <<'EOF'
name: CD — Build, Scan, Publish, Promote

on:
  push:
    branches: [main]
    paths-ignore:
      - 'k8s/overlays/**'        # CRITICAL: prevents the promote commit re-triggering this
      - '**.md'
  workflow_dispatch:

permissions:
  contents: write                # needed to commit the manifest update
  packages: write                # needed to push to GHCR

concurrency:
  group: cd-${{ github.ref }}
  cancel-in-progress: false      # NEVER cancel a deploy mid-flight

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ═══════════════════════════════════════════════════════════════════
  test:
    name: 1 · Test
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip, cache-dependency-path: app/requirements-dev.txt }
      - run: pip install -r app/requirements-dev.txt
      - run: flake8 app/src app/tests
      - run: pytest app/tests --cov=src --cov-report=term
        working-directory: app

  # ═══════════════════════════════════════════════════════════════════
  build:
    name: 2 · Build, scan and publish
    needs: test                  # nothing is built until the tests pass
    runs-on: ubuntu-24.04
    outputs:
      image: ${{ steps.out.outputs.image }}
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Lowercase the image path
        id: lower
        run: echo "repo=$(echo '${{ env.IMAGE_NAME }}' | tr '[:upper:]' '[:lower:]')" >> "$GITHUB_OUTPUT"

      - name: Build and push (BUILD ONCE — this artefact is promoted unchanged)
        id: push
        uses: docker/build-push-action@v6
        with:
          context: ./app
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ steps.lower.outputs.repo }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ steps.lower.outputs.repo }}:main
          build-args: |
            GIT_SHA=${{ github.sha }}
            APP_VERSION=1.${{ github.run_number }}.0
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan the image
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: ${{ env.REGISTRY }}/${{ steps.lower.outputs.repo }}:${{ github.sha }}
          severity: HIGH,CRITICAL
          ignore-unfixed: true        # do not block on CVEs with no available fix
          exit-code: '0'              # Lab 17 changes this to '1' — a real gate
          format: table

      - id: out
        run: echo "image=${{ env.REGISTRY }}/${{ steps.lower.outputs.repo }}:${{ github.sha }}" >> "$GITHUB_OUTPUT"

  # ═══════════════════════════════════════════════════════════════════
  promote:
    name: 3 · Promote (commit the desired state)
    needs: build
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Update the desired image in the overlay
        run: |
          NEW_IMAGE="${{ needs.build.outputs.image }}"
          echo "Promoting: $NEW_IMAGE"
          sed -i -E "s|^(\s+image:).*|\1 ${NEW_IMAGE}|" k8s/overlays/dev/image.yaml
          grep 'image:' k8s/overlays/dev/image.yaml

      - name: Commit the promotion
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          if git diff --quiet; then
            echo "No change to promote."; exit 0
          fi
          git add k8s/overlays/dev/image.yaml
          git commit -m "deploy: promote ${{ github.sha }} to dev

          Source commit : ${{ github.sha }}
          Image         : ${{ needs.build.outputs.image }}
          Digest        : ${{ needs.build.outputs.digest }}
          Pipeline run  : ${{ github.run_id }}

          [skip ci]"
          git push

      - name: Deployment summary
        run: |
          {
            echo "## Promoted to dev"
            echo ""
            echo "| Field | Value |"
            echo "|---|---|"
            echo "| Image | \`${{ needs.build.outputs.image }}\` |"
            echo "| Digest | \`${{ needs.build.outputs.digest }}\` |"
            echo "| Source commit | ${{ github.sha }} |"
            echo ""
            echo "The in-cluster reconciler will pick this up within 15 seconds."
          } >> "$GITHUB_STEP_SUMMARY"
EOF
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/cd.yml'));print('YAML valid')"
```
**The design decisions that matter:**

| Decision | Reason |
|---|---|
| `paths-ignore: k8s/overlays/**` | **Without this you get an infinite loop**: the promote commit triggers the workflow, which promotes again, forever |
| `needs: test` → `needs: build` | A strict DAG. Nothing is published unless tests pass; nothing is promoted unless the image exists |
| Tag with `${{ github.sha }}` | **Immutable.** You can always answer "which commit is running in production?" |
| Build once in one job | The **same digest** is promoted — no rebuild per environment (Module 6 §6.2) |
| `permissions: contents: write` | The minimum needed to commit the promotion. No PAT to create or rotate |
| `[skip ci]` in the message | Belt and braces alongside `paths-ignore` |
| `cancel-in-progress: false` | **Never cancel a deployment mid-rollout.** Half-applied state is worse than a slow queue |
| `ignore-unfixed: true` | Do not block on vulnerabilities that have no patch — you would only teach people to bypass the gate |

```bash
git add .github/workflows/cd.yml k8s/overlays scripts/
git commit -m "feat(cd): GitOps pipeline from commit to cluster

test -> build+scan+publish -> promote (commit the new image tag).
An in-cluster reconciler pulls the change, applies it, verifies the rollout
and rolls back automatically on failure.

Pull-based: no cluster credentials ever leave the cluster, and the git
history of k8s/overlays IS the deployment history."
git push -u origin ci/add-cd-pipeline
```
Open and **merge** the PR.

---

## Step 4 — Start the reconciler

In a **dedicated terminal** (leave it running for the rest of the course):

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
./scripts/gitops-sync.sh
```
**What this does:** starts the loop. You should see it log the current desired image and
`✅ SYNCED`.

---

## Step 5 — Ship a change and watch it arrive

In your **main terminal**:

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
git switch -c feat/add-build-info

python3 - <<'PY'
import pathlib, re
p = pathlib.Path("app/src/app.py")
s = p.read_text()

# Anchor on the info() endpoint itself, so this works regardless of which
# fields earlier labs already added. It ASSERTS - a silent no-op would leave
# you debugging a deployment that never actually changed.
m = re.search(r'(def info\(\):\n        return jsonify\(\n)(.*?)(        \)\n)', s, re.S)
assert m, "could not find the info() endpoint in app/src/app.py"

if "git_sha" not in m.group(2):
    added = ('            git_sha=os.getenv("GIT_SHA", "unknown"),\n'
             '            pipeline="gitops",\n')
    s = s[:m.end(2)] + added + s[m.end(2):]
    p.write_text(s)
    print("added git_sha and pipeline to /api/v1/info")
else:
    print("already present - nothing to do")
PY

cd app && source .venv/bin/activate 2>/dev/null && pytest -q && deactivate; cd ..
git add app/src/app.py
git commit -m "feat(api): report git_sha and pipeline in /api/v1/info

Lets an operator confirm exactly which commit is serving, without checking
the deployment manifest."
git push -u origin feat/add-build-info
```
Open the PR, wait for CI to go green, then **Squash and merge**.

**Now watch the whole chain, end to end:**

1. **GitHub Actions tab** — `test` → `build` → `promote` (≈2–3 minutes)
2. **The promote commit** appears on `main`, authored by `github-actions[bot]`, with the SHA
   and digest in its message
3. **Your reconciler terminal** logs:
   ```
   14:22:31  new commit on origin/main: a3f9e2c — pulling
   14:22:33  desired image: ghcr.io/you/paytrack-api:a3f9e2c1…
   14:22:41  imported image into the cluster
   14:22:58  ✅ SYNCED — live image: ghcr.io/you/paytrack-api:a3f9e2c1…
   ```

✅ **Checkpoint**
```bash
curl -s http://paytrack.localhost:8080/api/v1/info | jq
kubectl get deployment paytrack-api -n paytrack-dev \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```
The new fields are present, and the running image tag is the commit SHA you merged.

> **You did not run `kubectl` once.** A code change went from your editor to a running
> Kubernetes workload, and the git log records every step with the commit, the image and the
> digest. That is Continuous Delivery.

---

## Step 6 — Trace a running container back to its commit

```bash
LIVE=$(kubectl get deployment paytrack-api -n paytrack-dev -o jsonpath='{.spec.template.spec.containers[0].image}')
echo "Running: $LIVE"
docker inspect "$LIVE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' 2>/dev/null \
  || echo "(pull the image first to inspect its labels)"
git log --oneline -3 -- k8s/overlays/dev/image.yaml
```
**What this does:** answers the audit question — *which commit is running, who approved it,
and when was it deployed?* — from the OCI labels stamped in Lab 06 and the git history of the
overlay. **This is the change record**, generated automatically, no ticket typed by hand
(Module 9 §9.1).

---

## Step 7 — Prove the automatic rollback

```bash
git switch main && git pull
sed -i -E "s|^(\s+image:).*|\1 ghcr.io/does-not-exist/nope:v9|" k8s/overlays/dev/image.yaml
git add k8s/overlays/dev/image.yaml
git commit -m "test: deploy a deliberately broken image [skip ci]"
git push
```
**What this does:** commits a desired state that cannot possibly work.

**Watch the reconciler terminal:**
```
14:31:02  new commit on origin/main: 7c1d4f8 — pulling
14:31:04  desired image: ghcr.io/does-not-exist/nope:v9
14:33:05  ❌ ROLLOUT FAILED — rolling back
14:33:19  rolled back; will retry when the desired state changes
```

```bash
curl -s http://paytrack.localhost:8080/health | jq
kubectl get pods -n paytrack-dev
```
**The service never went down.** `maxUnavailable: 0` kept the healthy pods serving while the
new one failed to pull, and the reconciler undid the change automatically.

```bash
git revert --no-edit HEAD
git push
```
**What this does:** `git revert` restores the previous desired state as a **new commit** —
history preserved, fully auditable. The reconciler picks it up and re-syncs.

> **In GitOps, rollback is `git revert`.** The same review, the same audit trail, the same
> mechanism as any other change.

---

## ✅ Final checkpoint

```bash
curl -s http://paytrack.localhost:8080/api/v1/info | jq
git log --oneline -6
kubectl rollout history deployment/paytrack-api -n paytrack-dev
```

---

## 🧩 Stretch (homework)

1. **Install the real thing.**
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```
   Then create an `Application` pointing at your repo and compare its sync/health UI with
   your script.
2. **Separate the config repo.** Move `k8s/` to its own repository. This is standard practice:
   it separates who may change code from who may change what is deployed.
3. **Kustomize.** Replace the patch file with `kustomization.yaml` and
   `kustomize edit set image`. Then `kubectl apply -k` — no `sed` on YAML.
4. **Deployment metrics.** Have the promote job append the timestamp and commit to a file, and
   compute your own **lead time for change** and **deployment frequency** (Module 9 §9.2).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Workflow loops forever | `paths-ignore` missing | Confirm `k8s/overlays/**` is ignored in `cd.yml` |
| `permission denied` on the promote push | Missing `contents: write` | Check the `permissions:` block and repo Actions settings |
| Reconciler never syncs | Not on `main`, or a diverged local branch | `git switch main && git pull --ff-only` |
| `ImagePullBackOff` on the GHCR image | Package is private | Make it public, or add an `imagePullSecret` |
| GHCR path rejected | Uppercase in the repo name | The `tr '[:upper:]' '[:lower:]'` step handles it |
| Rollout times out on a good image | Slow pull on first use | Raise the timeout, or rely on the `k3d image import` step |

---

## 🎯 Outcome

A complete GitOps delivery pipeline: commit → test → build once → scan → publish → promote →
reconcile → verify → auto-rollback. No human runs `kubectl`, no cluster credential leaves the
cluster, and git is the deployment history.

**Next:** [Lab 16 — Deployment Strategies](../lab-16-deployment-strategies/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **This is the keystone lab.** If time is short elsewhere, protect this one — Labs 17 and 19
  both extend this pipeline.
- **Have a dedicated projector terminal running the reconciler** for the whole afternoon.
  Delegates watching it log `✅ SYNCED` while they merge a PR is the single best moment of
  day 5.
- **The three things that go wrong:**
  1. The infinite workflow loop when `paths-ignore` is mistyped. Show them how to spot it in
     the Actions tab, and how to stop it.
  2. GHCR uppercase paths. The lowercase step handles it — point it out.
  3. Someone leaves the reconciler running on a feature branch and nothing syncs.
- **Step 7 (auto-rollback) is worth its three minutes.** A broken image is deployed and the
  service stays up and self-heals. Ask what happens today in their environment.
- **Debrief question:** "Right now, who in your organisation can answer 'which commit is
  running in production?' in under a minute — and how?"
</details>
