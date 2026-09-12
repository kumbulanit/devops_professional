# Lab 11 — Configuration, Secrets and Persistent Storage

| | |
|---|---|
| **Day** | 4 |
| **Duration** | 25 minutes |
| **Module** | 4 — Kubernetes for DevOps |
| **You will produce** | ConfigMap, Secret, and a PostgreSQL StatefulSet with a PVC — the API talking to a real database |
| **Feeds into** | Lab 12 (ingress & scaling), Lab 17 (replaces the Secret with a Sealed Secret) |

---

## Objective

Externalise every setting from the image, give PostgreSQL durable storage, connect the API to
it — and find out for yourself exactly how secure a Kubernetes Secret is.

## Prerequisites

- Lab 10 complete: `paytrack-api` running with 3 replicas in `paytrack-dev`

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev
kubectl apply -f k8s/base/ && kubectl rollout status deployment/paytrack-api
```

---

## Step 1 — ConfigMap: non-confidential configuration

```bash
cd ~/devops-course/paytrack-api-team
cat > k8s/base/configmap.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: paytrack-config
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
data:
  # Simple key/value pairs → consumed as environment variables
  APP_ENV: "dev"
  APP_COLOR: "blue"
  LOG_LEVEL: "INFO"
  READINESS_REQUIRES_DB: "true"
  DB_HOST: "postgres"          # the Kubernetes Service name for the database
  DB_PORT: "5432"
  DB_NAME: "paytrack"

  # A whole FILE, for when config is not key/value.
  # Mounted as a volume, this appears at <mountPath>/runtime.json
  runtime.json: |
    {
      "feature_flags": {
        "extended_metrics": true,
        "verbose_health": false
      },
      "limits": { "max_checks_per_request": 200 }
    }
EOF
kubectl apply -f k8s/base/configmap.yaml
kubectl get configmap paytrack-config -o yaml | head -20
```
**What this does:** creates a ConfigMap. Note the two shapes: **flat keys** become environment
variables, and a **key whose value is a file** (`runtime.json`, using YAML's `|` literal
block) becomes a file when mounted as a volume.

---

## Step 2 — Secret: and an honest look at how safe it is

```bash
kubectl create secret generic paytrack-db-secret \
  --namespace=paytrack-dev \
  --from-literal=POSTGRES_USER=paytrack \
  --from-literal=POSTGRES_PASSWORD='S3cur3-Cl4ss-Only!' \
  --dry-run=client -o yaml > /tmp/paytrack-db-secret.yaml
kubectl apply -f /tmp/paytrack-db-secret.yaml
```
**What this does:** `--dry-run=client -o yaml` generates the manifest **without creating
anything**, then `apply` creates it. Generating rather than hand-writing avoids base64
mistakes.

> 🔴 **`/tmp/paytrack-db-secret.yaml` contains the password in base64 and must never be
> committed.** In Lab 17 you will replace this with a Sealed Secret that *is* safe to commit.

```bash
kubectl get secret paytrack-db-secret -o yaml
```
**What this does:** shows the stored object. The values look encrypted. **They are not.**

```bash
kubectl get secret paytrack-db-secret -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d; echo
```
**What this does:** extracts the field with a JSONPath expression and decodes it. **The
password prints in plain text.**

> 🔴 **Say this out loud in the room.** Kubernetes Secrets are **base64-encoded, not
> encrypted**, in etcd by default. Anyone with `get secrets` RBAC in this namespace can read
> them; anyone who can create a pod here can mount them; anyone with etcd access reads all of
> them.
>
> What Secrets *do* give you over a ConfigMap: they are not shown in `kubectl describe`, they
> are mounted as **tmpfs** (RAM, never written to the node's disk), they are distributed only
> to nodes that need them, and they are separately controllable by RBAC.
>
> **Production fixes:** enable [encryption at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/),
> apply least-privilege RBAC, and keep secrets out of git with **Sealed Secrets**, **SOPS**,
> **External Secrets Operator** or **Vault**. Lab 17.

```bash
grep -q 'paytrack-db-secret.yaml' .gitignore || echo "**/paytrack-db-secret.yaml" >> .gitignore
```

---

## Step 3 — PostgreSQL as a StatefulSet with a PVC

```bash
cat > k8s/base/postgres.yaml <<'EOF'
---
# A HEADLESS service (clusterIP: None) gives each StatefulSet pod a stable DNS name:
#   postgres-0.postgres.paytrack-dev.svc.cluster.local
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: paytrack-dev
  labels: { app.kubernetes.io/name: postgres }
spec:
  clusterIP: None
  selector: { app.kubernetes.io/name: postgres }
  ports:
    - name: postgres
      port: 5432
      targetPort: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: paytrack-dev
  labels: { app.kubernetes.io/name: postgres }
spec:
  serviceName: postgres          # links the StatefulSet to the headless Service
  replicas: 1
  selector:
    matchLabels: { app.kubernetes.io/name: postgres }
  template:
    metadata:
      labels: { app.kubernetes.io/name: postgres }
    spec:
      securityContext:
        runAsNonRoot: true       # satisfies the 'restricted' Pod Security profile
        runAsUser: 999           # the postgres user inside the official image
        runAsGroup: 999
        fsGroup: 999             # makes the mounted volume group-writable by postgres
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - name: postgres
              containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: paytrack
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata    # a SUBDIRECTORY of the mount
            # Values injected from the Secret - never written in this file.
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef: { name: paytrack-db-secret, key: POSTGRES_USER }
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef: { name: paytrack-db-secret, key: POSTGRES_PASSWORD }
          readinessProbe:
            exec: { command: ["pg_isready", "-U", "paytrack", "-d", "paytrack"] }
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            exec: { command: ["pg_isready", "-U", "paytrack"] }
            initialDelaySeconds: 30
            periodSeconds: 15
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { cpu: 500m, memory: 512Mi }
          securityContext:
            allowPrivilegeEscalation: false
            capabilities: { drop: ["ALL"] }
            # NOTE: readOnlyRootFilesystem is deliberately NOT set here. Postgres
            # writes to /var/run/postgresql and /tmp; making it read-only needs extra
            # emptyDir mounts. Hardening a database is a real exercise, not a copy-paste.
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data

  # volumeClaimTemplates: each replica gets its OWN PVC, which survives rescheduling.
  # This is the defining feature of a StatefulSet and why databases use one.
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: local-path      # k3s/k3d default provisioner
        resources:
          requests:
            storage: 1Gi
EOF
kubectl apply -f k8s/base/postgres.yaml
kubectl rollout status statefulset/postgres --timeout=120s
```
**Why a StatefulSet and not a Deployment:**

| | Deployment | **StatefulSet** |
|---|---|---|
| Pod names | Random (`paytrack-api-7d4f-x9k2`) | **Ordinal and stable** (`postgres-0`) |
| Storage | Shared or none | **One PVC per replica**, reattached on reschedule |
| DNS | Via the Service VIP | **Per-pod DNS** through the headless Service |
| Ordering | Parallel | Ordered creation, scaling and deletion |

`PGDATA` points at a **subdirectory** of the mount because some volume drivers place a
`lost+found` at the mount root, which Postgres refuses to initialise into. A one-line fix for
a confusing failure.

> ⚠️ **`storageClassName: local-path` is k3s/k3d specific.** On any other cluster the PVC will
> sit `Pending` with `pod has unbound immediate PersistentVolumeClaims`. Check what you have
> with `kubectl get storageclass` and either use the name you find, or **delete the
> `storageClassName` line entirely** to take the cluster default — which is the portable
> choice. (Docker Desktop calls its class `hostpath`; EKS `gp2`/`gp3`; AKS `default`.)

```bash
kubectl get pvc,pv
```
**What this does:** shows the PersistentVolumeClaim (your **request**) `Bound` to a
dynamically created PersistentVolume (the **actual storage**), provisioned automatically by
the `local-path` StorageClass. Nobody had to pre-create storage — that is dynamic
provisioning (Module 4 §4.7).

✅ **Checkpoint**
```bash
kubectl exec postgres-0 -- pg_isready -U paytrack -d paytrack
```

---

## Step 4 — Wire the API to the ConfigMap, Secret and database

```bash
python3 - <<'PY'
import pathlib, re
p = pathlib.Path("k8s/base/deployment.yaml")
s = p.read_text()

new_env = '''          # ── Configuration: nothing hard-coded, everything injected ──
          envFrom:
            - configMapRef:
                name: paytrack-config          # every key becomes an env var
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef: { name: paytrack-db-secret, key: POSTGRES_USER }
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef: { name: paytrack-db-secret, key: POSTGRES_PASSWORD }
            - name: DATABASE_URL
              value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)"
            - name: POD_NAME
              valueFrom: { fieldRef: { fieldPath: metadata.name } }
            - name: NODE_NAME
              valueFrom: { fieldRef: { fieldPath: spec.nodeName } }
'''
# replace the whole existing env: block, up to the probes
s = re.sub(r'          env:\n(?:.*\n)*?\n          # .. PROBES', new_env + '\n          # ── PROBES', s)
s = s.replace('''          volumeMounts:
            - name: tmp
              mountPath: /tmp''',
'''          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: runtime-config
              mountPath: /etc/paytrack          # runtime.json appears here
              readOnly: true''')
s = s.replace('''      volumes:
        - name: tmp
          emptyDir: { sizeLimit: 64Mi }''',
'''      volumes:
        - name: tmp
          emptyDir: { sizeLimit: 64Mi }
        - name: runtime-config
          configMap:
            name: paytrack-config
            items:
              - key: runtime.json
                path: runtime.json''')
p.write_text(s)
print("deployment.yaml updated")
PY
grep -n 'envFrom\|DATABASE_URL\|runtime-config' k8s/base/deployment.yaml
```
**What this does:** rewrites the Deployment to take **all** configuration from outside the
image:

| Mechanism | What it demonstrates |
|---|---|
| `envFrom: configMapRef` | Every ConfigMap key becomes an environment variable — no per-key wiring |
| `secretKeyRef` | Individual secret values injected. **Never write the password in the manifest** |
| `$(VAR)` interpolation | Kubernetes substitutes **previously-defined** env vars, so `DATABASE_URL` is assembled at pod start from four separate sources |
| `configMap` **volume** | `runtime.json` becomes a real file at `/etc/paytrack/runtime.json` |

> **`env` vs volume — the difference that catches people.** Environment variables are **fixed
> at container start**; editing the ConfigMap does *not* change them until the pod restarts.
> A mounted **file** *is* updated (within ~1 minute) — if your application re-reads it. You
> will prove both in Step 6.

```bash
kubectl apply -f k8s/base/
kubectl rollout status deployment/paytrack-api --timeout=120s
```

✅ **Checkpoint — the one that matters**
```bash
kubectl port-forward service/paytrack-api 8888:80 >/dev/null 2>&1 &
sleep 3
curl -s localhost:8888/ready | jq
```
**Must report `{"status":"ready","store":"postgres"}`.** `postgres`, not `memory` — the API
built its connection string from a ConfigMap and a Secret and reached the database by
Service name.

```bash
curl -s -X POST localhost:8888/api/v1/authorisations -H 'Content-Type: application/json' \
  -d '{"merchant":"KUBERNETES LEDGER TEST","amount_minor":1500,"currency":"GBP","card_last4":"4242"}' | jq
curl -s localhost:8888/api/v1/authorisations | jq '.count'
kubectl exec postgres-0 -- psql -U paytrack -d paytrack -tAc "SELECT merchant FROM authorisations;"
```
**What this does:** writes through the API and reads directly from the database, proving the
whole path.

---

## Step 5 — Prove the storage is persistent

```bash
kubectl delete pod postgres-0
kubectl wait --for=condition=Ready pod/postgres-0 --timeout=120s
kubectl exec postgres-0 -- psql -U paytrack -d paytrack -tAc "SELECT count(*) FROM authorisations;"
```
**What this does:** deletes the database pod. The StatefulSet recreates it **with the same
name**, and the PVC is **reattached**. The row count is unchanged.

```bash
kubectl get pvc
```
**What this does:** shows the PVC still `Bound` — it outlived the pod entirely. That is the
whole point of a PersistentVolumeClaim.

> ⚠️ **Deleting a StatefulSet does *not* delete its PVCs** — deliberately, so you cannot
> destroy a database with one command. You must delete PVCs explicitly. And check the
> StorageClass's `reclaimPolicy`: with `Delete` (the default for dynamic provisioning), the
> underlying volume **is** destroyed when the PVC goes.

---

## Step 6 — Prove how config updates behave

```bash
kubectl exec deploy/paytrack-api -- printenv LOG_LEVEL
kubectl exec deploy/paytrack-api -- cat /etc/paytrack/runtime.json
```
**What this does:** shows the current values from both mechanisms.

```bash
kubectl patch configmap paytrack-config --type merge -p '{"data":{"LOG_LEVEL":"DEBUG","runtime.json":"{\"feature_flags\":{\"extended_metrics\":true,\"verbose_health\":true},\"limits\":{\"max_checks_per_request\":500}}"}}'
sleep 70
kubectl exec deploy/paytrack-api -- printenv LOG_LEVEL
kubectl exec deploy/paytrack-api -- cat /etc/paytrack/runtime.json
```
**What this does:** `patch --type merge` updates specific keys. After waiting for the kubelet
sync period:
- **`LOG_LEVEL` still prints `INFO`** — environment variables are frozen at container start.
- **`runtime.json` shows the new content** — mounted files *are* refreshed.

**The standard fix for env vars:**
```bash
kubectl rollout restart deployment/paytrack-api
kubectl rollout status deployment/paytrack-api --timeout=90s
kubectl exec deploy/paytrack-api -- printenv LOG_LEVEL
```
**What this does:** `rollout restart` performs a **rolling** restart with no spec change —
zero downtime, new pods pick up the new config. Now `DEBUG`.

> **In a pipeline**, add a hash of the ConfigMap as a pod-template annotation
> (`checksum/config: <sha>`). Changing the config then changes the pod template, which
> triggers a rollout automatically. Kustomize's `configMapGenerator` and Helm both do this
> for you.

---

## Step 7 — Restrict who can talk to the database

```bash
cat > k8s/base/networkpolicy.yaml <<'EOF'
---
# Default-deny INGRESS for the namespace. Nothing may receive traffic unless allowed.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: paytrack-dev
spec:
  podSelector: {}            # {} = every pod in the namespace
  policyTypes: [Ingress]
---
# Only paytrack-api pods may reach postgres, and only on 5432.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-allow-from-api
  namespace: paytrack-dev
spec:
  podSelector:
    matchLabels: { app.kubernetes.io/name: postgres }
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels: { app.kubernetes.io/name: paytrack-api }
      ports:
        - protocol: TCP
          port: 5432
---
# The API accepts HTTP from anywhere in the cluster (the Ingress controller lives elsewhere).
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow-http
  namespace: paytrack-dev
spec:
  podSelector:
    matchLabels: { app.kubernetes.io/name: paytrack-api }
  policyTypes: [Ingress]
  ingress:
    - ports:
        - protocol: TCP
          port: 8080
EOF
kubectl apply -f k8s/base/networkpolicy.yaml
kubectl get networkpolicy
```
**What this does:** **Kubernetes pod-to-pod traffic is completely unrestricted by default** —
any pod in any namespace can reach your database. These three policies establish
default-deny, then allow exactly what is needed.

> ⚠️ **NetworkPolicy requires a CNI that enforces it** (Calico, Cilium). k3s's default
> Flannel **does not**, so on this cluster the objects are accepted but not enforced. Write
> them anyway — they are correct, they are reviewed, and they take effect the moment the
> platform supports them. Say this plainly rather than letting delegates believe they are
> protected.

---

## Step 8 — Commit

```bash
git add k8s/base/ .gitignore
git commit -m "feat(k8s): externalise config, add Postgres StatefulSet and NetworkPolicy

- ConfigMap supplies env vars and a mounted runtime.json
- Secret supplies DB credentials; DATABASE_URL assembled via \$(VAR) at start
- Postgres runs as a StatefulSet with a 1Gi PVC that survives pod deletion
- default-deny ingress plus explicit allows for api→postgres and →api:8080

Note: the Secret manifest is git-ignored. Lab 17 replaces it with a
SealedSecret that is safe to commit."
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
curl -s localhost:8888/ready | jq -r '.store'       # → postgres
kubectl get pvc                                      # → Bound
kubectl get cm,secret,netpol
kubectl exec deploy/paytrack-api -- printenv | grep -c DB_    # → 3
kill %1 2>/dev/null
```

---

## 🧩 Stretch (homework)

1. **Immutable ConfigMaps.** Add `immutable: true`. The API server then refuses updates —
   which is a *feature*: you create `paytrack-config-v2` and roll forward, making config changes
   as versioned and revertable as code.
2. **Expand a PVC.** Change `storage: 1Gi` to `2Gi` and apply. Whether it works depends on
   the StorageClass's `allowVolumeExpansion`.
3. **Encryption at rest.** Read the Kubernetes `EncryptionConfiguration` docs and write down
   what you would need to change on a managed cluster.
4. **`reclaimPolicy: Retain`.** Create a StorageClass with it, and explain what changes when
   a PVC is deleted.

---

## 🎯 Outcome

Configuration and secrets fully externalised; PostgreSQL running on durable storage that
survives pod deletion; the API reaching it by Service name with a connection string assembled
at runtime; network policy written; and an accurate, evidence-based understanding of what a
Kubernetes Secret does and does not protect.

**Next:** [Lab 12 — Ingress and Autoscaling](../lab-12-k8s-ingress-scaling/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Step 2's `base64 -d` is the moment of the lab.** Decode the password on the projector.
  Expect at least one delegate to say "we store production credentials like that."
- **The three things that go wrong:**
  1. Postgres will not initialise because `PGDATA` was left at the mount root. The
     subdirectory is in the manifest — flag it if anyone hand-types it.
  2. `/ready` reports `memory` — `DATABASE_URL` did not resolve. Check
     `kubectl exec deploy/paytrack-api -- printenv DATABASE_URL`.
  3. Step 6 takes 60+ seconds and people conclude it failed. Warn them about the kubelet
     sync period before they start.
- **Be explicit about NetworkPolicy not being enforced by Flannel.** Delegates who miss this
  will go home believing their k3s cluster is segmented.
- **Debrief question:** "Where do your production database credentials live right now, and
  who can read them? List every place — the answer is usually longer than expected."
</details>
