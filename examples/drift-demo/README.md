# Drift Demo (v1 — concept)

Measures directional drift across model runs with and without a CP-Core capsule.

## What this shows

- How constraints are violated without a capsule
- How direction is preserved with CP-Core

## How to run

```bash
# Without API key (uses mock models)
python run_drift_demo.py

# With real API
pip install requests
set ANTHROPIC_API_KEY=your_key   # Windows
export ANTHROPIC_API_KEY=your_key  # Linux/Mac
python run_drift_demo.py
```

## How drift is measured

```
drift_score = (violation_ratio × 0.7) + (decision_loss_ratio × 0.3)
```

- **violation_ratio** — constraints explicitly broken (hard signal)
- **decision_loss_ratio** — decisions not respected (soft signal)

## Limitations

- Keyword-based evaluation, not semantic equivalence
- A model can avoid flagged keywords while still drifting semantically
- Single run, no variance measurement

## Roadmap

| Version | What changes |
|---------|-------------|
| v1 (this) | Keyword evaluation, mock fallback, concept demo |
| v2 | Structured JSON output, semantic evaluation |
| v3 | Multiple runs, variance measurement, multi-model |

At v3, this stops being a demo and becomes evidence.
