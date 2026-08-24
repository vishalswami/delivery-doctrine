---
name: given-when-then-tests
description: Use when writing or reviewing tests in ANY language — enforces Given-When-Then structure (arrange/act/assert separated by blank lines), exactly one act per test, given_when_then method naming, and zero comments. Language-agnostic; language-specific skills (e.g. gwt-testing for Java/JUnit) refine it.
---

# Given-When-Then Testing (language-agnostic)

Every test follows explicit Given-When-Then structure, in any language. This skill
is the canonical convention; language-specific skills (`delivery-doctrine:gwt-testing` for
Java/JUnit) add ecosystem detail on top and never contradict it.

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

No comments in tests — zero, no exceptions. Never annotate the phases with
`given`/`when`/`then` marker comments: the blank lines are the separators. If an
arrange block feels long enough to want a marker, extract a well-named helper
instead. Reinforces the global no-comments rule.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Assertion inside Given | Move to Then |
| Multiple When calls | Split into separate tests |
| Name describes implementation | Rename to scenario + outcome |
| Phases run together | Separate with blank lines |
| Phase-marker comments | Delete; extract a helper if orientation is needed |

## TDD pairing

Use inside `superpowers:test-driven-development`: write the GWT test RED first,
implement to GREEN, then refactor. This skill governs how the test reads; the TDD
skill governs the red-green-refactor loop and stays unforked.