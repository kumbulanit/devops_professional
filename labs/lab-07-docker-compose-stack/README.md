# Lab 07 — A Full Local Stack with Docker Compose

| | |
|---|---|
| **Day** | 3 |
| **Duration** | 35 minutes |
| **Module** | 3 — Containers with Docker |
| **You will produce** | `compose.yaml` — PayTrack API + PostgreSQL + Nginx, started with one command |
| **Feeds into** | Lab 08 (networking/volumes deep-dive), Lab 11 (the same topology on Kubernetes) |

---

## Objective

Turn a single container into a **real application stack**: the API, a PostgreSQL database it
actually uses, and an Nginx reverse proxy in front. One command starts it; one command
destroys it; the data survives a restart. This is the environment a new joiner should be able
to reach in five minutes.

You will also meet the single most common Compose bug — `depends_on` without a health
condition — by causing it deliberately.

## Prerequisites

- Lab 06 complete (`paytrack-api:1.0.0` built locally)

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && git switch main && git pull
cd app && docker build -t paytrack-api:1.0.0 . && cd ..
```

---

## Step 1 — What you are building

```
                    HOST                                COMPOSE NETWORK "paytrack-net"
  ┌──────────────────────────────┐   ┌───────────────────────────────────────────────┐
  │  browser → localhost:8080    │──►│  nginx  :80    reverse proxy, rate limiting   │
  │  psql    → localhost:5432    │─┐ │    │  proxy_pass http://api:8080              │
  │           (dev only)         │ │ │    ▼                                          │
  └──────────────────────────────┘ │ │  api    :8080  PayTrack API (2 replicas)         │
                                   │ │    │  DATABASE_URL=…@db:5432/paytrack            │
                                   │ │    ▼                                          │
                                   └─┼──►db     :5432  PostgreSQL 16                 │
                                     │    │                                          │
                                     │    └──► volume "pgdata"  ← survives restarts  │
                                     └───────────────────────────────────────────────┘
   Names ("api", "db") are DNS names on the user-defined network. No IP addresses anywhere.
```

```bash
cd ~/devops-course/paytrack-api-team
git switch main && git pull
git switch -c feat/add-compose-stack
mkdir -p nginx db
```

---

## Step 2 — The database initialisation script

```bash
cat > db/init.sql <<'EOF'
-- Runs ONCE, only when the data directory is empty (i.e. on a brand-new volume).
-- The application also creates this table idempotently at start-up; having both is
-- deliberate - it makes a fresh stack useful immediately and a rolling update safe.

CREATE TABLE IF NOT EXISTS authorisations (
    id            BIGSERIAL   PRIMARY KEY,
    merchant      TEXT        NOT NULL,
    status        TEXT        NOT NULL,          -- approved | declined | referred
    amount_minor  BIGINT      NOT NULL DEFAULT 0, -- integer MINOR units. NEVER a float.
    currency      CHAR(3)     NOT NULL DEFAULT 'GBP',
    card_last4    CHAR(4)     NOT NULL DEFAULT '0000', -- last four only: no PAN, no PCI scope
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_created_at ON authorisations (created_at DESC);

INSERT INTO authorisations (merchant, status, amount_minor, currency, card_last4) VALUES
    ('NORTHGATE FUEL',  'approved',    4599, 'GBP', '4242'),
    ('CITY CAFE LTD',   'approved',     320, 'GBP', '1881'),
    ('PRESTIGE MOTORS', 'referred',  1250000, 'GBP', '4242'),
    ('UNKNOWN VENDOR',  'declined',   99900, 'EUR', '0000');
EOF
```
**What this does:** the official Postgres image runs every `*.sql` and `*.sh` file in
`/docker-entrypoint-initdb.d/` on first start. ⚠️ **Only when the data directory is empty** —
if the volume already has data, this file is ignored entirely. That surprises people; it is
also exactly why real schema changes need migrations rather than init scripts (Module 6 §6.6).

> 🏦 **Two banking decisions are encoded in that schema.** `amount_minor BIGINT` holds money
> as an integer number of pence — `NUMERIC` would be acceptable, a floating-point type never
> is, because a rounding error in a ledger becomes a reconciliation break and then an audit
> finding. And there is **no column for a primary account number**: storing a PAN would pull
> this database, its backups, its replicas and everything that reads them into PCI-DSS
> cardholder-data scope. Scope is something you design out, not something you secure later.

---

## Step 3 — The Nginx reverse proxy

```bash
cat > nginx/nginx.conf <<'EOF'
events { worker_connections 1024; }

http {
    # "api" resolves via Docker's embedded DNS on the user-defined network.
    upstream paytrack_backend {
        server api:8080;
        keepalive 32;                       # reuse upstream connections
    }

    # Rate limit: 10 requests/second per client IP, with a burst allowance.
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    log_format json escape=json '{"ts":"$time_iso8601","remote":"$remote_addr",'
        '"method":"$request_method","uri":"$request_uri","status":$status,'
        '"bytes":$body_bytes_sent,"rt":$request_time,"upstream":"$upstream_addr"}';
    access_log /dev/stdout json;            # stdout: the platform collects it
    error_log  /dev/stderr warn;

    server {
        listen 80;
        server_name _;

        # Health endpoints: no rate limit, no logging noise.
        location ~ ^/(health|ready)$ {
            proxy_pass http://paytrack_backend;
            access_log off;
        }

        # Metrics: internal networks only. NEVER expose /metrics publicly.
        location /metrics {
            allow 172.16.0.0/12;
            allow 127.0.0.1;
            deny  all;
            proxy_pass http://paytrack_backend;
        }

        location / {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://paytrack_backend;
            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 5s;
            proxy_read_timeout    30s;
        }
    }
}
EOF
```
**What the important directives do:**

| Directive | Purpose |
|---|---|
| `upstream … server api:8080` | `api` is the **Compose service name**, resolved by Docker's DNS. Compose scales `api` to 2 replicas and Docker round-robins the DNS answer |
| `limit_req_zone` / `limit_req` | Basic rate limiting. `burst=20 nodelay` allows short spikes without queuing |
| `access_log /dev/stdout json` | **Structured logs to stdout** — the container logging rule from Module 3 §3.10 |
| `access_log off` on health paths | Probes fire every few seconds; logging them drowns the signal |
| `allow`/`deny` on `/metrics` | Metrics leak internal detail (endpoints, versions, volumes). Restrict them |
| `X-Forwarded-For` / `X-Real-IP` | Without these the app sees only the proxy's IP, breaking rate limiting and audit logs |

---

## Step 4 — The Compose file

```bash
cat > compose.yaml <<'EOF'
# Docker Compose v2. Run with:  docker compose up -d --build
# The top-level `version:` key is obsolete in v2 and is deliberately omitted.

services:
  # ── PostgreSQL ────────────────────────────────────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: paytrack-db
    environment:
      POSTGRES_USER: paytrack
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-paytrack_dev_only}
      POSTGRES_DB: paytrack
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - pgdata:/var/lib/postgresql/data          # named volume → data survives
      - ./db/init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro   # bind mount, read-only
    ports:
      - "127.0.0.1:5432:5432"                    # LOOPBACK ONLY - see the note below
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paytrack -d paytrack"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    restart: unless-stopped
    networks: [paytrack-net]

  # ── PayTrack API ─────────────────────────────────────────────────────────────
  api:
    build:
      context: ./app
      args:
        GIT_SHA: ${GIT_SHA:-local}
        APP_VERSION: ${APP_VERSION:-1.0.0}
    image: paytrack-api:1.0.0
    environment:
      DATABASE_URL: postgresql://paytrack:${POSTGRES_PASSWORD:-paytrack_dev_only}@db:5432/paytrack
      APP_ENV: local
      APP_COLOR: blue
      APP_VERSION: ${APP_VERSION:-1.0.0}
      LOG_LEVEL: INFO
      READINESS_REQUIRES_DB: "true"
    depends_on:
      db:
        condition: service_healthy        # ← WAIT for the healthcheck, not merely for start
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 15s
    deploy:
      replicas: 2                          # two instances; nginx load-balances via DNS
    restart: unless-stopped
    networks: [paytrack-net]
    # NOTE: no `ports:` - the API is NOT reachable from the host directly.
    # All traffic must go through nginx. This is defence in depth.

  # ── Nginx reverse proxy ───────────────────────────────────────────────────
  proxy:
    image: nginx:1.27-alpine
    container_name: paytrack-proxy
    ports:
      - "8080:80"                          # the ONLY public entry point
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      api:
        condition: service_started
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 10s
      retries: 3
    restart: unless-stopped
    networks: [paytrack-net]

volumes:
  pgdata:
    name: paytrack-pgdata

networks:
  paytrack-net:
    name: paytrack-net
    driver: bridge                         # user-defined bridge → service-name DNS
EOF
```

**The decisions worth arguing about:**

| Choice | Why |
|---|---|
| `condition: service_healthy` on `db` | **This is the fix for the most common Compose bug.** Plain `depends_on: [db]` waits only for the container to *start*, not for Postgres to accept connections — so the API crashes on its first query. You will demonstrate this in Step 6 |
| `ports: "127.0.0.1:5432:5432"` | Binds Postgres to loopback only. **`"5432:5432"` would expose your database to every machine on the network** — and Docker writes iptables rules that bypass UFW, so a firewall would not save you |
| `api` has no `ports:` | The API is unreachable except through the proxy. Fewer entry points, fewer problems |
| `${POSTGRES_PASSWORD:-paytrack_dev_only}` | Reads from the environment or `.env`, with a **development-only** default. A real password never appears in the file |
| `:ro` on config bind mounts | The container cannot modify its own configuration |
| `PGDATA` in a subdirectory | Avoids Postgres complaining about `lost+found` on some volume drivers |
| Named volume for data, bind mount for config | Volumes for state; bind mounts for files you edit |
| `deploy.replicas: 2` | Two API instances. Compose does not orchestrate them across hosts — that limitation is why day 4 exists |

```bash
cat > .env.example <<'EOF'
# Copy to .env and set real values.  .env is git-ignored.
POSTGRES_PASSWORD=change_me_locally
APP_VERSION=1.0.0
GIT_SHA=local
EOF
cp .env.example .env
grep -q '^\.env$' .gitignore || echo ".env" >> .gitignore
```
**What this does:** `.env.example` is committed and documents the required variables; `.env`
holds real values and is ignored. `grep -q … ||` appends only if the rule is missing —
idempotent, so re-running is safe.

---

## Step 5 — Start the stack

```bash
docker compose config
```
**What this does:** renders the fully-resolved configuration — all variables substituted,
all defaults applied. **Run this before `up` whenever something behaves unexpectedly**; it
shows you what Compose actually decided, not what you think you wrote.

```bash
docker compose up -d --build
```
**What this does:** `up` creates the network, volume and containers; `-d` detaches;
`--build` rebuilds `api` from `./app` first. Watch the ordering in the output — `db` becomes
healthy *before* `api` starts.

```bash
docker compose ps
```
**What this does:** shows every service with its state and health. Wait for `db` and `proxy`
to read `healthy` and both `api` replicas to be `running`.

✅ **Checkpoint**
```bash
curl -s localhost:8080/health | jq
curl -s localhost:8080/ready | jq
```
`/ready` must report `{"status":"ready","store":"postgres"}` — **`postgres`, not `memory`**.
That single word proves the API found the database through Docker's DNS using only the name
`db`.

```bash
curl -s localhost:8080/api/v1/authorisations | jq '.count, .items[0]'
```
**Expect `4`** — the seeded authorisations from `init.sql`. Data flows end to end: browser → nginx → api →
postgres.

---

## Step 6 — See the `depends_on` bug for yourself

```bash
cp compose.yaml compose.broken.yaml
python3 - <<'PY'
import pathlib
p = pathlib.Path("compose.broken.yaml")
s = p.read_text()
s = s.replace("    depends_on:\n      db:\n        condition: service_healthy",
              "    depends_on: [db]        # BROKEN: waits for START, not READY")
p.write_text(s)
print("created compose.broken.yaml")
PY
docker compose down
docker volume rm paytrack-pgdata
docker compose -f compose.broken.yaml up -d
sleep 4 && docker compose -f compose.broken.yaml logs api | tail -20
```
**What this does:** removes the health condition, destroys the volume so Postgres must
initialise from scratch (which takes several seconds), and starts again. The API now races
the database and you see connection errors in its logs — the failure that costs teams an
afternoon and gets "fixed" with a `sleep 10` in an entrypoint script.

```bash
docker compose -f compose.broken.yaml down -v
rm compose.broken.yaml
docker compose up -d
```
**What this does:** tears the broken stack down (`-v` removes volumes) and brings the correct
one back.

> **The lesson:** *started* and *ready* are different states. This is the same distinction as
> Kubernetes' liveness versus readiness probes, which you meet tomorrow.

---

## Step 7 — Operate the stack

```bash
docker compose logs -f --tail=20 api
```
**What this does:** follows the last 20 lines of the `api` service's logs across **both
replicas**, prefixing each line with the container name. `Ctrl+C` to stop.

```bash
docker compose exec db psql -U paytrack -d paytrack -c "SELECT status, count(*) FROM authorisations GROUP BY status;"
```
**What this does:** runs `psql` **inside** the db container. `-c` executes one statement and
exits. No Postgres client needed on your host.

```bash
for i in 1 2 3 4 5 6; do
  curl -s -X POST localhost:8080/api/v1/authorisations \
    -H 'Content-Type: application/json' \
    -d "{\"merchant\":\"MERCHANT-$i\",\"amount_minor\":$((RANDOM % 8000 + 100)),\"currency\":\"GBP\",\"card_last4\":\"4242\"}" \
    -o /dev/null -w "%{http_code} "
done; echo
```
**What this does:** posts six records through nginx. `$((RANDOM % 200))` generates a random
latency; `-w "%{http_code} "` prints just the status code. Expect six `201`s.

```bash
docker compose exec db psql -U paytrack -d paytrack -c "SELECT count(*) FROM authorisations;"
```
**Expect 10** (4 seeded + 6 new). Requests were load-balanced across two API replicas, and
both wrote to the same database — a two-tier application working correctly.

```bash
docker compose up -d --scale api=4
docker compose ps | grep api
```
**What this does:** scales to four replicas **without downtime**. Nginx picks them up via
DNS on the next resolution. Scale back with `--scale api=2`.

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```
**What this does:** a one-shot (`--no-stream`) resource snapshot. Note how little the API
containers use — that density is the containerisation argument in one screen.

---

## Step 8 — Prove the data survives

```bash
docker compose down
docker compose ps -a
docker volume ls | grep paytrack
```
**What this does:** `down` stops and removes containers **and the network**, but **not named
volumes**. The volume `paytrack-pgdata` is still listed.

```bash
docker compose up -d
sleep 8
curl -s localhost:8080/api/v1/authorisations | jq '.count'
```
**Expect 9 again.** Containers are disposable; the volume is not. This is the separation
between the ephemeral writable layer and persistent storage from Module 3 §3.9.

> ⚠️ **`docker compose down -v` deletes the volume and every row in it.** There is no
> confirmation prompt. Know the difference between `down` and `down -v` before you type it
> on anything that matters.

---

## Step 9 — Commit

```bash
git add compose.yaml .env.example nginx/ db/ .gitignore
git commit -m "feat: add Docker Compose stack

PayTrack API (x2) behind nginx, backed by PostgreSQL 16 with a named volume.

- depends_on uses condition: service_healthy so the API never races the DB
- Postgres is bound to 127.0.0.1 only; the API is not published at all
- nginx terminates traffic, rate limits, and restricts /metrics to internal CIDRs
- passwords come from .env (git-ignored); .env.example documents the contract"
git push -u origin feat/add-compose-stack
```
Open and merge the PR.

---

## ✅ Final checkpoint

```bash
docker compose ps
curl -s localhost:8080/ready | jq -r '.store'      # → postgres
curl -s localhost:8080/api/v1/authorisations | jq '.count' # → 9
docker compose exec api id                          # → uid=10001 (not root)
```

---

## ⭐ Advanced — optional, in this folder

The stack runs. If you want the version of Compose that survives contact with more than one
environment, it is beside this page — nothing on Day 4 onwards depends on it.

| In this folder | What it is | Time | Needs |
|---|---|---|---|
| **[README-07A — Compose in Depth](README-07A-compose-in-depth.md)** | See what `docker compose config` really merges; split the stack into dev and UAT overlays; meet the `compose.override.yaml` that loads itself; hide tooling behind a profile; add CPU, memory and log limits and watch them bite; then destroy the database with `down -v` and restore it from a backup you took | 60 min, eight parts | Docker and the Lab 07 stack |
| **`Lab07A_Advanced_Compose.pptx`** | The 8 slides behind it: merging and precedence, profiles, health gating, restart policies and limits | Read it first | PowerPoint |

---

## 🧩 Stretch (homework)

1. **Compose profiles.** Add `profiles: ["debug"]` to an adminer service and start it only
   with `docker compose --profile debug up -d`.
2. **Override files.** Create `compose.override.yaml` bind-mounting `./app/src` into the
   container for live reload — Compose merges it automatically. Then show that
   `docker compose -f compose.yaml up` (explicit `-f`) ignores it, which is how you keep
   production honest.
3. **Resource limits.** Add `deploy.resources.limits` and watch `docker stats` change.
4. **Backup the volume:**
   `docker run --rm -v paytrack-pgdata:/data -v "$PWD":/backup alpine tar czf /backup/pg-$(date +%F).tar.gz -C /data .`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/ready` says `"store":"memory"` | `DATABASE_URL` unset or unreachable | `docker compose config` and check the rendered value |
| `api` restarts repeatedly | Postgres not ready | Confirm `condition: service_healthy` is present |
| `port is already allocated` | 8080 or 5432 in use | `sudo lsof -i :8080`; change the host-side port |
| `init.sql` never runs | Volume already had data | `docker compose down -v` then `up` (**destroys data**) |
| nginx `host not found in upstream "api"` | Service renamed, or not on the same network | Names must match; both must list `paytrack-net` |
| Changes to `nginx.conf` do nothing | Bind mount is loaded at start | `docker compose restart proxy` |

---

## 🎯 Outcome

A three-tier stack — proxy, API ×2, database — defined in one file, started with one command,
with correct startup ordering, persistent storage, and no ports exposed that should not be.

**Next:** [Lab 08 — Docker Networking and Volumes](../lab-08-docker-networking-volumes/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Step 6 is the highlight.** Breaking `depends_on` deliberately teaches started-vs-ready
  better than any slide, and it sets up tomorrow's liveness-vs-readiness discussion.
- **The three things that go wrong:**
  1. Port 8080 occupied by a container left over from Lab 06. `docker rm -f paytrack`.
  2. `.env` not created, so the password substitutes to the default. Harmless here — but
     point out that in production that default *is* the vulnerability.
  3. YAML indentation in `depends_on`. `docker compose config` gives a precise error.
- **Spend 60 seconds on the `127.0.0.1:5432` binding.** Ask who has seen a database exposed
  on 0.0.0.0 in a cloud VM. Mention that Docker bypasses UFW — it genuinely surprises
  experienced admins.
- **Debrief question:** "How long does it take a new joiner at your organisation to get a
  working local environment? What would `docker compose up` be worth?"
</details>
