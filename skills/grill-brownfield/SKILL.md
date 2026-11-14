---
name: grill-brownfield
description: Brownfield grilling session — challenges your plan against the existing
  codebase and domain model, sharpens terminology, and updates documentation
  (CONTEXT.md, ADRs) inline as decisions crystallise. Use to stress-test a plan against
  a project's language, code, and documented decisions. For greenfield work use
  grill-fast instead.
---

<!-- Adapted from mattpocock/skills (MIT); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

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

Most repos have one context: a `CONTEXT.md` glossary at the root and decisions in
`docs/adr/` (`0001-event-sourced-orders.md`). A root `CONTEXT-MAP.md` means several contexts:
it points to each one's home (`src/ordering/`, `src/billing/`), each with its own glossary and
`docs/adr/` for context-specific decisions; the root `docs/adr/` keeps system-wide ones.

### Context files

Each bounded context has one context file at its package root, in the shape in [CONTEXT-FILE.md](./CONTEXT-FILE.md). It is that context's glossary home: its Domain terms section replaces CONTEXT.md, and a CONTEXT-MAP.md entry may point at it. For every bounded context the plan touches:
- **Missing:** draft it from the code and this grill, with the feature's line (in delivery), and create it with the Gate 1 documents.
- **Present but not in shape:** show the gaps and propose the correction, including the feature's line (in delivery); change it only on the user's explicit yes, since other teams may own it.
- **Several files for one context** (nested in subpackages, or spread across folders): one context file at the context's root owns terms, invariants and boundaries; a nested file keeps only mechanics local to its folder (commands, traps) and needs no pointer; a satellite folder outside the package gets at most a one-line pointer to the context file. Propose the consolidation as its own docs PR, applied only on the user's yes. Before moving any text, search the repository for hooks, tests or scripts that read those files. If the duplication comes from the context being drawn wrong, raise that as a modelling finding (an ADR candidate); merging files does not fix it.
- **Present and in shape:** leave it. Terms resolved here go into the spec's design.md; close-out folds them in, and the feature appears there once it is live. Close-out is the only step that edits an existing context file without asking.

Create files lazily — only when you have something to write. A repository that already keeps its glossary in `CONTEXT.md` files keeps using them (the repository profile can say so); everywhere else the context file is the glossary. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in the glossary (`CONTEXT.md` or the context file's Domain terms), call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

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

### Update the glossary inline

When a term is resolved, update the glossary right there: `CONTEXT.md`, or a context file created in this session (an existing context file waits for close-out; record the term in design.md). Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

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
approval invoke `delivery-doctrine:thin-slice-planner` for the wave plan (Gate 2). Honor the
existing architecture — slices conform to the house style, they don't impose a new one.
For comprehension-only sessions, stop at shared understanding; no slices needed.

</supporting-info>
