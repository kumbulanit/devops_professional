#!/usr/bin/env bash
# =============================================================================
#  Lab 03A — build the Git practice repository ("the gym")
#
#  Creates ~/devops-course/git-gym: a copy of PayTrack API with a realistic
#  history — ten commits by four people over ten days. One of those commits
#  quietly breaks the card-fee maths; Part 5 of the lab finds it.
#
#  Safe to re-run: it deletes and rebuilds the gym, and touches nothing else.
# =============================================================================
set -euo pipefail

COURSE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GYM="$HOME/devops-course/git-gym"

if [ -z "$(git config user.email || true)" ]; then
  echo "Set your git identity first (Lab 00, Step 6):"
  echo '  git config --global user.name  "Your Name"'
  echo '  git config --global user.email "you@example.com"'
  exit 1
fi
[ -d "$COURSE/app/src" ] || { echo "Cannot find the course app in $COURSE/app"; exit 1; }

rm -rf "$GYM" "$GYM-origin.git" "$GYM-colleague"
mkdir -p "$GYM"
cd "$GYM"
git init -q -b main

ANA="Ana Silva <ana.silva@example.com>"
BEN="Ben Okafor <ben.okafor@example.com>"
CHEN="Chen Li <chen.li@example.com>"
YOU="$(git config user.name) <$(git config user.email)>"

commit() {   # commit "<author>" <days-ago> "<message>"
  git add -A
  git commit -q --author="$1" --date="$2 days ago" -m "$3"
}

# ── 1 · the service itself, tagged v1.0.0 ────────────────────────────────────
cp -R "$COURSE/app" app
rm -rf app/.venv app/.pytest_cache app/.coverage
find app -name __pycache__ -type d -prune -exec rm -rf {} +
printf '__pycache__/\n.venv/\n.pytest_cache/\n.coverage\n' > .gitignore
cat > README.md <<'EOF'
# PayTrack API — Git practice copy

This repository exists to be broken. Rebuild it at any time with:

    bash ~/devops-course/course-material/labs/lab-03a-git-going-further/setup-gym.sh
EOF
cat > CHANGELOG.md <<'EOF'
# Changelog

## Unreleased

## 1.0.0
- First release of PayTrack API.
EOF
commit "$YOU" 10 "feat: add PayTrack API service"
git tag -a v1.0.0 -m "PayTrack API 1.0.0"

# ── 2 · card fees arrive ─────────────────────────────────────────────────────
cat > app/src/fees.py <<'EOF'
"""Card fees. Money is an integer in minor units (cents) - never a float."""

FEE_BPS = 150  # 1.50 %, in basis points (1 basis point = 0.01 %)


def card_fee(amount_minor: int) -> int:
    """The fee for a card payment, in minor units.

    Always rounds DOWN: the bank never rounds a fee up in its own favour.
    """
    return amount_minor * FEE_BPS // 10_000
EOF
cat > app/tests/check_fees.py <<'EOF'
"""Checks the card-fee rules. Run it with:  python3 app/tests/check_fees.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from fees import card_fee  # noqa: E402

assert card_fee(10_000) == 150, card_fee(10_000)
assert card_fee(4_599) == 68, f"expected 68, got {card_fee(4_599)}: a fee was rounded UP"
print("fee checks passed")
EOF
commit "$ANA" 9 "feat(fees): add the card fee calculator"

# ── 3 · documentation ────────────────────────────────────────────────────────
mkdir -p docs
cat > docs/fees.md <<'EOF'
# How card fees work

PayTrack charges a fee on every card payment.

## The rate

The fee is 1.50 % of the payment amount.

## Money is never a float

Amounts are whole numbers of minor units (cents).
A payment of 45.99 is stored as 4599.

## Rounding

A fee that is not a whole number of cents is rounded down.
EOF
commit "$BEN" 8 "docs: explain how card fees are calculated"

# ── 4 · a minimum fee ────────────────────────────────────────────────────────
cat > app/src/fees.py <<'EOF'
"""Card fees. Money is an integer in minor units (cents) - never a float."""

FEE_BPS = 150  # 1.50 %, in basis points (1 basis point = 0.01 %)
MIN_FEE_MINOR = 5  # every card payment pays at least 5 cents


def card_fee(amount_minor: int) -> int:
    """The fee for a card payment, in minor units.

    Always rounds DOWN: the bank never rounds a fee up in its own favour.
    """
    return max(MIN_FEE_MINOR, amount_minor * FEE_BPS // 10_000)
EOF
printf 'assert card_fee(100) == 5, card_fee(100)\nprint("minimum fee checks passed")\n' >> app/tests/check_fees.py
commit "$CHEN" 7 "feat(fees): add a minimum fee of 5 cents"

# ── 5 · docs for the minimum fee ─────────────────────────────────────────────
printf '\n## Minimum fee\n\nEvery card payment pays at least 5 cents.\n' >> docs/fees.md
commit "$ANA" 6 "docs: describe the minimum fee"

# ── 6 · the "harmless" refactor that breaks the rounding rule ────────────────
python3 - <<'EOF'
import pathlib
p = pathlib.Path("app/src/fees.py")
p.write_text(p.read_text().replace(
    "amount_minor * FEE_BPS // 10_000", "round(amount_minor * FEE_BPS / 10_000)"))
EOF
commit "$BEN" 5 "refactor(fees): simplify the fee maths"

# ── 7 · more tests (none of them catch it) ───────────────────────────────────
printf 'assert card_fee(1_000_000) == 15_000, card_fee(1_000_000)\n' >> app/tests/check_fees.py
commit "$CHEN" 4 "test(fees): check a large payment"

# ── 8 · worked examples ──────────────────────────────────────────────────────
printf '\n## Examples\n\n| Payment | Fee |\n|---|---|\n| 100.00 | 1.50 |\n| 1.00 | 0.05 (the minimum) |\n' >> docs/fees.md
commit "$ANA" 3 "docs: add worked fee examples"

# ── 9 · changelog ────────────────────────────────────────────────────────────
python3 - <<'EOF'
import pathlib
p = pathlib.Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "## Unreleased\n", "## Unreleased\n- Card fees, with a 5-cent minimum.\n"))
EOF
commit "$BEN" 2 "docs: record card fees in the changelog"

# ── 10 · version bump ────────────────────────────────────────────────────────
python3 - <<'EOF'
import pathlib
p = pathlib.Path("app/src/config.py")
p.write_text(p.read_text().replace('"APP_VERSION", "1.0.0"', '"APP_VERSION", "1.1.0"'))
EOF
commit "$CHEN" 1 "chore: bump version to 1.1.0"

echo "The gym is ready: $GYM"
echo
git log --oneline --decorate
