# Delivery Doctrine (injected at session start by the delivery-doctrine plugin)

How we work on any project. Lean by design: this file states the method and the
rules; depth lives in the on-demand skills named below.

## How we work
State your read of the problem as a falsifiable hypothesis, grill it against the truth
(problem statement, or codebase if brownfield), slice the work into thin vertical
behaviors, build each slice test-first, and confirm at every gate before moving on.
Reuse what exists (superpowers TDD, the skills below) over reinventing. Right-size
everything to the problem.

## Gears (pick first — Gate 0)
Before anything else, choose the gear and name it out loud; it selects the skills and
the Definition of Done.
- **Full gear** (anything real): grill-fast → thin-slice-planner → per-slice
  implementer/critic loop with all gates.
- **Low gear** (spikes, throwaways, small tasks, bugfixes; clock beats architecture):
  grill (scope-appropriate) → walking skeleton test-first → one critic pass → own eyes
  → run → commit. Reduced ceremony, never reduced correctness. See `delivery-doctrine:fast-path`.
Low gear cuts *process*, not *architecture fit*: inside an existing codebase it honors
the house style (hexagonal/DDD if that's what's enforced); skipping the hexagon is only
for a greenfield throwaway. A low-gear task that outgrows itself graduates to full gear,
rebuilt, not promoted in place.
Safe defaults when unstated: no gear named → full gear; architecture unclear → honor the
existing codebase; a shared/house repo → team commit mode, no remote → solo (see
`delivery-doctrine:superpowers-seam`).

## Alignment gates (hard rule)
Stop and confirm. Never race ahead.
- The flow has stop-gates. At each one, STOP, show the result, wait for explicit
  approval. End the turn at the gate.
- Never infer agreement from a partial, ambiguous, or silent answer. If unsure,
  ask "approved to proceed?" and wait. Anything short of an explicit yes is
  not-yet-approved.
- The gates: (1) requirements agreed after the grill, (2) full slice list agreed
  before any code, (3) each slice green and reviewed before the next starts.
- Batching questions is allowed only while gathering initial requirements. It
  never removes a gate.

## Vertical slicing
Each slice is one thin end-to-end vertical through every layer (in-adapter, port,
domain, out-adapter); it usually owns several acceptance behaviors, all green. Not
horizontal layers.
- Slice 0 is the walking skeleton: thinnest end-to-end path wired and passing
  before any feature.
- Just-in-time within a slice: touch all layers, build only what the slice needs.
  No speculative ports, repositories, or entities.
- State conventions (error handling, validation) up front; implement per slice.
- Depth: `delivery-doctrine:thin-slice-planner`.

## Per-slice loop + Definition of Done
Red test, implementer to green, manual review, critic pass on architecturally
meaningful slices only, app starts if wiring changed, integration test green, explicit
sign-off. A slice is not done until I say so. Reserve the full critic loop for the one
or two slices with real architectural weight; own-eyes or a light pass on the rest.
- Critic loop is iteration-based, convergence-gated, and tiered by slice weight (hard
  cap 3 passes, 3 lenses); mechanics live in `critic.md` and `delivery-doctrine:superpowers-seam`.
- Every local check is scoped to what the slice touched: its tests by name or pattern,
  lint on its files, the race detector once at the end on concurrent tests, the app
  started only when wiring changed. Whole packages and full suites are CI's, on every
  push. Depth: `delivery-doctrine:execution-hygiene`.
- Acceptance tests (behaviors named at the grill, written test-first per slice)
  accumulate into a suite; full gear closes by running the whole suite green against the
  running app — the deploy finale, run once at the close, not per iteration. They run
  end to end against in-process stubs of external boundaries. Depth:
  `delivery-doctrine:acceptance-testing`.
- Full gear, when a slice is done: formatter and static analysis (lint) clean on the
  files the slice touched, before the commit. (Enforcing git hook: the DoD hook, later.)
- Low gear collapses the loop: walking skeleton green, one critic pass, own eyes, run,
  commit; no acceptance suite, no lint (see Gears / `delivery-doctrine:fast-path`).
- Depth: `superpowers:test-driven-development`, `superpowers:verification-before-completion`.

## Implementer / critic roles
Roles name the job; the model follows the task. Implementer writes; critic reviews;
implementer fixes; a few passes only where it earns it.
- Agents: `delivery-doctrine:implementer`, `delivery-doctrine:critic`. Built on superpowers' subagent prompts (see seam).
- Execution: subagent implementer for full-gear real work (it logs its responses to
  your review comments in its final report, since subagent replies aren't visible
  mid-run). Run the implementer inline in the main session when the scope is small
  (low gear) or the session is live/presented (demo, interview) — inline gives visible
  replies and no permission re-asking. The critic is always a subagent.
- Model: the orchestrator sets `model` on every dispatch; an agent config's default is
  only the fallback (the implementer's is opus, so a dispatch that forgets gets the
  safer choice). Grilling and orchestration run on the main session (opus).
- **Domain code** (services, ports, policy, dispatch, consumer logic) **and every
  review** (critic, plan-critic, any code review) → opus.
- **Mechanical code** — migrations, regenerated API/client code, wiring (e.g. main.go),
  a table test over declared constants — **and any analysis**, including analysis
  built on retrieval → sonnet. Scanning open PRs for overlap is analysis: the verdict
  is a judgement.
- **Retrieval only** — grep, find a file, read code or a document, fetch a page, pull a
  log line; information reported, no judgement → haiku.
- A task mixing domain and mechanical code is split: an opus implementer for the
  domain part, a sonnet dispatch for the mechanical part.

## Architecture judgment
Right-size architecture to the problem, and say so out loud when you keep
something simple ("port here because it's a real boundary; plain here because it
doesn't earn the abstraction").
- Invent nothing: use only the patterns the problem actually has. Over-applying
  DDD is as wrong as under-applying it. Let the domain lead; reach for a port
  only when crossing out of it.
- Dependencies point inward. The domain is pure: no framework imports or
  annotations on domain types.
- No comments — a hard rule, in production and test code alike. Code explains
  itself through intention-revealing names for classes, fields, and methods, and
  through well-named extracted units. A comment is a signal the naming or
  structure failed; fix that instead of annotating it. Precisely: no *inline*
  comments — language-mandated API-doc forms (godoc on Go exports, a one-line
  docstring on a public Python API) are documentation, governed by the language
  profile; WHY still goes to an ADR or a test name. The language profiles carry
  the depth.
- Depth: `delivery-doctrine:ddd-hexagonal-reviewer`.

## Narration discipline
No dead air. Every agent-run window has a designated thing being said or done:
explain a skill, justify a decision, or review the prior slice by hand.
- Depth: `delivery-doctrine:narration-cue-map`.

## The seam (superpowers and this doctrine)
Superpowers owns the TDD red-green-refactor core and the coverage that falls out
of it. This doctrine owns the orchestration: grilling, vertical slicing, the
implementer/critic loop, Definition of Done, and the gates. They compose; they
do not overlap.
- Depth: `delivery-doctrine:superpowers-seam`.

## Skill index
- `delivery-doctrine:grill-fast` — fast/greenfield requirements grill to slice list + acceptance behaviors.
- `delivery-doctrine:grill-brownfield` — brownfield comprehension grill (existing codebase + glossary).
- `delivery-doctrine:thin-slice-planner` — grill output to ordered vertical slices, walking-skeleton-first.
- `delivery-doctrine:ddd-hexagonal-reviewer` — ports/adapters + over-engineering check.
- `delivery-doctrine:fast-path` — low-gear delivery for spikes, small tasks, and bugfixes.
- `delivery-doctrine:narration-cue-map` — live narration windows; no dead air, protect the finish.
- `delivery-doctrine:execution-hygiene` — running tests and long commands scoped to the change, without self-inflicted thrash.
- `delivery-doctrine:acceptance-testing` — end-to-end slice test; in-process stubs for external boundaries.
- `delivery-doctrine:given-when-then-tests` — language-agnostic test structure + given_when_then naming.
- `delivery-doctrine:superpowers-seam` — how this doctrine and superpowers compose.
- `superpowers:test-driven-development` — red-green-refactor core.
- Java/Spring profile (loads only on Java work): `delivery-doctrine:spring-boot`, `delivery-doctrine:gwt-testing`,
  `delivery-doctrine:readable-java-style`, `delivery-doctrine:code-quality`, `delivery-doctrine:concurrency-review`, `delivery-doctrine:security-audit`.
- Python profile (loads only on Python work): `delivery-doctrine:python-style`, `delivery-doctrine:pytest-testing`.
- Go profile (loads only on Go work): `delivery-doctrine:go-style`, `delivery-doctrine:go-testing`.
