---
name: systematic-debugging
description: Use when encountering any bug, test failure, hang or unexpected behavior, before
  proposing a fix — root cause first, one hypothesis at a time, a failing reproduction test,
  then one fix. Covers tracing a bad value to its origin, flaky and order-dependent tests, and
  when three failed fixes mean the design is wrong. Language-agnostic.
---

# Systematic Debugging

A fix aimed at the symptom moves the bug; a fix aimed at the cause removes it. So no fix is
proposed until the cause is known, and a change that turns the test green without an
explanation is not a cause. Simple bugs follow the same order; for them it is quick.

## 1. Investigate
- **Read the whole error.** Every line of the message and the stack trace: file, line, error
  code, and the frame where your code hands over to a library. Warnings printed near it count.
- **Reproduce it on demand**: the exact steps, or one test that shows it. If it comes and
  goes, collect data at each failure (inputs, timing, environment) until a pattern shows; a
  fix for a failure you cannot trigger cannot be checked.
- **Look at what changed** since it last worked: `git log` and `git diff`, dependency and
  configuration changes, how this environment differs (CI against local, one worktree
  against another).
- **Locate the break across components.** When the path crosses several (handler, queue,
  consumer, database), record what enters and leaves each boundary for one run. The first
  boundary where the value is already wrong is where to dig. Take that instrumentation out
  before the commit.
- **Follow a bad value back to its origin.** Ask what passed it in, then what passed that,
  up the callers, until you reach the place it was made; the fix goes there. When reading
  cannot follow the chain, capture a stack trace just before the failing operation (to
  stderr inside a test, so the runner shows it).
- **A hang** gets a thread dump at once (`delivery-doctrine:execution-hygiene`), never a
  longer timeout.

## 2. Compare
Find code in the same codebase that does the same kind of thing and works. Read it whole,
then list every difference from the broken path, the ones that seem harmless included:
configuration, ordering, lifecycle, what each assumes about its inputs. When the code follows
a reference implementation or a library's documented pattern, read all of it before adapting
any of it.

## 3. Hypothesize and test
- Write one hypothesis down: "X causes it, because Y."
- Test it with the smallest change that could prove it wrong, one variable at a time.
- Confirmed: go to step 4. Refuted: revert the change and form the next hypothesis from what
  you learned. A second guess stacked on an unreverted first one makes both unreadable.
- Not understanding something is a finding. Say what you do not understand and find out.

## 4. Fix
1. A failing test that reproduces the bug, per `delivery-doctrine:test-first`, red for the
   right reason. Where no test harness reaches, a script that exits non-zero.
2. One change, at the cause. Clean-up and refactoring are separate commits after green.
3. Evidence per `delivery-doctrine:execution-hygiene`: the reproduction test green, the
   scoped tests around the change green, the original symptom gone.
- **Fix at the source; guard at one boundary.** After the cause is fixed, add the single
  check that should have stopped the value: the adapter that accepted it, or the domain
  invariant it broke (invariants live in the domain). Not a validation layer in every tier.
- **Three failed fixes: stop.** When each fix exposes a new problem somewhere else, the
  design is the problem (shared state, hidden coupling, a pattern that does not fit). Take
  that to the user before a fourth attempt; it is an architecture decision, not a hypothesis.

## Flaky and order-dependent tests
- **Timing.** A test that sleeps for a guessed duration passes on a fast machine and fails
  under load. Wait for the condition instead: poll a predicate at a short interval up to a
  deadline, and fail with a message naming what never happened. A fixed wait is right only
  when timing is the behavior under test (a debounce, a retry interval), it starts after the
  triggering event, and the test name says why.
- **Pollution.** A test that passes alone and fails among others, or a file some unknown test
  leaves behind: run the candidate test files one at a time and check for the symptom after
  each; the first one that produces it is the culprit. Halve the list when it is long.
- **Several failures at once.** Unrelated ones (different files, subsystems, causes) can be
  investigated in parallel, one agent each, all dispatched in one message, each given its
  failing tests, the error output and the files it may change. Related ones are investigated
  together first: one cause often explains several.

## When the cause is outside the code
If the investigation shows the cause really is external (network, a provider's outage, the
clock), handle it where it enters: a bounded retry, a timeout, an error the caller can act
on; and say in the report what was checked. Most "no root cause" verdicts are investigations
that stopped early, so confirm steps 1 to 3 were done before reaching one.

## Stop signs
Go back to step 1 on any of these: a fix proposed before the failure reproduces; "try X and
see"; several changes in one run; a fix with no failing test before it; an explanation that
starts with "probably"; a fourth attempt after three that failed.

## Pairing
A bugfix is low gear (`delivery-doctrine:fast-path`): the reproduction test is its
acceptance test. Inside a wave, a slice that hits a bug it cannot explain follows this skill
before reporting BLOCKED (`delivery-doctrine:delivery-loop`).
