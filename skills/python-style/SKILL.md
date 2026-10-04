---
name: python-style
description: Use when writing or reviewing Python — enforces type hints (mypy-clean),
  dataclasses/NamedTuple for value objects, small typed functions, guard clauses, zero
  comments, and formatting delegated to ruff/black. The Python profile's clean-code
  depth; pairs with pytest-testing. Loads at implementation time for Python work.
---

# Python Style

The Python quality profile. Loaded at implementation time for Python work (the language
is chosen after the grill, per right-sizing — the grill and slicing are language-agnostic).
Pairs with `delivery-doctrine:pytest-testing`.

## Rules
- **Type hints everywhere.** Annotate every function signature and non-trivial local;
  aim mypy-clean. Types are Python's real type system — use them, don't skip them.
- **Value objects as `@dataclass(frozen=True)` or `NamedTuple`** — immutable, typed. No
  bare dicts standing in for domain types. Keep the domain free of framework imports.
- **Small, single-responsibility functions**; guard clauses and early returns over deep
  nesting. A clear 20-line function is not a smell; don't reflexively split it.
- **No inline comments** — zero, in production and tests (CLAUDE.md hard rule). A
  one-line docstring on a public API documents the contract (the Python analog of
  godoc); a non-obvious WHY goes to an ADR or a test name — never a docstring or an
  inline comment. Names carry the what.
- **On a hang:** `py-spy dump --pid <pid>` names the stuck stack in seconds (see
  `delivery-doctrine:execution-hygiene`).
- **No magic values** — name constants.
- **Formatting delegated** to ruff/black; don't hand-format. Lint with ruff on the
  files you touched (`ruff check <paths>`), per `delivery-doctrine:execution-hygiene`.
- **Errors:** raise typed, meaningful exceptions; never swallow; no secrets or PII in
  messages or logs.

## Stack right-sizing
Plain Python (an entrypoint + modules + pytest) for batch/CLI/reconciliation — most
take-homes. FastAPI only when it's genuinely a web service; don't reach for a framework
a script doesn't need. Same "invent nothing" rule as the architecture.

## Architecture
Hexagonal applies in Python when it earns it: pure domain (dataclasses, no framework
imports), a port as a `Protocol` or ABC only at a real boundary, adapters implement it.
Right-size per `delivery-doctrine:ddd-hexagonal-reviewer` — a script rarely needs more than one port in
and one out.
