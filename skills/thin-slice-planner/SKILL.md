---
name: thin-slice-planner
description: Use after requirements are locked to turn a spec and acceptance tests
  into an ordered list of thin vertical slices, walking-skeleton-first. Owns the
  slice-list gate before any code. Pairs with grill-fast (input) and the per-slice
  loop (output).
---

# Thin-Slice Planner

Turn locked requirements + acceptance tests into an ordered list of thin vertical
slices. Each slice is one end-to-end behavior, walking-skeleton-first. This skill
owns gate 2: the slice list is agreed before any code is written.

Input usually comes from `delivery-doctrine:grill-fast` (requirements, canonical terms, domain
shape, acceptance behaviors — the plan). It works from any spec with the same pieces.

## What a slice is
One thin end-to-end vertical through every layer it needs — in-adapter, port,
domain, out-adapter. A single vertical usually has several acceptance behaviors (a
happy path plus its negative and edge flows); the slice owns all of them, and its
done-criterion is all its acceptance tests green. Never a horizontal layer
("build all repositories" is not a slice).

## Process
1. **Slice 0 = walking skeleton.** The thinnest end-to-end path wired and passing
   before any feature: one request in, through all layers, one response out,
   proving the wiring. Not a feature.
2. **Group behaviors into slices.** A slice is one thin vertical and usually owns
   several related acceptance behaviors (happy path plus its negative and edge flows).
   Group the grill's behaviors by the vertical they exercise; each behavior's test is
   written test-first during the slice. Order slices by dependency first, then value.
3. **Just-in-time within each slice.** A slice touches all the layers it needs and
   builds only what it needs. No speculative ports, repositories, or entities;
   note what is deliberately stubbed this slice and built later.
4. **Name the MVP vertical.** The 3-4 slices that prove the core domain end to end.
   A coherent finished vertical beats a sprawling half-done app.
5. **Name the deferrals.** State what is out of scope for now and where it slots in
   later. Deferrals are a product-driven signal, not an omission.
6. **State conventions once.** Error handling and validation approach up front,
   implemented JIT per slice.

## Output format
```markdown
### Slice 0 — walking skeleton
- Cue: <one-glance end-to-end sketch, e.g. `GET /health → controller → domain → 200`>
- Proves: end-to-end wiring (request in, all layers, response out)
- Touches: in-adapter, port, domain (minimal), out-adapter (stub)

### Slice N — <behavior in one line>
- Cue: <one-glance flow sketch, e.g. `POST /booking → check overlap → persist → 201`>
- Acceptance tests: <one GWT flow per behavior this slice owns — positive + negative/edge>
- Touches: <layers; what's real vs stubbed this slice>
- Establishes: <convention or boundary introduced here, if any>
- Risk: <most likely wrong or skipped here; "none" if trivial>
- Deferred: <what's intentionally not built yet>
```
End with **MVP vertical** (which slices) and **Deferred** (what + where it slots).

## Low gear
In low gear (see `delivery-doctrine:fast-path`), skip the slice-list ceremony: emit only the walking
skeleton (one, at most two slices), and no MVP/deferrals section. Ordering and JIT
still apply.

## Plan-critic (full gear, not demos)
Before Gate 2, dispatch the `plan-critic` agent — a fresh context that did NOT write
the plan — to independently check the slices and acceptance behaviors against the
actual problem statement:
- Coverage: does every behavior the problem requires map to a slice? Flag misses.
- Drift: does any slice or behavior wander from what the problem asked? Flag it.
Feed its misses and drift back into the slice list before presenting Gate 2. Skip in low
gear and in live/presented sessions — there the deliberate slice-walk at Gate 2 is the
safeguard.

## Gate 2 — slice list agreed
Stop. Present the ordered slice list, the MVP vertical, and the deferrals. Wait for
explicit approval before any code. No slice starts until the list is signed off. Walk
each slice aloud by its Cue, its acceptance test, and its Risk; never skim — a skipped
slice is how gaps hide.

## Handoff
After approval, each slice runs the per-slice loop: its acceptance tests red, implementer to green,
review, critic on architecturally meaningful slices only, integration green, commit
the green slice, explicit sign-off before the next. See `delivery-doctrine:superpowers-seam`.

## Reuse
- Bite-sized TDD step format within a slice: superpowers `writing-plans` (format only).
- Over-engineering / horizontal-creep check: `delivery-doctrine:ddd-hexagonal-reviewer`.
- Loop and commit protocol: `delivery-doctrine:superpowers-seam`.
