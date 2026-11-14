---
name: ddd-hexagonal-reviewer
description: Use to review a slice's architecture — right-sizing (is this over-engineered
  for the scope?) and fit (does it respect the codebase's architecture?). Enforces
  hexagonal/DDD rules only where hexagonal is the chosen or house style; on other
  codebases it conforms and flags imposed structure. In low gear it runs in conform mode
  when the house style is hexagonal/DDD; skipped only for a greenfield throwaway.
---

# DDD / Hexagonal Reviewer

Review a slice's architecture on two axes: is it right-sized (not over-engineered),
and does it fit the codebase it lives in. Used by the critic's Stage 2. In low gear it
still runs in conform mode when the house style is hexagonal/DDD; it is skipped only for
a greenfield throwaway with no architecture to honor.

## Applicability guard (decide first)
- **Read the house record before judging**: the context file of each touched bounded context
  (AGENTS.md or CLAUDE.md; format in `delivery-doctrine:grill-brownfield`'s CONTEXT-FILE.md),
  the repository profile, and the specs and ADRs they point to. A choice recorded there as
  deliberate is not a finding (a SQL-only status guard that avoids a read-update-persist
  race); flag only where the code departs from its own record.
- **House names and structure first, for consistency** (the canonical rule; the language
  profiles point here). Where the house has a structure under other names, conform to its
  names; where it lacks one these rules or the language profile call for, introduce it
  inside the house's architecture, never a different architecture (below). A house rule
  that is plainly bad practice (bugs, security or correctness risk, or working against
  consistency) is neither followed nor bypassed silently: a finding that names it, gives
  the reason and proposes the better practice for the user to decide. This governs names
  and structure only; the doctrine's hard rules (zero comments, test-first) hold in every
  house.
- **Greenfield with hexagonal chosen, or brownfield whose house style is hexagonal**
  → apply the hexagonal rules below.
- **Brownfield with a different established architecture** → do NOT impose hexagonal.
  Conform to the existing patterns. Flag only violations of the house style, plus any
  structure this change imposes that the codebase doesn't already use. A move to
  hexagonal is a separate, explicitly granted refactor, never smuggled into a slice.
- **A generated skeleton or near-empty scaffold is greenfield, not a house style.**
  IntelliJ/Maven boilerplate (an Application class, config, an empty package) is not an
  architecture to conform to — design the structure. "Existing architecture" means a real
  codebase with patterns actually in use, not a blank scaffold.

## Hexagonal rules (when applicable)
- Dependencies point inward. The domain is pure: no framework imports or annotations
  on domain types (no Jackson, no Spring on domain).
- Ports vs adapters: a `ports/out` interface for anything the domain needs from
  outside (sinks, readers, clocks, encryptors); a `ports/in` interface per use case where
  the language profile calls for one. Depend on ports, never concrete adapters. Port and
  adapter are roles, not directory names: the language profile says how its language
  spells them (Go and Python declare the port at its consumer).
- Mechanism/technology names (Jwt, AesGcm, Kinesis, Spring) appear ONLY in adapter
  class names — never in domain or port names.
- Wire/serialization lives in an adapter (DTO + hand-written mapper), never on domain
  value objects.
- Invent nothing: no Aggregate Root without mutable invariants; no Repository without
  persistence-by-identity. Over-applying DDD is as wrong as under-applying it. Let the
  domain lead; reach for a port only when crossing out of it.

## Over-engineering check (both directions)
- Speculative structure: ports, repositories, entities, or abstractions the slice
  doesn't use. Flag them.
- Imposed structure: a pattern introduced that the surrounding codebase doesn't use.
  Flag that too — it fights the house style.
- When something is kept deliberately simple, the code or the slice note should say
  why: "port here because it's a real boundary; plain here because it doesn't earn it."

## Output
Feed findings into the critic's report, ranked by severity. Architecture
issues are usually Important, unless they break a boundary the domain depends on, which
is Critical.

## Pairing
- Invoked by `critic` Stage 2. Java specifics: `delivery-doctrine:java-domain` (domain types,
  layout, wiring), `delivery-doctrine:spring-boot`, `delivery-doctrine:code-quality`,
  `delivery-doctrine:readable-java-style`. The layered examples in `delivery-doctrine:spring-boot` / `delivery-doctrine:code-quality` are
  illustrative Spring wiring, not the mandated architecture — architecture is decided
  here, per context.
- Go: `delivery-doctrine:go-style` (Domain types, Layout and wiring). Python:
  `delivery-doctrine:python-style` (same sections).
