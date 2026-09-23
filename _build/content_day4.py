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


# ═════════════════════════════════════════════════════════════════════════════
# DAY 4 — GOING FURTHER (optional reading, not taught in the session)
#
# Three sections, each with a hands-on lab that lives inside the lab folder it
# extends:  A → Lab 10A,  B → Lab 11A,  C → Lab 12A.
# ═════════════════════════════════════════════════════════════════════════════

DAY4_EXTRA = [
  ('title', 4,
   'Day 4 — Going Further',
   'Optional reading, for after class — once Deployments, Services and probes feel comfortable',
   ['A: debugging and rollouts — why is this pod not running, and how do I go back?',
    'B: access, configuration and storage in depth — RBAC, NetworkPolicy, Secrets, volumes',
    'C: scaling, scheduling and disruption — HPA behaviour, where pods land, draining a node'],
   'Not taught in the session — read it, then practise it in Labs 10A, 11A and 12A'),

  # ── A ──────────────────────────────────────────────────────────────────────
  ('section', 'A', 'Debugging and Rollouts',
   'The four commands that answer nine out of ten Kubernetes questions',
   ['get · describe · logs · events — in that order',
    'What each pod state actually means',
    'Ephemeral containers: a shell for an image that has none',
    'rollout history, undo, pause — and what a rolling update really does']),

  ('code', 'The four commands, in order',
   'kubectl get pods -o wide                 # where is it, how many restarts\n'
   'kubectl describe pod <name>              # WHY - read the Events at the bottom\n'
   'kubectl logs <name> --previous           # what the CRASHED container said\n'
   'kubectl get events --sort-by=.lastTimestamp | tail -20',
   [('get tells you WHAT', 'Status, restarts, age, node — the shape of the problem'),
    ('describe tells you WHY', 'Scheduling decisions, image pulls, probe failures, mount errors'),
    ('--previous is the one people miss', 'The current container is fine; the one that died holds the evidence'),
    ('events are namespaced and expire', 'Roughly an hour by default — capture them before they are gone')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.58}),

  ('table', 'Pod states, and what each one means',
   ['You see', 'It means', 'Look at'],
   [['Pending', 'No node can take it yet', 'describe → Events: insufficient cpu/memory, or an unbound PVC'],
    ['ContainerCreating', 'Pulling the image, or mounting volumes', 'describe → Events; a stuck mount is usually a missing Secret'],
    ['ImagePullBackOff', 'The registry said no', 'The image name, the tag, and whether the pull secret exists'],
    ['CrashLoopBackOff', 'It starts, then exits, repeatedly', 'logs --previous. The restart delay grows to 5 minutes'],
    ['OOMKilled (exit 137)', 'It exceeded its memory limit', 'The limit, and whether the app leaks'],
    ['Error (exit 1)', 'The process itself failed', 'logs — this is an application problem, not a cluster one'],
    ['Evicted', 'The node ran out of something', 'describe node → conditions: DiskPressure, MemoryPressure'],
    ['Running but not Ready', 'The readiness probe fails', 'It is out of the Service. describe → probe output']],
   'MODULE 4 §4.8',
   {'note': ('READY 0/1 IS NOT A CRASH',
             'A pod can be Running and still receive no traffic, because readiness removed it from the '
             'EndpointSlice. That is the state people misread most often.'),
    'widths': [2.9, 3.4, 4.0]}),

  ('code', 'A shell for an image that has none',
   '# the production image is distroless - no sh, no curl, nothing\n'
   'kubectl debug -it paytrack-api-abc123 \\\n'
   '  --image=nicolaka/netshoot --target=api -- bash\n'
   '\n'
   '# a copy of the pod, with a shell, that does NOT take traffic\n'
   'kubectl debug paytrack-api-abc123 --copy-to=debug-pod \\\n'
   '  --image=nicolaka/netshoot --share-processes -- sleep infinity\n'
   '\n'
   'kubectl delete pod debug-pod',
   [('An ephemeral container joins the running pod', 'Same network and, with --target, the same process namespace'),
    ('Nothing is added to your image', 'The debug tooling lives and dies with the session'),
    ('--copy-to leaves production alone', 'The copy is not in the Service, so you can poke it safely'),
    ('Delete the copy when you are done', 'It is a pod like any other and will sit there for ever')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.60}),

  ('code', 'Going back is one command — if you kept the history',
   'kubectl rollout history deployment/paytrack-api\n'
   'kubectl rollout history deployment/paytrack-api --revision=3\n'
   '\n'
   'kubectl rollout undo deployment/paytrack-api              # to the previous revision\n'
   'kubectl rollout undo deployment/paytrack-api --to-revision=2\n'
   '\n'
   'kubectl rollout pause deployment/paytrack-api   # stop mid-rollout\n'
   'kubectl rollout resume deployment/paytrack-api',
   [('A revision is a ReplicaSet', 'Kubernetes keeps old ones so "undo" is a scale-up, not a rebuild'),
    ('revisionHistoryLimit decides how far back', 'Default 10. Set it to 0 and undo has nothing to go to'),
    ('pause is the manual canary', 'Change the image, let some pods roll, watch, then resume or undo'),
    ('undo is faster than a pipeline', 'Minutes of CI versus seconds of scheduler — know both')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.60}),

  ('table', 'The three probes, and the failure each one causes',
   ['Probe', 'When it fails', 'The failure mode you will meet'],
   [['liveness', 'The container is RESTARTED', 'Probe hits a slow dependency → every replica restarts at once → outage'],
    ['readiness', 'The pod leaves the Service', 'A database blip takes all pods out of the EndpointSlice → 503 with pods "Running"'],
    ['startup', 'The container is restarted', 'Missing on a slow starter → liveness kills it before it ever finishes booting'],
    ['(none)', 'Nothing', 'Traffic is sent to a process that is still loading — the default until you add them']],
   'MODULE 4 §4.4',
   {'note': ('THE RULE',
             'Liveness must test the PROCESS, never its dependencies. Readiness may test dependencies. '
             'If your liveness probe queries the database, one slow query restarts the whole deployment.'),
    'widths': [2.2, 3.4, 4.7]}),

  ('predict', 'The database gets slow. What does Kubernetes do?',
   'Your liveness probe calls /health, which runs SELECT 1 against PostgreSQL. The database has a '
   'thirty-second stall.',
   ['Write down what happens to one pod.',
    'Then write down what happens to all six replicas at the same moment.',
    'Does the deployment recover on its own when the database does?'],
   'Every liveness probe times out together, so every container is killed together — a full outage '
   'caused by a slow query, not a failed one. They restart, hit the same stall, and enter '
   'CrashLoopBackOff with a growing back-off. Readiness would have removed them from the Service '
   'and let them return quietly. You build both probes and break them in Lab 10A.',
   3),

  ('lab', '10A',
   'Debugging and Rollouts — the 3 a.m. commands',
   'Break the deployment six ways on purpose, diagnose each from the cluster\'s own output, and '
   'roll back a bad release in one command.',
   ['Produce Pending, ImagePullBackOff, CrashLoopBackOff, OOMKilled and Running-but-not-Ready',
    'Read each one with get, describe, logs --previous and events',
    'Get a shell into the distroless image with kubectl debug',
    'Turn a liveness probe into a restart storm, then fix it with readiness',
    'Roll out a bad image, watch maxSurge and maxUnavailable, and undo it',
    'Pause a rollout half-way and decide from real output whether to resume'],
   'The six failures you will actually meet, and the command that explains each one',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-10-k8s-deploy-app/README-10A-debugging-and-rollouts.md. Optional; '
               'about 70 minutes; needs the Lab 09 cluster and the Lab 10 deployment. The restart-storm '
               'demo is the one to show from the front.'}),

  # ── B ──────────────────────────────────────────────────────────────────────
  ('section', 'B', 'Access, Configuration and Storage in Depth',
   'Who can do what, what a Secret really protects, and where the data actually lives',
   ['ServiceAccounts, Roles and RoleBindings — and auth can-i',
    'What a Secret is, and what it is not',
    'NetworkPolicy: default deny, then allow what you meant',
    'Storage classes, access modes, reclaim policies and resize']),

  ('code', 'RBAC in four objects, and one command to test it',
   'kubectl create serviceaccount deploy-bot\n'
   'kubectl create role pod-reader \\\n'
   '  --verb=get,list,watch --resource=pods,pods/log\n'
   'kubectl create rolebinding deploy-bot-can-read \\\n'
   '  --role=pod-reader --serviceaccount=paytrack-dev:deploy-bot\n'
   '\n'
   'kubectl auth can-i list pods \\\n'
   '  --as=system:serviceaccount:paytrack-dev:deploy-bot    # yes\n'
   'kubectl auth can-i delete deployments \\\n'
   '  --as=system:serviceaccount:paytrack-dev:deploy-bot    # no',
   [('Role is namespaced, ClusterRole is not', 'Start namespaced; reach for cluster scope only when you must'),
    ('A binding is the grant', 'Roles grant nothing on their own — the binding ties subject to role'),
    ('auth can-i --as is the audit tool', 'Ask the API server what an identity may do, before an auditor does'),
    ('Every pod has a ServiceAccount', 'The default one is mounted into your pod unless you say otherwise')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash', 'split': 0.62}),

  ('table', 'What a Secret is — and is not',
   ['Belief', 'Reality', 'What to do about it'],
   [['"It is encrypted"', 'base64 only, unless the cluster enables encryption at rest', 'Turn on EncryptionConfiguration, or use an external store'],
    ['"Only my app can read it"', 'Anyone with get secret in the namespace can read it', 'RBAC is the actual control'],
    ['"It is safe in git"', 'A Secret manifest is plaintext in your repository', 'Sealed Secrets (Lab 17) or External Secrets'],
    ['"Rotating it is easy"', 'An env-var Secret needs a pod restart to be re-read', 'Mount as a file, or trigger a rollout deliberately'],
    ['"It never leaves the cluster"', 'It reaches etcd, backups, and any log that echoes it', 'Treat etcd backups as secret material']],
   'MODULE 4 §4.6 · MODULE 7',
   {'note': ('THE HONEST SUMMARY',
             'A Kubernetes Secret keeps a credential out of the image and out of the manifest that '
             'defines the workload. Everything beyond that is RBAC, encryption at rest, and what you '
             'do with backups.'),
    'widths': [2.7, 3.7, 3.9]}),

  ('code', 'Default deny, then allow what you meant',
   'apiVersion: networking.k8s.io/v1\n'
   'kind: NetworkPolicy\n'
   'metadata: { name: default-deny-ingress }\n'
   'spec:\n'
   '  podSelector: {}            # every pod in this namespace\n'
   '  policyTypes: [Ingress]     # with no ingress rules = deny all inbound\n'
   '---\n'
   'spec:                        # ... then one that allows the API to reach Postgres\n'
   '  podSelector: { matchLabels: { app: postgres } }\n'
   '  ingress:\n'
   '    - from: [{ podSelector: { matchLabels: { app.kubernetes.io/name: paytrack-api } } }]\n'
   '      ports: [{ port: 5432 }]',
   [('Policies are additive and allow-only', 'There is no "deny" rule — you deny by not allowing'),
    ('An empty podSelector means every pod', 'That is how a default-deny is written'),
    ('It needs a CNI that enforces it', 'k3s (Flannel) does; some managed clusters need it enabled'),
    ('Test it from a pod, not from your laptop', 'Policy applies to pod-to-pod traffic inside the cluster')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'networkpolicy.yaml', 'split': 0.62}),

  ('code', 'Config changes that actually reach the process',
   '# 1. env vars from a ConfigMap are read ONCE, at start:\n'
   'kubectl rollout restart deployment/paytrack-api\n'
   '\n'
   '# 2. the automatic version - a checksum annotation in the pod template:\n'
   'spec:\n'
   '  template:\n'
   '    metadata:\n'
   '      annotations:\n'
   '        checksum/config: "{{ sha256sum of the ConfigMap }}"\n'
   '\n'
   '# 3. or make it impossible to edit in place:\n'
   'kubectl create configmap paytrack-config --from-file=... --dry-run=client -o yaml\n'
   '# ... with  immutable: true',
   [('A mounted ConfigMap updates in the file', 'Eventually — kubelet syncs it, and only if you did not use subPath'),
    ('subPath mounts never update', 'The most common "my config change did nothing" cause'),
    ('env: values never update', 'The process read them at exec time; only a restart re-reads them'),
    ('A checksum annotation forces a rollout', 'Change the config, the pod template changes, Kubernetes rolls')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  yaml', 'split': 0.60}),

  ('table', 'Storage: the four decisions',
   ['Decision', 'Field', 'Getting it wrong looks like'],
   [['Which storage', 'storageClassName', 'PVC stuck Pending — no default class, or a name that does not exist'],
    ['How many writers', 'accessModes', 'ReadWriteOnce on a multi-replica Deployment → pods stuck ContainerCreating'],
    ['What happens on delete', 'persistentVolumeReclaimPolicy', 'Delete: the data goes with the PVC. Retain: orphaned volumes and a bill'],
    ['Per-replica or shared', 'volumeClaimTemplates vs a PVC', 'A StatefulSet needs its own volume per pod; a Deployment cannot have one']],
   'MODULE 4 §4.7',
   {'note': ('THE ONE THAT BITES',
             'ReadWriteOnce means one NODE, not one pod. Two replicas on the same node can share it; '
             'the moment the scheduler puts one elsewhere, that pod never starts.'),
    'widths': [2.6, 2.9, 4.8]}),

  ('lab', '11A',
   'Access, Config and Storage in Depth',
   'Grant an identity exactly what it needs and prove it, deny traffic by default and allow only '
   'what you meant, then make a config change actually reach the process.',
   ['Create a ServiceAccount, Role and RoleBinding, then test with auth can-i --as',
    'Read a Secret as any namespace member can, and decide what that means',
    'Apply a default-deny NetworkPolicy and watch the API lose the database',
    'Allow exactly one path, and prove nothing else got in',
    'Change a ConfigMap and see why nothing happened — then fix it two ways',
    'Resize a PVC, and see what accessModes and reclaim policy really do'],
   'Least privilege you can demonstrate, a namespace that denies by default, and config you can roll',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-11-k8s-config-secrets-storage/README-11A-access-and-storage.md. '
               'Optional; about 70 minutes; needs the Lab 11 objects. The NetworkPolicy part is the one '
               'that surprises people — k3s does enforce it.'}),

  # ── C ──────────────────────────────────────────────────────────────────────
  ('section', 'C', 'Scaling, Scheduling and Disruption',
   'Where pods land, when they multiply, and what happens when a node goes away',
   ['HPA behaviour: stabilisation windows and policies',
    'What actually decides which node a pod lands on',
    'Taints, tolerations, affinity and topology spread',
    'PodDisruptionBudgets and kubectl drain']),

  ('code', 'An HPA that does not flap',
   'apiVersion: autoscaling/v2\n'
   'spec:\n'
   '  minReplicas: 2\n'
   '  maxReplicas: 10\n'
   '  metrics:\n'
   '    - type: Resource\n'
   '      resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }\n'
   '  behavior:\n'
   '    scaleUp:\n'
   '      stabilizationWindowSeconds: 0     # react to load immediately\n'
   '      policies: [{ type: Percent, value: 100, periodSeconds: 30 }]\n'
   '    scaleDown:\n'
   '      stabilizationWindowSeconds: 300   # wait 5 min of calm before shrinking\n'
   '      policies: [{ type: Pods, value: 1, periodSeconds: 60 }]',
   [('Utilization is a percentage of REQUESTS', 'No requests set = no CPU target = the HPA cannot work'),
    ('Scale up fast, scale down slowly', 'The asymmetry is deliberate: a wrong scale-down costs an outage'),
    ('The default scaleDown window is 5 minutes', 'Change it only when you can explain the flapping you accept'),
    ('The HPA takes the HIGHEST recommendation', 'Add a memory metric and it will usually win — see the Day 4 deck')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'hpa.yaml', 'split': 0.64}),

  ('table', 'What decides which node a pod lands on',
   ['Mechanism', 'Says', 'Typical use'],
   [['resources.requests', '"I need this much room"', 'The primary input — the scheduler packs by requests, not usage'],
    ['nodeSelector', '"Only nodes with this label"', 'Simple hardware or zone pinning'],
    ['nodeAffinity', '"Prefer / require these labels"', 'Soft preferences the scheduler may ignore under pressure'],
    ['podAntiAffinity', '"Not next to my own kind"', 'Spreading replicas across nodes for availability'],
    ['topologySpreadConstraints', '"Even across zones, within a skew"', 'The modern replacement for most anti-affinity rules'],
    ['taints + tolerations', '"Keep off unless you tolerate this"', 'Reserving nodes — GPUs, licensed software, control plane'],
    ['priorityClass', '"Evict someone else if you must"', 'Making sure the critical workload is the one that survives']],
   'MODULE 4 §4.9',
   {'note': ('REQUESTS ARE THE CONTRACT',
             'Every other mechanism is a filter on top. A pod with no requests can be scheduled '
             'anywhere, is the first to be evicted, and is invisible to the autoscaler.'),
    'widths': [3.3, 3.2, 3.8]}),

  ('code', 'Reserve a node, and spread the replicas',
   '# reserve: nothing lands here unless it tolerates the taint\n'
   'kubectl taint nodes k3d-paytrack-agent-1 workload=payments:NoSchedule\n'
   '\n'
   'spec:                      # ... and in the pod template:\n'
   '  tolerations:\n'
   '    - { key: workload, operator: Equal, value: payments, effect: NoSchedule }\n'
   '  topologySpreadConstraints:\n'
   '    - maxSkew: 1\n'
   '      topologyKey: kubernetes.io/hostname\n'
   '      whenUnsatisfiable: ScheduleAnyway   # DoNotSchedule is the strict version\n'
   '      labelSelector: { matchLabels: { app.kubernetes.io/name: paytrack-api } }',
   [('A taint repels; a toleration permits', 'The toleration does not attract — pair it with affinity if you must pin'),
    ('NoSchedule, PreferNoSchedule, NoExecute', 'Only NoExecute evicts pods that are already running'),
    ('maxSkew 1 means "within one"', 'Across nodes, zones, or any label you choose as the topology key'),
    ('ScheduleAnyway degrades, DoNotSchedule blocks', 'Choose which failure you prefer at 3 a.m.')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'bash  ·  yaml', 'split': 0.62}),

  ('code', 'Draining a node — and the budget that protects you',
   'apiVersion: policy/v1\n'
   'kind: PodDisruptionBudget\n'
   'spec:\n'
   '  minAvailable: 1                 # or maxUnavailable: 1\n'
   '  selector: { matchLabels: { app.kubernetes.io/name: paytrack-api } }\n'
   '\n'
   'kubectl drain k3d-paytrack-agent-0 --ignore-daemonsets --delete-emptydir-data\n'
   '# evicting pod paytrack-dev/paytrack-api-...\n'
   '# error when evicting pod ... (will retry): Cannot evict pod as it would violate the PDB',
   [('A PDB constrains VOLUNTARY disruption', 'Drains and node upgrades — not a crash, and not a node that dies'),
    ('The drain waits rather than breaking it', 'That message is the budget working, not an error to force past'),
    ('minAvailable: 1 with replicas: 1 deadlocks', 'Nothing can ever be evicted — the classic self-inflicted stall'),
    ('uncordon when you are done', 'A cordoned node stays unschedulable until you say otherwise')],
   {'kicker': 'GOING FURTHER · OPTIONAL', 'lang': 'yaml  ·  bash', 'split': 0.62}),

  ('myth', 'Four things teams say about scaling Kubernetes',
   [('"The HPA will handle the traffic."',
     'Only if requests are set, metrics-server is running, and your pods start faster than the load arrives.'),
    ('"More replicas means more capacity."',
     'Not if they all land on one node, or all wait on the same database connection pool.'),
    ('"A PodDisruptionBudget keeps us available."',
     'It constrains voluntary evictions only. A node that dies takes its pods with it, budget or not.'),
    ('"We set limits, so we are safe."',
     'Limits without requests give the worst QoS class: first to be throttled, first to be evicted.')],
   'MODULE 4 §4.9'),

  ('lab', '12A',
   'Scaling, Scheduling and Disruption',
   'Tune an HPA so it stops flapping, decide where pods land, and drain a node while the service '
   'stays up — then create the deadlock a bad budget causes.',
   ['Add behaviour to the HPA and watch scale-up and scale-down differ',
    'Read why a pod is Pending straight from the scheduler\'s own events',
    'Taint a node, tolerate it, and see the pods move',
    'Spread replicas with topologySpreadConstraints and prove the skew',
    'Drain a node with a PodDisruptionBudget in place and watch it protect you',
    'Set minAvailable equal to replicas, deadlock the drain, and fix it'],
   'A workload that scales sensibly, lands where you meant, and survives a node being taken away',
   {'kicker': 'GOING FURTHER  ·  HANDS-ON',
    'speaker': 'Lab guide: labs/lab-12-k8s-ingress-scaling/README-12A-scaling-and-scheduling.md. '
               'Optional; about 70 minutes; needs the Lab 09 three-node cluster and the Lab 12 HPA. '
               'The drain deadlock is the memorable one.'}),
]


# Per-lab ADVANCED decks: slices of DAY4_EXTRA, each shipped in the lab folder it belongs to.
_D4_A = DAY4_EXTRA[1:9]       # section A + Lab 10A
_D4_B = DAY4_EXTRA[9:16]      # section B + Lab 11A
_D4_C = DAY4_EXTRA[16:]       # section C + Lab 12A

LAB10A_ADVANCED = [
  ('title', 4, 'Lab 10A — Debugging and Rollouts',
   'The advanced debugging slides, for after class — the commands you reach for at 3 a.m.',
   ['get · describe · logs --previous · events, in that order',
    'What each pod state means, and which command explains it',
    'Ephemeral containers · rollout history, undo and pause',
    'Optional. Nothing on Day 5 onwards depends on it'],
   'Practise it: labs/lab-10-k8s-deploy-app/README-10A-debugging-and-rollouts.md'),
] + _D4_A

LAB11A_ADVANCED = [
  ('title', 4, 'Lab 11A — Access, Config and Storage in Depth',
   'The advanced access and storage slides, for after class — RBAC, Secrets, NetworkPolicy, volumes',
   ['ServiceAccounts, Roles, RoleBindings and auth can-i',
    'What a Secret protects, and what it does not',
    'Default-deny networking · config changes that actually apply · storage decisions',
    'Optional. Nothing on Day 5 onwards depends on it'],
   'Practise it: labs/lab-11-k8s-config-secrets-storage/README-11A-access-and-storage.md'),
] + _D4_B

LAB12A_ADVANCED = [
  ('title', 4, 'Lab 12A — Scaling, Scheduling and Disruption',
   'The advanced scaling slides, for after class — HPA behaviour, where pods land, draining a node',
   ['HPA stabilisation windows and policies',
    'Requests, taints, affinity and topology spread',
    'PodDisruptionBudgets and kubectl drain',
    'Optional. Nothing on Day 5 onwards depends on it'],
   'Practise it: labs/lab-12-k8s-ingress-scaling/README-12A-scaling-and-scheduling.md'),
] + _D4_C
