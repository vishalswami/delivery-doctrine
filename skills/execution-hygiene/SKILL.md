---
name: execution-hygiene
description: Use when running tests, lint, or any long/slow command, and before
  claiming anything is green, fixed or done. Prevents self-inflicted thrash — scope every
  local check to what you changed and run it in the foreground, long output to a file,
  thread-dump on hang, kill only the PID you own — and makes every claim rest on fresh
  output. Language-agnostic.
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
- **Long output goes to a file; read its tail.** A test log, a build or a package lint
  goes to a file in a git-ignored scratch dir or the session scratchpad, and you read the
  summary and the first failure, then search the file for anything else. A whole log in
  context crowds out the work it was run for. An implementer writes to its own worktree's
  `.delivery-doctrine/` (its `.gitignore` holds `*`), since a worktree subagent cannot write
  into the main checkout; the lead uses the dir `build-scratch <spec-folder>` prints. Always
  an absolute path.
  ```
  go test -run '^TestOrder' ./internal/order > /work/shop/.claude/worktrees/s3/.delivery-doctrine/run.log 2>&1; echo "exit=$?"
  tail -n 40 /work/shop/.claude/worktrees/s3/.delivery-doctrine/run.log
  ```

## Evidence before claims
"Green", "fixed" and "done" are claims, and a claim rests on output produced in this
turn: not memory, not an earlier run, not a report.
1. Name the command that proves it: the scoped check above; breadth is CI's.
2. Run it.
3. Read the exit code and the output: failures, errors, stray warnings.
4. Claim with the evidence (the command and its result in a line), or state the real
   status if the output disagrees.

What each claim needs:
- **Tests pass**: zero failures in the run, and output free of new warnings.
- **Lint clean, builds**: that tool's own exit 0; a clean lint says nothing about the build.
- **Bug fixed**: the reproduction test of the original symptom, seen red, now green.
- **Regression test works**: seen red, then green. Never watched it fail? Revert the fix,
  watch it fail, restore.
- **Slice meets its spec**: each acceptance behavior checked against the slice file, not
  inferred from a green run.
- **A subagent's DONE**: its report is a claim. The evidence is the branch:
  `git -C <worktree> log --stat BASE..HEAD` shows the commits and files the report names.
  The lead checks it before dispatching the critic.

"Should pass", "probably", "seems to", or "Done!" before a run all mean the check has
not happened yet: run it.
