<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Security - Spring Security 7

Read when the slice configures authentication, authorization, CSRF, CORS or headers in a Spring
Boot 4 service. What to check in a review is `delivery-doctrine:security-audit`'s; this file is
how to configure it. Apply only the security the requirements or the house name.

Spring Boot 4.1 ships Spring Security 7.1: the lambda DSL is required (no `.and()` chaining; custom
DSLs use `http.with(...)` instead of `apply(...)`), and the OAuth2 starters are
`spring-boot-starter-security-oauth2-resource-server` / `-client` / `-authorization-server`
(Spring Authorization Server is now part of Spring Security).

## API secured by bearer tokens (resource server)

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> jwt
                .jwtAuthenticationConverter(rolesFromClaim())))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .csrf(AbstractHttpConfigurer::disable)
            .build();
    }

    JwtAuthenticationConverter rolesFromClaim() {
        var authorities = new JwtGrantedAuthoritiesConverter();
        authorities.setAuthoritiesClaimName("roles");
        authorities.setAuthorityPrefix("ROLE_");
        var converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(authorities);
        return converter;
    }
}
```
- The decoder comes from `spring.security.oauth2.resourceserver.jwt.issuer-uri`; Boot builds
  it and validates signature, issuer, `exp` and `nbf`. It checks `aud` only when
  `spring.security.oauth2.resourceserver.jwt.audiences` lists this API, so set it: a token
  minted for another service must not pass. Without a custom converter, authorities come from
  the `scope`/`scp` claim prefixed `SCOPE_` (`hasAuthority("SCOPE_orders:write")`).
- Deny by default: the last matcher is `anyRequest().authenticated()` (or `denyAll()`), and each
  public path is listed by name.
- CSRF off only because no browser sends credentials to this API automatically. A cookie, a
  session or HTTP basic that a browser sends makes it a browser app, stateless or not.
- Tokens are issued by an authorization server (the house's, or Spring Authorization Server),
  not by a hand-written JWT filter and signing service in the API.
- The current caller in a controller: `@AuthenticationPrincipal Jwt jwt`, passed to the use case
  as a domain value (`CustomerId`), never the `Jwt` itself.

## Browser app with a session
Keep CSRF on. For a single-page app reading the token from a cookie, `csrf.spa()` (since 7.0)
sets up the cookie repository and the request handler together:

```java
http.csrf(csrf -> csrf.spa());
```
Login through `oauth2Login(...)` or `formLogin(...)`, session fixation protection left at its
default, and a session timeout the requirements name. Where the service stores its own users, a
`UserDetailsService` over the persistence adapter plus the password encoder below; still no
self-minted JWT. If the service must issue tokens, that is Spring Authorization Server.

## Headers
Spring Security writes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Cache-Control: no-cache, no-store, max-age=0, must-revalidate`, `X-XSS-Protection: 0` and, on
HTTPS requests only, `Strict-Transport-Security: max-age=31536000 ; includeSubDomains`. It adds no
Content-Security-Policy, because no default fits every app; set one where the service serves HTML:

```java
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'self'; frame-ancestors 'none'")));
```

## CORS
One `CorsConfigurationSource` bean with the exact origins; `http.cors(Customizer.withDefaults())`
picks it up; the origins come from configuration (`CorsProperties` is a `@ConfigurationProperties`
record). Never `*` origins with credentials.

```java
@Bean
CorsConfigurationSource corsConfigurationSource(CorsProperties cors) {
    var config = new CorsConfiguration();
    config.setAllowedOrigins(cors.allowedOrigins());
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    config.setAllowCredentials(true);
    var source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", config);
    return source;
}
```

## Passwords
Where the service stores passwords at all, one bean:
`PasswordEncoderFactories.createDelegatingPasswordEncoder()`. It encodes with bcrypt (strength 10)
and stores the `{id}` prefix, so a later move to `argon2` re-encodes on login instead of breaking
old hashes. Tests may define a `BCryptPasswordEncoder(4)` to stay fast.

## Method security
`@EnableMethodSecurity` turns on `@PreAuthorize`/`@PostAuthorize`. Put them on controller or
adapter methods, never on domain types (`delivery-doctrine:java-domain`). A rule about who may
touch which object is a domain rule (`order.requirePlacedBy(customerId)`), tested as one; a
`@PreAuthorize("@orderAccess.canRead(#id, authentication)")` is for a coarse gate in front of
it. `@Secured` needs `securedEnabled = true` and is legacy; prefer `@PreAuthorize`.

## Testing
Every rule gets a test that turns red when it is dropped: 401 without a token, 403 with the wrong
role, 2xx with the right one. In `@WebMvcTest`, `@Import(SecurityConfig.class)` and either
`@WithMockUser(roles = "ADMIN")` or the request post-processor
`.with(jwt().authorities(new SimpleGrantedAuthority("ROLE_ADMIN")))`
(`SecurityMockMvcRequestPostProcessors`).
