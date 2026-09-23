# Lab 12A — Scaling, Scheduling and Disruption

| | |
|---|---|
| **Day** | 4 — **optional**, after class or as homework |
| **Duration** | About 70 minutes, in eight parts |
| **Module** | 4 — Kubernetes (the Day 4 *Going Further* slides, section C) |
| **Slides** | `Lab12A_Advanced_Scaling.pptx` — in this folder, 8 slides, read it first |
| **Parent lab** | [Lab 12 — Ingress Routing and Autoscaling](README.md) |
| **You will produce** | An HPA whose step size you chose, pods that land where you meant, and a node drained without an outage — plus the deadlock a careless budget causes |
| **Feeds into** | Nothing. Everything you change here, you put back |

---

## Objective

Lab 12 created an HPA and watched it scale. This lab asks the three questions that come next:

- **How fast should it scale, and how slowly should it shrink?** The `behavior` block, and what
  each policy does to the step size.
- **Where do the pods actually land?** Requests, taints, tolerations and topology spread — and how
  to read the scheduler's own reason when the answer is "nowhere".
- **What happens when a node goes away on purpose?** `kubectl drain`, the PodDisruptionBudget that
  protects you, and the budget that deadlocks you.

## Prerequisites

- **Labs 09–12 complete** — the three-node k3d cluster, `deployment/paytrack-api`, the HPA and the
  PodDisruptionBudget from Lab 10
- **metrics-server working** — `kubectl top pods` must return numbers
- **Docker running**

---

## Before you start — how to run the commands

Every instruction is **one command in one grey box**, numbered in the order you run it.

| Question | Answer |
|---|---|
| **How do I run a command?** | Click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait for the prompt. |
| **Some boxes take minutes** | Scaling and draining are not instant. The text says what you are waiting for. |
| **A command is watching** | Anything with `-w` or `--watch` runs until you stop it. `Ctrl` + `C` stops watching without changing anything. |
| **Two parts break scheduling on purpose** | Each one ends by putting it back, and Part 8 restores everything. |

**Symbols:** `|` passes output on · `$(…)` runs a command first and uses its answer · `\` means the
command continues on the next line — copy every line · a box beginning `cat <<'EOF' | kubectl
apply -f -` is one command that feeds a manifest straight to the cluster.

🔁 **RECOVER — put everything back at any time**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project.

```bash
kubectl apply -f k8s/base/ && kubectl uncordon --all
```
**What this does:** re-applies the committed manifests and makes every node schedulable again —
undoing any drain from Part 7.

---

## Part 1 — Cluster, app, and a working metrics pipeline (6 min)

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command runs from here.

**2. Start the cluster if needed.**

```bash
k3d cluster start paytrack 2>/dev/null || k3d cluster create --config k8s/k3d-cluster.yaml
```
**What this does:** starts the existing cluster, or creates it from Lab 09's file.

**3. Select the namespace.**

```bash
kubectl config set-context --current --namespace=paytrack-dev
```
**What this does:** saves typing `-n paytrack-dev` everywhere.

**4. Apply the committed state.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** Deployment, Service, HPA, PDB, Ingress and the rest, from git.

**5. Wait for the application.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits until every replica is available.

**6. Check metrics are flowing.**

```bash
kubectl top pods
```
**What this does:** CPU and memory per pod. **If this errors, the HPA cannot work** — metrics-server
needs a minute after a cluster start; wait and try again.

**7. Look at the three nodes.**

```bash
kubectl get nodes -o custom-columns='NAME:.metadata.name,STATUS:.status.conditions[-1].type,CPU:.status.capacity.cpu,MEM:.status.capacity.memory'
```
**What this does:** name, readiness and capacity for each node. Those capacity numbers are what the
scheduler packs against.

---

## Part 2 — What the HPA is actually deciding (10 min)

**1. Read the HPA's current state.**

```bash
kubectl get hpa paytrack-api
```
**What this does:** one line: the metric target, the current value, and the replica range. `TARGETS`
showing `<unknown>` means metrics are not arriving yet.

**2. Read its reasoning.**

```bash
kubectl describe hpa paytrack-api | tail -20
```
**What this does:** the Conditions and Events at the bottom say **why** it chose the current
replica count — `ScalingActive`, `AbleToScale`, and the recommendation it computed.

**3. See the behaviour Lab 12 set.**

```bash
kubectl get hpa paytrack-api -o jsonpath='{.spec.behavior}{"\n"}'
```
**What this does:** prints the `behavior` block: scale up with no stabilisation window, scale down
after 120 seconds of calm. **Asymmetry is deliberate** — scaling up late costs latency, scaling
down early costs an outage.

**4. Add explicit step policies.**

```bash
kubectl patch hpa paytrack-api --type=merge -p '{"spec":{"behavior":{"scaleUp":{"stabilizationWindowSeconds":0,"policies":[{"type":"Pods","value":2,"periodSeconds":15}]},"scaleDown":{"stabilizationWindowSeconds":60,"policies":[{"type":"Pods","value":1,"periodSeconds":60}]}}}}'
```
**What this does:** sets the **step size**: add at most 2 pods every 15 seconds; remove at most 1
pod every 60 seconds, after 60 seconds of calm. (60 rather than the 300 you would use in
production, so this lab finishes.)

**5. Confirm it took.**

```bash
kubectl get hpa paytrack-api -o jsonpath='{.spec.behavior.scaleUp.policies[0]}{"\n"}'
```
**What this does:** prints the scale-up policy you just set.

**6. Start watching, in this terminal.**

```bash
kubectl get hpa paytrack-api --watch &
```
**What this does:** `--watch` prints a new line each time the HPA changes, and `&` puts it in the
background so you keep the prompt. You will stop it in command 10.

**7. Generate load.**

```bash
kubectl run load-generator --image=busybox:1.36 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/api/v1/info >/dev/null; done"
```
**What this does:** starts a pod that calls the Service in a tight loop, driving CPU up on the API
pods.

**8. Watch the replica count climb.**

```bash
sleep 90 && kubectl get hpa paytrack-api && kubectl get pods -l app.kubernetes.io/name=paytrack-api --no-headers | wc -l
```
**What this does:** waits ninety seconds, then prints the HPA line and counts the pods. Replicas
should have risen in steps of two — the policy you set.

**9. Stop the load.**

```bash
kubectl delete pod load-generator
```
**What this does:** removes the load generator. CPU falls immediately; the HPA does **not**.

**10. Watch it wait before shrinking.**

```bash
sleep 120 && kubectl get hpa paytrack-api && kubectl get pods -l app.kubernetes.io/name=paytrack-api --no-headers | wc -l
```
**What this does:** after the 60-second stabilisation window plus a 60-second policy period, the
count starts dropping — **one pod at a time**, which is what your scale-down policy says.

**11. Stop the background watch.**

```bash
kill %1 2>/dev/null; echo "watch stopped"
```
**What this does:** `%1` is the first background job. The message confirms it; the error is hidden
if it had already finished.

> 🔑 **Utilisation is a percentage of `requests`, not of the node.** Lab 10 requests 50m CPU, so a
> 50% target means 25m per pod. A pod with no requests gives the HPA nothing to compute, and it
> reports `<unknown>` for ever.

---

## Part 3 — Why is this pod Pending? Read the scheduler (8 min)

**1. Ask for more pods than the namespace can hold.**

```bash
kubectl scale deployment paytrack-api --replicas=30
```
**What this does:** requests thirty replicas. Each needs 50m CPU and 64Mi, and the Lab 09
ResourceQuota allows 2 CPU and 2Gi in total.

**2. Look at what happened.**

```bash
sleep 20 && kubectl get pods -l app.kubernetes.io/name=paytrack-api --no-headers | awk '{print $3}' | sort | uniq -c
```
**What this does:** counts the pods by status. `awk '{print $3}'` prints the third column and
`uniq -c` counts repeats — so you get, for example, `20 Running`, without a screen of names.

**3. Find out what stopped the rest.**

```bash
kubectl describe replicaset -l app.kubernetes.io/name=paytrack-api | grep -A5 -i "quota\|failed" | head -20
```
**What this does:** the ReplicaSet controller — not the pod — reports the refusal:
`exceeded quota: paytrack-dev-quota`. **A quota refusal never produces a Pending pod**; the object
is rejected before it exists, so you must look at the controller.

**4. Check the quota's own numbers.**

```bash
kubectl describe quota paytrack-dev-quota | tail -10
```
**What this does:** `Used` against `Hard`. This is the line to screenshot when someone says "the
cluster is full".

**5. Scale back to something schedulable.**

```bash
kubectl scale deployment paytrack-api --replicas=4
```
**What this does:** four replicas, comfortably inside the quota — and enough to see spreading in
Part 5.

**6. Wait for them.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits until all four are available.

---

## Part 4 — Reserve a node with a taint (10 min)

**1. See where the pods are now.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName' --no-headers | awk '{print $2}' | sort | uniq -c
```
**What this does:** counts pods per node. Lab 10's pod anti-affinity already prefers spreading, so
you should see them across two or three nodes.

**2. Pick a node that is not running the database.**

```bash
TAINTED=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep agent | grep -v "$(kubectl get pod -l app.kubernetes.io/name=postgres -o jsonpath='{.items[0].spec.nodeName}')" | head -1)
```
**What this does:** lists the agent nodes, removes the one hosting PostgreSQL (its storage is
pinned there), and keeps the first of what is left. Nothing is printed.

**3. Check which node you picked.**

```bash
echo "$TAINTED"
```
**What this does:** prints something like `k3d-paytrack-agent-1`. If it is empty, your cluster has
only one agent — use the server node name instead.

**4. Reserve it.**

```bash
kubectl taint nodes "$TAINTED" workload=payments:NoSchedule
```
**What this does:** a **taint** repels pods. `NoSchedule` means "nothing new lands here unless it
tolerates this" — existing pods stay put.

**5. Force fresh pods.**

```bash
kubectl rollout restart deployment/paytrack-api && kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** replaces every pod, so each one is scheduled again under the new rule.

**6. See where they went.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName' --no-headers | awk '{print $2}' | sort | uniq -c
```
**What this does:** the tainted node no longer appears — every pod avoided it.

**7. Let the application onto that node.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"add","path":"/spec/template/spec/tolerations","value":[{"key":"workload","operator":"Equal","value":"payments","effect":"NoSchedule"}]}]'
```
**What this does:** adds a **toleration** — permission to ignore that specific taint. A toleration
does not *attract* pods; it only removes the objection.

**8. Watch them spread back.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s && kubectl get pods -l app.kubernetes.io/name=paytrack-api -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName' --no-headers | awk '{print $2}' | sort | uniq -c
```
**What this does:** rolls the pods and counts them per node again. The tainted node is back in use,
because these pods now tolerate it.

**9. Remove the taint.**

```bash
kubectl taint nodes "$TAINTED" workload=payments:NoSchedule-
```
**What this does:** the trailing **`-`** removes a taint. Forgetting it is why a node sometimes
stays mysteriously empty for weeks.

**10. Remove the toleration.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"remove","path":"/spec/template/spec/tolerations"}]'
```
**What this does:** takes the permission away again, leaving the Deployment as git has it.

---

## Part 5 — Spread the replicas on purpose (8 min)

**1. Add a topology spread constraint.** One command — copy the whole box:

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"add","path":"/spec/template/spec/topologySpreadConstraints","value":[{"maxSkew":1,"topologyKey":"kubernetes.io/hostname","whenUnsatisfiable":"DoNotSchedule","labelSelector":{"matchLabels":{"app.kubernetes.io/name":"paytrack-api"}}}]}]'
```
**What this does:** says "across nodes (`kubernetes.io/hostname`), the busiest and the emptiest may
differ by at most one pod". `DoNotSchedule` makes it a hard rule: a pod that cannot satisfy it stays
Pending.

**2. Roll the pods so the rule applies.**

```bash
kubectl rollout restart deployment/paytrack-api && kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** every pod is scheduled again, now under the spread rule.

**3. Count them per node.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName' --no-headers | awk '{print $2}' | sort | uniq -c
```
**What this does:** with four replicas across three nodes you should see `2 1 1` — a skew of one.
That is the constraint working.

**4. Ask for a count that cannot be spread evenly.**

```bash
kubectl scale deployment paytrack-api --replicas=7
```
**What this does:** seven pods across three nodes is `3 2 2` — still a skew of one, so this should
succeed. Kubernetes does the arithmetic, not you.

**5. Check.**

```bash
sleep 30 && kubectl get pods -l app.kubernetes.io/name=paytrack-api -o custom-columns='NODE:.spec.nodeName' --no-headers | sort | uniq -c
```
**What this does:** counts again. If any pod is Pending, the next command explains why.

**6. If anything is Pending, read the reason.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api --field-selector=status.phase=Pending -o name | head -1 | xargs -r kubectl describe | grep -A4 "FailedScheduling" | head -8
```
**What this does:** finds a Pending pod, if there is one, and prints the scheduler's reason.
`xargs -r` runs the next command only if something was found. With a spread constraint the message
names `node(s) didn't match pod topology spread constraints`.

**7. Scale back down.**

```bash
kubectl scale deployment paytrack-api --replicas=3
```
**What this does:** back to the committed replica count.

**8. Remove the constraint.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"remove","path":"/spec/template/spec/topologySpreadConstraints"}]'
```
**What this does:** leaves the Deployment as git has it. Lab 10's pod anti-affinity still spreads
the pods — topology spread is the more precise, more modern way of saying the same thing.

---

## Part 6 — Drain a node without an outage (10 min)

**1. Check the budget that protects you.**

```bash
kubectl get pdb paytrack-api
```
**What this does:** Lab 10's PodDisruptionBudget: `MIN AVAILABLE 2`. `ALLOWED DISRUPTIONS` tells you
how many pods may be evicted **right now**.

**2. Wait for the rollout to settle.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** a budget only allows disruption when enough pods are healthy.

**3. Pick a node to drain — again, not the database's.**

```bash
DRAIN=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep agent | grep -v "$(kubectl get pod -l app.kubernetes.io/name=postgres -o jsonpath='{.items[0].spec.nodeName}')" | head -1)
```
**What this does:** the same selection as Part 4. PostgreSQL's volume is pinned to its node, so
draining that one would leave the database Pending.

**4. Check your choice.**

```bash
echo "draining: $DRAIN"
```
**What this does:** prints the node name.

**5. See what is on it.**

```bash
kubectl get pods -A -o wide --field-selector spec.nodeName="$DRAIN" --no-headers | awk '{print $1, $2}'
```
**What this does:** every pod on that node, namespace first. `-A` means all namespaces.

**6. Drain it.**

```bash
kubectl drain "$DRAIN" --ignore-daemonsets --delete-emptydir-data --timeout=120s
```
**What this does:** two things at once: **cordons** the node (nothing new is scheduled) and
**evicts** what is running, honouring the PodDisruptionBudget. `--ignore-daemonsets` is required
because daemonset pods are recreated on the node by design; `--delete-emptydir-data` acknowledges
that the API's `/tmp` scratch volume will be lost.

**7. Watch the service stay up.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api -o wide
```
**What this does:** the evicted pods have been rescheduled onto the remaining nodes, and the
replica count is unchanged. **A node left the cluster and nobody was served an error.**

**8. Confirm the node is cordoned.**

```bash
kubectl get nodes
```
**What this does:** the drained node shows `Ready,SchedulingDisabled`.

**9. Put it back in service.**

```bash
kubectl uncordon "$DRAIN"
```
**What this does:** makes it schedulable again. **Draining does not undo itself** — a forgotten
cordon quietly shrinks your cluster.

---

## Part 7 — The budget that deadlocks the drain (8 min)

**1. Make the budget impossible to satisfy.**

```bash
kubectl patch pdb paytrack-api --type=merge -p '{"spec":{"minAvailable":3}}'
```
**What this does:** requires all three replicas to stay available — so **no** pod may ever be
voluntarily evicted.

**2. Check what it now allows.**

```bash
kubectl get pdb paytrack-api
```
**What this does:** `ALLOWED DISRUPTIONS 0`. That number is the whole story.

**3. Try to drain. This fails on purpose.**

```bash
kubectl drain "$DRAIN" --ignore-daemonsets --delete-emptydir-data --timeout=60s
```
**What this does:** the eviction is refused, repeatedly:
`Cannot evict pod as it would violate the pod's disruption budget`, and the command gives up after
sixty seconds. **This is the budget working, not an error to force past** — a node upgrade would
hang here for as long as you let it.

**4. Uncordon the node the failed drain left behind.**

```bash
kubectl uncordon "$DRAIN"
```
**What this does:** a failed drain still cordons. This is why "the cluster stopped scheduling" is
often a drain someone abandoned.

**5. Fix the budget.**

```bash
kubectl patch pdb paytrack-api --type=merge -p '{"spec":{"minAvailable":2}}'
```
**What this does:** back to Lab 10's value: two must stay, so one may go.

**6. Confirm it allows a disruption again.**

```bash
kubectl get pdb paytrack-api
```
**What this does:** `ALLOWED DISRUPTIONS 1`.

> 🔴 **`minAvailable` equal to `replicas` is the classic self-inflicted stall** — and with
> `replicas: 1` it is guaranteed. A budget must leave room for at least one pod to move, or nothing
> can ever be patched, upgraded or rebalanced.
>
> **And remember what a PDB is not:** it constrains **voluntary** disruption only. A node that dies
> takes its pods with it, budget or no budget.

---

## Part 8 — Put the cluster back (5 min)

**1. Re-apply the committed manifests.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** Deployment, HPA, PDB and the rest exactly as git has them, discarding every
patch from this lab.

**2. Make sure no node is left cordoned.**

```bash
kubectl uncordon --all
```
**What this does:** clears any leftover `SchedulingDisabled`. Safe to run even if nothing is
cordoned.

**3. Make sure no taint is left behind.**

```bash
kubectl get nodes -o custom-columns='NODE:.metadata.name,TAINTS:.spec.taints[*].key'
```
**What this does:** lists taints per node. The control-plane node may carry a built-in one; the
agents should show `<none>`. If `workload` is still there, run Part 4 command 9 again.

**4. Wait for a healthy rollout.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits until the committed replica count is available.

**5. Final check.**

```bash
kubectl get pods,hpa,pdb -o wide
```
**What this does:** pods Running across nodes, the HPA reporting a real percentage, and the PDB
allowing one disruption. The cluster is as Lab 13 expects it.

---

## What decides where a pod goes

| Mechanism | Used in | The failure it causes when wrong |
|---|---|---|
| `resources.requests` | Lab 10 | No requests → the HPA reports `<unknown>` and the pod is evicted first |
| ResourceQuota | Lab 09 | Pods are **refused at creation** — look at the ReplicaSet, not for a Pending pod |
| podAntiAffinity | Lab 10 | Too strict → replicas stay Pending with no node to take them |
| topologySpreadConstraints | Part 5 | `DoNotSchedule` with an impossible skew → Pending |
| taints / tolerations | Part 4 | A taint left behind → a node that is silently empty for weeks |
| PodDisruptionBudget | Parts 6–7 | `minAvailable` = `replicas` → drains hang for ever |

---

## 🧩 Stretch (homework)

1. **Memory as a second metric.** Add a memory metric to the HPA and drive memory up without
   driving CPU up. Confirm the HPA takes the **highest** recommendation, then write down why memory
   is usually a poor scaling signal for a web service.
2. **PriorityClass.** Create two PriorityClasses, give the API the higher one, fill the cluster with
   low-priority pods, and watch preemption evict them to make room.
3. **A real node failure.** `docker stop k3d-paytrack-agent-1` and time how long until the pods are
   rescheduled. Compare with the graceful drain in Part 6 — and note that the PDB did nothing.
4. **Cluster autoscaling, on paper.** Write the two sentences you would tell a finance team about
   what the HPA does, what a cluster autoscaler would add, and which one costs money.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `kubectl top pods` errors | metrics-server is not ready | Wait a minute after a cluster start; `kubectl get pods -n kube-system \| grep metrics` |
| HPA `TARGETS` shows `<unknown>` | No metrics, or no CPU requests on the pods | Fix metrics first; check `resources.requests` exists |
| The HPA never scales up | The load generator is not actually loading | `kubectl top pods` during the load; the API pods should be well above 25m |
| `$TAINTED` or `$DRAIN` is empty | A new terminal, or only one agent node | Re-run the box that sets it; on a one-agent cluster use the node name directly |
| Drain hangs for ever | The PDB allows no disruption | `kubectl get pdb` — see Part 7 |
| A node stays empty after the lab | A taint or cordon was left behind | Part 8 commands 2 and 3 |
| PostgreSQL goes Pending | You drained the node holding its local volume | `kubectl uncordon <node>`; the pod returns |
| Pods Pending after Part 5 | The spread constraint is still applied | Part 5 command 8, or `kubectl apply -f k8s/base/` |

---

## 🎯 Outcome

You can set an HPA's step size and stabilisation windows and explain why they are asymmetric, read
the scheduler's own reason for a Pending pod, reserve a node with a taint and let one workload back
on to it, spread replicas within a skew you chose, and drain a node while the service keeps
serving — including the moment a badly written PodDisruptionBudget makes that impossible.

**Next:** [Lab 13 — Terraform](../lab-13-terraform-iac/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 7 is the memorable one.** Set `minAvailable` to the replica count, run the drain, and let
  the room watch the eviction be refused over and over. Then ask how many of their services run a
  single replica with a budget that says `minAvailable: 1`.
- **Part 2 needs patience.** The scale-down window means nothing happens for two minutes. Say so
  before you start it, or the room will decide the HPA is broken.
- **Things that go wrong:**
  1. metrics-server is not ready after a cluster start and every HPA number is `<unknown>`.
  2. Delegates drain the node holding PostgreSQL's local-path volume. The `$DRAIN` command avoids
     it; if someone types a node name by hand, `uncordon` fixes it.
  3. A taint or cordon is left behind and the next lab schedules oddly. Part 8 exists for that.
- **Debrief question:** "Your platform team wants to patch every node next month. For your most
  critical service, what are `replicas`, `minAvailable` and `maxUnavailable` today — and does that
  combination let them do it without calling you?"
</details>
