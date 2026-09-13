# Lab 18 — Monitoring, Dashboards, Alerts and an Incident

| | |
|---|---|
| **Day** | 6 |
| **Duration** | 40 minutes |
| **Module** | 8 — Monitoring and Observability |
| **You will produce** | Prometheus + Grafana + Alertmanager on the cluster, a RED dashboard, SLO burn-rate alerts, and a worked incident |
| **Feeds into** | Lab 19 (capstone) |

---

## Objective

Instrument the running service, build a dashboard from the RED method, define an SLO with an
error budget, write burn-rate alerts, then **break production and run the incident** using the
telemetry you just built.

## Prerequisites

- Labs 09–15. **At least 3 GB RAM free** — the monitoring stack is the heaviest thing you run
  all week.
  ```bash
  docker compose -f ~/devops-course/paytrack-api-team/compose.yaml down 2>/dev/null
  docker rm -f web1 web2 db1 jenkins 2>/dev/null
  free -h
  ```

🔁 **RECOVER**
```bash
cd ~/devops-course/paytrack-api-team && k3d cluster start paytrack 2>/dev/null
kubectl config set-context --current --namespace=paytrack-dev && kubectl apply -f k8s/base/
```

---

## Step 1 — Confirm the app is already instrumented

```bash
cd ~/devops-course/paytrack-api-team
kubectl port-forward service/paytrack-api 8888:80 >/dev/null 2>&1 &
sleep 3
curl -s localhost:8888/metrics | grep -E '^# (HELP|TYPE) paytrack' | head -12
```
**What this does:** PayTrack API has exposed Prometheus metrics since day 1. Each metric carries
`# HELP` (what it means) and `# TYPE` (counter, gauge or histogram) — **this self-description
is why Prometheus needs no per-application configuration.**

| Metric | Type | Answers |
|---|---|---|
| `paytrack_http_requests_total` | counter | **Rate** and **Errors** (labelled by status) |
| `paytrack_http_request_duration_seconds` | histogram | **Duration** — true aggregate quantiles |
| `paytrack_authorisations_total` | counter | **Business volume**, by `status` and `currency` |
| `paytrack_declined_amount_minor_total` | counter | **Value declined** — a business KPI, not a technical one |
| `paytrack_authorisations_stored` | gauge | Ledger row count |
| `paytrack_build_info` | gauge | Which version/colour/entity is running |

> 🏦 **The last two matter more to a bank than the first two.** Every technical metric can be
> green while the business is broken: the pods are healthy, latency is fine, no 5xx — and the
> decline rate has quietly gone from 4 % to 40 % because an upstream scheme link is failing
> closed. **A payments team that only watches RED metrics will not see that.** You will add a
> decline-rate alert in Step 6 for exactly this reason.

```bash
curl -s localhost:8888/metrics | grep 'paytrack_http_requests_total{' | head -3
```
**Look at the shape:** `paytrack_http_requests_total{method="GET",endpoint="health",status="200"} 47`.
Each **unique label combination** is a separate time series.

> 🔴 **Cardinality.** `endpoint="/api/v1/authorisations"` is correct. `path="/api/v1/authorisations/8213"` would
> create a new series per record and eventually kill the Prometheus. This application uses the
> Flask *endpoint name*, not the raw URL, deliberately.

```bash
kill %1 2>/dev/null
```

---

## Step 2 — Install the monitoring stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null
helm repo update >/dev/null
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

mkdir -p k8s/monitoring
cat > k8s/monitoring/values.yaml <<'EOF'
# kube-prometheus-stack, sized for a laptop.
prometheus:
  prometheusSpec:
    retention: 6h
    resources:
      requests: { cpu: 100m, memory: 400Mi }
      limits:   { cpu: 600m, memory: 1Gi }
    # Discover ServiceMonitors in EVERY namespace, not only where Helm installed it.
    serviceMonitorSelectorNilUsesHelmValues: false
    ruleSelectorNilUsesHelmValues: false
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources: { requests: { storage: 2Gi } }

grafana:
  adminPassword: paytrack-admin
  resources:
    requests: { cpu: 50m, memory: 128Mi }
    limits:   { cpu: 300m, memory: 384Mi }
  ingress:
    enabled: true
    ingressClassName: traefik
    hosts: [grafana.localhost]
  defaultDashboardsTimezone: browser

alertmanager:
  alertmanagerSpec:
    resources:
      requests: { cpu: 20m, memory: 64Mi }
      limits:   { cpu: 150m, memory: 192Mi }

# Trim components a laptop does not need.
kubeEtcd:                  { enabled: false }
kubeControllerManager:     { enabled: false }
kubeScheduler:             { enabled: false }
kubeProxy:                 { enabled: false }
prometheus-node-exporter:  { enabled: true }
kubeStateMetrics:          { enabled: true }
EOF

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values k8s/monitoring/values.yaml \
  --wait --timeout 10m
```
**What this does:** installs the **kube-prometheus-stack** — Prometheus, Alertmanager,
Grafana, node-exporter, kube-state-metrics, the Prometheus Operator and a set of default
dashboards and alert rules — in one command. Doing this by hand is roughly forty manifests.

**The critical setting is `serviceMonitorSelectorNilUsesHelmValues: false`.** Left at its
default, Prometheus only discovers ServiceMonitors carrying the Helm release label, and your
`paytrack-dev` monitor is silently ignored. This is the single most common reason "my app does
not appear in Prometheus".

```bash
kubectl get pods -n monitoring
grep -q 'grafana.localhost' /etc/hosts || echo "127.0.0.1  grafana.localhost" | sudo tee -a /etc/hosts
```

---

## Step 3 — Tell Prometheus to scrape PayTrack API

```bash
cat > k8s/monitoring/servicemonitor.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: paytrack-api
  namespace: paytrack-dev
  labels:
    app.kubernetes.io/name: paytrack-api
    release: monitoring          # some chart configurations select on this
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: paytrack-api    # which SERVICE to scrape
  namespaceSelector:
    matchNames: [paytrack-dev]
  endpoints:
    - port: http                 # the NAMED port on the Service
      path: /metrics
      interval: 15s              # scrape frequency
      scrapeTimeout: 10s
EOF
kubectl apply -f k8s/monitoring/servicemonitor.yaml
```
**What this does:** a `ServiceMonitor` is a **custom resource** the Prometheus Operator
watches. Creating it rewrites Prometheus' scrape configuration automatically — you never edit
`prometheus.yml`. **This is monitoring as code**: adding a service to monitoring is a pull
request, not a ticket.

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 >/dev/null 2>&1 &
sleep 5
curl -s 'localhost:9090/api/v1/targets?state=active' | jq -r '.data.activeTargets[] | select(.labels.job=="paytrack-api") | "\(.labels.pod)  health=\(.health)"'
```
**What this does:** queries the Prometheus API for active targets. Expect one line per pod,
`health=up`. If nothing appears, wait 60 seconds — the operator reconciles on a cycle.

Open **http://localhost:9090** → **Status → Targets** for the same view in the UI.

---

## Step 4 — PromQL: the RED method

Generate some traffic first:

```bash
kubectl run traffic --restart=Never --image=busybox:1.36 \
  --overrides='{"spec":{"containers":[{"name":"traffic","image":"busybox:1.36","resources":{"requests":{"cpu":"20m","memory":"32Mi"}},"command":["/bin/sh","-c","while true; do wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/api/v1/authorisations>/dev/null; wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/health>/dev/null; wget -q -O- http://paytrack-api.paytrack-dev.svc.cluster.local/nonexistent>/dev/null 2>&1; sleep 0.4; done"]}]}}'
sleep 60
```
**What this does:** a steady mix of good requests and 404s, so the error-rate queries have
something to show.

In the Prometheus UI (**http://localhost:9090**), run each of these:

**R — Rate (requests per second):**
```promql
sum(rate(paytrack_http_requests_total[5m]))
```
**What this does:** `rate()` computes the per-second average increase of a counter over 5
minutes, correctly handling counter resets when a pod restarts. `sum()` aggregates across all
pods. **Never graph a raw counter — it only ever goes up.**

**By endpoint:**
```promql
sum by (endpoint) (rate(paytrack_http_requests_total[5m]))
```

**E — Errors (as a ratio, which is what an SLO needs):**
```promql
sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(paytrack_http_requests_total[5m]))
```
**What this does:** `=~` is a regex matcher. **Both numerator and denominator must be
aggregated the same way**, or you are dividing incompatible vectors.

**D — Duration (p95, correctly):**
```promql
histogram_quantile(0.95,
  sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))
```
**What this does:** `le` ("less than or equal") is the histogram bucket label. You must
`sum by (le)` **before** `histogram_quantile`, which is what makes this a true aggregate
percentile across all pods.

> 🔴 **Never average percentiles.** `avg(p95_per_pod)` is not the p95. Histograms exist
> precisely so you can aggregate correctly — this is why Module 8 says use histograms, not
> summaries.

**Availability — is the target even up?**
```promql
up{job="paytrack-api"}
```
**What this does:** `1` if the last scrape succeeded, `0` if it failed. Prometheus generates
this for free — **the scrape is itself a health check**, which is the main practical advantage
of pull over push.

### 🏦 The queries a payments team actually watches

**Decline rate** — the single most important number on a card platform:
```promql
sum(rate(paytrack_authorisations_total{status="declined"}[5m]))
  /
clamp_min(sum(rate(paytrack_authorisations_total[5m])), 0.001)
```
**What this does:** the proportion of authorisations being declined. A normal card estate
sits in a stable band (often 3–8 %). **A sudden move in either direction is an incident**:
up means you are refusing good customers, down can mean a fraud control has failed open.

**Authorisation throughput by decision:**
```promql
sum by (status) (rate(paytrack_authorisations_total[5m]))
```

**Value declined per second, by currency** — puts a number on the business impact:
```promql
sum by (currency) (rate(paytrack_declined_amount_minor_total[5m])) / 100
```
**What this does:** divides minor units by 100 to give major units (pounds, euros) per
second. **This is the query that turns "the service is degraded" into "we are turning away
£4 200 a minute"** — which is the sentence that gets an incident the attention it needs.

> 🔑 **Technical metrics tell you the system is unwell. Business metrics tell you it
> matters.** Put at least one of each on every dashboard.

---

## Step 5 — Build a dashboard

Open **http://grafana.localhost:8080** — user `admin`, password `paytrack-admin`.

```bash
mkdir -p k8s/monitoring/dashboards
cat > k8s/monitoring/dashboards/paytrack-red.json <<'EOF'
{
  "title": "PayTrack API \u2014 RED + Business",
  "uid": "paytrack-red",
  "tags": [
    "paytrack",
    "red-method"
  ],
  "timezone": "browser",
  "refresh": "10s",
  "time": {
    "from": "now-30m",
    "to": "now"
  },
  "panels": [
    {
      "type": "stat",
      "title": "Request rate (req/s)",
      "gridPos": {
        "h": 4,
        "w": 6,
        "x": 0,
        "y": 0
      },
      "targets": [
        {
          "expr": "sum(rate(paytrack_http_requests_total[5m]))",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps",
          "decimals": 2
        }
      }
    },
    {
      "type": "stat",
      "title": "Error ratio",
      "gridPos": {
        "h": 4,
        "w": 6,
        "x": 6,
        "y": 0
      },
      "targets": [
        {
          "expr": "sum(rate(paytrack_http_requests_total{status=~\"5..\"}[5m])) / clamp_min(sum(rate(paytrack_http_requests_total[5m])), 0.001)",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "decimals": 3,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 0.005
              },
              {
                "color": "red",
                "value": 0.02
              }
            ]
          }
        }
      }
    },
    {
      "type": "stat",
      "title": "p95 latency",
      "gridPos": {
        "h": 4,
        "w": 6,
        "x": 12,
        "y": 0
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "s",
          "decimals": 3
        }
      }
    },
    {
      "type": "stat",
      "title": "Pods up",
      "gridPos": {
        "h": 4,
        "w": 6,
        "x": 18,
        "y": 0
      },
      "targets": [
        {
          "expr": "sum(up{job=\"paytrack-api\"})",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "red",
                "value": null
              },
              {
                "color": "green",
                "value": 1
              }
            ]
          }
        }
      }
    },
    {
      "type": "timeseries",
      "title": "R \u2014 Request rate by endpoint",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 4
      },
      "targets": [
        {
          "expr": "sum by (endpoint) (rate(paytrack_http_requests_total[5m]))",
          "legendFormat": "{{endpoint}}",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      }
    },
    {
      "type": "timeseries",
      "title": "E \u2014 Requests by status class",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 4
      },
      "targets": [
        {
          "expr": "sum by (status) (rate(paytrack_http_requests_total[5m]))",
          "legendFormat": "{{status}}",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      }
    },
    {
      "type": "timeseries",
      "title": "D \u2014 Latency percentiles",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 12
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.50, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))",
          "legendFormat": "p50",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.95, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))",
          "legendFormat": "p95",
          "refId": "B"
        },
        {
          "expr": "histogram_quantile(0.99, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))",
          "legendFormat": "p99",
          "refId": "C"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "s"
        }
      }
    },
    {
      "type": "timeseries",
      "title": "Error-budget burn rate (1h / 5m)",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 12
      },
      "targets": [
        {
          "expr": "(sum(rate(paytrack_http_requests_total{status=~\"5..\"}[1h])) / clamp_min(sum(rate(paytrack_http_requests_total[1h])), 0.001)) / 0.005",
          "legendFormat": "1h burn",
          "refId": "A"
        },
        {
          "expr": "(sum(rate(paytrack_http_requests_total{status=~\"5..\"}[5m])) / clamp_min(sum(rate(paytrack_http_requests_total[5m])), 0.001)) / 0.005",
          "legendFormat": "5m burn",
          "refId": "B"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short"
        }
      }
    },
    {
      "type": "stat",
      "title": "Decline rate",
      "gridPos": {
        "h": 4,
        "w": 6,
        "x": 0,
        "y": 20
      },
      "targets": [
        {
          "expr": "sum(rate(paytrack_authorisations_total{status=\"declined\"}[5m])) / clamp_min(sum(rate(paytrack_authorisations_total[5m])), 0.001)",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "decimals": 2,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 0.1
              },
              {
                "color": "red",
                "value": 0.15
              }
            ]
          }
        }
      }
    },
    {
      "type": "timeseries",
      "title": "Authorisations by decision (business volume)",
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 6,
        "y": 20
      },
      "targets": [
        {
          "expr": "sum by (status) (rate(paytrack_authorisations_total[5m]))",
          "legendFormat": "{{status}}",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps"
        }
      }
    },
    {
      "type": "timeseries",
      "title": "Value declined per second (major units)",
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 20
      },
      "targets": [
        {
          "expr": "sum by (currency) (rate(paytrack_declined_amount_minor_total[5m])) / 100",
          "legendFormat": "{{currency}}",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "currencyGBP",
          "decimals": 2
        }
      }
    }
  ],
  "schemaVersion": 39,
  "version": 1
}
EOF
echo "Dashboard written. Import it in Grafana: Dashboards → New → Import → Upload JSON"
```
**What this does:** defines the dashboard **as code**. Import it via
**Dashboards → New → Import → Upload JSON file**, selecting the Prometheus data source.

> 🔑 **Dashboards belong in git.** A dashboard clicked together in a UI is a snowflake: it
> cannot be reviewed, versioned, copied to another environment, or restored after an
> accidental deletion. This JSON is reviewable in a pull request like any other code.

**Note `clamp_min(..., 0.001)` in the denominators** — it prevents division by zero when there
is no traffic, which otherwise renders panels as `NaN` and makes people distrust the
dashboard.

---

## Step 6 — Define an SLO and write burn-rate alerts

```bash
cat > k8s/monitoring/alerts.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: paytrack-api-slo
  namespace: paytrack-dev
  labels:
    release: monitoring
spec:
  groups:
    # ── Recording rules: pre-compute the expensive expressions ──────────────
    - name: paytrack-api.recording
      interval: 30s
      rules:
        - record: paytrack:request_rate5m
          expr: sum(rate(paytrack_http_requests_total[5m]))
        - record: paytrack:error_ratio5m
          expr: |
            sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))
              / clamp_min(sum(rate(paytrack_http_requests_total[5m])), 0.001)
        - record: paytrack:latency_p95_5m
          expr: histogram_quantile(0.95, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))

    # ── SLO: 99.5% of requests succeed.  Error budget = 0.5% ────────────────
    - name: paytrack-api.slo
      rules:
        # FAST BURN: 14.4x. Consumes 2% of a 30-day budget in one hour. PAGE.
        - alert: PayTrackAPIErrorBudgetFastBurn
          expr: |
            (
              sum(rate(paytrack_http_requests_total{status=~"5.."}[1h]))
                / clamp_min(sum(rate(paytrack_http_requests_total[1h])), 0.001)
            ) > (14.4 * 0.005)
            and
            (
              sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))
                / clamp_min(sum(rate(paytrack_http_requests_total[5m])), 0.001)
            ) > (14.4 * 0.005)
          for: 2m
          labels: { severity: critical, team: platform }
          annotations:
            summary: "PayTrack API is burning its error budget 14.4x too fast"
            description: "Error ratio is {{ $value | humanizePercentage }} over 1h AND 5m."
            runbook_url: "https://github.com/<your-username>/paytrack-api/blob/main/docs/runbooks/high-error-rate.md"

        # SLOW BURN: 6x. Consumes 5% of the budget in six hours. Ticket, not a page.
        - alert: PayTrackAPIErrorBudgetSlowBurn
          expr: |
            (
              sum(rate(paytrack_http_requests_total{status=~"5.."}[6h]))
                / clamp_min(sum(rate(paytrack_http_requests_total[6h])), 0.001)
            ) > (6 * 0.005)
            and
            (
              sum(rate(paytrack_http_requests_total{status=~"5.."}[30m]))
                / clamp_min(sum(rate(paytrack_http_requests_total[30m])), 0.001)
            ) > (6 * 0.005)
          for: 15m
          labels: { severity: warning, team: platform }
          annotations:
            summary: "PayTrack API error budget burning 6x too fast"
            runbook_url: "https://github.com/<your-username>/paytrack-api/blob/main/docs/runbooks/high-error-rate.md"

    # ── Symptom-based alerts ───────────────────────────────────────────────
    - name: paytrack-api.symptoms
      rules:
        - alert: PayTrackAPIDown
          expr: absent(up{job="paytrack-api"} == 1)     # absent() fires when the series VANISHES
          for: 2m
          labels: { severity: critical }
          annotations:
            summary: "No healthy PayTrack API instance is being scraped"

        - alert: PayTrackAPIHighLatency
          expr: paytrack:latency_p95_5m > 1
          for: 5m
          labels: { severity: warning }
          annotations:
            summary: "p95 latency is {{ $value }}s (threshold 1s)"

        - alert: PayTrackAPIPodRestarting
          expr: |
            increase(kube_pod_container_status_restarts_total{namespace="paytrack-dev",container="paytrack-api"}[15m]) > 2
          for: 5m
          labels: { severity: warning }
          annotations:
            summary: "Pod {{ $labels.pod }} restarted more than twice in 15 minutes"

    # ── BUSINESS alerts. Every technical metric can be green while these are not. ──
    - name: paytrack-api.business
      rules:
        - alert: PayTrackDeclineRateHigh
          expr: |
            (
              sum(rate(paytrack_authorisations_total{status="declined"}[10m]))
                / clamp_min(sum(rate(paytrack_authorisations_total[10m])), 0.001)
            ) > 0.15
          for: 10m
          labels: { severity: critical, team: payments }
          annotations:
            summary: "Decline rate is {{ $value | humanizePercentage }} (normal band 3-8%)"
            description: >-
              Authorisations are being declined far above the normal band. Check the
              upstream scheme link and any fraud rule deployed in the last hour.
              This can be RED-green: pods healthy, latency fine, customers refused.
            runbook_url: "https://github.com/<your-username>/paytrack-api/blob/main/docs/runbooks/decline-rate.md"

        - alert: PayTrackAuthorisationsStopped
          expr: sum(rate(paytrack_authorisations_total[10m])) == 0
          for: 10m
          labels: { severity: critical, team: payments }
          annotations:
            summary: "No authorisations recorded for 10 minutes"
            description: >-
              Zero throughput. Either upstream has stopped calling us, or we are
              failing before the record is written. Outside a maintenance window this
              is a SEV1 - and NO technical alert will fire, because the service is
              perfectly healthy and simply idle.
EOF
kubectl apply -f k8s/monitoring/alerts.yaml
sleep 30
curl -s localhost:9090/api/v1/rules | jq -r '.data.groups[] | select(.name|startswith("paytrack")) | .rules[].name' 2>/dev/null
```
**The design principles on display:**

| Principle | Where |
|---|---|
| **Recording rules** | `paytrack:error_ratio5m` is computed every 30 s so dashboards and alerts read a cheap pre-aggregated series |
| **Multi-window, multi-burn-rate** | Long window = "this is real", short window = "it is still happening", so the alert **resolves** when the problem does |
| **Severity tiers** | 14.4× pages a human; 6× creates a ticket. Different urgency, different response |
| **`runbook_url` on every alert** | 03:00 is not the time to reason from first principles |
| **Symptoms, not causes** | Error ratio and latency (users hurting) rather than CPU (may be fine) |
| **`absent()`** | Fires when the metric **disappears** — a threshold alert cannot detect "gone" |
| **`for:`** | Requires the condition to persist, which suppresses flapping |

---

## Step 7 — Cause an incident and work it

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093 >/dev/null 2>&1 &
sleep 3
echo "Alertmanager: http://localhost:9093"
```

**Inject the failure — a memory limit far too small:**
```bash
kubectl set resources deployment/paytrack-api -n paytrack-dev --limits=memory=24Mi
kubectl rollout status deployment/paytrack-api -n paytrack-dev --timeout=90s 2>&1 | tail -2
```
**What this does:** 24Mi cannot hold the Python interpreter plus Flask. The kernel OOM-kills
each container as it starts.

**Now work the incident with the telemetry, in order:**

**1. DETECT**
```bash
kubectl get pods -n paytrack-dev
curl -s 'localhost:9090/api/v1/query?query=up{job="paytrack-api"}' | jq -r '.data.result[] | "\(.metric.pod) up=\(.value[1])"'
```
Look at your Grafana dashboard: **Pods up** falls, error ratio climbs.

**2. TRIAGE — how bad, and for whom?**
```bash
curl -s 'localhost:9090/api/v1/query?query=paytrack:error_ratio5m' | jq -r '.data.result[0].value[1]'
curl -s 'localhost:9090/api/v1/query?query=paytrack:request_rate5m' | jq -r '.data.result[0].value[1]'
```
Users affected × duration = impact. That decides the severity, before anyone starts debugging.

**3. DIAGNOSE**
```bash
kubectl describe pod -l app.kubernetes.io/name=paytrack-api -n paytrack-dev | grep -A6 'Last State\|Events' | head -25
kubectl get events -n paytrack-dev --sort-by=.lastTimestamp | tail -8
```
**Look for `Reason: OOMKilled` and `Exit Code: 137`** (128 + 9 = SIGKILL). Kubernetes tells you
exactly what happened, in plain English, in the Events section.

**4. MITIGATE — restore service first, understand later**
```bash
time kubectl rollout undo deployment/paytrack-api -n paytrack-dev
kubectl rollout status deployment/paytrack-api -n paytrack-dev --timeout=90s
kubectl get pods -n paytrack-dev
```
**Rollback before root cause.** The incident is the priority; the investigation is not urgent.

**5. VERIFY**
```bash
sleep 45
curl -s 'localhost:9090/api/v1/query?query=paytrack:error_ratio5m' | jq -r '.data.result[0].value[1]'
curl -s http://paytrack.localhost:8080/health | jq -r '.status'
```
Error ratio falls back toward zero. **Confirm recovery with data, not with a feeling.**

**6. LEARN**
```bash
mkdir -p docs/postmortems docs/runbooks
cat > docs/postmortems/$(date +%Y-%m-%d)-oom-incident.md <<'EOF'
# Post-mortem: PayTrack API unavailable — OOMKilled

**Status:** Resolved   **Severity:** SEV2   **Duration:** ~4 minutes
**Authors:** <names>   **Reviewed:** <date>

## Summary
A deployment reduced the container memory limit to 24Mi. Every pod was OOM-killed on
start, entering CrashLoopBackOff. The service was unavailable for approximately four
minutes until the change was rolled back.

## Impact
- Users affected: 100% of requests during the window
- Duration: 4 minutes
- Error budget consumed: ~X% of the 28-day budget

## Timeline (UTC)
| Time | Event |
|---|---|
| T+0    | `kubectl set resources` applied the 24Mi limit |
| T+0:30 | Pods began OOMKilling; readiness failed; endpoints emptied |
| T+1:00 | Grafana "Pods up" fell to 0; error ratio spiked |
| T+2:00 | PayTrackAPIDown alert fired |
| T+3:00 | Engineer identified OOMKilled / exit 137 from pod events |
| T+3:30 | `kubectl rollout undo` issued |
| T+4:00 | Pods Ready; error ratio recovering |

## Contributing factors  (SYSTEM, never people)
1. No validation that a resource limit is plausible for the workload.
2. No admission policy rejecting limits below a minimum for this image.
3. No staging soak: the change went straight to the environment serving traffic.
4. Rollback was manual; the reconciler's auto-rollback covers image failures but not
   an out-of-band `kubectl set resources`.

## What went well
- The alert fired within 2 minutes of impact.
- Pod events named the cause precisely (`OOMKilled`, exit 137).
- Rollback restored service in under 30 seconds.

## Where we got lucky
- It happened during working hours with someone watching the dashboard.

## Action items
| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Kyverno policy: reject memory limits < 128Mi for this image | | |
| 2 | Load-test the pod to establish a documented memory floor | | |
| 3 | Extend the reconciler to auto-rollback on ANY failed rollout | | |
| 4 | Add a "Pods up" panel to the on-call default view | | |
EOF

cat > docs/runbooks/high-error-rate.md <<'EOF'
# Runbook: PayTrack API high error rate / error-budget burn

**Alert:** PayTrackAPIErrorBudgetFastBurn · **Severity:** critical (page)

## 1. Confirm the impact (1 min)
- Grafana → "PayTrack API — RED Method". Check error ratio and Pods up.
- `curl -s http://paytrack.localhost:8080/health`

## 2. Was there a recent change? (2 min)
- `kubectl rollout history deployment/paytrack-api -n paytrack-dev`
- `git log --oneline -5 -- k8s/overlays/`
- **If a deploy landed in the last 30 minutes, roll it back FIRST and diagnose after.**

## 3. Triage the pods (2 min)
- `kubectl get pods -n paytrack-dev`
- `kubectl describe pod <pod> -n paytrack-dev`   ← read Events
- `kubectl logs <pod> -n paytrack-dev --previous`  ← for CrashLoopBackOff

| Symptom | Likely cause | Action |
|---|---|---|
| OOMKilled / exit 137 | Memory limit too low, or a leak | Raise the limit, or roll back |
| CrashLoopBackOff | Bad config or missing env var | Check `logs --previous` |
| 0/1 READY | Readiness failing, often a dependency | Check `/ready` and the database |
| ImagePullBackOff | Bad tag or registry auth | Fix the tag; check the pull secret |
| All healthy but 5xx | Application bug or downstream failure | Check logs and the database |

## 4. Mitigate
- `kubectl rollout undo deployment/paytrack-api -n paytrack-dev`   ← default action
- Scale out if it is a load problem: `kubectl scale --replicas=6`
- Database problem: check `kubectl exec postgres-0 -- pg_isready`

## 5. Verify
- Error ratio falling in Grafana; alert resolves within ~5 minutes.

## 6. After
- Open a post-mortem from `docs/postmortems/TEMPLATE.md` within 48 hours.
EOF
echo "Post-mortem and runbook written."
```

---

## Step 8 — Commit

```bash
kubectl delete pod traffic --ignore-not-found --now
git add k8s/monitoring/ docs/postmortems/ docs/runbooks/
git commit -m "feat(observability): Prometheus, Grafana, Alertmanager, SLO alerts

- kube-prometheus-stack via Helm, laptop-sized values
- ServiceMonitor discovers paytrack-api (serviceMonitorSelectorNilUsesHelmValues:
  false, or cross-namespace discovery silently fails)
- RED dashboard as JSON, version-controlled and reviewable
- SLO 99.5%: multi-window multi-burn-rate alerts at 14.4x (page) and 6x (ticket)
- absent() alert catches the service disappearing entirely
- runbook and a worked post-mortem from a real OOMKill incident"
git push -u origin HEAD
```

---

## ✅ Final checkpoint

```bash
kubectl get pods -n monitoring | head
curl -s localhost:9090/api/v1/rules | jq -r '[.data.groups[].rules[].name] | length' 2>/dev/null
curl -s 'localhost:9090/api/v1/query?query=up{job="paytrack-api"}' | jq -r '.data.result | length'
```
Grafana at **http://grafana.localhost:8080** shows live RED panels.

---

## 🧩 Stretch (homework)

1. **Loki for logs.** `helm install loki grafana/loki-stack` and pivot from a metric spike to
   the matching log lines in one click. Same label vocabulary, same UI.
2. **Alertmanager routing.** Configure a Slack or webhook receiver, plus `inhibit_rules` so
   `PayTrackAPIDown` suppresses `PayTrackAPIHighLatency` — one root cause, one page.
3. **Provision dashboards automatically.** Put the JSON in a ConfigMap labelled
   `grafana_dashboard: "1"` so Grafana loads it on start. No manual import, ever.
4. **A real SLO burn.** Scale to 1 replica, hammer it until it 5xx's, and watch the fast-burn
   alert fire and then resolve on its own.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| App not in Prometheus targets | `serviceMonitorSelectorNilUsesHelmValues` left at default | Set it to `false` and upgrade the release |
| ServiceMonitor ignored | Selector does not match the **Service** labels | Match on the Service, not the pods |
| Grafana panels show `NaN` | Division by zero with no traffic | `clamp_min()` in the denominator (already applied) |
| Alerts never fire | Rule group not loaded | Check `release: monitoring` on the PrometheusRule |
| Prometheus pod evicted | Insufficient memory | Lower `retention`; free RAM by stopping other stacks |
| `histogram_quantile` returns NaN | Missing `sum by (le)` | Always aggregate by `le` first |

---

## 🎯 Outcome

A full monitoring stack on the cluster; the app scraped via a ServiceMonitor; a
version-controlled RED dashboard; an SLO with multi-window burn-rate alerts; and a real
incident detected, triaged, mitigated, verified and written up.

**Next:** [Lab 19 — Capstone](../lab-19-capstone/README.md)

---

<details>
<summary><strong>Instructor notes</strong></summary>

- **Install the Helm chart at the very start of day 6** (or before the break) — it takes 5–8
  minutes to pull and settle. Do not let it eat the lab.
- **The three things that go wrong:**
  1. `serviceMonitorSelectorNilUsesHelmValues`. It is in the values file — but if anyone
     installs the chart with defaults, their app never appears and there is no error message.
  2. Out of memory. Insist on `docker compose down`, removing the Ansible nodes and stopping
     Jenkins first.
  3. `histogram_quantile` without `sum by (le)` returning NaN. Show the correct form twice.
- **Step 7 is the lab.** Run it as a real incident with roles: someone is Incident Commander,
  someone drives, someone keeps the timeline. Then write the post-mortem together.
- **Debrief question:** "Your last production incident: how long from impact to detection?
  What told you — an alert, or a customer?"
</details>
