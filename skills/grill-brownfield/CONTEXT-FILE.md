# Context file format

One agent-instructions file per bounded context, at the context's package root. Claude
Code loads it when an agent opens a file in that package with the Read tool (packages
under the session's working directory; AGENTS.md needs Claude Code v2.1.277 or later), so
it holds what an agent changing the context must not miss; depth stays in the spec docs.

Which file: `CLAUDE.md` if the repository commits any CLAUDE.md from the root down to the
package; `AGENTS.md` only when it commits none (Claude Code ignores AGENTS.md when a
CLAUDE.md is on the path). A personal, gitignored CLAUDE.local.md does not change the
choice; its owner sets Project instructions to `claude-md-and-agents-md` in `/config`.
The repository profile can name another convention.

```md
# <Context name>

<Two or three lines: what this context owns, and what it explicitly does not.>

## Domain terms
- **<Term>**: <definition in domain language>. _Avoid_: <synonyms>.

## Invariants
- <Rule an agent changing this package must not break>, because <reason in a clause>.

## Boundaries
- Upstream: <context or service this one depends on>, via <port, API or event>.
- Downstream: <who consumes this context>, via <API or event>.
- Ports: <named ports and their adapters, where the context is hexagonal>.

## Features
- <Feature>: <one line>. Spec: `docs/specs/<date>-<feature>/` (<in delivery | live>).

## Commands
- <Test, lint or run commands scoped to this package, only where they differ from the repository's.>
```

## Rules
- Under 200 lines; past that, agents follow it less reliably.
- Domain terms follow [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md): terms only, no
  implementation detail, no example dialogue. This section is the context's glossary; no
  CONTEXT.md beside it.
- Feature lines: the grill adds one (in delivery) when it creates or corrects the file;
  close-out sets it live. At most three lines per feature. Spec paths in backticks, never with a leading `@`: an
  `@path` is imported whole into every session that loads the file.
- Facts, not prose. Leave out a section the context has nothing for.
- One context file per bounded context. A nested instruction file inside the context
  holds only mechanics local to its folder; terms, invariants and boundaries live here.
- In shape means: the purpose lines, the sections above that apply, terms and invariants
  as lists rather than buried in prose, and under 200 lines.
