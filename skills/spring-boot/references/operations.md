<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Operations - configuration, health, telemetry, resilience

Read when the slice adds configuration, a health check, metrics or tracing, or an outbound call
that needs timeouts, retries or a circuit breaker. Deployment infrastructure (discovery, gateway,
Kubernetes manifests, container images) belongs to the platform: follow the house, add none.

## Configuration
```java
@ConfigurationProperties("payment")
@Validated
record PaymentProperties(@NotNull URI baseUrl, @NotNull Duration timeout, @NotBlank String apiKey) {}
```
- A record binds by constructor (no `@ConstructorBinding` unless it has several constructors);
  register it with `@ConfigurationPropertiesScan` on the application class or
  `@EnableConfigurationProperties`, not `@Component`. Inject the record, not scattered `@Value`.
- `@Validated` fails startup on a missing or malformed value, instead of the first request.
- Values come from `application.yml` defaults, profiles for environments, and environment variables
  (`PAYMENT_API_KEY` binds `payment.api-key`); secrets only from the environment or a secret
  manager, never a committed file.
- Spring Cloud Config, where the house runs it: `spring.config.import=optional:configserver:`
  (without `optional:` startup fails when the server is down). `@RefreshScope` with
  `POST /actuator/refresh` only for values that truly change without a restart.

## Health
- Boot 4 enables the liveness and readiness probes by default:
  `/actuator/health/liveness` and `/actuator/health/readiness`.
- Liveness never depends on an external system: a database outage would restart every instance
  at once. A dependency the service cannot serve without belongs in readiness.
- A custom check implements `HealthIndicator` (`org.springframework.boot.health.contributor`)
  and returns `Health.up()` or `Health.down().withDetail("reason", ...)`; it stays fast and
  times out on its own.
- `management.endpoint.health.show-details` is `never` by default; `when-authorized` (with
  `management.endpoint.health.roles`) rather than `always`, which leaks internals.

## Metrics and tracing
- Prometheus: `io.micrometer:micrometer-registry-prometheus`, and expose the endpoint
  (`management.endpoints.web.exposure.include=health,prometheus`); only `health` is exposed over
  HTTP by default. Expose nothing else without a reason.
- A business metric is a `Counter` or `Timer` from the injected `MeterRegistry`, recorded in the
  adapter or application layer, never in the domain.
- Tracing: `spring-boot-starter-opentelemetry` with
  `management.opentelemetry.tracing.export.otlp.endpoint`, or Zipkin under
  `management.tracing.export.zipkin.*`; `management.tracing.enabled` is now
  `management.tracing.export.enabled`. `management.tracing.sampling.probability` defaults to `0.1`.
  Boot puts `traceId` and `spanId` in the log lines by default (`logging.pattern.correlation`).
- A custom span through the Observation API:
  `Observation.createNotStarted("order.place", observationRegistry).observe(() -> placeOrder.handle(command))`.

## Resilience on outbound calls
Timeouts first (`web.md`); then retry or break the circuit on the out-adapter, never in the
domain, never inside a transaction.
- **Retry** only an idempotent call (or one carrying an idempotency key). Spring Framework 7 has it
  in core: `@EnableResilientMethods` on a configuration class, then
  `@Retryable(includes = PaymentUnavailableException.class, maxRetries = 3, delay = 200, multiplier = 2)`
  on the adapter method; `@ConcurrencyLimit(10)` caps concurrent calls. `RetryTemplate`
  (`org.springframework.core.retry`) for the programmatic form.
- **Circuit breaker and rate limiter**: Resilience4j, where the house uses it
  (`io.github.resilience4j:resilience4j-spring-boot4` with `spring-boot-starter-aspectj`):

```java
@CircuitBreaker(name = "payments", fallbackMethod = "chargeLater")
public PaymentReceipt charge(PaymentRequest payment) { ... }
```
```yaml
resilience4j:
  circuitbreaker:
    instances:
      payments:
        sliding-window-size: 10
        minimum-number-of-calls: 5
        failure-rate-threshold: 50
        wait-duration-in-open-state: 5s
        register-health-indicator: true
```
- A fallback only where a degraded answer is the contract (queue the charge, serve the last known
  rate); a fallback that invents data or hides the failure from a caller who must know is a
  swallowed error. Each policy has a test that drives the stub into the failure.
