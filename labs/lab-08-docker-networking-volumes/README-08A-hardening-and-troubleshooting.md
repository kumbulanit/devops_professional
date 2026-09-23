# Lab 08A — Hardening and Troubleshooting the Runtime

| | |
|---|---|
| **Day** | 3 — **optional**, after class or as homework |
| **Duration** | About 60 minutes, in eight parts |
| **Module** | 3 — Containers with Docker (the Day 3 *Going Further* slides, section C) |
| **Slides** | `Lab08A_Advanced_Hardening.pptx` — in this folder, 9 slides, read it first |
| **Parent lab** | [Lab 08 — Networking and Volumes: Prove It, Don't Assume It](README.md) |
| **You will produce** | A `docker run` line you could defend in a security review, and the six commands you would actually use to investigate a container at 3 a.m. |
| **Feeds into** | Nothing — but Lab 11 (Kubernetes securityContext) and Lab 17 (DevSecOps) are the same ideas with a scheduler in front |

---

## Objective

Lab 06 built a hardened *image*. This lab hardens the **runtime** — the flags on the command that
starts the container — and proves each control with the kernel's own output rather than with
documentation.

Then it does the other half of the job: getting information out of a container that is
misbehaving, including one with no shell in it.

## Prerequisites

- **Lab 06 complete** — the image `paytrack-api:1.0.0` exists
- **Docker running**
- Parts 5 and 6 read host firewall rules. They need **Linux** (the course's Ubuntu machine or VM)
  and `sudo`. On Docker Desktop for Mac or Windows the rules live inside a hidden VM — those two
  parts say so, and can be read rather than run.

---

## Before you start — how to run the commands

**No Linux experience needed.** Every instruction is **one command in one grey box**, numbered in
the order you run it.

- **Open a terminal** with `Ctrl` + `Alt` + `T`; it shows a line ending in `$`, the prompt.
- **Run a command:** click in, paste one box with **`Ctrl` + `Shift` + `V`**, press `Enter`, wait
  for the prompt.
- **Some commands fail on purpose.** The text says so before the box; a red error where one was
  predicted means the control works.
- **`sudo` asks for your login password** and shows nothing as you type. That is normal.
- Symbols: `~` home folder · `|` pass output to the next command · `>` write a file · `$(…)` run
  this first and use its answer · `#` a note the computer ignores.

🔁 **RECOVER — if you do not have the image**

```bash
cd ~/devops-course/paytrack-api-team
```
**What this does:** moves into your project.

```bash
cd app && docker build -t paytrack-api:1.0.0 . && cd ..
```
**What this does:** rebuilds the Lab 06 image and returns to the project root.

---

## Part 1 — What a container can do by default (8 min)

**1. Look at the capabilities a normal container gets.**

```bash
docker run --rm alpine sh -c "grep CapEff /proc/self/status"
```
**What this does:** every Linux process has a set of **capabilities** — individual privileges such
as "change file ownership" or "bind a low port" — and `/proc/self/status` is the kernel telling you
which ones this process holds. You get a long hexadecimal number such as `00000000a80425fb`: not
root over the host, but more privilege than an application needs.

**2. Drop all of them.**

```bash
docker run --rm --cap-drop ALL alpine sh -c "grep CapEff /proc/self/status"
```
**What this does:** prints `CapEff: 0000000000000000` — **zero**. This is the kernel's own answer,
not a claim in a README.

**3. See what that stops.** This fails on purpose.

```bash
docker run --rm --cap-drop ALL alpine sh -c "chown nobody /etc/hosts"
```
**What this does:** `chown` needs the `CHOWN` capability, which the container no longer has. You
get `Operation not permitted` and a non-zero exit. Without `--cap-drop`, the same command
succeeds — that is the difference the flag makes.

**4. Add back only what is needed.**

```bash
docker run --rm --cap-drop ALL --cap-add CHOWN alpine sh -c "chown nobody /etc/hosts && echo 'CHOWN allowed again'"
```
**What this does:** drops everything, then grants one capability by name. The message prints. **Drop
all, add back the few you can justify** — that sentence is the whole practice.

**5. Stop privilege escalation inside the container.**

```bash
docker run --rm --security-opt no-new-privileges:true alpine sh -c "grep NoNewPrivs /proc/self/status"
```
**What this does:** prints `NoNewPrivs: 1`. With that flag, a setuid binary inside the container
cannot raise the process's privileges — closing the usual next step after a break-in.

---

## Part 2 — A read-only container (8 min)

**1. Prove the filesystem is writable by default.**

```bash
docker run --rm alpine sh -c "touch /evil && ls -l /evil"
```
**What this does:** creates a file in the image's filesystem. Anything that gets code execution can
write a tool, a miner or a backdoor here.

**2. Make it read-only.** This fails on purpose.

```bash
docker run --rm --read-only alpine sh -c "touch /evil"
```
**What this does:** `touch: /evil: Read-only file system`. The container can still *read* its image;
it can no longer modify it.

**3. Give it somewhere legitimate to write.**

```bash
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m alpine sh -c "touch /tmp/scratch && echo 'writable: /tmp only'"
```
**What this does:** mounts a small in-memory filesystem at `/tmp`. `noexec` means nothing there can
be run, `nosuid` ignores setuid bits, `size=64m` caps it. Real applications need scratch space; this
gives them exactly that and nothing more.

**4. Run the real application read-only.**

```bash
docker run -d --name paytrack-hard --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop ALL --security-opt no-new-privileges:true --memory 256m --pids-limit 200 -p 8081:8080 paytrack-api:1.0.0
```
**What this does:** starts PayTrack API with every control from this lab at once, on host port 8081
so it cannot clash with the Lab 07 stack. This is the line you would put in a review.

**5. Check it actually serves traffic.**

```bash
sleep 5 && curl -s localhost:8081/health
```
**What this does:** waits five seconds for gunicorn to start, then asks the health endpoint. You get
`{"status":"ok", …}` — **hardening did not break it**, which is the point worth proving before
anyone argues about it.

**6. Confirm the container's own view of itself.**

```bash
docker inspect paytrack-hard --format 'read-only: {{.HostConfig.ReadonlyRootfs}} · caps dropped: {{.HostConfig.CapDrop}} · security: {{.HostConfig.SecurityOpt}} · memory: {{.HostConfig.Memory}} · pids: {{.HostConfig.PidsLimit}}'
```
**What this does:** asks Docker what it applied, in one line. Every value should be non-empty — an
empty `Memory` of `0` means unlimited, which is what you are trying to avoid.

**7. Check which user it runs as.**

```bash
docker exec paytrack-hard id
```
**What this does:** prints `uid=10001 gid=10001`. The image already drops root (Lab 06); the runtime
flags assume it. Root inside a container is root on a mounted volume — that is why both halves
matter.

---

## Part 3 — Limits, and what happens when they are hit (10 min)

**1. Start a container that will ask for too much memory.**

```bash
docker run -d --name hog --memory 64m python:3.12-slim python -c "b=bytearray()
for _ in range(50): b.extend(bytes(10**7))
print('never printed')"
```
**What this does:** allocates about 500 MB inside a 64 MB limit. `-d` returns immediately; the
container is already dying.

**2. Wait for it to finish and read the exit code.**

```bash
docker wait hog
```
**What this does:** blocks until the container exits, then prints its exit code: **137**. That is
128 + 9 — the process was killed with SIGKILL.

**3. Ask who killed it.**

```bash
docker inspect hog --format 'OOMKilled: {{.State.OOMKilled}} · exit: {{.State.ExitCode}}'
```
**What this does:** prints `OOMKilled: true · exit: 137`. The kernel's out-of-memory killer ended
it because of your limit — the application did not crash, it was stopped.

**4. Remove it.**

```bash
docker rm hog
```
**What this does:** deletes the stopped container.

**5. Now limit the number of processes.** This fails on purpose.

```bash
docker run --rm --pids-limit 5 alpine sh -c 'for i in $(seq 20); do sleep 30 & done; wait'
```
**What this does:** tries to start twenty background processes where only five are allowed. You get
`can't fork` errors. A `--pids-limit` is the cheap insurance against a runaway loop — or a fork
bomb — taking the host with it.

**6. Limit CPU and see it applied.**

```bash
docker run -d --name cpu-capped --cpus 0.25 alpine sh -c "while true; do :; done"
```
**What this does:** starts an infinite loop limited to a quarter of one core.

**7. Watch it.**

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" cpu-capped
```
**What this does:** `--no-stream` takes one snapshot. The CPU column sits near **25%**, not 100%.
Without the flag that loop would consume a whole core and slow everything else down.

**8. Stop it.**

```bash
docker rm -f cpu-capped
```
**What this does:** kills and removes the container in one step.

> 🔑 **These are the same numbers you will see in Kubernetes.** A pod in `CrashLoopBackOff` with
> exit code 137 is this OOM kill, with a scheduler restarting it. Lab 10 sets `requests` and
> `limits` for exactly this reason.

---

## Part 4 — Investigating a container (10 min)

**1. Start the Lab 07 stack, so there is something realistic to look at.**

```bash
cd ~/devops-course/paytrack-api-team && docker compose up -d
```
**What this does:** brings up db, api and proxy in the background.

**2. Snapshot resource use across the stack.**

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```
**What this does:** one line per running container: CPU, memory against its limit, and network in
and out. This reads the kernel's cgroup counters — no agent, no instrumentation.

**3. Read the container event log.**

```bash
docker events --since 30m --until now --filter type=container --format '{{.Time}} {{.Actor.Attributes.name}} {{.Action}}' | tail -20
```
**What this does:** every container lifecycle event of the last 30 minutes — `create`, `start`,
`die`, `health_status`, `oom`. `--until now` makes it print and exit instead of following forever.
This is the first place to look for "it restarted at some point last night".

**4. Ask one precise question of one container.**

```bash
docker inspect paytrack-db --format 'status={{.State.Status}} restarts={{.RestartCount}} health={{.State.Health.Status}} started={{.State.StartedAt}}'
```
**What this does:** `--format` pulls exactly the fields you asked for out of a very large JSON
document. A rising `RestartCount` is the single most useful number on a sick container.

**5. Read the last health check the database ran.**

```bash
docker inspect paytrack-db --format '{{json .State.Health}}' | python3 -m json.tool | tail -14
```
**What this does:** prints the recent health-check log — the command, its exit code and its output.
When a container is stuck `unhealthy`, this tells you why without guessing.

**6. See what is listening inside the API container.**

```bash
docker compose exec -T api python -c "import socket,os;s=socket.socket();print('pid 1 is', open('/proc/1/cmdline').read().replace(chr(0),' '));print('hostname', socket.gethostname())"
```
**What this does:** runs a tiny Python program inside the running API container to print what PID 1
actually is and which host it thinks it is. The image has no `ps`, so you use what it *does* have.

---

## Part 5 — Debugging a container with no shell (8 min)

The production image is deliberately minimal. When there is no shell, you do not add one to the
image — you bring a second container and **join its namespaces**.

**1. Find the container you want to inspect.**

```bash
docker compose ps -q api | head -1
```
**What this does:** prints the id of the first API container. `ps -q` prints ids only.

**2. Store it.**

```bash
API=$(docker compose ps -q api | head -1)
```
**What this does:** keeps that id under the name `API` for this terminal window. Nothing is printed.

**3. Borrow a toolbox and use the API container's network.**

```bash
docker run --rm --network container:$API nicolaka/netshoot curl -s -o /dev/null -w "health check from inside the app's network: %{http_code}\n" http://localhost:8080/health
```
**What this does:** `--network container:<id>` puts the new container **in the same network
namespace** as the API — so `localhost` there is the API's `localhost`. `netshoot` is a
troubleshooting image full of network tools. It prints `200`. The first run downloads the image.

**4. Resolve a service name the way the app does.**

```bash
docker run --rm --network container:$API nicolaka/netshoot nslookup db
```
**What this does:** asks Docker's embedded DNS for the database's address, from inside the app's
network view. This is how you prove a name-resolution problem is real rather than suspected.

**5. See the app's own open connections.**

```bash
docker run --rm --network container:$API nicolaka/netshoot ss -tunp
```
**What this does:** `ss` lists sockets: listening ports and established connections — including the
one to PostgreSQL on 5432. Nothing was installed into the application image to get this.

**6. Attach a debug shell to a running container (Docker 20.10+).**

```bash
docker debug --help >/dev/null 2>&1 && echo "docker debug is available (Docker Desktop)" || echo "docker debug not available - use the netshoot pattern above"
```
**What this does:** `docker debug` (Docker Desktop, subscription feature) attaches a shell with
tools to any container, even a distroless one. The `&&`/`||` pair prints which route is open to
you. The netshoot pattern works everywhere, including servers.

---

## Part 6 — Where a published port really goes (8 min · **Linux hosts only**)

> **On Docker Desktop for Mac or Windows, skip to Part 7.** Your rules live inside a hidden Linux
> VM and `iptables` on your machine will not show them. Read this part rather than running it — the
> lesson still applies to every Linux server you deploy to.

**1. Confirm the hardened container is still publishing 8081.**

```bash
docker ps --filter name=paytrack-hard --format "table {{.Names}}\t{{.Ports}}"
```
**What this does:** shows `0.0.0.0:8081->8080/tcp` — reachable from **any** address on your network,
not only from this machine.

**2. Find the rule Docker wrote for it.**

```bash
sudo iptables -t nat -L DOCKER -n | grep 8081
```
**What this does:** lists the NAT rules Docker maintains and picks the one for your port. You see a
`DNAT` line redirecting traffic to the container's private address. **Docker wrote a firewall rule
on your behalf when you typed `-p`.**

**3. See why UFW does not protect it.**

```bash
sudo ufw status | head -5
```
**What this does:** prints your firewall's policy. Even with UFW active and denying incoming
traffic, the DNAT above is evaluated **before** UFW's rules — so the port is open anyway. This
surprises people with a database published "behind a firewall".

**4. Block it in the chain Docker leaves for you.**

```bash
sudo iptables -I DOCKER-USER -p tcp --dport 8081 -j DROP
```
**What this does:** `DOCKER-USER` is a chain Docker evaluates first and never rewrites — the
supported place for your own rules. `-I` inserts at the top.

**5. Prove the block works.**

```bash
curl -s --max-time 3 localhost:8081/health || echo "blocked, as intended"
```
**What this does:** the request times out and the fallback message prints. (Traffic from the host
itself may still pass depending on your kernel's routing — try it from another machine on your
network for the real test.)

**6. Remove your rule again.**

```bash
sudo iptables -D DOCKER-USER -p tcp --dport 8081 -j DROP
```
**What this does:** `-D` deletes that exact rule, leaving the chain as you found it.

**7. The better answer: do not publish it at all.**

```bash
docker run --rm -d --name loopback-only -p 127.0.0.1:8082:8080 paytrack-api:1.0.0
```
**What this does:** publishes to **loopback only**, so the port exists for this machine and is
invisible to the network. Lab 07's `compose.yaml` does exactly this for PostgreSQL.

**8. Confirm what that looks like.**

```bash
docker ps --filter name=loopback-only --format "{{.Ports}}"
```
**What this does:** prints `127.0.0.1:8082->8080/tcp` — note the address in front. Compare with
command 1's `0.0.0.0`, which means "everywhere".

**9. Remove it.**

```bash
docker rm -f loopback-only
```
**What this does:** stops and deletes that container.

---

## Part 7 — Volumes: back one up, and get the permissions right (8 min)

**1. Create a volume with something in it.**

```bash
docker run --rm -v demo-vol:/data alpine sh -c "echo 'ledger row 1' > /data/ledger.txt && echo 'ledger row 2' >> /data/ledger.txt && ls -l /data"
```
**What this does:** creates the named volume `demo-vol` on first use and writes two lines into it.
The container is deleted straight away — the volume is not.

**2. Back it up to a file.**

```bash
docker run --rm -v demo-vol:/data:ro -v "$PWD":/backup alpine tar czf /backup/demo-vol.tgz -C /data .
```
**What this does:** mounts the volume **read-only** (`:ro`) and the current folder as `/backup`,
then `tar` packs the contents into an archive. `-C /data .` means "everything inside /data, without
the folder name". This is the pattern for any volume — but for a **database**, stop the container
first, or use `pg_dump` (Lab 07A Part 7).

**3. Check the archive exists.**

```bash
ls -lh demo-vol.tgz
```
**What this does:** a small file, listed with a human-readable size.

**4. Destroy the volume.**

```bash
docker volume rm demo-vol
```
**What this does:** deletes it permanently. There is no undo.

**5. Restore it.**

```bash
docker run --rm -v demo-vol:/data -v "$PWD":/backup alpine sh -c "tar xzf /backup/demo-vol.tgz -C /data && cat /data/ledger.txt"
```
**What this does:** recreates the volume, unpacks the archive into it, and prints the contents —
your two lines are back.

**6. See the ownership problem bind mounts cause.**

```bash
docker run --rm -v "$PWD":/work -u 10001:10001 alpine sh -c "touch /work/owned-by-10001 && ls -l /work/owned-by-10001"
```
**What this does:** writes into your project folder as uid 10001 — the user the PayTrack image runs
as. The file appears on **your** disk owned by a user that does not exist on your machine. This is
why "permission denied" on a bind mount is usually a uid mismatch, not Docker being broken.

**7. Clean up that file.**

```bash
rm -f owned-by-10001 demo-vol.tgz && docker volume rm demo-vol
```
**What this does:** removes the test file, the archive and the volume. If `rm` says permission
denied, prefix it with `sudo` — you are deleting a file owned by another uid.

---

## Part 8 — Reclaiming disk, safely (5 min)

**1. Find out what is actually using space.**

```bash
docker system df
```
**What this does:** four buckets — Images, Containers, Local Volumes, Build Cache — each with a
`RECLAIMABLE` column. **Always start here.** Most "I am out of disk" cases are build cache.

**2. See the detail.**

```bash
docker system df -v | head -30
```
**What this does:** `-v` lists individual images, containers and volumes with their sizes, so you
can see which one is the problem rather than deleting everything.

**3. Delete the safe thing first.**

```bash
docker builder prune -f
```
**What this does:** deletes the build cache. `-f` skips the confirmation. Nothing you are running is
affected; your next build is slower once.

**4. Remove stopped containers.**

```bash
docker container prune -f
```
**What this does:** deletes containers that have exited. Running ones are untouched.

**5. Check the result.**

```bash
docker system df
```
**What this does:** compare with command 1.

> 🔴 **The two dangerous ones.** `docker volume prune` deletes every volume no **running or
> stopped** container references — a stopped stack's database qualifies. `docker system prune -a
> --volumes` does that *and* removes every unused image. Only run them on a machine you are happy to
> rebuild, and never as a reflex when a disk alert fires.

**6. Clean up this lab's containers.**

```bash
docker rm -f paytrack-hard 2>/dev/null; docker ps --format "table {{.Names}}\t{{.Status}}"
```
**What this does:** removes the hardened container (`2>/dev/null` hides the error if it is already
gone) and lists what is still running — the Lab 07 stack, ready for whatever you do next.

---

## The hardened run line, and what each part buys you

```bash
docker run -d --name paytrack \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --memory 256m --cpus 0.5 --pids-limit 200 \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  paytrack-api:1.0.0
```

| Flag | Stops | Proved in |
|---|---|---|
| `--read-only` + `--tmpfs` | Writing tools or malware into the filesystem | Part 2 |
| `--cap-drop ALL` | Almost every privileged syscall path | Part 1 |
| `--security-opt no-new-privileges` | A setuid binary escalating inside | Part 1 |
| `--memory` / `--cpus` | One container starving the host | Part 3 |
| `--pids-limit` | A fork bomb or runaway loop | Part 3 |
| `-p 127.0.0.1:…` | The service being exposed to the whole network | Part 6 |
| *(the image)* `USER 10001` | Root on a mounted volume | Part 2, command 7 |

**What none of it gives you:** a hard boundary. This is a shared kernel. These flags make an escape
much harder and a compromise much less useful; multi-tenant isolation still needs a virtual machine.

---

## 🧩 Stretch (homework)

1. **Seccomp.** Run `docker run --rm --security-opt seccomp=unconfined alpine …` and compare with
   the default profile. Then write a profile that blocks one syscall and prove it.
2. **User namespaces.** Turn on `userns-remap` in `/etc/docker/daemon.json`, restart Docker, and
   check `ls -ln /var/lib/docker/*.*` — root inside the container is now an unprivileged uid on the
   host.
3. **Prove the UFW gap to a colleague.** Publish a container on `0.0.0.0` with UFW denying
   incoming, then reach it from a second machine on the same network. Write down what you would
   change in your own deployment.
4. **Compare with Kubernetes.** Read Lab 11's `securityContext` block and map each field to a flag
   from this lab: `runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities.drop`,
   `allowPrivilegeEscalation`, `resources.limits`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running | Start it; log out and back in if you were just added to the `docker` group |
| `chown: Operation not permitted` in Part 1 | That is the exercise | It proves `--cap-drop ALL` works |
| The app fails to start with `--read-only` | It writes somewhere other than `/tmp` | `docker logs <name>` names the path; add another `--tmpfs` for it |
| `docker wait hog` never returns | The allocation fitted inside the limit | Raise the loop count, or lower `--memory` |
| `iptables: command not found` | You are on Docker Desktop, not Linux | Part 6 is Linux-only — read it instead |
| `nicolaka/netshoot` will not pull | No network, or a restricted registry | Use `docker run --rm --network container:$API alpine sh` and work with what Alpine has |
| `$API` is empty | A new terminal window, or the stack is down | `docker compose up -d`, then set it again |
| `permission denied` deleting a file from Part 7 | It is owned by uid 10001 | `sudo rm <file>` |

---

## 🎯 Outcome

You can write a `docker run` line that drops every capability, forbids privilege escalation, runs
read-only with a small scratch space, and cannot exhaust the host's memory, CPU or process table —
and you can prove each control with the kernel's own output. You can also investigate a running
container, including one with no shell, and reclaim disk without deleting a database.

**Next:** [Lab 09 — Stand Up a Real Kubernetes Cluster](../lab-09-kubernetes-setup/README.md) —
where these same controls reappear as a `securityContext`.

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Part 1 commands 1 and 2 are the demo.** Two lines of kernel output, one with a long hex number
  and one with zeros. Nothing argues with that.
- **Part 6 is the one that changes behaviour** in banks — a "firewalled" host publishing a database
  to the LAN. If the room is on Docker Desktop, run it yourself on a Linux VM and show the output.
- **Things that go wrong:**
  1. Docker Desktop delegates try Part 6 and see nothing. The note at the top is there for that —
     say it out loud as well.
  2. The OOM demo does not trigger because the loop fitted in the limit. Lower `--memory` to 32m.
  3. Someone runs `docker system prune -a --volumes` "to tidy up" and loses the Lab 07 database.
     Cover the red box in Part 8 before letting them loose.
- **Debrief question:** "Your CI agent runs `docker run` with a mounted docker.sock and no limits.
  Using only the flags from this lab, what would you change first, and what would you tell the team
  it costs?"
</details>
