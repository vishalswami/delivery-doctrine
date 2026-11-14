---
name: concurrency-review
description: Review Java concurrency code for thread safety, race conditions, deadlocks, and modern patterns (Virtual Threads, CompletableFuture, @Async). Use when user asks "check thread safety", "concurrency review", "async code review", or when reviewing multi-threaded code.
---

<!-- Adapted from decebals/claude-code-java (MIT); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Concurrency Review Skill

Examples carry ✅/❌ labels to teach; delivered code carries none.

Review Java concurrent code for correctness, safety, and modern best practices.

## Why This Matters

Concurrency bugs are:
- **Hard to reproduce** - timing-dependent
- **Hard to test** - may only appear under load
- **Hard to debug** - non-deterministic behavior

This skill helps catch issues **before** they reach production.

## When to Use
- Reviewing code with `synchronized`, `volatile`, `Lock`
- Checking `@Async`, `CompletableFuture`, `ExecutorService`
- Validating thread safety of shared state
- Reviewing Virtual Threads / Structured Concurrency code
- Any code accessed by multiple threads

---

## Modern Java (21/25): Virtual Threads

### When to Use Virtual Threads

```java
// ✅ Perfect for I/O-bound tasks (HTTP, DB, file I/O)
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (Request request : requests) {
        executor.submit(() -> callExternalApi(request));
    }
}

// ❌ Not beneficial for CPU-bound tasks: use platform threads or a ForkJoinPool
```

**Rule of thumb**: If your app never has 10,000+ concurrent tasks, virtual threads may not provide significant benefit.

### Java 25: Synchronized Pinning Fixed

In Java 21-23, virtual threads became "pinned" when entering `synchronized` blocks with blocking operations. **Java 25 fixes this** (JEP 491).

```java
// ❌ Java 21-23: blocking inside synchronized pins the virtual thread to its carrier
synchronized (lock) {
    blockingIoCall();
}
```

Java 25 no longer pins here; `ReentrantLock` still gives explicit control.

### ScopedValue Over ThreadLocal

```java
// ❌ ThreadLocal problematic with virtual threads
private static final ThreadLocal<User> currentUser = new ThreadLocal<>();

// ✅ ScopedValue (Java 21+ preview, improved in 25)
private static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

ScopedValue.where(CURRENT_USER, user).run(() -> processRequest());
```

`CURRENT_USER.get()` is available inside `processRequest()` and in child virtual threads.

### Structured Concurrency (Java 25 Preview)

```java
// ✅ Structured concurrency - tasks tied to scope lifecycle
try (StructuredTaskScope.ShutdownOnFailure scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(id));
    Subtask<Orders> ordersTask = scope.fork(() -> fetchOrders(id));

    scope.join();
    scope.throwIfFailed();

    return new Profile(userTask.get(), ordersTask.get());
}
```

`join()` waits for every subtask, `throwIfFailed()` propagates the first failure, and leaving
the scope cancels whatever is still running.

---

## Spring @Async Pitfalls

### 1. Forgetting @EnableAsync

```java
// ❌ @Async silently ignored
@Service
public class EmailService {
    @Async
    public void sendEmail(String to) { }
}

// ✅ Enable async processing
@Configuration
@EnableAsync
public class AsyncConfig { }
```

### 2. Calling Async from Same Class

```java
@Service
public class OrderService {

    // ❌ A direct call bypasses the proxy: it runs synchronously
    public void processOrder(Order order) {
        sendConfirmation(order);
    }

    @Async
    public void sendConfirmation(Order order) { }
}

// ✅ Call through another bean (a separate service, or an injected self): the proxy applies @Async
@Service
public class OrderService {
    private final EmailService emailService;

    public OrderService(EmailService emailService) {
        this.emailService = emailService;
    }

    public void processOrder(Order order) {
        emailService.sendConfirmation(order);
    }
}
```

### 3. @Async on Non-Public Methods

```java
// ❌ Non-public methods - proxy can't intercept
@Async
private void processInBackground() { }

@Async
protected void processInBackground() { }

// ✅ Must be public
@Async
public void processInBackground() { }
```

### 4. Default Executor Creates Thread Per Task

```java
// ❌ Default SimpleAsyncTaskExecutor: a new thread per task, OutOfMemoryError under load

// ✅ Configure proper thread pool
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(new CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

### 5. SecurityContext Not Propagating

```java
// ❌ SecurityContextHolder is ThreadLocal-bound: its context is empty on the async thread
@Async
public void auditAction() {
    String user = SecurityContextHolder.getContext().getAuthentication().getName();
}

// ✅ Use DelegatingSecurityContextAsyncTaskExecutor
@Bean
public Executor taskExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.initialize();
    return new DelegatingSecurityContextAsyncTaskExecutor(executor);
}
```

### 6. OSIV + async @Transactional → pool-exhaustion deadlock

`spring.jpa.open-in-view` is ON by default and binds a DB connection to the whole HTTP
request. An async or nested `@Transactional` operation then needs a SECOND connection
while the first is still held. Under concurrency, N threads each holding one connection
and waiting for another exhaust the pool and deadlock — the symptom is a test that hangs
until timeout, not an error.

Turn it off; it is the recommended production setting anyway, and Spring logs a warning
when it is left unset:

```properties
spring.jpa.open-in-view=false
```

One connection per operation, taken and released. On any hang, `jstack` the process — the
pool deadlock shows up immediately instead of costing a full timeout.

---

## CompletableFuture Patterns

### Error Handling

```java
// ❌ Exception silently swallowed: if riskyOperation throws, nobody knows
CompletableFuture.supplyAsync(() -> riskyOperation());

// ✅ Always handle exceptions
CompletableFuture.supplyAsync(() -> riskyOperation())
    .exceptionally(ex -> {
        log.error("Operation failed", ex);
        return fallbackValue;
    });

// ✅ Or use handle() for both success and failure
CompletableFuture.supplyAsync(() -> riskyOperation())
    .handle((result, ex) -> {
        if (ex != null) {
            log.error("Failed", ex);
            return fallbackValue;
        }
        return result;
    });
```

### Timeout Handling (Java 9+)

```java
// ✅ Fail after timeout with a TimeoutException
CompletableFuture.supplyAsync(() -> slowOperation())
    .orTimeout(5, TimeUnit.SECONDS);

// ✅ Return default after timeout
CompletableFuture.supplyAsync(() -> slowOperation())
    .completeOnTimeout(defaultValue, 5, TimeUnit.SECONDS);
```

### Combining Futures

```java
// ✅ Wait for all
CompletableFuture.allOf(future1, future2, future3)
    .thenRun(() -> log.info("All completed"));

// ✅ Wait for first
CompletableFuture.anyOf(future1, future2, future3)
    .thenAccept(result -> log.info("First result: {}", result));

// ✅ Combine results
future1.thenCombine(future2, (r1, r2) -> merge(r1, r2));
```

### Use Appropriate Executor

```java
// ❌ CPU-bound task in ForkJoinPool.commonPool (default)
CompletableFuture.supplyAsync(() -> cpuIntensiveWork());

// ✅ Custom executor for blocking/I/O operations
ExecutorService ioExecutor = Executors.newFixedThreadPool(20);
CompletableFuture.supplyAsync(() -> blockingIoCall(), ioExecutor);

// ✅ In Java 21+, virtual threads for I/O
ExecutorService virtualExecutor = Executors.newVirtualThreadPerTaskExecutor();
CompletableFuture.supplyAsync(() -> blockingIoCall(), virtualExecutor);
```

---

## Classic Concurrency Issues

### Race Conditions: Check-Then-Act

```java
// ❌ Race condition: another thread may add the key between the check and the put
if (!map.containsKey(key)) {
    map.put(key, computeValue());
}

// ✅ Atomic operation
map.computeIfAbsent(key, k -> computeValue());

// ❌ Race condition with counter: read-check-write is not atomic
if (count < MAX) {
    count++;
}

// ✅ Atomic counter
AtomicInteger count = new AtomicInteger();
count.updateAndGet(c -> c < MAX ? c + 1 : c);
```

### Visibility: Missing volatile

```java
// ❌ Other threads may never see the update, so run() may loop forever
private boolean running = true;

public void stop() {
    running = false;
}

public void run() {
    while (running) { }
}

// ✅ Volatile ensures visibility
private volatile boolean running = true;
```

### Non-Atomic long/double

```java
// ❌ 64-bit read/write is non-atomic on 32-bit JVMs, and counter++ is never atomic
private long counter;

public void increment() {
    counter++;
}

// ✅ Use AtomicLong or synchronization
private AtomicLong counter = new AtomicLong();

// ✅ Or volatile (for single-writer scenarios)
private volatile long counter;
```

### Double-Checked Locking

```java
// ❌ Broken without volatile: another thread may see a partially constructed instance
private static Singleton instance;

public static Singleton getInstance() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) {
                instance = new Singleton();
            }
        }
    }
    return instance;
}

// ✅ Correct with volatile
private static volatile Singleton instance;

// ✅ Or use holder class idiom
private static class Holder {
    static final Singleton INSTANCE = new Singleton();
}

public static Singleton getInstance() {
    return Holder.INSTANCE;
}
```

### Deadlocks: Lock Ordering

```java
// ❌ Potential deadlock: transfer(a, b) locks A then B while transfer(b, a) locks B then A
public void transfer(Account from, Account to, int amount) {
    synchronized (from) {
        synchronized (to) {
            from.withdraw(amount);
            to.deposit(amount);
        }
    }
}

// ✅ Consistent lock ordering
public void transfer(Account from, Account to, int amount) {
    Account first = from.getId() < to.getId() ? from : to;
    Account second = from.getId() < to.getId() ? to : from;

    synchronized (first) {
        synchronized (second) {
            from.withdraw(amount);
            to.deposit(amount);
        }
    }
}
```

---

## Thread-Safe Collections

### Choose the Right Collection

| Use Case | Wrong | Right |
|----------|-------|-------|
| Concurrent reads/writes | `HashMap` | `ConcurrentHashMap` |
| Frequent iteration | `ConcurrentHashMap` | `CopyOnWriteArrayList` |
| Producer-consumer | `ArrayList` | `BlockingQueue` |
| Sorted concurrent | `TreeMap` | `ConcurrentSkipListMap` |

### ConcurrentHashMap Pitfalls

```java
// ❌ Non-atomic compound operation
if (!map.containsKey(key)) {
    map.put(key, value);
}

// ✅ Atomic
map.putIfAbsent(key, value);
map.computeIfAbsent(key, k -> createValue());

// ❌ Nested compute on the same map can deadlock
map.compute(key1, (k, v) -> {
    return map.compute(key2, ...);
});
```

---

## Concurrency Review Checklist

### 🔴 High Severity (Likely Bugs)
- [ ] No check-then-act on shared state without synchronization
- [ ] No `synchronized` calling external/unknown code (deadlock risk)
- [ ] `volatile` present for double-checked locking
- [ ] Non-volatile fields not read in loops waiting for updates
- [ ] `ConcurrentHashMap.compute()` doesn't call other map operations
- [ ] @Async methods are public and called from different beans

### 🟡 Medium Severity (Potential Issues)
- [ ] Thread pools properly sized and named
- [ ] CompletableFuture exceptions handled (exceptionally/handle)
- [ ] SecurityContext propagated to async tasks if needed
- [ ] `ExecutorService` properly shut down
- [ ] `Lock.unlock()` in finally block
- [ ] Thread-safe collections used for shared data

### 🟢 Modern Patterns (Java 21/25)
- [ ] Virtual threads used for I/O-bound concurrent tasks
- [ ] ScopedValue considered over ThreadLocal
- [ ] Structured concurrency for related subtasks
- [ ] Timeouts on CompletableFuture operations

### 📝 Rationale (no comments — see readable-java-style)
- [ ] Thread-safety expectations pinned by tests or an ADR, not comments
- [ ] Locking order for nested locks recorded in an ADR
- [ ] Each `volatile` justified by a test or an ADR

---

## Analysis Commands

In order: `synchronized` blocks, `@Async` methods, `volatile` fields, thread pool creation,
`CompletableFuture` chains without error handling, and `ThreadLocal` (consider `ScopedValue`
on Java 21+).

```bash
grep -rn "synchronized" --include="*.java"
grep -rn "@Async" --include="*.java"
grep -rn "volatile" --include="*.java"
grep -rn "Executors\.\|ThreadPoolExecutor\|ExecutorService" --include="*.java"
grep -rn "CompletableFuture\." --include="*.java" | grep -v "exceptionally\|handle\|whenComplete"
grep -rn "ThreadLocal" --include="*.java"
```
