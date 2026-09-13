# Module 8 — Monitoring, Logging and Observability

> **Day 6 · ~25 minutes of lecture · Lab 18**
>
> **Learning outcomes.** You can distinguish monitoring from observability precisely;
> describe the three pillars and what each is good and bad at; choose metrics using RED and
> USE; explain Prometheus' data model, scrape architecture and PromQL basics; define SLI,
> SLO and error budget and use burn rate for alerting; design alerts people do not ignore;
> and run an incident with a usable structure.

---

## 8.1 Monitoring vs observability

> **Monitoring** — collecting and analysing **predefined** metrics and logs to determine
> whether a system is behaving as expected, and alerting when it is not.
> *It answers questions you thought of in advance.*

> **Observability** — a property of a system: the degree to which you can understand its
> **internal state from its external outputs**, including for failure modes you did not
> anticipate.
> *It lets you ask new questions without shipping new code.*

```
   MONITORING                              OBSERVABILITY
   ───────────────────────────────         ─────────────────────────────────────────
   "Is CPU above 80 %?"                    "Why are checkout requests from Android
   "Is the service up?"                     users in eu-west-1 on app version 4.2.1
   "Did the error rate exceed 1 %?"         slow only between 14:00 and 15:00?"

   KNOWN unknowns                          UNKNOWN unknowns
   Dashboards + thresholds                 High-cardinality, high-dimensional data
   Necessary, and not sufficient           Explore without deploying new instrumentation
```

Monitoring is not obsolete — you need both. Monitoring tells you *something is wrong*;
observability lets you find out *what*. In a monolith, monitoring was often enough. In a
distributed system with dozens of services, the number of possible failure modes exceeds
what anyone can enumerate in advance, and that is what forced the shift.

### The three pillars

```
 ┌─────────────────────┬──────────────────────┬────────────────────────────┐
 │      METRICS        │        LOGS          │          TRACES            │
 ├─────────────────────┼──────────────────────┼────────────────────────────┤
 │ Numeric measurements│ Timestamped, discrete│ The causal path of ONE     │
 │ over time,          │ event records        │ request across services    │
 │ aggregatable        │                      │                            │
 │                     │                      │                            │
 │ "p95 latency is     │ "OrderService threw  │ "This request: gateway 2ms │
 │  480 ms"            │  NullPointer at …"   │  → auth 8ms → db 1 840ms"  │
 ├─────────────────────┼──────────────────────┼────────────────────────────┤
 │ ✅ cheap, constant  │ ✅ rich detail,      │ ✅ shows WHERE the time    │
 │    storage cost;    │    exact context     │    goes; essential for     │
 │    great for alerts │                      │    microservices           │
 │ ❌ no per-request   │ ❌ expensive at      │ ❌ needs instrumentation   │
 │    detail; cardin-  │    volume; hard to   │    and context propagation;│
 │    ality explodes   │    aggregate         │    usually sampled         │
 ├─────────────────────┼──────────────────────┼────────────────────────────┤
 │ Prometheus          │ Loki, ELK/OpenSearch │ Jaeger, Tempo              │
 │                     │ Splunk               │ (OpenTelemetry)            │
 └─────────────────────┴──────────────────────┴────────────────────────────┘
        Bound together by CORRELATION IDs / trace IDs — the fourth thing that matters,
        and the one most teams skip. A log line without a trace ID is an orphan.
```

**OpenTelemetry (OTel)** is the vendor-neutral CNCF standard for generating and exporting
all three signals. Instrument once with OTel and you can change backend without touching
application code — the strategic choice for new work.

---

## 8.2 Metrics

### Types

| Type | Definition | Only goes… | Examples |
|---|---|---|---|
| **Counter** | Cumulative; monotonically increasing (resets to 0 on restart) | up | requests_total, errors_total |
| **Gauge** | A value that goes up and down | either way | memory_bytes, queue_depth, active_connections |
| **Histogram** | Observations bucketed by size, plus `_sum` and `_count`; **quantiles computed at query time, aggregatable across instances** | — | request duration, response size |
| **Summary** | Quantiles computed **client-side** | — | Avoid: **you cannot average percentiles across instances** |

**Use histograms for latency, not summaries.** Averaging p95 across ten pods is
mathematically meaningless; a histogram lets Prometheus compute a true aggregate quantile.

> ⚠️ **Never average a percentile.** The mean of ten p95s is not the p95. This mistake makes
> dashboards confidently wrong.

### RED — for request-driven services (use this for PayTrack API)

| Metric | Definition | PromQL |
|---|---|---|
| **R**ate | Requests per second | `sum(rate(paytrack_http_requests_total[5m]))` |
| **E**rrors | Failed requests per second (and as a ratio) | `sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))` |
| **D**uration | Latency distribution — p50, p95, p99 | `histogram_quantile(0.95, sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))` |

### USE — for resources (nodes, disks, pools)

| Metric | Definition |
|---|---|
| **U**tilisation | % of time the resource was busy |
| **S**aturation | Queued work the resource could not service — **usually the earliest warning signal** |
| **E**rrors | Error events for the resource |

### The Four Golden Signals (Google SRE)

**Latency · Traffic · Errors · Saturation.** Effectively RED + saturation. Any of the three
frameworks is fine — the failure is having no framework and instrumenting whatever was easy.

> **Measure latency of successful and failed requests separately.** A fast 500 flatters your
> latency graph while your users are broken.

---

## 8.3 Prometheus

> **Prometheus** — an open-source monitoring system and time-series database that **pulls**
> metrics over HTTP from instrumented targets it discovers dynamically, stores them as
> multi-dimensional time series, and evaluates rules over them in **PromQL**.

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                              PROMETHEUS SERVER                               │
 │  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────────────┐    │
 │  │  RETRIEVAL   │──►│     TSDB     │◄──│  PromQL engine + rule evaluator│    │
 │  │ scrapes /    │   │ time-series  │   │  recording rules · alert rules │    │
 │  │ metrics on   │   │ storage      │   └────────────┬──────────────────┘    │
 │  │ an interval  │   └──────────────┘                │  fires alerts          │
 │  └──────┬───────┘                                   ▼                        │
 │         │ service discovery                 ┌──────────────┐                 │
 │         │ (kubernetes_sd, file_sd, …)       │ ALERTMANAGER │                 │
 └─────────┼───────────────────────────────────┴──────┬───────┴─────────────────┘
           │ HTTP GET /metrics                        │ group · inhibit · silence · route
   ┌───────▼────────┐ ┌──────────────┐ ┌────────────┐ ▼
   │ paytrack-api pods │ │ node-exporter│ │ kube-state │  email · Slack · PagerDuty · webhook
   │ (app metrics)  │ │ (host metrics│ │ -metrics   │
   └────────────────┘ └──────────────┘ └────────────┘        ┌──────────┐
                                                              │ GRAFANA  │ queries Prometheus
                                                              └──────────┘
```

### Pull vs push, and why it matters

Prometheus **pulls**. Consequences: the scrape itself is a health check (`up` is a free
metric); there is no client-side buffering to lose; targets are discovered dynamically
(perfect for Kubernetes, where pods appear and vanish); and you can hit `/metrics` in a
browser to debug. For short-lived batch jobs that die before a scrape, use the
**Pushgateway** — and only for that.

### The data model

```
   paytrack_http_requests_total{method="POST", endpoint="create_check", status="201"}  4821
   └──────── metric name ────────┘└──────────────── labels ────────────────────┘   value
```

Every unique **combination of labels** is a separate time series.

> 🔴 **Cardinality is the #1 way to destroy a Prometheus.** Never use user IDs, email
> addresses, request IDs, full URLs with parameters, or timestamps as label values.
> `endpoint="/api/v1/authorisations"` is right; `path="/api/v1/authorisations/8213/detail?t=169…"` creates a
> new time series per request and will exhaust memory.

### PromQL essentials

```promql
# instant vector: current value of every matching series
paytrack_http_requests_total{status="200"}

# range vector → per-second rate over 5 minutes. ALWAYS use rate() on counters.
rate(paytrack_http_requests_total[5m])

# aggregate away the labels you do not care about
sum by (endpoint) (rate(paytrack_http_requests_total[5m]))

# error RATIO — the numerator and denominator must be aggregated the same way
sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))
  / sum(rate(paytrack_http_requests_total[5m]))

# p95 latency from a histogram (note: sum by (le) before histogram_quantile)
histogram_quantile(0.95,
  sum by (le) (rate(paytrack_http_request_duration_seconds_bucket[5m])))

# is the target up? 1 = scrape succeeded, 0 = failed
up{job="paytrack-api"}
```

| Function | Use |
|---|---|
| `rate()` | Per-second average over a range. **Counters only.** Handles resets |
| `irate()` | Instant rate from the last two points — spiky graphs, not alerts |
| `increase()` | Total increase over a range (= `rate() × seconds`) |
| `histogram_quantile()` | Quantile from histogram buckets |
| `sum/avg/max by (label)` | Aggregation |
| `absent()` | Alert when a series disappears entirely |
| `predict_linear()` | Extrapolate — "will the disk fill within 4 hours?" |

**Recording rules** pre-compute expensive expressions on a schedule, so dashboards and
alerts read a cheap pre-aggregated series instead of recomputing across thousands of series.

---

## 8.4 Logging

### Practices

| Practice | Why |
|---|---|
| **Structured (JSON), not free text** | Machine-parseable, queryable, aggregatable |
| **Log to stdout/stderr** | The platform collects it. Never write log files inside a container |
| **Correlation / trace ID on every line** | The only way to reconstruct one request across services |
| **Consistent levels** | ERROR = needs action · WARN = suspicious · INFO = significant events · DEBUG = off in prod |
| **Never log secrets or PII** | Logs are widely readable and long-retained — this is a data-protection incident waiting to happen |
| **Sample high-volume paths** | Log 100 % of errors, sample successes |
| **Retention tiers** | Hot 7 days searchable, warm 30, cold archive — logs are the largest observability cost |

```json
{"ts":"2026-09-07T09:14:22Z","level":"ERROR","service":"paytrack-api","version":"1.4.2",
 "entity":"retail","trace_id":"4f2b8c…","span_id":"a12f",
 "event":"ledger_write_failed","merchant":"NORTHGATE FUEL","currency":"GBP",
 "card_last4":"4242","error":"connection timeout","duration_ms":5031}

Note what is deliberately ABSENT: no PAN, no cardholder name, no account number, no
customer identifier. In a bank, log records are widely readable, long-retained and
frequently exported — a PAN in a log line is a PCI-DSS finding, and a customer name
beside a transaction is a GDPR one.
```
Everything is a queryable field. Compare with
`ERROR: something went wrong writing to db` — which tells an on-call engineer nothing at
03:00.

### The stacks

| Stack | Components | Notes |
|---|---|---|
| **ELK / Elastic** | Elasticsearch (store/search) · Logstash or Beats (ingest) · Kibana (UI) | Powerful, heavy; indexes everything → expensive at volume |
| **OpenSearch** | Apache-2.0 fork of Elasticsearch + OpenSearch Dashboards | Same shape, permissive licence |
| **Loki + Promtail + Grafana** | Indexes only **labels**, not the log body | Much cheaper; deliberately "Prometheus for logs"; same label model, same Grafana |
| **Cloud native** | CloudWatch, Cloud Logging, Azure Monitor | Zero ops, per-GB cost |

For a Prometheus/Grafana shop, **Loki** is the path of least resistance: same label
vocabulary, same UI, and you can pivot from a metric spike straight to the matching logs.

---

## 8.5 SLI, SLO and error budgets

> **SLI (Service Level Indicator)** — a quantitative measure of some aspect of service
> quality, expressed as *good events ÷ valid events*.
> Example: proportion of HTTP requests completing in under 300 ms with a non-5xx status.

> **SLO (Service Level Objective)** — a target value for an SLI over a time window.
> Example: 99.5 % of requests succeed in under 300 ms, measured over 28 rolling days.

> **SLA (Service Level Agreement)** — a **contract** with financial or legal consequences.
> Always looser than your internal SLO, so you find out before your customer does.

> **Error budget** — `100 % − SLO`. The amount of unreliability you are permitted to spend.
> At a 99.5 % SLO over 28 days, the budget is **0.5 % = ~3 h 22 m** of failure.

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  ERROR BUDGET — 28-day window, SLO 99.5 %  →  budget = 3 h 22 m          │
 │  ████████████████████████████░░░░░░░░░   72 % consumed, 57 min remaining │
 └──────────────────────────────────────────────────────────────────────────┘
     Budget remaining        →  ship freely; take risks; deploy often
     Budget nearly exhausted →  freeze features; reliability work only, by prior agreement
     Budget blown            →  everything stops until the budget recovers
```

The error budget is what converts "Dev wants speed, Ops wants stability" from a political
argument into **one shared number that both teams manage**. That is its real purpose.

### Availability targets

| SLO | Downtime / 30 days | Downtime / year |
|---|---|---|
| 99 % | 7 h 12 m | 3.65 days |
| 99.5 % | 3 h 36 m | 1.83 days |
| 99.9 % ("three nines") | 43 m 12 s | 8.77 h |
| 99.95 % | 21 m 36 s | 4.38 h |
| 99.99 % ("four nines") | 4 m 19 s | 52.6 m |
| 99.999 % | 26 s | 5.26 m |

**Do not choose 99.99 % by default.** Each nine multiplies cost, and if your users' own
network is 99.9 %, they cannot perceive the difference. Pick the SLO from what users
actually need — and make it explicitly *lower* than 100 %, so that risk-taking is
legitimate.

---

## 8.6 Alerting

### The rules that make alerts survivable

| Rule | Why |
|---|---|
| **Alert on symptoms, not causes** | "Error ratio > 2 %" (users hurting) beats "CPU > 80 %" (may be fine) |
| **Every alert must be actionable** | If there is nothing to do, it is a dashboard entry, not a page |
| **Every alert needs a runbook link** | 03:00 is not the time to work out first principles |
| **Page only for user-facing, urgent problems** | Everything else is a ticket |
| **Alert on SLO burn rate**, not raw thresholds | Ties urgency to actual budget consumption |
| **Use `for:` durations** | Prevents flapping on transient blips |
| **Group, inhibit and silence** | One node failure must not produce 200 pages |
| **Review alerts monthly** | Delete anything nobody acted on |

> **Alert fatigue is a safety failure, not an annoyance.** A team that receives 50 pages a
> night stops reading them, and misses the one that mattered. Fewer, better alerts is a
> reliability improvement.

### Multi-window, multi-burn-rate alerting

> **Burn rate** — how fast you are consuming the error budget relative to the rate that
> would exactly exhaust it over the window. Burn rate 1 = on track to use exactly the whole
> budget; burn rate 14.4 = you will exhaust a 30-day budget in ~2 days.

| Burn rate | Long window | Short window | Budget consumed | Action |
|---|---|---|---|---|
| 14.4× | 1 h | 5 m | 2 % in 1 h | **Page immediately** |
| 6× | 6 h | 30 m | 5 % in 6 h | **Page** |
| 3× | 1 d | 2 h | 10 % in 1 d | Ticket |
| 1× | 3 d | 6 h | 10 % in 3 d | Ticket |

Both windows must fire: the long window establishes that it is real, the short window that
it is still happening (so the alert resolves when the problem does).

```yaml
groups:
  - name: paytrack-api-slo
    rules:
      - alert: PayTrackAPIHighErrorRateFastBurn
        expr: |
          (sum(rate(paytrack_http_requests_total{status=~"5.."}[1h]))
             / sum(rate(paytrack_http_requests_total[1h]))) > (14.4 * 0.005)
          and
          (sum(rate(paytrack_http_requests_total{status=~"5.."}[5m]))
             / sum(rate(paytrack_http_requests_total[5m]))) > (14.4 * 0.005)
        for: 2m
        labels: { severity: page }
        annotations:
          summary: "PayTrack API is burning its error budget 14.4× too fast"
          runbook: "https://github.com/<your-username>/paytrack-api/blob/main/docs/runbooks/high-error-rate.md"
```

---

## 8.7 Incident response

```
 DETECT ──► TRIAGE ──► MITIGATE ──► RESOLVE ──► LEARN
   │          │           │            │          │
 alert or   severity?   RESTORE      root      blameless
 report     who is      SERVICE      cause     post-mortem
            IC?         FIRST        fixed     → backlog items
```

**Roles** (assign explicitly, even in a small team): **Incident Commander** (coordinates,
decides — does *not* debug), **Operations/Subject lead** (does the hands-on work),
**Communications lead** (stakeholders and status page), **Scribe** (timeline).

**Severity levels** — define them in advance, because arguing about severity during an
incident wastes the first 15 minutes:

| Sev | Meaning | Response |
|---|---|---|
| **SEV1** | Complete outage or data loss; all users | Page immediately, all hands, exec comms |
| **SEV2** | Major degradation or a key feature down | Page, incident channel |
| **SEV3** | Minor degradation, workaround exists | Business hours |
| **SEV4** | Cosmetic / no user impact | Backlog |

**Mitigate before you diagnose.** Roll back, fail over, shed load, disable the feature flag
— restore the user first. Root cause is important, and it is not urgent.

### The blameless post-mortem

Required sections: **Summary · Impact (users, duration, money) · Timeline (with timestamps)
· Contributing factors · What went well · What went badly · Where we got lucky ·
Action items (each with an owner and a date)**.

Rules: no names in the narrative, only roles. No counterfactuals ("should have"). Ask
**"what made this failure possible and easy?"** rather than "who did it?". Publish it
organisation-wide — an unread post-mortem taught nobody anything.

**Action items are the product.** A post-mortem that produces no tracked, owned, dated work
was a therapy session.

---

## 8.8 Key terms

| Term | Definition |
|---|---|
| **Monitoring / Observability** | Predefined checks / ability to answer new questions from outputs |
| **Metrics / Logs / Traces** | Aggregatable numbers / discrete events / per-request causal paths |
| **OpenTelemetry** | Vendor-neutral standard for generating and exporting telemetry |
| **Counter / Gauge / Histogram / Summary** | Monotonic / up-down / bucketed / client-side quantiles |
| **Cardinality** | Number of distinct label combinations; the main scaling risk |
| **RED / USE / Golden Signals** | Rate-Errors-Duration / Utilisation-Saturation-Errors / L-T-E-S |
| **Scrape / Exporter / Pushgateway** | Prometheus pulling / a metrics adapter / a buffer for short jobs |
| **PromQL / Recording rule** | Prometheus query language / a pre-computed series |
| **SLI / SLO / SLA** | Measure / internal target / external contract |
| **Error budget / Burn rate** | Permitted unreliability / how fast it is being consumed |
| **Alert fatigue** | Desensitisation from too many low-value alerts |
| **Runbook** | Documented, tested procedure for handling a specific alert |
| **MTTD / MTTA / MTTR** | Mean time to detect / acknowledge / restore |
| **Incident Commander** | The person who coordinates an incident and does not debug |
| **Blameless post-mortem** | Systems-focused incident review producing owned action items |
| **Toil** | Manual, repetitive, automatable operational work |

---

## 8.9 Module 8 self-check

1. Give a question monitoring can answer and one it cannot, and say what observability adds.
2. Why must you never label a metric with a request ID?
3. Your dashboard averages p95 latency across 12 pods. Why is this wrong, and what is right?
4. Define error budget and explain how it resolves the speed-vs-stability argument.
5. Your team gets 60 pages a night. Give four concrete changes, in priority order.
6. Explain multi-window burn-rate alerting and why both windows are needed.
7. During a SEV1 you discover the root cause after 10 minutes but the fix will take 2 hours.
   What do you do?
8. What makes a post-mortem blameless, and how do you tell whether it worked?

---

**Next:** [Module 9 — Enterprise DevOps Best Practices](module-09-enterprise-devops.md)
· Lab: [18](../../labs/lab-18-observability/README.md)
