"""Runtime configuration for PayTrack API.

Every setting comes from an environment variable so that the *same* image can be
promoted from a laptop, to a Compose stack, to Kubernetes, without a rebuild.
This is the 12-Factor "config in the environment" rule, and in a regulated bank it
is also an audit control: the artefact that passed testing is bit-for-bit the
artefact that reaches production, and only its configuration differs.
"""
import os


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # Cosmetic identity - drives the banner colour used in the blue/green + canary labs.
    APP_NAME = os.getenv("APP_NAME", "PayTrack API")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    COLOR = os.getenv("APP_COLOR", "blue")           # blue | green | canary
    ENVIRONMENT = os.getenv("APP_ENV", "local")      # local | dev | uat | prod

    # Banking context: which entity and ledger this instance serves. Multi-entity
    # banks run the same image per legal entity with different configuration.
    ENTITY = os.getenv("BANK_ENTITY", "retail")      # retail | corporate | cards
    REGION = os.getenv("APP_REGION", "local")        # data-residency marker

    # Storage. When DATABASE_URL is unset the app falls back to an in-memory store so
    # that Lab 02 (plain git) and the unit tests run with zero infrastructure.
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    USE_DB = bool(DATABASE_URL)

    # Operational toggles
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    READINESS_REQUIRES_DB = _flag("READINESS_REQUIRES_DB", "true")
    PORT = int(os.getenv("PORT", "8080"))

    # Business rule: authorisations above this value are referred, not auto-approved.
    # Held in config, not code, so Risk can change the limit without a code release -
    # the "separate deploy from release" principle applied to a banking control.
    REFERRAL_LIMIT_MINOR = int(os.getenv("REFERRAL_LIMIT_MINOR", "500000"))  # 5 000.00
