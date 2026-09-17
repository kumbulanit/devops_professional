# -*- coding: utf-8 -*-
"""Day 4 — Kubernetes for DevOps.  Module 4.

Theory-first edition: mostly theory with exercises and a live demo; Labs 09–12 are
started together at the end of the session and finished after class.
"""
import diagrams as dg

DAY4 = [
 ('title', 4, 'Kubernetes',
  'Declare what you want; let the platform close the gap',
  ['Why an orchestrator · architecture · the reconciliation loop',
   'Pods, probes, requests and limits · Deployments and rolling updates',
   'Services, Ingress · ConfigMaps, Secrets · persistent storage · autoscaling · debugging',
   'After class — Labs 09–12: build a cluster · deploy · config and storage · ingress and HPA'],
  'The idea to hold on to all day: you declare the desired state, and controllers make it true'),

 ('agenda', 'Day 4 at a glance',
  [('check', 'You said, we did — the one change from check-in 2'),
   ('theory', 'Why an orchestrator · control plane and nodes · what kubectl apply really does'),
   ('theory', 'Workloads: Pods, container patterns, the three probes, requests, limits and QoS'),
   ('exercise', 'PREDICT — a node dies at 03:00  ·  COMPARE — which probe checks the database?'),
   ('demo', 'Watch a probe take a pod out of traffic'),
   ('break', 'Break · 15 minutes'),
   ('theory', 'Deployments, rolling updates, rollback · Services, DNS, Ingress'),
   ('theory', 'ConfigMaps and Secrets — honestly · storage · autoscaling · debugging in order'),
   ('practical', 'Start Lab 09 together: build the three-node cluster'),
   ('after', 'Finish Labs 09–12 · every lab has a RECOVER block')],
  'TODAY', {'speaker': 'Open with the one change you made from check-in 2 — it is what makes the day 6 '
            'check-in honest. Anyone still missing the Lab 06 image or the Lab 07 stack needs the RECOVER '
            'blocks before Lab 10.'}),

 ('table', 'Why an orchestrator — what Compose cannot do',
  ['Requirement', 'Compose', 'Kubernetes'],
  [['A node dies at 03:00 — workloads move', '✗ No', '✔ Reschedules automatically'],
   ['Roll out a new version with zero downtime', '✗ No', '✔ Rolling update with surge and availability control'],
   ['Roll back in seconds', '✗ No', '✔ kubectl rollout undo'],
   ['Scale on CPU or custom metrics', '✗ No', '✔ HorizontalPodAutoscaler'],
   ['Pack workloads across a fleet of machines', '✗ No', '✔ The scheduler'],
   ['A stable network identity as pods come and go', '✗ No', '✔ Services'],
   ['Restart a container that is running but wedged', '✗ No', '✔ Liveness probes'],
   ['Declarative, self-healing desired state', '✗ No', '✔ Controllers']],
  'MODULE 4 §4.1 · FROM DAY 3 TO DAY 4', {'widths': [4.4, 1.6, 4.2]}),

 ('define', 'Kubernetes',
  'An open-source platform for automating the deployment, scaling and operation of containerised workloads, '
  'in which you declare a DESIRED STATE and a set of CONTROLLERS continuously act to make the observed state match it.',
  [('The word to hold on to is DECLARATIVE', 'You never say "start a container"; you say "there should be four healthy replicas"'),
   ('Controllers make it true — and KEEP it true', 'Now, after a node failure at 03:00, and after the cluster is resized'),
   ('Everything is an API object', 'Deployments, Services, Secrets — records of intent stored in etcd'),
   ('It runs the same OCI images you built on day 3', 'Through containerd, not the Docker daemon')],
  'MODULE 4 §4.1'),

 ('section', '1', 'Architecture', 'The control plane, the nodes, and the loop that runs everything',
  ['Control plane components', 'Node components', 'The reconciliation loop',
   'What kubectl apply really does', 'Namespaces']),

 ('diagram', 'Kubernetes architecture', dg.k8s_architecture, 'MODULE 4 §4.2'),

 ('table', 'The control plane — the brain',
  ['Component', 'What it does', 'Remember'],
  [['kube-apiserver', 'The only front door: authenticate → authorise (RBAC) → admission → validate → persist',
    'The ONLY component that talks to etcd'],
   ['etcd', 'A consistent key-value store holding all cluster state', 'The source of truth — back it up, encrypt it'],
   ['kube-scheduler', 'Picks a node for each unscheduled pod: filter, then score', 'It only decides; it starts nothing'],
   ['kube-controller-manager', 'Runs the built-in controllers: Deployment, ReplicaSet, Node, Job, EndpointSlice…',
    'Each one is a reconciliation loop'],
   ['cloud-controller-manager', 'Talks to a cloud provider: load balancers, routes, volumes', 'Absent on bare metal and k3d']],
  'MODULE 4 §4.2', {'widths': [2.6, 4.7, 2.9]}),

 ('table', 'The worker nodes — the muscle',
  ['Component', 'What it does', 'Remember'],
  [['kubelet', 'Watches the API server for pods assigned to this node, runs them, runs the probes, reports status',
    'It never reads your YAML file'],
   ['kube-proxy', 'Programmes iptables or IPVS so Service virtual IPs reach ready pods', 'How a ClusterIP actually works'],
   ['Container runtime', 'containerd + runc actually start the containers', 'Day 3\'s architecture, unchanged'],
   ['CNI plugin', 'Pod networking — Flannel, Calico, Cilium', 'Plus a policy controller to enforce NetworkPolicy']],
  'MODULE 4 §4.2', {'widths': [2.4, 5.0, 2.8]}),

 ('define', 'The reconciliation loop',
  'A controller continuously observes the actual state of the cluster, compares it with the '
  'declared desired state, and takes action to close the gap — forever, without being asked.',
  [('You never issue commands — you declare intent', 'kubectl apply records what you want; controllers do the work'),
   ('kubectl apply returns IMMEDIATELY', 'It has recorded intent, not completed a deployment'),
   ('Which is why kubectl rollout status exists', 'That is the command that waits, and can fail'),
   ('Delete a pod and it comes back', 'Not magic — a ReplicaSet controller observing 2 where 3 were declared'),
   ('It is also why manual kubectl edits are reverted under GitOps', 'The loop restores what git declares')],
  'MODULE 4 §4.1'),

 ('flow', 'What happens when you run kubectl apply',
  [('kubectl sends the manifest to the API server', 'Authenticated, authorised by RBAC, checked by admission, validated'),
   ('The API server writes the object to etcd', 'kubectl is now DONE — nothing is running yet'),
   ('The Deployment controller notices', 'It creates a ReplicaSet for this pod template'),
   ('The ReplicaSet controller creates Pod objects', 'Pods exist, but spec.nodeName is empty'),
   ('The scheduler binds each pod to a node', 'Filter on requests, taints and affinity; score the survivors'),
   ('The kubelet on that node starts the containers', 'Pulls the image, starts containers, runs the probes'),
   ('Ready pods join the Service\'s EndpointSlice', 'Only now does traffic arrive')],
  'MODULE 4 §4.2',
  {'note': ('THE INSIGHT', 'kubectl apply only records intent. Everything after it is independent controllers '
            'reacting to changes — which is why no single component "does the deploy".')}),

 ('define', 'Namespace',
  'A virtual cluster within a cluster: a scope for object names, RBAC, resource quotas and network policy.',
  [('The standard unit of separation for teams and environments', 'This course creates paytrack-dev and paytrack-prod'),
   ('Four exist from the start', 'default · kube-system · kube-public · kube-node-lease'),
   ('NOT a hard security boundary on its own', 'That needs RBAC + NetworkPolicy + quotas + Pod Security Admission'),
   ('Short names resolve inside the namespace', 'paytrack-api from the same namespace; paytrack-api.paytrack-dev from another')],
  'MODULE 4 §4.2'),

 ('section', '2', 'Workloads', 'Pods, probes, resources and how updates roll',
  ['Objects and how they relate', 'Pods and container patterns', 'The three probes',
   'Requests, limits and QoS', 'Deployments and rolling updates']),

 ('diagram', 'The objects, and how they relate', dg.k8s_objects, 'MODULE 4 §4.3–4.8'),

 ('define', 'Pod',
  'The smallest deployable unit: one or more containers that share a network namespace (the same '
  'IP and port space), share storage volumes, and are always scheduled together onto one node.',
  [('Containers in a pod reach each other on localhost', 'The only place that is true in Kubernetes'),
   ('Pods are EPHEMERAL and disposable', 'A new pod has a new name and a new IP. Never address one directly'),
   ('You rarely create a pod directly', 'A bare pod is not rescheduled, not replaced, and cannot be rolled out'),
   ('A pause container holds the shared namespaces', 'Your containers join it — which is how they share an IP')],
  'MODULE 4 §4.3'),

 ('table', 'Container patterns inside a pod',
  ['Pattern', 'Purpose', 'Example'],
  [['Sidecar', 'Augments the main container for its whole life', 'Log shipper, service-mesh proxy, config reloader'],
   ['Init container', 'Runs to completion BEFORE the app containers start', 'Wait for the database, run a schema migration'],
   ['Ambassador', 'Proxies the app\'s outbound connections', 'A local connection pooler'],
   ['Adapter', 'Normalises the app\'s output for the platform', 'Converting metrics to Prometheus format']],
  'MODULE 4 §4.3', {'widths': [2.2, 4.1, 3.9],
   'note': ('THE NORM', 'One main container per pod. Add a second only when the two must share a network '
            'namespace and a lifecycle.')}),

 ('predict', 'A node dies at 03:00. What happens?',
  'You have three replicas spread across two worker nodes behind a Service. One node loses power '
  'entirely. Walk through what happens, second by second, with no human involved.',
  ['What happens to the pods that were ON that node?',
   'What happens to traffic that was being routed to them?',
   'How long until the service is fully back to three healthy replicas?',
   'Now answer the same three questions for your CURRENT production environment.'],
  'Kubernetes marks the node NotReady within about a minute; its pods stop being ready, so they drop '
  'out of the EndpointSlice and traffic stops going there while the survivors keep serving. After the '
  'default five-minute eviction toleration the pods are recreated elsewhere. In Lab 09 you stop a node and watch it.', 4),

 ('diagram', 'The three probes — and the mistake that takes down a platform', dg.probes,
  'MODULE 4 §4.3',
  {'speaker': 'The restart-storm scenario is worth acting out. Ask the room what happens to 40 pods '
   'when the database blips for 30 seconds and the liveness probe checks it. Wait for someone to '
   'realise the health check caused the outage.'}),

 ('code', 'The three probes, as PayTrack declares them',
  '''containers:
  - name: paytrack-api
    image: ghcr.io/<your-username>/paytrack-api:9f3e2a1
    ports: [{ containerPort: 8080 }]
    startupProbe:
      httpGet: { path: /health, port: 8080 }
      failureThreshold: 30
      periodSeconds: 2
    livenessProbe:
      httpGet: { path: /health, port: 8080 }
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet: { path: /ready, port: 8080 }
      periodSeconds: 5
      failureThreshold: 2''',
  [('startupProbe holds the others off', 'Up to 30 × 2 s = 60 s to boot, without weakening liveness'),
   ('liveness → /health', 'Never touches the database. Failing it RESTARTS the container'),
   ('readiness → /ready', 'Checks the database. Failing it removes the pod from traffic — no restart'),
   ('The rule', 'Liveness must not depend on anything external. Readiness should')],
  {'lang': 'k8s/base/deployment.yaml', 'kicker': 'MODULE 4 §4.3 · LAB 10', 'split': 0.56}),

 ('compare', 'Liveness or readiness — which probe checks the database?',
  'PayTrack has two health endpoints. /health answers "is the process alive?" and /ready answers '
  '"can I serve traffic?". One of them may check the database. Which one, and what happens if you '
  'get it the wrong way round?',
  ['Two minutes in pairs. Decide which probe gets the database check.',
   'Then work out what happens to 40 pods when the database blips for 30 seconds.'],
  'READINESS checks the database — failing removes the pod from the Service without restarting '
  'it. If LIVENESS checks it, a 30-second database blip fails every probe, Kubernetes restarts '
  'all 40 pods at once, and the reconnection stampede keeps the database down. Your health check '
  'caused the outage.', 3),

 ('demo', 'Watch a probe take a pod out of traffic',
  '''$ kubectl scale statefulset postgres --replicas=0
statefulset.apps/postgres scaled
$ kubectl get pods -l app.kubernetes.io/name=paytrack-api
NAME                           READY  STATUS   RESTARTS
paytrack-api-7d9c5b6f4b-2kq8x  0/1    Running  0
paytrack-api-7d9c5b6f4b-v7mzn  0/1    Running  0
$ kubectl get endpointslices \\
    -l kubernetes.io/service-name=paytrack-api \\
    -o jsonpath='{.items[*].endpoints[*].conditions.ready}'
false false
$ kubectl scale statefulset postgres --replicas=1
# a minute later: READY 1/1 — and RESTARTS is still 0''',
  [('READY drops to 0/1, but STATUS stays Running', 'The process is healthy; it just cannot serve'),
   ('RESTARTS stays at 0', 'Liveness never touched the database, so nothing restarts'),
   ('The EndpointSlice marks both not ready', 'The Service stops sending them traffic'),
   ('Bring the database back — the pods rejoin by themselves', 'A database blip, not an outage')],
  {'minutes': 6, 'speaker': 'Pod names are illustrative. This is exactly the behaviour PayTrack was built to '
   'show: /health stays 200 while /ready returns 503. Lab 19 game-day failure 5 revisits it under pressure.'}),

 ('table', 'Requests and limits — and why they are a security control',
  ['Setting', 'What it does', 'If you get it wrong'],
  [['requests.cpu', 'What the SCHEDULER reserves when placing the pod', 'Too low: noisy neighbours. Too high: wasted capacity'],
   ['limits.cpu', 'A ceiling — the container is THROTTLED above it', 'Mysterious latency with no errors'],
   ['requests.memory', 'Reserved for scheduling', 'The pod may land on a node that cannot really host it'],
   ['limits.memory', 'A hard ceiling — the container is OOM-KILLED', 'CrashLoopBackOff, exit code 137'],
   ['No requests at all', 'QoS class BestEffort', 'Evicted FIRST under pressure — and the HPA cannot scale it']],
  'MODULE 4 §4.3', {'widths': [2.4, 3.8, 3.8], 'emph': [4],
   'note': ('THE SECURITY ANGLE', 'Limits bound the blast radius of a compromised or leaking container. '
            'A LimitRange supplies defaults so nothing is BestEffort by accident.')}),

 ('table', 'Quality of Service classes — who gets evicted first',
  ['QoS class', 'How you get it', 'Under memory pressure'],
  [['Guaranteed', 'Every container sets requests EQUAL to limits for CPU and memory', '✔ Evicted last'],
   ['Burstable', 'At least one request set, lower than its limit', 'Evicted after BestEffort'],
   ['BestEffort', 'No requests or limits anywhere', '✗ Evicted first — never ship this to production']],
  'MODULE 4 §4.3', {'widths': [2.2, 5.0, 3.0],
   'note': ('FOR A PAYMENTS SERVICE', 'Guaranteed for the ledger and anything that must survive pressure; '
            'Burstable is a sensible default for stateless APIs; BestEffort only for work you can lose.')}),

 ('define', 'ReplicaSet and Deployment',
  'A ReplicaSet keeps a set number of pods matching a label selector running. A Deployment manages '
  'ReplicaSets to give declarative, versioned, rollable updates.',
  [('A Deployment does not update pods', 'It creates a NEW ReplicaSet and shifts replicas from the old one to the new'),
   ('The old ReplicaSet is kept at 0 replicas', 'That is the rollback history — revisionHistoryLimit controls how much'),
   ('Rollback is fast for exactly that reason', 'kubectl rollout undo just scales the old ReplicaSet back up'),
   ('Change the pod template → a new ReplicaSet', 'Change replicas only → the same ReplicaSet scales')],
  'MODULE 4 §4.4'),

 ('flow', 'A rolling update, step by step',
  [('replicas: 3 · maxSurge: 1 · maxUnavailable: 0', 'Three v1 pods, all ready and serving'),
   ('Surge: one v2 pod starts', 'Four pods exist; the controller waits for v2 to become READY'),
   ('One v1 pod is terminated', 'SIGTERM, then the grace period — day 3\'s PID 1 lesson matters here'),
   ('Repeat: another v2 starts, another v1 stops', 'Never fewer than three ready pods at any moment'),
   ('Done: three v2 pods', 'The v1 ReplicaSet remains, scaled to 0, for rollback')],
  'MODULE 4 §4.4',
  {'note': ('WHAT BUYS ZERO DOWNTIME', 'maxUnavailable: 0 plus an accurate readiness probe. Without readiness, '
            'a pod counts as ready the moment its process starts — and the rollout drops requests. '
            'type: Recreate stops everything first: only when two versions cannot coexist.')}),

 ('table', 'Rollout commands',
  ['Command', 'What it does'],
  [['kubectl rollout status deploy/paytrack-api', 'Blocks until the rollout finishes; exits non-zero if it fails — use it in pipelines'],
   ['kubectl rollout history deploy/paytrack-api', 'Lists the revisions still held as ReplicaSets'],
   ['kubectl rollout undo deploy/paytrack-api', 'Back to the previous ReplicaSet'],
   ['kubectl rollout undo deploy/paytrack-api --to-revision=3', 'Back to a specific revision'],
   ['kubectl rollout restart deploy/paytrack-api', 'Re-rolls with no spec change — picks up changed Secrets and ConfigMaps'],
   ['kubectl rollout pause | resume deploy/paytrack-api', 'Batch several changes into one rollout']],
  'MODULE 4 §4.4', {'widths': [4.6, 5.4]}),

 ('table', 'The other workload controllers',
  ['Controller', 'Use for', 'Key property'],
  [['Deployment', 'Stateless services', 'Interchangeable pods with random names'],
   ['StatefulSet', 'Databases, queues — anything with identity', 'Stable names (postgres-0), stable storage, ordered rollout'],
   ['DaemonSet', 'One pod on every node', 'Log agents, CNI, node exporters'],
   ['Job', 'Run to completion once', 'Migrations, batch work'],
   ['CronJob', 'Scheduled Jobs', 'Backups, reports']],
  'MODULE 4 §4.4', {'widths': [2.2, 3.8, 4.2]}),

 ('lab', '09 + 10', 'Build a Cluster · Deploy PayTrack API',
  'A genuine three-node Kubernetes cluster on your laptop, then break it on purpose.',
  ['Create a 3-node k3d cluster (1 server, 2 agents) from a versioned config file',
   'Create namespaces with Pod Security Admission labels, a ResourceQuota and a LimitRange',
   'Deploy PayTrack with all three probes, a security context, limits and topology spread',
   'Delete a pod — watch it return in seconds',
   'STOP A NODE — watch the service keep serving from the survivors',
   'Deploy a BROKEN image — and watch maxUnavailable: 0 refuse to take the service down'],
  'PayTrack running on Kubernetes, having survived pod deletion, node failure and a bad deployment',
  {'kicker': 'STARTED TOGETHER IN CLASS  ·  FINISH AFTER'}),

 ('section', '3', 'Services & Ingress', 'A stable address in front of mortal pods',
  ['Services and EndpointSlices', 'Service types', 'Cluster DNS and ports', 'Ingress and its controller']),

 ('define', 'Service',
  'A stable virtual IP and DNS name that load-balances to a changing set of pods, selected by labels.',
  [('Pods are mortal; their IPs change constantly', 'The Service is the stable abstraction in front of them'),
   ('It selects POD LABELS — it has no relationship to the Deployment', 'Which is exactly how blue-green works on day 5'),
   ('Only READY pods are in its EndpointSlice', 'The readiness probe is what gates traffic'),
   ('kube-proxy makes the virtual IP work', 'iptables or IPVS rules on every node rewrite it to a pod IP')],
  'MODULE 4 §4.5'),

 ('diagram', 'How a request finds a ready pod', dg.service_endpoints, 'MODULE 4 §4.5'),

 ('table', 'Service types',
  ['Type', 'What it gives you', 'Reachable from', 'Use'],
  [['ClusterIP (default)', 'An internal virtual IP', 'Inside the cluster', '✔ Service-to-service — usually correct'],
   ['NodePort', 'The same high port (30000–32767) on every node', '<nodeIP>:<port>', 'Dev, bare metal, behind your own LB'],
   ['LoadBalancer', 'An external load balancer from the provider', 'The network or internet', 'The cloud production entry point'],
   ['ExternalName', 'A DNS CNAME to an outside name', '—', 'A managed database outside the cluster'],
   ['Headless (clusterIP: None)', 'No virtual IP; DNS returns every pod IP', 'Inside the cluster', 'StatefulSets, client-side balancing']],
  'MODULE 4 §4.5', {'widths': [2.6, 3.2, 2.1, 2.4]}),

 ('code', 'Cluster DNS, and port vs targetPort',
  '''# DNS: <service>.<namespace>.svc.cluster.local
paytrack-api.paytrack-dev.svc.cluster.local

# same namespace         http://paytrack-api:80
# another namespace      http://paytrack-api.paytrack-dev:80

apiVersion: v1
kind: Service
metadata: { name: paytrack-api }
spec:
  selector: { app.kubernetes.io/name: paytrack-api }
  ports:
    - port: 80            # what the SERVICE listens on
      targetPort: 8080    # the port on the POD''',
  [('Short names work inside a namespace', 'CoreDNS adds search domains to every pod\'s resolv.conf'),
   ('The direct successor to Compose DNS', 'Day 3\'s @db:5432 idea works unchanged'),
   ('port is the Service, targetPort is the pod', 'nodePort is a third number, only for NodePort and LoadBalancer'),
   ('The selector matches pod labels', 'One typo and the EndpointSlice is empty')],
  {'lang': 'dns · service.yaml', 'kicker': 'MODULE 4 §4.5', 'split': 0.56}),

 ('define', 'Ingress and the Ingress controller',
  'An Ingress is an API object holding HTTP/HTTPS routing rules — host and path — into Services. An Ingress '
  'CONTROLLER is the pod that watches those objects and actually routes the traffic.',
  [('An Ingress without a controller does nothing', 'The most common day-one confusion'),
   ('k3d ships Traefik as the controller', 'A real pod, listening on ports 80 and 443'),
   ('It routes on the HTTP Host header', 'Which is why the lab hostnames go into /etc/hosts'),
   ('It is deliberately limited', 'Weighted splits, header routing and mTLS need annotations, the Gateway API or a mesh')],
  'MODULE 4 §4.8'),

 ('code', 'An Ingress for PayTrack',
  '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: paytrack
spec:
  ingressClassName: traefik          # WHICH controller
  rules:
    - host: paytrack.localhost       # matched on the Host header
      http:
        paths:
          - path: /
            pathType: Prefix         # Prefix | Exact
            backend:
              service:
                name: paytrack-api
                port: { number: 80 }''',
  [('ingressClassName picks the controller', 'Several controllers can coexist in one cluster'),
   ('host is matched against the Host header', 'curl with the wrong Host gets a 404 from Traefik'),
   ('The backend is a SERVICE, never a pod', 'Readiness still decides which pods receive traffic'),
   ('Nothing works? Check the controller first', 'kubectl get pods -n kube-system — is Traefik running?')],
  {'lang': 'k8s/base/ingress.yaml', 'kicker': 'MODULE 4 §4.8 · LAB 12', 'split': 0.54}),

 ('bullets', 'Services, Ingress and the bug that wastes an afternoon',
  [('"My service returns nothing" → kubectl get endpointslices',
    'Empty means no ready pods, or a label/selector mismatch. Check this FIRST'),
   ('A pod Running at 0/1 READY serves nothing', 'That is the readiness probe doing its job'),
   ('An Ingress object alone does nothing', 'It is a set of rules; a controller pod implements them'),
   ('A 404 from the controller usually means the Host did not match', 'Check the host rule and /etc/hosts'),
   ('A 502 or 503 usually means the backend has no ready pods', 'Back to the EndpointSlice')],
  'MODULE 4 §4.5 · §4.8'),

 ('section', '4', 'Configuration, Secrets & Storage', 'Getting config, credentials and data to your pods',
  ['ConfigMaps and Secrets', 'Environment variables vs mounted files', 'How secure Secrets really are',
   'PersistentVolumes, claims and StorageClasses']),

 ('two', 'ConfigMap vs Secret — and the honest truth about Secrets',
  ('CONFIGMAP', ['Non-confidential configuration',
                 'Env vars via envFrom, or mounted as files',
                 'Shown in kubectl describe',
                 'Mounted FILES update ~1 min after a change',
                 'Env vars do NOT — they are fixed at container start'], 'teal'),
  ('SECRET', ['✗ base64-encoded, NOT encrypted by default',
              '✗ Anyone with get-secrets RBAC can read it',
              '✔ Hidden from describe; mounted as tmpfs (RAM)',
              '✔ Distributed only to nodes that need it',
              '→ Needs encryption at rest + RBAC to mean anything'], 'orange'),
  'MODULE 4 §4.6',
  ('YOU WILL DECODE ONE IN THE LAB', 'kubectl get secret -o jsonpath=… | base64 -d prints the password '
   'in plain text. Production answers: Sealed Secrets, SOPS, External Secrets Operator or Vault — '
   'you will use Sealed Secrets on day 6.')),

 ('table', 'Environment variables or mounted files?',
  ['Method', 'Manifest', 'Live updates?'],
  [['Environment variables', 'envFrom: [{ configMapRef: { name: paytrack-config } }]',
    '✗ No — fixed at container start; the pod must restart'],
   ['Mounted volume', 'volumes: [{ configMap: { name: paytrack-config } }]',
    '✔ Yes — the kubelet refreshes the files within about a minute, if the app re-reads them']],
  'MODULE 4 §4.6', {'widths': [2.2, 4.6, 3.4],
   'note': ('THE IDIOM', 'Put a checksum of the ConfigMap in a pod-template annotation, so changing config changes '
            'the template and triggers a rollout — or simply run kubectl rollout restart. Lab 11 proves both behaviours.')}),

 ('bullets', 'How secure are Kubernetes Secrets, honestly?',
  [('Stored in etcd base64-encoded — NOT encrypted — unless encryption at rest is enabled', 'A common audit finding'),
   ('Anyone with get secrets in the namespace can read them',
    'kubectl get secret x -o jsonpath=\'{.data.password}\' | base64 -d'),
   ('Anyone who can create a pod in the namespace can mount them', 'Pod-creation rights are secret-read rights'),
   ('Anyone with etcd access reads all of them', None),
   ('What they DO give you', 'Hidden from describe, tmpfs mounts, delivered only to nodes that need them, separable by RBAC')],
  'MODULE 4 §4.6',
  {'note': ('PRODUCTION PRACTICE', 'Encryption at rest + least-privilege RBAC + secrets kept out of git with '
            'Sealed Secrets, SOPS, External Secrets Operator or Vault. Lab 17 uses Sealed Secrets.')}),

 ('table', 'Persistent storage — three objects',
  ['Object', 'What it is', 'Who writes it'],
  [['PersistentVolumeClaim (PVC)', 'A namespaced REQUEST: "I need 5Gi, ReadWriteOnce"', '✔ The application developer'],
   ['StorageClass', 'A named provisioner that creates volumes on demand', 'The platform team'],
   ['PersistentVolume (PV)', 'The actual piece of storage: local path, NFS, Ceph, a cloud disk', 'The provisioner, automatically']],
  'MODULE 4 §4.7', {'widths': [3.0, 4.6, 2.6],
   'note': ('ACCESS AND RECLAIM', 'RWO = one node at a time (almost all block storage) · RWX needs a shared '
            'filesystem. reclaimPolicy Delete — the default for dynamic volumes — destroys the data with the claim; '
            'Retain keeps it for recovery.')}),

 ('bullets', 'Databases on Kubernetes',
  [('StatefulSet, not Deployment', 'Stable ordinal names — postgres-0 — and one PVC per replica'),
   ('volumeClaimTemplates', 'Each replica gets its own claim, reattached wherever the pod is rescheduled'),
   ('ReadWriteOnce constrains updates', 'The volume must detach from one node before it attaches to another'),
   ('Deleting a StatefulSet does NOT delete its PVCs', 'Deliberate — one command cannot destroy a database'),
   ('Lab 11 proves it', 'Delete postgres-0, watch it return with the same name and the same rows')],
  'MODULE 4 §4.7'),

 ('section', '5', 'Scaling & Debugging', 'More pods when needed — and finding out why one is broken',
  ['The HorizontalPodAutoscaler', 'HPA, VPA and the Cluster Autoscaler', 'PodDisruptionBudgets',
   'Debugging, in order']),

 ('define', 'HorizontalPodAutoscaler',
  'A controller that adjusts the replica count of a workload to keep an observed metric near a '
  'target — most commonly average CPU utilisation as a percentage OF THE POD\'S REQUEST.',
  [('averageUtilization: 50 with requests.cpu: 50m means a target of 25m per pod', None),
   ('A pod with no CPU request CANNOT be autoscaled on CPU', 'No request, no percentage, no scaling'),
   ('It needs metrics-server', 'Without it the HPA reports <unknown> and does nothing'),
   ('Tune behaviour asymmetrically', 'Scale up immediately; scale down after a stabilisation window'),
   ('Requests per second is often a better signal than CPU', 'Via the Prometheus Adapter')],
  'MODULE 4 §4.9'),

 ('table', 'Choosing the metric — where most HPAs go wrong',
  ['Signal', 'Usable?', 'Why'],
  [['Requests per second, queue depth', 'BEST', 'Proportional to demand in BOTH directions; needs the Prometheus Adapter'],
   ['CPU utilisation', 'Good', 'Tracks work done, and it drops the moment the work stops. The sensible default'],
   ['Memory utilisation', 'ALMOST NEVER', 'Rises with load but does NOT fall afterwards - the JVM, Python and Go hold freed memory rather than returning it to the OS']],
  'MODULE 4 §4.9 · LAB 12', {'widths': [3.0, 1.7, 5.5], 'emph': [3],
   'speaker': 'This is the slide that saves someone a production incident. A metric is only usable if it '
              'falls when demand falls - people always check the first half and never the second. Lab 12 '
              'ships CPU-only for exactly this reason: the PayTrack pod idles at about 103% of its 64Mi '
              'memory request, so a memory metric at 80% pins it at maxReplicas with ZERO traffic, and it '
              'never comes back down. Worse, the HPA takes the HIGHEST recommendation across its metrics, '
              'so adding memory "for safety" silently overrides CPU. Then it eats the namespace quota and '
              'the NEXT deployment is what fails - which is how this usually gets discovered.'}),

 ('flow', 'Memory as a scaling metric — the failure, step by step',
  [('The pod is honest', 'Requests 64Mi; genuinely idles at 66Mi of interpreter, modules and caches'),
   ('The HPA does its arithmetic', 'target 80%, actual 103% -> ceil(3 x 103 / 80) = 4 replicas, at IDLE'),
   ('Every new pod reports the same 103%', 'So the recommendation never comes down - 5, 7, 9, 10'),
   ('The highest metric wins', 'CPU says 18%/50% and is simply ignored'),
   ('The bill arrives elsewhere', '10 x limits.cpu 300m = 3000m of a 4000m namespace quota; the NEXT deploy fails'),
   ('The rule', 'Memory belongs in requests and limits. Alert on it; do not autoscale on it')],
  'MODULE 4 §4.9'),

 ('code', 'An HPA, and the formula it runs',
  '''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: paytrack-api }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: paytrack-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 60 }
  behavior:
    scaleDown: { stabilizationWindowSeconds: 300 }

# desired = ceil( current × currentMetric ÷ target )''',
  [('The formula', '3 pods at 90 % against a 60 % target → ceil(3 × 90 ÷ 60) = 5 pods'),
   ('minReplicas of at least 2', 'Anything that must stay available never scales to one'),
   ('The scale-down window', 'Five minutes of calm before removing pods — no flapping'),
   ('It writes Deployment.replicas', 'Remove replicas: from the Deployment YAML, or GitOps and the HPA will fight')],
  {'lang': 'k8s/base/hpa.yaml', 'kicker': 'MODULE 4 §4.9 · LAB 12', 'split': 0.58}),

 ('table', 'Three scalers, and the budget that protects you',
  ['Object', 'Adjusts', 'Note'],
  [['HorizontalPodAutoscaler', 'The number of pods', 'The default answer for stateless services'],
   ['VerticalPodAutoscaler', 'The requests and limits of pods', 'Restarts pods to apply; do not combine with HPA on the same CPU metric'],
   ['Cluster Autoscaler', 'The number of nodes', 'Reacts to pods stuck Pending for lack of capacity'],
   ['PodDisruptionBudget', 'Nothing — it limits VOLUNTARY disruption', 'Without one, a node drain or cluster upgrade can take the whole service down, legitimately']],
  'MODULE 4 §4.9', {'widths': [2.8, 3.0, 4.4], 'emph': [3]}),

 ('table', 'Debugging — what the status is telling you',
  ['Symptom', 'Usual cause'],
  [['Pending', 'No node has enough resources; an unsatisfiable selector or affinity; an unbound PVC'],
   ['ImagePullBackOff', 'Wrong image name or tag; a private registry with no imagePullSecret'],
   ['CrashLoopBackOff', 'The app exits at start — read logs --previous; usually bad config or a missing variable'],
   ['ContainerCreating (stuck)', 'A volume cannot mount; a Secret or ConfigMap is missing; a CNI problem'],
   ['OOMKilled · exit code 137', 'limits.memory too low, or a memory leak'],
   ['Running but no traffic', 'Readiness failing, or a label/selector mismatch — check the EndpointSlice'],
   ['no matches for kind', 'The CRD is not installed, or the apiVersion is wrong']],
  'MODULE 4 §4.10', {'widths': [2.9, 7.1]}),

 ('code', 'Debugging — the order to work in',
  '''$ kubectl get pods                      # 1 what state is it in?
$ kubectl describe pod <pod>            # 2 read EVENTS at the bottom
$ kubectl logs <pod>                    # 3 the application's logs
$ kubectl logs <pod> --previous         # 3b the crashed instance
$ kubectl get events --sort-by=.lastTimestamp
$ kubectl exec -it <pod> -- sh          # 4 get inside
$ kubectl get endpointslices            # 5 is the Service selecting pods?''',
  [('describe first, and read the Events', 'It explains most failures in plain English'),
   ('logs --previous for CrashLoopBackOff', 'The current container has only just started — the evidence is in the last one'),
   ('Events expire', 'Look soon, or they are gone after about an hour'),
   ('The EndpointSlice answers "why no traffic?"', 'Almost every "the service is down" that is not a crash')],
  {'lang': 'bash', 'kicker': 'MODULE 4 §4.10', 'split': 0.58}),

 ('lab', '11 + 12', 'Config, Secrets, Storage · Ingress and Autoscaling',
  'Externalise everything, give the ledger durable storage, then watch Kubernetes scale under load.',
  ['ConfigMap for settings; Secret for credentials — then DECODE the secret and discuss',
   'PostgreSQL as a StatefulSet with a PVC; delete the pod and watch the data survive',
   'Assemble DATABASE_URL at runtime from four separate sources with $(VAR) interpolation',
   'Prove env vars are frozen at start but mounted files refresh — then rollout restart',
   'Expose PayTrack through the Traefik Ingress on a real hostname',
   'Create an HPA, generate load, and watch it scale out and back in'],
  'A fully externalised, durable, reachable, autoscaling workload'),

 ('bank', 'Kubernetes controls that map to banking requirements',
  [('Namespaces + ResourceQuota + LimitRange', 'Blast-radius and noisy-neighbour containment'),
   ('NetworkPolicy — default-deny, then explicit allows',
    'Pod-to-pod traffic is UNRESTRICTED by default. This is your segmentation control'),
   ('Pod Security Admission', 'Rejects privileged workloads at admission — baseline enforced, restricted warned in the labs'),
   ('RBAC as code; no standing production access', 'Access-control evidence, versioned in git'),
   ('Encryption at rest for etcd', 'Otherwise Secrets are just base64 on a disk')],
  {'lead': 'Kubernetes gives you the controls; it does not apply them for you. Every default is '
           'permissive, and a cluster with no NetworkPolicy is a flat network.',
   'ref': 'Appendix A §A.9 · Labs 09–11'}),

 ('myth', 'Three things people believe about Kubernetes',
  [('Kubernetes Secrets are encrypted.',
    'They are base64-encoded. Anyone with get-secrets RBAC reads them. You need encryption at rest, RBAC and a real secret store.'),
   ('If a pod is Running, it is serving traffic.',
    'Only READY pods are in the EndpointSlice. Running at 0/1 READY serves nothing — the readiness probe working.'),
   ('NetworkPolicy protects my cluster by default.',
    'Traffic is unrestricted until you write a policy, and something must enforce it. k3s has a built-in policy controller; plain Flannel alone does not.')],
  'MYTH vs REALITY'),

 ('table', 'Day 4 key terms',
  ['Term', 'Definition'],
  [['Desired state / reconciliation', 'Declared intent, and the loops that make reality match it'],
   ['API server / etcd / scheduler / kubelet', 'The front door / the store / pod placement / the node agent'],
   ['Pod', 'The smallest deployable unit; containers sharing a network namespace'],
   ['ReplicaSet / Deployment', 'Keeps N pods running / manages ReplicaSets for rollable updates'],
   ['Liveness / readiness / startup probe', 'Restart if wedged / remove from traffic / hold off until booted'],
   ['QoS class', 'Guaranteed, Burstable or BestEffort — decides eviction order'],
   ['Service / EndpointSlice', 'A stable IP and name / the list of ready pod IPs behind it'],
   ['Ingress / Ingress controller', 'HTTP routing rules / the pod that implements them'],
   ['ConfigMap / Secret', 'Non-confidential / confidential configuration (base64, not encrypted)'],
   ['PVC / StorageClass / PV', 'The request / the provisioner / the storage'],
   ['HPA / PodDisruptionBudget', 'Scales pods on a metric / limits voluntary disruption']],
  'REFERENCE', {'widths': [3.6, 6.4]}),

 ('check', 'Day 4 — check your understanding',
  ['You delete a pod created by a Deployment and it reappears. Explain the exact chain of events.',
   'Your liveness probe checks the database. The database blips for 30 seconds. What happens to '
   'your 40 pods, and why is that worse than the original problem?',
   'Your Service returns nothing but all pods show Running. Give the first command you run and '
   'the two most likely causes.',
   'maxSurge: 1, maxUnavailable: 0, replicas: 3 — walk through the rollout and say what guarantees zero downtime.',
   'An HPA shows <unknown> for CPU. Give two possible causes.',
   'A colleague says "Secrets are encrypted, so storing the DB password there is fine." Correct them and name a production fix.']),

 ('close', 4, 'Day 4 complete',
  ['Declarative desired state, and the reconciliation loop behind every behaviour',
   'The control plane and nodes — and what really happens on kubectl apply',
   'Probes, requests, limits and QoS; Deployments, rolling updates and rollback',
   'Services, DNS and Ingress; ConfigMaps, Secrets and persistent storage; autoscaling and debugging',
   'AFTER CLASS: finish Labs 09–12 — cluster, deployment, config and storage, ingress and HPA'],
  'Day 5 stops doing any of this by hand. Terraform provisions the environments, Ansible configures '
  'the machines, and a GitOps pipeline takes a commit all the way to the cluster with no human '
  'running kubectl. Then blue-green, canary and rollback — and the database changes that make or break them.'),
]
