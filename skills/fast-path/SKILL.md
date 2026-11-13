---
name: fast-path
description: Low-gear delivery for spikes, throwaways, small tasks, and bugfixes where
  clock beats architecture. Walking skeleton test-first with reduced ceremony — one
  critic pass, no slice-list ceremony. Honors the codebase's existing architecture;
  skips the hexagon only on a greenfield throwaway. Chosen at Gate 0.
---

# Fast Path (low gear)

The low gear of the delivery loop, chosen at Gate 0. For spikes, throwaways, small
tasks, and bugfixes where the clock beats architecture. Reduced ceremony, not reduced
correctness.

By default the implementer runs inline in the main session, not as a dispatched
subagent — small scope means no isolation overhead and its replies stay visible (see
CLAUDE.md's execution rule).

## The flow
1. **Grill with `delivery-doctrine:grill-fast`, scope-appropriate.** Run the `delivery-doctrine:grill-fast` skill even in
   low gear — a small task shrinks the grill naturally; it does not remove it. Lock
   what's being built and its acceptance check.
2. **Walking skeleton, test-first.** Write the failing acceptance test for the thin
   end-to-end thread, then minimal code to green. Follow
   `superpowers:test-driven-development`; drive the entry point per `delivery-doctrine:acceptance-testing`.
   Name the test `given<Context>_when<Action>_then<Outcome>` (per `delivery-doctrine:given-when-then-tests`)
   — this is quality, not ceremony, and is never dropped in low gear. A behavior-y
   camelCase name like `receiptsAddAndSalesRemoveInTimestampOrder` is NOT compliant;
   restructure to
   `given_receipts_and_sales_when_replayed_in_timestamp_order_then_balance_applies_in_order`.
3. **One critic pass, then own eyes.** Dispatch the critic once (spec, quality,
   adversarial spec-gap); fix findings; then your own eye-pass. No iterate-to-cap loop.
4. **Run and commit.** Acceptance green (the test you wrote, by name), the app started
   if wiring changed (a walking skeleton usually is wiring), commit the green thread with
   a clear message. In team mode, commit on a branch and PR per `delivery-doctrine:superpowers-seam`'s commit
   protocol — house lint/CI gates apply regardless of gear. Follow `delivery-doctrine:execution-hygiene`
   when running tests or any long command.

## What low gear drops (vs full gear)
- The wave plan and MVP/deferrals ceremony (`delivery-doctrine:thin-slice-planner` emits just the
  walking skeleton).
- The iterate-to-cap critic loop (one pass only).
- The accumulated acceptance suite and per-commit linting / static analysis (solo mode;
  in team mode the house CI/lint gates still apply).
- ADRs.

## What low gear never drops
- Test-first and a green, running result.
- One critic pass.
- Test structure and naming: given-when-then (`given…_when…_then…`) and zero comments.
  Low gear cuts process ceremony, not test quality.
- **Architecture fit.** Inside an existing codebase, honor its architecture — if the
  house style is hexagonal/DDD (enforced by convention or manually), conform to it via
  `delivery-doctrine:ddd-hexagonal-reviewer`. Skipping the hexagon is only for a greenfield throwaway with
  no house style to honor.

## Graduation
A low-gear task that turns out to matter is rebuilt in full gear, not promoted in place.
Toy code is disposable by definition.
