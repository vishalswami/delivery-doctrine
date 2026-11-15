# Changelog

What changed for users in each release. Update with `claude plugin marketplace update
delivery-doctrine` then `claude plugin update delivery-doctrine`, and restart your sessions.

## 0.6.0

- **Skill check.** Before acting on each message, the agent writes a one-line YES/NO for the
  skills that could apply and loads every YES. Candidates follow the repository's language.
  `DOCTRINE_SKILL_CHECK=0` turns it off.
- **Guard switches.** `DOCTRINE_GUARD=0` turns the guard off; `DOCTRINE_GUARD_HYGIENE=0` keeps
  only the destructive-command blocks and drops the wide-test and sleep-poll blocks.
- **diagnose** skill and `doctrine-diagnose` command: explains why a session did not follow the
  doctrine (skills never loaded, guard denials, missing language profile) and writes a scrubbed
  bundle for a bug report.
- The guard has a regression suite (`tests/guard.py`), run in CI on Linux and macOS.
- README: uninstalling, contribution policy.

## 0.5.3 to 0.5.8

- Guard hardening after adversarial review. It matches the raw command, so quoting a word,
  splitting flags (`-r -f`), putting `git -C dir` first or continuing a line with a backslash
  no longer slips a destructive command past it. A commit message that only mentions such a
  command is refused too; write it to a file and use `git commit -F <file>`.
- `plugin.json` gains homepage and repository; third-party notices completed.

## 0.5.2

- Java skills trimmed to their checklists, depth moved to `references/`.
- Language baselines pinned to the oldest fully supported releases: Java 25 with Spring Boot 4.1,
  Go 1.26, Python 3.14.
- Examples made neutral (orders, customers, bookings).

## 0.5.1

- README rewritten, with a flow diagram. Commit messages say what changed.

## 0.5.0

- Language profiles: new `java-domain` skill; domain types and layout for Go and Python, with
  adapter, concurrency and security references. Profiles load in the main session too, not
  only in subagents.

## 0.4.0

- Stands on its own: the parts of superpowers it relied on are adapted in, with credit. New
  skills `delivery-loop`, `test-first`, `systematic-debugging`, `review-feedback`; commands
  `build-scratch` and `review-package`.
- Long-session anchor: past 150k tokens of context, restates the core rules next to each message.
- Eval suite, run with `claude plugin eval . --scaffold`.

## 0.3.1

- Context files (CLAUDE.md or AGENTS.md) per part of the codebase, kept current at close-out.
- Model tiers (deep, standard, fast) with per-task and per-agent overrides in a personal profile.

## 0.3.0

- Repository profiles that are symlinks are ignored; profiles are capped in size.

## 0.2.0

- Waves of parallel slices, close-out after launch, repository profiles.

## 0.1.x

- First releases: the doctrine, skills, implementer and critic agents, the guard and session
  hooks; local test runs scoped to what changed; keep-awake on macOS.
