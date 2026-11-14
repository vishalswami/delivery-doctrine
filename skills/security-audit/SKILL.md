---
name: security-audit
description: Use when reviewing Java code for security, before a release, or when asked about
  vulnerabilities, OWASP or secure coding — the review checklist mapped to the OWASP Top
  10:2025 (access control and SSRF, misconfiguration and headers, supply chain, crypto and
  passwords, injection, XSS and HTML sanitizing, CSRF, secrets, deserialization and XXE,
  security logging, failing closed). Works for Spring, Quarkus, Jakarta EE and plain Java;
  Spring Security configuration lives in spring-boot's references/security.md.
---

<!-- Adapted from decebals/claude-code-java (MIT); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Security Audit

Examples carry ✅/❌ labels to teach; delivered code carries none.

The Java security review checklist. How to configure Spring Security (filter chains, resource
server, CSRF, CORS, headers, password encoder, method security) is
`delivery-doctrine:spring-boot`'s `references/security.md`; this skill says what must be true.
Findings rank Critical, Important or Minor in the critic's shape (`delivery-doctrine:critic`).

## OWASP Top 10:2025, the Java checks
| # | Risk | Check |
|---|------|-------|
| A01 | Broken Access Control (SSRF folded in) | Deny by default; every object checked against the caller; outbound URLs allowlisted |
| A02 | Security Misconfiguration | Headers and CSP; debug, dev endpoints and default credentials gone; Actuator exposure minimal |
| A03 | Software Supply Chain Failures | Dependency scan before the PR; pinned versions; nothing unused |
| A04 | Cryptographic Failures | Adaptive password hashing; HTTPS enforced; no home-made crypto; no secret in code |
| A05 | Injection | Parameters, never concatenation: SQL, JPQL, commands, LDAP |
| A06 | Insecure Design | Rules in the domain, refusals tested; rate limits on auth and costly endpoints |
| A07 | Authentication Failures | Tokens from an authorization server; sessions rotated; MFA where named |
| A08 | Software or Data Integrity Failures | No native deserialization of untrusted input; signed artifacts |
| A09 | Security Logging and Alerting Failures | Security events logged, secrets and personal data never |
| A10 | Mishandling of Exceptional Conditions | Fail closed; errors leak no internals |

## Input
- **Validate at the edge, allowlist the shape.** Bean Validation on the request record
  (`@NotBlank @Size(max = 50) @Pattern(regexp = "^[a-zA-Z0-9_]+$") String username`, `@Valid` on
  the parameter), then the domain constructor keeps the invariant (`delivery-doctrine:java-domain`).

```java
// ❌
if (input.contains("<script>")) {
    throw new InvalidNameException(input);
}

// ✅
private static final Pattern NAME = Pattern.compile("^[\\p{L} '-]{1,100}$");
```
- **Rich text is sanitized by an allowlist policy**, never filtered by a regex of bad tags:
  OWASP Java HTML Sanitizer (`com.googlecode.owasp-java-html-sanitizer:owasp-java-html-sanitizer`).

```java
private static final PolicyFactory COMMENT_HTML = Sanitizers.FORMATTING.and(Sanitizers.LINKS);

String safe = COMMENT_HTML.sanitize(untrustedHtml);
```
- **Size limits** on bodies, uploads, collections and strings.

## Injection
```java
// ❌
String jpql = "SELECT o FROM OrderEntity o WHERE o.reference = '" + reference + "'";

// ✅
@Query("SELECT o FROM OrderEntity o WHERE o.reference = :reference")
Optional<OrderEntity> findByReference(@Param("reference") String reference);
```
- Same for native queries, JDBC (`PreparedStatement`), Criteria and `JdbcClient` (`.param(...)`).
  A varying column or sort field comes from an allowlist in code, never from the request.
- Commands: `new ProcessBuilder("git", "log", ref)`, never `sh -c` with input in the string.

## Output, XSS and headers
- Templates escape (Thymeleaf `th:text`; `th:utext` only for sanitized HTML). Manual encoding:
  OWASP Java Encoder (`org.owasp.encoder:encoder` 1.5.0+), `Encode.forHtml`, `forJavaScript`,
  `forUriComponent`, each for its one context; the caller adds quotes; never `forJavaScript` for JSON.
- Headers on every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Strict-Transport-Security` on HTTPS, and a `Content-Security-Policy` wherever HTML is served.
  Spring Security writes all but the CSP by default; without it, one servlet filter sets them.

## CSRF
CSRF protection stays on wherever a browser sends credentials automatically (a session cookie, a
custom auth cookie, HTTP basic), stateless or not. Only an API used by non-browser clients with
bearer tokens may turn it off. Spring: `csrf.spa()` for a single-page app (security.md); Quarkus:
the `quarkus-rest-csrf` extension (`quarkus.rest-csrf.*`).

## Authentication and access
- **Object-level checks.** A request that names an ID is checked against the caller before use:
  `readDocument.asOwner(documentId, callerId)`, never `documents.byId(id)` for whatever ID
  arrived. Loading by the given ID alone is an IDOR (A01, Critical).
- **Passwords** hashed adaptively: bcrypt or Argon2 through a delegating encoder; MD5, SHA-1 or a
  bare SHA-256 is Critical. Comparison of secrets in constant time (`MessageDigest.isEqual`).
- **Tokens** validated (signature, issuer, audience, expiry) by the framework, not hand-parsed.
- **Outbound calls** built from user input (webhooks, image URLs) resolve against an allowlist of
  hosts and schemes, and do not follow redirects into internal addresses (SSRF).

## Secrets
Never in code, `application.yml` or a committed `.env`: `password: ${DB_PASSWORD}` from the
environment or a secret manager, bound into `@ConfigurationProperties`. `.gitignore` carries `.env`,
`*.pem`, `*.key`, `*credentials*`, `application-local.yml`; a secret ever committed is rotated.

## Deserialization and XML
- No `ObjectInputStream.readObject()` on untrusted bytes (remote code execution, Critical); if a
  legacy protocol forces it, an `ObjectInputFilter` allowlists the classes.
- Jackson binds into concrete record types. Never default typing (`activateDefaultTyping`) or
  `@JsonTypeInfo(use = Id.CLASS)` on input: the payload would pick the class. Polymorphism is
  `@JsonTypeInfo(use = Id.NAME)` with listed subtypes.
- XML parsers refuse DOCTYPEs (`http://apache.org/xml/features/disallow-doctype-decl` set true),
  so no external entities (XXE).

## Logging and failures
- Log logins, failures, access denied and privilege changes as structured fields
  (`kv("userId", id)`); never passwords, tokens, card numbers or whole request bodies.
- Fail closed: an exception in an authorization check denies; a 500 answers with a generic
  `ProblemDetail` and logs the cause once.

## Dependencies
Once before the PR, not per iteration: `mvn org.owasp:dependency-check-maven:check` (an NVD API
key speeds it up; `failBuildOnCVSS` 7 fails on high severity), or the house's scanner;
`mvn versions:display-dependency-updates` for what is behind; unused dependencies removed.
