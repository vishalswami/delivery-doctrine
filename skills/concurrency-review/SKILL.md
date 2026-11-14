---
name: concurrency-review
description: Use when writing or reviewing Java code that runs on more than one thread —
  shared mutable state, race conditions (check-then-act, visibility), deadlocks and lock
  ordering, concurrent collections, virtual threads and pinning, ScopedValue, structured
  concurrency (preview StructuredTaskScope), CompletableFuture, Spring @Async and its executor,
  and the open-in-view connection-pool deadlock. Triggers on "thread safety", "concurrency
  review", "race condition", "deadlock", "async code review", synchronized, volatile, executors.
---

<!-- Adapted from decebals/claude-code-java (MIT); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Concurrency Review

Examples carry ✅/❌ labels to teach; delivered code carries none.

Concurrency only when it earns it; a sequential loop is the default. Its bugs are timing-
dependent, so a green run proves little: review the code, and pin each guarantee with a test
that forces the interleaving (a `CountDownLatch` or barrier holding two threads at the race).
On a hang, take a thread dump at once (`jcmd <pid> Thread.print` or `jstack <pid>`), per
`delivery-doctrine:execution-hygiene`. Read `references/async.md` when the change uses
`CompletableFuture`, `@Async` or an executor, or a Spring test hangs under load (the open-in-view
pool deadlock).

## Shared state
- **Immutable first.** Records and `final` fields (`delivery-doctrine:java-domain`) are safe to
  share; shared mutable state is the exception, and its guard is named.
- **Check-then-act is one atomic step.**

```java
// ❌
if (!cache.containsKey(key)) {
    cache.put(key, load(key));
}

// ✅
cache.computeIfAbsent(key, this::load);

// ✅
permits.updateAndGet(used -> used < MAX ? used + 1 : used);
```
  `count++` on a `long`, `int` or any field is a read-modify-write: `AtomicLong`, `LongAdder` for
  hot counters, or a lock.
- **Visibility**: a flag another thread reads in a loop is `volatile` or atomic, or it may never change.
- **Lazy initialisation**: the holder idiom; double-checked locking only on a `volatile` field.
- **`ConcurrentHashMap`**: compound operations through `compute`, `merge`, `putIfAbsent`; a
  remapping function never touches the same map (it can deadlock or throw), and stays short.
- **Locks**: `unlock()` in `finally`; no call to unknown code (listeners, callbacks, another
  service) while holding a lock; nested locks taken in one global order:

```java
// ✅
Account first = from.id().compareTo(to.id()) < 0 ? from : to;
Account second = first == from ? to : from;
synchronized (first) {
    synchronized (second) {
        from.withdraw(amount);
        to.deposit(amount);
    }
}
```

| Need | Not | Use |
|------|-----|-----|
| Shared map | `HashMap` | `ConcurrentHashMap` |
| Rare writes, many iterations | synchronized `ArrayList` | `CopyOnWriteArrayList` |
| Producer and consumer | `ArrayList` plus `wait` | `BlockingQueue` |
| Sorted and concurrent | `TreeMap` | `ConcurrentSkipListMap` |

## Virtual threads
- For blocking I/O, one per task: `Executors.newVirtualThreadPerTaskExecutor()` in
  try-with-resources, or `spring.threads.virtual.enabled=true` in Boot. CPU-bound work gains
  nothing; it belongs on a bounded platform pool.
- Never pool virtual threads. Limit concurrency against a scarce resource with a `Semaphore`.
- Pinning: since JDK 24 (JEP 491) `synchronized` no longer pins the carrier while blocked. A
  thread still pins when a native or FFM frame is on its stack and the Java callback blocks,
  when it blocks while loading a class, when it blocks inside a class initializer, and while it
  waits for a class another thread is initialising. On a house JDK before 24, blocking I/O
  inside `synchronized` pins: use a `ReentrantLock`. JFR's `jdk.VirtualThreadPinned` says why.
- `ThreadLocal` caches multiply with a thread per task. Request context goes in a `ScopedValue`:
  bound for a call, read with `get()`, inherited only by subtasks forked in a
  `StructuredTaskScope`, not by threads started through an executor.

```java
private static final ScopedValue<CustomerId> CALLER = ScopedValue.newInstance();

ScopedValue.where(CALLER, customerId).run(() -> placeOrder.handle(command));
```

## Structured concurrency (preview in Java 25 and 27, `--enable-preview`)
Subtasks that serve one result share one scope: it waits for them, fails on the first failure
and cancels the rest, so none outlives the method.

```java
try (var scope = StructuredTaskScope.open()) {
    Subtask<Customer> customer = scope.fork(() -> customers.byId(id));
    Subtask<List<Order>> orders = scope.fork(() -> orderHistory.of(id));

    scope.join();

    return new Profile(customer.get(), orders.get());
}
```
- `open()` uses `Joiner.awaitAllSuccessfulOrThrow()`; `join()` throws
  `StructuredTaskScope.FailedException` with the first failure as cause, and
  `InterruptedException`. Other policies: `Joiner.anySuccessfulResultOrThrow()` (first success
  wins), `allSuccessfulOrThrow()` (a stream of subtasks), `awaitAll()`, `allUntil(predicate)`.
- A deadline: `open(joiner, config -> config.withTimeout(Duration.ofSeconds(2)))`; expiry throws
  `StructuredTaskScope.TimeoutException`.
- The API above is Java 25's and changes each release: Java 27 adds an exception type parameter,
  `join()` throws `ExecutionException`, and `awaitAll()` is gone. Only where the house builds
  with preview on.

## Rationale and review
- No comments (`delivery-doctrine:readable-java-style`): a thread-safety guarantee is pinned by a
  test; a lock order or a deliberate `volatile` no test can show goes to an ADR.
- Critical: a race on money, stock or identity; a deadlock path; a swallowed async failure.
  Important: an unbounded queue or executor, a missing timeout, a lost security context.
  Report in the critic agent's Output shape. Where to look first:
  `grep -rnE "synchronized|volatile|ThreadLocal|@Async|Executors\.|CompletableFuture\." --include="*.java" src/main`
