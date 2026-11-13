# Delivery Doctrine (injected at session start by the delivery-doctrine plugin)

How we work on any project. Lean by design: this file states the method and the
rules; depth lives in the on-demand skills named below.

## How we work
State your read of the problem as a falsifiable hypothesis, grill it against the truth
(problem statement, or codebase if brownfield), slice the work into thin vertical
behaviors, build each slice test-first, and confirm at every gate before moving on.
Reuse what exists (the skills below, the codebase's patterns) over reinventing. Right-size
everything to the problem.

## Gears (pick first — Gate 0)
Before anything else, choose the gear and name it out loud; it selects the skills and
the Definition of Done.
- **Full gear** (anything real): grill-fast → thin-slice-planner (waves) → per-wave
  parallel implementer/critic loop with all gates → close-out once live.
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
House facts (spec folder, hot files, PR and merge rules, worktree setup) come from the
repository profile when one is injected below; otherwise discover and honor them.

## Alignment gates (hard rule)
Stop and confirm. Never race ahead.
- The flow has stop-gates. At each one, STOP, show the result, wait for explicit
  approval. End the turn at the gate.
- Never infer agreement from a partial, ambiguous, or silent answer. If unsure,
  ask "approved to proceed?" and wait. Anything short of an explicit yes is
  not-yet-approved.
- The gates: (1) requirements agreed after the grill, (2) the wave plan agreed before
  any code, (3) per wave: every PR of the wave open and critic-clean, shown to the user
  together; on their go-ahead, each merges once mergeable under the house rules with every
  review thread resolved. The next wave starts only when the whole wave is on main.
- Batching questions is allowed only while gathering initial requirements. It
  never removes a gate.

## Vertical slicing
Each slice is one thin end-to-end vertical through every layer (in-adapter, port,
domain, out-adapter); it usually owns several acceptance behaviors, all green. Not
horizontal layers.
- Slice 0 is the walking skeleton: thinnest end-to-end path wired and passing
  before any feature.
- Slices run in waves of parallel PRs, as few waves as possible; each stays narrow so
  its PR stays easy to review.
- Just-in-time within a slice: touch all layers, build only what the slice needs.
  No speculative ports, repositories, or entities.
- State conventions (error handling, validation) up front; implement per slice.
- Depth: `delivery-doctrine:thin-slice-planner`.

## Per-slice loop + Definition of Done
Red test, implementer to green, manual review, critic pass on architecturally
meaningful slices only, app starts if wiring changed, integration test green, PR open.
A slice is not done until its PR merges on the user's go-ahead at the wave gate. Reserve the
full critic loop for the one or two slices with real architectural weight; own-eyes or
a light pass on the rest.
- Once the user says the feature is live, close out: what the slice files hold that
  plan.md, design.md and deferred.md lack moves there, the slice files are deleted, the
  three docs are fact-checked against the code, deduplicated and tightened, and each
  touched bounded context's context file (its AGENTS.md or CLAUDE.md) is updated.
  Depth: `delivery-doctrine:close-out`.
- Critic loop is iteration-based, convergence-gated, and tiered by slice weight (hard
  cap 3 passes, 3 lenses); mechanics live in `critic.md` and `delivery-doctrine:superpowers-seam`.
- Every local check is scoped to what the slice touched: its tests by name or pattern,
  lint on its files, the race detector once at the end on concurrent tests, the app
  started only when wiring changed. One package run at slice close is fine; `./...`,
  several packages, and full suites are CI's, on every push (the guard hook denies them
  locally). Depth: `delivery-doctrine:execution-hygiene`.
- Acceptance tests (behaviors named at the grill, written test-first per slice)
  accumulate into a suite; full gear closes by running the whole suite green against the
  running app — the deploy finale, run once at the close, not per iteration. They run
  end to end against in-process stubs of external boundaries. Depth:
  `delivery-doctrine:acceptance-testing`.
- Full gear, when a slice is done: formatter and static analysis (lint) clean on the
  files the slice touched, before the commit. (Enforcing git hook: the DoD hook, later.)
- Low gear collapses the loop: walking skeleton green, one critic pass, own eyes, run,
  commit; no acceptance suite, no lint (see Gears / `delivery-doctrine:fast-path`).
- Depth: `delivery-doctrine:test-first`, `superpowers:verification-before-completion`.

## Implementer / critic roles
Roles name the job; the model follows the task. Implementer writes; critic reviews;
implementer fixes; a few passes only where it earns it.
- Agents: `delivery-doctrine:implementer`, `delivery-doctrine:critic`. Built on superpowers' subagent prompts (see seam).
- Execution: subagent implementer for full-gear real work (it logs its responses to
  your review comments in its final report, since subagent replies aren't visible
  mid-run). Run the implementer inline in the main session when the scope is small
  (low gear) or the session is live/presented (demo, interview) — inline gives visible
  replies and no permission re-asking, and runs a wave's slices one after another by
  choice. The critic is always a subagent.
- Model: the orchestrator sets `model` on every dispatch; an agent config's default is
  only the fallback (the agent files say opus, so a dispatch that forgets gets the safer
  choice; with a remapped tier or agent, set `model` on every dispatch). Grilling and orchestration run on the main session (deep tier).
  Three tiers: deep = opus, standard = sonnet, fast = haiku. A profile's `## Models`
  section can remap a tier, a task kind below (domain, review, mechanical, analysis,
  retrieval) or an agent (implementer, critic, plan-critic), to a model alias (opus,
  sonnet, haiku, fable). An agent entry covers every dispatch of that agent; otherwise
  the task kind, then the tier.
- **Domain code** (services, ports, policy, dispatch, consumer logic) **and every
  review** (critic, plan-critic, any code review) → deep.
- **Mechanical code** — migrations, regenerated API/client code, wiring (e.g. main.go),
  a table test over declared constants, rebasing or restacking branches (rebase, regenerate,
  force-with-lease) — **and any analysis**, including analysis
  built on retrieval → standard. Scanning open PRs for overlap is analysis: the verdict
  is a judgement.
- **Retrieval only** — grep, find a file, read code or a document, fetch a page, pull a
  log line; information reported, no judgement → fast.
- A task mixing domain and mechanical code is split: a deep implementer for the
  domain part, a standard dispatch for the mechanical part.

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
Superpowers supplies the subagent and review mechanics the seam names. This
doctrine owns test-first and the orchestration: grilling, vertical slicing, the
implementer/critic loop, Definition of Done, and the gates. They compose; they
do not overlap.
- Depth: `delivery-doctrine:superpowers-seam`.

## Skills
Each skill self-describes; the harness lists them. Language profiles load only on their
language's work: Java/Spring, Python, Go.
