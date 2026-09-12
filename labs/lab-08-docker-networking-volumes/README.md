# Lab 08 — Networking and Volumes: Prove It, Don't Assume It

| | |
|---|---|
| **Day** | 3 |
| **Duration** | 20 minutes |
| **Module** | 3 — Containers with Docker |
| **You will produce** | Verified understanding of container DNS, isolation, port binding and data persistence |
| **Feeds into** | Lab 11 (Kubernetes Services and PVCs are the same ideas, differently implemented) |

---

## Objective

Every claim made in the networking and storage lecture, demonstrated on your own machine in
one command each. This lab is deliberately experimental: **run the command, predict the
output, then check.**

> **Trainer:** the second lab to demote to a demo if the room is behind (`docs/run-sheet.md`).

## Prerequisites

- Lab 07 running: `cd ~/devops-course/paytrack-api-team && docker compose up -d`

---

## Part 1 — Networking

### Step 1.1 — Inspect the network Compose built

```bash
docker network ls
```
**What this does:** lists networks. You will see the three defaults — `bridge` (the legacy
`docker0`), `host`, `none` — plus **`paytrack-net`**, your user-defined bridge.

```bash
docker network inspect paytrack-net --format '{{json .IPAM.Config}}' | jq
docker network inspect paytrack-net --format '{{range $k,$v := .Containers}}{{$v.Name}} {{$v.IPv4Address}}{{"\n"}}{{end}}'
```
**What this does:** the first prints the subnet Docker allocated (typically
`172.18.0.0/16`); the second walks the attached containers with a Go template, printing each
name and IP. **These IPs change on every restart** — which is exactly why nothing in your
configuration refers to them.

### Step 1.2 — Prove service-name DNS

```bash
docker compose exec proxy sh -c 'nslookup api; nslookup db'
```
**What this does:** resolves both service names **from inside** a container. Docker runs an
embedded DNS server at **127.0.0.11** on every user-defined network, and it answers with the
current container IPs.

> 🔑 **This is the mechanism** behind `proxy_pass http://api:8080` and
> `DATABASE_URL=…@db:5432/…`. No IP addresses, no `/etc/hosts` editing, no service-discovery
> tool. And it maps one-to-one onto Kubernetes Services tomorrow.

```bash
docker compose exec proxy sh -c 'nslookup api | tail -6'
```
**What this does:** with two `api` replicas running, DNS returns **both IPs**. That is
client-side load balancing via round-robin DNS — and its weaknesses (no health awareness, DNS
caching) are precisely why Kubernetes puts a Service VIP in front instead.

### Step 1.3 — Prove `localhost` inside a container is the container

```bash
docker compose exec api sh -c 'curl -s --max-time 3 http://localhost:5432 || echo "FAILED as expected"'
docker compose exec api sh -c 'curl -s --max-time 3 -o /dev/null -w "db:5432 reachable\n" telnet://db:5432 2>/dev/null || echo "use nc instead"'
docker compose exec api sh -c 'python3 -c "
import socket
s=socket.create_connection((\"db\",5432),timeout=3); print(\"✅ db:5432 reachable\"); s.close()"'
```
**What this does:** the first command fails because **`localhost` inside the API container is
the API container's own loopback**, where nothing listens on 5432. The third succeeds using
the service name. This is the single most common beginner error, and seeing both results
back to back fixes it permanently.

### Step 1.4 — Prove network isolation

```bash
docker network create isolated-net
docker run -d --name stranger --network isolated-net alpine sleep 300
docker exec stranger sh -c 'nslookup db || echo "❌ cannot resolve db - isolated"'
docker exec stranger sh -c 'ping -c1 -W2 db 2>/dev/null || echo "❌ cannot reach db - isolated"'
```
**What this does:** creates a second network and a container on it. That container **cannot
resolve or reach** your stack: user-defined bridges are isolated from each other by default.
This is real segmentation, not a convention.

```bash
docker network connect paytrack-net stranger
docker exec stranger sh -c 'nslookup db | tail -4 && echo "✅ now reachable - joined the network"'
```
**What this does:** attaches the running container to a second network. It can now resolve
`db`. Containers can be multi-homed, and connectivity is a **property of network membership**
— which is exactly the model Kubernetes NetworkPolicy formalises.

```bash
docker rm -f stranger && docker network rm isolated-net
```

### Step 1.5 — Prove the port-publishing rules

```bash
docker compose ps --format "table {{.Service}}\t{{.Ports}}"
```
**What this does:** shows published ports. Note that **`api` has none** — it is reachable
only from inside the network.

```bash
curl -s --max-time 3 localhost:8080/health | jq -c   # via nginx  → works
curl -s --max-time 3 localhost:8081/health || echo "❌ api not published to the host"
ss -tlnp 2>/dev/null | grep -E '8080|5432' || sudo ss -tlnp | grep -E '8080|5432'
```
**What this does:** `ss -tlnp` lists listening TCP sockets. **Look carefully at the addresses:**
- `0.0.0.0:8080` — nginx, reachable from anywhere on your network
- `127.0.0.1:5432` — Postgres, reachable **only from this machine**

> 🔴 **The security point.** Had you written `"5432:5432"` instead of `"127.0.0.1:5432:5432"`,
> your database would be listening on every interface. And because **Docker inserts its own
> iptables rules ahead of UFW's**, `sudo ufw deny 5432` would *not* protect you. This has
> caused real breaches. Verify with:
> ```bash
> sudo iptables -t nat -L DOCKER -n 2>/dev/null | head -10
> ```
> **What this does:** shows the DNAT rules Docker wrote directly into the kernel, bypassing
> your firewall's user-facing configuration.

---

## Part 2 — Volumes and persistence

### Step 2.1 — Prove the writable layer is ephemeral

```bash
docker compose exec api sh -c 'echo "critical data" > /tmp/important.txt && cat /tmp/important.txt'
docker compose restart api
docker compose exec api sh -c 'cat /tmp/important.txt 2>/dev/null || echo "❌ file survived a restart"'
```
**What this does:** `restart` stops and starts the *same* container, so its writable layer
survives — the file is still there.

```bash
docker compose up -d --force-recreate api
docker compose exec api sh -c 'cat /tmp/important.txt 2>/dev/null || echo "✅ GONE - the writable layer was destroyed"'
```
**What this does:** `--force-recreate` destroys the container and builds a new one from the
image. **The writable layer goes with it.** Restart ≠ recreate, and Kubernetes recreates
constantly — which is why nothing durable may live on a container filesystem.

### Step 2.2 — Prove the named volume persists

```bash
docker compose exec db psql -U paytrack -d paytrack -c \
  "INSERT INTO authorisations (merchant,status,amount_minor,currency,card_last4) VALUES ('PERSISTENCE-TEST','approved',1,'GBP','0000');"
docker compose exec db psql -U paytrack -d paytrack -tAc \
  "SELECT count(*) FROM authorisations WHERE merchant='PERSISTENCE-TEST';"
```
**What this does:** inserts a marker row. `-tAc` = tuples only, unaligned, one command —
which gives a bare `1` rather than an ASCII table, ideal for scripting.

```bash
docker compose down            # containers and network removed; volumes KEPT
docker volume ls | grep paytrack
docker compose up -d && sleep 8
docker compose exec db psql -U paytrack -d paytrack -tAc \
  "SELECT count(*) FROM authorisations WHERE merchant='PERSISTENCE-TEST';"
```
**Expect `1`.** The containers were destroyed and rebuilt; the data survived in the volume.

### Step 2.3 — Look at where the data actually is

```bash
docker volume inspect paytrack-pgdata --format '{{.Mountpoint}}'
sudo ls -la "$(docker volume inspect paytrack-pgdata --format '{{.Mountpoint}}')" | head
```
**What this does:** shows the host path Docker manages (`/var/lib/docker/volumes/…`) and its
contents. `sudo` is required because Postgres' data directory is owned by uid 999.
**Useful to see once, so volumes stop being magic — but never edit files here directly.**

### Step 2.4 — Back up and restore a volume

```bash
mkdir -p ~/devops-course/backups
docker run --rm \
  -v paytrack-pgdata:/data:ro \
  -v ~/devops-course/backups:/backup \
  alpine tar czf /backup/pgdata-$(date +%F-%H%M).tar.gz -C /data .
ls -lh ~/devops-course/backups/
```
**What this does:** Docker has no `volume backup` command, so this is the standard idiom: a
throwaway `alpine` container mounts the volume **read-only** (`:ro`) and your backup
directory read-write, then tars one into the other. `--rm` cleans up. `-C /data` makes the
archive paths relative rather than absolute.

**A logical backup is usually better for a database:**
```bash
docker compose exec -T db pg_dump -U paytrack paytrack | gzip > ~/devops-course/backups/paytrack-$(date +%F).sql.gz
ls -lh ~/devops-course/backups/*.sql.gz
```
**What this does:** `pg_dump` produces SQL that can be restored to a *different* Postgres
version — a file-level tar cannot. `-T` disables TTY allocation so the pipe is not corrupted.
`gzip` compresses on the host.

> **Test your restores.** A backup you have never restored is a hypothesis, not a backup.

### Step 2.5 — Bind mount vs named volume

```bash
docker run --rm -v "$PWD/nginx:/mnt:ro" alpine ls -la /mnt
```
**What this does:** a **bind mount** — a host path mapped straight into a container. You see
your actual `nginx.conf`. Bind mounts are for **development** (live editing) and for
**configuration**; they couple the container to a host path, so they are wrong for
production data.

| | **Named volume** | **Bind mount** | **tmpfs** |
|---|---|---|---|
| Path | Docker-managed | Any host path | RAM only |
| Portable | ✅ | ❌ | ✅ |
| Backup idiom | The tar recipe above | Ordinary host tooling | N/A |
| Permissions | Docker handles them | Host UID/GID mismatches are common | N/A |
| Use for | **Production data** | Dev source, config files | **Secrets, scratch** |

---

## Part 3 — Clean-up hygiene

```bash
docker system df
```
**What this does:** shows disk used by images, containers, volumes and the build cache, with
a **RECLAIMABLE** column. Run it now — you are three days in and it is already substantial.

```bash
docker image prune -f
docker builder prune -f --filter until=24h
```
**What this does:** `image prune` removes dangling images (untagged layers left by rebuilds);
`builder prune` clears build cache older than 24 hours. Both are safe.

```bash
# docker system prune -a --volumes    # ⚠️ removes ALL unused images AND VOLUMES
```
**What this does:** the nuclear option. `--volumes` **deletes every volume not currently
attached to a running container** — including your database if the stack is down. Left
commented deliberately. Know exactly what it removes before you ever run it.

---

## ✅ Final checkpoint

Answer these from what you just observed, not from memory:

1. Why does `proxy_pass http://api:8080` work with no IP address anywhere in the config?
2. Why did `curl localhost:5432` fail *inside* the API container?
3. What is the difference between `docker compose restart api` and
   `docker compose up -d --force-recreate api`, in terms of what survives?
4. If you had published Postgres as `"5432:5432"` on a cloud VM with `ufw deny 5432`
   active — would the database be exposed? Why?
5. What exactly does `docker compose down -v` destroy that `docker compose down` does not?

Answers: [`solutions/lab-08-answers.md`](../../solutions/lab-08-answers.md)

---

## 🧩 Stretch (homework)

1. **`--network host`.** Run a container with it and compare `ip addr` inside against the
   host's. Note that `-p` is ignored entirely, and think about why that is both faster and
   less safe.
2. **Custom subnet.** `docker network create --subnet 10.99.0.0/24 lab-net` — useful when
   Docker's default ranges collide with your corporate VPN, which is a real and annoying
   problem.
3. **`tmpfs` for secrets.** `docker run --tmpfs /run/secrets:rw,noexec,nosuid,size=1m …` and
   verify with `mount | grep secrets` that it never touches disk.
4. **Restore drill.** `docker compose down -v`, then restore from your `pg_dump` backup and
   prove the row count matches. **Do this one** — it is the only way to know your backup works.

---

## 🎯 Outcome

Demonstrated, not assumed: container DNS, network isolation, the danger of careless port
publishing, the ephemerality of the writable layer, and volume persistence and backup.

**Next:** [Lab 09 — Kubernetes Cluster Setup](../lab-09-kubernetes-setup/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Run this as predict-then-check.** Before each command, ask the room what it will print.
  The value is in the wrong predictions.
- **The three things that go wrong:**
  1. `ss` needs `sudo` on some systems to show process names. The fallback is in the command.
  2. `sudo ls` into `/var/lib/docker/volumes` on WSL2 or Docker Desktop shows a VM path or
     nothing — explain that the daemon runs in a VM there, which is itself a useful point.
  3. Delegates run `docker system prune -a --volumes` "to tidy up" and destroy their stack
     before day 4. Say the warning out loud rather than relying on them reading it.
- **The port-binding demonstration (1.5) is the one to slow down for.** The UFW-bypass fact
  surprises experienced sysadmins and is worth the extra two minutes.
- **Debrief question:** "When did your organisation last *restore* from a backup, as opposed
  to taking one?"
</details>
