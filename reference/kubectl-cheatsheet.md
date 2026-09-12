# kubectl Reference

## Setup
```bash
alias k=kubectl
source <(kubectl completion bash) && complete -o default -F __start_kubectl k
kubectl config get-contexts                              # ALWAYS check before destructive commands
kubectl config use-context k3d-paytrack
kubectl config set-context --current --namespace=paytrack-dev   # stop typing -n
```

## Inspect
```bash
kubectl get pods -o wide                    # + node and pod IP
kubectl get all -l app.kubernetes.io/name=paytrack-api
kubectl get pods -w                         # watch for changes
kubectl get events --sort-by=.lastTimestamp # the most under-used debugging command
kubectl describe pod <p>                    # ← READ THE EVENTS AT THE BOTTOM FIRST
kubectl get pod <p> -o yaml                 # the full live object
kubectl explain deployment.spec.strategy    # the API's own docs, correct for YOUR version
kubectl api-resources                       # every kind, with its short name
```

## Debugging, in the order to try it
```bash
kubectl get pods                                   # 1 what state?
kubectl describe pod <p>                           # 2 EVENTS
kubectl logs <p>                                   # 3 app logs
kubectl logs <p> --previous                        # 3b the CRASHED container's logs
kubectl logs -l app=x --tail=50 --all-containers   # across all pods of a selector
kubectl exec -it <p> -- sh                         # 4 get inside
kubectl get endpointslices -l kubernetes.io/service-name=<svc>   # 5 IS THE SERVICE SELECTING ANYTHING?
kubectl debug <p> -it --image=busybox --target=<c> # ephemeral container (distroless images)
kubectl top pods / top nodes                       # resource usage (needs metrics-server)
```

| Symptom | Almost always |
|---|---|
| `Pending` | Insufficient resources · quota · unbound PVC · unsatisfiable nodeSelector |
| `ImagePullBackOff` | Wrong tag · private registry with no `imagePullSecret` |
| `CrashLoopBackOff` | App exits on start — **`logs --previous`** |
| `OOMKilled` / exit 137 | `limits.memory` too low, or a leak |
| Running but `0/1 READY` | Readiness probe failing |
| Service returns nothing | **Empty EndpointSlice** — no Ready pods, or a selector mismatch |
| `field is immutable` | You changed `spec.selector`. Delete and recreate |

## Apply and manage
```bash
kubectl apply -f dir/                       # declarative create-or-update
kubectl apply -f dir/ --dry-run=server      # FULL validation, persists nothing. Use in CI
kubectl diff -f dir/                        # what apply WOULD change
kubectl delete -f dir/
kubectl patch deployment x -p '{"spec":{"replicas":3}}'
kubectl set image deployment/x c=img:tag
kubectl set env deployment/x KEY=value
kubectl scale deployment/x --replicas=5
kubectl edit deployment x                   # ⚠️ imperative — the change is not in git
```

## Rollouts
```bash
kubectl rollout status deployment/x --timeout=120s   # BLOCKS until done; non-zero on failure
kubectl rollout history deployment/x
kubectl rollout undo deployment/x [--to-revision=3]
kubectl rollout restart deployment/x                 # re-roll with no spec change
kubectl rollout pause|resume deployment/x
```

## Access
```bash
kubectl port-forward svc/x 8888:80          # debugging only
kubectl run tmp --rm -it --image=curlimages/curl -- sh
kubectl cp <p>:/path ./local
kubectl proxy                               # authenticated proxy to the API server
```

## Nodes
```bash
kubectl get nodes -o wide
kubectl cordon <node>                       # stop scheduling new pods
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data   # evict, respecting PDBs
kubectl uncordon <node>
kubectl taint nodes <node> key=value:NoSchedule
```

## JSONPath and output
```bash
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
kubectl get deploy x -o jsonpath='{.spec.template.spec.containers[0].image}'
kubectl get secret s -o jsonpath='{.data.password}' | base64 -d
kubectl get pods --sort-by=.status.startTime
kubectl get pods -o custom-columns='NAME:.metadata.name,NODE:.spec.nodeName'
```

## Scripting primitives
```bash
kubectl wait --for=condition=Ready pod/x --timeout=120s
kubectl wait --for=condition=Available deployment/x --timeout=120s
kubectl rollout status deployment/x --timeout=120s      # the correct "is it deployed?" check
```
**Use these instead of `sleep`.** They return non-zero on timeout, which is what makes a
pipeline able to fail correctly.

## Object quick reference
| Kind | Purpose |
|---|---|
| Pod | Smallest unit; shared network + storage namespace |
| Deployment | Manages ReplicaSets → rolling updates and rollback |
| StatefulSet | Stable names + per-replica PVCs. Databases |
| DaemonSet | One pod per node. Agents |
| Job / CronJob | Run once / on a schedule |
| Service | Stable VIP + DNS to **Ready** pods |
| Ingress | HTTP routing (needs a controller pod) |
| ConfigMap / Secret | Non-confidential / confidential config |
| PVC / PV / StorageClass | Storage request / storage / dynamic provisioner |
| HPA | Scale replicas on metrics (**needs CPU requests set**) |
| PodDisruptionBudget | Minimum availability during drains and upgrades |
| NetworkPolicy | Pod-to-pod firewall (**needs a CNI that enforces it**) |
| ResourceQuota / LimitRange | Namespace caps / per-container defaults |

## Probes — the rule
```yaml
livenessProbe:  { httpGet: { path: /health } }   # NO external dependencies. Failing = RESTART
readinessProbe: { httpGet: { path: /ready  } }   # dependencies OK here. Failing = no traffic
startupProbe:   { httpGet: { path: /health }, failureThreshold: 30, periodSeconds: 2 }
```
**A liveness probe that checks the database turns a DB blip into a cluster-wide restart storm.**
