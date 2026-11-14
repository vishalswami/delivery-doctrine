---
name: pytest-testing
description: Use when writing or reviewing pytest tests in Python — the Python
  specialization of test-first. Given-When-Then structure, test_given_when_then
  naming (pytest requires the test_ prefix), one act per test, zero comments, hand-written
  fakes at ports with a contract test, infrastructure tests behind a marker.
---

# Pytest Testing

The Python/pytest specialization of `delivery-doctrine:test-first`. Everything there applies —
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
- Run only the test you're on, by node id
  (`pytest tests/test_auth.py::test_given_expired_token_when_authenticating_then_rejected`)
  or `-k given_expired_token`; never a bare `pytest` as the red/green loop — scope per
  `delivery-doctrine:execution-hygiene`.

## Doubles — fakes at ports first
- **A hand-written fake is the default double** for a port the domain owns: a class in
  `tests/fakes.py` that satisfies the `Protocol` and records what it was given as data
  (`self.saved: list[Order]`). Assert the outcome (what was stored, what came back), never a
  call count. Type-check the tests too, so mypy holds the fake to the port.
- **`unittest.mock` or `monkeypatch` only where the interaction is the contract** (the message
  sent is the behavior) or at a boundary you don't own. Never patch what you own inside the
  unit.
- **A contract test keeps the fake honest**: one suite over a parametrized fixture, the real
  adapter marked so the fast loop skips it.

```python
@pytest.fixture(params=["fake", pytest.param("postgres", marks=pytest.mark.integration)])
def store(request: pytest.FixtureRequest) -> OrderStore:
    if request.param == "fake":
        return FakeOrderStore()
    return request.getfixturevalue("postgres_store")


def test_given_a_saved_order_when_getting_it_then_returned(store: OrderStore) -> None:
    store.save(an_order(OrderId("o-1")))

    found = store.get(OrderId("o-1"))

    assert found.id == OrderId("o-1")
```

## Test files and infrastructure
- One naming convention per repository. Rename tests with the API they test, in the same
  commit: a test named for a function that no longer exists misleads.
- One act per test; split a test module past ~800 lines by behavior.
- A test that boots infrastructure (a database, a broker) carries a registered marker
  (`markers = ["integration: boots real infrastructure"]` under `[tool.pytest.ini_options]`)
  or lives in its own directory, so the loop runs `-m "not integration"` and stays hermetic.

## Test-first pairing
The loop is `delivery-doctrine:test-first`'s: RED for the right reason (an assertion, not
an `ImportError`), GREEN minimal, refactor.
