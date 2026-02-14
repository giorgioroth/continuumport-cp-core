# CP-Core Canonical Examples

This directory contains official reference examples of CP-Core capsules.

These are not templates.
They are normative demonstrations of correct usage.

---

## git-refactor-cli.json

**Domain:** CLI tool refactoring  
**Status:** Active (mid-task)

Demonstrates:
- Backward compatibility as constraint
- Architecture decisions captured explicitly
- Clear separation between requirements and implementation
- Declarative state reporting

Key lesson:
Constraints define boundaries.
Decisions define commitments.
State describes present capability.

---

## yjs-collaboration.json

**Domain:** Real-time collaborative system  
**Status:** Blocked

Demonstrates:
- Quantified performance constraints
- Explicit technical decisions (CRDT choice, transport, persistence)
- Honest reporting of partial failures
- Proper use of "blocked" progress state

Key lesson:
A capsule can represent incomplete work without collapsing direction.

---

## What makes these canonical?

A valid CP-Core capsule:

- Declares intent, not process.
- Uses constraints as negative space.
- Locks architecture in decisions.
- Reports state declaratively.
- Avoids timestamps, history, and narrative.

These examples are reference-grade.
