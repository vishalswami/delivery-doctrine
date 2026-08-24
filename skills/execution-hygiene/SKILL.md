---
name: execution-hygiene
description: Use when running tests or any long/slow command. Prevents self-inflicted
  thrash — background a slow run once and wait, thread-dump on hang, kill only the PID
  you own. Language-agnostic.
---

# Execution Hygiene

Rules for running tests and long commands. They exist because the thrash *around* a slow
run usually costs more than the bug that caused it.

- **Launch a slow run once, in the background, and wait for its completion.** No
  sleep/grep polling, and no re-running the whole suite after every edit.
- **On any hang, take a thread dump immediately** instead of waiting out the timeout — it
  names the cause in seconds. The command is stack-specific; see the language profile.
- **Kill only the PID you own.** Never kill a shared tool, or a port you aren't tracking —
  you will take down the run you just launched. (Blanket `pkill`/`killall` are denied at
  the permission layer; the discipline still applies to port-based kills.)
