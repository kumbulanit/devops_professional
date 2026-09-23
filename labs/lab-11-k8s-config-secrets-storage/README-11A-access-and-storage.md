# Lab 11A — Access, Config and Storage in Depth

| | |
|---|---|
| **Day** | 4 — **optional**, after class or as homework |
| **Duration** | About 70 minutes, in nine parts |
| **Module** | 4 — Kubernetes (the Day 4 *Going Further* slides, section B) |
| **Slides** | `Lab11A_Advanced_Access_and_Storage.pptx` — in this folder, 8 slides, read it first |
| **Parent lab** | [Lab 11 — Configuration, Secrets and Persistent Storage](README.md) |
| **You will produce** | A ServiceAccount with exactly the rights it needs, an egress policy that does not break DNS, and a config change you can prove reached the process |
| **Feeds into** | Nothing. Everything you add here, you remove |

---

## Objective

Lab 11 created a ConfigMap, a Secret, a StatefulSet with storage, and an **ingress** NetworkPolicy.
This lab takes the other three steps that separate a demo namespace from one an auditor would
accept:

- **Who can do what** — a ServiceAccount, a Role, a RoleBinding, and the one command that proves
  it, rather than a YAML file that claims it.
- **Egress** — deny outbound traffic by default, watch it take the application down, and then
  allow exactly what it needs. Including DNS, which is the part everyone forgets.
- **Config and storage that behave the way you assumed** — why a ConfigMap change did nothing,
  what `ReadWriteOnce` really means, and what happens to a volume when you delete its workload.

## Prerequisites

- **Labs 09, 10 and 11 complete** — the `paytrack-dev` namespace has `deployment/paytrack-api`,
  `statefulset/postgres`, `configmap/paytrack-config` and `secret/paytrack-db-secret`
- **Docker running** (k3d runs Kubernetes inside containers)

---

## Before you start — how to run the commands

Every instruction is **one command in one grey box**, numbered in the order you run it.

| Question | Answer |
|---|---|
| **How do I run a command?** | Click into the terminal, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait for the prompt. |
| **Some steps break the app on purpose** | Each part says so, and ends by putting it back. |
| **A command is waiting** | `rollout status` and `-w` watch until something changes; `Ctrl` + `C` stops watching without changing anything. |
| **The last line is `:` or `(END)`** | A scrollable view. Press `q`. |

**Symbols:** `|` passes output on · `$(…)` runs a command first and uses its answer · `\` means the
command continues on the next line — copy every line · a box beginning `cat <<'EOF' | kubectl
apply -f -` is **one** command that feeds a manifest straight to the cluster.

🔁 **RECOVER — put the namespace back at any time**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project.

```bash
kubectl apply -f k8s/base/
```
**What this does:** re-applies the committed manifests. Objects this lab *adds* are removed
explicitly in Part 9 — `apply` does not delete what is not in the folder.

---

## Part 1 — Cluster, namespace, starting state (5 min)

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command runs from here.

**2. Start the cluster if it is stopped.**

```bash
k3d cluster start paytrack 2>/dev/null || k3d cluster create --config k8s/k3d-cluster.yaml
```
**What this does:** starts the existing cluster, or creates it from Lab 09's file.

**3. Select the namespace.**

```bash
kubectl config set-context --current --namespace=paytrack-dev
```
**What this does:** saves typing `-n paytrack-dev` on every command.

**4. Make sure everything from Lab 11 is applied.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** Deployment, Service, ConfigMap, StatefulSet, NetworkPolicies — all from git.

**5. Wait for the application.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits until the API is available.

**6. Check the database is up too.**

```bash
kubectl get pods,pvc
```
**What this does:** lists pods and persistent volume claims in one command. Expect
`postgres-0` `Running` and a PVC in state `Bound`.

---

## Part 2 — Who can do what: RBAC in four objects (10 min)

**1. Create an identity for a deployment robot.**

```bash
kubectl create serviceaccount deploy-bot
```
**What this does:** a **ServiceAccount** is an identity for software, as a user account is for a
person. On its own it can do almost nothing — which is the right starting point.

**2. Prove it can do nothing useful yet.**

```bash
kubectl auth can-i list pods --as=system:serviceaccount:paytrack-dev:deploy-bot
```
**What this does:** asks the API server whether that identity may list pods. It answers **`no`**.
`--as` is impersonation — you are asking on the robot's behalf, not granting anything.

**3. Create a role that can read pods and their logs.**

```bash
kubectl create role pod-reader --verb=get,list,watch --resource=pods,pods/log
```
**What this does:** a **Role** is a set of permissions inside one namespace. It grants nothing by
itself — it is a definition waiting to be attached to somebody.

**4. Attach the role to the robot.**

```bash
kubectl create rolebinding deploy-bot-reads-pods --role=pod-reader --serviceaccount=paytrack-dev:deploy-bot
```
**What this does:** a **RoleBinding** ties a subject (the ServiceAccount) to a Role. This is the
object that actually grants access.

**5. Ask again.**

```bash
kubectl auth can-i list pods --as=system:serviceaccount:paytrack-dev:deploy-bot
```
**What this does:** now **`yes`**. Two objects, one grant, and a command that proves it.

**6. Check it cannot do more than you meant.**

```bash
kubectl auth can-i delete deployments --as=system:serviceaccount:paytrack-dev:deploy-bot
```
**What this does:** **`no`**. Least privilege is not a claim in a policy document — it is this
output.

**7. Check it cannot read secrets.**

```bash
kubectl auth can-i get secrets --as=system:serviceaccount:paytrack-dev:deploy-bot
```
**What this does:** **`no`**. Remember this answer — Part 3 asks the same question about a
different identity.

**8. List everything that identity may do.**

```bash
kubectl auth can-i --list --as=system:serviceaccount:paytrack-dev:deploy-bot | head -12
```
**What this does:** prints every permission the identity holds, including the handful every account
gets. This is the output to paste into an access review.

**9. See who else is bound in this namespace.**

```bash
kubectl get rolebindings -o custom-columns='NAME:.metadata.name,ROLE:.roleRef.name,SUBJECTS:.subjects[*].name'
```
**What this does:** `-o custom-columns` builds a small table from chosen fields. It answers "who
has rights here?" in one line each.

---

## Part 3 — What a Secret actually protects (8 min)

**1. Read the secret as you — the cluster admin.**

```bash
kubectl get secret paytrack-db-secret -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo
```
**What this does:** prints the database password in clear text. `base64 -d` decodes it, because a
Secret's values are **encoded, not encrypted**. The `; echo` just adds a line break.

**2. Ask whether an ordinary namespace identity could do that.**

```bash
kubectl auth can-i get secrets --as=system:serviceaccount:paytrack-dev:default
```
**What this does:** the `default` ServiceAccount — the one every pod gets unless told otherwise —
answers **`no`** here, because nothing granted it that. **RBAC, not encoding, is what protects a
Secret.**

**3. Grant read access, the way a careless change would.**

```bash
kubectl create role secret-reader --verb=get,list --resource=secrets
```
**What this does:** creates a role that can read every Secret in the namespace.

**4. Bind it to the robot.**

```bash
kubectl create rolebinding deploy-bot-reads-secrets --role=secret-reader --serviceaccount=paytrack-dev:deploy-bot
```
**What this does:** attaches it — the sort of change that arrives in a pull request titled "fix
deploy permissions".

**5. See the consequence.**

```bash
kubectl auth can-i get secrets --as=system:serviceaccount:paytrack-dev:deploy-bot
```
**What this does:** now **`yes`** — and since anything that can `get` a Secret can decode it, that
robot now has the database password.

**6. Take it away again.**

```bash
kubectl delete rolebinding deploy-bot-reads-secrets
```
**What this does:** removes the grant. The Role still exists but binds to nobody.

**7. Check which pods mount a token at all.**

```bash
kubectl get pods -o custom-columns='POD:.metadata.name,SA:.spec.serviceAccountName,AUTOMOUNT:.spec.automountServiceAccountToken'
```
**What this does:** shows which ServiceAccount each pod runs as and whether its API token is
mounted. `<none>` under AUTOMOUNT means the default — **mounted**. An application that never calls
the Kubernetes API should set `automountServiceAccountToken: false`.

> 🔑 **The honest summary.** A Secret keeps a credential out of the image and out of the workload
> manifest. Beyond that it is base64 in etcd, and everything depends on **RBAC**, on encryption at
> rest being enabled, and on who can read your etcd backups. Lab 17 adds Sealed Secrets so the
> encrypted form is the thing you commit.

---

## Part 4 — Deny egress, then allow exactly what is needed (12 min)

Lab 11 denied **inbound** traffic by default. Outbound is still wide open: a compromised pod can
reach anything in the cluster and anything on the internet.

**1. Prove outbound is open right now.**

```bash
kubectl run egress-test --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl -s -m 5 -o /dev/null -w "outbound to the internet: %{http_code}\n" https://example.com
```
**What this does:** runs a throw-away pod that calls a site on the internet. You get `200` — any
pod in this namespace can reach the outside world.

**2. Deny all egress for the namespace.** One command — copy the whole box:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: paytrack-dev
spec:
  podSelector: {}            # every pod in the namespace
  policyTypes: [Egress]      # with no egress rules = deny all outbound
EOF
```
**What this does:** `cat <<'EOF' | kubectl apply -f -` feeds a manifest straight to the cluster
without writing a file. `podSelector: {}` means every pod; listing `Egress` with no rules denies
all of it.

**3. Prove the internet is now unreachable.**

```bash
kubectl run egress-test --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl -s -m 5 -o /dev/null -w "outbound now: %{http_code}\n" https://example.com
```
**What this does:** prints `000` after a five-second timeout — blocked.

**4. Now look at what you also broke.**

```bash
sleep 30 && kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** after half a minute the API pods go `READY 0/1`. They are Running, but their
readiness probe checks the database — and they can no longer reach it, **or even resolve its
name**.

**5. Confirm it is DNS as well as the database.**

```bash
kubectl run dns-test --rm -i --restart=Never --image=busybox:1.36 -- nslookup postgres.paytrack-dev.svc.cluster.local
```
**What this does:** DNS itself is network traffic — to CoreDNS in the `kube-system` namespace. With
egress denied, name resolution fails. **This is the mistake almost everyone makes on their first
egress policy.**

**6. Allow DNS, and only DNS, to the cluster's resolver.** One command:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: paytrack-dev
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels: { kubernetes.io/metadata.name: kube-system }
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
EOF
```
**What this does:** permits port 53, UDP and TCP, to pods in `kube-system` — where CoreDNS runs.
`kubernetes.io/metadata.name` is a label Kubernetes puts on every namespace automatically.

**7. Check DNS works again.**

```bash
kubectl run dns-test --rm -i --restart=Never --image=busybox:1.36 -- nslookup postgres.paytrack-dev.svc.cluster.local
```
**What this does:** the name resolves. The internet is still blocked — policies are **additive**,
and you have only allowed port 53.

**8. Allow the API to reach the database.** One command:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress-to-postgres
  namespace: paytrack-dev
spec:
  podSelector:
    matchLabels: { app.kubernetes.io/name: paytrack-api }
  policyTypes: [Egress]
  egress:
    - to:
        - podSelector:
            matchLabels: { app.kubernetes.io/name: postgres }
      ports:
        - { protocol: TCP, port: 5432 }
EOF
```
**What this does:** allows the API pods — and only them — to open connections to the database pods
on 5432, and nothing else.

**9. Watch the application come back.**

```bash
sleep 30 && kubectl get pods -l app.kubernetes.io/name=paytrack-api
```
**What this does:** `READY 1/1` again. The readiness probe can reach the database, so the pods
return to the Service.

**10. Confirm the internet is still closed.**

```bash
kubectl run egress-test --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl -s -m 5 -o /dev/null -w "outbound to the internet: %{http_code}\n" https://example.com
```
**What this does:** `000`. You now have a namespace that talks to its own database and its own DNS,
and to nothing else — the shape a payments service should have.

> 🔑 **Egress policy is how you stop data leaving.** Ingress rules stop people getting in; egress
> rules stop a compromised container calling home. Write them together, and always allow DNS
> deliberately.

---

## Part 5 — Why your ConfigMap change did nothing (10 min)

**1. See the value the application currently has.**

```bash
kubectl exec deployment/paytrack-api -- printenv LOG_LEVEL
```
**What this does:** runs `printenv` inside one of the pods and prints the current log level — `INFO`.

**2. Change it in the ConfigMap.**

```bash
kubectl patch configmap paytrack-config --type=merge -p '{"data":{"LOG_LEVEL":"DEBUG"}}'
```
**What this does:** `--type=merge` changes one key and leaves the rest alone. The ConfigMap now
says `DEBUG`.

**3. Confirm the ConfigMap really changed.**

```bash
kubectl get configmap paytrack-config -o jsonpath='{.data.LOG_LEVEL}{"\n"}'
```
**What this does:** prints `DEBUG`.

**4. Now ask the running application again.**

```bash
kubectl exec deployment/paytrack-api -- printenv LOG_LEVEL
```
**What this does:** still `INFO`. **Environment variables are read once, when the process starts.**
Nothing restarted, so nothing re-read the value. This is the single most common "my config change
did nothing" in Kubernetes.

**5. Make it take effect, deliberately.**

```bash
kubectl rollout restart deployment/paytrack-api
```
**What this does:** starts a rolling restart — new pods, which read the ConfigMap as they start.
The old ones keep serving until the new ones are ready.

**6. Wait for it.**

```bash
kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** waits for every pod to be replaced.

**7. Confirm the new value arrived.**

```bash
kubectl exec deployment/paytrack-api -- printenv LOG_LEVEL
```
**What this does:** `DEBUG`.

**8. Make the ConfigMap unchangeable.**

```bash
kubectl patch configmap paytrack-config --type=merge -p '{"immutable":true}'
```
**What this does:** marks it immutable. The kubelet then stops watching it, which reduces load on
the API server — and, more usefully, makes "someone edited config in place" impossible.

**9. Prove it.** This fails on purpose.

```bash
kubectl patch configmap paytrack-config --type=merge -p '{"data":{"LOG_LEVEL":"WARNING"}}'
```
**What this does:** the API server refuses: `field is immutable`. With immutable config, a change
means a **new** ConfigMap and a deliberate rollout — which is exactly the audit trail you want.

**10. Put it back.**

```bash
kubectl delete configmap paytrack-config && kubectl apply -f k8s/base/configmap.yaml
```
**What this does:** an immutable ConfigMap cannot be edited back, so you delete and re-apply the
committed version. `&&` runs the apply only if the delete succeeded.

**11. Restore the running value.**

```bash
kubectl rollout restart deployment/paytrack-api && kubectl rollout status deployment/paytrack-api --timeout=120s
```
**What this does:** rolls the pods so they pick up the committed `INFO` again.

> 🔑 **Three ways config reaches a process, and how each behaves.** `env:` — read once, needs a
> restart. A **mounted** ConfigMap — the file updates in place after a minute or two, *unless* you
> used `subPath`, in which case it never updates. A **checksum annotation** on the pod template —
> changes the template, so Kubernetes rolls the pods for you. Pick one deliberately.

---

## Part 6 — Storage: what the fields actually promise (8 min)

**1. Look at the storage class the cluster uses.**

```bash
kubectl get storageclass
```
**What this does:** k3s ships `local-path` as the default (marked `(default)`). It writes data to a
directory on the node the pod landed on.

**2. Ask whether volumes can be grown.**

```bash
kubectl get storageclass local-path -o jsonpath='allowVolumeExpansion: {.allowVolumeExpansion}{"\n"}'
```
**What this does:** prints an empty value — meaning **false**. On this class, a PVC cannot be
resized. **Check this before you promise anyone you can grow a volume**; on a cloud class it is
usually `true`.

**3. Look at the claim the database is using.**

```bash
kubectl get pvc -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,CAPACITY:.status.capacity.storage,MODE:.spec.accessModes[0],CLASS:.spec.storageClassName'
```
**What this does:** one line per claim: its size, its access mode (`ReadWriteOnce`) and its class.

**4. See what `ReadWriteOnce` really means.**

```bash
kubectl get pv -o custom-columns='NAME:.metadata.name,RECLAIM:.spec.persistentVolumeReclaimPolicy,CLAIM:.spec.claimRef.name,NODE:.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]'
```
**What this does:** shows the underlying volume, its **reclaim policy**, and — for `local-path` —
the node it is pinned to. `ReadWriteOnce` means one **node**, not one pod: a second replica
scheduled elsewhere would never start.

**5. Find where the data physically is.**

```bash
kubectl get pv -o jsonpath='{.items[0].spec.hostPath.path}{"\n"}'
```
**What this does:** prints a path inside the k3d node container. That is the whole promise of
`local-path`: fast, simple, and **gone if that node goes**. It is a lab storage class, not a
production one.

**6. Prove the data survives the pod.**

```bash
kubectl exec postgres-0 -- psql -U paytrack -d paytrack -c "CREATE TABLE IF NOT EXISTS survives (id int); INSERT INTO survives VALUES (1);"
```
**What this does:** writes a row into a new table inside the database.

**7. Delete the database pod.**

```bash
kubectl delete pod postgres-0
```
**What this does:** the StatefulSet immediately creates a replacement with the **same name** and
**the same PVC** — that is what a StatefulSet guarantees.

**8. Wait for it.**

```bash
kubectl rollout status statefulset/postgres --timeout=120s
```
**What this does:** waits until `postgres-0` is ready again.

**9. Check the row is still there.**

```bash
kubectl exec postgres-0 -- psql -U paytrack -d paytrack -c "SELECT count(*) FROM survives;"
```
**What this does:** prints `1`. The pod was replaced; the volume was not.

**10. See what would happen if you deleted the StatefulSet.**

```bash
kubectl get pvc -l app.kubernetes.io/name=postgres -o name
```
**What this does:** lists the claim. **Deleting a StatefulSet does not delete its PVCs** — they
outlive it deliberately, so a mistaken `delete` does not destroy the data. It also means orphaned
volumes accumulate and are billed for; clean them up on purpose.

---

## Part 7 — Prove the whole thing still works (4 min)

**1. Check every pod.**

```bash
kubectl get pods -o wide
```
**What this does:** API pods `1/1 Running`, `postgres-0` `1/1 Running`.

**2. Call the service from inside the cluster.**

```bash
kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- curl -s -m 5 http://paytrack-api.paytrack-dev.svc.cluster.local/ready
```
**What this does:** the readiness endpoint, which checks the database. A JSON answer means the
egress policy you wrote permits exactly what the application needs — no more, no less.

---

## Part 8 — Tidy up the identities (3 min)

**1. Remove the binding.**

```bash
kubectl delete rolebinding deploy-bot-reads-pods
```
**What this does:** removes the grant.

**2. Remove the roles.**

```bash
kubectl delete role pod-reader secret-reader
```
**What this does:** deletes both definitions.

**3. Remove the ServiceAccount.**

```bash
kubectl delete serviceaccount deploy-bot
```
**What this does:** removes the identity. In a real cluster these three objects would be committed
to git and applied by CI, not typed — but knowing what each one does is the point of Part 2.

---

## Part 9 — Leave the namespace as Lab 12 expects it (4 min)

The egress policies you wrote are correct — but Lab 12 assumes Lab 11's networking, so remove them
here and add them back deliberately if you keep the cluster.

**1. Delete the three egress policies.**

```bash
kubectl delete networkpolicy default-deny-egress allow-dns-egress api-egress-to-postgres
```
**What this does:** removes only what this lab added. Lab 11's ingress policies stay.

**2. Confirm what is left.**

```bash
kubectl get networkpolicy
```
**What this does:** the three from Lab 11 — `default-deny-ingress`, `postgres-allow-from-api`,
`api-allow-http`.

**3. Re-apply the committed manifests.**

```bash
kubectl apply -f k8s/base/
```
**What this does:** puts any object you patched back to the version in git.

**4. Final check.**

```bash
kubectl get pods,pvc,networkpolicy
```
**What this does:** everything Running and Bound, three policies. Lab 12 can start.

---

## What you proved

| Claim | The command that settles it |
|---|---|
| "This robot can only read pods" | `kubectl auth can-i --list --as=system:serviceaccount:…` |
| "Secrets are safe" | `kubectl get secret … -o jsonpath=… \| base64 -d` — then check who has `get` |
| "Nothing can call out of the namespace" | A `curl` pod after `default-deny-egress` |
| "The config change is live" | `kubectl exec deployment/… -- printenv` |
| "The volume can be grown" | `kubectl get storageclass … -o jsonpath='{.allowVolumeExpansion}'` |
| "The data survives" | Delete the pod; read the row back |

---

## 🧩 Stretch (homework)

1. **A CI robot for real.** Write `k8s/rbac/deploy-bot.yaml` containing the ServiceAccount, a Role
   limited to `deployments` with `get,list,patch`, and a RoleBinding. Commit it, apply it, and
   prove with `auth can-i` that it can roll the API but not read a Secret.
2. **The checksum annotation.** Add `checksum/config` to the pod template, set it from
   `kubectl get configmap paytrack-config -o yaml | sha256sum`, and confirm that changing the
   ConfigMap now rolls the pods on its own.
3. **Mounted config.** Mount the ConfigMap as files instead of env vars, change a value, and time
   how long until the file inside the pod updates. Then do it again with `subPath` and explain the
   difference.
4. **Encryption at rest.** Read the Kubernetes `EncryptionConfiguration` docs and write down, in
   two sentences, what it would change about Part 3 — and what it would not.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `The connection to the server … was refused` | The cluster is stopped | `k3d cluster start paytrack` |
| Everything says `namespace not found` | The context namespace was reset | `kubectl config set-context --current --namespace=paytrack-dev` |
| The API never returns to `1/1` in Part 4 | An egress rule is missing or mislabelled | `kubectl describe networkpolicy api-egress-to-postgres`; check the pod labels match |
| `nslookup` still fails after the DNS policy | Your CoreDNS is not in `kube-system` | `kubectl get pods -A -l k8s-app=kube-dns -o wide` and use that namespace |
| `error: field is immutable` | That is Part 5 command 9 | Delete and re-apply — command 10 |
| `pod has unbound immediate PersistentVolumeClaims` | No default StorageClass | `kubectl get sc`; k3s should show `local-path (default)` |
| `auth can-i` always says `yes` | You forgot `--as` and are asking about yourself | Include the full `system:serviceaccount:<ns>:<name>` |
| Pods stay `0/1` after Part 9 | A policy from this lab is still applied | `kubectl get networkpolicy` — only Lab 11's three should remain |

---

## 🎯 Outcome

You can grant an identity exactly the rights it needs and **prove** the limits, explain precisely
what a Kubernetes Secret does and does not protect, write an egress policy that closes the
namespace without breaking DNS, make a configuration change actually reach a running process, and
read what a StorageClass, an access mode and a reclaim policy really promise.

**Next:** [Lab 12A — Scaling, Scheduling and Disruption](../lab-12-k8s-ingress-scaling/README-12A-scaling-and-scheduling.md),
or carry on with [Lab 12](../lab-12-k8s-ingress-scaling/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 4 is the lab.** Applying `default-deny-egress` and watching the application fall over —
  because DNS is egress — is the moment the room understands NetworkPolicy. Do it live.
- **Part 3 command 5** is worth pausing on: one RoleBinding in a pull request is all it takes to
  hand a robot the database password. Ask who reviews RBAC changes in their organisation.
- **Things that go wrong:**
  1. Delegates apply the egress policy and then wander off; the API stays `0/1` and they think they
     broke the cluster. Say up front that Part 4 restores it.
  2. `auth can-i` without `--as` answers for the admin and always says yes.
  3. Someone skips Part 9 and Lab 12's ingress traffic behaves oddly. The final check catches it.
- **Debrief question:** "Your namespace denies all ingress. A compromised pod still exfiltrates
  data. Which policy was missing, and which port would you have had to allow anyway?"
</details>
