---
name: gwt-testing
description: Use when writing or reviewing JUnit Jupiter tests in Java — the Java/JUnit specialization of test-first (GWT structure, given_when_then naming, zero comments).
---

# Given-When-Then Testing (JUnit Jupiter)

The Java/JUnit specialization of `delivery-doctrine:test-first`. Everything in that skill
applies unchanged — blank-line phase structure, `given<Context>_when<Action>_then<Outcome>`
naming, exactly one act per test, zero comments. This file adds only the JUnit specifics.

Tool defaults are the common community ones: JUnit Jupiter (6, as Boot 4.1 manages; 5 reads
the same), AssertJ, Mockito only where the interaction is the contract, Testcontainers for real
infrastructure. A house rule that picks others wins.

## JUnit shape
```java
@Test
void givenExpiredJwt_whenPreHandle_thenRejectedWith401() {
    var token = expiredTokenFor("user-1");
    var request = requestWithBearer(token);

    var allowed = interceptor.preHandle(request, response, handler);

    assertThat(allowed).isFalse();
    assertThat(response.getStatus()).isEqualTo(401);
}
```
- Phases separated by blank lines; no `// given` / `// when` / `// then` markers.
- `@Test` is the marker — no `test` prefix.
- Two acts → two tests.

## Test-first pairing
The loop is `delivery-doctrine:test-first`'s. A new test that does not compile is not red
yet: add the empty method, see the assertion fail, then implement to GREEN and refactor.
