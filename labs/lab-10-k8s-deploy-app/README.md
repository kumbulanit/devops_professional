# Lab 10 — Deploy PayTrack API to Kubernetes

| | |
|---|---|
| **Day** | 4 |
| **Duration** | 35 minutes |
| **Module** | 4 — Kubernetes for DevOps |
| **You will produce** | `k8s/base/deployment.yaml` + `service.yaml` — the manifests every later lab builds on |
| **Feeds into** | Lab 11 (config & storage), Lab 12 (ingress & scaling), Lab 15 (CD), Lab 16 (strategies) |

---

## Objective

Deploy the image your CI built to Kubernetes; then **break it deliberately** — delete pods,
kill a node, push a bad image — and watch the platform recover. You will finish able to
explain, from observation, why a Deployment is not "a fancier `docker run`".

## Prerequisites

- Lab 09 (cluster running) and Lab 06 (image on GHCR)

🔁 **RECOVER**
```bash
k3d cluster start paytrack 2>/dev/null || k3d cluster create --config ~/devops-course/paytrack-api-team/k8s/k3d-cluster.yaml
kubectl config set-context --current --namespace=paytrack-dev
```

---

## Step 1 — Get the image into the cluster

```bash
cd ~/devops-course/paytrack-api-team
export GHCR_USER=$(git remote get-url origin | sed -E 's#.*[:/]([^/]+)/[^/]+(\.git)?$#\1#' | tr 'A-Z' 'a-z')
echo "Your GHCR namespace: ${GHCR_USER}"
export IMAGE="ghcr.io/${GHCR_USER}/paytrack-api"
export TAG="1.0.0"
```
**What this does:** extracts your GitHub username from the remote URL with a `sed` regular
expression, lowercases it (**GHCR paths must be lowercase** — a real and irritating gotcha),
and builds the image reference. `export` makes the variables available to the commands below.

**`TAG` is the version this lab deploys, written in exactly one place.** Every command from
here on — and the Deployment in Step 2 — refers to `${IMAGE}:${TAG}`, so the two routes below
cannot drift apart.

```bash
docker pull "${IMAGE}:latest" \
  && docker tag "${IMAGE}:latest" "${IMAGE}:${TAG}" \
  && k3d image import "${IMAGE}:${TAG}" -c paytrack
```
**What this does:** pulls the image your pipeline published, **re-tags the moving `:latest`
pointer to the fixed `1.0.0` you will actually deploy**, then **imports it directly into the
cluster's nodes**. `k3d image import` copies the image into each node container's containerd
store, so pods start without going out to the internet — much faster in a classroom, and it
works offline.

> **`:latest` is fine for *pulling* and never right for *deploying*.** Pulling it says "give
> me the newest build"; a manifest that references it says "run whatever happened to be
> pushed last", so two pods started an hour apart can run different code and `rollout undo`
> has nothing stable to return to. Course rule, Module 6 §6.5: **a deployment manifest never
> says `:latest`.** Here you pin to `1.0.0`; from Lab 15 the pipeline pins to the commit SHA,
> which is stronger still.

> **If the pull fails** (package still private, or CI has not run), build locally instead:
> ```bash
> cd app && docker build -t "paytrack-api:${TAG}" . && cd ..
> k3d image import "paytrack-api:${TAG}" -c paytrack
> export IMAGE=paytrack-api
> ```
> **What this does:** builds and imports your local image **under the same `${TAG}`**. Only
> `${IMAGE}` changes — everything below works unchanged, deploying `paytrack-api:1.0.0`
> instead of the GHCR copy.

✅ **Checkpoint — before you write any YAML**
```bash
echo "Will deploy: ${IMAGE}:${TAG}"
docker image inspect "${IMAGE}:${TAG}" >/dev/null 2>&1 && echo "✅ built/pulled" || echo "❌ not on this machine"
docker exec k3d-paytrack-server-0 crictl images | grep paytrack-api || echo "❌ not imported into the cluster"
```
**What this does:** confirms the image exists **on your machine**, then lists what the
cluster's own container runtime actually holds — `crictl` is containerd's CLI, running
*inside* the k3d node. **The `TAG` column must contain `1.0.0`.** A tag that is in one place
and not the other is the single most common cause of `ImagePullBackOff` in the next five
minutes.

---

## Step 2 — Write the Deployment

```bash
mkdir -p k8s/base
cat > k8s/base/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paytrack-api
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
    app.kubernetes.io/version: "${TAG}"
    app.kubernetes.io/component: api
    app.kubernetes.io/part-of: paytrack
spec:
  replicas: 3

  # The selector binds this Deployment to the pods it owns.
  # IT IS IMMUTABLE after creation - get it right the first time.
  selector:
    matchLabels:
      app.kubernetes.io/name: paytrack-api

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1            # allow 1 extra pod above replicas during a roll
      maxUnavailable: 0      # never drop below 3 available  → ZERO DOWNTIME

  revisionHistoryLimit: 5    # keep 5 old ReplicaSets so rollback has somewhere to go

  template:                  # ── the POD TEMPLATE: everything below describes a pod ──
    metadata:
      labels:
        app.kubernetes.io/name: paytrack-api      # MUST match spec.selector.matchLabels
        app.kubernetes.io/version: "${TAG}"       # same source as the image tag: they cannot drift
    spec:
      # Security: hardening from Lab 06, now expressed as Kubernetes policy.
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault

      # Spread replicas across nodes so one node failure cannot take out the service.
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: paytrack-api

      containers:
        - name: paytrack-api
          image: ${IMAGE}:${TAG}             # PINNED — never :latest (Module 6 §6.5)
          imagePullPolicy: IfNotPresent      # use the imported image; do not go to the registry

          ports:
            - name: http                     # a NAMED port - Services can refer to it by name
              containerPort: 8080
              protocol: TCP

          env:
            - name: APP_ENV
              value: "dev"
            - name: APP_COLOR
              value: "blue"
            - name: LOG_LEVEL
              value: "INFO"
            - name: READINESS_REQUIRES_DB
              value: "false"                 # no database yet - Lab 11 adds it
            # Downward API: inject facts about the pod itself.
            - name: POD_NAME
              valueFrom: { fieldRef: { fieldPath: metadata.name } }
            - name: NODE_NAME
              valueFrom: { fieldRef: { fieldPath: spec.nodeName } }

          # ── PROBES ── the three questions Kubernetes asks about your container
          startupProbe:                      # "has it finished booting?"
            httpGet: { path: /health, port: http }
            failureThreshold: 30
            periodSeconds: 2                 # allows up to 60s to start before any kill
          livenessProbe:                     # "is it wedged?" → RESTARTS the container
            httpGet: { path: /health, port: http }
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:                    # "can it serve?" → removes it from the Service
            httpGet: { path: /ready, port: http }
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2

          resources:
            requests: { cpu: 50m,  memory: 64Mi }    # what the SCHEDULER reserves
            limits:   { cpu: 300m, memory: 192Mi }   # ceiling: CPU throttles, memory OOM-kills

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }

          volumeMounts:
            - name: tmp
              mountPath: /tmp                # read-only root needs one writable path

      volumes:
        - name: tmp
          emptyDir: { sizeLimit: 64Mi }      # ephemeral, dies with the pod

      terminationGracePeriodSeconds: 30      # time to finish in-flight requests after SIGTERM
EOF
```

> ⚠️ Note this heredoc uses **`<<EOF`** (unquoted) so that `${IMAGE}` and `${TAG}` are
> substituted. Every other heredoc in this course uses `<<'EOF'` to prevent substitution. The
> difference matters — and it means **the shell that writes this file must be the one that ran
> Step 1.** If you come back in a new terminal, re-run the two `export` lines first, or you
> will write `image: :` into the manifest.

**The decisions worth understanding:**

| Field | Why it is there |
|---|---|
| `image: ${IMAGE}:${TAG}` | **A pinned tag.** Both routes in Step 1 produce `1.0.0`, so the manifest matches what was imported whichever one you took. Module 6 §6.5 and the Lab 19 platform check both reject `:latest` |
| `spec.selector` | **Immutable.** Binds the Deployment to its pods. Changing it later requires deleting and recreating the Deployment |
| `maxUnavailable: 0` | The line that buys zero downtime. It requires spare capacity **and an accurate readiness probe** |
| `revisionHistoryLimit: 5` | Old ReplicaSets are what `rollout undo` scales back up. Set to 0 and you cannot roll back |
| `topologySpreadConstraints` | Spreads pods across nodes. `ScheduleAnyway` = a preference, so a 2-node cluster still schedules 3 replicas |
| Named port `http` | Probes and Services reference the name; the number can change in one place |
| Downward API (`fieldRef`) | Injects the pod and node name — invaluable when you need to know *which* replica answered |
| **startupProbe** | Gives a slow start up to 60 s **without** weakening the liveness probe |
| **livenessProbe → `/health`** | Deliberately **does not** touch the database. A liveness probe that checks a dependency turns a DB blip into a cluster-wide restart storm |
| **readinessProbe → `/ready`** | *Does* check dependencies. Failing removes the pod from the Service, without restarting it |
| `requests` vs `limits` | Requests drive scheduling; limits cap usage. Requests set here also make the Lab 12 HPA possible |
| `readOnlyRootFilesystem` + `emptyDir` at `/tmp` | Immutable container, one writable scratch path |
| `terminationGracePeriodSeconds: 30` | SIGTERM, then up to 30 s to drain, then SIGKILL |

---

## Step 3 — Write the Service

```bash
cat > k8s/base/service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: paytrack-api
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
spec:
  type: ClusterIP              # internal virtual IP. The default, and usually correct.
  selector:
    app.kubernetes.io/name: paytrack-api   # which PODS receive traffic
  ports:
    - name: http
      port: 80                 # the port the SERVICE listens on
      targetPort: http         # the NAMED port on the pod (8080)
      protocol: TCP
EOF
```
**What this does:** creates a stable virtual IP and DNS name in front of a changing set of
pods.

> 🔑 **The Service's `selector` is matched against pod labels — it has no relationship to the
> Deployment.** A Service will happily select pods from several Deployments (which is exactly
> how blue-green works in Lab 16), or from none at all (which is the classic "my service
> returns nothing" bug).

---

## Step 4 — Deploy

```bash
kubectl apply -f k8s/base/ --dry-run=server
```
**What this does:** sends the manifests to the API server for **full validation** —
authentication, authorisation, admission controllers, schema — **without persisting
anything**. `--dry-run=client` only checks local syntax; `server` is the one that catches
quota violations and admission-policy rejections. Put this in your pipeline.

```bash
kubectl apply -f k8s/base/
```
**What this does:** creates the Deployment and Service. It returns **immediately** — as
Module 4 §4.2 explains, `apply` only records intent. The controllers do the work.

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** **blocks until the rollout completes**, then exits 0 — or exits non-zero
on timeout. This is the correct way for a pipeline to verify a deployment; `sleep 30` is not.

```bash
kubectl get all -l app.kubernetes.io/name=paytrack-api
```
**What this does:** shows the whole object graph created from two files:

```
pod/paytrack-api-7d4f8b9c6-xxxxx     ← 3 of these
service/paytrack-api                  ← ClusterIP
deployment.apps/paytrack-api          ← what you wrote
replicaset.apps/paytrack-api-7d4f8b9c6  ← what the Deployment created
```

**You wrote a Deployment. Kubernetes created a ReplicaSet, which created three Pods, and
placed them on nodes.** That chain is the reconciliation loop.

```bash
kubectl get pods -o wide
```
**What this does:** shows which node each replica landed on — the topology spread constraint
at work.

---

## Step 5 — Verify it works

```bash
kubectl port-forward service/paytrack-api 8888:80 &
sleep 3
curl -s localhost:8888/health | jq
curl -s localhost:8888/api/v1/info | jq
```
**What this does:** `port-forward` tunnels a local port through the API server to the
Service. `&` backgrounds it. **This is a debugging tool only** — it goes through your
kubeconfig credentials and dies with your shell.

```bash
for i in $(seq 1 8); do curl -s localhost:8888/api/v1/info | jq -r '.host'; done
```
**What this does:** eight requests. `HOSTNAME` inside a pod is the pod name, so **you see the
Service load-balancing across all three replicas**. This is `kube-proxy`'s iptables rules
doing DNAT (Module 4 §4.5).

```bash
kubectl get endpointslices -l kubernetes.io/service-name=paytrack-api -o jsonpath='{.items[0].endpoints[*].addresses[*]}{"\n"}'
```
**What this does:** prints the pod IPs the Service currently routes to. **Only Ready pods
appear here** — this is the single most useful command when a Service returns nothing.

```bash
kill %1 2>/dev/null
```

**Now test from inside the cluster, which is how services actually talk:**
```bash
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl:8.10.1 -- \
  sh -c 'curl -s http://paytrack-api/api/v1/info; echo; curl -s http://paytrack-api.paytrack-dev.svc.cluster.local/health'
```
**What this does:** runs a temporary pod (`--rm` deletes it on exit, `-it` attaches your
terminal) and calls the Service by **short name** and by **fully-qualified name**. Both work:
same-namespace short names resolve thanks to the search domains CoreDNS puts in every pod's
`/etc/resolv.conf`. This is the direct successor to Compose's service-name DNS.

---

## Step 6 — Break it three ways

### 6.1 — Delete a pod

```bash
kubectl get pods
kubectl delete pod $(kubectl get pods -l app.kubernetes.io/name=paytrack-api -o jsonpath='{.items[0].metadata.name}')
kubectl get pods -w &
sleep 15 && kill %1 2>/dev/null
```
**What this does:** deletes one pod and watches. **A replacement appears within seconds.**
The ReplicaSet controller observed 2 pods where 3 were desired and corrected it — you did
nothing. Note the new pod has a *different* name: pods are cattle.

### 6.2 — Kill a node

```bash
kubectl get pods -o wide
docker stop k3d-paytrack-agent-0
sleep 20 && kubectl get nodes && kubectl get pods -o wide
docker start k3d-paytrack-agent-0
```
**What this does:** stops a worker. The node goes `NotReady`; pods on it are marked for
eviction (Kubernetes waits ~5 minutes by default before evicting, to ride out transient
network problems). **Meanwhile the Service keeps serving from the surviving replicas**,
because the readiness-driven EndpointSlice dropped the unreachable pods.

### 6.3 — Deploy a broken image

```bash
kubectl set image deployment/paytrack-api paytrack-api=ghcr.io/nonexistent/does-not-exist:v9
kubectl rollout status deployment/paytrack-api --timeout=45s || echo "❌ rollout did not complete"
kubectl get pods
```
**What this does:** points the Deployment at an image that does not exist.

✅ **The important observation:** you will see a new pod in `ImagePullBackOff` — **and three
old pods still `Running` and still serving traffic.** Because `maxUnavailable: 0`, Kubernetes
refuses to remove a healthy pod until a new one becomes Ready. **The bad deploy could not
take the service down.**

```bash
kubectl describe pod -l app.kubernetes.io/name=paytrack-api | grep -A5 "Events:" | tail -12
```
**What this does:** the Events section explains the failure in plain English
(`Failed to pull image … not found`). **Always `describe` first.**

```bash
kubectl rollout undo deployment/paytrack-api
kubectl rollout status deployment/paytrack-api --timeout=90s
kubectl get pods
```
**What this does:** rolls back. It is nearly instant because the previous ReplicaSet still
exists with `desired 0` — undo simply scales it back to 3.

```bash
kubectl rollout history deployment/paytrack-api
```
**What this does:** lists revisions. Add `--revision=2` to see a specific one's pod template.

---

## Step 7 — Scale, and see the quota bite

```bash
kubectl scale deployment/paytrack-api --replicas=6
kubectl get pods -o wide
kubectl describe quota -n paytrack-dev
```
**What this does:** scales to six and shows quota consumption. With `requests.cpu: 50m` per
pod against a 2-CPU namespace quota, there is room — but watch `Used` climb.

```bash
kubectl scale deployment/paytrack-api --replicas=40
sleep 5 && kubectl get deployment paytrack-api
kubectl get events --sort-by=.lastTimestamp | grep -i 'quota\|failed' | tail -5
```
**What this does:** deliberately exceeds the ResourceQuota from Lab 09. The Deployment reports
fewer ready replicas than desired, and the events show `exceeded quota`. **This is the quota
protecting the cluster from you** — exactly its purpose in a shared environment.

```bash
kubectl scale deployment/paytrack-api --replicas=3
kubectl rollout status deployment/paytrack-api
```

---

## Step 8 — Add a PodDisruptionBudget

```bash
cat > k8s/base/pdb.yaml <<'EOF'
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: paytrack-api
  namespace: paytrack-dev
spec:
  minAvailable: 2          # never allow VOLUNTARY disruption below 2 pods
  selector:
    matchLabels:
      app.kubernetes.io/name: paytrack-api
EOF
kubectl apply -f k8s/base/pdb.yaml
kubectl get pdb
```
**What this does:** a PDB constrains **voluntary** disruptions — node drains, cluster
upgrades, autoscaler scale-down. Without one, `kubectl drain` on a node during a cluster
upgrade can legitimately remove every replica of your service at once.

```bash
kubectl drain k3d-paytrack-agent-0 --ignore-daemonsets --delete-emptydir-data --timeout=60s
kubectl get pods -o wide
kubectl uncordon k3d-paytrack-agent-0
```
**What this does:** `drain` cordons the node (marks it unschedulable) and evicts its pods —
**respecting the PDB**, so it will block rather than breach `minAvailable: 2`.
`uncordon` makes the node schedulable again. This is the exact procedure for a real node
maintenance window.

---

## Step 9 — Commit

```bash
git add k8s/base/
git commit -m "feat(k8s): deploy PayTrack API with probes, limits and a PDB

3 replicas, rolling update with maxUnavailable=0 for zero downtime.

- startup/liveness/readiness probes; liveness deliberately has NO external
  dependency so a DB blip cannot cause a restart storm
- non-root (uid 10001), read-only rootfs, all capabilities dropped
- requests/limits set (also the prerequisite for the HPA in Lab 12)
- image pinned to 1.0.0, never :latest
- topology spread across nodes; PodDisruptionBudget minAvailable=2"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
kubectl get deployment,replicaset,pod,service,pdb -l app.kubernetes.io/name=paytrack-api
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.nodeName}{"\t"}{.status.phase}{"\n"}{end}'
```
3 pods Running, spread across nodes, 1 Service, 1 PDB.

---

## ⭐ Advanced — optional, in this folder

The application runs and survives a pod being deleted. The advanced page is about the other
day — the one where it does not run — and it sits beside this one. Nothing later depends on it.

| In this folder | What it is | Time | Needs |
|---|---|---|---|
| **[README-10A — Debugging and Rollouts](README-10A-debugging-and-rollouts.md)** | Produce the six failures Kubernetes actually serves up — Pending, quota refusal, ImagePullBackOff, CrashLoopBackOff, OOMKilled, and Running-but-not-Ready — and diagnose each from the cluster's own output; get a shell into an image that has none with `kubectl debug`; cause a liveness restart storm; then pause, undo and read a rollout | 70 min, ten parts | The Lab 09 cluster and this lab's deployment |
| **`Lab10A_Advanced_Debugging.pptx`** | The 10 slides behind it: get/describe/logs/events, what each pod state means, ephemeral containers, rollout history | Read it first | PowerPoint |

---

## 🧩 Stretch (homework)

1. **`kubectl explain`.** Run `kubectl explain deployment.spec.strategy.rollingUpdate` —
   the API's own documentation, always correct for your cluster version. Better than a web
   search.
2. **`Recreate` strategy.** Switch to it, roll out, and watch downtime appear. Then explain
   when you would deliberately choose it.
3. **Break the liveness probe** (point it at `/nonexistent`) and watch `CrashLoopBackOff`
   with an increasing back-off. `kubectl logs --previous` reads the dead container's logs.
4. **Delete the ReplicaSet directly** and predict what happens before you look.

---

## Troubleshooting

| Symptom | First command | Usual cause |
|---|---|---|
| `ImagePullBackOff` | `kubectl describe pod <p>` | Wrong name/tag, or a private registry with no `imagePullSecret`. Compare the tag in the pod spec with what Step 1 imported — they must match exactly |
| `image: :` in the manifest | `grep image: k8s/base/deployment.yaml` | `${IMAGE}`/`${TAG}` were unset: a new terminal that skipped Step 1's `export` lines |
| `CrashLoopBackOff` | `kubectl logs <p> --previous` | App exits on start — bad config or missing env var |
| `Pending` | `kubectl describe pod <p>` | Insufficient resources, quota, or an unbound PVC |
| Running but `0/1 READY` | `kubectl describe pod <p>` | Readiness probe failing |
| Service returns nothing | `kubectl get endpointslices` | No Ready pods, or a label/selector mismatch |
| `field is immutable` | — | You changed `spec.selector`. Delete and recreate the Deployment |

---

## 🎯 Outcome

PayTrack API running on Kubernetes with three replicas, correct probes, security context,
resource limits, a PodDisruptionBudget and a Service — and you have watched it survive pod
deletion, node failure and a bad deployment.

**Next:** [Lab 11 — ConfigMaps, Secrets and Persistent Storage](../lab-11-k8s-config-secrets-storage/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Step 6.3 is the lab's centrepiece.** A bad image is deployed and the service stays up.
  Ask the room what happens in their environment when someone deploys a broken artefact.
- **The three things that go wrong:**
  1. GHCR path case. GitHub usernames may be mixed case; GHCR paths must be lowercase. The
     `tr 'A-Z' 'a-z'` in Step 1 handles it — mention it, because they will hit it manually.
  2. Image not imported, or imported under a different tag than the manifest asks for →
     `ImagePullBackOff` everywhere. Check `k3d image import` ran, and that it imported
     `${IMAGE}:${TAG}`. The Step 1 checkpoint exists to catch exactly this.
  3. Someone edits `spec.selector` and gets `field is immutable`. Excellent teaching moment
     about why labels and selectors are a contract.
- **Why the extra `docker tag`.** The registry's `:latest` is a moving pointer; the manifest
  must name something fixed. Re-tagging it to `1.0.0` locally is the classroom stand-in for
  what Lab 15's pipeline does properly — deploy the immutable commit-SHA tag. If someone asks
  "why not just deploy `:latest`?", that is the answer, and Lab 19's platform check enforces it.
- **Slow down on liveness vs readiness.** Ask: "your liveness probe checks the database, and
  the database has a 30-second blip. What happens to your 40 pods?" Let them work it out.
- **Debrief question:** "Your service currently runs on VMs. Which of the three failures you
  just caused would have paged a human, and how long would recovery have taken?"
</details>
