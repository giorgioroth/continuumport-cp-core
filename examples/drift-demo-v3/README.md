# Drift Demo — v3

Estimates directional drift under constrained vs unconstrained conditions,
with mean, standard deviation, and optional CSV export.

> ⚠️ For the concept version (v1) see [../drift-demo/](https://github.com/giorgioroth/continuumport-cp-core/tree/main/examples/drift-demo)  
> ⚠️ For the structured version (v2.1) see [../drift-demo-v2/](https://github.com/giorgioroth/continuumport-cp-core/tree/main/examples/drift-demo-v2)

## What this demonstrates

Two scenarios. Same task sequence. Same seed. Same output format.

**Scenario A** — baseline: the model chooses its own architecture freely.  
**Scenario B** — with CP-Core: constraints and committed decisions are provided.

Constraints are **negative** (what not to do), not hard-coded answers.  
The model is free to choose any solution within the constrained space.

## What this measures

> In this setup, constraints reduce both drift AND variance — not just correctness.

Mean drift shows where the model tends to go.  
Standard deviation shows how stable that tendency is.

## What this does NOT claim

This demo does not enforce constraints.  
It provides them to the model and observes resulting behavior.

Constraint enforcement belongs to a separate execution layer,  
outside the scope of this repository.

## Drift score formula

```
drift_score = (violation_ratio × 0.7) + (decision_loss_ratio × 0.3)
```

- **violation_ratio** — fraction of constraint rules violated  
- **decision_loss_ratio** — fraction of committed decisions ignored  
- Weighted 70/30: violations are harder failures than ignored decisions

## Usage

**Mock mode (offline, no API key):**
```bash
python run_drift_demo_v3.py
python run_drift_demo_v3.py --runs 10
```

**With Anthropic API (empirical runs):**
```bash
export ANTHROPIC_API_KEY=your_key_here
python run_drift_demo_v3.py --api --runs 20
python run_drift_demo_v3.py --api --runs 20 --csv
```

Python 3.10+ required. No external dependencies.

## Limitations (documented honestly)

- Evaluation is structural (JSON field matching), not semantic.  
  A model that avoids the word "GraphQL" but implements equivalent  
  behavior will pass this test.
- Mock model uses `random.choice()` — illustrative only.  
  Use `--api` for empirical results.
- Statistical significance requires N ≥ 20.  
  Default N=5 gives directional signal. Use `--runs 20` for stronger claims.
- Observed variance reduction is model-dependent.  
  Results should be validated with real API runs.

## Files

```
drift-demo-v3/
├── run_drift_demo_v3.py   # demo script
├── capsule.json           # CP-Core capsule (same as v2.1)
└── README.md              # this file
```

## Relation to CP-Core

CP-Core defines what must hold.  
This demo observes the effect of stating that.  
It does not verify or enforce it.
