# Docker Reference

## Images
```bash
docker build -t name:tag .                    # trailing . is the BUILD CONTEXT
docker build -f Dockerfile.prod --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t n:t .
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker history img --human --format "table {{.CreatedBy}}\t{{.Size}}"   # where the MB are
docker tag src:tag registry/ns/dst:tag
docker push / pull registry/ns/img:tag
docker save img -o img.tar / docker load -i img.tar     # move images without a registry
docker rmi img
```

## Containers
```bash
docker run -d --name n -p 8080:8080 img       # detached, published
docker run --rm -it img sh                    # interactive, auto-removed
docker ps            / docker ps -a           # running / all
docker logs -f --tail=50 n                    # follow logs
docker exec -it n sh                          # shell inside a RUNNING container
docker inspect n --format '{{.State.Health.Status}}'
docker stats --no-stream                      # one-shot resource usage
docker stop n        (SIGTERM, then SIGKILL after 10s)
docker rm -f n
docker cp n:/path/in/container ./local
docker diff n                                 # what changed in the writable layer
```

## Runtime hardening — the flags that matter
```bash
docker run -d \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=256m --cpus=0.5 \
  --user 10001:10001 \
  -p 127.0.0.1:8080:8080 \
  img
```
| Flag | Effect |
|---|---|
| `--read-only` | Immutable root filesystem |
| `--cap-drop=ALL` | Remove every Linux capability |
| `--security-opt=no-new-privileges` | Block setuid escalation |
| `--memory` / `--cpus` | Bound the blast radius |
| `-p 127.0.0.1:PORT:PORT` | **Loopback only** — Docker bypasses UFW, so this matters |

## Dockerfile essentials
```dockerfile
FROM python:3.12-slim AS builder      # multi-stage: this stage is DISCARDED
WORKDIR /build
COPY requirements.txt .               # dependencies FIRST → cached
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
RUN groupadd -g 10001 app && useradd -u 10001 -g 10001 -M -s /usr/sbin/nologin app
COPY --from=builder /install /install
COPY --chown=10001:10001 src/ ./src/
USER 10001                            # DROP ROOT
EXPOSE 8080                           # documentation only
HEALTHCHECK CMD curl -fsS localhost:8080/health || exit 1
CMD ["gunicorn","--bind","0.0.0.0:8080","wsgi:app"]   # EXEC form → signals work
```

| Trap | Fix |
|---|---|
| `COPY . .` before `pip install` | Copy the dependency manifest first |
| `RUN apt install` then `RUN apt remove` | Same `RUN`, `&& rm -rf /var/lib/apt/lists/*` |
| Shell-form `CMD` | Exec form, or `SIGTERM` is never delivered |
| Secrets in `ARG`/`ENV` | Visible in `docker history`. Use BuildKit `--mount=type=secret` |
| No `USER` | Runs as root |
| No `.dockerignore` | Ships `.git`, `.venv`, and possibly `.env` |

## Compose
```bash
docker compose config                 # RENDER the resolved config — run this when confused
docker compose up -d --build
docker compose ps                     # state + health
docker compose logs -f svc
docker compose exec svc sh
docker compose up -d --scale api=4
docker compose restart svc
docker compose down                   # containers + network. Volumes KEPT
docker compose down -v                # ⚠️ ALSO DELETES VOLUMES — your data
```
```yaml
depends_on:
  db: { condition: service_healthy }   # WAIT FOR READY, not merely started
```

## Networking
```bash
docker network ls / create / inspect / connect / disconnect
```
| Fact | Consequence |
|---|---|
| User-defined bridge gives **container-name DNS** | Use service names, never IPs |
| Default `bridge` has **no DNS** | Always create your own network |
| `localhost` inside a container = **that container** | Use the service name for siblings |
| `host.docker.internal` | Reach the host from a container |
| Docker writes iptables **ahead of UFW** | `-p 0.0.0.0:5432` exposes the DB regardless of `ufw deny` |

## Volumes
```bash
docker volume create/ls/inspect/rm
docker run -v myvol:/data img                       # named volume — production data
docker run -v "$PWD/src:/app/src:ro" img            # bind mount — dev / config
docker run --tmpfs /run/secrets:rw,noexec,nosuid img # RAM only — secrets
# backup (no built-in command exists):
docker run --rm -v myvol:/data:ro -v "$PWD":/b alpine tar czf /b/backup.tar.gz -C /data .
```

## Housekeeping
```bash
docker system df                       # what is using disk, and what is reclaimable
docker image prune -f                  # dangling images — safe
docker builder prune -f --filter until=24h
docker system prune -a --volumes       # ⚠️ removes ALL unused images AND VOLUMES
```
