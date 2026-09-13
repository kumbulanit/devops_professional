# Access Card — every URL, port, credential and command

**Print this.** It is the page delegates reach for when they ask "what was the Grafana
password?" or "why is port 8080 busy?"

---

## 🔴 The one thing that breaks the week: port 8080

**Three different labs bind host port 8080, and only one may run at a time.**

| Day | What owns 8080 | Started by |
|---|---|---|
| 1 | Flask dev server | `python -m src.app` (Lab 02) |
| 3 | Nginx in the Compose stack | `docker compose up -d` (Lab 07) |
| 4–6 | Traefik in the k3d cluster | `k3d cluster create` (Lab 09) |

**Before starting the next one, stop the previous one:**
```bash
# Find what is holding the port
sudo lsof -i :8080

# Stop each, as appropriate
Ctrl+C                                   # the Flask dev server
docker compose down                      # the Compose stack (from the repo root)
k3d cluster stop paytrack                   # the cluster
```
**What this does:** `lsof -i :8080` lists the process listening on that port. From day 4
onward the cluster should own 8080 — so `docker compose down` becomes part of your morning
routine.

---

## URLs — where to go, and when

### Day 1–3 (local / Docker)

| URL | What | Lab | Needs |
|---|---|---|---|
| `http://localhost:8080/` | PayTrack API banner page | 02 | `python -m src.app` running |
| `http://localhost:8080/health` | Liveness JSON | 02 | " |
| `http://localhost:8080/api/v1/info` | Version, colour, backend | 02 | " |
| `http://localhost:8080/api/v1/authorisations` | List/create records | 02 | " |
| `http://localhost:8080/metrics` | Prometheus metrics | 02 | " |
| `http://localhost:8080/` | Same, but **via nginx → API ×2 → Postgres** | 07 | `docker compose up -d` |
| `http://localhost:8081` | **Jenkins** | 05 | `docker start jenkins` |
| `https://github.com/<your-username>/paytrack-api` | Your repository | 03 | — |
| `https://github.com/<your-username>/paytrack-api/actions` | Pipeline runs | 04 | — |
| `https://github.com/<your-username>/paytrack-api/network` | **Team branch graph** ← see Lab 03 Part 6 | 03 | public repo |

### Day 4–6 (Kubernetes)

| URL | What | Lab |
|---|---|---|
| `http://paytrack.localhost:8080/` | PayTrack API via Traefik Ingress | 12 |
| `http://paytrack.localhost:8080/health` · `/ready` · `/metrics` | Probes and metrics | 12 |
| `http://bg.paytrack.localhost:8080/` | Blue-green Service | 16 |
| `http://canary.paytrack.localhost:8080/` | Canary (replica-ratio split) | 16 |
| `http://weighted.paytrack.localhost:8080/` | Traefik weighted routing | 16 |
| `http://prod.paytrack.localhost:8080/` | Terraform-provisioned prod | 13 |
| `http://staging.paytrack.localhost:8080/` | Terraform-provisioned staging | 13 |
| `http://grafana.localhost:8080/` | **Grafana** | 18 |

### Ports opened by `kubectl port-forward` (temporary, debugging only)

| Command | Opens | Lab |
|---|---|---|
| `kubectl port-forward service/paytrack-api 8888:80` | `localhost:8888` | 10, 11 |
| `kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090` | Prometheus UI | 18 |
| `kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093` | Alertmanager UI | 18 |
| `kubectl port-forward deployment/paytrack-api-green 9999:8080` | Smoke-test green directly | 16 |

**These die when your shell closes.** Backgrounded with `&`? Stop with `kill %1`.

---

## Credentials — all of them

| System | User | Password / how to get it | Lab |
|---|---|---|---|
| **Grafana** | `admin` | `paytrack-admin` | 18 |
| **Jenkins** | you create it in the wizard | initial: `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword` | 05 |
| **Postgres (Compose)** | `paytrack` | `paytrack_dev_only` (or your `.env`) | 07 |
| **Postgres (Kubernetes)** | `paytrack` | `S3cur3-Cl4ss-Only!` — replaced in Lab 17 by a SealedSecret | 11, 17 |
| **Ansible Vault** | — | `lab-vault-password` (in `ansible/.vault_pass`, git-ignored) | 14 |
| **GitHub** | your account | **Personal Access Token**, not your password (Settings → Developer settings → PAT → Fine-grained) | 03 |
| **GHCR** | your GitHub user | the automatic `GITHUB_TOKEN` in CI; locally `docker login ghcr.io` with a PAT | 06 |
| **Container runtime user** | `10001` (numeric, non-root) | n/a | 06 |

> Every password here is **deliberately a lab value**. Lab 17 is where you learn what to do
> instead.

---

## `/etc/hosts` — the full set

Labs add these one at a time. To add them all at once:

```bash
sudo tee -a /etc/hosts <<'EOF'
127.0.0.1  paytrack.localhost api.paytrack.localhost
127.0.0.1  grafana.localhost
127.0.0.1  bg.paytrack.localhost canary.paytrack.localhost weighted.paytrack.localhost
127.0.0.1  prod.paytrack.localhost staging.paytrack.localhost
EOF
getent hosts paytrack.localhost
```
**What this does:** maps every hostname the course uses to loopback, so your browser and
`curl` send the right `Host:` header — **which is what Ingress routes on**. `getent` confirms
resolution works.

---

## Start / stop, per day

### Day 1–2
```bash
cd ~/devops-course/paytrack-api/app
source .venv/bin/activate      # activate the Python environment
python -m src.app              # start on :8080   (Ctrl+C to stop)
deactivate                     # leave the environment
```

### Day 3 — Compose stack
```bash
cd ~/devops-course/paytrack-api-team
docker compose up -d --build   # start proxy + api x2 + postgres
docker compose ps              # check state and health
docker compose logs -f api     # follow logs (Ctrl+C to detach)
docker compose down            # stop.  Volumes (your data) are KEPT
docker compose down -v         # ⚠️ ALSO deletes the database
```

### Day 4–6 — Kubernetes
```bash
k3d cluster start paytrack                                   # morning
kubectl config set-context --current --namespace=paytrack-dev
kubectl get pods                                          # verify
k3d cluster stop paytrack                                    # evening — frees RAM, keeps state
```

### Jenkins (day 2 only)
```bash
docker start jenkins    # http://localhost:8081
docker stop jenkins     # stop when done — it is the heaviest thing on day 2
```

### The GitOps reconciler (day 5–6, its own terminal)
```bash
cd ~/devops-course/paytrack-api-team && ./scripts/gitops-sync.sh    # Ctrl+C to stop
```
> **Stop it before Lab 16** — it will otherwise revert your blue-green and canary changes.

---

## "Is it working?" — one command each

```bash
~/devops-course/toolcheck.sh                              # the toolchain          (Lab 00)
cd ~/devops-course/paytrack-api-team/app && pytest -q        # the app                (Lab 02)
docker compose ps                                         # the Compose stack      (Lab 07)
kubectl get pods                                          # the cluster workloads  (Lab 09+)
curl -s http://paytrack.localhost:8080/api/v1/info | jq      # the live service       (Lab 12+)
./scripts/verify-platform.sh                              # EVERYTHING             (Lab 19)
```

---

## Directories

| Path | What |
|---|---|
| `~/devops-course/` | Everything for the week |
| `~/devops-course/paytrack-api/` | Your **local-only** repo (Labs 01–02) |
| `~/devops-course/paytrack-api-team/` | The **team clone from GitHub** — Labs 03 onward. **This is the working directory for the rest of the course** |
| `~/devops-course/course-material/` | This course repo; a source of files only |
| `~/devops-course/jenkins/` | Jenkins Dockerfile (Lab 05) |
| `~/devops-course/backups/` | Volume and database backups (Lab 08) |

> ⚠️ **From Lab 03 onward, work in `paytrack-api-team/`, not `paytrack-api/`.** Editing the wrong
> one is the single most common way to lose an afternoon's work.

---

## Free-tier limits worth knowing

| Service | Limit | What happens when you hit it |
|---|---|---|
| GitHub Actions | Unlimited on **public** repos; 2 000 min/month private | Runs queue, then fail |
| GHCR | Free for public packages | Private packages count against storage |
| Docker Hub | 100 anonymous pulls / 6 h per IP | `toomanyrequests` — fix with `docker login` |
| GitHub Codespaces | 60 core-hours/month | Codespace stops |
