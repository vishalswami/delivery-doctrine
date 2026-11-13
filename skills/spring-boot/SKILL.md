---
name: spring-boot
description: Spring Boot 4.x development - REST APIs, JPA, Security, Testing, and Cloud-native patterns. Use for building enterprise Java applications with Spring Boot.
metadata:
  version: "2.0.0"
  domain: backend
  triggers: Spring Boot, Spring Framework, Spring Security, Spring Data JPA, Spring WebFlux, Java REST API, Microservices Java
  role: specialist
  scope: implementation
  output-format: code
---

<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Spring Boot Skill

Enterprise Spring Boot 4.x development with focus on clean architecture and production-ready code.

## Core Workflow

1. **Analyze** - Understand requirements, identify service boundaries, APIs, data models
2. **Design** - Plan architecture, confirm design before coding
3. **Implement** - Build with constructor injection and layered architecture
4. **Secure** - Add Spring Security, OAuth2, method security; verify tests pass
5. **Test** - Write unit, integration tests; run only the tests you wrote
   (`./mvnw test -Dtest='ProductControllerTest#givenValidRequest*'`; Gradle `--tests`),
   per `delivery-doctrine:execution-hygiene` — the full suite is CI's
6. **Deploy** - Configure health checks via Actuator; validate `/actuator/health` returns UP

## Quick Start Templates

### Entity
```java
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    private String name;

    @DecimalMin("0.0")
    private BigDecimal price;
}
```

### Repository
```java
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByNameContainingIgnoreCase(String name);
}
```

### Service
```java
@Service
@Transactional(readOnly = true)
public class ProductService {
    private final ProductRepository repo;

    public ProductService(ProductRepository repo) {
        this.repo = repo;
    }

    public List<Product> search(String name) {
        return repo.findByNameContainingIgnoreCase(name);
    }

    @Transactional
    public Product create(ProductRequest request) {
        var product = new Product();
        product.setName(request.name());
        product.setPrice(request.price());
        return repo.save(product);
    }
}
```

### REST Controller
```java
@RestController
@RequestMapping("/api/v1/products")
@Validated
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductResponse> search(@RequestParam(defaultValue = "") String name) {
        return service.search(name).stream().map(ProductResponse::from).toList();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductResponse create(@Valid @RequestBody ProductRequest request) {
        return ProductResponse.from(service.create(request));
    }
}
```

### DTO (Record)
```java
public record ProductRequest(
    @NotBlank String name,
    @DecimalMin("0.0") BigDecimal price
) {}

public record ProductResponse(Long id, String name, BigDecimal price) {
    static ProductResponse from(Product product) {
        return new ProductResponse(product.getId(), product.getName(), product.getPrice());
    }
}
```

### Global Exception Handler
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleValidation(MethodArgumentNotValidException ex) {
        return ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(FieldError::getField,
                    error -> error.getDefaultMessage() != null ? error.getDefaultMessage() : "Invalid"));
    }

    @ExceptionHandler(EntityNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Map<String, String> handleNotFound(EntityNotFoundException ex) {
        return Map.of("error", ex.getMessage());
    }
}
```

### Test Slice
```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean ProductService service;

    @Test
    void givenValidRequest_whenCreateProduct_thenReturns201() throws Exception {
        var product = new Product();
        product.setName("Widget");
        when(service.create(any())).thenReturn(product);

        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"Widget\",\"price\":10.0}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Widget"));
    }
}
```

## Reference Guide

Load detailed patterns based on context:

| Topic | Reference | When to Load |
|-------|-----------|-------------|
| Web/REST | `references/web.md` | Controllers, validation, exception handling |
| Data Access | `references/data.md` | JPA, repositories, transactions, queries |
| Security | `references/security.md` | Spring Security 7, OAuth2, JWT, auth |
| Cloud/Config | `references/cloud.md` | Config server, discovery, resilience |
| Testing | `references/testing.md` | Unit, integration, slice tests, Testcontainers `@ServiceConnection` |

## Constraints

### MUST DO
- Constructor injection (no field injection)
- `@Valid` on all request bodies
- `@Transactional` for multi-step writes
- `@Transactional(readOnly = true)` for reads
- Type-safe config with `@ConfigurationProperties`
- Global exception handling with `@RestControllerAdvice`
- Externalize secrets (use env vars, not properties files)
- Set `spring.jpa.open-in-view=false` (Spring warns if unset) and disable `show-sql` in
  the test loop. OSIV binds a DB connection to the whole request — see
  `delivery-doctrine:concurrency-review` for the deadlock it causes. On a hang, `jstack` the process.

### MUST NOT DO
- Field injection (`@Autowired` on fields)
- Skip input validation on endpoints
- Mix blocking and reactive code
- Store secrets in application.properties
- Use deprecated Spring Boot 2.x/3.x patterns
- Hardcode URLs, credentials, environment values

### Spring Boot 4 Notes
- Baseline: Java 17+ (21 or 25 LTS recommended), Spring Framework 7, Jakarta EE 11 (Servlet 6.1), Spring Security 7, Spring Data 2025.1, Hibernate 7, JUnit Jupiter 6, Testcontainers 2
- Jackson 3 is the default: packages and group IDs move from `com.fasterxml.jackson` to `tools.jackson` (annotations stay in `com.fasterxml.jackson.annotation`); `@JsonComponent` is `@JacksonComponent`, `Jackson2ObjectMapperBuilderCustomizer` is `JsonMapperBuilderCustomizer`; to replace the mapper, define a `JsonMapper` bean
- Modular starters: `spring-boot-starter-web` is `spring-boot-starter-webmvc`, `spring-boot-starter-oauth2-*` is `spring-boot-starter-security-oauth2-*`, `spring-boot-starter-aop` is `spring-boot-starter-aspectj`; Flyway and Liquibase need `spring-boot-starter-flyway` / `spring-boot-starter-liquibase`
- Test slices live in per-technology modules and packages: `@WebMvcTest` in `org.springframework.boot.webmvc.test.autoconfigure` (`spring-boot-webmvc-test`), `@DataJpaTest` in `org.springframework.boot.data.jpa.test.autoconfigure` (`spring-boot-data-jpa-test`), `@WebFluxTest` in `org.springframework.boot.webflux.test.autoconfigure`
- `@MockBean`/`@SpyBean` are removed: use `@MockitoBean`/`@MockitoSpyBean` on test-class fields (not in `@Configuration` classes)
- `@SpringBootTest` no longer provides `MockMvc`, `TestRestTemplate` or `WebTestClient` on its own: add `@AutoConfigureMockMvc`, `@AutoConfigureRestTestClient` (preferred, `RestTestClient`) or `@AutoConfigureTestRestTemplate`; for `WebTestClient`, `@AutoConfigureWebTestClient` (from `spring-boot-webflux-test`)
- `@EntityScan` is `org.springframework.boot.persistence.autoconfigure.EntityScan`; Actuator's `HealthIndicator`/`Health` are in `org.springframework.boot.health.contributor`
- Undertow is removed; Spring Retry is no longer version-managed
- Spring Cloud release train for Boot 4 is 2025.1.x (Oakwood)

## Stack right-sizing
Plain Java (a `main` + packages, JUnit, Maven) for CLI/batch/take-home tools — don't pay
framework startup for a file-in/report-out problem. Spring Boot only when it's genuinely
a web service. Same "invent nothing" rule as the architecture.

## Architecture Patterns

> Architecture is decided per context, not mandated here. Hexagonal (ports/adapters,
> pure domain) is the default on greenfield; on brownfield, conform to the house style.
> The layered Controller → Service → Repository shape below is illustrative Spring
> wiring, not the required architecture, and the domain stays free of Spring
> annotations. See `delivery-doctrine:ddd-hexagonal-reviewer`.

**Project Structure:**
```
src/main/java/com/example/service/
├── controller/     # REST endpoints
├── service/        # Business logic
├── repository/     # Data access
├── model/          # Entities
├── dto/            # Request/Response DTOs
├── config/         # Configuration
└── exception/      # Custom exceptions + handler
```

**Layering:**
- Controller → Service → Repository
- Controller handles HTTP, validation
- Service handles business logic, transactions
- Repository handles data persistence

**Clean Architecture Principles:**
- Domain models independent of frameworks
- Use case driven design
- Dependency inversion (interfaces)
- Clear boundaries between layers

## Common Annotations

| Annotation | Purpose |
|------------|---------|
| `@RestController` | REST controller (combines @Controller + @ResponseBody) |
| `@Service` | Business logic component |
| `@Repository` | Data access component |
| `@Transactional` | Transaction management |
| `@Valid` | Trigger validation |
| `@ConfigurationProperties` | Bind properties to class |
| `@EnableMethodSecurity` | Enable method security |

## Reactive WebFlux Endpoint

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/{id}")
    public Mono<ResponseEntity<OrderDto>> getOrder(@PathVariable UUID id) {
        return orderService.findById(id)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<OrderDto> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        return orderService.create(request);
    }
}
```

## Spring Security JWT

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/actuator/health").permitAll()
                        .anyRequest().authenticated())
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
                .build();
    }
}
```

## Knowledge Base

Spring Boot 4.x, Java 21+ (17 minimum), Spring Framework 7, Spring WebFlux, Project Reactor, Spring Data JPA, Spring Security 7, OAuth2/JWT, Hibernate 7, Jackson 3, R2DBC, Spring Cloud 2025.1, Resilience4j, Micrometer, JUnit 6, Testcontainers 2, Mockito, Maven/Gradle
