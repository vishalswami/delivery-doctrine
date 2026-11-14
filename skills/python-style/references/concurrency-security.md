# Python concurrency and security

Read when the slice adds async code or threads, or takes untrusted input. Synchronous code is
the default; asyncio earns its place only when the work is many concurrent I/O waits.

## asyncio discipline

- **No blocking call in async code.** `time.sleep`, `requests`, a synchronous database driver,
  file reads and CPU-heavy work stall the whole event loop, so every other task waits. Use the
  async library (`httpx.AsyncClient`, `asyncpg`, psycopg's async connection) or move the call
  off the loop with `await asyncio.to_thread(render_pdf, order)`. Ruff's `ASYNC` rules flag the
  common cases; `asyncio.run(main(), debug=True)` logs any callback slower than 100 ms.
- **Fan-out uses `asyncio.TaskGroup`** (3.11+). The first task to fail cancels the rest, and the
  failures arrive together as an `ExceptionGroup`, handled with `except*`. The group keeps
  strong references and awaits every task; a bare `create_task` whose result is dropped can be
  garbage-collected mid-run and its exception lost.

```python
async def refresh_all(order_ids: Sequence[OrderId]) -> None:
    async with asyncio.timeout(30):
        async with asyncio.TaskGroup() as group:
            for order_id in order_ids:
                group.create_task(refresh(order_id))
```

- **Bound the concurrency** with an `asyncio.Semaphore` when the far side has a limit.
- **Cancellation propagates.** `asyncio.timeout` (3.11+) cancels the block and raises
  `TimeoutError` outside it. `CancelledError` derives from `BaseException`, so `except Exception`
  does not catch it; code that catches it explicitly cleans up and re-raises, because
  `TaskGroup` and `timeout` rely on it arriving.
- **Tests** run async code under the house's plugin (`pytest-asyncio` or anyio's).

## Threads

- Shared mutable state sits behind a `threading.Lock` owned by the object that holds the state;
  no module-level mutable state.
- `concurrent.futures.ThreadPoolExecutor` as a context manager, so its threads are joined on
  exit; iterating `executor.map` or calling `future.result()` re-raises a worker's exception,
  so collect every result.

## Security

- **Static analysis**: `bandit -r src`, or ruff's `S` rules (its port of bandit's checks) in the
  lint run already scoped to the touched files. Fix the call over suppressing it; when a finding
  does not apply, the suppression names the exact code (`# noqa: S603`), never a bare `noqa`.
- **Dependencies**: `pip-audit` against the environment or the lock/requirements file, once
  before the PR.
- **SQL is parameterized** (`%s` for psycopg, `?` for sqlite3, bound parameters in SQLAlchemy),
  never an f-string or `%` into the query. A table or column name that varies comes from an
  allowlist in code.
- **Input is validated at the edge.** The adapter parses the wire shape with pydantic, then the
  domain constructor rejects bad values before the service runs; the service never sees an
  unchecked dict. An ID in a request is checked against the caller's ownership before use.
  Request size limits sit at the server or proxy.
- **Subprocesses take a list** (`subprocess.run(["git", "log", ref], check=True)`), never
  `shell=True` with input in the string.
- **No `pickle`, `marshal` or `yaml.load` on untrusted data**; `yaml.safe_load` and JSON are the
  parsers for input.
- **Tokens come from `secrets`** (`secrets.token_urlsafe()`); `random` is for simulations.
- **Secrets come from the environment or a secret manager**, read once in the composition root
  and passed in, never logged; `pydantic.SecretStr` keeps them out of reprs and logs.
