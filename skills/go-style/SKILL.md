---
name: go-style
description: Use when writing or reviewing Go — enforces idiomatic error wrapping,
  consumer-side interfaces at real boundaries, guard-clause happy path, zero inline
  comments (godoc one-liners on exported identifiers; directives exempt), formatting
  delegated to gofmt/golangci-lint. Pairs with go-testing.
---

# Go Style

The Go quality profile. Loaded at implementation time for Go work. Pairs with `delivery-doctrine:go-testing`.

## Rules
- **Formatting delegated** to gofmt/goimports (or `golangci-lint fmt` on v2 configs);
  lint with golangci-lint. Don't hand-format.
- **Errors are values.** Wrap with context: `fmt.Errorf("registering order: %w", err)` —
  `%w` only when callers should `errors.Is/As` through it (wrapping is API), else `%v`.
  Error strings: lower-case, no trailing punctuation, no "failed to" prefixes — the wrap
  chain reads as one sentence. Check every error; `_ =` needs a reason.
- **No `panic` for expected failures**, and never across an API boundary; `Must*` helpers
  at init and invariant violations are the exception.
- **Comments:** zero inline comments in bodies (names carry the what; WHY goes to an ADR
  or a test name). Godoc one-liners on exported identifiers are API documentation —
  write them, keep them one line. Compiler/tool directives (`//go:build`,
  `//go:generate`, `//go:embed`, `//nolint:<linter> // reason`) are code, not comments —
  never strip them; a `//nolint` must carry its reason.
- **Interfaces are ports, defined at the consumer.** Accept interfaces, return structs —
  Go's native right-sized hexagon: an interface only at a real boundary, only as big as
  the consumer needs (usually one to three methods; bigger needs a reason). No
  speculative interfaces.
- **Guard clauses; happy path left-aligned.** Early returns over nesting.
- **`context.Context` first param** for anything crossing a boundary (IO, RPC, DB).
- **Small structs as value objects**; make the zero value useful where natural.
- **Concurrency only when it earns it** — no goroutines/channels for structure's sake
  (race detector: see `delivery-doctrine:go-testing`).
- **On a hang:** send SIGQUIT (`kill -QUIT <pid>`) — the runtime dumps all goroutine
  stacks (see `delivery-doctrine:execution-hygiene`).
- **Package names:** short, lowercase, no stutter (`order.Service`, not
  `order.OrderService`).

## Stack right-sizing
A CLI or batch tool is a `main` + packages. For services, stdlib `http.ServeMux` is the
default (Go 1.22+: `mux.HandleFunc("GET /orders/{id}", ...)`, `r.PathValue("id")`); a
third-party router only if the house already uses one. Same "invent nothing" rule as the
architecture.
