# Delivery Doctrine

A gear-based agentic delivery method for Claude Code. Hypothesis-first grilling, thin
vertical slices behind hard alignment gates, an implementer/critic loop built on
superpowers' TDD core, right-sized architecture (hexagonal only where it earns it,
honor existing codebases), and language profiles for Java, Python, and Go.

## What's in the box

- **Doctrine** — injected at session start (SessionStart hook): gears (full / low),
  alignment gates, vertical slicing, per-slice Definition of Done, architecture
  judgment, narration discipline, safe defaults.
- **20 skills** — the method: `grill-fast` (greenfield), `grill-brownfield`,
  `thin-slice-planner` (+ plan-critic gate), `superpowers-seam`,
  `ddd-hexagonal-reviewer`, `fast-path` (low gear), `acceptance-testing`,
  `given-when-then-tests`, `execution-hygiene`, `narration-cue-map`; plus language
  profiles — Java (`spring-boot`, `gwt-testing`, `readable-java-style`, `code-quality`,
  `concurrency-review`, `security-audit`), Python (`python-style`, `pytest-testing`),
  Go (`go-style`, `go-testing`).
- **3 agents** — `implementer` (opus by default; mechanical work is dispatched on
  sonnet), `critic` (opus, 3-lens review), `plan-critic` (opus, coverage/drift check
  before code).
- **Guard hook** — PreToolUse block on destructive commands (`rm -rf`, `sudo`,
  `pkill`/`killall`, force-push in all its spellings — `--force-with-lease` stays
  allowed for stacked-PR restacks, `git reset --hard`, `chmod 777`).
- **Timing hook** — SubagentStop, async, zero tokens: when a subagent finishes,
  appends one JSON line on how it spent the clock (seconds per tool category and per
  doctrine phase — red, green, verification, lint, waiting) to
  `~/.claude/doctrine-metrics/runs.jsonl`. Evidence for tuning the doctrine; read it
  with `python3 hooks/subagent_timing.py summarise`. Set `DOCTRINE_METRICS_DIR` to log
  elsewhere.

## Requirements

- **superpowers plugin** (declared as a dependency; auto-installs if the
  `claude-plugins-official` marketplace is configured, otherwise install it first):
  the doctrine composes with its TDD red-green-refactor core, subagent prompts, and
  code-review template — it does not replace them.
- `python3` on PATH (used by the guard and timing hooks).

## Install

```bash
claude plugin marketplace add https://github.com/vishalswami/delivery-doctrine
claude plugin install delivery-doctrine@delivery-doctrine
```

Verify after install (in a fresh session):
- `/plugin` — delivery-doctrine listed and enabled (superpowers too).
- `/context` — the doctrine text present; skills/agents listed under delivery-doctrine.
- `/hooks` — the SessionStart, PreToolUse and SubagentStop hooks registered.
- Ask "what gear are we in?" — the session should answer from the doctrine.
- On a scratch branch, try `git push --force` — the guard must refuse and point to
  `--force-with-lease`.

## Updating

Maintainer (this repo): make the change, bump `version` in
`.claude-plugin/plugin.json`, commit and push to `main`. The marketplace tracks the
branch, so consumers pick up any new commit.

Consumer (each machine):

```bash
claude plugin marketplace update delivery-doctrine
claude plugin update delivery-doctrine
```

Then restart the session and re-run the verification above.

## Maintenance cadence (monthly review)

Once a month, review the doctrine against real use:
1. **Harvest** — new learnings from the month, admitted only past the bar: cost real
   time or correctness, non-obvious, recurs across projects. Prefer enforcing
   (guard hook) over instructing.
2. **Prune** — remove rules that never fired; keep the doctrine lean (DOCTRINE.md
   ~100 lines, skills ~80).
3. **Drift check** — Claude Code CLI changes (permissions schema, hooks, plugin
   commands, model names) and stack changes (mockery, Go/Spring versions).
4. **Ship** — bump version, push, update machines.

## Recommended user settings

The guard hook enforces the destructive-command blocks. For belt-and-suspenders (and
prompt-free flow), add to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "default",
    "allow": ["Bash", "Read", "Grep", "Glob", "Task", "TodoWrite", "WebFetch", "WebSearch"],
    "ask": ["Edit", "Write", "MultiEdit", "NotebookEdit"]
  }
}
```

This auto-allows read/execute (no prompt spam; the guard hook still blocks the
destructive subset) and keeps every file edit gated for your approval.

## Migrating from loose ~/.claude skills

If you previously ran these as user-level skills/agents, remove the loose copies after
installing the plugin — otherwise both load and double-trigger:
`~/.claude/skills/{grill-fast,grill-brownfield,thin-slice-planner,superpowers-seam,ddd-hexagonal-reviewer,fast-path,acceptance-testing,narration-cue-map,given-when-then-tests,execution-hygiene,gwt-testing,readable-java-style,code-quality,concurrency-review,security-audit,spring-boot,python-style,pytest-testing,go-style,go-testing}`,
`~/.claude/agents/{implementer,critic,plan-critic}.md`, and the doctrine section of
`~/.claude/CLAUDE.md` (the plugin injects it).

## Other tools (Cursor, Codex)

This is a native Claude Code plugin. Cursor/Codex have no standard mechanism for
Claude Code plugins today (superpowers' `.cursor-plugin`/`.codex-plugin` dirs are their
own custom tooling). The skills and agents are plain Markdown — portable by copying
into each tool's own rules/config format if needed.

## Shape of the method

Gate 0: pick the gear (full / low) and commit mode (solo / team-PR) → state your
hypothesis → grill breaks it against ground truth → Gate 1: requirements locked →
thin vertical slices, walking-skeleton-first, plan-critic checks coverage → Gate 2:
slice list approved → per-slice loop (red test → implementer to green → critic on
meaningful slices → green commit) → close: full acceptance suite against the running
app. Low gear (`fast-path`) collapses the ceremony for spikes and small fixes without
dropping test-first, one critic pass, or architecture fit.
