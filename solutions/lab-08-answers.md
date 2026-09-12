# Lab 08 — Answers

**1. Why does `proxy_pass http://api:8080` work with no IP address?**

Docker runs an **embedded DNS server at 127.0.0.11** on every *user-defined* network, and it
resolves container and Compose service names to their current IPs. Because pod/container IPs
change on every restart, name-based resolution is the only stable option — which is why the
default `bridge` network (which has **no** DNS) should never be used for a real stack.

This is the direct ancestor of Kubernetes Services: same problem, same solution, different
implementation.

**2. Why did `curl localhost:5432` fail inside the API container?**

Each container has its **own network namespace**, so `localhost` (127.0.0.1) refers to *that
container's* loopback interface. Nothing is listening on 5432 there — Postgres is listening on
its own loopback, in a different namespace.

Use the service name (`db:5432`), which the embedded DNS resolves to the database container's
IP on the shared network.

**3. `restart` vs `--force-recreate`.**

`docker compose restart api` stops and starts **the same container**, so its **writable layer
survives** — files written to `/tmp` are still there.

`docker compose up -d --force-recreate api` **destroys the container and creates a new one**
from the image. The writable layer is discarded; only volumes and bind mounts survive.

This matters because Kubernetes recreates pods constantly — every rollout, node failure and
scale event. Anything durable must live outside the container filesystem.

**4. `"5432:5432"` on a cloud VM with `ufw deny 5432` — is the database exposed?**

**Yes.** Docker writes its own DNAT rules into iptables' `DOCKER` chain in the `nat` table,
and these are evaluated **before** the rules UFW manages. Publishing a port therefore punches
straight through a UFW deny rule.

The fixes: bind explicitly to loopback (`-p 127.0.0.1:5432:5432`), do not publish the port at
all (containers on the same network reach it by name regardless), use
`DOCKER_OPTS="--iptables=false"` and manage the rules yourself, or place the host behind a
cloud security group that Docker cannot modify.

This is a real and repeatedly-exploited class of exposure, and it surprises experienced Linux
administrators.

**5. `down` vs `down -v`.**

`docker compose down` removes **containers and the network**. **Named volumes are kept**, so
your database survives.

`docker compose down -v` additionally removes the **named volumes declared in the compose
file** — every row in your database, with no confirmation prompt and no recovery. Use it
deliberately, never habitually.
