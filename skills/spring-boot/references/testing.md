<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Testing - Spring Boot Test

## Unit Testing with JUnit Jupiter

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("Should create user successfully")
    void shouldCreateUser() {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        User user = new User();
        user.setId(1L);
        user.setEmail(request.email());
        user.setUsername(request.username());

        when(userRepository.existsByEmail(request.email())).thenReturn(false);
        when(passwordEncoder.encode(request.password())).thenReturn("encodedPassword");
        when(userRepository.save(any(User.class))).thenReturn(user);

        UserResponse response = userService.create(request);

        assertThat(response).isNotNull();
        assertThat(response.email()).isEqualTo(request.email());

        verify(userRepository).existsByEmail(request.email());
        verify(passwordEncoder).encode(request.password());
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("Should throw exception when email already exists")
    void shouldThrowExceptionWhenEmailExists() {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        when(userRepository.existsByEmail(request.email())).thenReturn(true);

        assertThatThrownBy(() -> userService.create(request))
            .isInstanceOf(DuplicateResourceException.class)
            .hasMessageContaining("Email already registered");

        verify(userRepository, never()).save(any(User.class));
    }
}
```

## Integration Testing with @SpringBootTest

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class UserIntegrationTest {

    @Autowired
    private RestTestClient restTestClient;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    @Order(1)
    @DisplayName("Should create user via API")
    void shouldCreateUserViaApi() {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        RestTestClient.ResponseSpec response = restTestClient.post()
            .uri("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .exchange();

        response.expectStatus().isCreated()
            .expectHeader().exists("Location")
            .expectBody(UserResponse.class)
            .value(body -> assertThat(body.email()).isEqualTo(request.email()));
    }

    @Test
    @Order(2)
    @DisplayName("Should return validation error for invalid request")
    void shouldReturnValidationError() {
        UserCreateRequest request = new UserCreateRequest(
            "invalid-email",
            "short",
            "u",
            15
        );

        RestTestClient.ResponseSpec response = restTestClient.post()
            .uri("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .body(request)
            .exchange();

        response.expectStatus().isBadRequest()
            .expectBody()
            .jsonPath("$.errors").isNotEmpty();
    }
}
```

Spring Boot 4: `@SpringBootTest` no longer auto-configures a client. `RestTestClient` (Spring Framework 7) needs `@AutoConfigureRestTestClient` from `spring-boot-resttestclient`. `TestRestTemplate` still exists in `org.springframework.boot.resttestclient` but needs `@AutoConfigureTestRestTemplate`, and `MockMvc` in a `@SpringBootTest` needs `@AutoConfigureMockMvc`.

## Web Layer Testing with MockMvc

```java
@WebMvcTest(UserController.class)
@Import(SecurityConfig.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Should get all users")
    void shouldGetAllUsers() throws Exception {
        Page<UserResponse> users = new PageImpl<>(List.of(
            new UserResponse(1L, "user1@example.com", "user1", 25, true, null, null),
            new UserResponse(2L, "user2@example.com", "user2", 30, true, null, null)
        ));

        when(userService.findAll(any(Pageable.class))).thenReturn(users);

        mockMvc.perform(get("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").isArray())
            .andExpect(jsonPath("$.content.length()").value(2))
            .andExpect(jsonPath("$.content[0].email").value("user1@example.com"))
            .andDo(print());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Should create user")
    void shouldCreateUser() throws Exception {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        UserResponse response = new UserResponse(
            1L,
            request.email(),
            request.username(),
            request.age(),
            true,
            LocalDateTime.now(),
            LocalDateTime.now()
        );

        when(userService.create(any(UserCreateRequest.class))).thenReturn(response);

        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(header().exists("Location"))
            .andExpect(jsonPath("$.email").value(request.email()))
            .andExpect(jsonPath("$.username").value(request.username()))
            .andDo(print());
    }

    @Test
    @WithMockUser(roles = "USER")
    @DisplayName("Should return 403 for non-admin user")
    void shouldReturn403ForNonAdmin() throws Exception {
        mockMvc.perform(get("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isForbidden());
    }
}
```

`@WebMvcTest` comes from `org.springframework.boot.webmvc.test.autoconfigure` (module `spring-boot-webmvc-test`). With Jackson 3, the injected `ObjectMapper` is `tools.jackson.databind.ObjectMapper` (the auto-configured `JsonMapper`), and `writeValueAsString` throws the unchecked `JacksonException`. `MockMvcTester` (AssertJ-based) is available alongside `MockMvc`.

## Data JPA Testing

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@ActiveProfiles("test")
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TestEntityManager entityManager;

    @Test
    @DisplayName("Should find user by email")
    void shouldFindUserByEmail() {
        User user = User.builder()
            .email("test@example.com")
            .password("password")
            .username("testuser")
            .active(true)
            .build();

        entityManager.persistAndFlush(user);

        Optional<User> found = userRepository.findByEmail("test@example.com");

        assertThat(found).isPresent();
        assertThat(found.get().getEmail()).isEqualTo("test@example.com");
    }

    @Test
    @DisplayName("Should check if email exists")
    void shouldCheckIfEmailExists() {
        User user = User.builder()
            .email("test@example.com")
            .password("password")
            .username("testuser")
            .active(true)
            .build();

        entityManager.persistAndFlush(user);

        boolean exists = userRepository.existsByEmail("test@example.com");

        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("Should fetch user with roles")
    void shouldFetchUserWithRoles() {
        Role adminRole = Role.builder().name("ADMIN").build();
        entityManager.persist(adminRole);

        User user = User.builder()
            .email("admin@example.com")
            .password("password")
            .username("admin")
            .active(true)
            .roles(Set.of(adminRole))
            .build();

        entityManager.persistAndFlush(user);
        entityManager.clear();

        Optional<User> found = userRepository.findByEmailWithRoles("admin@example.com");

        assertThat(found).isPresent();
        assertThat(found.get().getRoles()).hasSize(1);
        assertThat(found.get().getRoles()).extracting(Role::getName).contains("ADMIN");
    }
}
```

## Testcontainers with @ServiceConnection

```java
@SpringBootTest
@Testcontainers
@ActiveProfiles("test")
class UserServiceIntegrationTest {

    @Container
    @ServiceConnection
    static PostgreSQLContainer postgres = new PostgreSQLContainer("postgres:17-alpine");

    @Autowired
    private UserService userService;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("Should create and find user in real database")
    void shouldCreateAndFindUser() {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        UserResponse created = userService.create(request);
        UserResponse found = userService.findById(created.id());

        assertThat(found).isNotNull();
        assertThat(found.email()).isEqualTo(request.email());
    }
}
```

`@ServiceConnection` (`org.springframework.boot.testcontainers.service.connection`) derives the datasource properties from the container, replacing `@DynamicPropertySource`. Testcontainers 2 moved modules to `org.testcontainers.<module>` packages with non-generic classes: `org.testcontainers.postgresql.PostgreSQLContainer` from artifact `testcontainers-postgresql`.

## Testing Reactive Endpoints with WebTestClient

```java
@WebFluxTest(UserReactiveController.class)
class UserReactiveControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockitoBean
    private UserReactiveService userService;

    @Test
    @DisplayName("Should get user reactively")
    void shouldGetUserReactively() {
        UserResponse user = new UserResponse(
            1L,
            "test@example.com",
            "testuser",
            25,
            true,
            LocalDateTime.now(),
            LocalDateTime.now()
        );

        when(userService.findById(1L)).thenReturn(Mono.just(user));

        webTestClient.get()
            .uri("/api/v1/users/{id}", 1L)
            .accept(MediaType.APPLICATION_JSON)
            .exchange()
            .expectStatus().isOk()
            .expectBody(UserResponse.class)
            .value(response -> {
                assertThat(response.id()).isEqualTo(1L);
                assertThat(response.email()).isEqualTo("test@example.com");
            });
    }

    @Test
    @DisplayName("Should create user reactively")
    void shouldCreateUserReactively() {
        UserCreateRequest request = new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );

        UserResponse response = new UserResponse(
            1L,
            request.email(),
            request.username(),
            request.age(),
            true,
            LocalDateTime.now(),
            LocalDateTime.now()
        );

        when(userService.create(any(UserCreateRequest.class))).thenReturn(Mono.just(response));

        webTestClient.post()
            .uri("/api/v1/users")
            .contentType(MediaType.APPLICATION_JSON)
            .body(Mono.just(request), UserCreateRequest.class)
            .exchange()
            .expectStatus().isCreated()
            .expectHeader().exists("Location")
            .expectBody(UserResponse.class)
            .value(user -> {
                assertThat(user.email()).isEqualTo(request.email());
            });
    }
}
```

## Testing Configuration

**application-test.yml**

```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: true
    properties:
      hibernate:
        format_sql: true
  security:
    user:
      name: test
      password: test

logging:
  level:
    org.hibernate.SQL: DEBUG
    org.hibernate.orm.jdbc.bind: TRACE
```

**Test configuration class** (a low-cost BCrypt strength keeps tests fast)

```java
@TestConfiguration
public class TestConfig {

    @Bean
    @Primary
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(4);
    }

    @Bean
    public Clock fixedClock() {
        return Clock.fixed(
            Instant.parse("2024-01-01T00:00:00Z"),
            ZoneId.of("UTC")
        );
    }
}
```

## Test Fixtures with @DataJpaTest

```java
@Component
public class TestDataFactory {

    public static User createUser(String email, String username) {
        return User.builder()
            .email(email)
            .password("encodedPassword")
            .username(username)
            .active(true)
            .createdAt(LocalDateTime.now())
            .updatedAt(LocalDateTime.now())
            .build();
    }

    public static UserCreateRequest createUserRequest() {
        return new UserCreateRequest(
            "test@example.com",
            "Password123",
            "testuser",
            25
        );
    }
}
```

## Quick Reference

| Annotation | Purpose |
|------------|---------|
| `@SpringBootTest` | Full application context integration test |
| `@WebMvcTest` | Test MVC controllers with mocked services (`spring-boot-webmvc-test`) |
| `@WebFluxTest` | Test reactive controllers |
| `@DataJpaTest` | Test JPA repositories (`spring-boot-data-jpa-test`) |
| `@MockitoBean` | Add mock bean to Spring context (replaces `@MockBean`, removed in Spring Boot 4) |
| `@MockitoSpyBean` | Wrap a Spring bean in a Mockito spy (replaces `@SpyBean`) |
| `@AutoConfigureRestTestClient` | Auto-configure `RestTestClient` for `@SpringBootTest` |
| `@AutoConfigureMockMvc` | Auto-configure `MockMvc`/`MockMvcTester` for `@SpringBootTest` |
| `@ServiceConnection` | Wire a Testcontainers container into Spring Boot connection details |
| `@WithMockUser` | Mock authenticated user for security tests |
| `@Testcontainers` | Enable Testcontainers support |
| `@ActiveProfiles` | Activate specific Spring profiles for test |

## Testing Best Practices

- Write tests following AAA pattern (Arrange, Act, Assert)
- Use descriptive test names with @DisplayName
- Mock external dependencies, use real DB with Testcontainers
- Achieve 85%+ code coverage
- Test happy path and edge cases
- Use @Transactional for test data cleanup
- Separate unit tests from integration tests
- Use parameterized tests for multiple scenarios
- Test security rules and validation
- Keep tests fast and independent
