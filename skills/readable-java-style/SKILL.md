---
name: readable-java-style
description: Use when writing or reviewing Java code — enforces zero comments (rationale goes to ADRs or test names, never inline), and complete logical methods over reflexive private-method decomposition.
---

# Readable Java Style

Two rules that override generic "clean code" advice in this codebase.

## Rule 1: No Comments

Code explains itself through naming. Comments are banned — zero, in production and
test code alike (the doctrine's hard rule). A comment is a signal that a name or the
structure failed; fix that, don't annotate it.

- When a comment would explain *what*, rename until it is unnecessary, then delete it.
- When a rationale would explain *why* (a hidden constraint, a spec reference, a
  non-obvious invariant), record it in an ADR (`docs/adr/`) or carry it in a test
  name — never inline.

```java
// ❌ restates what the code already says
// increment retry count
retryCount++;

// ❌ Javadoc on a self-evident method
/** Validates the token. Returns true if valid. */
public boolean isValid(String token) { ... }

// ❌ even a WHY comment is still a comment
// payment provider forbids automatic retries; see contract §4.2
retryPolicy.maxAttempts(1);
```

The rationale belongs in `docs/adr/NNNN-no-automatic-retries.md` or a test named
`givenProviderTimeout_whenCharge_thenNotRetried`, and the line stays bare.

## Rule 2: Complete Logical Methods over Helper Chains

A method should read top-to-bottom as the full story of what it does.

**Extract a private method only to:**
- Remove real duplication (same block in 2+ places)
- Isolate a genuinely complex sub-problem that hurts readability inline

**Do NOT extract just because a method is 15–30 lines.** A clear 20-line method is not a smell. Three one-call private helpers that fragment the story is worse.

❌ Reflexive decomposition: the reader chases three helpers to follow one flow.

```java
public void registerOrder(OrderRequest request) {
    validateRequest(request);
    Order order = buildOrder(request);
    persistAndPublish(order);
}
private void validateRequest(...) { ... }
private Order buildOrder(...) { ... }
private void persistAndPublish(...) { ... }
```

✅ The complete story inline, readable in one pass.

```java
public void registerOrder(OrderRequest request) {
    if (request.items().isEmpty()) {
        throw new EmptyOrderException(request.customerId());
    }
    Order order = new Order(request.customerId(), request.items(), clock.now());
    orderRepository.save(order);
    eventPublisher.publish(new OrderRegistered(order.id()));
}
```

## Where this overrides code-quality

`delivery-doctrine:code-quality` wins on: null safety, API contracts, exception handling, performance.  
This skill wins on: method decomposition decisions and comment removal.

## Quick Checklist

- [ ] No comments at all — none in production or test code
- [ ] WHY (constraints, invariants, spec refs) recorded in an ADR or test name, not inline
- [ ] No Javadoc on self-evident methods/classes
- [ ] Each private method earns its existence (duplication removal or real complexity isolation)
- [ ] Method reads as a complete story without chasing helpers
