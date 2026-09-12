"""Unit tests for PayTrack API.

They run with no database and no network: `build_store("")` returns the in-memory
store. A CI job that needs infrastructure to run its unit tests is a job that will
be flaky - and in a bank, a flaky control is one the auditors will eventually find
has been routinely overridden.
"""
import json

import pytest

from src.app import create_app
from src.config import Config


class TestConfig(Config):
    DATABASE_URL = ""            # force the in-memory store
    VERSION = "test"
    READINESS_REQUIRES_DB = False
    REFERRAL_LIMIT_MINOR = 500000        # 5 000.00


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


# ── platform behaviour ────────────────────────────────────────────────────────
def test_health_is_always_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_ready_reports_backend(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.get_json()["store"] == "memory"


def test_info_exposes_version_and_entity(client):
    body = client.get("/api/v1/info").get_json()
    assert body["version"] == "test"
    assert body["app"] == "PayTrack API"
    assert body["entity"] == "retail"


def test_index_renders_banner(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"PayTrack API" in r.data


def test_metrics_are_exposed(client):
    client.get("/health")
    body = client.get("/metrics").data.decode()
    assert "paytrack_http_requests_total" in body
    assert "paytrack_build_info" in body


def test_unknown_route_returns_json_404(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not found"


# ── authorisation behaviour ───────────────────────────────────────────────────
def test_record_and_list_authorisation(client):
    created = client.post(
        "/api/v1/authorisations",
        data=json.dumps({
            "merchant": "NORTHGATE FUEL",
            "status": "approved",
            "amount_minor": 4599,
            "currency": "GBP",
            "card_last4": "4242",
        }),
        content_type="application/json",
    )
    assert created.status_code == 201
    row = created.get_json()
    assert row["merchant"] == "NORTHGATE FUEL"
    assert row["amount_minor"] == 4599       # integer minor units, not 45.99
    assert row["id"] == 1

    listed = client.get("/api/v1/authorisations").get_json()
    assert listed["count"] == 1
    assert listed["by_status"]["approved"] == 1


def test_amount_above_referral_limit_is_referred(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "PRESTIGE MOTORS", "amount_minor": 1250000, "card_last4": "1881",
    })
    assert r.status_code == 201
    # 12 500.00 exceeds the 5 000.00 referral limit -> referred, not auto-approved
    assert r.get_json()["status"] == "referred"


def test_amount_below_referral_limit_is_approved(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "CITY CAFE", "amount_minor": 320, "card_last4": "1881",
    })
    assert r.get_json()["status"] == "approved"


def test_rejects_missing_merchant(client):
    r = client.post("/api/v1/authorisations", json={"amount_minor": 100})
    assert r.status_code == 400
    assert "merchant" in r.get_json()["error"]


def test_rejects_bad_status(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "status": "exploded", "card_last4": "0000",
    })
    assert r.status_code == 400


def test_rejects_negative_amount(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "amount_minor": -1, "card_last4": "0000",
    })
    assert r.status_code == 400


def test_rejects_non_integer_amount(client):
    """Money must never arrive as a float - 45.99 is a rounding error waiting to happen."""
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "amount_minor": "45.99", "card_last4": "0000",
    })
    assert r.status_code == 400


def test_rejects_bad_currency(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "currency": "POUNDS", "card_last4": "0000",
    })
    assert r.status_code == 400


def test_rejects_bad_card_last4(client):
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "card_last4": "42",
    })
    assert r.status_code == 400


def test_refuses_a_full_card_number(client):
    """PCI-DSS: accepting a PAN would pull this service, its logs and its backups
    into cardholder-data scope. The API refuses it at the edge."""
    r = client.post("/api/v1/authorisations", json={
        "merchant": "X", "pan": "4111111111111111", "card_last4": "1111",
    })
    assert r.status_code == 400
    assert "primary account number" in r.get_json()["error"]


def test_declined_value_is_counted(client):
    client.post("/api/v1/authorisations", json={
        "merchant": "SUSPECT LTD", "status": "declined",
        "amount_minor": 99900, "card_last4": "0000",
    })
    body = client.get("/metrics").data.decode()
    assert "paytrack_declined_amount_minor_total" in body


# ── the readiness contract ────────────────────────────────────────────────────
def test_postgres_store_does_not_connect_on_construction():
    """REGRESSION GUARD for the whole probe lesson.

    PostgresStore must NOT open a connection in __init__. If it does, a container
    whose database is briefly unreachable crashes at boot instead of starting
    degraded — and then /health can never return 200 while /ready returns 503,
    which is the behaviour Module 4, Lab 11 and the Lab 19 game day all depend on.
    """
    pytest.importorskip("psycopg", reason="psycopg is in requirements.txt; skip if absent")
    from src.store import PostgresStore

    # A DSN pointing at a host that cannot resolve. Constructing must still succeed.
    store = PostgresStore("postgresql://u:p@no-such-host.invalid:5432/db")
    assert store.backend == "postgres"
    # ...and it must report itself unhealthy rather than raising.
    assert store.healthy() is False


def test_app_starts_and_serves_health_when_the_ledger_is_unreachable():
    """/health stays 200 (liveness: the process is fine) while /ready returns 503
    (readiness: it cannot serve). This is what stops a database blip becoming a
    cluster-wide restart storm."""
    pytest.importorskip("psycopg", reason="psycopg is in requirements.txt; skip if absent")

    class DownConfig(Config):
        DATABASE_URL = "postgresql://u:p@no-such-host.invalid:5432/db"
        READINESS_REQUIRES_DB = True

    app = create_app(DownConfig)          # must not raise
    with app.test_client() as c:
        assert c.get("/health").status_code == 200
        r = c.get("/ready")
        assert r.status_code == 503
        assert r.get_json()["status"] == "degraded"
