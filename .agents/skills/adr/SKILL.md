---
name: adr
description: >
  Use when proposing architectural changes, technological substitutions, database selections,
  or system trade-offs to generate formal Architecture Decision Records (ADRs).
---

# Architecture Decision Record (ADR) Skill

## When to Use

- Proposing a new framework, library, vector database, or persistence engine.
- Modifying architectural layer boundaries or communication protocols.
- Evaluating trade-offs between technical alternatives.
- Creating formal ADR documentation in `docs/adr/`.

## ADR Template Format

```markdown
# ADR [Number]: [Short Title]

## Date
[YYYY-MM-DD]

## Status
[Proposed | Accepted | Rejected | Superseded]

## Context & Problem Statement
[Describe the technical context, constraints, and specific problem requiring a decision.]

## Decision Drivers
- [Driver 1: Performance / Scalability / Latency]
- [Driver 2: Security & Compliance]
- [Driver 3: Developer Velocity & Maintainability]

## Considered Options
1. **Option 1** (Selected)
2. **Option 2** (Alternative)
3. **Option 3** (Alternative)

## Decision Outcome
Chosen option: **[Option 1]**, because [summary of key rationale].

### Positive Consequences
- [Benefit 1]
- [Benefit 2]

### Negative Consequences
- [Trade-off / Overhead 1]
- [Trade-off / Overhead 2]

## Pros and Cons of Options

### Option 1: [Selected Option]
- **Pros**: ...
- **Cons**: ...

### Option 2: [Alternative]
- **Pros**: ...
- **Cons**: ...
```

## Checklist

- [ ] ADR is saved to `docs/adr/NNNN-short-title.md`.
- [ ] Number is sequentially incremented from previous ADRs.
- [ ] Context clearly explains why a decision was necessary.
- [ ] At least 2 viable alternatives were evaluated.
- [ ] Explicit trade-offs and negative consequences are documented.
- [ ] Indexed in `docs/README.md`.

## References

- [docs/adr/](../../docs/adr/)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
