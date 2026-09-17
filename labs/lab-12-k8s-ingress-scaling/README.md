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
from Lab 09. Its `EXTERNAL-IP` column should list your node addresses — that is k3s's ServiceLB
at work. **`<pending>` means ServiceLB was disabled** and nothing will answer on
`paytrack.localhost:8080`; the fix is in Lab 09's troubleshooting table.

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
    # CPU ONLY - and that is a deliberate decision, not an omission. See below.
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50     # 50% OF THE REQUEST (50m), i.e. 25m per pod

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

### Why there is no memory metric — the most useful five minutes of this lab

Adding `memory` alongside `cpu` looks like free extra safety. It is the opposite. Prove it
to yourself before you move on:

```bash
kubectl top pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** shows actual usage per pod. **Look at the memory column with no load
running at all** — roughly **65–85Mi against a `64Mi` request**, i.e. **100 %+ utilisation
while the service is completely idle.**

Now do the arithmetic an HPA would do with `memory: averageUtilization: 80`:

```
desired = ceil( 3 pods × 103% ÷ 80% ) = ceil(3.9) = 4      ← at IDLE
… then 5, 7, 9, 10 as each new pod reports the same 103 %
```

**An HPA takes the highest recommendation across all its metrics.** So a memory metric that
is above target at idle pins the Deployment at `maxReplicas` permanently, and the CPU metric
never gets a say. Three separate things then break:

| Consequence | Why |
|---|---|
| The scaling demo becomes meaningless | You are already at 10 replicas before any load arrives |
| It never scales back down | Python does not return freed heap to the OS. Memory does not fall when load falls, so the metric stays above target forever |
| The namespace quota is exhausted | 10 × `limits.cpu: 300m` = 3000m of the 4000m in Lab 09's quota. **Lab 16 then cannot start blue and green**, and fails with `exceeded quota` |

> 🔑 **Memory is a poor autoscaling signal for almost every web application.** A good signal
> *rises when demand rises and falls when demand falls*. CPU does that. Requests-per-second
> does it better. A Python process's RSS is mostly interpreter, imported modules and cached
> allocations — it is nearly independent of load on the way up, and on the way down it is
> a **ratchet**. Scale on memory and you buy a cluster that only ever grows.
>
> Memory belongs in `requests` and `limits`, where it does its real job: scheduling and
> OOM protection. Not in an HPA.

> ⚠️ **The same numbers tell you something else:** a pod steady at ~70Mi against a `64Mi`
> request is under-requesting. `requests` is what the **scheduler reserves**, so the node is
> quietly over-committed. It causes no failure here (the `192Mi` limit is far away), but in
> production you set requests from measured steady-state usage — exactly what `kubectl top`
> just gave you.

```bash
kubectl get hpa paytrack-api -w &
sleep 45 && kill %1 2>/dev/null
```
**What this does:** watches until TARGETS shows a real number (e.g. `cpu: 18%/50%`) instead
of `<unknown>`. It takes 15–60 seconds for the first metrics window.

> ✅ **The number to sanity-check before Step 6:** idle CPU should read **well under 50 %**
> (typically 15–30 %). If it is already at or above target with no load running, the demo in
> the next step cannot work — check that nothing else is hitting the Service.

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

**Watch the second terminal.** Over roughly 60 seconds — these are real numbers from a
three-node k3d cluster, yours will differ in detail but not in shape:

```
 t=0s    hpa  cpu:  18%/50%   deployment 3/3     ← idle, comfortably under target
 t=20s   hpa  cpu:  92%/50%   deployment 3/5     ← load detected, SCALING UP
 t=40s   hpa  cpu: 169%/50%   deployment 5/8     ← still above target, scaling again
 t=60s   hpa  cpu: 235%/50%   deployment 8/10    ← maxReplicas reached
```

**Notice the utilisation keeps climbing even as pods are added.** The load generator is an
unthrottled loop: it simply consumes whatever capacity you give it, so it can always outrun
the HPA. Real traffic has a ceiling; a `while true` loop does not. That is why you hit
`maxReplicas` here and why `maxReplicas` exists.

```bash
kubectl describe hpa paytrack-api | tail -15
```
**What this does:** the Events section narrates every decision:
`New size: 8; reason: cpu resource utilization (percentage of request) above target`. **This
is where you debug an HPA that is not behaving** — the `reason` names the metric that won.

Stop the load with `Ctrl+C`, then watch the scale-down:

```bash
kubectl get hpa,deployment -l app.kubernetes.io/name=paytrack-api -w &
sleep 240 && kill %1 2>/dev/null
```
**What this does:** after the 120-second stabilisation window, replicas fall back — by at
most 50 % per minute — towards `minReplicas: 2`. **The slow, deliberate scale-down is the
`behavior` block working.**

> ⏱ **Do not expect to see it reach 2 before the lab ends.** Measured across two runs on a
> real cluster: CPU drops below target within ~45 s, the **first** reduction lands at about
> 3 minutes, and reaching `minReplicas: 2` takes **the better part of 10 minutes**. The exact
> ladder down varies with how the metric samples fall — one run stepped
> `10 → 8 → 7 → 6 → 4 → 3 → 2`, another went `10 → 5 → … → 2` — because the policy caps each
> step at 50 % per minute rather than prescribing one. That asymmetry — seconds to scale up,
> minutes to scale down — **is the design, not slowness.** Move on to Step 7 and check
> `kubectl get hpa` again at the end of the lab.

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

HPA scales 2-10 replicas on 50% CPU utilisation of the pod REQUEST.

CPU only, on purpose: the pod idles at ~100% of its memory request, so a
memory metric would pin the Deployment at maxReplicas with no load at all,
and would never scale back down because Python does not return freed heap
to the OS. behavior is deliberately asymmetric: immediate scale-up (users
are waiting) and a 120s stabilisation window on scale-down (avoids
thrashing)."
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
curl -s http://paytrack.localhost:8080/api/v1/info | jq -r '.app + " " + .version'
kubectl get ingress,hpa
kubectl get hpa paytrack-api -o jsonpath='{.status.currentReplicas}/{.spec.maxReplicas}{"\n"}'
```
**What to expect:** the Ingress listed with an address, and the HPA showing a **single**
`cpu:` target well under 50 %. The replica count will be somewhere between **2 and 10**
depending on how long ago you stopped the load — it is still walking down. Anything pinned
at `10/10` with the cluster idle means a metric is above target; re-read Step 5.

> 🔑 **Leave the HPA in place.** Lab 16 deliberately scales this Deployment to `0`, and an
> HPA does not act on a target that is scaled to zero — you will see that behaviour there.

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
| **HPA sits at `maxReplicas` with no load** | A metric that is above target at idle — almost always `memory`. The HPA takes the **highest** recommendation across metrics | `kubectl describe hpa` and read the `reason` on the rescale events; remove the offending metric |
| Lab 16 fails with `exceeded quota` | The HPA parked this Deployment at 10 replicas, consuming Lab 09's `limits.cpu` quota | `kubectl get hpa`; let it scale down, or `kubectl scale deployment/paytrack-api --replicas=0` as Lab 16 Step 2.2 does |
| Scales up then straight back down | No stabilisation window | Set `behavior.scaleDown.stabilizationWindowSeconds` |
| `connection refused` on :8080 | k3d port mapping missing | Recreate the cluster from `k8s/k3d-cluster.yaml` |

---

## 🎯 Outcome

PayTrack API reachable on `http://paytrack.localhost:8080` through Traefik, autoscaling between 2
and 10 replicas **on CPU** with tuned scale-up/scale-down behaviour, a reasoned argument for
why memory is *not* a scaling metric, and demonstrated zero-downtime deployment under live
load.

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
- **If a delegate adds a memory metric "for safety", let them, then show them the result.**
  The pod idles at ~100 % of its `64Mi` request, so the HPA jumps straight to 10 replicas
  with no load at all and never comes back down. It is a two-minute demonstration and it is
  the single most transferable idea in this lab: **an autoscaling signal must fall when
  demand falls.** It also breaks Lab 16 by eating the namespace CPU quota, so fix it before
  day 5.
- **Two terminals side by side on the projector** for Step 6: load on the left, `watch` on
  the right. Seeing replicas climb live is the memorable moment of day 4.
- **Debrief question:** "Your traffic triples at 09:00 every weekday. What happens today, and
  what would this HPA have done? Now: what does it cost you to be permanently provisioned for
  peak?"
</details>
