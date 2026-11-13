---
name: thin-slice-planner
description: Use after requirements are locked to turn a spec and acceptance tests
  into thin vertical slices grouped into waves of parallel PRs, walking-skeleton-first,
  with as few waves as possible. Owns the wave-plan gate before any code. Pairs with
  grill-fast (input) and the per-wave loop (output).
---

# Thin-Slice Planner

Turn locked requirements + acceptance tests into thin vertical slices, grouped into
waves. A wave is a set of slices built and merged in parallel, one PR each; the next
wave starts only when the whole wave is on main. Narrow slices keep review easy; few
waves keep delivery fast. This skill owns gate 2: the wave plan is agreed before any
code is written.

Input usually comes from `delivery-doctrine:grill-fast` (requirements, canonical terms, domain
shape, acceptance behaviors — the plan). It works from any spec with the same pieces.

## What a slice is
One thin end-to-end vertical through every layer it needs — in-adapter, port,
domain, out-adapter. A single vertical usually has several acceptance behaviors (a
happy path plus its negative and edge flows); the slice owns all of them, and its
done-criterion is all its acceptance tests green. Never a horizontal layer
("build all repositories" is not a slice). Width comes from more slices per wave,
never from fatter slices.

## Process
1. **Slice 0 = walking skeleton.** The thinnest end-to-end path wired and passing
   before any feature: one request in, through all layers, one response out,
   proving the wiring. Not a feature. It also lands the shared seams later slices
   need — contracts, interfaces, any migration later slices share, registration points,
   wiring, and empty per-slice sections in shared docs — so they depend on it alone.
2. **Group behaviors into slices.** A slice is one thin vertical and usually owns
   several related acceptance behaviors (happy path plus its negative and edge flows).
   Group the grill's behaviors by the vertical they exercise; each behavior's test is
   written test-first during the slice.
3. **Record real dependencies.** `Depends on:` a slice only when this one needs that
   one's code on main; give the reason. Ordering by habit is not a dependency. If a
   slice depends on a small piece of another, move that piece into an earlier wave.
4. **Merge order lives in the wave table.** Where one wave-mate must merge before
   another for release reasons (where merging to main deploys) though the code is
   independent, or a release check that is not code (a query, another team's release)
   gates a merge, the wave table says so for that wave. It is delivery scaffolding;
   close-out removes it.
5. **Place slices in waves.** A slice's wave = 1 + the latest wave among its
   dependencies; wave 0 is the skeleton plus any slice not needing it. Then shrink
   the wave count: remove false dependencies, pull shared pieces earlier.
6. **No collisions inside a wave.** Wave-mates must not edit the same hot file:
   migration chains (one slice per wave adds a migration; prefer the skeleton wave),
   registries and wiring (`main`, DI, routers), API specs and generated clients (one
   slice per spec per wave; regenerate, never hand-merge), dependency manifests and
   lockfiles, shared per-feature doc sections — plus any the repository profile lists.
   Pre-create the hook in an earlier wave, or move one slice to the next wave.
7. **Width.** No hard cap. Flag a wave wider than about five: the user reviews a
   wave's PRs in one sitting, and a serial merge queue flattens the gain past 3-4.
8. **Just-in-time within each slice.** A slice touches all the layers it needs and
   builds only what it needs. No speculative ports, repositories, or entities;
   note what is deliberately stubbed this slice and built later. Over-engineering and
   horizontal creep: `delivery-doctrine:ddd-hexagonal-reviewer`.
9. **Name the MVP vertical** (the slices that prove the core domain end to end) and
   **the deferrals** (out of scope for now, and where each slots in later).
10. **State conventions once.** Error handling and validation approach up front,
   implemented JIT per slice. Slice numbers are stable once agreed: never reused or
   renumbered, since other documents cite them.

## Output format
```markdown
### Slice N — <behavior in one line>
- Wave: <n>
- Cue: <one-glance flow sketch, e.g. `POST /booking → check overlap → persist → 201`>
- Acceptance tests: <one GWT flow per behavior this slice owns — positive + negative/edge>
- Touches: <files or packages where known; every hot file it edits, always>
- Interfaces: <consumes: exact names and signatures already on main (slice 0's seams,
  earlier waves) or pinned in this plan; produces: what later waves build against; "none">
- Depends on: <slice ids + why it needs their code on main; "none">
- Establishes: <convention or boundary introduced here, if any>
- Risk: <most likely wrong or skipped here; "none" if trivial>
- Deferred: <what's intentionally not built yet>
```
Slice 0 uses the same shape (Proves: end-to-end wiring). End with the **wave table**
(wave → slices, plus any merge order or release check inside a wave), the **MVP
vertical**, and **Deferred** (what + where it slots). Interfaces are exact signatures
(`ReserveSeat(ctx, showID, seat) (Hold, error)`). A slice consumes what is on main when its
wave starts and produces for later waves. Wave-mates never build on each other's code; the
most they share is a contract pinned in this plan, which the consumer builds against a stub.

Where it is written: the spec folder (the repository profile names it; otherwise
`docs/specs/<date>-<feature>/`). The wave table, MVP vertical and deferrals go in
`slices.md`, each slice in `slices/<N>-<name>.md`. plan.md, design.md and deferred.md
carry the agreed requirements and design from Gate 1; the slice files are build notes
that close-out removes.

## Steps (optional)
Only for a mechanical slice (a standard-tier dispatch) or a live session that wants a
script. Five per behavior: the failing test as code, with the spec's values; the run and
the failure it should show; the signature to implement and its file; the run that should
pass; the commit. A step is done when it leaves one reasonable thing to write, not when
it holds the code; steps longer than the code they describe are a transcript.

## Low gear
In low gear (`delivery-doctrine:fast-path`), skip the wave plan: emit only the walking
skeleton (one, at most two slices, serial), and no MVP/deferrals section. JIT still applies.

## Plan-critic (full gear, not demos)
Before Gate 2, dispatch the `plan-critic` agent — a fresh context that did NOT write
the plan — to check it against the actual problem statement: coverage misses, drift, false
dependencies, collisions and interface mismatches between wave-mates, and defects the plan
mandates. Fold its findings in before presenting Gate 2. Skip in low gear and in
live/presented sessions — there the deliberate slice-walk at Gate 2 is the safeguard.

## Gate 2 — wave plan agreed
Stop. Present the wave table, each slice, the MVP vertical, and the deferrals. Wait for
explicit approval before any code. Walk each slice aloud by its Cue, its acceptance
test, its dependencies, and its Risk; never skim — a skipped slice is how gaps hide.

## Handoff
After approval, the per-wave loop runs: all slices of a wave start together, each
through red → green → review → PR; the wave gate merges them; then the next wave. See
`delivery-doctrine:delivery-loop`. Once the feature is live: `delivery-doctrine:close-out`.
