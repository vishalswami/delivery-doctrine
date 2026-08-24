---
name: pytest-testing
description: Use when writing or reviewing pytest tests in Python — the Python
  specialization of given-when-then-tests. Given-When-Then structure, test_given_when_then
  naming (pytest requires the test_ prefix), one act per test, zero comments.
---

# Pytest Testing

The Python/pytest specialization of `delivery-doctrine:given-when-then-tests`. Everything there applies —
blank-line phases, one act per test, zero comments. This adds only the pytest specifics.

## Naming
pytest requires the `test_` prefix, so the shape is:
`test_given_<context>_when_<action>_then_<outcome>`
The JUnit "no test prefix" rule does NOT transfer — without `test_`, pytest won't collect it.

```python
def test_given_expired_token_when_authenticating_then_rejected():
    token = expired_token_for("user-1")

    result = authenticate(token)

    assert result.rejected
    assert result.status == 401
```
- Phases separated by blank lines; no `# given` / `# when` / `# then` markers.
- Two acts → two tests.

## pytest specifics
- Fixtures for shared arrange; keep them small and named for what they provide.
- `@pytest.mark.parametrize` for range checks (zero, negative, boundary) — one behavior,
  many cases, still readable.
- Acceptance tests drive the entry point and stub boundaries with `responses` or an
  `httpx` mock transport, per `delivery-doctrine:acceptance-testing`.

## TDD pairing
Inside `superpowers:test-driven-development`: RED first, GREEN minimal, refactor. Full
structure rules live in `delivery-doctrine:given-when-then-tests`.
