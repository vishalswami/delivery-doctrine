# Repository profile for delivery-doctrine
<!--
Optional. Copy to .claude/delivery-doctrine.md in your repository (shared with the team),
.claude/delivery-doctrine.local.md (personal; add it to .gitignore), or
~/.claude/delivery-doctrine.md (personal, every repository; the natural home for Models). The plugin injects
it after the doctrine at session start. Keep only the sections that apply; facts, not prose.
Sessions in a git worktree read the main checkout's .local.md, since the worktree has no copy.
-->

## Models
<!-- Keep only the lines you change; values are model aliases (opus, sonnet, haiku, fable).
An agent entry covers every dispatch of that agent; otherwise task kind, then tier. -->
- deep: <default opus — domain code and every review>
- standard: <default sonnet — mechanical code and analysis>
- fast: <default haiku — retrieval only>
- <task kind: domain | review | mechanical | analysis | retrieval>: <alias>
- <agent: implementer | critic | plan-critic>: <alias, e.g. critic: fable>

## Specs
- Folder: <e.g. docs/specs/<date>-<feature>/ with plan.md, design.md, deferred.md, slices.md, slices/>
- Context files: <only if not the default: one CLAUDE.md, or AGENTS.md in a repo without CLAUDE.md, at each bounded context's package root>
- Size budgets: <only if different from close-out's: context file 200 lines, plan 150, design 300, deferred 100>

## Hot files (wave-mates must not both edit)
- <e.g. db/migrations/ — one migration per wave>
- <e.g. cmd/server/main.go — registration points pre-created in the skeleton wave>
- <e.g. openapi/ and generated clients — regenerate, never hand-merge>

## Pull requests and merging
- Opening: <title format, labels that trigger review bots, reviewers>
- Merging: <squash / merge queue / required checks; who may merge>
- Merging to main deploys to: <environment, or "nothing">

## Worktrees and local runs
- Setup per worktree: <commands a fresh worktree needs, per stack>
- Tests in parallel worktrees: <isolated, or what to set (database name, ports)>
- Starting the app in a worktree: <command, or "lead only, after merge">
