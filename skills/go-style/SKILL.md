---
name: go-style
description: Use when writing or reviewing Go — enforces idiomatic error wrapping,
  domain types that keep their own invariants, consumer-side interfaces at real boundaries,
  package-by-feature layout wired in main, guard-clause happy path, zero inline comments
  (godoc one-liners on exported identifiers; directives exempt), formatting delegated to
  gofmt/golangci-lint. Pairs with go-testing.
---

# Go Style

The Go quality profile. Loaded at implementation time for Go work. Pairs with `delivery-doctrine:go-testing`.

House names and structure first (`delivery-doctrine:ddd-hexagonal-reviewer`, applicability guard):
conform to the house's names, introduce what it lacks, name a plainly bad house rule rather than follow or bypass it.

## Rules
- **Formatting delegated** to gofmt/goimports (or `golangci-lint fmt` on v2 configs);
  lint with golangci-lint on the packages you touched (`golangci-lint run ./path/to/pkg/...`),
  and `go vet` the same packages after a rename or signature change — scope per
  `delivery-doctrine:execution-hygiene`. Don't hand-format.
- **Errors are values.** Wrap with context: `fmt.Errorf("registering order: %w", err)` —
  `%w` only when callers should `errors.Is/As` through it (wrapping is API), else `%v`.
  Error strings: lower-case, no trailing punctuation, no "failed to" prefixes — the wrap
  chain reads as one sentence. Check every error; `_ =` needs a reason.
- **No `panic` for expected failures**, and never across an API boundary; `Must*` helpers
  at init and invariant violations are the exception.
- **Comments:** zero inline comments in bodies (names carry the what; WHY goes to an ADR
  or a test name). Godoc one-liners on exported identifiers are API documentation —
  write them, keep them one line; a godoc paragraph defending a choice is a comment in
  disguise, so the WHY goes to the ADR or spec. Compiler/tool directives (`//go:build`,
  `//go:generate`, `//go:embed`, `//nolint:<linter> // reason`) are code, not comments —
  never strip them; a `//nolint` must carry its reason.
- **Interfaces are ports, defined at the consumer.** Accept interfaces, return structs —
  Go's native right-sized hexagon: an interface only at a real boundary, only as big as
  the consumer needs (usually one to three methods; bigger needs a reason). No
  speculative interfaces.
- **Guard clauses; happy path left-aligned.** Early returns over nesting.
- **`context.Context` first param** for anything crossing a boundary (IO, RPC, DB).
- **Concurrency only when it earns it** — no goroutines/channels for structure's sake
  (race detector: see `delivery-doctrine:go-testing`).
- **On a hang:** send SIGQUIT (`kill -QUIT <pid>`) — the runtime dumps all goroutine
  stacks (see `delivery-doctrine:execution-hygiene`).
- **Names:** packages short, lowercase, no stutter — `order.Service`, not `order.OrderService`,
  and `consumers.Bankruptcy`, not `consumers.BankruptcyConsumer`. Accessors carry no `Get`
  prefix (`o.Total()`).

## Domain types
- **Constructors keep the invariant.** When the zero value is not a valid X, its fields are
  unexported and `NewX(...) (X, error)` is the way in, so an invalid X cannot exist. It checks
  shape before any I/O; the service never re-checks it. A valid zero value stays useful.
- **Typed IDs and values.** `type OrderID string` stops a swapped argument at compile time.
  Value objects are small structs compared by value; a change returns a new value.
- **A closed set is a type with a Parse and behaviour**: `type Method string`, its consts,
  `ParseMethod(s string) (Method, error)` called once at the edge, and the classification as a
  method (`m.NeedsCreditCheck()`), so the rule sits on the value, not in a `map[Method]struct{}`
  and an `isX` helper elsewhere. An integer set uses `iota` and `String()`. A test that
  inspects source to prove a map covers every case says the set should be closed: an
  exhaustive `switch` (the `exhaustive` linter where the house runs it).
- **Entities carry their rules.** Identity by ID; state changes are pointer-receiver methods
  that keep the invariant; callers never set fields, so it has one keeper. Lifecycle state is
  one method taking `now` (`o.Status(now)`), so "open" has one definition in Go. A SQL guard
  enforcing the same rule atomically (`UPDATE … WHERE released_at IS NULL`, so no
  read-update-persist race) is right; the method mirrors it and one test pins the two together.
- **One command type per use case**, no mode flags: a request the service must re-classify
  (`if isOperator(req.Source)`) is several types sharing one struct.
- **Derived identity is data.** A parent ID or a provenance kind is a field or column, not a
  string prefix decoded elsewhere; if an encoding is forced, one type encodes and decodes it.
- **Domain errors.** `var ErrOrderNotFound = errors.New("order not found")` for conditions
  callers branch on; `type LimitError struct{...}` when it carries data. One refusal
  vocabulary per service: sentinels or an outcome type, mapped to the other in one function,
  never once per adapter. Adapters branch with `errors.Is/As`, never on the message.

## Layout and wiring
- **Package by feature**, under `internal/` when no other module should import it:
  `internal/order` holds domain types, ports and service; adapters are subpackages named for
  their mechanism (`order/postgres`, `order/httpapi`), not `ports/` and `adapters/` dirs.
- **The consumer declares the port**: `order.Store` lives in `order`, beside `order.Service`;
  `postgres.Store` satisfies it implicitly (`var _ order.Store = (*Store)(nil)` pins it). No
  bool parameters: `Release(ctx, r, true)` says nothing at the call site, so two methods. No
  persistence or wire types in signatures; they drag the adapter into the domain. Transaction
  scope is the adapter's; a caller that depends on it reads it in the method name, not godoc.
- **No inbound port by default.** Handlers and consumers hold the concrete `*order.Service`;
  an interface appears when a second implementation does.
- **Inbound adapters live in subpackages**, so the domain package carries no transport. One
  that needs an unexported rule gets it exported as a function, never an `export_test.go` leak.
- **The domain imports inward only**: the stdlib, other domain packages, value libraries such
  as `github.com/google/uuid`. No ORM models, no generated wire types, no framework helpers;
  event DTO builders live with the publisher. Pin it where the house runs golangci-lint;
  `allow` matches by prefix, so each domain package it may import is listed exact (`$`):

```yaml
linters:
  settings:
    depguard:
      rules:
        order-domain:
          list-mode: strict
          files: ["**/internal/order/*.go", "!$test"]
          allow: [$gostd, github.com/google/uuid, github.com/acme/shop/internal/money$]
```
- **`cmd/<app>/main.go` is the composition root**: it reads config, builds the adapters and
  passes them to constructors, so every dependency is visible in one place and a test can
  pass its own. No `init()` side effects, no package-level mutable state, no DI framework.

## Stack right-sizing
A CLI or batch tool is a `main` + packages. For services, stdlib `http.ServeMux` is the
default (Go 1.22+: `mux.HandleFunc("GET /orders/{id}", ...)`, `r.PathValue("id")`); a
third-party router only if the house already uses one. Same "invent nothing" rule as the
architecture.

## References
- `references/adapters.md` when the slice touches an adapter (store, HTTP, consumer).
- `references/concurrency-security.md` when it spawns goroutines or takes untrusted input.
