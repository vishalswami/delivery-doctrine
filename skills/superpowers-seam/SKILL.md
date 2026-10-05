---
name: superpowers-seam
description: Use when running the delivery loop with superpowers installed. Defines
  who owns what between superpowers (TDD, subagent prompts, code review) and this
  doctrine (grill, slicing, gates), so they compose instead of fighting.
---

# Superpowers Seam

Superpowers owns the inner mechanics; this doctrine owns the orchestration. They
compose. Where they overlap, this file says who wins.

## Ownership
- superpowers `test-driven-development` — red-green-refactor inner loop.
- superpowers `subagent-driven-development` — implementer + spec/code-quality
  reviewer prompts, status handling.
- superpowers `requesting-code-review` — critic dispatch (diff + template).
- superpowers `writing-plans` — bite-sized TDD step format only.
- doctrine `delivery-doctrine:grill-fast` — requirements grill.
- doctrine `delivery-doctrine:thin-slice-planner` — vertical slice decomposition + ordering,
  walking-skeleton-first.
- doctrine — per-slice loop, Definition of Done, alignment gates, narration, model
  binding.
- doctrine `delivery-doctrine:ddd-hexagonal-reviewer` — architecture + over-engineering check.

## Reconciliations
1. **Gates override SDD continuous-execution.** SDD says "execute all tasks
   without stopping." That directive applies only *within* a slice. The slice
   boundary is a hard stop for sign-off. Borrow SDD's prompts and two-stage
   review; drive the loop yourself and end the turn at each slice.
2. **thin-slice-planner owns decomposition; writing-plans is format only.**
   Decompose by end-to-end behavior (vertical), not by file/responsibility.
   Expand an approved slice into writing-plans' bite-sized TDD steps if useful.
3. **TDD is the shared core, unforked.** Implementer subagent and the per-slice
   red-to-green both call `test-driven-development` as-is.
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
- **Team mode** (real repos with a PR workflow): branch per slice or task off the house
  base branch; push freely; PR — or stacked PR — per change. Follow the HOUSE branch,
  commit-message, and stacking conventions: honor-existing applies to workflow, not just
  architecture. The critic reviews the branch diff BEFORE push, so PRs arrive clean —
  tiered like everything else: own-eyes for trivial, critic for meaningful. "Push
  freely" means no permission friction, not review-free. The lead pushes and opens the
  PR after the review. External review bots (CodeRabbit etc.) run after push and do not
  replace the critic; treat their findings like critic findings — fix, or push back
  with reasoning.
- Both modes: commit once per green slice — slice tests pass, integration green. Never
  commit red or breaking code. Message names the slice and its behavior precisely
  (e.g. "slice 3: reject expired JWT with 401"), never "wip".
- Critic diffs: solo — BASE_SHA = previous slice's commit. Team — merge-base with the
  PR's *target* branch (for a stacked PR, the previous branch in the stack, not main);
  one review per push, covering commits since the last reviewed SHA. HEAD_SHA = current.
  Reuse `superpowers:requesting-code-review` as-is.

## Integration notes
- Reserve the full two-stage review (spec then code-quality) for architecturally
  meaningful slices; light pass or own eyes on trivial ones.
- SDD's `finishing-a-development-branch` (merge/PR) is optional for a
  single-session greenfield demo; the doctrine's close is the closing refactor
  plus final sign-off.
