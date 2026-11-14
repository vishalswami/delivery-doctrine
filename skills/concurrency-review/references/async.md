<!-- Adapted from decebals/claude-code-java (MIT); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Async: CompletableFuture, @Async, executors

Read when the change uses `CompletableFuture`, Spring `@Async` or an executor, or a Spring test
hangs under load. Examples carry ✅/❌ labels to teach; delivered code carries none.

## CompletableFuture
- **Every chain ends in handling.** A `supplyAsync` nobody joins or handles drops its exception
  silently. Handle it where the outcome is decided: `exceptionally` or `handle` for a real
  fallback, otherwise `join()` at the boundary so the failure propagates (as a
  `CompletionException` wrapping the cause). A fallback that hides an error the caller must see
  is a swallowed exception.

```java
// ❌
CompletableFuture.supplyAsync(() -> rates.fetch(currency));

// ✅
CompletableFuture.supplyAsync(() -> rates.fetch(currency), ioExecutor)
    .orTimeout(2, TimeUnit.SECONDS)
    .exceptionally(failure -> rates.lastKnown(currency));
```
- **Every remote call has a deadline**: `orTimeout` fails with a `TimeoutException`;
  `completeOnTimeout(value, ...)` substitutes a value where a default is the contract.
- **Combining**: `allOf(...)` then each `join()` for all results; `anyOf` for the first;
  `thenCombine` for two. Several subtasks that serve one result read better as a
  `StructuredTaskScope` where the house runs preview features (see the SKILL).
- **The executor is chosen, not defaulted.** Without one, async stages run on
  `ForkJoinPool.commonPool()`, sized for CPU work and shared by the whole JVM: blocking I/O there
  starves everyone. Pass an executor: virtual threads (`newVirtualThreadPerTaskExecutor()`) or a
  bounded pool for I/O, the common pool only for short CPU work.
- **Executors are shut down**: try-with-resources (`ExecutorService` is `AutoCloseable` since
  Java 19) or the owning bean's lifecycle; a pool created per call leaks threads.

## Spring @Async
- **`@EnableAsync`** on a `@Configuration` class, or `@Async` silently runs synchronously.
- **Through the proxy.** A call from the same class (`this.sendConfirmation(order)`) bypasses the
  proxy and runs on the caller's thread. Call it on another bean. The method is public: a private
  method is never intercepted.
- **The executor behind it.** In Boot, with no `Executor` bean of yours, `@Async` runs on the
  auto-configured `applicationTaskExecutor`: a `ThreadPoolTaskExecutor` with 8 core threads and an
  unbounded queue, so `max-size` never applies and a burst queues without limit. Bound it with
  `spring.task.execution.pool.queue-capacity` (then `max-size` takes effect) and name the threads
  (`spring.task.execution.thread-name-prefix`). With `spring.threads.virtual.enabled=true` it is a
  `SimpleAsyncTaskExecutor` on virtual threads. Defining your own `Executor` bean makes Boot's
  back off. Plain Spring without an executor bean falls back to `SimpleAsyncTaskExecutor`, a new
  thread per task: unbounded under load.
- **Failures of `void` methods** go to the `AsyncUncaughtExceptionHandler` (logged by default) and
  never reach the caller; a failure the caller must act on returns `CompletableFuture<T>`.
- **Context does not follow the thread.** `SecurityContextHolder` is thread-bound, so the async
  method sees no authentication: wrap the executor in `DelegatingSecurityContextAsyncTaskExecutor`,
  or better, pass the caller to the method as a value. Tracing and MDC context reach Boot's
  executor with `spring.task.execution.propagate-context=true`, or a `ContextPropagatingTaskDecorator`
  bean on an executor you build yourself.

## Open-in-view and the pool deadlock
`spring.jpa.open-in-view` is on by default (Boot logs a warning when it is unset) and holds a
connection for the whole request. A nested or async `@Transactional` call then needs a second
connection; N requests each holding one and waiting for another exhaust the pool, and the
symptom is a hang until timeout, not an error. Set `spring.jpa.open-in-view=false`: one
connection per unit of work, taken and released. A thread dump shows the deadlock at once.
