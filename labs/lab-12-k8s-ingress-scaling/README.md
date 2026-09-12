# Lab 12 — Ingress Routing and Autoscaling

| | |
|---|---|
| **Day** | 4 |
| **Duration** | 17 minutes |
| **Module** | 4 — Kubernetes for DevOps |
| **You will produce** | `k8s/base/ingress.yaml` + `hpa.yaml` — the app reachable on a hostname and scaling under load |
| **Feeds into** | Lab 16 (canary weighting uses this Ingress), Lab 18 (Grafana gets its own Ingress) |

---

## Objective

Expose PayTrack API on a real hostname through the Traefik Ingress controller, then generate
load and **watch Kubernetes scale it out and back in without you**.

## Prerequisites

- Lab 11 complete: API talking to Postgres in `paytrack-dev`

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev
kubectl apply -f k8s/base/ && kubectl rollout status deployment/paytrack-api
```

---

## Step 1 — Confirm an Ingress controller exists

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik
kubectl get ingressclass
kubectl get svc -n kube-system traefik
```
**What this does:** confirms the three things an Ingress needs.

> 🔑 **An Ingress object on its own does absolutely nothing.** It is a set of routing *rules*.
> An **Ingress Controller** — here Traefik, a real pod — watches for those objects and
> implements the routing. This is the most common day-one Kubernetes confusion: "I applied
> the Ingress and nothing happened."

The `traefik` Service holds host ports 8080 → 80 and 8443 → 443, mapped by the k3d config
from Lab 09.

---

## Step 2 — Local DNS for the test hostnames

```bash
grep -q 'paytrack.localhost' /etc/hosts || \
  echo "127.0.0.1  paytrack.localhost api.paytrack.localhost grafana.localhost" | sudo tee -a /etc/hosts
getent hosts paytrack.localhost
```
**What this does:** maps the hostnames to loopback so your browser and `curl` send the right
`Host:` header. **The header is what Ingress routes on** — without it Traefik cannot tell
which rule applies. `grep -q … ||` makes the command idempotent.

---

## Step 3 — Write the Ingress

```bash
cat > k8s/base/ingress.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paytrack-api
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  ingressClassName: traefik        # WHICH controller should handle this object
  rules:
    - host: paytrack.localhost
      http:
        paths:
          # Most specific path FIRST - matching is longest-prefix, but be explicit anyway.
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: paytrack-api
                port: { number: 80 }
          - path: /metrics
            pathType: Exact         # exact match only; /metrics/foo will NOT match
            backend:
              service:
                name: paytrack-api
                port: { number: 80 }
          - path: /
            pathType: Prefix
            backend:
              service:
                name: paytrack-api
                port: { number: 80 }
EOF
kubectl apply -f k8s/base/ingress.yaml
kubectl get ingress
```
**What the fields mean:**

| Field | Meaning |
|---|---|
| `ingressClassName: traefik` | Selects the controller. On a cluster with both NGINX and Traefik, this decides which one routes you |
| `host` | Routes on the HTTP `Host:` header. Omit it and the rule matches every hostname |
| `pathType: Prefix` | `/api` matches `/api`, `/api/v1/authorisations`, … |
| `pathType: Exact` | `/metrics` matches only `/metrics` |
| `backend.service.port.number: 80` | **The Service port (80), not the container port (8080).** A very common mistake |
| `annotations` | Controller-specific configuration. Ingress is deliberately minimal; anything beyond host/path/TLS lives here |

✅ **Checkpoint**
```bash
curl -s http://paytrack.localhost:8080/health | jq
curl -s http://paytrack.localhost:8080/api/v1/info | jq
curl -s -o /dev/null -w "root path: %{http_code}\n" http://paytrack.localhost:8080/
```
Open **http://paytrack.localhost:8080/** in a browser — the blue PayTrack API banner. Traffic now
goes: browser → host:8080 → k3d LB → Traefik → Service → a Ready pod.

```bash
curl -s -o /dev/null -w "wrong host: %{http_code}\n" -H 'Host: unknown.localhost' http://127.0.0.1:8080/
```
**What this does:** sends a different `Host` header. **404** — no rule matches. That proves
routing is host-based, not port-based.

---

## Step 4 — Verify metrics-server, the HPA's prerequisite

```bash
kubectl top nodes
kubectl top pods
```
**What this does:** queries the metrics API. If this errors, the HPA cannot work — it reads
from the same place.

> ⚠️ If you see `error: Metrics API not available`, wait 60 seconds after cluster start and
> retry. It is the number-one cause of "my HPA says `<unknown>`".

---

## Step 5 — Create the HorizontalPodAutoscaler

```bash
cat > k8s/base/hpa.yaml <<'EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: paytrack-api
  namespace: paytrack-dev
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: paytrack-api

  minReplicas: 2          # >= 2 for anything that must stay available
  maxReplicas: 10

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50     # 50% OF THE REQUEST (50m), i.e. 25m per pod
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0        # scale up immediately - latency hurts users now
      policies:
        - type: Percent
          value: 100                        # may double the replica count …
          periodSeconds: 15                 # … at most every 15s
        - type: Pods
          value: 4                          # or add 4 pods
          periodSeconds: 15
      selectPolicy: Max                     # whichever allows the bigger increase
    scaleDown:
      stabilizationWindowSeconds: 120       # wait 2 min of calm before shrinking
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
EOF
kubectl apply -f k8s/base/hpa.yaml
kubectl get hpa
```
**Why the asymmetry in `behavior` matters:** scaling **up** late means users wait; scaling
**down** early means you thrash (scale in, load returns, scale out again). So: react
instantly on the way up, and require two minutes of sustained calm on the way down. This is
one of the most practically useful settings in the whole HPA API and it is routinely left at
defaults.

> 🔑 **`averageUtilization: 50` is 50 % of the pod's CPU *request*, not of a core.** Your
> request is `50m`, so the target is **25m per pod**. **A pod with no CPU request cannot be
> autoscaled on CPU utilisation at all** — which is why Lab 10 set requests, and why the
> LimitRange from Lab 09 supplies defaults.

```bash
kubectl get hpa paytrack-api -w &
sleep 45 && kill %1 2>/dev/null
```
**What this does:** watches until TARGETS shows real numbers (e.g. `1%/50%, 2%/80%`) instead
of `<unknown>`. It takes 15–60 seconds for the first metrics window.

---

## Step 6 — Generate load and watch it scale

Open a **second terminal** for the watcher:

```bash
watch -n 2 'kubectl get hpa,deployment,pods -l app.kubernetes.io/name=paytrack-api --no-headers'
```
**What this does:** `watch -n 2` re-runs the command every 2 seconds — a live dashboard of
replica count and pod states.

In the **first terminal**, generate load:

```bash
kubectl run load-generator --rm -it --restart=Never \
  --image=busybox:1.36 \
  --overrides='{"spec":{"containers":[{"name":"load-generator","image":"busybox:1.36","resources":{"requests":{"cpu":"50m","memory":"32Mi"}},"command":["/bin/sh","-c","while true; do wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/api/v1/authorisations >/dev/null; wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/metrics >/dev/null; done"]}]}}'
```
**What this does:** runs a pod that hammers the Service in a tight loop, **from inside the
cluster** so traffic goes through the real Service path. `--rm -it` keeps it in the
foreground so `Ctrl+C` stops it. `/metrics` is included because rendering it is deliberately
the most CPU-hungry endpoint.

**Watch the second terminal.** Over roughly 60–120 seconds:

```
 t=0s    hpa  cpu: 2%/50%    deployment 3/3     ← idle
 t=30s   hpa  cpu: 71%/50%   deployment 3/3     ← load detected, above target
 t=45s   hpa  cpu: 71%/50%   deployment 6/3     ← SCALING UP (doubling policy)
 t=75s   hpa  cpu: 44%/50%   deployment 6/6     ← new pods Ready, utilisation falling
 t=120s  hpa  cpu: 38%/50%   deployment 6/6     ← stabilised
```

```bash
kubectl describe hpa paytrack-api | tail -15
```
**What this does:** the Events section narrates every decision:
`New size: 6; reason: cpu resource utilization above target`. **This is where you debug an
HPA that is not behaving.**

Stop the load with `Ctrl+C`, then watch the scale-down:

```bash
kubectl get hpa,deployment -l app.kubernetes.io/name=paytrack-api -w &
sleep 180 && kill %1 2>/dev/null
```
**What this does:** after the 120-second stabilisation window, replicas fall back — by at
most 50 % per minute — until `minReplicas: 2`. **The slow, deliberate scale-down is the
`behavior` block working.**

---

## Step 7 — Zero-downtime under load (optional, 3 min)

```bash
kubectl run load2 --restart=Never --image=busybox:1.36 \
  --overrides='{"spec":{"containers":[{"name":"load2","image":"busybox:1.36","resources":{"requests":{"cpu":"20m","memory":"32Mi"}},"command":["/bin/sh","-c","i=0; f=0; while [ $i -lt 400 ]; do wget -q -T2 -O- http://paytrack-api.paytrack-dev.svc.cluster.local/health >/dev/null 2>&1 || f=$((f+1)); i=$((i+1)); sleep 0.25; done; echo TOTAL=$i FAILURES=$f"]}]}}'
sleep 5
kubectl set env deployment/paytrack-api APP_VERSION=1.1.0
kubectl rollout status deployment/paytrack-api --timeout=120s
sleep 45
kubectl logs load2
kubectl delete pod load2 --now
```
**What this does:** fires 400 requests over ~100 seconds while you roll out a new version
underneath. **Expect `FAILURES=0`.**

Zero downtime comes from three things working together, and it is worth naming all three:
`maxUnavailable: 0` (never drop below the desired count), the **readiness probe** (traffic
only reaches Ready pods), and `terminationGracePeriodSeconds: 30` (in-flight requests finish
before SIGKILL).

---

## Step 8 — Commit

```bash
git add k8s/base/ingress.yaml k8s/base/hpa.yaml
git commit -m "feat(k8s): add Traefik Ingress and HPA

Ingress routes paytrack.localhost to the Service (path rules for /api, /metrics, /).

HPA scales 2-10 replicas on 50% CPU / 80% memory utilisation of the pod
REQUEST. behavior is deliberately asymmetric: immediate scale-up (users are
waiting) and a 120s stabilisation window on scale-down (avoids thrashing)."
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
curl -s http://paytrack.localhost:8080/api/v1/info | jq -r '.app + " " + .version'
kubectl get ingress,hpa
kubectl get hpa paytrack-api -o jsonpath='{.status.currentReplicas}/{.spec.maxReplicas}{"\n"}'
```

---

## 🧩 Stretch (homework)

1. **TLS.** Generate a self-signed certificate, create a `kubernetes.io/tls` Secret, and add
   a `tls:` block to the Ingress. Then look up `cert-manager`, which automates Let's Encrypt.
2. **Path rewriting.** Add a Traefik `Middleware` with `stripPrefix` so `/api/v2/*` reaches
   the backend as `/v2/*`.
3. **Custom metrics.** Read about the Prometheus Adapter, which lets an HPA scale on
   `paytrack_http_requests_total` — requests per second is a far better scaling signal than CPU
   for an I/O-bound service.
4. **Gateway API.** Compare `HTTPRoute` with Ingress and note what it fixes.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Ingress returns 404 | Wrong `Host` header, or no matching rule | `curl -H 'Host: paytrack.localhost'`; check `/etc/hosts` |
| 503 Service Unavailable | No Ready pods behind the Service | `kubectl get endpointslices` |
| HPA shows `<unknown>` | metrics-server not ready, **or no CPU request on the pod** | `kubectl top pods`; check `resources.requests` |
| HPA never scales up | Target already met, or `maxReplicas` reached | `kubectl describe hpa` and read Events |
| Scales up then straight back down | No stabilisation window | Set `behavior.scaleDown.stabilizationWindowSeconds` |
| `connection refused` on :8080 | k3d port mapping missing | Recreate the cluster from `k8s/k3d-cluster.yaml` |

---

## 🎯 Outcome

PayTrack API reachable on `http://paytrack.localhost:8080` through Traefik, autoscaling between 2
and 10 replicas on CPU and memory with tuned scale-up/scale-down behaviour, and demonstrated
zero-downtime deployment under live load.

**Next:** [Lab 13 — Infrastructure as Code with Terraform](../lab-13-terraform-iac/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Only 17 minutes.** Have `/etc/hosts` and the Ingress applied from the front while
  delegates catch up, then give them the full time on Step 6.
- **The three things that go wrong:**
  1. `<unknown>` in the HPA. Ninety percent of the time it is metrics-server still starting;
     the rest of the time it is a missing CPU request. Show both diagnoses.
  2. `backend.service.port.number: 8080` instead of `80`. Ingress points at the **Service**
     port. Extremely common.
  3. Load generator is too gentle and nothing scales. The `/metrics` call in the loop is
     there to make it bite — do not let anyone remove it.
- **Two terminals side by side on the projector** for Step 6: load on the left, `watch` on
  the right. Seeing replicas climb live is the memorable moment of day 4.
- **Debrief question:** "Your traffic triples at 09:00 every weekday. What happens today, and
  what would this HPA have done? Now: what does it cost you to be permanently provisioned for
  peak?"
</details>
