# ContinuumPort CP-Core v1.0

**Minimal semantic state container for portable AI task continuity.**

CP-Core v1.0 is a lossy semantic compression format designed for **directional continuity**, not implementation replication. It provides a "safety cage" for AI work handoffs, ensuring that different models, sessions, or providers stay aligned with the project's trajectory while retaining implementation freedom.

---

## Design Philosophy: Portability > Fidelity

CP-Core operates on the principle that AI models are non-deterministic and diverse. Trying to force "Model B" to perfectly replicate the internal state of "Model A" leads to fragile, suboptimal code.

Instead, CP-Core preserves the **semantic boundary**:

* **Divergence in implementation** is expected and encouraged.
* **Convergence in direction** is mandatory.

---

## Quick Start

### Creating a capsule (mid-task):

1. State your **intent** (end goal, not current step)
2. List hard **constraints** (technical/business boundaries)
3. Document **decisions** already committed (architecture choices)
4. Describe **current state** declaratively (what exists now)
5. Set **progress** (active/blocked/completed)

### Receiving a capsule:

1. Read constraints → these are walls, don't cross them
2. Read decisions → these are anchors, build on them
3. Read state → this is your starting point
4. Implement toward intent using your best judgment within boundaries

**No prior context needed. The capsule is self-contained.**

---

## Schema v1.0

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
 "$id": "https://raw.githubusercontent.com/giorgioroth/continuumport-cp-core/main/schema/cp-core-v1.0.schema.json",
  "title": "ContinuumPort CP-Core v1.0",
  "description": "Lossy semantic compression for cross-model task continuity. Preserves intent/constraints/decisions, NOT implementation determinism.",
  "type": "object",
  "additionalProperties": false,
  "required": ["cp_version", "intent", "state_summary", "progress"],
  "properties": {
    "cp_version": {
      "type": "string",
      "const": "1.0",
      "description": "Fixed version identifier. Must be exactly '1.0'."
    },
    "intent": {
      "type": "string",
      "maxLength": 2000,
      "description": "The North Star. Declarative desired end-state. No process history."
    },
    "constraints": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 1000
      },
      "uniqueItems": true,
      "default": [],
      "description": "Negative space: what the AI MUST NOT do or change."
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 1000
      },
      "uniqueItems": true,
      "default": [],
      "description": "Committed choices: path-finding options already exhausted or fixed."
    },
    "state_summary": {
      "type": "string",
      "maxLength": 4000,
      "description": "Declarative snapshot of the present. No narrative or temporal language."
    },
    "progress": {
      "type": "string",
      "enum": ["active", "blocked", "completed"],
      "description": "Semantic work state. 'blocked' means continuation requires external input."
    }
  }
}
```

---

## Usage Principles

### I. Constraints are Negative Space

Constraints do not define the path; they define the walls. An AI model is free to choose any architecture, library, or pattern as long as it does not breach these boundaries.

**Example:**
```json
"constraints": [
  "Must not use external API dependencies",
  "Bundle size under 50kB gzipped",
  "Analysis must complete in under 2 minutes"
]
```

### II. Decisions are Anchors

Once a decision is committed to the capsule, it is no longer up for debate. Model B must build upon these choices even if it would have chosen differently at the start.

**Example:**
```json
"decisions": [
  "Using Yjs for CRDT (not Automerge)",
  "State-based sync (not delta-based)",
  "Binary update format (Uint8Array)"
]
```

### III. Absence is Permission

If a technical choice is not restricted by a `constraint` or locked by a `decision`, it is considered **implementation freedom**. Silence in the capsule is a signal for the receiving model to use its best judgment.

### IV. State is Declarative

Avoid narrative history ("We have fixed the bug"). Use declarative snapshots ("Bug fixed. Regression test passing."). CP-Core is about *where we are*, not *how we got here*.

---

## What CP-Core Preserves

✅ **Semantic direction** - Where we're going  
✅ **Hard boundaries** - What must not change  
✅ **Committed choices** - What's been decided  
✅ **Current state** - Where we are declaratively

## What CP-Core Does NOT Preserve

❌ **Implementation details** - Library choices, exact parameters  
❌ **Execution history** - How we got here  
❌ **Process metadata** - Who did what when  
❌ **Deterministic reproducibility** - Exact replication of steps

---

## Scope Boundaries

### ✅ What CP-Core is designed for:

* **Architecture & Refactoring:** System design evolution, technical debt resolution
* **Feature Development:** Multi-session feature work, cross-model collaboration
* **Strategic & Creative Work:** Research direction, content strategy, design iteration

### ❌ What CP-Core is NOT designed for:

* **Precision Debugging:** Race conditions, memory leaks, performance regressions
* **Deterministic Replay:** "Continue exactly where I left off" scenarios
* **Implementation Lock-in:** Forcing specific library versions or code structures

**Examples of tasks that should NOT use CP-Core:**

- "Debug why Redis connection pool exhausts under load"  
  → Need: logs, metrics, exact configuration
  
- "Continue this conversation exactly where we left off"  
  → Need: full conversation history, not semantic compression
  
- "Implement authentication using passport.js v0.6.0 with these exact middleware"  
  → Need: technical specification, not directional boundary

---

## Expected Behavior: The Divergence Test

**Scenario:** *Implement a Real-time Collaborative Editor*

* **Model A** creates a capsule after setting up the CRDT logic using Yjs and WebSockets
* **Model B** receives the capsule
* **Outcome:** Model B implements WebRTC for transport instead of WebSockets because the capsule constrained the protocol to be "transport-agnostic" but didn't lock the initial WebSocket choice
* **Verdict:** ✅ **SUCCESS**

The intent (Collaborative Editor) and key decision (CRDT approach) were preserved. The implementation adapted to Model B's expertise.

**What constitutes failure:**

❌ Model B ignores the CRDT decision and implements Operational Transform  
❌ Model B violates a stated constraint (e.g., "no external services")  
❌ Model B discards existing state and starts from scratch

**What constitutes success:**

✅ Model B completes the work using different libraries but same architecture  
✅ Model B refactors existing code while maintaining functionality  
✅ Model B adds features not specified in capsule (within boundaries)

---

## Version Policy

* **v1.0 is immutable.** This schema will never be patched or extended.
* **Evolution:** If structural gaps are discovered, a new version (v1.1 or v2.0) will be released as a separate schema.
* **Stability:** A v1.0 capsule will always be valid as v1.0.

### When to evolve to v1.1:

**Do NOT create v1.1 for:**
- Feature requests ("would be nice to have timestamps")
- Convenience additions ("add priority levels")
- Scope creep ("what about adding metadata?")

**DO create v1.1 if:**
- Real-world usage reveals **structural insufficiency**
- Critical information cannot be represented
- Safety properties are violated in practice

Monitor usage for 3-6 months before considering evolution.

---

## Examples

See the [`examples/`](examples/) directory for canonical reference capsules demonstrating proper CP-Core usage.

---

## Contributing

Contributions are welcome! Please:

1. Open an issue for discussion before major changes
2. Respect the minimalist philosophy - proposals to add fields will face high scrutiny
3. Provide real-world use cases demonstrating structural gaps (not convenience requests)

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Core Principle

**"The less you specify, the more you constrain."**

By eliminating implementation details, CP-Core forces the receiving model to focus on the geometry of the problem, not its history.

---

**ContinuumPort CP-Core v1.0**  
*Directional Continuity for the AI Era*

**Portability beats fidelity.**  
**Direction beats determinism.**  
**Boundaries beat specifications.**

