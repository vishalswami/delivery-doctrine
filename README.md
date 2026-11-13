# Delivery Doctrine

A gear-based agentic delivery method for Claude Code. Hypothesis-first grilling, thin
vertical slices behind hard alignment gates, an implementer/critic loop built on
superpowers' TDD core, right-sized architecture (hexagonal only where it earns it,
honor existing codebases), and language profiles for Java, Python, and Go.

## What's in the box

- **Doctrine** — injected at session start (SessionStart hook): gears (full / low),
  alignment gates, vertical slicing, per-slice Definition of Done, architecture
  judgment, narration discipline, safe defaults.
- **21 skills** — the method: `grill-fast` (greenfield), `grill-brownfield`,
  `thin-slice-planner` (waves of parallel PRs, + plan-critic gate), `superpowers-seam`,
  `close-out` (once live: consolidate slice files into plan/design/deferred, delete them, fact-check and tighten the three),
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
  allowed for rebasing a PR after a wave-mate merges, `git reset --hard`, `chmod 777`), plus the
  execution-hygiene rules it enforces rather than instructs: wide test runs (`go test
  ./...` or several whole packages, bare `pytest` or several test directories; one
  package or file stays allowed, `DOCTRINE_WIDE_TESTS=1` opts out) and
  `while`/`until` … `sleep` poll loops.
- **Keep-awake hook** — SessionStart, macOS only: `caffeinate` tied to the session's
  `claude` process, so the machine does not idle-sleep mid-run (in the author's logs, sleep
  was a third of implementer time). Lid-closed still sleeps unless sleep is disabled
  system-wide (`pmset disablesleep`, or an app that sets it); `DOCTRINE_LID_REMINDER=1`
  adds a once-a-day reminder when it is not, and `DOCTRINE_KEEP_AWAKE=0` turns the
  hook off.
- **Timing hook** — SubagentStop, async, zero tokens: when a subagent finishes,
  appends one JSON line on how it spent the clock (seconds per tool category and per
  doctrine phase — red, green, verification, lint, waiting; gaps past 10 minutes,
  the machine asleep or offline, go to `idle` rather than model time) to
  `~/.claude/doctrine-metrics/runs.jsonl`. Evidence for tuning the doctrine; read it
  with `python3 hooks/subagent_timing.py summarise`. Set `DOCTRINE_METRICS_DIR` to log
  elsewhere.
  It stays on your machine: nothing is sent anywhere. Each line holds timings, tool
  categories and the names of uncategorised tools (MCP tool names included), the agent
  and model, the working directory and git branch; never code, prompts or command text.
  `DOCTRINE_METRICS=0` turns it off.

## Repository profile (optional)

The plugin stays generic; facts about one repository live in that repository. Copy
`templates/delivery-doctrine.md` to `.claude/delivery-doctrine.md` (shared with the team)
or `.claude/delivery-doctrine.local.md` (personal; gitignore it) and fill in what applies:
spec folder layout, hot files wave-mates must not both edit, PR and merge rules, worktree
setup and test isolation. The SessionStart hook injects it after the doctrine. Without
one, agents discover and honor the house conventions themselves. The profile is injected
verbatim, so it is trusted like the repository's CLAUDE.md. A session in a git
worktree reads the main checkout's `.local.md`, since the worktree has no copy of it.

## Requirements

- **superpowers plugin** (declared as a dependency; auto-installs if the
  `claude-plugins-official` marketplace is configured, otherwise install it first):
  the doctrine calls its test-driven-development, verification-before-completion,
  requesting-code-review, subagent-driven-development, dispatching-parallel-agents,
  writing-plans and finishing-a-development-branch skills by name and does not replace
  them. Tested with superpowers 7.0.x; the version is not pinned, because superpowers'
  release tags do not follow the `superpowers--v<version>` form a pin needs.
- `python3` on PATH (used by all three hooks).

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

## Optional: fewer permission prompts

The guard hook blocks a short list of destructive commands; it is not a sandbox. If you
want fewer prompts, you can auto-allow reading and searching and keep edits gated, in
`~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Read", "Grep", "Glob", "Task", "TodoWrite", "WebFetch", "WebSearch"],
    "ask": ["Edit", "Write", "MultiEdit", "NotebookEdit"]
  }
}
```

Adding `"Bash"` to `allow` runs every shell command without asking, with only the guard
hook's blocklist as a brake. Do that only if you accept that risk.

## Switches

| Variable | Default | Effect |
|---|---|---|
| `DOCTRINE_WIDE_TESTS=1` | off | prefix one command to allow a wide test run past the guard |
| `DOCTRINE_KEEP_AWAKE=0` | on | stop the keep-awake hook (macOS) |
| `DOCTRINE_LID_REMINDER=1` | off | daily reminder when system sleep is not disabled (macOS) |
| `DOCTRINE_METRICS=0` | on | stop the timing hook |
| `DOCTRINE_METRICS_DIR` | `~/.claude/doctrine-metrics` | where the timing log goes |

Set them in the `env` block of `~/.claude/settings.json`.

## Other tools (Cursor, Codex)

This is a native Claude Code plugin. Cursor/Codex have no standard mechanism for
Claude Code plugins today (superpowers' `.cursor-plugin`/`.codex-plugin` dirs are their
own custom tooling). The skills and agents are plain Markdown — portable by copying
into each tool's own rules/config format if needed.

## Shape of the method

Gate 0: pick the gear (full / low) and commit mode (solo / team-PR) → state your
hypothesis → grill breaks it against ground truth → Gate 1: requirements locked →
thin vertical slices grouped into as few waves as possible, walking-skeleton-first,
plan-critic checks coverage and wave-mate collisions → Gate 2: wave plan approved →
per wave: every slice starts together off main, one implementer each in its own
worktree (red test → green → critic on meaningful slices → PR) → Gate 3: all the
wave's PRs shown together, merged on the user's go-ahead once mergeable with every
thread resolved → next wave → close: full acceptance suite against the running app →
once live, close-out consolidates the slice files into plan.md, design.md and deferred.md, deletes them, and fact-checks and tightens the three docs.
Low gear (`fast-path`) collapses the ceremony for spikes and small fixes without
dropping test-first, one critic pass, or architecture fit.

## Maintainer notes

### Monthly review

Once a month, review the doctrine against real use:
1. **Harvest** — new learnings from the month, admitted only past the bar: cost real
   time or correctness, non-obvious, recurs across projects. Prefer enforcing
   (guard hook) over instructing.
2. **Prune** — remove rules that never fired; keep the doctrine lean (DOCTRINE.md
   ~100 lines, skills ~80).
3. **Drift check** — Claude Code CLI changes (permissions schema, hooks, plugin
   commands, model names) and stack changes (mockery, Go/Spring versions).
4. **Ship** — bump version, push, update machines.

### Migrating from loose ~/.claude skills

If you previously ran these as user-level skills/agents, remove the loose copies after
installing the plugin — otherwise both load and double-trigger:
`~/.claude/skills/{grill-fast,grill-brownfield,thin-slice-planner,superpowers-seam,ddd-hexagonal-reviewer,fast-path,acceptance-testing,narration-cue-map,given-when-then-tests,execution-hygiene,gwt-testing,readable-java-style,code-quality,concurrency-review,security-audit,spring-boot,python-style,pytest-testing,go-style,go-testing}`,
`~/.claude/agents/{implementer,critic,plan-critic}.md`, and the doctrine section of
`~/.claude/CLAUDE.md` (the plugin injects it).

## License and credits

MIT — see `LICENSE`. Some skills are adapted from Matt Pocock's
[skills](https://github.com/mattpocock/skills) (MIT), Piotr Mińkowski's
[claude-ai-spring-boot](https://github.com/piomin/claude-ai-spring-boot) (Apache-2.0) and
Decebal Suiu's [claude-code-java](https://github.com/decebals/claude-code-java) (MIT); see
`THIRD_PARTY_NOTICES.md`.
