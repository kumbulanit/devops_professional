# -*- coding: utf-8 -*-
"""Day 4 — Kubernetes for DevOps.  Module 4."""
import diagrams as dg

DAY4 = [
 ('title', 4, 'Kubernetes',
  'Declare what you want; let the platform close the gap',
  ['Architecture · the reconciliation loop · Pods, ReplicaSets, Deployments',
   'Services, Ingress · ConfigMaps, Secrets · persistent storage',
   'Probes, resource limits, autoscaling and disruption budgets',
   'Labs 09–12 — Build a cluster · Deploy · Config & storage · Ingress & HPA'],
  'Today you will kill a node in front of the room and watch nothing break'),

 ('bullets', 'Why Compose could not take you further',
  [('Compose runs containers on ONE machine', 'No scheduling across hosts, no failover'),
   ('If that machine dies, everything dies', None),
   ('Scaling is manual and bounded by one host', None),
   ('No self-healing', 'A crashed container restarts; a crashed HOST does not'),
   ('No rolling update with health-gated traffic', None),
   ('Kubernetes adds one idea: DECLARE the desired state, and let controllers maintain it',
    'That single idea is what the whole day is about')],
  'FROM DAY 3 TO DAY 4'),

 ('section', '1', 'Architecture', 'The control plane, the nodes, and the loop that runs everything',
  ['Control plane components', 'Node components', 'The reconciliation loop', 'Objects and controllers']),

 ('diagram', 'Kubernetes architecture', dg.k8s_architecture, 'MODULE 4 §4.1'),

 ('define', 'The reconciliation loop',
  'A controller continuously observes the actual state of the cluster, compares it with the '
  'declared desired state, and takes action to close the gap — forever, without being asked.',
  [('You never issue commands — you declare intent', 'kubectl apply records what you want; controllers do the work'),
   ('kubectl apply returns IMMEDIATELY', 'It has recorded intent, not completed a deployment'),
   ('Which is why kubectl rollout status exists', 'That is the command that waits and can fail'),
   ('Delete a pod and it comes back', 'Not magic — a ReplicaSet controller observing 2 where 3 was declared'),
   ('This is also why manual kubectl edits are silently reverted under GitOps', None)],
  'MODULE 4 §4.1'),

 ('diagram', 'The objects, and how they relate', dg.k8s_objects, 'MODULE 4 §4.2–4.7'),

 ('define', 'Pod',
  'The smallest deployable unit: one or more containers that share a network namespace (the same '
  'IP and port space), share storage volumes, and are always scheduled together onto one node.',
  [('Containers in a pod reach each other on localhost', 'The only place that is true in Kubernetes'),
   ('Pods are EPHEMERAL and disposable', 'A new pod has a new name and a new IP. Never address one directly'),
   ('You rarely create a pod directly', 'You declare a Deployment and let it manage pods'),
   ('One main container per pod is the norm', 'Sidecars exist for proxies, log shippers and init work')],
  'MODULE 4 §4.3'),


 ('predict', 'A node dies at 03:00. What happens?',
  'You have three replicas spread across two worker nodes behind a Service. One node loses power '
  'entirely. Walk through what happens, second by second, with no human involved.',
  ['What happens to the pods that were ON that node?',
   'What happens to traffic that was being routed to them?',
   'How long until the service is fully back to three healthy replicas?',
   'Now answer the same three questions for your CURRENT production environment.'],
  'Kubernetes marks the node NotReady within ~40 s; readiness drops those pods out of the '
  'EndpointSlice almost immediately so traffic stops going there; the survivors keep serving '
  'throughout. You will do exactly this in Lab 09 — stop a node and watch nothing break.', 4),
 ('diagram', 'The three probes — and the mistake that takes down a platform', dg.probes,
  'MODULE 4 §4.4',
  {'speaker': 'The restart-storm scenario is worth acting out. Ask the room what happens to 40 pods '
   'when the database blips for 30 seconds and the liveness probe checks it. Wait for someone to '
   'realise the health check caused the outage.'}),


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
 ('table', 'Requests and limits — and why they are a security control',
  ['Setting', 'What it does', 'If you get it wrong'],
  [['requests.cpu', 'What the SCHEDULER reserves when placing the pod', 'Too low: noisy neighbours. Too high: wasted capacity'],
   ['limits.cpu', 'Ceiling — the container is THROTTLED above it', 'Mysterious latency with no errors'],
   ['requests.memory', 'Reserved for scheduling', 'Pod may land on a node that cannot really host it'],
   ['limits.memory', 'Hard ceiling — the container is OOM-KILLED', 'CrashLoopBackOff, exit code 137'],
   ['No requests at all', 'QoS class BestEffort', 'Evicted FIRST under pressure. And the HPA cannot scale it']],
  'MODULE 4 §4.4', {'widths': [2.4, 3.8, 3.6], 'emph': [4],
   'note': ('THE SECURITY ANGLE', 'Limits bound the blast radius of a compromised or leaking container: '
            'they stop one workload starving its neighbours. A LimitRange supplies defaults so nothing '
            'is BestEffort by accident.')}),

 ('lab', '09 + 10', 'Build a Cluster · Deploy PayTrack API',
  'A genuine three-node Kubernetes cluster on your laptop, then break it on purpose.',
  ['Create a 3-node k3d cluster (1 server, 2 agents) from a versioned config file',
   'Create namespaces with Pod Security Admission, a ResourceQuota and a LimitRange',
   'Deploy PayTrack with all three probes, security context, limits and topology spread',
   'Delete a pod — watch it return in seconds',
   'STOP A NODE — watch the service keep serving from the survivors',
   'Deploy a BROKEN image — and watch maxUnavailable:0 refuse to take the service down'],
  'PayTrack running on Kubernetes, survived pod deletion, node failure and a bad deployment'),

 ('section', '2', 'Configuration, Storage & Traffic', 'Getting data and users to your pods',
  ['ConfigMaps and Secrets', 'Persistent volumes', 'Services and Ingress', 'Autoscaling']),

 ('two', 'ConfigMap vs Secret — and the honest truth about Secrets',
  ('CONFIGMAP', ['Non-confidential configuration',
                 'Env vars via envFrom, or mounted as files',
                 'Shown in kubectl describe',
                 'Mounted FILES update ~1 min after a change',
                 'Env vars do NOT — they are fixed at container start'], 'teal'),
  ('SECRET', ['✗ base64-encoded, NOT encrypted by default',
              '✗ Anyone with get secrets RBAC can read it',
              '✔ Hidden from describe; mounted as tmpfs (RAM)',
              '✔ Distributed only to nodes that need it',
              '→ Needs encryption-at-rest + RBAC to mean anything'], 'orange'),
  'MODULE 4 §4.6',
  ('YOU WILL DECODE ONE IN THE LAB', 'kubectl get secret -o jsonpath=… | base64 -d prints the password '
   'in plain text. Production answers: Sealed Secrets, SOPS, External Secrets Operator or Vault — '
   'you will use Sealed Secrets on day 6.')),

 ('bullets', 'Persistent storage',
  [('PersistentVolumeClaim (PVC)', 'A REQUEST for storage — size, access mode, class'),
   ('PersistentVolume (PV)', 'The actual storage that satisfies it'),
   ('StorageClass', 'Provisions PVs dynamically — nobody pre-creates storage any more'),
   ('ReadWriteOnce is the common case', 'One node at a time — which is why it constrains rolling updates'),
   ('StatefulSet, not Deployment, for databases',
    'Stable ordinal names, one PVC per replica, reattached on reschedule'),
   ('Deleting a StatefulSet does NOT delete its PVCs',
    'Deliberate — you cannot destroy a database with one command. Check the reclaimPolicy')],
  'MODULE 4 §4.7'),

 ('bullets', 'Services, Ingress and the bug that wastes an afternoon',
  [('Service = a stable virtual IP and DNS name in front of a changing set of pods', None),
   ('Its selector matches POD LABELS — it has no relationship to the Deployment',
    'Which is exactly how blue-green works: one selector edit moves all traffic'),
   ('Only READY pods appear in the EndpointSlice', 'The readiness probe is what gates traffic'),
   ('"My service returns nothing" → kubectl get endpointslices',
    'Empty means no ready pods, or a label/selector mismatch. Check this FIRST'),
   ('An Ingress object alone does nothing',
    'It is a set of rules; an Ingress CONTROLLER pod implements them'),
   ('Ingress routes on the HTTP Host header', 'Which is why /etc/hosts matters in the lab')],
  'MODULE 4 §4.5 · §4.8'),

 ('define', 'HorizontalPodAutoscaler',
  'A controller that adjusts the replica count of a workload to keep an observed metric near a '
  'target — most commonly average CPU utilisation as a percentage OF THE POD\'S REQUEST.',
  [('averageUtilization: 50 with requests.cpu: 50m means a target of 25m per pod', None),
   ('A pod with no CPU request CANNOT be autoscaled on CPU', 'This is why requests are mandatory'),
   ('It needs metrics-server', 'No metrics-server, no HPA — it reports <unknown>'),
   ('Tune behaviour asymmetrically',
    'Scale UP immediately (users are waiting); scale DOWN after a stabilisation window (avoid thrashing)'),
   ('Requests per second is often a better signal than CPU', 'Via the Prometheus Adapter')],
  'MODULE 4 §4.9'),

 ('lab', '11 + 12', 'Config, Secrets, Storage · Ingress and Autoscaling',
  'Externalise everything, give the ledger durable storage, then watch Kubernetes scale under load.',
  ['ConfigMap for settings; Secret for credentials — then DECODE the secret and discuss',
   'PostgreSQL as a StatefulSet with a PVC; delete the pod and watch the data survive',
   'Assemble DATABASE_URL at runtime from four separate sources with $(VAR) interpolation',
   'Prove env vars are frozen at start but mounted files refresh — then rollout restart',
   'Expose PayTrack through Traefik Ingress on a real hostname',
   'Create an HPA, generate load, and WATCH IT SCALE 3 → 6 → back down'],
  'A fully externalised, durable, internet-reachable, autoscaling workload'),

 ('bank', 'Kubernetes controls that map to banking requirements',
  [('Namespaces + ResourceQuota + LimitRange', 'Blast-radius and noisy-neighbour containment'),
   ('NetworkPolicy — default-deny, then explicit allows',
    'Pod-to-pod traffic is UNRESTRICTED by default. This is your segmentation control'),
   ('Pod Security Admission (restricted profile)', 'Rejects privileged workloads at admission'),
   ('RBAC as code; no standing production access', 'Access-control evidence, versioned in git'),
   ('Encryption at rest for etcd', 'Otherwise Secrets are just base64 on a disk')],
  {'lead': 'Kubernetes gives you the controls; it does not apply them for you. Every default is '
           'permissive, and a cluster with no NetworkPolicy is a flat network.',
   'ref': 'Appendix A §A.9 · Labs 11–12'}),


 ('myth', 'Three things people believe about Kubernetes',
  [('Kubernetes Secrets are encrypted.',
    'They are base64-encoded. Anyone with get-secrets RBAC reads them. You need encryption at rest, RBAC and a real secret store.'),
   ('If a pod is Running, it is serving traffic.',
    'Only READY pods are in the EndpointSlice. Running with 0/1 READY serves nothing — and that is the readiness probe working.'),
   ('NetworkPolicy protects my cluster by default.',
    'Pod-to-pod traffic is completely unrestricted until you write one — AND your CNI must enforce it. k3s\'s default Flannel does not.')]),
 ('check', 'Day 4 — check your understanding',
  ['Your liveness probe checks the database. The database blips for 30 seconds. What happens to '
   'your 40 pods, and why is that worse than the original problem?',
   'Your Service returns nothing but all pods show Running. Give the first command you run and '
   'the two most likely causes.',
   'Explain why a pod with no CPU request cannot be autoscaled on CPU utilisation.',
   'Deleting a StatefulSet leaves the PVCs behind. Why is that the right default?',
   'A bad image was deployed and the service stayed up. Which single setting made that true?']),

 ('close', 4, 'Day 4 complete',
  ['A real three-node cluster, built from a versioned config file',
   'PayTrack deployed with correct probes, limits, security context and a disruption budget',
   'Survived pod deletion, node failure and a deliberately broken image',
   'Config and secrets externalised; the ledger on storage that outlives its pod',
   'Ingress routing on a hostname, and an HPA you watched scale under real load'],
  'Day 5 stops doing any of this by hand. Terraform provisions the environments, Ansible configures '
  'the machines, and a GitOps pipeline takes a commit all the way to the cluster with no human '
  'running kubectl. Then blue-green and canary, with the traffic split visible in a browser.'),
]
