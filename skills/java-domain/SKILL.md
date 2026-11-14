---
name: java-domain
description: Use when writing or reviewing a Java domain and its wiring — records as value
  objects with compact-constructor invariants, typed IDs, entities without setters, sealed
  outcomes, one domain exception base, package-by-feature with adapters in subpackages,
  @Configuration wiring, JPA entities as adapter types, ProblemDetail at the edge, ArchUnit
  dependency rules, Spotless and Error Prone. Pairs with spring-boot, readable-java-style
  and gwt-testing.
---

# Java Domain

The Java profile's domain and hexagon. `delivery-doctrine:spring-boot` shows Spring wiring;
this skill keeps Spring out of the domain. Loaded at implementation and review time for Java
work, beside `delivery-doctrine:readable-java-style` and `delivery-doctrine:gwt-testing`.

**Baseline: Java 25 (LTS)** for every Java skill here; Java 27 is the newest release. A feature
newer than 25 is named with its version; on an older house JDK, check before using one.

House names and structure first (`delivery-doctrine:ddd-hexagonal-reviewer`, applicability guard):
conform to the house's names, introduce what it lacks, name a plainly bad house rule rather than follow or bypass it.

## Domain types
- **Value objects are records.** The compact constructor checks the invariant and throws a
  domain exception, so an invalid instance never exists.

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(currency);
        if (amount.signum() < 0) {
            throw new NegativeAmountException(amount);
        }
    }
}
```
- **Typed IDs**: `record OrderId(UUID value)`, so a method taking two IDs cannot swap them.
- **Entities carry behaviour, not setters.** Identity by ID (`equals` and `hashCode` on it);
  fields that never change are `final`; a state change is an intention-named method that keeps
  the invariant (`order.pay(payment)`, not `order.setStatus(PAID)`), so the invariant has one
  keeper. A constructor or static factory validates creation. An aggregate root only where an
  invariant spans several objects.
- **Lifecycle state is one method** (`order.statusAt(now)`). A conditional `UPDATE … WHERE`
  in the adapter that enforces the same rule against a read-update-persist race is right; the
  method mirrors it and one test pins the two together.
- **Closed sets**: an `enum` with the behaviour on its constants. Outcomes that carry
  different data are a `sealed interface` of records, consumed with an exhaustive `switch`,
  so a new case breaks the build rather than a test.
- **Domain exceptions**: one unchecked base per bounded context
  (`OrderException extends RuntimeException`), subclasses named for the refusal. Wrap a cause
  with the cause constructor; log once, where the exception is handled, never log and rethrow.
- **No framework on domain types**: no `@Entity`, `@Service`, `@Component`, `@Transactional`,
  Jackson or Bean Validation annotations. Validation annotations belong on request DTOs.

## Layout and wiring
- **Package by feature.** `com.acme.orders` holds the domain types, its ports and the use-case
  services; each adapter is a subpackage named for its mechanism (`orders.web`,
  `orders.persistence`, `orders.messaging`), or sits where the house puts adapters.
- **Ports are plain interfaces in the domain package**, named for the domain's need
  (`OrderStore`, `PaymentGateway`) and implemented in an adapter. An inbound interface per use
  case where hexagonal is the house style (`delivery-doctrine:ddd-hexagonal-reviewer`).
- **`@Configuration` wires the domain** from outside it (`orders.config` or the application
  package). Domain services are plain classes built in `@Bean` methods
  (`PlaceOrderService placeOrder(OrderStore store, Clock clock)` returns
  `new PlaceOrderService(store, clock)`; the return type is `PlaceOrder` where that inbound
  port exists), so they carry no `@Service`.
- **The persistence adapter owns the transaction.** One port call is one unit of work:
  `@Transactional` on the adapter method (`JpaOrderStore.place`), never on a domain type. A
  use case spanning several port calls depends on a plain domain port, implemented in
  `orders.persistence` as `template.execute(status -> work.get())` on a `TransactionTemplate`,
  so the domain imports no Spring and the ArchUnit rule below holds:

```java
public interface Transactions {
    <T> T inTransaction(Supplier<T> work);

    default void inTransaction(Runnable work) {
        inTransaction(() -> { work.run(); return null; });
    }
}
```
  No remote call inside a transaction: it holds the connection for the call, and a commit
  that fails after the call succeeded leaves the remote side changed. Call after commit, or
  write an outbox row in the transaction.
- **JPA entities are adapter types.** `OrderEntity` in `orders.persistence` maps to and from
  the `Order` aggregate, so the domain never sees lazy proxies or setters. If the house maps
  JPA straight onto the aggregate, follow it and say so in the slice.
- **The edge speaks `ProblemDetail`** (RFC 9457, Spring 6+) unless the house has its own error
  body: one `@RestControllerAdvice` maps each domain exception to a status, so the mapping
  lives in one place. Request and response records live in `orders.web`, mapped by hand.
- **ArchUnit pins the direction**, run as an ordinary test:

```java
@AnalyzeClasses(packages = "com.acme.orders")
class OrdersArchitectureTest {
    @ArchTest
    static final ArchRule domainDependsOnNothingOutward = noClasses()
        .that().resideInAPackage("com.acme.orders")
        .should().dependOnClassesThat()
        .resideInAnyPackage("org.springframework..", "jakarta.persistence..",
            "com.acme.orders.web..", "com.acme.orders.persistence..");
}
```
  ArchUnit rules are named for the invariant they pin; GWT names are for `@Test` methods.

## Format and static analysis
Spotless with google-java-format or palantir-java-format, whichever the house pins
(`./mvnw spotless:apply -pl <module>`, `spotless:check` before commit; Gradle `spotlessApply`,
`spotlessCheck`). Error Prone in the compiler; Checkstyle, PMD or SpotBugs where the house runs
them. Scope every run to the slice's module, per `delivery-doctrine:execution-hygiene`.
