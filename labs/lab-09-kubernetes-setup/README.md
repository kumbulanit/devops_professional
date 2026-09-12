# Lab 09 — Stand Up a Real Kubernetes Cluster

| | |
|---|---|
| **Day** | 4 |
| **Duration** | 20 minutes |
| **Module** | 4 — Kubernetes for DevOps |
| **You will produce** | A 3-node k3d cluster with an Ingress controller and a registry, and `k8s/namespaces.yaml` |
| **Feeds into** | Labs 10–19 — every remaining lab runs on this cluster |

---

## Objective

Create a genuine multi-node Kubernetes cluster on your laptop, inspect the control plane and
node components you learned about in the lecture, and set up the namespaces the rest of the
week uses.

**k3d** runs **k3s** (Rancher's CNCF-certified lightweight Kubernetes) inside Docker
containers. Each "node" is a container. It is a real cluster with a real API server,
scheduler, controller manager and kubelets — it starts in about 30 seconds and it is free.

| Alternative | Note |
|---|---|
| **k3d** (used here) | Fastest, true multi-node, trivial registry and port mapping |
| kind | Also excellent; upstream Kubernetes rather than k3s |
| minikube | Single-node by default; heavier |
| Docker Desktop | Single-node; convenient if you already run it |

## Prerequisites

- Lab 00 (Docker, kubectl, k3d, helm) — re-run `~/devops-course/toolcheck.sh`
- **At least 4 GB RAM free.** Stop the Lab 07 stack first:
  ```bash
  cd ~/devops-course/paytrack-api-team && docker compose down
  ```

---

## Step 1 — Raise the kernel limits k3s needs

```bash
cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes.conf
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=512
EOF
sudo sysctl --system | grep -E 'inotify' || true
```
**What this does:** Kubernetes components watch a very large number of files. Ubuntu's
defaults (128 instances) are too low, and the symptom is horrible: pods stuck in
`ContainerCreating`, or `too many open files` deep in a kubelet log twenty minutes later.
`sysctl --system` reloads all configuration files immediately, so no reboot is needed.

---

## Step 2 — Create the cluster

```bash
cd ~/devops-course/paytrack-api-team
mkdir -p k8s
cat > k8s/k3d-cluster.yaml <<'EOF'
# k3d cluster definition — cluster creation as code, not a long command line.
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: paytrack

servers: 1          # control-plane node (API server, scheduler, controller manager, etcd)
agents: 2           # worker nodes — enough to SEE scheduling and rescheduling happen

image: rancher/k3s:v1.31.2-k3s1     # pinned: never build a cluster on a floating tag

ports:
  - port: 8080:80                    # host 8080 → Traefik ingress HTTP
    nodeFilters: [loadbalancer]
  - port: 8443:443                   # host 8443 → Traefik ingress HTTPS
    nodeFilters: [loadbalancer]

registries:
  create:
    name: registry.localhost         # a local image registry, so you never push to the
    host: "0.0.0.0"                  # internet just to test a one-line change
    hostPort: "5111"

options:
  k3s:
    extraArgs:
      # Disable k3s's bundled ServiceLB: Traefik is enough, and this avoids port conflicts.
      - arg: --disable=servicelb
        nodeFilters: [server:*]
  kubeconfig:
    updateDefaultKubeconfig: true    # write the context into ~/.kube/config
    switchCurrentContext: true       # and select it
EOF
```
**What the key fields do:**

| Field | Purpose |
|---|---|
| `servers: 1`, `agents: 2` | One control plane, two workers. Two workers is the minimum that lets you *watch* the scheduler distribute pods and reschedule after a node failure |
| `image: rancher/k3s:v1.31.2-k3s1` | **Pinned version.** A cluster built on a floating tag is not reproducible |
| `ports … nodeFilters: [loadbalancer]` | Maps host ports to k3d's built-in load balancer, so `http://paytrack.localhost:8080` reaches Traefik |
| `registries.create` | Stands up a local registry at `registry.localhost:5111` reachable from inside the cluster |
| `--disable=servicelb` | k3s ships two LB mechanisms; Traefik is the one we use |
| `updateDefaultKubeconfig` | Merges credentials into `~/.kube/config` and switches context |

```bash
k3d cluster create --config k8s/k3d-cluster.yaml
```
**What this does:** creates the Docker network, the registry, the server container, two agent
containers and the load balancer; waits for the API server; and writes your kubeconfig.
Takes roughly 30–60 seconds.

✅ **Checkpoint**
```bash
kubectl get nodes -o wide
```
Three nodes, all `Ready`: `k3d-paytrack-server-0`, `k3d-paytrack-agent-0`, `k3d-paytrack-agent-1`.

```bash
docker ps --filter name=k3d --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```
**What this does:** shows the truth — **your "nodes" are Docker containers**. Understanding
that removes most of the mystery about how k3d behaves.

---

## Step 3 — Inspect the control plane

```bash
kubectl cluster-info
```
**What this does:** prints the API server endpoint and CoreDNS. Everything you do goes through
that one API server URL.

```bash
kubectl get pods -n kube-system
```
**What this does:** lists the system pods. You should see:

| Pod | Role |
|---|---|
| `coredns-*` | Cluster DNS — makes `paytrack-api.paytrack-dev.svc.cluster.local` resolve |
| `local-path-provisioner-*` | The default StorageClass; dynamically provisions PVCs (Lab 11) |
| `metrics-server-*` | Serves pod CPU/memory. **The HPA in Lab 12 does nothing without it** |
| `traefik-*` | The Ingress controller. Without it, Ingress objects do nothing (Lab 12) |
| `helm-install-traefik-*` | A completed Job that installed Traefik |

```bash
kubectl get componentstatuses 2>/dev/null || kubectl get --raw='/readyz?verbose' | head -20
```
**What this does:** `componentstatuses` is deprecated, so the fallback queries the API
server's readiness endpoint directly with `--raw`, listing every internal health check. A
useful reminder that **kubectl is only an HTTP client**.

```bash
kubectl config current-context
kubectl config get-contexts
```
**What this does:** shows which cluster kubectl is pointed at. **Check this before every
destructive command** — running `kubectl delete` against the wrong context is a career
event.

---

## Step 4 — Make kubectl comfortable

You will type these hundreds of times over the next three days.

```bash
cat >> ~/.bashrc <<'EOF'

# ── Kubernetes shortcuts (DevOps Professional course) ──
alias k='kubectl'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias kaf='kubectl apply -f'
alias kdf='kubectl delete -f'
alias kgp='kubectl get pods -o wide'
alias kge='kubectl get events --sort-by=.lastTimestamp'
alias kns='kubectl config set-context --current --namespace'
export KUBE_EDITOR=nano
source <(kubectl completion bash)
complete -o default -F __start_kubectl k
EOF
source ~/.bashrc
```
**What this does:**
- The aliases cut typing dramatically. `kge` (events, oldest-last) is the one you will thank
  yourself for during debugging.
- `kns <namespace>` switches your default namespace so you stop typing `-n` on every command.
- `kubectl completion bash` generates a completion script; `source <(...)` executes it from a
  process substitution without a temporary file. The `complete` line extends completion to
  the `k` alias too.

✅ **Checkpoint**
```bash
k get nodes
```

---

## Step 5 — Create the namespaces

```bash
cat > k8s/namespaces.yaml <<'EOF'
---
apiVersion: v1
kind: Namespace
metadata:
  name: paytrack-dev
  labels:
    app.kubernetes.io/part-of: paytrack
    environment: dev
    # Pod Security Admission: enforce the 'restricted' profile from day one.
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: Namespace
metadata:
  name: paytrack-prod
  labels:
    app.kubernetes.io/part-of: paytrack
    environment: prod
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# ResourceQuota caps what the whole namespace may consume.
apiVersion: v1
kind: ResourceQuota
metadata:
  name: paytrack-dev-quota
  namespace: paytrack-dev
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 2Gi
    limits.cpu: "4"
    limits.memory: 4Gi
    pods: "20"
    persistentvolumeclaims: "4"
---
# LimitRange supplies DEFAULTS, so a pod with no resources set is never BestEffort.
apiVersion: v1
kind: LimitRange
metadata:
  name: paytrack-dev-limits
  namespace: paytrack-dev
spec:
  limits:
    - type: Container
      default:            { cpu: 200m, memory: 256Mi }   # applied as limits if unset
      defaultRequest:     { cpu: 50m,  memory: 64Mi }    # applied as requests if unset
      max:                { cpu: "1",  memory: 1Gi }
EOF
```
**What each object does:**

| Object | Purpose |
|---|---|
| `Namespace` | A scope for names, RBAC, quotas and policy. Not a hard security boundary on its own |
| `pod-security.kubernetes.io/*` labels | **Pod Security Admission.** `enforce: baseline` rejects privileged pods outright; `warn`/`audit: restricted` tell you what would fail under the stricter profile without breaking the class |
| `ResourceQuota` | Caps total namespace consumption. Without it, one runaway Deployment starves the cluster |
| `LimitRange` | Supplies default requests/limits. **This matters:** a pod with no resources set is QoS class *BestEffort* and is evicted first under pressure |

```bash
kubectl apply -f k8s/namespaces.yaml
kubectl get ns --show-labels | grep paytrack
kubectl describe quota -n paytrack-dev
```
**What this does:** `apply` creates or updates the objects declaratively (as opposed to
`create`, which fails if they exist — `apply` is what you use in a pipeline).
`describe quota` shows Used vs Hard, which will become interesting when you scale in Lab 12.

```bash
kubectl config set-context --current --namespace=paytrack-dev
kubectl config view --minify | grep namespace
```
**What this does:** sets `paytrack-dev` as your default namespace, so `-n paytrack-dev` becomes
unnecessary. `--minify` shows only the current context.

---

## Step 6 — Smoke-test the cluster

```bash
kubectl run smoke --image=nginx:1.27-alpine --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"smoke","image":"nginx:1.27-alpine","resources":{"requests":{"cpu":"10m","memory":"16Mi"}}}]}}'
kubectl wait --for=condition=Ready pod/smoke --timeout=90s
kubectl get pod smoke -o wide
```
**What this does:** creates a single pod (`--restart=Never` means a bare Pod rather than a
Deployment) with explicit resource requests so the quota accepts it.
**`kubectl wait` is the scripting primitive you need**: it blocks until the condition is met
or the timeout expires, and returns non-zero on timeout — which is how a pipeline verifies a
deployment rather than guessing with `sleep`.

The `-o wide` output shows **which node** the scheduler chose.

```bash
kubectl exec smoke -- curl -s -o /dev/null -w "nginx responded %{http_code}\n" localhost
kubectl delete pod smoke
```
**What this does:** runs a command inside the pod to prove the container works, then removes
it. Note the `--` separating kubectl's flags from the command to run inside.

---

## Step 7 — Watch a node fail and recover

```bash
kubectl create deployment resilience-test --image=nginx:1.27-alpine --replicas=4
kubectl wait --for=condition=Available deployment/resilience-test --timeout=90s
kubectl get pods -o wide --selector=app=resilience-test
```
**What this does:** creates four replicas and shows their node placement. The scheduler will
have spread them across both agents.

```bash
docker stop k3d-paytrack-agent-1
kubectl get nodes -w &
sleep 45 && kill %1 2>/dev/null
```
**What this does:** **kills a node** by stopping its container. `kubectl get nodes -w`
*watches* for changes; running it with `&` backgrounds it so the `sleep` can run, and
`kill %1` stops it. Within about 40 seconds the node goes `NotReady`.

```bash
kubectl get pods -o wide --selector=app=resilience-test
```
**What this does:** shows pods on the dead node as `Terminating` or `Unknown`. Kubernetes'
default is to wait **5 minutes** (`--pod-eviction-timeout`) before evicting them — a
deliberate trade-off against a transient network blip causing mass rescheduling.

```bash
docker start k3d-paytrack-agent-1
kubectl wait --for=condition=Ready node/k3d-paytrack-agent-1 --timeout=120s
kubectl get nodes
kubectl get pods -o wide --selector=app=resilience-test
kubectl delete deployment resilience-test
```
**What this does:** brings the node back; the kubelet re-registers and pods stabilise. **You
did nothing.** That reconciliation loop — desired state versus observed state, corrected
continuously — is the whole of Kubernetes (Module 4 §4.1), and it is why Compose could not
take you further.

---

## Step 8 — Cluster lifecycle commands

```bash
k3d cluster list
```
**What this does:** shows clusters, server/agent counts and whether they are running.

```bash
# k3d cluster stop paytrack      # stop the containers; state is preserved
# k3d cluster start paytrack     # bring it back, same state
# k3d cluster delete paytrack    # ⚠️ destroys the cluster and everything in it
```
**What these do:** stop/start preserve everything and are what you want at the end of a day.
**`delete` is unrecoverable** — but harmless here, because from Lab 13 your entire cluster is
defined in Terraform.

```bash
git add k8s/k3d-cluster.yaml k8s/namespaces.yaml
git commit -m "feat(k8s): add cluster definition and namespaces

3-node k3d cluster (1 server, 2 agents) pinned to k3s v1.31.2, with a local
registry and Traefik ingress on host port 8080.

Namespaces carry Pod Security Admission labels, a ResourceQuota and a
LimitRange so that no workload can be BestEffort by accident."
git push -u origin main 2>/dev/null || (git switch -c feat/k8s-cluster && git push -u origin feat/k8s-cluster)
```

---

## ✅ Final checkpoint

```bash
kubectl get nodes
kubectl get ns | grep paytrack
kubectl get pods -n kube-system | grep -cE 'Running|Completed'
kubectl config view --minify | grep namespace
```
- 3 nodes `Ready`
- `paytrack-dev` and `paytrack-prod` exist
- kube-system pods running
- default namespace is `paytrack-dev`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Cluster creation hangs | inotify limits | Re-run Step 1, then `k3d cluster delete paytrack` and recreate |
| `connection refused` to the API server | Cluster stopped | `k3d cluster start paytrack` |
| Nodes `NotReady` after a host reboot | Containers did not restart | `k3d cluster start paytrack` |
| Port 8080 already allocated | Lab 07 stack still up | `docker compose down` in the repo, then recreate the cluster |
| Pods `Pending` with `FailedScheduling` | Quota, or genuinely insufficient resources | `kubectl describe pod <name>` and read Events |
| `error: You must be logged in` | kubeconfig context lost | `k3d kubeconfig merge paytrack --kubeconfig-switch-context` |

---

## 🎯 Outcome

A 3-node Kubernetes cluster with Traefik, metrics-server, a local registry, two namespaces
with quotas and Pod Security Admission, and a kubectl environment set up for speed. Cluster
definition committed as code.

**Next:** [Lab 10 — Deploy PayTrack API to Kubernetes](../lab-10-k8s-deploy-app/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Run Step 1 for the whole room at once**, before anyone creates a cluster. The inotify
  failure appears twenty minutes later, in an unrelated place, and burns the afternoon.
- **The three things that go wrong:**
  1. Lab 07's stack still holds port 8080. Make `docker compose down` the first instruction.
  2. Under 4 GB free RAM → agents flap. Check `free -h` before starting.
  3. The `k get pods` alias appears not to work in an existing terminal — they must `source
     ~/.bashrc` or open a new one.
- **Step 7 is the money shot.** Stopping a node in front of the room and watching Kubernetes
  cope is the moment orchestration stops being abstract. Give it the full three minutes.
- **Debrief question:** "You have just seen a node die and the cluster carry on. What does
  your organisation currently do when a production VM fails at 03:00, and how long does it
  take?"
</details>
