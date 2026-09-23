# Lab 10A — Debugging and Rollouts: the 3 a.m. Commands

| | |
|---|---|
| **Day** | 4 — **optional**, after class or as homework |
| **Duration** | About 70 minutes, in ten parts |
| **Module** | 4 — Kubernetes (the Day 4 *Going Further* slides, section A) |
| **Slides** | `Lab10A_Advanced_Debugging.pptx` — in this folder, 10 slides, read it first |
| **Parent lab** | [Lab 10 — Deploy PayTrack API to Kubernetes](README.md) |
| **You will produce** | Six broken deployments you diagnosed from the cluster's own output, and a rollback done in one command |
| **Feeds into** | Nothing. Everything you break here, you put back |

---

## Objective

Lab 10 deployed the application and broke it three ways. This lab breaks it **six** ways on
purpose and, for each one, walks the four commands that explain it — because the difference
between a ten-minute incident and a two-hour one is knowing which command to type first.

Then it covers going back: what a rolling update actually does, how to watch one, how to stop one
half-way, and how to undo it.

## Prerequisites

- **Labs 09 and 10 complete** — the k3d cluster `paytrack` exists and `deployment/paytrack-api`
  runs in the `paytrack-dev` namespace
- **Docker running** (k3d runs Kubernetes inside containers)

---

## Before you start — how to run the commands

**No Linux or Kubernetes experience assumed beyond Labs 09–10.** Every instruction is **one
command in one grey box**, numbered in the order you run it.

| Question | Answer |
|---|---|
| **How do I open a terminal?** | Press `Ctrl` + `Alt` + `T`. It shows a line ending in `$` — the prompt. |
| **How do I run a command?** | Click in, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait for the prompt. |
| **Several commands here break things on purpose** | The text says so before the box. Each part ends by putting it back. |
| **A command is waiting and printing nothing** | `kubectl rollout status` and `-w` watch until something changes. `Ctrl` + `C` stops watching without changing anything. |
| **The last line is `:` or `(END)`** | A scrollable view. Press `q`. |

**Symbols in the boxes:** `|` passes output to the next command · `$(…)` runs a command first and
uses its answer · `\` at the end of a line means the command continues below — copy every line ·
`#` starts a note the computer ignores.

**`kubectl` shorthand used throughout:** `-n` namespace · `-l` label selector · `-o wide` more
columns · `-o jsonpath=…` print one field · `--tail=N` last N log lines.

🔁 **RECOVER — put everything back at any time**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project, where `k8s/base/` lives.

```bash
kubectl apply -f k8s/base/
```
**What this does:** re-applies the committed manifests, overwriting every experiment in this lab.
The deployment returns to the state Lab 10 left it in.

---

## Part 1 — A cluster, a namespace and a running app (6 min)

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command below runs from here.

**2. Make sure the cluster is running.**

```bash
k3d cluster start paytrack 2>/dev/null || k3d cluster create --config k8s/k3d-cluster.yaml
```
**What this does:** starts the existing cluster; if there is none, `||` creates it from the file
Lab 09 wrote. Starting takes about twenty seconds.

**3. Point kubectl at the right namespace.**

```bash
kubectl config set-context --current --namespace=paytrack-dev
```
**What this does:** saves you typing `-n paytrack-dev` on every command for the rest of the lab.

**4. Check the nodes.**

```bash
kubectl get nodes
```
**What this does:** three nodes — one server and two agents — all `Ready`. If any says `NotReady`,
wait a few seconds and run it again.

**5. Make sure the app is deployed.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** applies the Deployment, Service and anything else in that folder. `configured`
or `unchanged` are both fine.

**6. Wait for it to be ready.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits until every replica is updated and available, then prints
`successfully rolled out`. This is the command a deployment pipeline waits on.

**7. Look at what you have.**

```bash
kubectl get pods -o wide
```
**What this does:** three pods, `READY 1/1`, `STATUS Running`, each on a node named in the last
column. Note the `RESTARTS` column — it should be `0`.

---

## Part 2 — The four commands, in order (6 min)

Learn this order once: **get → describe → logs → events.**

**1. Store one pod's name.**

```bash
POD=$(kubectl get pods -l app.kubernetes.io/name=paytrack-api -o jsonpath='{.items[0].metadata.name}')
```
**What this does:** `-l` selects pods by label and `-o jsonpath` prints one field — the first pod's
name — which is stored under `POD`. Nothing is printed.

**2. Check what you stored.**

```bash
echo "$POD"
```
**What this does:** prints something like `paytrack-api-7d4f8c9b5-x2k9p`. If it is empty, the pods
are not running yet.

**3. `get` — what is the shape of the problem?**

```bash
kubectl get pod "$POD" -o wide
```
**What this does:** one line: ready state, status, restarts, age, IP and node. On a healthy pod
this is all you need.

**4. `describe` — why is it in that state?**

```bash
kubectl describe pod "$POD" | tail -20
```
**What this does:** prints the end of a long description — and the end is the part that matters:
the **Events** list. Scheduling decisions, image pulls, probe failures and mount errors all appear
here, newest last.

**5. `logs` — what did the application say?**

```bash
kubectl logs "$POD" --tail=15
```
**What this does:** the last fifteen lines the container wrote. For a crashed container you add
`--previous`, which you will use in Part 5.

**6. `events` — what has been happening in this namespace?**

```bash
kubectl get events --sort-by=.lastTimestamp | tail -15
```
**What this does:** every recent event in the namespace, oldest first, so the newest are at the
bottom. Events **expire after about an hour** — capture them during an incident, not afterwards.

---

## Part 3 — Failure 1: Pending, and the quota that says no (8 min)

**1. Ask for a node that does not exist.**

```bash
kubectl run pending-demo --image=nginx:1.27-alpine --restart=Never --overrides='{"spec":{"nodeSelector":{"disktype":"nvme-fast"}}}'
```
**What this does:** creates a single pod that insists on a node labelled `disktype=nvme-fast`. No
node has that label. `--restart=Never` makes it a plain pod rather than a Deployment.

**2. Look at it.**

```bash
kubectl get pod pending-demo
```
**What this does:** `STATUS Pending`, `READY 0/1`, and it will stay that way for ever. Pending
means **no node has been chosen yet**.

**3. Ask why.**

```bash
kubectl describe pod pending-demo | tail -6
```
**What this does:** the Events show `FailedScheduling` and the scheduler's own reason:
`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`. The scheduler
tells you exactly what it could not satisfy.

**4. Delete it.**

```bash
kubectl delete pod pending-demo
```
**What this does:** removes the pod.

**5. Now ask for more than the namespace is allowed.**

```bash
kubectl run quota-demo --image=nginx:1.27-alpine --restart=Never --overrides='{"spec":{"containers":[{"name":"quota-demo","image":"nginx:1.27-alpine","resources":{"requests":{"cpu":"8","memory":"8Gi"}}}]}}'
```
**What this does:** requests 8 CPUs and 8 GB, far beyond the `ResourceQuota` Lab 09 set (2 CPU,
2 Gi). **The pod is never created at all**: the API server rejects it with
`exceeded quota: paytrack-dev-quota`.

**6. Confirm nothing was created.**

```bash
kubectl get pod quota-demo
```
**What this does:** `Error from server (NotFound)`. This is the difference worth knowing:
**quota rejects at admission** (no object, an error in your terminal or your pipeline), while
**scheduling failure creates the object** and leaves it Pending.

**7. See what the quota has left.**

```bash
kubectl describe quota paytrack-dev-quota | tail -10
```
**What this does:** `Used` against `Hard` for each resource. When a deployment will not scale, this
is the second place to look after node capacity.

---

## Part 4 — Failure 2: ImagePullBackOff (6 min)

**1. Point the deployment at an image that does not exist.**

```bash
kubectl set image deployment/paytrack-api paytrack-api=ghcr.io/nobody/paytrack-api:does-not-exist
```
**What this does:** `set image <resource> <container>=<image>` changes just the image. The
container in Lab 10's Deployment is called `paytrack-api`, which is why the name appears twice.

**2. Watch what happens to the new pod.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** a new pod appears with `STATUS ErrImagePull`, then `ImagePullBackOff`. **The
three original pods are still Running** — `maxUnavailable: 0` means Kubernetes will not remove a
healthy pod until a new one is ready. A bad image is not an outage.

**3. Ask why.**

```bash
kubectl describe pod -l app.kubernetes.io/name=paytrack-api | grep -A5 "Failed"
```
**What this does:** shows the failure events with five lines of context: `Failed to pull image …`
and the registry's own message. Read the image name in that message character by character — it is
usually a typo or a missing tag.

**4. Check the rollout is stuck.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=20s
```
**What this does:** waits twenty seconds, reports `Waiting for deployment … 1 out of 3 new replicas
have been updated`, and exits non-zero. **This is what makes a pipeline fail rather than hang.**

**5. Undo it.**

```bash
kubectl rollout undo deployment/paytrack-api
```
**What this does:** goes back to the previous revision — the working image. Kubernetes keeps the
old ReplicaSet, so this is a scale-up, not a rebuild.

**6. Confirm.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=60s
```
**What this does:** `successfully rolled out`. The broken pod is gone.

---

## Part 5 — Failure 3: CrashLoopBackOff (8 min)

**1. Make the container exit as soon as it starts.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/command","value":["sh","-c","echo starting up; sleep 2; echo giving up; exit 3"]}]'
```
**What this does:** `patch --type=json` adds one field — a `command` that overrides the image's
own start-up and exits with code 3 after two seconds. Every new pod will do this.

**2. Watch the pods cycle.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** a pod goes `Running` → `Error` → `CrashLoopBackOff`, and `RESTARTS` climbs.
Run it a few times: the restarts slow down, because Kubernetes doubles the wait each time, up to
five minutes.

**3. Store the crashing pod's name.**

```bash
CRASHED=$(kubectl get pods -l app.kubernetes.io/name=paytrack-api --field-selector=status.phase!=Running -o jsonpath='{.items[0].metadata.name}')
```
**What this does:** `--field-selector` picks pods that are **not** Running — the broken one.
Nothing is printed.

**4. Read the logs of the container that died.**

```bash
kubectl logs "$CRASHED" --previous
```
**What this does:** `--previous` reads the **last terminated** container, not the one currently
starting. You see `starting up` and `giving up` — the evidence that is gone the moment you forget
this flag.

**5. Confirm the exit code.**

```bash
kubectl describe pod "$CRASHED" | grep -A3 "Last State"
```
**What this does:** `Last State: Terminated`, `Reason: Error`, `Exit Code: 3`. An exit code from
your own application means an application problem: read the logs. Exit **137** would mean the
kernel killed it — see Part 6.

**6. Put it back.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"remove","path":"/spec/template/spec/containers/0/command"}]'
```
**What this does:** removes the `command` override, so the image's own start-up runs again.

**7. Wait for health.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=90s
```
**What this does:** `successfully rolled out`, and the crash loop is over.

---

## Part 6 — Failure 4: OOMKilled (6 min)

**1. Set a memory limit the application cannot live in.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"32Mi"}]'
```
**What this does:** lowers the memory ceiling from 192Mi to 32Mi. Python plus gunicorn needs more
than that, so the kernel will kill it.

**2. Watch the result.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** a new pod restarts repeatedly. The status may read `OOMKilled` directly, or
`CrashLoopBackOff` with restarts climbing.

**3. Find out who killed it.**

```bash
kubectl describe pod -l app.kubernetes.io/name=paytrack-api | grep -B2 -A6 "Last State"
```
**What this does:** `Reason: OOMKilled` and `Exit Code: 137`. That is 128 + 9 — SIGKILL from the
kernel's out-of-memory killer, exactly as in Lab 08A. **The application did not crash; it was
stopped.**

**4. Put the limit back.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"192Mi"}]'
```
**What this does:** restores the committed value.

**5. Wait for health.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=90s
```
**What this does:** back to three healthy pods.

> 🔑 **Exit 137 is a capacity conversation, not a bug report.** Either the limit is too low or the
> application leaks. Deciding which is what `kubectl top pod` and a week of metrics are for.

---

## Part 7 — Failure 5: Running, but taking no traffic (8 min)

**1. Break the readiness probe only.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/not-a-real-path"}]'
```
**What this does:** points readiness at a URL the application does not serve. Liveness is
untouched, so nothing will be restarted.

**2. Wait a few seconds, then look.**

```bash
sleep 20 && kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** pods show `READY 0/1` while `STATUS` stays `Running`. Nothing crashed;
Kubernetes simply does not believe they can serve.

**3. See the consequence.**

```bash
kubectl get endpointslices -l kubernetes.io/service-name=paytrack-api -o jsonpath='{range .items[*]}{.endpoints[*].conditions.ready}{"\n"}{end}'
```
**What this does:** prints the readiness of each endpoint behind the Service. They are `false` — so
the Service has nobody to send traffic to, and a caller gets a connection error or a 503.

**4. Confirm from inside the cluster.**

```bash
kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://paytrack-api.paytrack-dev.svc.cluster.local/health
```
**What this does:** runs a throw-away pod that calls the Service by its cluster DNS name. You get
`000` — no connection — because the Service has no ready endpoints.

**5. Read the probe's own complaint.**

```bash
kubectl describe pod -l app.kubernetes.io/name=paytrack-api | grep -A2 "Readiness probe failed"
```
**What this does:** `Readiness probe failed: HTTP probe failed with statuscode: 404`. The cluster
tells you the exact status code it got.

**6. Put it back.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/ready"}]'
```
**What this does:** restores the committed path.

**7. Confirm traffic returns.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=90s
```
**What this does:** back to `1/1` and in the Service again.

> 🔑 **"Running" is not "working".** `READY 0/1` with `Running` is the state people misread most
> often — and it is the one where the application is usually fine and its *dependency* is not.

---

## Part 8 — Failure 6: the liveness restart storm (8 min)

**1. Point liveness at a path that does not exist.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe/httpGet/path","value":"/not-a-real-path"}]'
```
**What this does:** liveness now fails for every pod. Liveness failure means **restart**.

**2. Watch the restarts climb.**

```bash
sleep 45 && kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** waits for the probe's failure threshold, then shows `RESTARTS 1`, then 2, then
3 — on **every** pod, at roughly the same time, because they all fail the same check together.

**3. See it in the events.**

```bash
kubectl get events --sort-by=.lastTimestamp | grep -i "liveness\|killing" | tail -8
```
**What this does:** `Liveness probe failed … Container paytrack-api failed liveness probe, will be
restarted`. This is the signature of a restart storm.

**4. Put it back.**

```bash
kubectl patch deployment paytrack-api --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe/httpGet/path","value":"/health"}]'
```
**What this does:** restores the committed probe.

**5. Confirm calm.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=90s
```
**What this does:** a clean rollout; restarts stop.

> 🔴 **Now imagine the probe had called the database.** A thirty-second database stall would fail
> liveness on every replica simultaneously, restarting the entire deployment — an outage caused by
> slowness, not by failure. **Liveness tests the process. Readiness may test dependencies.** That
> single sentence prevents this whole class of incident.

---

## Part 9 — A shell for an image that has none (7 min)

**1. Store a healthy pod's name.**

```bash
POD=$(kubectl get pods -l app.kubernetes.io/name=paytrack-api -o jsonpath='{.items[0].metadata.name}')
```
**What this does:** the first running pod. Nothing is printed.

**2. Try the obvious thing first.**

```bash
kubectl exec "$POD" -- curl -s -o /dev/null -w "health: %{http_code}\n" http://localhost:8080/health
```
**What this does:** runs a command *inside* the container. It works here because Lab 06's image
includes `curl` for its HEALTHCHECK — many production images include nothing at all.

**3. Now bring your own tools.**

```bash
kubectl debug "$POD" --image=nicolaka/netshoot --target=paytrack-api -- sh -c "ss -tunp | head; nslookup paytrack-api"
```
**What this does:** attaches an **ephemeral container** to the running pod, sharing its network and
(with `--target`) its process namespace. You get socket and DNS tools without adding anything to
the application image. The first run pulls the netshoot image.

**4. Read what it printed.**

```bash
kubectl logs "$POD" -c $(kubectl get pod "$POD" -o jsonpath='{.spec.ephemeralContainers[0].name}')
```
**What this does:** an ephemeral container's output is read like any other container's, with `-c`
naming it. The inner command finds that name for you.

**5. Make a safe copy to experiment on.**

```bash
kubectl debug "$POD" --copy-to=debug-copy --image=nicolaka/netshoot --share-processes -- sleep 600
```
**What this does:** creates a **copy** of the pod with a debug container added. The copy has no
Service label pointing at it, so it takes no traffic — poke at it freely.

**6. Use it.**

```bash
kubectl exec debug-copy -c debugger -- curl -s -m 5 -o /dev/null -w "from the copy: %{http_code}\n" http://paytrack-api.paytrack-dev.svc.cluster.local/health
```
**What this does:** calls the Service from inside the cluster, from a pod you are free to break.

**7. Delete the copy.**

```bash
kubectl delete pod debug-copy
```
**What this does:** removes it. A debug copy left behind consumes quota and confuses the next
person.

---

## Part 10 — Rollouts: watch one, stop one, undo one (8 min)

**1. See the strategy in force.**

```bash
kubectl get deployment paytrack-api -o jsonpath='{.spec.strategy.rollingUpdate}{"\n"}'
```
**What this does:** prints `{"maxSurge":1,"maxUnavailable":0}` — Lab 10's zero-downtime setting:
add one extra pod before removing any, and never drop below the desired count.

**2. Look at the revision history.**

```bash
kubectl rollout history deployment/paytrack-api
```
**What this does:** lists revisions. Each one is a ReplicaSet Kubernetes kept — which is what makes
`undo` instant.

**3. Start a rollout and watch the ReplicaSets move.**

```bash
kubectl set env deployment/paytrack-api ROLLOUT_TEST=$(date +%s)
```
**What this does:** `set env` changes an environment variable, which changes the pod template,
which starts a rollout. A harmless way to trigger one.

**4. Watch it happen.**

```bash
kubectl get rs -l app.kubernetes.io/name=paytrack-api --sort-by=.metadata.creationTimestamp
```
**What this does:** the new ReplicaSet scales up while the old one scales down. Run it two or three
times during the roll to see the numbers move — this is what a rolling update *is*.

**5. Pause one half-way.**

```bash
kubectl set image deployment/paytrack-api paytrack-api=ghcr.io/nobody/paytrack-api:definitely-missing && kubectl rollout pause deployment/paytrack-api
```
**What this does:** starts a bad rollout and immediately freezes it. `&&` runs the pause only if
the change succeeded. Nothing further will roll while it is paused.

**6. See the damage — and the lack of it.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** one broken pod; the three healthy ones still serving. This is the manual canary:
change, pause, look, then decide.

**7. Decide against it.**

```bash
kubectl rollout resume deployment/paytrack-api
```
**What this does:** unfreezes the deployment so the next command can act on it. (Undo on a paused
deployment does nothing until it is resumed.)

**8. Roll back.**

```bash
kubectl rollout undo deployment/paytrack-api
```
**What this does:** returns to the previous revision — seconds, versus minutes of pipeline.

**9. Confirm.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=90s
```
**What this does:** `successfully rolled out`.

**10. Read what a specific revision contained.**

```bash
kubectl rollout history deployment/paytrack-api --revision=$(kubectl get deployment paytrack-api -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
```
**What this does:** prints the pod template of the current revision — image, env, probes. Use it to
answer "what exactly was running at 02:14?".

**11. Put everything back to the committed state.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** re-applies the manifests from git, discarding every live patch from this lab —
including the `ROLLOUT_TEST` variable.

**12. Final check.**

```bash
kubectl get pods -l app.kubernetes.io/name=paytrack-api -o wide
```
**What this does:** three pods, `1/1`, `Running`, `RESTARTS 0`, spread across nodes. The cluster is
as Lab 11 expects it.

---

## The six failures, and the command that explains each

| Symptom | First command | What it tells you |
|---|---|---|
| `Pending` | `kubectl describe pod` | The scheduler's own reason — selectors, capacity, unbound PVC |
| `exceeded quota` at creation | `kubectl describe quota` | The object was never created; you are over the namespace budget |
| `ImagePullBackOff` | `kubectl describe pod \| grep -A5 Failed` | The registry's message and the exact image string tried |
| `CrashLoopBackOff` | `kubectl logs <pod> --previous` | What the dead container printed before exiting |
| `OOMKilled` / exit 137 | `kubectl describe pod \| grep -A6 "Last State"` | The kernel stopped it: the limit is too low, or it leaks |
| `Running` but `0/1` | `kubectl describe pod \| grep -A2 "probe failed"` | Readiness is failing — it is out of the Service, not crashed |
| Restarts on every pod at once | `kubectl get events \| grep -i liveness` | A liveness probe failing cluster-wide — usually a dependency |

---

## 🧩 Stretch (homework)

1. **Make the storm real.** Change the liveness probe to call `/ready` (which checks the database),
   then scale PostgreSQL to zero. Watch every API pod restart. Put it back and write the one-line
   rule you would give a colleague.
2. **`kubectl events --for`.** Run `kubectl events --for pod/<name> --watch` in a second terminal
   while you break something. Compare with `get events --sort-by`.
3. **`revisionHistoryLimit`.** Set it to `0`, do two rollouts, and try `rollout undo`. Explain what
   you lost, and pick the value you would use in production.
4. **Dry-run everything.** Compare `kubectl apply -f k8s/base/ --dry-run=client` with
   `--dry-run=server`. Only one of them catches a quota violation — find out which, and why.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `The connection to the server … was refused` | The cluster is stopped | `k3d cluster start paytrack`, wait 20 seconds |
| Every command says `namespace not found` | The context namespace was reset | `kubectl config set-context --current --namespace=paytrack-dev` |
| `$POD` or `$CRASHED` is empty | A new terminal window, or no pod matched | Run the box that sets it again, in the window you are using |
| `kubectl debug` says `unknown command` | kubectl older than 1.18 | `kubectl version --client`; update, or use the `--copy-to` form only |
| `error: unable to upgrade connection` on exec | The pod is not Running | `kubectl get pods` first — exec needs a live container |
| A patch says `path … does not exist` | The manifest differs from Lab 10's | `kubectl apply -f k8s/base/` and try again |
| Pods stay Pending after Part 3 | A leftover experiment is holding quota | `kubectl get pods`, delete anything not `paytrack-api`, check `describe quota` |
| netshoot will not pull | No network, or a restricted registry | Use `--image=busybox:1.36` — fewer tools, same mechanism |

---

## 🎯 Outcome

You have produced the six failures Kubernetes actually serves up, diagnosed each from the
cluster's own output rather than by guessing, put a shell into an image that has none, and used
`rollout pause`, `undo` and `history` — the three commands that turn a bad release into a
five-minute event.

**Next:** [Lab 11A — Access, Config and Storage in Depth](../lab-11-k8s-config-secrets-storage/README-11A-access-and-storage.md),
or carry on with [Lab 11](../lab-11-k8s-config-secrets-storage/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 8 is the one to demo.** Break liveness on the projector, wait, and let the room watch
  `RESTARTS` climb on all three pods at once. Then ask what would happen if the probe called the
  database — most rooms have a probe that does.
- **Part 7 is the most useful.** `READY 0/1` with `Running` is the state that produces "the
  service is down but the pods are fine" tickets. Make them run the endpointslices command.
- **Things that go wrong:**
  1. Delegates forget `--previous` and see an empty log from the container that is still starting.
  2. A patch fails because they edited `k8s/base/deployment.yaml` earlier — `kubectl apply -f
     k8s/base/` fixes it.
  3. Leftover `pending-demo` or `debug-copy` pods eat the namespace quota. Part 10 command 11 and
     the troubleshooting table cover it.
- **Debrief question:** "Your alert says the service is down. `kubectl get pods` shows three pods
  Running with zero restarts. What are your next two commands, and what are you hoping to rule
  out?"
</details>
