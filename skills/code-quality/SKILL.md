---
name: code-quality
description: Use when reviewing or refactoring Java code, or before merging a Java change —
  the review checklist for null safety, exception handling, resource management, naming,
  duplication and speculative abstraction, query performance (N+1, unbounded reads), and the
  API contract at the edge, with findings ranked Critical, Important or Minor. Triggers on
  "review code", "code review", "check this PR", "refactor", "clean this up", "check API".
---

<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Code Quality Review

Examples carry ✅/❌ labels to teach; delivered code carries none.

The Java review checklist. It owns null safety, exceptions, resources, naming and performance.
It defers on method decomposition and comments to `delivery-doctrine:readable-java-style` (no
comments; a long but clear method is not a smell), on domain types and transactions to
`delivery-doctrine:java-domain`, and on HTTP depth to `delivery-doctrine:spring-boot`'s
`references/web.md`. The architecture itself is `delivery-doctrine:ddd-hexagonal-reviewer`'s call.

Read the change for intent first, house names and structure before these rules; then walk only
the categories it touches and report as below.

## Duplication and speculative structure
- **One rule, one keeper.** The same validation in two services is one value object whose
  compact constructor keeps the invariant (`record Email(String value)`, per `java-domain`),
  not a shared `EmailValidator` both remember to call.
- **No abstraction without a second case.** A factory interface with one implementation, a
  `ConfigurableXFactoryProvider`, an option nothing sets: flag it. Build it when the second
  case arrives.
- **Magic values get a name** (`SESSION_TTL = Duration.ofDays(1)`, not `86400`).

## Null safety
Decide the contract first: is absence an error, or a modelled outcome? Then make the code say so.

```java
// ❌
String name = Optional.ofNullable(user.name()).map(String::toUpperCase).orElse("");

// ✅
public record Customer(CustomerId id, String name) {
    public Customer {
        Objects.requireNonNull(id);
        Objects.requireNonNull(name);
    }
}

// ✅
Optional<Customer> findById(CustomerId id);
```
- A required value is checked once, where it enters (a compact constructor, the edge DTO's
  `@NotNull`), so the rest of the code never re-checks it. A silent default (`""`, `0`,
  `List.of()` for "unknown") hides the bug the null was reporting.
- Flags: chained calls through values that can be absent; `Optional.get()` without a proven
  presence (use `orElseThrow`); a method returning `null` for "none" instead of `Optional` or an
  empty collection; `Optional` as a field or parameter; nullness on a public API left implicit
  where the house uses annotations (JSpecify `@Nullable` in Spring Framework 7 code).

## Exceptions
```java
// ❌
catch (IOException e) {
    throw new RuntimeException(e.getMessage());
}

// ✅
catch (IOException e) {
    throw new StatementImportException(file, e);
}
```
- Flags: an empty `catch`; catching `Exception` or `Throwable` outside the one edge handler; a
  new exception without the cause; log-and-rethrow (the failure logged twice: log once, where
  it is handled); a checked exception wrapped in a generic `RuntimeException` rather than the
  context's domain exception (`java-domain`).

## Resources
Anything `AutoCloseable` (streams, JDBC objects, clients, executors on Java 19+) opens in
try-with-resources, so it closes on every path; a manual `close()` after the work leaks when
the work throws.

## Naming
Names say intent: `findActiveCustomersByRegion`, `isWithinCreditLimit`, `activate`; never
`get(String s)`, `check`, `doStuff`, `data2`. One casing convention per kind; a name that needs
a comment to explain it gets renamed (`readable-java-style`).

## Performance
```java
// ❌
for (Customer customer : customers) {
    orders.addAll(orderRepository.findByCustomerId(customer.id()));
}

// ✅
@EntityGraph(attributePaths = "lines")
List<OrderEntity> findByCustomerIdIn(Collection<UUID> customerIds);
```
- Flags: a query per loop iteration (N+1: fetch join, `@EntityGraph` or one `IN` query); an
  unbounded `findAll()` on a table that grows (page or stream it); a filter column with no
  index; a remote call inside a transaction (`java-domain`). Fetch and query depth:
  `spring-boot`'s `references/data.md`.

## Transactions and the API contract
- **One unit of work per port call**, owned by the persistence adapter; several writes that
  must commit together go through one adapter method or the `Transactions` port
  (`java-domain`). `@Transactional` on a controller or a domain type is a finding.
- **The edge contract**: verbs keep their semantics (no `GET` that changes state, no `POST` to
  read), statuses say the outcome (201 with `Location`, 204, 404, 409), errors leave as
  `ProblemDetail`, request and response records never JPA entities, and no API version nobody
  asked for. Depth: `spring-boot`'s `references/web.md`.

## Report
Use the critic agent's Output shape: a verdict, then findings most
severe first, each with file:line, the defect, what it breaks and the fix, then what to keep.
- **Critical**: security, data loss or a crash path; blocks the merge.
- **Important**: wrong or brittle behaviour, a swallowed error, copied logic, an N+1 on a hot
  path; fixed before the merge.
- **Minor**: naming, a magic value, polish; the author's call.
- **Keep**: what is done well (constructor injection, records at the edge, a behaviour pinned
  by a given_when_then test), so the fix pass leaves it alone.
