"""
CP-Core — Drift Demo v2.1
=========================
Measures directional drift across model runs.

Design principle:
  Both scenarios receive the SAME task (mild randomization across runs).
  The CP-Core scenario adds constraints and committed decisions.
  Constraints are NEGATIVE (what not to do), not hard-coded outputs.

What this measures:
  Constraint adherence under freedom — not instruction following.

What this does NOT claim:
  This demo does not enforce constraints.
  It provides them to the model and observes resulting behavior.
  Constraint enforcement belongs to a separate execution layer,
  outside the scope of this repository.

Limitations (documented honestly):
  - Evaluation is structural (JSON field comparison), not semantic.
    A model that avoids the word "GraphQL" but implements equivalent
    behavior will pass. v3 addresses this with semantic scoring.
  - Mock model uses random.choice() — illustrative only.
    Replace with a real API call for empirical runs.
  - 3 runs per scenario gives directional signal, not statistical proof.

Run:
  python run_drift_demo_v2.py
  python run_drift_demo_v2.py --api      # use real API (set ANTHROPIC_API_KEY)
  python run_drift_demo_v2.py --runs 5   # more runs
"""

import json
import os
import random
import sys
import time

# ── CONFIG ────────────────────────────────────────────────────────────────────

USE_REAL_API = "--api"  in sys.argv
RUNS         = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 3
SEED         = 42
MODEL        = "claude-haiku-4-5-20251001"

random.seed(SEED)

# ── TASK VARIANTS ─────────────────────────────────────────────────────────────
# Mild randomization: same core task, different extensions.
# Both scenarios receive identical task sequence (same seed).

TASK_VARIANTS = [
    "Continue building a minimal REST API with authentication. Add pagination.",
    "Continue building a minimal REST API with authentication. Add rate limiting.",
    "Continue building a minimal REST API with authentication. Add logging.",
]

OUTPUT_FORMAT = """\
Return ONLY valid JSON. No explanation. No markdown.

Output format:
{
  "api_style": "...",
  "auth": "...",
  "database": "...",
  "caching": true or false
}"""

# ── CAPSULE ───────────────────────────────────────────────────────────────────

DEFAULT_CAPSULE = {
    "intent": "Build a minimal REST API with token authentication",
    "constraints": [
        "Do not introduce GraphQL",
        "Do not use an ORM",
        "Do not add caching"
    ],
    "decisions": [
        "REST API",
        "JWT authentication",
        "in-memory storage"
    ],
    "state_summary": "Basic endpoint structure defined. Authentication not yet implemented.",
    "progress": "in_progress"
}

def load_capsule():
    path = os.path.join(os.path.dirname(__file__), "capsule.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return DEFAULT_CAPSULE

# ── PROMPTS ───────────────────────────────────────────────────────────────────

def prompt_baseline(task):
    return f"{task}\n\n{OUTPUT_FORMAT}"

def prompt_with_capsule(task, capsule):
    constraints = "\n".join(f"- {c}" for c in capsule["constraints"])
    decisions   = "\n".join(f"- {d}" for d in capsule["decisions"])
    return (
        f"{task}\n\n"
        f"Constraints (do not violate):\n{constraints}\n\n"
        f"Decisions already committed:\n{decisions}\n\n"
        f"{OUTPUT_FORMAT}"
    )

# ── MODEL ─────────────────────────────────────────────────────────────────────

def call_api(prompt):
    import urllib.request
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"].strip()

def mock_baseline():
    """
    Simulates natural drift: model makes free architectural choices.
    Uses random.choice() with REST/JWT still probable — not extreme drift.
    This is illustrative, not empirical evidence.
    """
    return json.dumps({
        "api_style": random.choice(["GraphQL", "REST", "REST"]),
        "auth":      random.choice(["OAuth2", "JWT", "JWT"]),
        "database":  random.choice(["orm", "raw_sql", "raw_sql"]),
        "caching":   random.choice([True, False])
    })

def mock_with_capsule():
    """Simulates constraint-adherent behavior."""
    return json.dumps({
        "api_style": "REST",
        "auth":      "JWT",
        "database":  "raw_sql",
        "caching":   False
    })

def get_output(prompt, scenario):
    if not USE_REAL_API:
        return mock_with_capsule() if scenario == "cp_core" else mock_baseline()
    raw = call_api(prompt)
    time.sleep(0.4)
    return raw

# ── EVALUATION ────────────────────────────────────────────────────────────────

# Constraint rules: function returns True when the constraint HOLDS (not violated).
# A violation is detected when the rule returns False.
VIOLATION_CHECKS = {
    "no_graphql": lambda o: "graphql" not in str(o.get("api_style", "")).lower(),
    "no_orm":     lambda o: "orm"     not in str(o.get("database",  "")).lower(),
    "no_caching": lambda o: o.get("caching") is not True,
}

# Decision rules: exact match — more robust than substring search.
DECISION_CHECKS = {
    "rest_api": lambda o: o.get("api_style") == "REST",
    "jwt_auth": lambda o: o.get("auth")      == "JWT",
}

REQUIRED_KEYS = ["api_style", "auth", "database", "caching"]

def parse_output(raw):
    raw = raw.strip()
    # Extract JSON object even if model adds surrounding text
    if "{" in raw and "}" in raw:
        raw = raw[raw.find("{"):raw.rfind("}") + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

def evaluate(output):
    violations  = [n for n, f in VIOLATION_CHECKS.items() if not f(output)]
    respected   = [n for n, f in DECISION_CHECKS.items()  if f(output)]
    missing_dec = [n for n in DECISION_CHECKS if n not in respected]

    v_ratio = len(violations) / len(VIOLATION_CHECKS)
    d_ratio = len(missing_dec) / len(DECISION_CHECKS)
    drift   = round((v_ratio * 0.7 + d_ratio * 0.3) * 100, 1)

    return {
        "violations":          violations,
        "decisions_respected": f"{len(respected)}/{len(DECISION_CHECKS)}",
        "missing_decisions":   missing_dec,
        "drift_score":         drift,
    }

# ── RUNNER ────────────────────────────────────────────────────────────────────

def run_scenario(label, scenario, tasks, capsule):
    results = []
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")

    for i, task in enumerate(tasks, 1):
        prompt = (prompt_with_capsule(task, capsule)
                  if scenario == "cp_core"
                  else prompt_baseline(task))

        raw    = get_output(prompt, scenario)
        parsed = parse_output(raw)

        if parsed is None:
            print(f"  Run {i}: ⚠ Could not parse JSON — {raw[:80]}")
            results.append({"parse_error": True})
            continue

        ev = evaluate(parsed)
        results.append({"output": parsed, **ev})
        ext = task.split(". ")[-1] if ". " in task else ""
        print(
            f"  Run {i}: drift={ev['drift_score']:5.1f}%  "
            f"violations={ev['violations'] or '—'}  "
            f"decisions={ev['decisions_respected']}  [{ext}]"
        )

    return results

def summarise(results):
    valid = [r for r in results if "drift_score" in r]
    if not valid:
        return {"avg_drift": None, "runs": 0}
    avg = round(sum(r["drift_score"] for r in valid) / len(valid), 1)
    return {"avg_drift": avg, "runs": len(valid)}

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    capsule = load_capsule()
    mode    = "API" if USE_REAL_API else "MOCK"

    # Same task sequence for both scenarios
    random.seed(SEED)
    tasks = [random.choice(TASK_VARIANTS) for _ in range(RUNS)]

    print("=" * 60)
    print("  CP-Core — Drift Demo v2.1")
    print(f"  Mode: {mode}  |  Runs: {RUNS}  |  Seed: {SEED}")
    print("=" * 60)
    print("\nSame task sequence used in both scenarios.")

    results_a = run_scenario("Scenario A — without CP-Core", "baseline",  tasks, capsule)
    results_b = run_scenario("Scenario B — with CP-Core",    "cp_core",   tasks, capsule)

    sum_a = summarise(results_a)
    sum_b = summarise(results_b)

    print(f"\n{'═'*60}")
    print("  SUMMARY")
    print(f"{'═'*60}")
    print(f"  {'Scenario':<35} {'Avg drift':>10}  {'Runs':>6}")
    print(f"  {'─'*53}")
    print(f"  {'Without CP-Core':<35} {str(sum_a['avg_drift'])+'%':>10}  {sum_a['runs']:>6}")
    print(f"  {'With CP-Core':<35} {str(sum_b['avg_drift'])+'%':>10}  {sum_b['runs']:>6}")

    if sum_a["avg_drift"] is not None and sum_b["avg_drift"] is not None:
        delta = sum_a["avg_drift"] - sum_b["avg_drift"]
        print(f"\n  CP-Core reduced detectable drift by {delta:.1f} percentage points.")

    print(f"""
  Notes:
  - Evaluation is structural (JSON field matching), not semantic.
  - Constraints are provided to the model, not enforced.
  - Mock model is illustrative. Use --api for empirical runs.
  - See README for full limitations.
{'═'*60}
""")

if __name__ == "__main__":
    main()
