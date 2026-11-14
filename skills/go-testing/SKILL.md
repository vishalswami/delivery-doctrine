---
name: go-testing
description: Use when writing or reviewing Go tests — the Go specialization of
  test-first. Table-driven tests with given/when/then case names, t.Parallel, hand-written
  fakes at ports with a contract test, mockery where the interaction is the contract,
  testify assertions, infra tests behind a build tag, -race once at the end.
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
- One naming convention per repository. Rename tests and sentinels with the API they test,
  in the same commit: a test named for a function that no longer exists misleads.

## Table-driven tests
Each case is one behavior: the name reads given/when/then, the fields are the Given, the
loop body is one When + Then. Don't force unrelated behaviors into one table — two
tables beat one confused one. Call `t.Parallel()` in tests and subtests unless they
share mutable state; loop variables are per-iteration, so no `tt := tt` copy.

## Doubles — fakes at ports first
- **A hand-written fake is the default double** for a port the domain owns: an in-memory
  `fakeStore` that records what it was given as data (`placed []order.Order`). Assert the
  outcome (what was stored, what came back), never a call count.
- **mockery where the interaction is the contract** (the message sent is the behavior) or the
  port is wide or owned by a framework (a house on another generator, such as gomock, keeps
  it). v3, house-pinned: interfaces declared in
  `.mockery.yml`, one `mockery` run regenerates all; the v2 `--name` flag is removed. Never
  mock what you own inside the unit.
- **A contract test keeps the fake honest.** A fake shared across packages lives in a helper
  package beside the port (`order/ordertest`) with one suite,
  `ordertest.StoreContract(t, func(t *testing.T) order.Store { ... })`, run against the fake in
  `ordertest`'s own test and against the real adapter behind the integration tag below.

## Assertions
testify by default: `require` for preconditions that make the rest meaningless, `assert`
for outcome checks. It is a house choice over the Google style guide's plain
`if got != want { t.Errorf(...) }`; a repository profile that says otherwise wins. Never
`require` inside a spawned goroutine (`FailNow` only works on the test goroutine).

## Test files and infrastructure
- One act per test; a test that places and then releases is two tests.
- Split a test file past ~800 lines by behavior (`place_test.go`, `release_test.go`).
- A test that boots infrastructure (a database, a broker) sits behind `//go:build integration`
  or in its own package, so `go test ./internal/order` stays hermetic and fast; it runs with
  `go test -tags integration ./internal/order/postgres`.

## Helpers and cleanup
Test helpers take `*testing.T` and call `t.Helper()`; register teardown with `t.Cleanup`
(also `t.TempDir`, `t.Setenv`). `t.Context()` over `context.Background()`.

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
