# Drift Demo (v1 — concept)

Illustrates directional drift across model runs with and without a CP-Core capsule.

## What this shows

- How constraints are violated without a capsule
- How direction is preserved with CP-Core

This demo illustrates the failure mode.  
It does not constitute empirical measurement.

---

## How to run

```bash
# Without API key (uses mock models)
python run_drift_demo.py

# With real API
pip install requests
set ANTHROPIC_API_KEY=your_key   # Windows
export ANTHROPIC_API_KEY=your_key  # Linux/Mac
python run_drift_demo.py
````

---

## How drift is estimated (v1)

```
drift_score = (violation_ratio × 0.7) + (decision_loss_ratio × 0.3)
```

* **violation_ratio** — constraints explicitly broken (hard signal)
* **decision_loss_ratio** — decisions not respected (soft signal)

---

## Limitations

* Keyword-based evaluation, not semantic equivalence
* Model outputs in mock mode are illustrative, not independent
* A model can avoid flagged keywords while still drifting semantically
* Single run, no variance measurement

---

## Interpretation

Without CP-Core:
execution continues — direction may drift

With CP-Core:
execution continues — direction is constrained

---

## Roadmap

| Version   | Focus                                               |
| --------- | --------------------------------------------------- |
| v1 (this) | Concept illustration, keyword-based evaluation      |
| v2        | Structured output, semantic validation              |
| v3        | Multi-run evaluation, statistical drift measurement |

**At v3, this transitions from illustration to evidence.**



