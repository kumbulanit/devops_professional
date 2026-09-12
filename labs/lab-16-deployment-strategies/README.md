# Lab 16 — Deployment Strategies: Blue-Green, Canary, Rollback

| | |
|---|---|
| **Day** | 5 |
| **Duration** | 17 minutes (**CORE**: Parts 1–2 · **STRETCH**: Parts 3–4) |
| **Module** | 6 — Continuous Delivery |
| **You will produce** | Working blue-green and canary deployments you can *see* in a browser |
| **Feeds into** | Lab 19 (capstone) |

---

## Objective

Implement three deployment strategies on the running cluster and **watch traffic move**. The
PayTrack API banner changes colour with `APP_COLOR`, which turns an abstract routing concept into
something visible.

> **Trainer:** Parts 1–2 are core. Parts 3–4 are marked STRETCH and can be homework.

## Prerequisites

- Lab 12 (Ingress) and Lab 15 (pipeline). **Pause the reconciler** (`Ctrl+C` in its terminal)
  so it does not fight you.

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev
kubectl apply -f k8s/base/ && kubectl rollout status deployment/paytrack-api
```

---

## Part 1 — Blue-Green (CORE, 7 min)

### The mechanism, in one sentence

**A Service selects pods by label. Change the label it selects, and 100 % of traffic moves
atomically.**

```
        Service paytrack-api  selector: {app: paytrack-api, version: blue}
                                                      ▲
              ┌───────────────────────────────────────┘  ONE field edit
              │                                          moves ALL traffic
   ┌──────────▼──────────┐        ┌─────────────────────┐
   │ Deployment BLUE     │        │ Deployment GREEN    │
   │ version: blue       │        │ version: green      │
   │ 3 replicas · LIVE   │        │ 3 replicas · warm,  │
   │                     │        │ tested, 0 % traffic │
   └─────────────────────┘        └─────────────────────┘
```

### Step 1.1 — Deploy both colours

```bash
cd ~/devops-course/paytrack-api-team
mkdir -p k8s/strategies

for COLOR in blue green; do
cat > k8s/strategies/deployment-${COLOR}.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paytrack-api-${COLOR}
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
    version: ${COLOR}
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: paytrack-api
      version: ${COLOR}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: paytrack-api
        version: ${COLOR}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
        - name: paytrack-api
          image: paytrack-api:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
          env:
            - name: APP_COLOR
              value: "${COLOR}"
            - name: APP_VERSION
              value: "$( [ "${COLOR}" = "blue" ] && echo 1.0.0 || echo 2.0.0 )"
            - name: READINESS_REQUIRES_DB
              value: "false"
          readinessProbe:
            httpGet: { path: /ready, port: http }
            periodSeconds: 3
          livenessProbe:
            httpGet: { path: /health, port: http }
            periodSeconds: 10
          resources:
            requests: { cpu: 25m, memory: 48Mi }
            limits:   { cpu: 150m, memory: 128Mi }
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - name: tmp
          emptyDir: { sizeLimit: 32Mi }
EOF
done

kubectl apply -f k8s/strategies/deployment-blue.yaml
kubectl apply -f k8s/strategies/deployment-green.yaml
kubectl rollout status deployment/paytrack-api-blue --timeout=90s
kubectl rollout status deployment/paytrack-api-green --timeout=90s
kubectl get pods -l app.kubernetes.io/name=paytrack-api --show-labels | head
```
**What this does:** a `for` loop writes both manifests from one template — identical except
for the `version` label, `APP_COLOR` and `APP_VERSION`. **Both are running; neither is
receiving traffic yet.**

### Step 1.2 — Point the Service at blue

```bash
cat > k8s/strategies/service-bluegreen.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: paytrack-bg
  namespace: paytrack-dev
spec:
  selector:
    app.kubernetes.io/name: paytrack-api
    version: blue                 # ← THE SWITCH. This one line decides everything.
  ports:
    - name: http
      port: 80
      targetPort: http
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paytrack-bg
  namespace: paytrack-dev
spec:
  ingressClassName: traefik
  rules:
    - host: bg.paytrack.localhost
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paytrack-bg
                port: { number: 80 }
EOF
kubectl apply -f k8s/strategies/service-bluegreen.yaml
grep -q 'bg.paytrack.localhost' /etc/hosts || \
  echo "127.0.0.1  bg.paytrack.localhost" | sudo tee -a /etc/hosts
```

```bash
for i in $(seq 1 6); do curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done
```
**All `blue`.** Open **http://bg.paytrack.localhost:8080/** — a blue banner.

### Step 1.3 — Smoke-test green *before* sending it any traffic

```bash
kubectl port-forward deployment/paytrack-api-green 9999:8080 >/dev/null 2>&1 &
sleep 3
curl -s localhost:9999/api/v1/info | jq
curl -s localhost:9999/health | jq -r '.status'
kill %1 2>/dev/null
```
**What this does:** tests green **in the real cluster, with real configuration, on real
infrastructure** — while it serves zero user traffic. This is blue-green's central advantage:
verification in production conditions, without production risk.

### Step 1.4 — The cut-over

```bash
watch -n 1 'curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r ".color + \" \" + .version"' &
sleep 2
kubectl patch service paytrack-bg -p '{"spec":{"selector":{"version":"green"}}}'
sleep 8
kill %1 2>/dev/null
for i in $(seq 1 6); do curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done
```
**What this does:** the `watch` polls once a second while `kubectl patch` changes one field.
Within about a second every response flips from `blue 1.0.0` to `green 2.0.0`.

Refresh the browser — **green banner**. 100 % of traffic moved in a single atomic API-server
operation.

### Step 1.5 — Roll back in one command

```bash
kubectl patch service paytrack-bg -p '{"spec":{"selector":{"version":"blue"}}}'
curl -s http://bg.paytrack.localhost:8080/api/v1/info | jq -r '.color'
```
**Back to blue, instantly** — because blue never stopped running. That is the whole point:
**your rollback is already deployed, warm, and proven.**

> **What blue-green does not roll back:** database schema changes, messages already published
> to a queue, emails already sent, and state written by green during the cut-over. Deploying
> both colours against one database is why the expand/contract pattern (Module 6 §6.6) is
> mandatory.
>
> **The cost:** 2× capacity during the cut-over.

---

## Part 2 — Canary (CORE, 6 min)

### The mechanism

**Replica ratio.** With a Service that selects *both* versions, a pod's share of the traffic
equals its share of the endpoints. 9 stable + 1 canary ≈ 10 % to the canary.

```
      Service paytrack-canary  selector: {app: paytrack-api}   ← no version label!
                    │
        ┌───────────┴────────────┐
        ▼ 9 endpoints (90%)      ▼ 1 endpoint (10%)
   ┌─────────────┐          ┌─────────────┐
   │ STABLE blue │          │ CANARY green│  ← watch its metrics
   └─────────────┘          └─────────────┘
```

### Step 2.1 — A Service that selects both

```bash
cat > k8s/strategies/service-canary.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: paytrack-canary
  namespace: paytrack-dev
spec:
  selector:
    app.kubernetes.io/name: paytrack-api    # deliberately NOT filtered by version
  ports:
    - name: http
      port: 80
      targetPort: http
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paytrack-canary
  namespace: paytrack-dev
spec:
  ingressClassName: traefik
  rules:
    - host: canary.paytrack.localhost
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paytrack-canary
                port: { number: 80 }
EOF
kubectl apply -f k8s/strategies/service-canary.yaml
grep -q 'canary.paytrack.localhost' /etc/hosts || \
  echo "127.0.0.1  canary.paytrack.localhost" | sudo tee -a /etc/hosts
```

### Step 2.2 — Park the base deployment first

> ⚠️ **Do this before you measure anything.** The canary Service selects on
> `app.kubernetes.io/name: paytrack-api` alone — and **the Deployment you created in Lab 10
> carries that same label**. Leave it running and the Service selects *its* pods too, so your
> "90/10" split is really 9 blue : 1 green : 3 unlabelled, the endpoint count is 13 instead of
> 10, and the arithmetic stops teaching anything.

```bash
kubectl scale deployment/paytrack-api --replicas=0
kubectl get pods -l app.kubernetes.io/name=paytrack-api --show-labels | head
```
**What this does:** scales the Lab 10 deployment to zero so only blue and green are selected.
You will scale it back in Step 5. **This is not a workaround — it is the lesson**: a Service
selects on labels, and a label you forgot about is a pod you did not intend to send traffic to.

### Step 2.3 — Set the ratio to 90/10 and measure it

```bash
kubectl scale deployment/paytrack-api-blue  --replicas=9
kubectl scale deployment/paytrack-api-green --replicas=1
kubectl rollout status deployment/paytrack-api-blue --timeout=120s
kubectl get endpointslices -l kubernetes.io/service-name=paytrack-canary \
  -o jsonpath='{.items[*].endpoints[*].addresses[*]}' | wc -w
```
**What this does:** sets the ratio and counts the endpoints behind the Service — expect
**10**. If you get 13, you skipped Step 2.2.

```bash
echo "Sampling 100 requests…"
for i in $(seq 1 100); do
  curl -s http://canary.paytrack.localhost:8080/api/v1/info | jq -r '.color'
done | sort | uniq -c | sort -rn
```
**What this does:** 100 requests, counted by colour. Expect roughly:
```
     90 blue
     10 green
```
**That is a 10 % canary**, achieved with nothing but replica counts and one Service.

### Step 2.4 — Progressive promotion

```bash
progress() {
  echo "── stable=$1  canary=$2 ──"
  kubectl scale deployment/paytrack-api-blue  --replicas=$1 >/dev/null
  kubectl scale deployment/paytrack-api-green --replicas=$2 >/dev/null
  kubectl rollout status deployment/paytrack-api-green --timeout=90s >/dev/null
  sleep 6
  for i in $(seq 1 40); do curl -s http://canary.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done \
    | sort | uniq -c
}
progress 7 3        # ~30% canary
progress 5 5        # ~50%
progress 0 10       # 100% - fully promoted
```
**What this does:** defines a shell function and calls it three times, walking the canary from
10 % → 30 % → 50 % → 100 %, sampling the split at each step.

> 🔑 **In production, each step is gated on metrics, not on a `sleep`.** You watch the
> canary's error rate, p95 latency and saturation for a **bake period**, and promote only if
> they stay within budget. If they degrade, you scale the canary to 0 and you are done —
> **that is the automatic abort**, and it is why a canary's blast radius is the smallest of
> any strategy.
>
> Tools that automate exactly this: **Argo Rollouts** and **Flagger**.

### Step 2.5 — Abort a canary

```bash
kubectl scale deployment/paytrack-api-blue --replicas=9
kubectl scale deployment/paytrack-api-green --replicas=1
sleep 8
echo "-- canary live at ~10% --"
for i in $(seq 1 20); do curl -s http://canary.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done | sort | uniq -c

kubectl scale deployment/paytrack-api-green --replicas=0     # ← ABORT
sleep 6
echo "-- after abort --"
for i in $(seq 1 20); do curl -s http://canary.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done | sort | uniq -c
```
**100 % blue.** The abort took one command and affected only the 10 % of users who had been
seeing the canary.

---

## Part 3 — Weighted routing at the proxy (STRETCH)

Replica-ratio canaries are coarse: 1 % needs 99 stable pods. Real traffic splitting happens at
the proxy. Traefik provides a `TraefikService` with explicit weights.

```bash
cat > k8s/strategies/traefik-weighted.yaml <<'EOF'
---
apiVersion: v1
kind: Service
metadata: { name: paytrack-stable-svc, namespace: paytrack-dev }
spec:
  selector: { app.kubernetes.io/name: paytrack-api, version: blue }
  ports: [{ name: http, port: 80, targetPort: http }]
---
apiVersion: v1
kind: Service
metadata: { name: paytrack-canary-svc, namespace: paytrack-dev }
spec:
  selector: { app.kubernetes.io/name: paytrack-api, version: green }
  ports: [{ name: http, port: 80, targetPort: http }]
---
apiVersion: traefik.io/v1alpha1
kind: TraefikService
metadata: { name: paytrack-weighted, namespace: paytrack-dev }
spec:
  weighted:
    services:
      - name: paytrack-stable-svc
        port: 80
        weight: 95            # ← change this pair to shift traffic.
      - name: paytrack-canary-svc
        port: 80
        weight: 5             #   No pod counts involved at all.
---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata: { name: paytrack-weighted, namespace: paytrack-dev }
spec:
  entryPoints: [web]
  routes:
    - match: Host(`weighted.paytrack.localhost`)
      kind: Rule
      services:
        - name: paytrack-weighted
          namespace: paytrack-dev
          kind: TraefikService
EOF
kubectl apply -f k8s/strategies/traefik-weighted.yaml
grep -q 'weighted.paytrack.localhost' /etc/hosts || \
  echo "127.0.0.1  weighted.paytrack.localhost" | sudo tee -a /etc/hosts

kubectl scale deployment/paytrack-api-blue --replicas=2
kubectl scale deployment/paytrack-api-green --replicas=2
sleep 10
for i in $(seq 1 100); do curl -s http://weighted.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done | sort | uniq -c
```
**What this does:** splits traffic **95/5 with two pods each**. Weights are independent of
replica counts, so you can run a 1 % canary without 99 stable pods — and you can shift traffic
without any scheduling at all.

```bash
kubectl patch traefikservice paytrack-weighted --type merge \
  -p '{"spec":{"weighted":{"services":[{"name":"paytrack-stable-svc","port":80,"weight":50},{"name":"paytrack-canary-svc","port":80,"weight":50}]}}}'
sleep 5
for i in $(seq 1 60); do curl -s http://weighted.paytrack.localhost:8080/api/v1/info | jq -r '.color'; done | sort | uniq -c
```
**What this does:** shifts to 50/50 instantly, with no pod churn.

---

## Part 4 — Rollback methods compared (STRETCH)

```bash
kubectl set image deployment/paytrack-api-blue paytrack-api=paytrack-api:2.0.0 --record 2>/dev/null || \
  kubectl set image deployment/paytrack-api-blue paytrack-api=paytrack-api:2.0.0
sleep 3
kubectl rollout history deployment/paytrack-api-blue

echo "── 1. kubectl rollout undo ──"
time kubectl rollout undo deployment/paytrack-api-blue
kubectl rollout status deployment/paytrack-api-blue --timeout=90s

echo "── 2. blue-green selector flip ──"
time kubectl patch service paytrack-bg -p '{"spec":{"selector":{"version":"green"}}}'
kubectl patch service paytrack-bg -p '{"spec":{"selector":{"version":"blue"}}}'

echo "── 3. canary abort ──"
time kubectl scale deployment/paytrack-api-green --replicas=0
```

| Method | Typical time | Scope | Notes |
|---|---|---|---|
| `rollout undo` | 20–60 s | The whole Deployment | Old ReplicaSet still exists at `desired 0` |
| Blue-green flip | **< 1 s** | All traffic | The alternative is already running |
| Canary abort | **< 5 s** | Only the canary share | Smallest blast radius throughout |
| `git revert` + pipeline | 3–10 min | Everything | **Slowest but the most auditable** — the production default |
| Feature flag off | **instant** | One feature | No deployment at all; the fastest rollback that exists |

---

## Step 5 — Clean up and commit

```bash
kubectl delete -f k8s/strategies/traefik-weighted.yaml --ignore-not-found
kubectl delete -f k8s/strategies/service-canary.yaml --ignore-not-found
kubectl delete -f k8s/strategies/service-bluegreen.yaml --ignore-not-found
kubectl delete deployment paytrack-api-blue paytrack-api-green --ignore-not-found
kubectl scale deployment/paytrack-api --replicas=3        # restore the base deployment
kubectl rollout status deployment/paytrack-api --timeout=90s
kubectl get pods -n paytrack-dev
```
**What this does:** removes the strategy resources and **scales the Lab 10 deployment back to
3** — you parked it in Step 2.2 and tomorrow's observability lab needs it running.

```bash
git add k8s/strategies/
git commit -m "feat(k8s): blue-green and canary deployment manifests

- blue-green: two Deployments labelled by version; the Service selector is
  the switch. Cut-over and rollback are one atomic field edit
- canary: one Service selecting both versions; the split is the replica ratio
- weighted: Traefik TraefikService with explicit weights, decoupling the
  traffic split from pod counts (1% canary without 99 stable pods)"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

Answer from what you observed:
1. Which single field moves 100 % of traffic in blue-green?
2. Why is a canary's blast radius smaller than blue-green's?
3. What does blue-green **not** roll back?
4. When is `Recreate` the correct choice?
5. Why is `git revert` + pipeline usually preferred in production despite being slowest?

Answers: [`solutions/lab-16-answers.md`](../../solutions/lab-16-answers.md)

---

## 🧩 Stretch (homework)

1. **Argo Rollouts.** Install it and convert the canary to a `Rollout` with `analysis` steps
   that query Prometheus and promote or abort automatically. This is the production form of
   what you did by hand.
2. **Feature flags.** Add `FEATURE_X_ENABLED` to PayTrack API and toggle it via ConfigMap +
   `rollout restart`. Note that you changed behaviour **without deploying a new image** —
   deploy and release, separated.
3. **Session affinity.** Set `sessionAffinity: ClientIP` on the canary Service and re-run the
   sampling loop. Explain why the distribution changes and what that means for stateful apps.

---

## 🎯 Outcome

Blue-green cut-over and rollback via a Service selector; a canary with measured traffic
splitting and progressive promotion; proxy-level weighted routing; and a measured comparison of
five rollback methods.

**Next:** [Lab 17 — DevSecOps Pipeline](../lab-17-devsecops-pipeline/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Keep the browser on the projector** throughout Part 1. The banner flipping blue→green
  when you patch the Service is the image delegates take home.
- **The three things that go wrong:**
  1. The reconciler from Lab 15 is still running and reverts changes. Say "stop it" first.
  2. Insufficient CPU quota for 9+1 pods. The manifests request `25m` for this reason; if
     the quota still bites, use 5+1 and explain the arithmetic changes, not the concept.
  3. The 100-request sample gives 87/13 rather than 90/10 and someone thinks it is broken.
     Explain sampling variance — and that this coarseness is precisely why Part 3 exists.
- **Be explicit about the database limitation** in blue-green. Delegates leave believing
  blue-green solves rollback entirely unless you say plainly that data does not roll back.
- **Debrief question:** "Your last production incident — which of these five rollback methods
  did you use, how long did it take, and which one *could* you have used?"
</details>
