<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Web Layer - Controllers & REST APIs

## HTTP contract

| Verb | For | Idempotent | Success status |
|------|-----|------------|----------------|
| GET | Read; never changes state | Yes | 200 |
| POST | Create, or a command (`/orders/{id}/cancellation`) | No | 201 with `Location`, or 200/202 |
| PUT | Replace the whole resource | Yes | 200, or 204 |
| PATCH | Partial update | Not by default | 200, or 204 |
| DELETE | Remove | Yes | 204 |

Failures: 400 malformed or invalid input, 404 unknown resource, 409 a state conflict or a
duplicate, 422 only where the house uses it for domain refusals, 500 the unexpected, logged
once. A search with many criteria stays a `GET` with query parameters until it no longer fits a
URL. Follow the versioning scheme the house or the requirements name and add none by default: a
`/v1` nobody asked for is invented structure, and how to ship a breaking change is the API
owners' decision.

## REST Controller Pattern

```java
@RestController
@RequestMapping("/api/users")
@Validated
public class UserController {
    private final UserService userService;
    
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @GetMapping
    public ResponseEntity<Page<UserResponse>> getUsers(
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {
        Page<UserResponse> users = userService.findAll(pageable);
        return ResponseEntity.ok(users);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        UserResponse user = userService.findById(id);
        return ResponseEntity.ok(user);
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody UserCreateRequest request) {
        UserResponse user = userService.create(request);
        URI location = ServletUriComponentsBuilder
                .fromCurrentRequest()
                .path("/{id}")
                .buildAndExpand(user.id())
                .toUri();
        return ResponseEntity.created(location).body(user);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UserUpdateRequest request) {
        UserResponse user = userService.update(id, request);
        return ResponseEntity.ok(user);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
```

## Request DTOs with Validation

```java
public record UserCreateRequest(
    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    String email,

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 100, message = "Password must be 8-100 characters")
    @Pattern(regexp = "^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d).*$",
             message = "Password must contain uppercase, lowercase, and digit")
    String password,

    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50)
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "Username must be alphanumeric")
    String username,

    @Min(value = 18, message = "Must be at least 18")
    @Max(value = 120, message = "Must be at most 120")
    Integer age
) {}

public record UserUpdateRequest(
    @Email(message = "Email must be valid")
    String email,

    @Size(min = 3, max = 50)
    String username
) {}
```

## Response DTOs

```java
public record UserResponse(
    Long id,
    String email,
    String username,
    Integer age,
    Boolean active,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getId(),
            user.getEmail(),
            user.getUsername(),
            user.getAge(),
            user.getActive(),
            user.getCreatedAt(),
            user.getUpdatedAt()
        );
    }
}
```

## Global Exception Handling

Errors leave as `ProblemDetail` (RFC 9457). Extending `ResponseEntityExceptionHandler` covers
Spring MVC's own exceptions; it already maps `MethodArgumentNotValidException`, so field errors
are added by overriding `handleMethodArgumentNotValid` (a second `@ExceptionHandler` for it is
an ambiguous mapping at startup). Each domain exception gets one `@ExceptionHandler` returning
`ProblemDetail`; Spring sets the status from it and `instance` from the request path, and
`setProperty` entries render as top-level JSON fields. Only the 500 branch logs: the others are
expected outcomes the response already reports.

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ProblemDetail handleDataIntegrity(DataIntegrityViolationException ex) {
        return ProblemDetail.forStatusAndDetail(
            HttpStatus.CONFLICT, "Data integrity violation - resource may already exist");
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex) {
        log.error("Unexpected error", ex);
        return ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex, HttpHeaders headers,
            HttpStatusCode status, WebRequest request) {
        Map<String, String> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                error -> error.getDefaultMessage() != null
                    ? error.getDefaultMessage()
                    : "Invalid value",
                (first, second) -> first));
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, "Validation failed");
        problem.setProperty("errors", errors);
        return handleExceptionInternal(ex, problem, headers, status, request);
    }
}
```

## Custom Validation

```java
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = UniqueEmailValidator.class)
public @interface UniqueEmail {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

@Component
public class UniqueEmailValidator implements ConstraintValidator<UniqueEmail, String> {
    private final UserRepository userRepository;

    public UniqueEmailValidator(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    @Override
    public boolean isValid(String email, ConstraintValidatorContext context) {
        if (email == null) return true;
        return !userRepository.existsByEmail(email);
    }
}
```

## RestClient for External APIs

```java
@Configuration
public class RestClientConfig {
    @Bean
    public RestClient restClient(RestClient.Builder builder) {
        return builder
            .baseUrl("https://api.example.com")
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}

@Service
public class ExternalApiService {
    private final RestClient restClient;

    public ExternalApiService(RestClient restClient) {
        this.restClient = restClient;
    }

    public ExternalDataResponse fetchData(String id) {
        return restClient
            .get()
            .uri("/data/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError, (request, response) -> {
                throw new ResourceNotFoundException("External resource not found");
            })
            .onStatus(HttpStatusCode::is5xxServerError, (request, response) -> {
                throw new ServiceUnavailableException("External service unavailable");
            })
            .body(ExternalDataResponse.class);
    }
}
```

Use `RestClient` for blocking calls in a Spring MVC app; use `WebClient` only in reactive or streaming code. In Spring Boot 4 the auto-configured `RestClient.Builder` comes from `spring-boot-starter-restclient` and `WebClient.Builder` from `spring-boot-starter-webclient`. Timeouts and retries belong to the request factory settings and to Resilience4j (see `cloud.md`), not to the call site.

## CORS Configuration

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000", "https://example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

## Quick Reference

| Annotation | Purpose |
|------------|---------|
| `@RestController` | Marks class as REST controller (combines @Controller + @ResponseBody) |
| `@RequestMapping` | Maps HTTP requests to handler methods |
| `@GetMapping/@PostMapping` | HTTP method-specific mappings |
| `@PathVariable` | Extracts values from URI path |
| `@RequestParam` | Extracts query parameters |
| `@RequestBody` | Binds request body to method parameter |
| `@Valid` | Triggers validation on request body |
| `@RestControllerAdvice` | Global exception handling for REST controllers |
| `@ResponseStatus` | Sets HTTP status code for method |
