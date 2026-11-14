# Go concurrency and security

Read when the slice spawns goroutines or takes untrusted input. Concurrency only when it earns
it (`delivery-doctrine:go-style`); a sequential loop is the default.

## Goroutines: owned, cancellable, waited for

- **Whoever starts a goroutine owns its end.** It stops when its `ctx` is cancelled, and the
  owner waits for it before returning. A function that returns while its goroutine runs on
  leaks it; a type that starts one in its constructor offers `Close` or `Run(ctx)`, and `Run`
  is the better shape because the caller owns the lifetime.
- **Loops select on `ctx.Done()`** beside every blocking send or receive, so cancellation
  reaches them.
- **Fan-out uses `errgroup`** (`golang.org/x/sync/errgroup`). `WithContext` cancels the derived
  context when the first function returns an error; `Wait` returns that error after every
  goroutine has returned; `SetLimit` bounds how many run at once.

```go
func (s *Service) RefreshAll(ctx context.Context, ids []ID) error {
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(8)
	for _, id := range ids {
		g.Go(func() error {
			return s.refresh(ctx, id)
		})
	}
	return g.Wait()
}
```

- **Channel direction is in the signature.** A producer takes `chan<- T`, a consumer `<-chan T`,
  so the compiler stops a receiver from sending or closing. The sender owns the channel and
  closes it; a receiver never closes.

```go
func produce(ctx context.Context, ids []ID, out chan<- ID) error {
	defer close(out)
	for _, id := range ids {
		select {
		case out <- id:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return nil
}
```

- **A mutex guards named fields**: an unexported `mu sync.Mutex` declared directly above the
  fields it guards, held for the shortest span, never copied (`go vet` copylocks catches it).
  Prefer a channel or `errgroup` result over shared state when either is simpler.
- **Verification**: `go test -race` once, at the end, on the packages with concurrency
  (`delivery-doctrine:go-testing`). `go.uber.org/goleak` (`goleak.VerifyTestMain(m)`) where the
  house uses it or a leak has bitten. On a hang, SIGQUIT dumps every goroutine
  (`delivery-doctrine:execution-hygiene`).

## Security

- **Dependencies**: `govulncheck ./...` once before the PR. It reports the vulnerabilities your
  code calls into, directly or not, and lists advisories in unreached code as informational;
  fix the first kind, weigh the second.
- **Static analysis**: `gosec` enabled in golangci-lint, run scoped like the other linters. A
  `//nolint:gosec // reason` names why the finding does not apply.
- **SQL is parameterized** (`$1`, `?`), never `fmt.Sprintf` into a query. A table or column name
  that varies comes from an allowlist in code.
- **Input is validated at the edge.** The adapter decodes into a DTO under a size limit
  (`http.MaxBytesReader`), then the domain constructor (`ParseX`, `NewX`) rejects bad shape
  before the service runs; the service never sees an unchecked string. An ID in a request is
  checked against the caller's ownership before use.
- **Servers set timeouts**: `ReadHeaderTimeout` at least (gosec G112), plus read and write
  timeouts where the handlers allow.
- **HTML through `html/template`**, which escapes by context; `text/template` never renders
  user input as HTML.
- **Commands without a shell**: `exec.CommandContext(ctx, "git", "log", ref)`, never
  `sh -c` with input in the string.
- **Randomness for tokens from `crypto/rand`** (`rand.Text()` on Go 1.24+); `math/rand` is for
  simulations.
- **Secrets come from the environment or a secret manager**, read once in `main` and passed in.
  They are never logged: a `Secret` type whose `LogValue() slog.Value` returns a redaction keeps
  them out of structured logs by construction.
