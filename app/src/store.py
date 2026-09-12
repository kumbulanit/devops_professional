"""Persistence for PayTrack authorisation records.

Two interchangeable backends behind one interface:

`MemoryStore`   - a dict. No dependencies. Used by unit tests and Lab 02.
`PostgresStore` - real SQL. Used from Lab 07 (Compose) onwards.

A CI job that needs a database to run its unit tests is a CI job that will be
flaky, and flaky pipelines get ignored - which in a bank means a control that
exists on paper and not in practice.

MONEY IS STORED IN MINOR UNITS AS AN INTEGER (pence/cents), never as a float.
0.1 + 0.2 != 0.3 in binary floating point; a rounding error in a ledger is a
reconciliation break and, eventually, a regulatory finding.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

VALID_STATUSES = {"approved", "declined", "referred"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MemoryStore:
    backend = "memory"

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []
        self._next_id = 1
        self._lock = threading.Lock()

    def healthy(self) -> bool:
        return True

    def add(self, merchant: str, status: str, amount_minor: int,
            currency: str, card_last4: str) -> dict[str, Any]:
        with self._lock:
            row = {
                "id": self._next_id,
                "merchant": merchant,
                "status": status,
                "amount_minor": amount_minor,
                "currency": currency,
                "card_last4": card_last4,
                "created_at": _now(),
            }
            self._next_id += 1
            self._rows.append(row)
            return row

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self._rows))[:limit]

    def count(self) -> int:
        return len(self._rows)

    def totals_by_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self._rows:
            out[r["status"]] = out.get(r["status"], 0) + 1
        return out


class PostgresStore:
    backend = "postgres"

    def __init__(self, dsn: str) -> None:
        import psycopg  # imported lazily so the memory path needs no driver

        self._psycopg = psycopg
        self._dsn = dsn
        self._migrated = False
        # DELIBERATELY no connection here. The process must start even when the
        # ledger is unreachable, so that /health stays 200 (the process is fine)
        # while /ready returns 503 (it cannot serve). Connecting in __init__ would
        # crash the container instead, turning a brief database blip into a
        # CrashLoopBackOff - which is the exact failure Module 4 warns about.

    def _ensure(self) -> None:
        """Migrate on first successful use, then never again. Lets the service
        start ahead of its database and converge when the database appears."""
        if not self._migrated:
            self.migrate()
            self._migrated = True

    def _connect(self):
        return self._psycopg.connect(self._dsn, connect_timeout=5)

    def migrate(self) -> None:
        """Create the table if it does not exist. Idempotent on purpose: safe to run on
        every container start, which is what makes rolling updates painless.

        Note `amount_minor BIGINT` - integer minor units, never NUMERIC-as-float and
        never a floating point type. Note also that there is no column for a full card
        number: storing a PAN would drag this service into PCI-DSS scope."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS authorisations (
                    id            BIGSERIAL PRIMARY KEY,
                    merchant      TEXT        NOT NULL,
                    status        TEXT        NOT NULL,
                    amount_minor  BIGINT      NOT NULL DEFAULT 0,
                    currency      CHAR(3)     NOT NULL DEFAULT 'GBP',
                    card_last4    CHAR(4)     NOT NULL DEFAULT '0000',
                    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_created_at "
                "ON authorisations (created_at DESC)"
            )
            conn.commit()

    def healthy(self) -> bool:
        """Readiness check. Also the point at which a service that started before
        its database catches up and runs its migration."""
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                ok = cur.fetchone()[0] == 1
            if ok and not self._migrated:
                self.migrate()
                self._migrated = True
            return ok
        except Exception:
            return False

    def add(self, merchant: str, status: str, amount_minor: int,
            currency: str, card_last4: str) -> dict[str, Any]:
        self._ensure()
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO authorisations "
                "(merchant, status, amount_minor, currency, card_last4) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, merchant, status, amount_minor, currency, card_last4, created_at",
                (merchant, status, amount_minor, currency, card_last4),
            )
            r = cur.fetchone()
            conn.commit()
        return {
            "id": r[0], "merchant": r[1], "status": r[2], "amount_minor": r[3],
            "currency": r[4], "card_last4": r[5],
            "created_at": r[6].isoformat(timespec="seconds"),
        }

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        self._ensure()
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, merchant, status, amount_minor, currency, card_last4, created_at "
                "FROM authorisations ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            return [
                {"id": r[0], "merchant": r[1], "status": r[2], "amount_minor": r[3],
                 "currency": r[4], "card_last4": r[5],
                 "created_at": r[6].isoformat(timespec="seconds")}
                for r in cur.fetchall()
            ]

    def count(self) -> int:
        self._ensure()
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM authorisations")
            return int(cur.fetchone()[0])

    def totals_by_status(self) -> dict[str, int]:
        self._ensure()
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT status, count(*) FROM authorisations GROUP BY status")
            return {row[0]: int(row[1]) for row in cur.fetchall()}


def build_store(dsn: str):
    return PostgresStore(dsn) if dsn else MemoryStore()
