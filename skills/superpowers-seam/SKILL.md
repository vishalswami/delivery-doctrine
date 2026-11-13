---
name: superpowers-seam
description: Use when running the delivery loop with superpowers installed. Defines
  who owns what between superpowers (subagent prompts, code review) and this
  doctrine (grill, slicing, test-first, gates), so they compose instead of fighting.
---

# Superpowers Seam

Superpowers owns the inner mechanics; this doctrine owns the orchestration. They
compose. Where they overlap, this file says who wins.

## Ownership
- superpowers `subagent-driven-development` — implementer + spec/code-quality
  reviewer prompts, status handling.
- superpowers `requesting-code-review` — critic dispatch (diff + template).
- superpowers `writing-plans` — bite-sized TDD step format only.
- doctrine `delivery-doctrine:grill-fast` — requirements grill.
- doctrine `delivery-doctrine:test-first` — red-green-refactor inner loop, test structure.
- doctrine `delivery-doctrine:thin-slice-planner` — vertical slice decomposition into waves,
  walking-skeleton-first.
- doctrine — per-wave loop, Definition of Done, alignment gates, narration, model
  binding.
- doctrine `delivery-doctrine:ddd-hexagonal-reviewer` — architecture + over-engineering check.

## Reconciliations
1. **Gates override SDD continuous-execution.** SDD says "execute all tasks
   without stopping." That directive applies only *within* a wave. The wave gate is a
   hard stop for the user's go-ahead. Borrow SDD's prompts and two-stage review;
   drive the loop yourself and end the turn at each wave gate. Parallel dispatch of a
   wave's slices follows superpowers `dispatching-parallel-agents`.
2. **thin-slice-planner owns decomposition; writing-plans is format only.**
   Decompose by end-to-end behavior (vertical), not by file/responsibility.
   Expand an approved slice into writing-plans' bite-sized TDD steps if useful.
3. **Test-first is the doctrine's own.** The implementer subagent and the inline
   per-slice red-to-green both follow `delivery-doctrine:test-first`.
4. **The lead decides what to delegate.** Design decisions stay with the lead;
   mechanical slices go to the implementer subagent. Which slices, if any, the
   lead writes by hand is a runtime call, not fixed by this doctrine.
5. **Adversarial spec-gap is a doctrine-added lens, not a fork.** The critic runs a
   third lens (attack inputs the spec never named) layered on top of superpowers'
   `requesting-code-review`, not replacing it.
6. **The doctrine binds the model, by task type.** SDD's per-role tiers
   (cheap/standard/capable) do not carry over; the orchestrator sets `model` on every
   dispatch per the doctrine's Implementer / critic roles.

## Commit protocol (how the critic gets its diff)
Two modes — pick with the gear at Gate 0:
- **Solo mode** (take-homes, demos, spikes — default when there's no shared repo):
  local `git init`, no remote required. (Overrides a project-level git ban only when
  that rule has no stated reason — e.g. a take-home skeleton default.)
- **Team mode** (real repos with a PR workflow): branch per slice off the house base
  branch; push freely; one PR per slice. Follow the HOUSE branch, commit-message, and
  PR-opening conventions (title tags, labels that trigger review bots): honor-existing
  applies to workflow, not just architecture. The critic reviews the branch diff BEFORE
  push, so PRs arrive clean — tiered like everything else: own-eyes for trivial, critic
  for meaningful. "Push freely" means no permission friction, not review-free. The lead
  pushes once per slice after the review and opens the PR. External review bots
  (CodeRabbit etc.) run after push and do not replace the critic; treat their findings
  like critic findings — fix, or push back with reasoning — and resolve each thread.
- Both modes: commit once per green slice — slice tests pass, integration green. Never
  commit red or breaking code. Message names the slice and its behavior precisely
  (e.g. "slice 3: reject expired JWT with 401"), never "wip".
- Critic diffs: BASE_SHA = merge-base with main (waves never stack); one review per
  push, covering commits since the last reviewed SHA. HEAD_SHA = current. Reuse
  `superpowers:requesting-code-review` as-is.

## Per-wave loop
1. **Start.** Every slice of the wave starts together, off current main: one implementer
   subagent per slice, dispatched in one message, each in its own git worktree and
   branch (Agent `isolation: worktree`, or `git worktree add`). The model per dispatch
   follows the doctrine's task-type binding. If a 429 hits, retry; never widen.
2. **Worktree cost.** A fresh worktree has no installed dependencies. Install only what
   the slice's stack needs (shared module caches cover most compiled stacks). Before the
   first wave in a repo, confirm local tests can run concurrently from separate
   worktrees (a shared test database, fixed ports); if not, give each worktree its own
   database name or port, or the lead runs those slices' verification one worktree at a time. Starting the
   app inside a wave needs per-worktree ports; otherwise the lead does it after merge.
3. **Each slice.** Red → green → critic (tiered) → fix → the lead pushes and opens the
   PR. Critics run in parallel as slices finish, each dispatched with its slice's worktree
   path and branch: it reads the code and runs its checks there, not in the main checkout.
4. **Wave gate.** When every PR of the wave is open and critic-clean, show the user
   all of them together. On the go-ahead, merge each PR once it is mergeable under the
   house rules (required checks, approvals; the repository profile names them) with every review thread resolved, human or
   bot. Enqueue (or merge) at once every PR the wave table puts no order on; a PR it
   orders is enqueued only once what it waits for has merged or its release check is done. Rebase a PR only when it actually conflicts (a mechanical
   restack, standard tier); regenerate generated files, never hand-merge them.
5. **Next wave.** Starts only when every PR of the wave is merged; its slices branch off
   the new main together.
6. **Blocked slice.** A slice that cannot be cleared inside its wave moves to the next
   wave (its PR to draft), with anything depending on it. Its branch is rebased onto the new main
   when that wave starts. Back to Gate 2 only when a
   dependency or the plan itself changed.
Solo mode runs the same loop locally: the gate is every branch critic-clean, and "merge" is
merging into local main on the go-ahead.

## Integration notes
- Reserve the full two-stage review (spec then code-quality) for architecturally
  meaningful slices; light pass or own eyes on trivial ones.
- SDD's `finishing-a-development-branch` (merge/PR) is optional for a
  single-session greenfield demo; the doctrine's close is the closing refactor
  plus final sign-off, then `delivery-doctrine:close-out` once the feature is live.
