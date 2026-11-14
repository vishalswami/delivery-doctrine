---
name: spring-boot
description: Use when building or changing a Spring Boot 4 service — Spring wiring of the
  java-domain hexagon (@Configuration beans, constructor injection), REST controllers with
  record DTOs and ProblemDetail, Spring Data JPA persistence adapters and transactions, Spring
  Security 7, test slices (@WebMvcTest, @DataJpaTest, @MockitoBean) with Testcontainers,
  configuration, Actuator health, tracing and resilience, plus the Boot 4 migration facts
  (Jackson 3, modular starters, Spring Framework 7). Pairs with java-domain.
---

<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Spring Boot

Examples carry ✅/❌ labels to teach; delivered code carries none.

How Spring wires a Java service. The domain, its layout and where transactions live are
`delivery-doctrine:java-domain`'s; architecture is `delivery-doctrine:ddd-hexagonal-reviewer`'s;
house names and structure come first. This skill keeps Spring at the edges.

## Stack right-sizing
Plain Java (a `main` + packages, JUnit, Maven) for CLI, batch and take-home tools: don't pay
framework startup for a file-in, report-out problem. Spring Boot only when it is genuinely a web
service. Same "invent nothing" rule as the architecture.

## Wiring the hexagon
Package by feature as `java-domain` lays it out: `orders` holds the domain and its ports,
`orders.web`, `orders.persistence` and `orders.config` the Spring parts. No `controller/`,
`service/`, `repository/`, `model/` tree, and no anemic entity with setters.

```java
@Configuration
class OrdersConfig {
    @Bean
    PlaceOrder placeOrder(OrderStore store, Clock clock) {
        return new PlaceOrderService(store, clock);
    }
}

@RestController
@RequestMapping("/orders")
class OrderController {
    private final PlaceOrder placeOrder;

    OrderController(PlaceOrder placeOrder) {
        this.placeOrder = placeOrder;
    }

    @PostMapping
    ResponseEntity<OrderResponse> place(@Valid @RequestBody PlaceOrderRequest request) {
        Order order = placeOrder.handle(request.toCommand());
        return ResponseEntity.created(URI.create("/orders/" + order.id().value()))
            .body(OrderResponse.from(order));
    }
}
```
- Constructor injection only; one constructor needs no `@Autowired`. Domain services are built in
  `@Bean` methods, so they carry no `@Service`.
- Request and response records live in `orders.web`, carry the Bean Validation annotations, and map
  to and from domain types by hand.
- One `@RestControllerAdvice extends ResponseEntityExceptionHandler` maps each domain exception to
  a `ProblemDetail` (`references/web.md`).
- The persistence adapter (`JpaOrderStore` over a Spring Data repository of `OrderEntity`) owns
  `@Transactional` (`references/data.md`).
- Configuration binds into `@ConfigurationProperties` records, never scattered `@Value`
  (`references/operations.md`). Secrets come from the environment, never a committed file.

## Test loop
Test-first per `delivery-doctrine:test-first` and `delivery-doctrine:gwt-testing`. Run only the
tests you are on (`./mvnw test -Dtest='OrderControllerTest#given*'`; Gradle `--tests`), per
`delivery-doctrine:execution-hygiene`: the full suite is CI's. Start the app only when wiring
changed, and check `/actuator/health` answers UP. On a hang, `jstack` the process.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvcTester mvc;
    @MockitoBean PlaceOrder placeOrder;

    @Test
    void givenOrderOverCreditLimit_whenPost_thenConflictProblem() {
        given(placeOrder.handle(any())).willThrow(new CreditLimitExceededException(CUSTOMER));

        var result = mvc.post().uri("/orders").contentType(APPLICATION_JSON).content(ORDER_JSON);

        assertThat(result).hasStatus(HttpStatus.CONFLICT).hasContentType(APPLICATION_PROBLEM_JSON);
    }
}
```

## Defaults to hold
- `spring.jpa.open-in-view=false` (Boot warns when it is unset): open-in-view holds a connection
  per request and deadlocks the pool under nested or async transactions
  (`delivery-doctrine:concurrency-review`). `show-sql` off in the test loop.
- No blocking calls inside reactive code, and no WebFlux unless the house runs it.
- No hardcoded URLs, credentials or environment values; no deprecated Boot 2/3 APIs.

## Spring Boot 4 notes
- Baseline: Java 17+ (21 or 25 LTS recommended), Spring Framework 7, Jakarta EE 11 (Servlet 6.1), Spring Security 7, Spring Data 2025.1, Hibernate 7, JUnit Jupiter 6, Testcontainers 2
- Jackson 3 is the default: packages and group IDs move from `com.fasterxml.jackson` to `tools.jackson` (annotations stay in `com.fasterxml.jackson.annotation`); `@JsonComponent` is `@JacksonComponent`, `Jackson2ObjectMapperBuilderCustomizer` is `JsonMapperBuilderCustomizer`; to replace the mapper, define a `JsonMapper` bean. Jackson 3 no longer fails on unknown properties by default
- Modular starters: `spring-boot-starter-web` is `spring-boot-starter-webmvc`, `spring-boot-starter-oauth2-*` is `spring-boot-starter-security-oauth2-*`, `spring-boot-starter-aop` is `spring-boot-starter-aspectj`; Flyway and Liquibase need `spring-boot-starter-flyway` / `spring-boot-starter-liquibase`
- Test slices live in per-technology modules and packages: `@WebMvcTest` in `org.springframework.boot.webmvc.test.autoconfigure` (`spring-boot-webmvc-test`), `@DataJpaTest` in `org.springframework.boot.data.jpa.test.autoconfigure` (`spring-boot-data-jpa-test`), `@WebFluxTest` in `org.springframework.boot.webflux.test.autoconfigure`
- `@MockBean`/`@SpyBean` are removed: use `@MockitoBean`/`@MockitoSpyBean` on test-class fields (not in `@Configuration` classes)
- `@SpringBootTest` no longer provides `MockMvc`, `TestRestTemplate` or `WebTestClient` on its own: add `@AutoConfigureMockMvc`, `@AutoConfigureRestTestClient` (preferred, `RestTestClient`) or `@AutoConfigureTestRestTemplate`; for `WebTestClient`, `@AutoConfigureWebTestClient` (from `spring-boot-webflux-test`)
- `@EntityScan` is `org.springframework.boot.persistence.autoconfigure.EntityScan`; Actuator's `HealthIndicator`/`Health` are in `org.springframework.boot.health.contributor`
- Spring Framework 7 null safety uses JSpecify (`org.jspecify.annotations.Nullable`, `@NullMarked`); the `org.springframework.lang` annotations are deprecated
- Undertow is removed; Spring Retry is no longer version-managed (Framework 7 has `@Retryable` in core)
- Spring Cloud release train for Boot 4 is 2025.1.x (Oakwood); where the house runs Gateway 5, it is `spring-cloud-starter-gateway-server-webflux` (or `-webmvc`) with properties under `spring.cloud.gateway.server.webflux.*`, the old starter and `spring.cloud.gateway.*` prefix gone

## References
- `references/web.md` when the slice adds or changes an endpoint: HTTP contract, validation, `ProblemDetail`, outbound `RestClient`, CORS.
- `references/data.md` when it touches persistence: entity mapping, repositories, transactions, queries, Flyway.
- `references/security.md` when it configures authentication, authorization, CSRF, CORS or headers.
- `references/testing.md` when it writes Spring tests: slices, Testcontainers, `RestTestClient`, security tests.
- `references/operations.md` when it adds configuration, health, metrics, tracing or resilience on an outbound call.
