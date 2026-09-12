# Lab 13 — Provision the Platform with Terraform

| | |
|---|---|
| **Day** | 5 |
| **Duration** | 37 minutes |
| **Module** | 5 — Infrastructure as Code |
| **You will produce** | A `terraform/` tree with a reusable module that provisions the whole `paytrack-prod` environment |
| **Feeds into** | Lab 15 (the pipeline deploys into what Terraform created), Lab 19 (capstone rebuilds from here) |

---

## Objective

Everything you built by hand in Labs 09–12 becomes **code**: reviewed, versioned, planned
before it is applied, and reproducible. You will write a module, instantiate it twice with
different variables, deliberately create configuration drift and detect it, and read a
destructive plan before it destroys anything.

**No cloud account and no cost.** The `kubernetes` and `docker` providers target your local
cluster and daemon, and every Terraform concept — providers, resources, state, locking,
variables, outputs, modules, drift, `plan`/`apply`/`destroy` — is identical to how you would
use AWS or Azure.

> **Licence.** Terraform is BUSL-licensed and free for this use. **OpenTofu** is the
> MPL-licensed fork: substitute `tofu` for `terraform` in every command below and everything
> works.

## Prerequisites

- Lab 09 (cluster) and Labs 10–12 (`paytrack-dev` running)

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev
kubectl apply -f k8s/base/
```

---

## Step 1 — Why we target `paytrack-prod`

`paytrack-dev` is managed by `kubectl apply`. Terraform will manage a **separate** namespace,
`paytrack-prod`. That is deliberate on two counts:

1. **Two tools must never manage the same resource.** They will fight, and the state file
   will disagree with reality.
2. It mirrors a real progression: an environment created by hand, then a properly codified
   one alongside it.

```bash
cd ~/devops-course/paytrack-api-team
mkdir -p terraform/modules/paytrack-environment
```

---

## Step 2 — Providers and the root module

```bash
cat > terraform/versions.tf <<'EOF'
terraform {
  # PIN EVERYTHING. An unpinned provider release can change your infrastructure
  # on a Tuesday morning without anyone changing a line of code.
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"          # >= 2.32.0, < 3.0.0
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }

  # BACKEND: where state lives.
  # Local is fine for this lab. For anything shared, use a remote backend with LOCKING:
  #
  #   backend "s3" {
  #     bucket         = "acme-tfstate"
  #     key            = "paytrack/prod/terraform.tfstate"
  #     region         = "eu-west-1"
  #     dynamodb_table = "tfstate-locks"   # <- the LOCK. Two concurrent applies
  #     encrypt        = true              #    against one state WILL corrupt it.
  #   }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "k3d-paytrack"     # EXPLICIT. Never let Terraform inherit whatever
}                                  # context you happened to be on.

provider "docker" {
  host = "unix:///var/run/docker.sock"
}
EOF
```
**What this does:** declares required versions, the providers, and (in comments) the remote
backend you would use in production.

> 🔴 **`config_context = "k3d-paytrack"` is not optional pedantry.** Without it, Terraform uses
> your *current* kubeconfig context. Switch context, run `terraform apply`, and you have just
> applied a dev plan to another cluster. Pin it.

```bash
cat > terraform/variables.tf <<'EOF'
variable "environment" {
  description = "Environment name; used as the namespace suffix"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "image" {
  description = "Fully-qualified container image for PayTrack API"
  type        = string
  default     = "paytrack-api:1.0.0"
}

variable "replica_count" {
  description = "Number of PayTrack API replicas"
  type        = number
  default     = 2

  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 20
    error_message = "replica_count must be between 1 and 20."
  }
}

variable "app_color" {
  description = "Banner colour: blue | green | canary"
  type        = string
  default     = "green"
}

variable "resource_limits" {
  description = "Per-pod resource requests and limits"
  type = object({
    cpu_request    = string
    memory_request = string
    cpu_limit      = string
    memory_limit   = string
  })
  default = {
    cpu_request    = "50m"
    memory_request = "64Mi"
    cpu_limit      = "300m"
    memory_limit   = "192Mi"
  }
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true          # masked in CLI output. NOT encrypted in state.
  default     = "prod-lab-only-change-me"
}
EOF
```
**What the variable features do:**

| Feature | Purpose |
|---|---|
| `type` | `string`, `number`, `bool`, `list()`, `map()`, `object({...})`. Catches errors at plan time |
| `validation` | Rejects bad input **with your own error message**, before anything is created |
| `sensitive = true` | Masks the value in CLI output and plans. ⚠️ **It is still plaintext in the state file** |
| `default` | Makes the variable optional |

**Precedence, lowest to highest:** `default` → `terraform.tfvars` → `*.auto.tfvars` →
`-var-file=` → `-var=` → `TF_VAR_name` environment variable.

---

## Step 3 — Write the module

```bash
cat > terraform/modules/paytrack-environment/variables.tf <<'EOF'
variable "environment"     { type = string }
variable "image"           { type = string }
variable "replica_count"   { type = number }
variable "app_color"       { type = string }
variable "db_password" {
  type      = string
  sensitive = true
}
variable "resource_limits" {
  type = object({
    cpu_request    = string
    memory_request = string
    cpu_limit      = string
    memory_limit   = string
  })
}
variable "quota_cpu" {
  type    = string
  default = "4"
}
variable "quota_memory" {
  type    = string
  default = "4Gi"
}
EOF
```

```bash
cat > terraform/modules/paytrack-environment/main.tf <<'EOF'
# ═══════════════════════════════════════════════════════════════════════════
#  Reusable module: one complete PayTrack environment.
#  Instantiate it once per environment; the ONLY differences are the inputs.
# ═══════════════════════════════════════════════════════════════════════════

locals {
  namespace = "paytrack-${var.environment}"

  # Standard Kubernetes recommended labels, defined ONCE and reused everywhere.
  labels = {
    "app.kubernetes.io/name"       = "paytrack-api"
    "app.kubernetes.io/part-of"    = "paytrack"
    "app.kubernetes.io/managed-by" = "terraform"
    "environment"                  = var.environment
  }
}

resource "kubernetes_namespace" "this" {
  metadata {
    name = local.namespace
    labels = merge(local.labels, {
      "pod-security.kubernetes.io/enforce" = "baseline"
      "pod-security.kubernetes.io/warn"    = "restricted"
    })
  }
}

resource "kubernetes_resource_quota" "this" {
  metadata {
    name      = "${local.namespace}-quota"
    namespace = kubernetes_namespace.this.metadata[0].name
    # ↑ Referencing the namespace resource creates an IMPLICIT DEPENDENCY.
    #   Terraform builds its graph from these references - you almost never
    #   need depends_on.
  }
  spec {
    hard = {
      "requests.cpu"    = var.quota_cpu
      "requests.memory" = var.quota_memory
      "limits.cpu"      = var.quota_cpu
      "limits.memory"   = var.quota_memory
      "pods"            = "20"
    }
  }
}

resource "kubernetes_secret" "db" {
  metadata {
    name      = "paytrack-db-secret"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = local.labels
  }
  data = {
    POSTGRES_USER     = "paytrack"
    POSTGRES_PASSWORD = var.db_password
  }
  type = "Opaque"
}

resource "kubernetes_config_map" "app" {
  metadata {
    name      = "paytrack-config"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = local.labels
  }
  data = {
    APP_ENV               = var.environment
    APP_COLOR             = var.app_color
    LOG_LEVEL             = var.environment == "prod" ? "WARNING" : "DEBUG"
    READINESS_REQUIRES_DB = "false"
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "paytrack-api"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = local.labels
  }

  spec {
    replicas = var.replica_count

    selector {
      match_labels = { "app.kubernetes.io/name" = "paytrack-api" }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_surge       = 1
        max_unavailable = 0
      }
    }

    template {
      metadata {
        labels = local.labels
        annotations = {
          # Hash the ConfigMap into the pod template: changing config then changes
          # the template, which triggers a rollout automatically.
          "checksum/config" = sha256(jsonencode(kubernetes_config_map.app.data))
        }
      }

      spec {
        security_context {
          run_as_non_root = true
          run_as_user     = 10001
          fs_group        = 10001
        }

        container {
          name              = "paytrack-api"
          image             = var.image
          image_pull_policy = "IfNotPresent"

          port {
            name           = "http"
            container_port = 8080
          }

          env_from {
            config_map_ref { name = kubernetes_config_map.app.metadata[0].name }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = "http"
            }
            period_seconds        = 10
            failure_threshold     = 3
            initial_delay_seconds = 10
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = "http"
            }
            period_seconds    = 5
            failure_threshold = 2
          }

          resources {
            requests = {
              cpu    = var.resource_limits.cpu_request
              memory = var.resource_limits.memory_request
            }
            limits = {
              cpu    = var.resource_limits.cpu_limit
              memory = var.resource_limits.memory_limit
            }
          }

          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities { drop = ["ALL"] }
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }
        }

        volume {
          name = "tmp"
          empty_dir { size_limit = "64Mi" }
        }
      }
    }
  }

  # Wait for the rollout to complete before Terraform reports success.
  wait_for_rollout = true
}

resource "kubernetes_service" "api" {
  metadata {
    name      = "paytrack-api"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = local.labels
  }
  spec {
    selector = { "app.kubernetes.io/name" = "paytrack-api" }
    port {
      name        = "http"
      port        = 80
      target_port = "http"
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_ingress_v1" "api" {
  metadata {
    name      = "paytrack-api"
    namespace = kubernetes_namespace.this.metadata[0].name
    labels    = local.labels
  }
  spec {
    ingress_class_name = "traefik"
    rule {
      host = "${var.environment}.paytrack.localhost"
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.api.metadata[0].name
              port { number = 80 }
            }
          }
        }
      }
    }
  }
}
EOF
```
**The Terraform features on show:**

| Feature | Why it matters |
|---|---|
| `locals` | Compute once, reuse. `local.labels` guarantees every object is labelled consistently |
| `merge()` | Combines maps — base labels plus environment-specific ones |
| Resource references | `kubernetes_namespace.this.metadata[0].name` creates an **implicit dependency**; Terraform derives the whole ordering graph from these |
| Conditional expression | `var.environment == "prod" ? "WARNING" : "DEBUG"` — environment-specific behaviour without duplicating the module |
| `sha256(jsonencode(...))` | The config-checksum annotation. **Changing the ConfigMap triggers a rollout** — the pattern Module 4 §4.6 describes |
| `wait_for_rollout` | Terraform waits for pods to be Ready before declaring success, so a failed deploy fails the apply |

```bash
cat > terraform/modules/paytrack-environment/outputs.tf <<'EOF'
output "namespace" {
  description = "The namespace created for this environment"
  value       = kubernetes_namespace.this.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.api.metadata[0].name
}

output "url" {
  description = "Where to reach this environment"
  value       = "http://${var.environment}.paytrack.localhost:8080"
}

output "replica_count" {
  value = kubernetes_deployment.api.spec[0].replicas
}
EOF
```
**What this does:** outputs are a module's **return values** — how a caller consumes what the
module built, and how one module feeds another.

---

## Step 4 — Call the module

```bash
cat > terraform/main.tf <<'EOF'
# ── Production environment ────────────────────────────────────────────────
module "paytrack_prod" {
  source = "./modules/paytrack-environment"

  environment     = "prod"
  image           = var.image
  replica_count   = var.replica_count
  app_color       = var.app_color
  db_password     = var.db_password
  resource_limits = var.resource_limits
  quota_cpu       = "4"
  quota_memory    = "4Gi"
}

# ── Staging: THE SAME MODULE, different inputs. ───────────────────────────
# One reviewed definition, two environments that cannot silently diverge.
module "paytrack_staging" {
  source = "./modules/paytrack-environment"

  environment   = "staging"
  image         = var.image
  replica_count = 1
  app_color     = "canary"
  db_password   = var.db_password
  resource_limits = {
    cpu_request    = "25m"
    memory_request = "48Mi"
    cpu_limit      = "150m"
    memory_limit   = "128Mi"
  }
  quota_cpu    = "1"
  quota_memory = "1Gi"
}
EOF

cat > terraform/outputs.tf <<'EOF'
output "environments" {
  description = "Every environment this configuration manages"
  value = {
    prod = {
      namespace = module.paytrack_prod.namespace
      url       = module.paytrack_prod.url
      replicas  = module.paytrack_prod.replica_count
    }
    staging = {
      namespace = module.paytrack_staging.namespace
      url       = module.paytrack_staging.url
      replicas  = module.paytrack_staging.replica_count
    }
  }
}
EOF
```

```bash
cat > terraform/terraform.tfvars <<'EOF'
# Non-sensitive values for this workspace. Committed.
image         = "paytrack-api:1.0.0"
replica_count = 2
app_color     = "green"
EOF
cat >> .gitignore <<'EOF'

# Terraform
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.*
terraform/tfplan
terraform/*.auto.tfvars
terraform/crash.log
EOF
```
**What this does:** commits ordinary values in `terraform.tfvars`, and ignores state, plans,
the provider cache, and `*.auto.tfvars` (where secrets typically go).

---

## Step 5 — The workflow: init, validate, plan

```bash
cd terraform
terraform init
```
**What this does:** downloads the pinned providers into `.terraform/`, initialises the
backend, and writes `.terraform.lock.hcl` — a **lock file recording the exact provider
versions and their checksums**. **Commit the lock file**: it is what makes everyone's, and
CI's, builds identical.

```bash
terraform fmt -recursive
terraform validate
```
**What this does:** `fmt` rewrites files to canonical style (put it in CI as
`terraform fmt -check -recursive` so formatting is never reviewed by a human again).
`validate` checks syntax, types, and that every reference resolves — **without contacting any
API**.

```bash
terraform plan -out=tfplan
```
**What this does:** the most important command in this module. Terraform refreshes state,
compares desired against actual, and prints exactly what it would do — **changing nothing**.
`-out=tfplan` saves the plan so it can be applied verbatim.

**Read the output.** Learn these symbols:

| Symbol | Meaning |
|---|---|
| `+ create` | New resource |
| `~ update in-place` | Modified, no replacement |
| `-/+ destroy and then create replacement` | **⚠️ REPLACEMENT.** On a database this is data loss. Always investigate |
| `- destroy` | Removed |
| `<= read` | Data source read |

At the bottom: `Plan: 14 to add, 0 to change, 0 to destroy.`

> 🔑 **The professional workflow:** `plan` runs automatically on every pull request, its
> output is posted as a PR comment, a human reads it, and **only then** does CI run `apply`
> on the saved plan. Nobody runs `apply -auto-approve` from a laptop.

```bash
terraform apply tfplan
```
**What this does:** applies **exactly** the saved plan — no re-evaluation, no drift between
what you reviewed and what happens. (`terraform apply` with no plan file re-plans and prompts
for confirmation.)

✅ **Checkpoint**
```bash
terraform output
kubectl get ns | grep paytrack
kubectl get all -n paytrack-prod
kubectl get all -n paytrack-staging
```

```bash
grep -q 'prod.paytrack.localhost' /etc/hosts || \
  echo "127.0.0.1  prod.paytrack.localhost staging.paytrack.localhost" | sudo tee -a /etc/hosts
curl -s http://prod.paytrack.localhost:8080/api/v1/info | jq
curl -s http://staging.paytrack.localhost:8080/api/v1/info | jq
```
**What this does:** proves both environments are live. Note the **different colours and log
levels** — same module, different inputs.

---

## Step 6 — Examine the state file

```bash
terraform state list
terraform state show 'module.paytrack_prod.kubernetes_service.api'
```
**What this does:** lists every resource Terraform manages and shows one in detail —
including attributes computed by the API server, such as the allocated ClusterIP.

```bash
grep -o 'POSTGRES_PASSWORD[^,]*' terraform.tfstate | head -2
```
**What this does:** demonstrates the point that matters most.

> 🔴 **The database password is in the state file in plain text**, even though the variable
> is marked `sensitive = true`. `sensitive` only masks **CLI output**.
>
> Therefore: **never commit state**; use a remote backend with **encryption at rest**;
> restrict who can read the state bucket as tightly as you restrict production; and prefer
> secrets that Terraform never sees at all (a secret manager, or a Kubernetes operator that
> fetches them).

```bash
ls -la terraform.tfstate*
```
**What this does:** shows the state and its automatic `.backup`. With a local backend there
is **no locking** — two people running `apply` simultaneously corrupt it. That is why remote
backends with a lock table are mandatory for teams.

---

## Step 7 — Drift: create it, detect it, correct it

```bash
kubectl scale deployment/paytrack-api -n paytrack-prod --replicas=5
kubectl get deployment paytrack-api -n paytrack-prod
```
**What this does:** the classic "quick fix in production" — someone changed reality without
changing the code.

```bash
terraform plan
```
**What this does:** Terraform refreshes state, finds 5 replicas where the code says 2, and
reports:
```
  ~ resource "kubernetes_deployment" "api" {
      ~ replicas = 5 -> 2
    }
Plan: 0 to add, 1 to change, 0 to destroy.
```

> 🔑 **This is your drift detector.** Run `terraform plan -detailed-exitcode` on a schedule:
> it exits **0** for no changes, **2** for a non-empty plan, **1** for an error. Alert on
> exit code 2 and you will know within an hour of anyone touching production by hand.

```bash
terraform apply -auto-approve
kubectl get deployment paytrack-api -n paytrack-prod
```
**What this does:** reconciles reality back to the code. Back to 2 replicas.
**The manual change is gone** — which is exactly right, and exactly why "just this once" SSH
fixes are so damaging: they are silently reverted, usually at the worst moment.

---

## Step 8 — Change through code, and read a dangerous plan

```bash
sed -i 's/^replica_count = 2/replica_count = 4/' terraform.tfvars
sed -i 's/^app_color     = "green"/app_color     = "blue"/' terraform.tfvars
terraform plan
```
**What this does:** shows two changes: `~ replicas 2 -> 4` (in-place) and a ConfigMap update
which **changes the `checksum/config` annotation** and therefore triggers a rolling update.
That checksum pattern is the mechanism, seen working.

```bash
terraform apply -auto-approve
curl -s http://prod.paytrack.localhost:8080/api/v1/info | jq -r '.color'
kubectl get pods -n paytrack-prod
```

**Now read a destructive plan without executing it:**
```bash
terraform plan -destroy | tail -20
```
**What this does:** shows exactly what `terraform destroy` would remove. **Read a destroy
plan every single time** — this is where you notice it is about to take a namespace, a
database or a load balancer you did not intend.

For genuinely important resources, add a lifecycle guard:
```
lifecycle { prevent_destroy = true }
```
Terraform will then **refuse** to plan a destroy of that resource until a human removes the
guard.

---

## Step 9 — Commit

```bash
cd ..
git add terraform/ .gitignore
git commit -m "feat(iac): provision prod and staging with a Terraform module

One reusable paytrack-environment module instantiated twice; the environments
differ only by input variables, so they cannot silently diverge.

- providers and versions pinned; .terraform.lock.hcl committed
- kubeconfig context pinned explicitly to k3d-paytrack
- ConfigMap checksum annotation triggers a rollout on config change
- state is git-ignored (it contains the DB password in plaintext)
- remote backend with DynamoDB locking documented in versions.tf"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
cd terraform && terraform output && terraform plan -detailed-exitcode; echo "exit=$?"
```
`exit=0` means no drift: reality matches code.

---

## 🧩 Stretch (homework)

1. **`for_each` vs `count`.** Rewrite the two module calls as a single `for_each` over a map
   of environments. Then remove the middle element of an equivalent `count` list and observe
   the re-indexing that destroys the wrong resource.
2. **Import an existing resource.** `terraform import` the `paytrack-dev` namespace and watch
   the plan try to reconcile it. This is the "we'll adopt IaC later" path, and it is harder
   than it looks.
3. **Remote backend.** Run MinIO locally and configure the `s3` backend against it.
4. **Policy as code.** Run [Checkov](https://www.checkov.io/) or `trivy config terraform/`
   and fix what it finds. This becomes a gate in Lab 17.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Error: Unauthorized` | Wrong or missing kube context | Check `config_context = "k3d-paytrack"`; `kubectl config get-contexts` |
| `namespaces already exists` | Created by kubectl earlier | Use a different name, or `terraform import` it |
| `Provider produced inconsistent result` | Provider/cluster version mismatch | Check the `~>` constraint against your cluster version |
| Plan shows changes every run | Kubernetes defaulted a field you did not set | Add `lifecycle { ignore_changes = [...] }` for that field |
| `state lock` errors | An interrupted run | `terraform force-unlock <id>` — **only** after confirming nothing else is running |
| Deployment never becomes ready | `wait_for_rollout` timed out | `kubectl describe pod -n paytrack-prod` and read Events |

---

## 🎯 Outcome

Two environments provisioned entirely from a single reviewed Terraform module, with pinned
providers, validated variables, drift detection proven, and a clear-eyed understanding of what
the state file contains.

**Next:** [Lab 14 — Configuration Management with Ansible](../lab-14-ansible-config-mgmt/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Step 7 (drift) is the lab.** Scale by hand, plan, watch Terraform notice, apply, watch it
  revert. Then ask who has "just quickly fixed" something in a console this month.
- **The three things that go wrong:**
  1. HCL syntax — a missing brace in a 300-line module. `terraform validate` locates it;
     teach them to run it constantly.
  2. Namespace collisions with kubectl-managed objects. Stress the "one tool per resource"
     rule up front.
  3. `terraform apply` prompting for confirmation when they expected the saved plan.
     Explain the difference between `apply` and `apply tfplan`.
- **Step 6's `grep` for the password in state is the second big moment.** Do it on the
  projector. Then ask where their state files live and who can read them.
- **Debrief question:** "If your production environment were deleted tonight, how long to
  rebuild it — and would the rebuild be identical, or merely similar?"
</details>
