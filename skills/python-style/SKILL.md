---
name: python-style
description: Use when writing or reviewing Python — enforces type hints (mypy-clean),
  frozen dataclasses that keep their own invariants, Protocol ports declared by their
  consumer, package-by-feature layout wired in main, small typed functions, guard clauses,
  zero comments, and formatting delegated to ruff/black. The Python profile's clean-code
  depth; pairs with pytest-testing. Loads at implementation time for Python work.
---

# Python Style

The Python quality profile. Loaded at implementation time for Python work (the language
is chosen after the grill, per right-sizing — the grill and slicing are language-agnostic).
Pairs with `delivery-doctrine:pytest-testing`.

**House conventions first**, for consistency, over this profile and `pytest-testing`: a
structure below that the house has under other names keeps the house's names; one it lacks,
introduce. A house rule that is plainly bad practice (it causes bugs, a security or correctness
risk, or works against consistency) is neither followed nor bypassed silently: name it, give
the reason, propose the better practice and let the user decide. Read the context file and
house docs before judging; a choice they record as deliberate is not a finding.

## Rules
- **Type hints everywhere.** Annotate every function signature and non-trivial local;
  aim mypy-clean. Types are Python's real type system — use them, don't skip them.
- **Small, single-responsibility functions**; guard clauses and early returns over deep
  nesting. A clear 20-line function is not a smell; don't reflexively split it.
- **No inline comments** — zero, in production and tests (the doctrine's hard rule). A
  one-line docstring on a public API documents the contract (the Python analog of
  godoc); a non-obvious WHY goes to an ADR or a test name — never a docstring or an
  inline comment. Names carry the what.
- **On a hang:** `py-spy dump --pid <pid>` names the stuck stack in seconds (see
  `delivery-doctrine:execution-hygiene`).
- **No magic values** — name constants.
- **Formatting delegated** to ruff/black; don't hand-format. Lint with ruff on the
  files you touched (`ruff check <paths>`), per `delivery-doctrine:execution-hygiene`.

## Domain types
- **Value objects are `@dataclass(frozen=True, slots=True)`** (`slots` needs 3.10+;
  `NamedTuple` where tuple behaviour is wanted). `__post_init__` checks the invariant and
  raises a domain error; frozen means a valid instance stays valid, and a change returns a
  new value (`dataclasses.replace`). No bare dicts or tuples standing in for domain types.

```python
@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeAmountError(self.amount)
```
- **Typed IDs and closed sets.** `OrderId = NewType("OrderId", str)` lets mypy catch a
  swapped argument. A closed set is an `Enum` (`StrEnum` on 3.11+), parsed once at the edge,
  with its classification as a method or property on the enum, so the rule sits on the value
  rather than in a module-level set of strings.
- **Entities carry their rules.** `@dataclass(eq=False)` keeps identity equality (or define
  `__eq__` and `__hash__` on the id). State changes are methods that keep the invariant;
  callers don't assign attributes, so it has one keeper. `@property` only for derived values;
  no getters or setters. Lifecycle state is one method taking `now`, so "open" has one
  definition in Python; a SQL guard enforcing the same rule atomically against a
  read-update-persist race is right, mirrored by the method and pinned to it by one test.
- **One command type per use case**, no mode flags: a request the service must re-classify
  is several types sharing one class.
- **Domain errors.** One base per bounded context (`class OrderError(Exception)`), subclasses
  ending in `Error` (PEP 8). Wrap a lower-level cause with
  `raise OrderNotFoundError(order_id) from e`, so the traceback keeps it; `from None` only
  when hiding the cause is deliberate.
  Narrow `try` blocks, no bare `except`, never swallow. A failure that is an error raises;
  it never returns `None` or a status tuple. Adapters map domain errors to their transport in
  one place. No secrets or PII in messages or logs.

## Layout and wiring
- **Package by feature under `src/<pkg>/`**: `orders/` holds the domain types, ports and
  service; adapters sit beside it by mechanism (`orders/postgres.py`, `orders/http.py`, or a
  subpackage). No `ports/` or `adapters/` packages unless the house has them. `__all__`
  names a module's public surface; `_name` marks internals.
- **The consumer declares the port as a `Protocol`** (`class OrderStore(Protocol)` in the
  module that uses it). The adapter satisfies it structurally without importing it (PEP 544),
  so the dependency points inward for free; mypy checks the fit where the root passes it in.
  An ABC only when the port shares implementation. No bool-flag parameters; no ORM rows or
  pydantic models in port signatures.
- **Imports point inward.** The domain imports the stdlib and other domain modules only: no
  SQLAlchemy, pydantic, FastAPI or HTTP clients. On a project big enough to drift, pin it with
  an `import-linter` contract (`forbidden` or `layers`).
- **pydantic is an adapter type**: request and response models live in the HTTP adapter and
  map to and from domain dataclasses there, so validation of the wire shape never leaks into
  the domain. ORM models likewise stay in the persistence adapter.
- **The composition root is `main()`** (or `__main__.py`, or the app factory): it reads
  config, builds the adapters and passes them to constructors, so every dependency is visible
  in one place and a test can pass its own. No DI container, no module-level mutable state;
  FastAPI `Depends` only as the hook into what the root built.

## Stack right-sizing
Plain Python (an entrypoint + modules + pytest) for batch/CLI/reconciliation — most
take-homes. FastAPI only when it's genuinely a web service; don't reach for a framework
a script doesn't need. Same "invent nothing" rule as the architecture.

## Architecture
Hexagonal applies in Python when it earns it: pure domain (dataclasses, no framework
imports), ports and adapters as above only at a real boundary. Right-size per
`delivery-doctrine:ddd-hexagonal-reviewer` — a script rarely needs more than one port in
and one out.
