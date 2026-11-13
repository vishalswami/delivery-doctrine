---
name: test-first
description: Use when writing any test or any production code, in any language — the red-green-refactor loop, Given-When-Then structure (arrange/act/assert separated by blank lines, one act per test), given_when_then naming, zero comments, and the honesty rules (name the break, hand-derived expectations, no assertions on mocks). Language-agnostic; gwt-testing, pytest-testing and go-testing refine it.
---

# Test First

Every behavior starts as a failing test, in any language. This skill is the canonical
convention for the loop and for how a test reads; the language skills (see Pairing) add
ecosystem detail on top and never contradict it.

## The loop
1. **Red.** Write one test for one behavior and run it by name. Watch it fail, and for
   the right reason: an assertion failure because the behavior is missing. A compile
   error, a missing import or a typo is not red yet; add the empty signature and run
   again. A test that passes on its first run is testing behavior that already exists:
   fix the test. A failure you cannot explain means you do not know what the test checks.
2. **Green.** The least code that passes. No option, feature or clean-up elsewhere that
   the test did not ask for; the next test asks for the next piece.
3. **Refactor**, on green only: names, duplication, extracted helpers. Rerun; refactoring
   never adds behavior.

- Code written before its test is deleted, not kept as a reference: kept code gets
  adapted, and that is testing after. Explore freely, then throw the exploration away.
- A bug fix starts with a test that reproduces the bug and fails.
- Low gear never drops the loop. Generated code and configuration are tested at their
  consumer: the test that breaks if they are wrong.
- Every run is scoped to the test you are on (`delivery-doctrine:execution-hygiene`);
  the full suite is CI's.
- Hard to test means the design is unclear: simplify the interface instead of growing
  the setup.

## Structure

Three phases, separated by **blank lines** — no other separators:

| Phase | Rule |
|-------|------|
| **Given** | Arrange all inputs and state |
| **When** | Exactly one call to the code under test |
| **Then** | Assert outcomes only — no new arrangement |

If you need two acts, it is two tests. An assertion in the Given phase is a smell —
move it to Then.

## Naming

Explicit Given-When-Then names: `given<Context>_when<Action>_then<Outcome>`.

- The name states the scenario and the expected outcome, never the method under test.
- Adapt only casing/separators to the language's idiom, never the three-part shape:
  - snake-heavy langs: `given_expired_token_when_authenticating_then_rejected`
  - camel/underscore mix (Java/JS/Kotlin): `givenExpiredToken_whenAuthenticate_thenRejected`
  - langs with string test names (Ruby/JS `it`, Go subtests): the string reads
    "given ... when ... then ..."
- No `test`/`should` filler prefix; the framework marker already says it is a test.

```
✅ givenExpiredToken_whenAuthenticate_thenRejectedWith401
✅ given_no_users_upstream_when_list_then_empty_array
❌ rejectsWhenExpired        behavior-named but not given_when_then
❌ testAuthenticate
❌ authenticateReturnsFalse
```

## Comments

No comments in tests — zero, no exceptions. No `given`/`when`/`then` marker comments: the
blank lines are the separators. An arrange block long enough to want a marker becomes a
well-named helper.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Assertion inside Given | Move to Then |
| Multiple When calls | Split into separate tests |
| Name describes implementation | Rename to scenario + outcome |
| Phases run together | Separate with blank lines |

## Honest tests
Each test exists to catch one specific break, and catches it against the real code.
- **Name the break first.** Before writing the body, say which change to production code
  would turn it red. If only a deliberate change would (a constant's value, a message's
  wording, private structure), the test breaks on every redesign and never on a bug:
  assert the behavior built on that choice instead.
- **Derive expectations by hand**, as literals or hand-checked fixtures. A value the code
  under test produced, itself or through a helper, agrees with it whatever it does.
- **A mock earns no assertion.** Asserting a mock was called proves the mock exists.
  Assert the outcome; assert arguments, counts or order only when the interaction is the
  contract, and then give each branch its own double.
- **Mock at the slow or external level.** Know what the real method does as a side effect
  before replacing it, and leave real whatever the test relies on. External boundaries get
  in-process stubs (`delivery-doctrine:acceptance-testing`); everything inside stays real.
  Once the doubles take more lines than the test itself, switch to the real components.
- **Mirror real payloads completely**, every documented field: a partial fake passes while
  the code that reads the missing field breaks in integration.
- **Production code carries production methods.** Teardown that exists for tests belongs
  in test helpers; a production class never grows a `reset()` for them.
- **Behavior, not text.** A test that greps a script, skill or config file for a line
  proves the line is there, not that it works: run it on inputs and assert output and exit code.
- **Test your contract, not the framework's**: the endpoint you expose, the SQL you send,
  the message you publish. Getters, constructors and plain forwarding earn a test only
  when they validate, default or derive something.

## Before calling it done
Mutate the production code in your head: swap a constant or argument, take the other
branch, drop a side effect, return empty or the default, skip the check on zero, empty,
null, malformed or unauthorized input. Each should fail at least one test; a mutation
nothing catches is an unprotected behavior.

Stop and restart the loop on any of these: production code with no failing test before
it; a new test green on its first run; a red you cannot explain; an assertion on a mock,
or an expected value the code under test produced.

## Pairing
Ecosystem detail: `delivery-doctrine:gwt-testing` (Java/JUnit),
`delivery-doctrine:pytest-testing`, `delivery-doctrine:go-testing`. Whole-vertical tests:
`delivery-doctrine:acceptance-testing`. Running checks and claiming green:
`delivery-doctrine:execution-hygiene`.
