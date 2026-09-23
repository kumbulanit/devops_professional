# Lab 07A — Compose in Depth: Merging, Profiles, Limits and Restores

| | |
|---|---|
| **Day** | 3 — **optional**, after class or as homework |
| **Duration** | About 60 minutes, in eight parts |
| **Module** | 3 — Containers with Docker (the Day 3 *Going Further* slides, section B) |
| **Slides** | `Lab07A_Advanced_Compose.pptx` — in this folder, 8 slides, read it first |
| **Parent lab** | [Lab 07 — A Full Local Stack with Docker Compose](README.md) |
| **You will produce** | `compose.dev.yaml`, `compose.uat.yaml`, a tooling profile, resource and log limits, and a database backup you have actually restored |
| **Feeds into** | Nothing. Lab 08 keeps using the Lab 07 stack |

---

## Objective

Lab 07 built one stack from one file. Real projects have **one stack described by several files**,
different shapes for a laptop and for UAT, tooling that must not start by default, limits so one
container cannot take the machine, and a backup someone has tested.

You will see what Compose actually runs after merging, split the file, hide developer tooling
behind a profile, put CPU, memory and log limits on the stack and watch them bite, and destroy the
database on purpose — then bring the data back.

## Prerequisites

- **Lab 07 complete** — `compose.yaml`, `db/init.sql` and `nginx/nginx.conf` exist and the stack
  starts
- **Docker running**, and ports 8080 and 5432 free

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction is **one command in one grey box**, numbered in
the order you run it.

- **Open a terminal** with `Ctrl` + `Alt` + `T`; it shows a line ending in `$`, the prompt.
- **Run a command:** click in, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait
  for the prompt.
- **Most boxes print nothing** when they succeed. Builds and pulls take minutes — wait.
- **A box that begins `cat > … <<'EOF'` or `python3 - <<'PY'` is one command** — copy all of it,
  final line included.
- Symbols: `~` home folder · `cd` move into a folder · `>` write a file · `|` pass output on ·
  `&&` only if that worked · `$(…)` run this first and use its answer.
- **YAML cares about spaces.** The boxes write the files for you; if you retype one, use two
  spaces per level and never a Tab.

🔁 **RECOVER — if the Lab 07 stack is not running**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project, where `compose.yaml` lives.

```bash
docker compose up -d --build
```
**What this does:** builds the API image if needed and starts db, api and proxy in the background.
If `compose.yaml` is missing, finish Lab 07 first.

---

## Part 1 — A branch, and a stack that is up (5 min)

**1. Go to your project.**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** every command in this lab runs from here.

**2. Go to the main branch.**

```bash
git switch main
```
**What this does:** start from the reviewed code.

**3. Update it.**

```bash
git pull
```
**What this does:** brings in anything merged since your last pull.

**4. Create a branch.**

```bash
git switch -c docker/07a-compose-in-depth
```
**What this does:** the new Compose files are a change like any other.

**5. Start the stack.**

```bash
docker compose up -d
```
**What this does:** starts (or leaves running) db, api ×2 and proxy in the background.

**6. Check it.**

```bash
docker compose ps
```
**What this does:** one row per container, with health where a healthcheck exists. Wait until `db`
says `healthy` before moving on.

---

## Part 2 — The file you run is not the file you wrote (8 min)

**1. Ask Compose what it will actually run.**

```bash
docker compose config
```
**What this does:** prints the **merged, fully resolved** configuration: every file combined, every
`${VARIABLE}` replaced, every default filled in. This — not `compose.yaml` — is what Compose runs.
Press `q` if a scrollable view opens.

**2. Find the value you did not mean to publish.**

```bash
docker compose config | grep -i password
```
**What this does:** searches that output for "password", ignoring case (`-i`). The database
password appears **in plain text**, because `config` resolves `${POSTGRES_PASSWORD:-…}`. Never
paste `docker compose config` output into a ticket or a screenshot.

**3. List just the service names.**

```bash
docker compose config --services
```
**What this does:** prints `api`, `db`, `proxy` — useful in scripts, and the quickest way to see
whether a file you added actually contributed a service.

**4. Check the file parses before anything else does.**

```bash
docker compose config --quiet && echo "compose files are valid"
```
**What this does:** `--quiet` prints nothing and returns success or failure, so `&&` only prints the
message when the merge is valid. This is the one-line check to put in CI.

---

## Part 3 — Split the file: a laptop shape and a UAT shape (12 min)

**1. Write the developer overlay.** One command — copy the whole box, including the final `EOF`:

```bash
cat > compose.dev.yaml <<'EOF'
# Developer overlay. Merged ON TOP of compose.yaml:
#   docker compose -f compose.yaml -f compose.dev.yaml up -d
services:
  api:
    environment:
      LOG_LEVEL: DEBUG            # replaces the value in compose.yaml
      APP_ENV: dev
    deploy:
      replicas: 1                 # one instance is easier to read while debugging
  db:
    ports:
      - "127.0.0.1:5432:5432"     # keep the loopback-only publish for local psql
EOF
```
**What this does:** writes an overlay that changes three things for local work. It does not repeat
the whole service — only the keys it changes.

**2. Write the UAT overlay.** One command, ending at `EOF`:

```bash
cat > compose.uat.yaml <<'EOF'
# UAT overlay. Merged ON TOP of compose.yaml:
#   docker compose -f compose.yaml -f compose.uat.yaml up -d
services:
  api:
    environment:
      LOG_LEVEL: INFO
      APP_ENV: uat
      APP_COLOR: green
    deploy:
      replicas: 3
      resources:
        limits:   { cpus: "0.50", memory: 256M }
        reservations: { memory: 128M }
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
  db:
    ports: []                     # NOT published in UAT - reachable only inside the network
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512M }
EOF
```
**What this does:** writes the shape you would run on a shared machine: three API instances,
resource and log limits, and a database with **no published port at all**.

**3. See what the developer shape resolves to.**

```bash
docker compose -f compose.yaml -f compose.dev.yaml config | grep -A2 "LOG_LEVEL"
```
**What this does:** merges the two files and shows the lines around `LOG_LEVEL`: `DEBUG`, from the
overlay. **Later `-f` wins**, key by key.

**4. See what the UAT shape resolves to.**

```bash
docker compose -f compose.yaml -f compose.uat.yaml config | grep -E "LOG_LEVEL|replicas|memory:"
```
**What this does:** `grep -E` with `|` means "any of these words". You see `INFO`, `replicas: 3`
and the memory limits — and no published database port.

**5. Confirm the database port really is gone.**

```bash
docker compose -f compose.yaml -f compose.uat.yaml config | grep -A3 "^  db:" | grep -c "published"
```
**What this does:** counts lines mentioning a published port in the `db` service. It prints `0`.
(`grep -c` printing `0` also exits non-zero, which is why nothing else is chained to it.)

**6. Now meet the file Compose loads without being asked.**

```bash
cp compose.dev.yaml compose.override.yaml
```
**What this does:** `cp` copies a file. `compose.override.yaml` is special: Compose merges it
**automatically**, with no `-f` at all.

**7. Prove it.**

```bash
docker compose config | grep -m1 "LOG_LEVEL"
```
**What this does:** a plain `docker compose config` — no `-f` — and the value is `DEBUG`, from the
override file. `-m1` stops at the first match. **This is the single most common "it works on my
machine" cause in Compose projects.**

**8. Remove it again.**

```bash
rm compose.override.yaml
```
**What this does:** deletes the automatic overlay, so the rest of this lab (and Lab 08) behaves as
written. Keep overlays explicit: name them and pass `-f`.

> 🔑 **The rule.** Scalars (a string, a number) are replaced by the later file. Most lists are
> appended to, which is why `ports: []` is how you *remove* a published port rather than
> overriding it. When in doubt, run `config` — never assume.

---

## Part 4 — Tooling that does not start by default (8 min)

**1. Add two tools behind profiles.** One command, ending at `EOF`:

```bash
cat > compose.tools.yaml <<'EOF'
# Optional tooling. Nothing here starts unless its profile is asked for.
services:
  pgadmin:
    image: dpage/pgadmin4:8.12
    profiles: ["tools"]
    environment:
      PGADMIN_DEFAULT_EMAIL: dev@example.com
      PGADMIN_DEFAULT_PASSWORD: pgadmin_dev_only
      PGADMIN_CONFIG_SERVER_MODE: "False"
    ports:
      - "127.0.0.1:5050:80"
    depends_on:
      db: { condition: service_healthy }
    networks: [paytrack-net]

  dbshell:
    image: postgres:16-alpine
    profiles: ["tools"]
    entrypoint: ["sleep", "infinity"]     # a container to exec psql in
    networks: [paytrack-net]
EOF
```
**What this does:** adds a database GUI and a throw-away shell container, both tagged with the
`tools` profile.

**2. Start the stack as usual.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml up -d
```
**What this does:** starts **only** db, api and proxy. The two profiled services are ignored —
that is the point of a profile.

**3. Prove they did not start.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml ps --services
```
**What this does:** lists the running services. `pgadmin` and `dbshell` are absent.

**4. Now ask for them.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml --profile tools up -d
```
**What this does:** `--profile tools` opts in, so pgadmin and dbshell start alongside the stack.
The first run pulls the pgAdmin image, which is large — give it a minute.

**5. Check they are up.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml --profile tools ps
```
**What this does:** now five services. pgAdmin is on **http://localhost:5050** if you want to look
(sign in with the email and password from the file).

**6. Use the throw-away shell.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml exec dbshell psql -h db -U paytrack -d paytrack -c "SELECT count(*) FROM authorisations;"
```
**What this does:** runs `psql` **inside** the tooling container, connecting to `db` by service
name. You never needed to publish the database port to do this.

**7. Stop just the tooling.**

```bash
docker compose -f compose.yaml -f compose.tools.yaml --profile tools stop pgadmin dbshell
```
**What this does:** stops the two tools and leaves the stack running.

> 🔑 **Profiles replace commenting services out.** The file stays one file, git stops showing
> churn, and nobody accidentally ships a database GUI to a shared environment. `COMPOSE_PROFILES=tools`
> in your shell has the same effect as typing `--profile tools` every time.

---

## Part 5 — Limits, and watching them bite (10 min)

**1. Start the stack in its UAT shape.**

```bash
docker compose -f compose.yaml -f compose.uat.yaml up -d
```
**What this does:** applies the limits you wrote in Part 3 and scales the API to three instances.

**2. Confirm the limit reached the container.**

```bash
docker inspect $(docker compose -f compose.yaml -f compose.uat.yaml ps -q api | head -1) --format 'memory limit: {{.HostConfig.Memory}} bytes, cpus: {{.HostConfig.NanoCpus}}'
```
**What this does:** `ps -q` prints container ids, `head -1` takes the first, and `inspect --format`
asks that container what limits it was given. You get `268435456` bytes — 256 MB — not `0`
(unlimited).

**3. Watch live usage.**

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```
**What this does:** `--no-stream` takes one snapshot instead of updating forever. `MemUsage` shows
usage **against the limit**, so you can see how much headroom each container really has.

**4. Push memory past the limit on purpose.**

```bash
docker compose -f compose.yaml -f compose.uat.yaml exec -T api python -c "b=bytearray()
for _ in range(60): b.extend(bytes(10**7))
print('allocated 600 MB')" ; echo "exit code: $?"
```
**What this does:** allocates about 600 MB inside a container limited to 256 MB. The kernel's
out-of-memory killer ends the process: you see a non-zero exit code — commonly **137**, which is
128 + 9 (SIGKILL) — and `allocated 600 MB` is never printed.

**5. See what Compose did about it.**

```bash
docker compose -f compose.yaml -f compose.uat.yaml ps
```
**What this does:** the API containers are still up: you killed a process you started with `exec`,
not the service's main process. Had gunicorn itself exceeded the limit, `restart: unless-stopped`
would have brought it back — and a restart loop with exit 137 always means "the limit is too low,
or the app leaks".

**6. Check the log limits.**

```bash
docker inspect $(docker compose -f compose.yaml -f compose.uat.yaml ps -q api | head -1) --format '{{json .HostConfig.LogConfig}}'
```
**What this does:** prints the logging driver and its options: `max-size` 10m and `max-file` 3, so
that container can never use more than 30 MB of disk on logs. Without those two lines, a chatty
service fills the disk — quietly, over weeks.

---

## Part 6 — Everyday operations people miss (7 min)

**1. Run a one-off command in a fresh container.**

```bash
docker compose run --rm api python -c "from src import config; print('version', config.Config.VERSION, '· db configured:', bool(config.Config.DATABASE_URL))"
```
**What this does:** `run` starts a **new** container for one command and `--rm` deletes it
afterwards — the right tool for migrations, one-off scripts and checks. (`exec`, by contrast, runs
inside a container that is already serving traffic.)

**2. Scale the API up.**

```bash
docker compose up -d --scale api=4
```
**What this does:** runs four API containers behind the proxy. `--scale` overrides the `replicas`
in the file. This only works because the `api` service has no fixed `container_name` — two
containers cannot share a name.

**3. Watch the proxy spread requests across them.**

```bash
for i in $(seq 8); do curl -s localhost:8080/api/v1/info | python3 -c "import sys,json; print(json.load(sys.stdin)['host'])"; done
```
**What this does:** makes eight requests and prints the hostname that answered each. `for … do …
done` repeats a command; `$(seq 8)` is the numbers 1 to 8. You should see several different
container ids — nginx load-balancing by service-name DNS.

**4. Read recent logs for one service.**

```bash
docker compose logs --since 5m --tail 20 api
```
**What this does:** the last 20 lines from the past 5 minutes, for the API only. During an incident
`--since` is what stops you scrolling through yesterday.

**5. Scale back down.**

```bash
docker compose up -d --scale api=2
```
**What this does:** stops the extra containers. Compose removes the newest ones first.

---

## Part 7 — Destroy the database, and bring it back (12 min)

A backup nobody has restored is a rumour. This part makes one and uses it.

**1. Put some data in.**

```bash
curl -s -X POST localhost:8080/api/v1/authorisations -H 'Content-Type: application/json' -d '{"merchant":"BACKUP TEST","amount_minor":1234,"currency":"GBP","card_last4":"4242"}' | python3 -m json.tool
```
**What this does:** records one authorisation through the proxy, and prints the stored row.

**2. Count what is in the table.**

```bash
docker compose exec -T db psql -U paytrack -d paytrack -c "SELECT count(*) FROM authorisations;"
```
**What this does:** `exec -T` runs a command in the running database container without a terminal
(`-T` matters when the output is piped or scripted). Note the number.

**3. Make a folder for backups, outside the repository.**

```bash
mkdir -p ~/devops-course/backups
```
**What this does:** backups must never be committed — this folder is outside your git project.

**4. Take a logical backup.**

```bash
docker compose exec -T db pg_dump -U paytrack -d paytrack > ~/devops-course/backups/paytrack-$(date +%Y%m%d-%H%M).sql
```
**What this does:** `pg_dump` writes the database as SQL statements, and `>` saves that stream to a
file named with today's date and time. A logical dump is safe to take while the database is
running — a file-level copy of the volume is not.

**5. Check the backup is real.**

```bash
ls -lh ~/devops-course/backups/
```
**What this does:** lists the file with a human-readable size (`-h`). A few kilobytes is right; zero
bytes means the dump failed and you should read the error before going further.

**6. Look inside it.**

```bash
grep -c "INSERT INTO\|COPY public.authorisations" ~/devops-course/backups/*.sql
```
**What this does:** counts the lines that carry your data. `pg_dump` uses `COPY` by default, so
one matching line is expected — the data follows it.

**7. Now destroy everything.**

```bash
docker compose down -v
```
**What this does:** stops the containers, removes the network **and deletes the named volume** —
`paytrack-pgdata`, with the database inside it. This is the command people run by accident.

**8. Prove the volume is gone.**

```bash
docker volume ls --filter name=paytrack-pgdata
```
**What this does:** lists matching volumes. Only the header line prints: there are none.

**9. Start the stack again.**

```bash
docker compose up -d
```
**What this does:** creates a fresh, empty volume and runs `db/init.sql`, so the schema exists but
your row does not.

**10. Wait for the database to be ready.**

```bash
until docker compose exec -T db pg_isready -U paytrack -d paytrack >/dev/null 2>&1; do sleep 2; done; echo "db is ready"
```
**What this does:** `until … do … done` repeats the check every two seconds until it succeeds, then
prints the message. This is the shell version of what `condition: service_healthy` does for you.

**11. Confirm the data really is gone.**

```bash
docker compose exec -T db psql -U paytrack -d paytrack -c "SELECT count(*) FROM authorisations;"
```
**What this does:** the count is back to whatever `init.sql` seeds — your `BACKUP TEST` row is not
there.

**12. Restore the backup.**

```bash
cat ~/devops-course/backups/*.sql | docker compose exec -T db psql -U paytrack -d paytrack
```
**What this does:** `cat` streams the file and `|` feeds it to `psql` inside the container, which
runs every statement. Expect a wall of `COPY 1`, `ALTER TABLE` and similar output — and possibly
errors about objects that already exist, which is normal when restoring into an initialised schema.

**13. Prove the data is back.**

```bash
docker compose exec -T db psql -U paytrack -d paytrack -c "SELECT merchant, amount_minor FROM authorisations WHERE merchant = 'BACKUP TEST';"
```
**What this does:** your row is listed. **You have now tested a restore** — which is the only thing
that turns a backup into a backup.

> 🔑 **Two kinds of backup.** A *logical* dump (`pg_dump`) is portable and safe while running. A
> *file-level* copy of the volume — `docker run --rm -v paytrack-pgdata:/data -v "$PWD":/backup
> alpine tar czf /backup/pgdata.tgz -C /data .` — is faster for big volumes but **must** be taken
> with the database stopped, or it is a copy of a half-written file.

---

## Part 8 — Commit, and leave the stack as Lab 08 expects it (5 min)

**1. Check nothing unexpected is lying around.**

```bash
git status -s
```
**What this does:** you should see three new files: `compose.dev.yaml`, `compose.uat.yaml` and
`compose.tools.yaml`. If `compose.override.yaml` appears, delete it — Part 3 command 8.

**2. Stage them by name.**

```bash
git add compose.dev.yaml compose.uat.yaml compose.tools.yaml
```
**What this does:** stages exactly those three.

**3. Commit.**

```bash
git commit -m "build: split the Compose stack into dev, uat and tooling overlays

compose.dev.yaml is the laptop shape (one replica, DEBUG logging, database
port on loopback). compose.uat.yaml is the shared-machine shape: three
replicas, CPU/memory limits, capped log files and no published database
port. compose.tools.yaml puts pgAdmin and a psql container behind the
'tools' profile so neither starts by default."
```
**What this does:** one command over several lines — copy all of it, both quote marks included.

**4. Put the stack back to the plain Lab 07 shape.**

```bash
docker compose up -d
```
**What this does:** no `-f` overlays, so Lab 08 sees exactly what it expects.

**5. Confirm.**

```bash
docker compose ps
```
**What this does:** db, two api containers and proxy, all up. Lab 08 can start.

---

## What overrode what

| Where a value came from | Beats | Example in this lab |
|---|---|---|
| `compose.yaml` | the defaults | `LOG_LEVEL: INFO` |
| `compose.override.yaml` (automatic) | `compose.yaml` | `DEBUG`, with no `-f` at all — Part 3 |
| A later `-f` file | every earlier `-f` | `compose.uat.yaml` setting `replicas: 3` |
| A command-line flag | every file | `--scale api=4` beating `replicas` |
| An environment variable | the file's default | `${POSTGRES_PASSWORD:-paytrack_dev_only}` |

---

## 🧩 Stretch (homework)

1. **`COMPOSE_FILE`.** Put `COMPOSE_FILE=compose.yaml:compose.dev.yaml` in a `.env` file and
   confirm a plain `docker compose up -d` uses both. Then explain why this is friendlier than an
   automatic `compose.override.yaml`.
2. **Required variables.** Change the database password to `${POSTGRES_PASSWORD:?set it in .env}`
   and run `docker compose config` with the variable unset. A stack that refuses to start beats one
   that starts with a default password.
3. **`docker compose watch`.** Add a `develop: watch:` block that syncs `app/src` into the running
   container and restarts it on change, then edit a file and watch it reload.
4. **Automate the restore test.** Write a script that dumps, runs `down -v`, brings the stack up,
   restores, and fails if the row count does not match. Run it in CI weekly — that is what turns a
   backup policy into evidence.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Values you did not set appear in `config` | `compose.override.yaml` exists | `ls compose.override.yaml`, then delete it or pass `-f` explicitly |
| `service "pgadmin" has profiles ["tools"]` and will not start | You forgot the flag | Add `--profile tools` to the command |
| `no such service: pgadmin` | You dropped `-f compose.tools.yaml` from a later command | Every command in Part 4 needs both `-f` files |
| `port is already allocated` | Something else has 8080 or 5432 | `sudo lsof -i :8080`, stop it, or change the published port in an overlay |
| The memory test prints nothing and no error | The container had more headroom than you allocated | Lower the limit in `compose.uat.yaml`, `up -d` again, repeat |
| `psql: FATAL: role "paytrack" does not exist` after a restore | The volume was recreated but `init.sql` had not finished | Wait for `pg_isready` (Part 7 command 10) and restore again |
| Errors about objects existing during the restore | You restored into an initialised schema | Normal — check the row count, which is the thing that matters |
| `docker compose down -v` deleted data you wanted | There was no backup | This lab exists to make that impossible next time |

---

## 🎯 Outcome

You can read what Compose will really run, split a stack into environment overlays without
duplicating it, keep tooling out of the default stack, put limits on CPU, memory and logs and prove
they apply, operate a stack with one-off containers and scaling — and you have restored a database
you deliberately destroyed.

**Next:** [Lab 08A — Hardening and Troubleshooting the Runtime](../lab-08-docker-networking-volumes/README-08A-hardening-and-troubleshooting.md),
or carry on with [Lab 08](../lab-08-docker-networking-volumes/README.md).

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 7 is the one they remember.** Run `down -v` on the projector after the backup, watch the
  room flinch, then restore. Ask how many of them could do that with today's production database,
  and how recently anyone tried.
- **Part 3 command 7 is the "aha".** A plain `docker compose config` picking up
  `compose.override.yaml` explains a whole class of environment drift. Leave the file in place for
  a moment before deleting it.
- **Things that go wrong:**
  1. Delegates forget `-f compose.tools.yaml` on the follow-up commands and get *no such service*.
  2. The memory test does nothing because the container had room — lower the limit and repeat.
  3. Someone leaves `compose.override.yaml` behind and Lab 08's output does not match. Part 8
     command 1 catches it.
- **Debrief question:** "Your UAT and production Compose files have drifted. Which command in this
  lab would have shown you that in one line, and where would you run it?"
</details>
