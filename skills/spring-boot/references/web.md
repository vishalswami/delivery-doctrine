<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Web Layer - Controllers & REST APIs

Read when the slice adds or changes an endpoint or an outbound HTTP call. Controllers are
inbound adapters in `<feature>.web` (`delivery-doctrine:java-domain`): they validate, map to a
domain command, call the use case and map the result back. Examples use an `orders` feature.

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

## Controller
```java
@RestController
@RequestMapping("/orders")
class OrderController {
    private final PlaceOrder placeOrder;
    private final FindOrders findOrders;

    OrderController(PlaceOrder placeOrder, FindOrders findOrders) {
        this.placeOrder = placeOrder;
        this.findOrders = findOrders;
    }

    @GetMapping("/{id}")
    OrderResponse get(@PathVariable UUID id) {
        return OrderResponse.from(findOrders.byId(new OrderId(id)));
    }

    @GetMapping
    Page<OrderSummaryResponse> list(@RequestParam UUID customerId, @PageableDefault(size = 20) Pageable page) {
        return findOrders.ofCustomer(new CustomerId(customerId), page).map(OrderSummaryResponse::from);
    }

    @PostMapping
    ResponseEntity<OrderResponse> place(@Valid @RequestBody PlaceOrderRequest request) {
        Order order = placeOrder.handle(request.toCommand());
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
            .path("/{id}").buildAndExpand(order.id().value()).toUri();
        return ResponseEntity.created(location).body(OrderResponse.from(order));
    }
}
```
- A missing order is a domain exception (`OrderNotFoundException`) mapped to 404 by the advice,
  not an `Optional` unwrapped in the controller. List endpoints page; none returns a whole table.
- A `Page` serialized straight to JSON publishes Spring's page shape as the contract; map it to
  a record (`PageResponse<T>(List<T> items, long total)`) where the response format matters.

## Request and response records
```java
record PlaceOrderRequest(
    @NotNull UUID customerId,
    @NotEmpty List<@Valid LineRequest> lines) {

    PlaceOrderCommand toCommand() {
        return new PlaceOrderCommand(new CustomerId(customerId), lines.stream().map(LineRequest::toLine).toList());
    }
}

record OrderResponse(UUID id, String status, BigDecimal total) {
    static OrderResponse from(Order order) {
        return new OrderResponse(order.id().value(), order.status().name(), order.total().amount());
    }
}
```
- Bean Validation annotations live on request records, never on domain types; the domain
  constructor still keeps its own invariant. Validate the whole range, not the example value
  (`@Positive`, not `@Min(1)` when zero and negatives are both wrong; `@Size(max = ...)` on every
  string and list).
- A custom constraint (`@Constraint(validatedBy = ...)` plus a `ConstraintValidator`) is for a shape
  rule several requests share. A constraint that queries the database (`@UniqueEmail`) is a
  check-then-act race: uniqueness is a unique index, and its `DataIntegrityViolationException`
  maps to 409.
- Response records never expose JPA entities: lazy proxies, internal columns and N+1 queries leak.

## Errors as ProblemDetail

Errors leave as `ProblemDetail` (RFC 9457). Extending `ResponseEntityExceptionHandler` covers
Spring MVC's own exceptions; it already maps `MethodArgumentNotValidException`, so field errors
are added by overriding `handleMethodArgumentNotValid` (a second `@ExceptionHandler` for it is
an ambiguous mapping at startup). Each domain exception gets one `@ExceptionHandler` returning
`ProblemDetail`; Spring sets the status from it and `instance` from the request path, and
`setProperty` entries render as top-level JSON fields. Only the 500 branch logs: the others are
expected outcomes the response already reports.

```java
@RestControllerAdvice
class OrdersExceptionHandler extends ResponseEntityExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(OrdersExceptionHandler.class);

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail notFound(OrderNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(CreditLimitExceededException.class)
    ProblemDetail creditLimit(CreditLimitExceededException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle("Credit limit exceeded");
        return problem;
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail unexpected(Exception ex) {
        log.error("Unexpected error", ex);
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        Map<String, String> errors = ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                error -> Objects.requireNonNullElse(error.getDefaultMessage(), "Invalid value"),
                (first, second) -> first));
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(status, "Validation failed");
        problem.setProperty("errors", errors);
        return handleExceptionInternal(ex, problem, headers, status, request);
    }
}
```
The detail of an unexpected error never carries `ex.getMessage()`: it can hold SQL, paths or
data (`delivery-doctrine:security-audit`, A10).

## Outbound calls with RestClient
An outbound HTTP call is an out-adapter implementing a domain port (`PaymentGateway`), so the
domain never sees HTTP types.

```java
class HttpPaymentGateway implements PaymentGateway {
    private final RestClient client;

    HttpPaymentGateway(RestClient.Builder builder, PaymentProperties properties) {
        this.client = builder.baseUrl(properties.baseUrl()).build();
    }

    @Override
    public PaymentReceipt charge(PaymentRequest payment) {
        return client.post().uri("/charges").body(ChargeBody.from(payment)).retrieve()
            .onStatus(status -> status.value() == 402, (request, response) -> {
                throw new PaymentDeclinedException(payment.orderId());
            })
            .body(ChargeResult.class)
            .toReceipt();
    }
}
```
- `RestClient` for blocking calls in a Spring MVC app; `WebClient` only in reactive or streaming
  code. In Boot 4 the auto-configured `RestClient.Builder` comes from `spring-boot-starter-restclient`
  and `WebClient.Builder` from `spring-boot-starter-webclient`.
- Every call has timeouts: `spring.http.clients.connect-timeout` and `spring.http.clients.read-timeout`
  for the auto-configured clients. Retries and circuit breaking sit on the adapter
  (`operations.md`), never inside a transaction.
- The base URL comes from configuration, so a test points it at an in-process stub
  (`delivery-doctrine:acceptance-testing`).

## CORS
With Spring Security on the classpath, configure CORS there (`security.md`). Without it, one
`WebMvcConfigurer.addCorsMappings` with exact origins from configuration; never `*` with credentials.
