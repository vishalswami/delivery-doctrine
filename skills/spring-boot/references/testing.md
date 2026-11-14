<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Testing - Spring Boot Test

Read when the slice writes Spring tests. Shape and naming are `delivery-doctrine:test-first` and
`delivery-doctrine:gwt-testing` (`given_when_then`, blank-line phases, one act, no comments, no
`@DisplayName`); run them scoped (`delivery-doctrine:execution-hygiene`). Pick the smallest test
that can fail for the break you name:

| Break | Test |
|-------|------|
| A domain rule | Plain JUnit, no Spring, fakes for ports |
| Mapping, validation, status, error body, a security rule | `@WebMvcTest` |
| A query, a constraint, a conditional update, the entity mapping | `@DataJpaTest` on Testcontainers |
| The vertical end to end | `@SpringBootTest` with `RestTestClient` (`delivery-doctrine:acceptance-testing`) |

## Domain: no Spring
```java
class PlaceOrderServiceTest {
    private final List<Order> saved = new ArrayList<>();
    private final PlaceOrderService service = new PlaceOrderService(saved::add, FIXED_CLOCK);

    @Test
    void givenOrderWithoutLines_whenPlace_thenRefusedAndNothingSaved() {
        var command = new PlaceOrderCommand(CUSTOMER, List.of());

        var thrown = catchThrowable(() -> service.handle(command));

        assertThat(thrown).isInstanceOf(EmptyOrderException.class);
        assertThat(saved).isEmpty();
    }
}
```
A lambda or a small in-memory class fakes a port; Mockito is for the rare double whose
interaction is the contract (test-first, Honest tests).

## Web slice
```java
@WebMvcTest(OrderController.class)
@Import(SecurityConfig.class)
class OrderControllerTest {
    @Autowired MockMvcTester mvc;
    @MockitoBean PlaceOrder placeOrder;

    @Test
    @WithMockUser
    void givenNegativeQuantity_whenPost_thenBadRequestNamingTheField() {
        var body = """
            {"customerId":"7d3c1f9e-2b4a-4c1e-9f00-1a2b3c4d5e6f","lines":[{"sku":"A-1","quantity":-1}]}
            """;

        var result = mvc.post().uri("/orders").contentType(MediaType.APPLICATION_JSON).content(body);

        assertThat(result).hasStatus(HttpStatus.BAD_REQUEST)
            .bodyJson().extractingPath("$.errors['lines[0].quantity']").isNotNull();
    }
}
```
- `@WebMvcTest` comes from `org.springframework.boot.webmvc.test.autoconfigure` (module
  `spring-boot-webmvc-test`) and loads the controller, its advice and MVC configuration only; the
  use case is a `@MockitoBean` (`@MockBean` is removed in Boot 4). `MockMvcTester` (AssertJ) or
  `MockMvc` both work.
- With Jackson 3 the injected `ObjectMapper` is `tools.jackson.databind.ObjectMapper` (the
  auto-configured `JsonMapper`), and `writeValueAsString` throws the unchecked `JacksonException`. A literal JSON body, as above,
  also pins the wire format the client sends.
- Security rules: `security.md`, Testing.

## Persistence slice on a real database
```java
@DataJpaTest
@Testcontainers
@Import(JpaOrderStore.class)
class JpaOrderStoreTest {
    @Container
    @ServiceConnection
    static PostgreSQLContainer postgres = new PostgreSQLContainer("postgres:17-alpine");

    @Autowired JpaOrderStore store;
    @Autowired TestEntityManager entityManager;

    @Test
    void givenReleasedOrder_whenReleaseAgain_thenRefused() {
        store.place(placedOrder(ORDER_ID));
        store.release(ORDER_ID);
        entityManager.flush();

        var released = store.release(ORDER_ID);

        assertThat(released).isFalse();
    }
}
```
- Test against the database production runs, never H2: dialect, constraints, locking and native
  SQL differ. Flyway runs the real migrations into the container.
- `@ServiceConnection` (`org.springframework.boot.testcontainers.service.connection`) derives the
  connection from the container, replacing `@DynamicPropertySource`. Since Boot 3.4,
  `@AutoConfigureTestDatabase` defaults to `Replace.NON_TEST`, which leaves a `@ServiceConnection`
  DataSource alone, so no `replace = NONE` is needed.
- Testcontainers 2 moved modules to `org.testcontainers.<module>` packages with non-generic
  classes: `org.testcontainers.postgresql.PostgreSQLContainer` from artifact `testcontainers-postgresql`.
- `@DataJpaTest` runs each test in a rolled-back transaction: `flush()` (and `clear()` before a
  re-read) so the SQL and the constraints actually run.
- Several test classes share one container through a `@TestConfiguration` with a
  `@Bean @ServiceConnection` container method, imported where needed, so it starts once.

## The vertical
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
@Import(ContainersConfig.class)
class PlaceOrderAcceptanceTest {
    @Autowired RestTestClient client;

    @Test
    void givenValidOrder_whenPost_thenCreatedWithLocation() {
        var body = Map.of("customerId", CUSTOMER_ID, "lines", List.of(Map.of("sku", "A-1", "quantity", 2)));

        var response = client.post().uri("/orders").contentType(MediaType.APPLICATION_JSON).body(body).exchange();

        response.expectStatus().isCreated().expectHeader().exists("Location");
    }
}
```
Boot 4's `@SpringBootTest` configures no client by itself: `RestTestClient` (Spring Framework 7)
needs `@AutoConfigureRestTestClient` from `spring-boot-resttestclient`; `TestRestTemplate` needs
`@AutoConfigureTestRestTemplate`, `MockMvc` needs `@AutoConfigureMockMvc`, and `WebTestClient`
(for a WebFlux app, also used with `@WebFluxTest`) needs `@AutoConfigureWebTestClient`.

## Test configuration
```java
@TestConfiguration
class TestClockConfig {
    @Bean
    @Primary
    Clock fixedClock() {
        return Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
    }
}
```
Time comes from an injected `Clock`, fixed in tests. A `BCryptPasswordEncoder(4)` bean keeps
password hashing fast where tests hash at all.

## Practices
- No coverage target: each behaviour has a test that fails when it breaks.
- Assert outcomes; `verify` a mock only when the interaction is the contract.
- Clean data explicitly (`deleteAll` in `@BeforeEach`, a fresh container), not with `@Transactional`
  on a `@SpringBootTest`: its rollback skips the flush and commit, hiding their bugs.
- Test the whole range of each validated field, every security rule (401, 403, allowed), and the
  not-found and conflict paths; `@ParameterizedTest` for one rule over many inputs.
- Unit and slice tests stay fast and independent; the acceptance suite runs whole at the close.
