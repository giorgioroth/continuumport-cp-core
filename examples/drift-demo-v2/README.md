# Drift Demo — v2.1

> ⚠️ This is the improved experimental version of the drift demo.
> For the original concept version, see [../drift-demo/](https://github.com/giorgioroth/continuumport-cp-core/tree/main/examples/drift-demo)

Estimates directional drift under constrained vs unconstrained conditions using structured JSON evaluation.

## What this demonstrates

Two scenarios. Same task sequence. Same output format. Same seed.

**Scenario A** — baseline: the model chooses its own architecture freely.  
**Scenario B** — with CP-Core: constraints and committed decisions are provided.

Constraints are **negative** (what not to do), not hard-coded answers.
The model is free to choose any solution within the constrained space.  

## What this measures

> Constraint adherence under freedom — not instruction following.

Task variants are randomized mildly (pagination / rate limiting / logging)  
to make baseline drift more natural. Both scenarios receive identical task sequences.

## What this does NOT claim

This demo does not enforce constraints.  
It provides them to the model and observes the resulting behavior.

Constraint enforcement is a separate concern and belongs to a dedicated  
execution layer outside the scope of this repository.

## Drift score formula

```
drift_score = (violation_ratio × 0.7) + (decision_loss_ratio × 0.3)
```

- **violation_ratio** — fraction of constraints violated  
- **decision_loss_ratio** — fraction of committed decisions ignored  
- Weighted 70/30: violations are harder failures than ignored decisions

## Usage

**Mock mode (offline, no API key needed):**
```bash
python run_drift_demo_v2.py
python run_drift_demo_v2.py --runs 5
```

**With Anthropic API (empirical runs):**
```bash
export ANTHROPIC_API_KEY=your_key_here
python run_drift_demo_v2.py --api
python run_drift_demo_v2.py --api --runs 10
```

Python 3.10+ required. No external dependencies.

## Limitations (documented honestly)

- Evaluation is structural (JSON field matching), not semantic.  
  A model that avoids the word "GraphQL" but implements equivalent  
  behavior will pass this test.
- Mock model uses `random.choice()` — illustrative only.  
  Use `--api` for empirical results.
- 3 runs gives directional signal, not statistical proof.  
  Use `--runs 10` or higher for more confidence.

v3 will address semantic scoring and variance measurement.

## Files

```
drift-demo/
├── run_drift_demo_v2.py   # demo script
├── capsule.json           # CP-Core capsule used in Scenario B
└── README.md              # this file
```

## Relation to CP-Core

CP-Core defines what must hold.  
This demo observes the effect of stating that.  
It does not verify or enforce it.
