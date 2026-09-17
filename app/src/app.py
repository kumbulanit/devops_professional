"""PayTrack API - the single application used by every lab in this course.

A card-authorisation tracking service: the sort of small, high-volume, always-on
internal service a bank runs dozens of. It is deliberately simple, but every
design decision in it is one a payments team really has to make.

Endpoints
---------
GET  /                        HTML banner page. Colour from APP_COLOR, text from
                              APP_VERSION. Used to *see* blue/green and canary splits.
GET  /health                  Liveness. "Is the process alive?" - never touches the
                              database, so a DB blip cannot cause a restart storm.
GET  /ready                   Readiness. "Can I serve?" - checks the ledger database.
GET  /api/v1/authorisations   List recent authorisation records (JSON).
POST /api/v1/authorisations   Record an authorisation decision (JSON body).
GET  /metrics                 Prometheus exposition format.
GET  /api/v1/info             Build and deployment identity. Which version is live?

Banking notes carried through the labs
--------------------------------------
* Money is an INTEGER in minor units. Never a float.
* No PAN is accepted or stored - only the last four digits - to keep this service
  out of PCI-DSS cardholder-data scope.
* Logs carry no cardholder data and no personal data; only the last four digits,
  which are not sensitive on their own.
* The referral limit is configuration, not code, so Risk can change it without a
  release. Deploy and release are separate things.
"""
from __future__ import annotations

import logging
import os
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from .config import Config
from .store import VALID_STATUSES, build_store

# --------------------------------------------------------------------------------------
# Metrics. Declared at import time so Prometheus sees a stable set of series.
# Label values are LOW CARDINALITY on purpose - never a merchant id, a card number
# or a request id, which would create a new time series per transaction.
# --------------------------------------------------------------------------------------
REQUESTS = Counter(
    "paytrack_http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "paytrack_http_request_duration_seconds", "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
AUTHORISATIONS = Counter(
    "paytrack_authorisations_total", "Authorisation decisions recorded",
    ["status", "currency"],
)
DECLINE_AMOUNT = Counter(
    "paytrack_declined_amount_minor_total", "Value of declined authorisations, minor units",
    ["currency"],
)
STORED = Gauge("paytrack_authorisations_stored", "Authorisation records currently stored")
BUILD_INFO = Gauge(
    "paytrack_build_info", "Build metadata (always 1)",
    ["version", "color", "env", "entity"],
)

BANNER = """<!doctype html>
<title>{name} {version}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #0e1116; color: #e6edf3; }}
  .banner {{ background: {css}; height: 44vh; display: flex; align-items: center;
             justify-content: center; flex-direction: column; }}
  .banner h1 {{ font-size: 3rem; margin: 0; color: #fff; letter-spacing: -1px; }}
  .banner p  {{ font-size: 1.2rem; margin: .4rem 0 0; color: rgba(255,255,255,.85); }}
  main {{ max-width: 760px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
  code {{ background: #1c222b; padding: .15rem .4rem; border-radius: 4px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #222a35; }}
  .note {{ color: #8b949e; font-size: .9rem; }}
</style>
<div class="banner">
  <h1>{name}</h1>
  <p>version {version} &middot; {color} &middot; {env} &middot; {entity} banking</p>
</div>
<main>
  <p>Serving from host <code>{host}</code> in region <code>{region}</code>,
     using the <code>{backend}</code> ledger store.</p>
  <table>
    <tr><th>Endpoint</th><th>Purpose</th></tr>
    <tr><td><code>/health</code></td><td>liveness probe</td></tr>
    <tr><td><code>/ready</code></td><td>readiness probe (checks the ledger)</td></tr>
    <tr><td><code>/api/v1/authorisations</code></td><td>list / record authorisations</td></tr>
    <tr><td><code>/metrics</code></td><td>Prometheus metrics</td></tr>
  </table>
  <p class="note">Amounts are held in minor units as integers. No primary account
     number is accepted or stored - only the last four digits.</p>
</main>"""

CSS_FOR = {
    "blue":   "linear-gradient(135deg,#1f6feb,#123a80)",
    "green":  "linear-gradient(135deg,#2ea043,#12602a)",
    "canary": "linear-gradient(135deg,#d29922,#8a5b00)",
    "red":    "linear-gradient(135deg,#da3633,#7d1a18)",
}


def create_app(config: type[Config] = Config) -> Flask:
    """Application factory. Tests build their own instance instead of importing a
    global, which is what lets pytest run several configurations in one session."""
    app = Flask(__name__)
    app.config.from_object(config)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format=(
            '{"ts":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","msg":"%(message)s"}'
        ),
    )
    log = logging.getLogger("paytrack")

    store = build_store(config.DATABASE_URL)
    log.info("ledger store backend=%s entity=%s", store.backend, config.ENTITY)
    BUILD_INFO.labels(config.VERSION, config.COLOR, config.ENVIRONMENT, config.ENTITY).set(1)

    # ---------------------------------------------------------------- instrumentation
    @app.before_request
    def _start_timer() -> None:
        request._started = time.perf_counter()

    @app.after_request
    def _record(response: Response) -> Response:
        endpoint = request.endpoint or "unknown"
        elapsed = time.perf_counter() - getattr(request, "_started", time.perf_counter())
        LATENCY.labels(request.method, endpoint).observe(elapsed)
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        return response

    # ------------------------------------------------------------------------ routes
    @app.get("/")
    def index() -> str:
        return BANNER.format(
            name=config.APP_NAME,
            version=config.VERSION,
            color=config.COLOR,
            env=config.ENVIRONMENT,
            entity=config.ENTITY,
            css=CSS_FOR.get(config.COLOR, CSS_FOR["blue"]),
            host=os.getenv("HOSTNAME", "localhost"),
            region=config.REGION,
            backend=store.backend,
        )

    @app.get("/health")
    def health():
        """Liveness: deliberately dependency-free. If this fails the process is broken."""
        return jsonify(status="ok", version=config.VERSION), 200

    @app.get("/ready")
    def ready():
        """Readiness: fails while the ledger is unreachable so the load balancer stops
        sending traffic here, without the orchestrator killing the pod."""
        if config.READINESS_REQUIRES_DB and not store.healthy():
            return jsonify(status="degraded", store=store.backend), 503
        return jsonify(status="ready", store=store.backend), 200

    @app.get("/api/v1/info")
    def info():
        return jsonify(
            app=config.APP_NAME, version=config.VERSION, color=config.COLOR,
            environment=config.ENVIRONMENT, entity=config.ENTITY,
            store=store.backend,
            referral_limit_minor=config.REFERRAL_LIMIT_MINOR,
            host=os.getenv("HOSTNAME", "localhost"),
        )

    @app.get("/api/v1/authorisations")
    def list_authorisations():
        limit = min(int(request.args.get("limit", 50)), 200)
        return jsonify(
            items=store.list(limit),
            count=store.count(),
            by_status=store.totals_by_status(),
        )

    @app.post("/api/v1/authorisations")
    def create_authorisation():
        body = request.get_json(silent=True) or {}

        merchant = body.get("merchant")
        if not merchant:
            return jsonify(error="field 'merchant' is required"), 400

        # Reject a full card number outright. Accepting one would put this service
        # into PCI-DSS cardholder-data scope, and every downstream log with it.
        if body.get("pan") or body.get("card_number"):
            return jsonify(error="primary account numbers are not accepted"), 400

        card_last4 = str(body.get("card_last4", "0000"))
        if not (card_last4.isdigit() and len(card_last4) == 4):
            return jsonify(error="card_last4 must be exactly 4 digits"), 400

        try:
            amount_minor = int(body.get("amount_minor", 0))
        except (TypeError, ValueError):
            return jsonify(error="amount_minor must be an integer in minor units"), 400
        if amount_minor < 0:
            return jsonify(error="amount_minor must not be negative"), 400

        currency = str(body.get("currency", "GBP")).upper()
        if len(currency) != 3 or not currency.isalpha():
            return jsonify(error="currency must be a 3-letter ISO 4217 code"), 400

        # Business rule from configuration: above the referral limit, refer to a human.
        status = body.get("status")
        if status is None:
            status = "referred" if amount_minor > config.REFERRAL_LIMIT_MINOR else "approved"
        if status not in VALID_STATUSES:
            return jsonify(
                error=f"status must be one of {'|'.join(sorted(VALID_STATUSES))}"
            ), 400

        row = store.add(merchant, status, amount_minor, currency, card_last4)

        AUTHORISATIONS.labels(status, currency).inc()
        if status == "declined":
            DECLINE_AMOUNT.labels(currency).inc(amount_minor)

        # Structured log. Note what is NOT here: no PAN, no cardholder name, no
        # customer identifier. Logs are widely readable and long-retained.
        log.info(
            "authorisation recorded merchant=%s status=%s amount_minor=%s currency=%s last4=%s",
            merchant, status, amount_minor, currency, card_last4,
        )
        return jsonify(row), 201

    @app.get("/metrics")
    def metrics():
        STORED.set(store.count())
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="not found"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT)
