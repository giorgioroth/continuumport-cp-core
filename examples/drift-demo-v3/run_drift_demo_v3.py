"""
CP-Core — Drift Demo v3
=======================
Estimates directional drift under constrained vs unconstrained conditions.

What's new in v3:
  - Mean drift + standard deviation per scenario
  - Comparative table with stability metric
  - Optional CSV export (--csv)
  - Upgraded from "directional signal" to "statistical observation"

Design principle:
  Both scenarios receive the SAME task sequence (same seed).
  Constraints are NEGATIVE (what not to do), not hard-coded outputs.
  The model is free to choose any solution within the constrained space.

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
    behavior will pass. This is acknowledged, not hidden.
  - Mock model uses random.choice() — illustrative only.
    Use --api for empirical runs.
  - Statistical significance requires N >= 20. Default N=5 gives
    directional signal with variance. Use --runs 20 for stronger claims.
  - Observed variance reduction is model-dependent.
    Results should be validated with real API runs.

Run:
  python run_drift_demo_v3.py
  python run_drift_demo_v3.py --runs 10
  python run_drift_demo_v3.py --api --runs 10
  python run_drift_demo_v3.py --api --runs 20 --csv
"""

import csv
import json
import math
import os
import random
import sys
import time

# ── CONFIG ────────────────────────────────────────────────────────────────────

USE_REAL_API = "--api"  in sys.argv
EXPORT_CSV   = "--csv"  in sys.argv
RUNS         = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 5
SEED         = 42
MODEL        = "claude-haiku-4-5-20251001"

# ── TASK VARIANTS ─────────────────────────────────────────────────────────────

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
    Simulates natural drift: free architectural choices.
    REST/JWT still probable — not extreme, not sabotaged.
    Illustrative only.
    """
    return json.dumps({
        "api_style": random.choice(["GraphQL", "REST", "REST"]),
        "auth":      random.choice(["OAuth2", "JWT", "JWT"]),
        "database":  random.choice(["orm", "raw_sql", "raw_sql"]),
        "caching":   random.choice([True, False])
    })

def mock_with_capsule():
    """
    Simulates constraint-adherent behavior.
    Minor variation in database field to avoid σ=0 (unrealistically perfect).
    """
    return json.dumps({
        "api_style": "REST",
        "auth":      "JWT",
        "database":  random.choice(["raw_sql", "raw_sql", "in-memory"]),
        "caching":   False
    })

def get_output(prompt, scenario):
    if not USE_REAL_API:
        return mock_with_capsule() if scenario == "cp_core" else mock_baseline()
    raw = call_api(prompt)
    time.sleep(0.4)
    return raw

# ── EVALUATION ────────────────────────────────────────────────────────────────

# Constraint rules: returns True when constraint HOLDS (not violated).
# A violation is detected when the rule returns False.
CONSTRAINT_RULES = {
    "no_graphql": lambda o: str(o.get("api_style", "")).lower() not in ["graphql", "gql"],
    "no_orm":     lambda o: (
        "orm"        not in str(o.get("database", "")).lower() and
        "sqlalchemy" not in str(o.get("database", "")).lower()
    ),
    "no_caching": lambda o: str(o.get("caching", "")).lower() != "true",
}

# Decision rules: exact match — more robust than substring search.
DECISION_CHECKS = {
    "rest_api": lambda o: o.get("api_style") == "REST",
    "jwt_auth": lambda o: o.get("auth")      == "JWT",
}

def parse_output(raw):
    raw = raw.strip()
    if "{" in raw and "}" in raw:
        raw = raw[raw.find("{"):raw.rfind("}") + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

def evaluate(output):
    violations  = [n for n, f in CONSTRAINT_RULES.items() if not f(output)]
    respected   = [n for n, f in DECISION_CHECKS.items()  if f(output)]
    missing_dec = [n for n in DECISION_CHECKS if n not in respected]

    v_ratio = len(violations) / len(CONSTRAINT_RULES)
    d_ratio = len(missing_dec) / len(DECISION_CHECKS)
    drift   = round((v_ratio * 0.7 + d_ratio * 0.3) * 100, 1)

    return {
        "violations":          violations,
        "decisions_respected": f"{len(respected)}/{len(DECISION_CHECKS)}",
        "missing_decisions":   missing_dec,
        "drift_score":         drift,
    }

# ── STATISTICS ────────────────────────────────────────────────────────────────

def mean(values):
    return sum(values) / len(values) if values else 0.0

def std_dev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

# ── RUNNER ────────────────────────────────────────────────────────────────────

def run_scenario(label, scenario, tasks, capsule):
    results = []
    print(f"\n{'─'*65}")
    print(f"  {label}")
    print(f"{'─'*65}")

    for i, task in enumerate(tasks, 1):
        prompt = (prompt_with_capsule(task, capsule)
                  if scenario == "cp_core"
                  else prompt_baseline(task))

        raw    = get_output(prompt, scenario)
        parsed = parse_output(raw)

        if parsed is None:
            print(f"  Run {i:>2}: ⚠ Could not parse JSON — {raw[:60]}")
            results.append({"parse_error": True})
            continue

        ev = evaluate(parsed)
        results.append({"output": parsed, **ev})
        ext = task.split(". ")[-1] if ". " in task else ""
        print(
            f"  Run {i:>2}: drift={ev['drift_score']:5.1f}%  "
            f"violations={str(ev['violations'] or '—'):<35}  "
            f"[{ext}]"
        )

    return results

# ── SUMMARY ───────────────────────────────────────────────────────────────────

def summarise(results):
    valid = [r for r in results if "drift_score" in r]
    if not valid:
        return {"mean": None, "std_dev": None, "runs": 0, "parse_errors": len(results)}
    drifts = [r["drift_score"] for r in valid]
    return {
        "mean":         round(mean(drifts), 2),
        "std_dev":      round(std_dev(drifts), 2),
        "runs":         len(valid),
        "parse_errors": len(results) - len(valid),
        "drifts":       drifts,
    }

# ── CSV EXPORT ────────────────────────────────────────────────────────────────

def export_csv(results_a, results_b, filename="drift_results.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "run", "drift_score"])
        for i, r in enumerate(results_a):
            if "drift_score" in r:
                writer.writerow(["baseline", i + 1, r["drift_score"]])
        for i, r in enumerate(results_b):
            if "drift_score" in r:
                writer.writerow(["cp_core", i + 1, r["drift_score"]])
    print(f"  CSV exported → {filename}")

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    capsule = load_capsule()
    mode    = "API" if USE_REAL_API else "MOCK"

    random.seed(SEED)
    tasks = [random.choice(TASK_VARIANTS) for _ in range(RUNS)]

    print("=" * 65)
    print("  CP-Core — Drift Demo v3")
    print(f"  Mode: {mode}  |  Runs: {RUNS}  |  Seed: {SEED}")
    print(f"  Model: {MODEL}")
    print("=" * 65)
    print("\nSame task sequence used in both scenarios.")

    results_a = run_scenario("Scenario A — without CP-Core", "baseline", tasks, capsule)
    results_b = run_scenario("Scenario B — with CP-Core",    "cp_core",  tasks, capsule)

    sum_a = summarise(results_a)
    sum_b = summarise(results_b)

    def fmt(v): return f"{v}%" if v is not None else "—"

    print(f"\n{'═'*65}")
    print("  SUMMARY")
    print(f"{'═'*65}")
    print(f"  {'Scenario':<25} {'Mean drift':>12} {'Std dev':>10} {'Runs':>6}")
    print(f"  {'─'*55}")
    print(f"  {'Without CP-Core':<25} {fmt(sum_a['mean']):>12} {fmt(sum_a['std_dev']):>10} {sum_a['runs']:>6}")
    print(f"  {'With CP-Core':<25} {fmt(sum_b['mean']):>12} {fmt(sum_b['std_dev']):>10} {sum_b['runs']:>6}")

    if sum_a["mean"] is not None and sum_b["mean"] is not None:
        delta = sum_a["mean"] - sum_b["mean"]
        print(f"\n  Drift reduction:  {delta:.2f} percentage points")
        print(f"  Variance (σ):     {sum_a['std_dev']}% → {sum_b['std_dev']}%")

    print(f"""
  Notes:
  - Evaluation is structural (JSON field matching), not semantic.
  - Constraints are provided to the model, not enforced.
  - Mock model is illustrative. Use --api for empirical runs.
  - N < 20 gives directional signal, not statistical significance.
  - Observed variance reduction is model-dependent.
    Results should be validated with real API runs.
{'═'*65}
""")

    if EXPORT_CSV:
        export_csv(results_a, results_b)

if __name__ == "__main__":
    main()
