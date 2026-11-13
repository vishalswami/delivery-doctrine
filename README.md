# Delivery Doctrine

A gear-based agentic delivery method for Claude Code. Hypothesis-first grilling, thin
vertical slices behind hard alignment gates, a test-first implementer/critic loop,
right-sized architecture (hexagonal only where it earns it, honor existing codebases),
and language profiles for Java, Python, and Go.

## What's in the box

- **Doctrine** — injected at session start (SessionStart hook): gears (full / low),
  alignment gates, vertical slicing, per-slice Definition of Done, architecture
  judgment, narration discipline, safe defaults.
- **23 skills** — the method: `grill-fast` (greenfield), `grill-brownfield`,
  `thin-slice-planner` (waves of parallel PRs, + plan-critic gate), `delivery-loop` (the
  per-wave loop: worktrees, ledger, review packages, fix loop, PRs, wave gate),
  `close-out` (once live: consolidate slice files into plan/design/deferred, delete them,
  fact-check and tighten the three, update each bounded context's context file),
  `ddd-hexagonal-reviewer`, `fast-path` (low gear), `acceptance-testing`, `test-first`,
  `execution-hygiene`, `systematic-debugging`, `review-feedback`, `narration-cue-map`; plus
  language profiles — Java (`spring-boot`, `gwt-testing`, `readable-java-style`,
  `code-quality`, `concurrency-review`, `security-audit`), Python (`python-style`,
  `pytest-testing`), Go (`go-style`, `go-testing`).
- **2 commands in `bin/`** — `build-scratch` (the lead's git-ignored scratch dir at the main
  checkout's root) and `review-package` (one file holding a slice's commits, stat and diff
  for the critic). Claude Code puts `bin/` on the Bash tool's PATH while the plugin is
  enabled, so the skills call them by bare name. claude.ai and Cowork do not install a
  plugin with a top-level `bin/`; this one is for Claude Code.
- **3 agents** — `implementer` (opus by default, the deep tier unless remapped; mechanical
  work is dispatched on the standard tier), `critic` (deep, 3-lens review), `plan-critic`
  (deep, coverage/drift check before code). Tiers map to models in your profile; defaults
  opus, sonnet, haiku.
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
## Repository profile (optional)

The plugin stays generic; facts about one repository live in that repository. Copy
`templates/delivery-doctrine.md` to `.claude/delivery-doctrine.md` (shared with the team)
or `.claude/delivery-doctrine.local.md` (personal; gitignore it) and fill in what applies:
spec folder layout, where domain instructions live, hot files wave-mates must not both
edit, PR and merge rules, worktree setup and test isolation. The SessionStart hook injects
it after the doctrine. A personal `~/.claude/delivery-doctrine.md` applies to every
repository and is injected before the repository's; use it for the `## Models` section,
which maps the doctrine's three tiers (deep, standard, fast; default opus, sonnet, haiku)
to the models you have, and can go finer: a task kind (`mechanical: opus`) or a single
agent (`critic: fable`). Values are model aliases; an agent entry beats a task kind, which
beats a tier. Without
one, agents discover and honor the house conventions themselves. The profile is injected
verbatim, so it is trusted like the repository's CLAUDE.md. A session in a git
worktree reads the main checkout's `.local.md`, since the worktree has no copy of it.

## Requirements

- `python3` on PATH (used by the guard and profile hooks).
- `bash` and `git` (used by the `bin/` commands).
- `gh`, for team mode's PRs and review threads.

## Install

```bash
claude plugin marketplace add https://github.com/vishalswami/delivery-doctrine
claude plugin install delivery-doctrine@delivery-doctrine
```

Verify after install (in a fresh session):
- `/plugin` — delivery-doctrine listed and enabled, with no errors.
- `/context` — the doctrine text present; the 23 skills and 3 agents listed under
  delivery-doctrine.
- `/hooks` — the SessionStart and PreToolUse hooks registered.
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

To run the two bundled commands without a prompt, add `"Bash(build-scratch *)"` and
`"Bash(review-package *)"` to `allow`. They read git and write only the scratch dir or the
package file you name.

Adding `"Bash"` to `allow` runs every shell command without asking, with only the guard
hook's blocklist as a brake. Do that only if you accept that risk.

## Switches

| Variable | Default | Effect |
|---|---|---|
| `DOCTRINE_WIDE_TESTS=1` | off | prefix one command to allow a wide test run past the guard |
| `DOCTRINE_KEEP_AWAKE=0` | on | stop the keep-awake hook (macOS) |
| `DOCTRINE_LID_REMINDER=1` | off | daily reminder when system sleep is not disabled (macOS) |

Set them in the `env` block of `~/.claude/settings.json`.

## Other tools (Cursor, Codex)

This is a native Claude Code plugin. Cursor/Codex have no standard mechanism for
Claude Code plugins today. The skills and agents are plain Markdown — portable by copying
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

## License and credits

MIT — see `LICENSE`. Some skills are adapted from Matt Pocock's
[skills](https://github.com/mattpocock/skills) (MIT), Piotr Mińkowski's
[claude-ai-spring-boot](https://github.com/piomin/claude-ai-spring-boot) (Apache-2.0) and
Decebal Suiu's [claude-code-java](https://github.com/decebals/claude-code-java) (MIT); the
delivery loop, test-first, execution-hygiene, systematic-debugging and review-feedback
skills, the implementer and critic agents and the two scripts are adapted from Jesse
Vincent's [superpowers](https://github.com/obra/superpowers) (MIT). See
`THIRD_PARTY_NOTICES.md`.
