# Third-party notices

Some skills are adapted from other open-source projects. Each keeps its original
license; the full texts are in `LICENSES/`. All of them were modified for this plugin
(cross-references to the doctrine's skills, the doctrine's no-comments rule, trimmed or
rewritten sections). The files adapted from superpowers were rewritten, not copied: the
rules were re-scoped to the doctrine (scoped verification, waves, gates) and restated in its
voice.

| Files | Source | License |
|---|---|---|
| `skills/grill-brownfield/` (SKILL.md, ADR-FORMAT.md, CONTEXT-FORMAT.md) | [mattpocock/skills](https://github.com/mattpocock/skills) — `grill-with-docs` and `domain-modeling` (SKILL.md, ADR-FORMAT.md, CONTEXT-FORMAT.md, since renamed GLOSSARY-FORMAT.md), as of revision `e74f0061`. Copyright (c) 2026 Matt Pocock | MIT — `LICENSES/MIT-mattpocock-skills.txt` |
| `skills/code-quality/`, `skills/spring-boot/` (including `references/`) | [piomin/claude-ai-spring-boot](https://github.com/piomin/claude-ai-spring-boot); `skills/code-quality/` as of revision `0d23826d`, `skills/spring-boot/` as of revision `31fe1d51`. Copyright 2026 Piotr Mińkowski | Apache-2.0 — `LICENSES/Apache-2.0-piomin-claude-ai-spring-boot.txt` |
| `skills/concurrency-review/`, `skills/security-audit/` | [decebals/claude-code-java](https://github.com/decebals/claude-code-java). Copyright (c) 2026 Decebal Suiu | MIT — `LICENSES/MIT-decebals-claude-code-java.txt` |
| `skills/delivery-loop/`, `skills/systematic-debugging/`, `skills/test-first/`, `skills/execution-hygiene/`, `skills/thin-slice-planner/` (Interfaces field, steps format), `agents/critic.md`, `agents/implementer.md` (report file, short return, no subagents, fix rounds), `agents/plan-critic.md` (interface and mandated-defect checks), `scripts/build-scratch`, `scripts/review-package` | [obra/superpowers](https://github.com/obra/superpowers) v7.0.2 — `test-driven-development` (SKILL.md, writing-good-tests.md), `verification-before-completion`, `executing-plans` (inline execution, long output to a file), `requesting-code-review` (code-reviewer.md), `writing-plans` (interfaces, step shape), `subagent-driven-development` (SKILL.md, implementer-prompt.md, task-reviewer-prompt.md, re-review-prompt.md, references/; scripts `review-package`, `sdd-workspace`, `sdd-repo`), `dispatching-parallel-agents`, `finishing-a-development-branch`, `using-git-worktrees`, `systematic-debugging` (SKILL.md, root-cause-tracing.md, condition-based-waiting.md, defense-in-depth.md, find-polluter.sh). Copyright (c) 2025 Jesse Vincent | MIT — `LICENSES/MIT-obra-superpowers.txt` |
