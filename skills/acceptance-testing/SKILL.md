---
name: acceptance-testing
description: Use when writing the acceptance test for a slice — the end-to-end flow
  that proves the vertical runs. Drives the system's real entry point and stubs
  external boundaries in-process (ephemeral port, config-injected URL) so tests stay
  deterministic and offline. Language-agnostic.
---

# Acceptance Testing

An acceptance test proves a behavior runs end to end through the whole vertical, not
that a unit works. A slice usually has several (a happy path plus its negative and edge
flows); all of them green is the slice's done-criterion.

## Rules
- **Drive the system's own entry point** so the whole vertical runs. Don't mock the
  port and test the halves separately when the behavior under test is end-to-end.
- **Stub external boundaries in-process.** Any test that crosses a network/service
  boundary runs against an in-process stub of that boundary: a real stub server on
  an ephemeral port, with the dependency URL injected via config. Never the live
  dependency. Deterministic and offline.
- **Pick the ecosystem's HTTP-stub tool:** WireMock (Java), nock/msw (JS/TS),
  responses (Python), httptest (Go), or equivalent.
- **Keep the layers apart from unit tests.** Lighter mocks are for fast per-slice
  unit tests, not the acceptance layer.
- **Name by given-when-then.** Every acceptance test uses the
  `given<Context>_when<Action>_then<Outcome>` shape (see `delivery-doctrine:test-first`, and
  `delivery-doctrine:gwt-testing` for Java). A descriptive name like
  `page_flags_incomplete_and_zero_length_shifts` is NOT compliant — restructure it,
  e.g. `given_incomplete_page_with_zero_length_shifts_when_validated_then_flagged`.

## The suite (full gear)
The grill names the acceptance behaviors for the whole service (what must be tested);
`delivery-doctrine:thin-slice-planner` groups them into slices (a slice owns one or more); the actual test
for each behavior is written test-first in its slice and run by name while the slice is
built (per `delivery-doctrine:execution-hygiene`). The per-slice tests accumulate into one suite; the
whole suite runs once, at the close, green against the running app — the "deploy"
finale, a closing run and not a per-iteration gate. Low gear skips the suite.

## Pairing
- Red-green-refactor loop, structure and naming of the test: `delivery-doctrine:test-first`
  (and `delivery-doctrine:gwt-testing` for Java).
- Where behaviors originate: the grill names them (the plan); `delivery-doctrine:thin-slice-planner` maps
  each to a slice; the test is written test-first in that slice.
