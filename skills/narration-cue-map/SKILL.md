---
name: narration-cue-map
description: Use to plan live narration for an agentic build in front of an audience —
  maps a designated talking point to each agent-run window so there's no dead air,
  keeps narration parallel to agent work (never adds serial time), and protects the
  finish. Fill task-specific talking points from the task prompt.
---

# Narration Cue Map

No dead air, and no narration that adds time. The rule: if you're talking, an agent
should be working. Each window has a designated thing to say or do, running in parallel
with the agent. Fill the task-specific content (your thesis, the domain, the beats)
from the task prompt.

## The windows

### 1. Grill (agent is working the problem)
Strongest window. While the grill runs, present your design thesis: your read of the
domain, the bounded contexts, the key boundary decisions. Then loop others in to
participate in the grill — hand them the question, make it a conversation. The grill's
labelled discoveries (`[SCOPE]` / `[FUTURE]` / `[DISCUSS]` / `[RISK]`) are ready-made
prompts to raise with the room. This window carries the most narration; lean on it.

### 2. Slice review (Gate 2) — deliberate, no talk-over
Do NOT narrate over the slice list while scrolling. This is where a skipped slice bites
you. Walk each slice aloud by its `Cue` (the one-glance flow sketch), check it against
its acceptance test, and name its risk. Never skim. Short and structured beats fluent
and skipping.

### 3. Implementer run (agent is coding slice N)
Review and narrate the *previous* slice (N-1) while N is being built — parallelism, so
talking costs no clock. Approve changes as they land (the permission allow-list keeps
this fast). Explain the code as you approve it; this doubles as your read-the-code beat.

For a live session, run the implementer inline (see CLAUDE.md's execution rule) so its
replies to your comments are visible live and permissions don't re-ask; keep the critic
a subagent.

### 4. Critic pass (agent is reviewing)
Explain what the critic checks — spec compliance, code quality, adversarial spec-gap —
and read its findings aloud, deciding fix vs accept and justifying the call.

### 5. Close — protect the finish
The finale is the app running and the acceptance/integration tests green, live. This is
the payoff and it must be reached. Narrate the run.

## Time discipline (why the finish gets missed)
The finish is missed when narration and slicing eat the clock and no vertical ships.
- Pre-commit a small MVP vertical (about 3 slices) and name deferrals at Gate 2.
- Hard time-box each window. Over budget? Cut a slice — never cut the finish.
- Reserve time for the close. A coherent finished vertical beats a sprawling half-build.
- Narration is parallel, never serial: it happens during agent work, not instead of it.

## Task-specific fill (from the task prompt)
- Your design thesis and domain read (window 1).
- Which others you loop in, and when (window 1).
- Per-window time budget for this problem.
