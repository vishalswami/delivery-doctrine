---
name: go-testing
description: Use when writing or reviewing Go tests — the Go specialization of
  test-first. Table-driven tests with given/when/then case names, t.Parallel,
  mockery mocks at ports only, testify assertions, -race once at the end on concurrent code.
---

# Go Testing

The Go specialization of `delivery-doctrine:test-first`. Everything there applies — blank-line
phases, one act per test, zero comments. Go specifics below.

## Naming
- Table-driven (the idiomatic default): `TestAuthenticate` with GWT case names —
  `t.Run("given expired token when authenticating then rejected", ...)`.
- Single-behavior unit only: `TestGivenExpiredToken_WhenAuthenticate_ThenRejected`.
- Default to the external test package (`package order_test`); same-package tests only
  when an unexported detail must be pinned.

## Table-driven tests
Each case is one behavior: the name reads given/when/then, the fields are the Given, the
loop body is one When + Then. Don't force unrelated behaviors into one table — two
tables beat one confused one. Call `t.Parallel()` in tests and subtests unless they
share mutable state; Go 1.22+ loop variables are per-iteration — no `tt := tt` copy.

## Mocks — mockery, at ports only
- mockery v3 (house-pinned): interfaces declared in `.mockery.yml`; one `mockery` run
  regenerates all. Never use the v2 per-interface `--name` flag — it's removed in v3.
  Mocks exist only at real boundaries (the port seam) — never mock what you own inside
  the unit; prefer real code (test behavior, not mocks).
- Assert outcomes, not call counts, unless the interaction IS the contract.

## Assertions
testify by default: `require` for preconditions that make the rest meaningless, `assert`
for outcome checks. It is a house choice over the Google style guide's plain
`if got != want { t.Errorf(...) }`; a repository profile that says otherwise wins. Never
`require` inside a spawned goroutine (`FailNow` only works on the test goroutine).

## Helpers and cleanup
Test helpers take `*testing.T` and call `t.Helper()`; register teardown with `t.Cleanup`
(also `t.TempDir`, `t.Setenv`). Go 1.24+: `t.Context()` over `context.Background()`.

## The loop
- Run only the test you're on, by name: `go test -run '^TestAuthenticate$/given_expired_token' ./path/to/pkg`
  (subtest names match with spaces as underscores). Never `./...` or a whole package as
  the red/green loop — scope per `delivery-doctrine:execution-hygiene`.
- The race detector is not optional for concurrent code, and runs once, at the end, on
  the packages that have it: `go test -race ./path/to/pkg` — not on every iteration.
- Acceptance tests: exercise the fully wired router via `httptest.NewServer` (or
  `NewRecorder` per request); stub external HTTP dependencies with their own
  `httptest.NewServer`, per `delivery-doctrine:acceptance-testing`. For CLIs, test an exported
  `run(args, stdout, stderr) error` — keep `main` a one-liner.
