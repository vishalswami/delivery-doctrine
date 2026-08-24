---
name: gwt-testing
description: Use when writing or reviewing JUnit 5 tests in Java — the Java/JUnit specialization of given-when-then-tests (GWT structure, given_when_then naming, zero comments).
---

# Given-When-Then Testing (JUnit 5)

The Java/JUnit 5 specialization of `delivery-doctrine:given-when-then-tests`. Everything in that skill
applies unchanged — blank-line phase structure, `given<Context>_when<Action>_then<Outcome>`
naming, exactly one act per test, zero comments. This file adds only the JUnit specifics.

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

## TDD pairing
Inside `superpowers:test-driven-development`: write the GWT test RED first (it won't
compile), implement to GREEN, then refactor. Full rules live in `delivery-doctrine:given-when-then-tests`.
