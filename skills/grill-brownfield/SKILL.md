---
name: grill-brownfield
description: Brownfield grilling session — challenges your plan against the existing
  codebase and domain model, sharpens terminology, and updates documentation
  (CONTEXT.md, ADRs) inline as decisions crystallise. Use to stress-test a plan against
  a project's language, code, and documented decisions. For greenfield work use
  grill-fast instead.
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

Treat the plan as the human's falsifiable hypothesis — it is theirs, not yours; do not produce your own. If no plan is offered, ask bare for the human's read (their understanding plus a rough design sketch) and wait — reveal nothing you found, no edge cases or judgment calls; hold them for the grill. Then grill to break it against the codebase and glossary (ground truth), never to confirm it.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Probe every constraint as a range, not a point

When the user states a validation or business rule, do not lock the literal value they named — interrogate the input space around it before writing it down. A rule stated as one point almost always has unstated neighbours.

For any "must (not) be X" rule, ask explicitly about:
- **Zero** — is `0` allowed? (empty string, empty list, `0.0`)
- **Negative / below-zero** — what about values on the wrong side? ("price must not be 0" rarely means negatives are fine.)
- **Upper bound / overflow** — is there a max? What happens past it?
- **Boundary itself** — inclusive or exclusive? Is the limit value allowed or rejected?

Example: user says "price should not be 0." Don't record `price == 0 → reject`. Ask: "So zero is rejected — what about a negative price? Is there a maximum?" Record the resolved *range* (e.g. "price must be strictly positive"), not the single point they happened to mention.

### Label discoveries

When something surfaces that wasn't in the original plan, tag it so it stays visible and
sorted: `[SCOPE]` (add now, needs a decision), `[FUTURE]` (defer, capture for later),
`[DISCUSS]` (open question, loop others in), `[RISK]` (hazard or ambiguity). Carry the
labels into the running notes so what's in, deferred, and unresolved is always explicit.

### Ask what the caller holds

For any API, key, or identifier about to become public, ask: what does the caller actually hold? If it's an internal representation (a derived id, an internal key) the caller doesn't naturally possess, surface it as a decision along with what it forecloses — don't settle it as elegant.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

### Handoff to the build (Gate + slices)

When the grill reaches shared understanding and the goal is to build (not just
comprehend), produce the same handoff `delivery-doctrine:grill-fast` does: lock the requirements and the
acceptance behaviors (the plan of what must be tested), present them as Gate 1, and on
approval invoke `delivery-doctrine:thin-slice-planner` for the ordered slice list (Gate 2). Honor the
existing architecture — slices conform to the house style, they don't impose a new one.
For comprehension-only sessions, stop at shared understanding; no slices needed.

</supporting-info>
