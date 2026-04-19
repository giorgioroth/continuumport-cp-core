"""
CP-Core Drift Demo — v1 (concept)
Measures semantic drift with and without a CP-Core capsule.

Usage:
    pip install requests
    set ANTHROPIC_API_KEY=your_key
    python run_drift_demo.py

Note: This is a concept demo (v1).
      Evaluation is keyword-based, not semantic.
      v2 will introduce structured output and real NLP evaluation.
"""

import os
import json
import sys
from typing import Dict, List

# ─── CONFIG ───────────────────────────────────────────────────────────────────

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"
USE_REAL_API = bool(API_KEY)

# ─── CAPSULE ──────────────────────────────────────────────────────────────────

with open(os.path.join(os.path.dirname(__file__), "capsule.json")) as f:
    CAPSULE = json.load(f)

# ─── TASK ─────────────────────────────────────────────────────────────────────

TASK = "Continue building a minimal REST API with authentication."

# ─── PROMPTS ──────────────────────────────────────────────────────────────────

def prompt_without_capsule() -> str:
    return TASK

def prompt_with_capsule() -> str:
    return (
        f"You are continuing a task.\n\n"
        f"CP-Core capsule:\n{json.dumps(CAPSULE, indent=2)}\n\n"
        f"Follow the capsule strictly. Respect all constraints and decisions.\n\n"
        f"Task: {TASK}"
    )

# ─── MOCK MODELS (fallback when no API key) ───────────────────────────────────

def mock_without_capsule(_prompt: str) -> str:
    return (
        "Let's build a modern API using GraphQL for flexibility. "
        "We'll use SQLAlchemy ORM for database abstraction, "
        "add Redis caching for performance, "
        "and implement OAuth2 for authentication."
    )

def mock_with_capsule(_prompt: str) -> str:
    return (
        "Continuing the REST API with token-based authentication. "
        "No ORM used — raw SQL queries only. "
        "In-memory store for simplicity. "
        "No caching layer added. "
        "JWT tokens for auth endpoints."
    )

# ─── API CALL ─────────────────────────────────────────────────────────────────

def call_api(prompt: str, with_capsule: bool) -> str:
    if not USE_REAL_API:
        return mock_with_capsule(prompt) if with_capsule else mock_without_capsule(prompt)

    try:
        import requests
    except ImportError:
        print("ERROR: pip install requests")
        sys.exit(1)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]

# ─── EVALUATION ───────────────────────────────────────────────────────────────

# Keywords that signal constraint violations
VIOLATION_SIGNALS = {
    "no_graphql":   ["graphql", "resolver", "query language"],
    "no_orm":       ["sqlalchemy", "orm", "django orm", "peewee", "sequelize"],
    "no_cache":     ["redis", "memcached", "caching layer"],
}

# Keywords that signal decisions were respected
DECISION_SIGNALS = {
    "rest":         ["rest", "endpoint", "route", "http"],
    "token_auth":   ["token", "jwt", "bearer"],
    "in_memory":    ["in-memory", "in memory", "dict", "memory store"],
}

def evaluate(output: str) -> Dict:
    if not output.strip():
        return {
            "violations": ["empty_output"],
            "respected": [],
            "decisions_respected": "0/0",
            "missing_decisions": len(DECISION_SIGNALS),
            "total_decisions": len(DECISION_SIGNALS),
            "drift_score": 100.0
        }

    import re
    text = re.sub(r"\s+", " ", output.lower())

    violations = []
    for label, keywords in VIOLATION_SIGNALS.items():
        for k in keywords:
            # avoid false positives from negations like "no orm", "without orm"
            pattern = rf'(?<!no )(?<!not )(?<!without )\b{re.escape(k)}\b'
            if re.search(pattern, text):
                violations.append(label)
                break

    respected = []
    for label, keywords in DECISION_SIGNALS.items():
        if any(k in text for k in keywords):
            respected.append(label)

    total_constraints = len(VIOLATION_SIGNALS)
    total_decisions = len(DECISION_SIGNALS)
    missing_decisions = total_decisions - len(respected)

    violation_ratio = len(violations) / (total_constraints or 1)
    decision_loss_ratio = missing_decisions / (total_decisions or 1)

    # Hard violations weighted 70%, missing decisions weighted 30%
    drift_score = round((violation_ratio * 0.7 + decision_loss_ratio * 0.3) * 100, 1)

    return {
        "violations": violations,
        "respected": respected,
        "decisions_respected": f"{len(respected)}/{total_decisions}",
        "missing_decisions": missing_decisions,
        "total_decisions": total_decisions,
        "drift_score": drift_score
    }

# ─── DISPLAY ──────────────────────────────────────────────────────────────────

def print_scenario(label: str, output: str, metrics: Dict):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(f"\nOutput (truncated):\n{output[:400]}")
    print(f"\nMetrics:")
    print(f"  Decisions respected : {metrics['decisions_respected']}")
    print(f"  Decision loss       : {metrics['missing_decisions']}/{metrics['total_decisions']}")
    print(f"  Constraint violations: {len(metrics['violations'])}")
    if metrics["violations"]:
        for v in metrics["violations"]:
            print(f"    ✗ {v}")
    print(f"  Drift score         : {metrics['drift_score']}%")
    print(f"  Note: measures detectable drift, not semantic equivalence.")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  CP-CORE — DRIFT MEASUREMENT DEMO  (v1 concept)")
    print("=" * 60)
    print(f"\nTask: {TASK}")
    print(f"Mode: {'Real API' if USE_REAL_API else 'Mock (set ANTHROPIC_API_KEY for real)'}")

    # Scenario A
    output_a = call_api(prompt_without_capsule(), with_capsule=False)
    metrics_a = evaluate(output_a)
    print_scenario("WITHOUT CP-CORE", output_a, metrics_a)

    # Scenario B
    output_b = call_api(prompt_with_capsule(), with_capsule=True)
    metrics_b = evaluate(output_b)
    print_scenario("WITH CP-CORE", output_b, metrics_b)

    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n  Without CP-Core  →  drift: {metrics_a['drift_score']}%")
    print(f"  With CP-Core     →  drift: {metrics_b['drift_score']}%")

    reduction = metrics_a["drift_score"] - metrics_b["drift_score"]
    if reduction > 0:
        print(f"\n  ✓ CP-Core reduced detectable drift by {reduction:.1f} percentage points.")
    elif reduction == 0:
        print(f"\n  — No measurable difference in this run.")
    else:
        print(f"\n  ✗ Unexpected result. Check output manually.")

    print(f"\n  Note: v1 uses keyword-based evaluation.")
    print(f"        v2 will use structured JSON output for precision.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
