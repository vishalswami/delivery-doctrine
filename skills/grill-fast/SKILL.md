---
name: grill-fast
description: Use for a greenfield, timeboxed requirements grill. Locks requirements
  and acceptance tests fast through batched questions (no codebase or glossary
  cross-reference), then hands off to thin-slice-planner. For brownfield
  exploration use grill-brownfield instead.
---

# Grill (fast / greenfield)

A fast requirements grill for greenfield, timeboxed work. Lock the requirements
and acceptance tests, then hand off to `delivery-doctrine:thin-slice-planner`. For brownfield work
with an existing codebase and glossary, use `delivery-doctrine:grill-brownfield` instead.

## How it differs from grill-brownfield
- No codebase exploration, no glossary-conflict challenge, no code cross-reference
  (there's no code yet).
- Questions are batched into one grouped pass, each with a recommended answer,
  instead of one-at-a-time.
- No CONTEXT.md / ADR ceremony. Keep a lightweight decision log inline. Optional:
  a 3-5 term mini-glossary only if terms actually collide; an ADR only after the
  fact for a genuinely hard-to-reverse call.

## Start from the human's hypothesis (step 0)
The hypothesis is the HUMAN's, not yours. Do NOT produce your own read or design sketch.
Your first move is a BARE ask, then stop: "What's your read of the problem, and your
rough design sketch — the few objects and the shape you expect?" Nothing else. Wait.
Reveal NOTHING you found: no edge cases, no ambiguities, no judgment calls, no examples
that hint at the answer or the traps. Even if you've spotted issues in the data, hold ALL
of it — listing them anchors the human and defeats the point, which is to see their
unaided read, including what they miss. Their answer can be 100% wrong; that's fine.
Only after they've answered do you grill: bring what you found then, testing THEIR
hypothesis to break it against the problem statement (ground truth), never to confirm it.
Keep their sketch to ~60 seconds — the point is their commitment and design ownership.

## The grill
Interrogate the human's hypothesis against the problem statement:
1. **Batch the requirements questions.** One grouped set covering scope,
   inputs/outputs, core behaviors, error and edge cases, and explicit non-goals.
   Give a recommended answer for each. This is the only place questions group.
   For every "must (not) be X" rule, probe the whole range, not the single point
   named: is zero allowed, are negatives, is there an upper bound, is the boundary
   inclusive? "Price must not be 0" rarely means negatives are fine — record the
   resolved range (e.g. "strictly positive"), not the literal value mentioned.
2. **Sharpen the language.** When a term is vague or overloaded, propose a precise
   canonical name and use it consistently. Capture collisions in a short glossary
   only if they actually cause confusion.
3. **Establish the domain shape.** Name the bounded context(s), the core domain
   model (value objects, domain services), and the port boundaries the problem
   actually has. Right-size: reach for a port only when crossing out of the
   domain. This shape is what makes vertical slicing possible.
4. **List the acceptance behaviors (the plan).** Name the behavioral flows, positive
   and negative, that must hold for the whole service — what tests should exist, not
   the test code. The planner groups the behaviors into slices (a slice owns one or
   more); the actual test for each is written test-first in its slice, and they
   accumulate into the suite.

## Lock the public contract with the caller in mind
For any API, key, or identifier about to become public, ask: **what does the caller
actually hold?** If the value is an internal representation (a derived id, an internal
key) the caller doesn't naturally possess, surface it as a gate decision along with what
it forecloses — never settle it as elegant.

## Label discoveries
When something surfaces mid-grill that wasn't in the original ask, tag it so it's
visible and sorted (and easy to raise with others in the room):
- `[SCOPE]` — add to this build; needs a decision at Gate 1.
- `[FUTURE]` — out of scope now, captured for later.
- `[DISCUSS]` — open question; loop in the human or others.
- `[RISK]` — hazard or ambiguity to resolve.
Carry the labels into the requirements summary so Gate 1 shows exactly what's in, what's
deferred, and what's unresolved.

## Gate 1 — requirements agreed
Stop. Present the locked requirements, the canonical terms, the domain shape, and
the acceptance tests. Wait for explicit approval. Batching the questions never
removes this gate.

## Handoff
On approval, a new bounded context gets its context file, written with the Gate 1
documents at the package path the design names (the walking skeleton builds the package
there): the canonical terms and domain shape just agreed, and the feature's line (in
delivery). Shape: `delivery-doctrine:grill-brownfield`'s CONTEXT-FILE.md. Then invoke `delivery-doctrine:thin-slice-planner` with the requirements + acceptance tests
to produce the walking-skeleton-first wave plan. Gate 2 (wave plan
agreed before any code) belongs to the planner.

## Reuse
- Spirit, precision, recommend-an-answer: `delivery-doctrine:grill-brownfield`.
- Slice decomposition and ordering: `delivery-doctrine:thin-slice-planner`.
- Loop and review after slicing: `delivery-doctrine:superpowers-seam`.
