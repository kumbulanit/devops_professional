# Reference material

Take-home material. Each file is written to be usable **after** the course, at a keyboard,
under pressure — not as revision notes.

| File | Covers |
|---|---|
| **[access-card.md](access-card.md)** | **Print this one.** Every URL, port, credential, `/etc/hosts` entry and start/stop command in the course, plus the port-8080 conflict map and the free-tier limits |
| [../docs/theory/git-command-guide.md](../docs/theory/git-command-guide.md) | **Every everyday Git command explained**: what it means, real output, when to use it, when not to — plus *which undo command?* and *the commands that can destroy work* |
| [git-cheatsheet.md](git-cheatsheet.md) | Setup, the four areas, daily commands, branching, **undo by situation**, merge strategies, conflict resolution, investigation (`bisect`, `log -S`), Conventional Commits, emergency recovery |
| [docker-cheatsheet.md](docker-cheatsheet.md) | Images, containers, **runtime hardening flags**, Dockerfile essentials and traps, Compose, networking facts (including the UFW bypass), volumes and backup, housekeeping |
| [kubectl-cheatsheet.md](kubectl-cheatsheet.md) | Inspection, **debugging in the order to try it**, symptom→cause table, apply/rollout, access, nodes, JSONPath, scripting primitives, object reference, the probe rule |
| [terraform-ansible-cheatsheet.md](terraform-ansible-cheatsheet.md) | Terraform workflow, **reading a plan**, state operations, drift detection, language reference, meta-arguments · Ansible commands, Vault, playbook shape, **idempotency techniques**, Jinja2, variable precedence |
| [devops-best-practices-checklist.md](devops-best-practices-checklist.md) | 100+ item assessment across ten areas, with a scoring table and the ten anti-patterns |

## Pipeline templates

Working, commented templates live in the labs that build them — they are easier to
understand alongside the explanation than in isolation:

| Template | Lab |
|---|---|
| GitHub Actions CI (lint, matrix tests, coverage gate) | [04](../labs/lab-04-github-actions-ci/README.md) |
| Jenkins declarative pipeline | [05](../labs/lab-05-jenkins-ci/README.md) |
| Multi-stage Dockerfile + GHCR publish workflow | [06](../labs/lab-06-docker-images/README.md) |
| Docker Compose stack with healthcheck ordering | [07](../labs/lab-07-docker-compose-stack/README.md) |
| Kubernetes manifests (Deployment, Service, ConfigMap, Secret, StatefulSet, Ingress, HPA, PDB, NetworkPolicy) | [10](../labs/lab-10-k8s-deploy-app/README.md), [11](../labs/lab-11-k8s-config-secrets-storage/README.md), [12](../labs/lab-12-k8s-ingress-scaling/README.md) |
| Terraform module + root configuration | [13](../labs/lab-13-terraform-iac/README.md) |
| Ansible inventory, roles, handlers, Vault | [14](../labs/lab-14-ansible-config-mgmt/README.md) |
| GitOps CD workflow + reconciler | [15](../labs/lab-15-cd-pipeline-to-k8s/README.md) |
| Blue-green / canary / weighted manifests | [16](../labs/lab-16-deployment-strategies/README.md) |
| Security workflow, `.trivyignore`, pre-commit config | [17](../labs/lab-17-devsecops-pipeline/README.md) |
| ServiceMonitor, PrometheusRule (SLO burn-rate), Grafana dashboard JSON, runbook, post-mortem | [18](../labs/lab-18-observability/README.md) |
