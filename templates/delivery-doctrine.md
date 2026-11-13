# Repository profile for delivery-doctrine
<!--
Optional. Copy to .claude/delivery-doctrine.md in your repository (shared with the team)
or .claude/delivery-doctrine.local.md (personal; add it to .gitignore). The plugin injects
it after the doctrine at session start. Keep only the sections that apply; facts, not prose.
Sessions in a git worktree read the main checkout's .local.md, since the worktree has no copy.
-->

## Specs
- Folder: <e.g. docs/specs/<date>-<feature>/ with plan.md, design.md, deferred.md, slices.md, slices/>

## Hot files (wave-mates must not both edit)
- <e.g. migrations/atlas.sum — one migration per wave>
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
