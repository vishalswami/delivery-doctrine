---
name: execution-hygiene
description: Use when running tests, lint, or any long/slow command. Prevents
  self-inflicted thrash — scope every local check to what you changed and run it in the
  foreground, thread-dump on hang, kill only the PID you own. Language-agnostic.
---

# Execution Hygiene

Rules for running tests, lint and long commands. They exist because the thrash *around*
a run usually costs more than the bug that caused it: measured on real implementer
runs, writing the failing test and the code took under a tenth of the clock, and
running and waiting on tests and lint took over half. Test-first is cheap; breadth of
verification is the cost. Scope every local check to the change — the full suites are
CI's, on every push.

- **Run only the tests you added or changed, by name or pattern** (the exact flag is in
  the language profile). At slice close, one run of the touched package is fine; never
  `./...`, several whole packages, or the full suite as a local gate. The guard hook
  denies those; prefix `DOCTRINE_WIDE_TESTS=1` only when a wide run is truly needed.
- **The race detector (or equivalent heavy mode) runs once, at the end, on the tests
  that exercise concurrency** — not on every red/green iteration.
- **Lint and format only the files or packages you touched**, not the whole repository.
  For a rename or signature change, compile and vet the touched packages; the compiler
  finds every call site.
- **Start the application only when wiring changed** (entry point, registration,
  configuration), not for every slice.
- **Run scoped checks in the foreground and wait.** A scoped run is short. No background
  runs polled with sleep loops (the guard hook denies `while`/`until` … `sleep`), and
  no re-running the whole suite after every edit. The rare run that must be long is
  launched once, in the background, and waited for through the harness's completion
  notice, never a poll.
- **On any hang, take a thread dump immediately** instead of waiting out the timeout — it
  names the cause in seconds. The command is stack-specific; see the language profile.
- **Kill only the PID you own.** Never kill a shared tool, or a port you aren't tracking —
  you will take down the run you just launched. (Blanket `pkill`/`killall` are denied at
  the permission layer; the discipline still applies to port-based kills.)
