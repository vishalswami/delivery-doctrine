---
name: delivery-loop
description: Use after Gate 2 to run the per-wave loop, and for commits and PRs in any gear.
  Commit modes, the build scratch dir and ledger, implementer dispatch into worktrees, report
  handling, review packages and the critic, the fix loop, push and PR, the wave gate, merge
  and cleanup, and inline mode.
allowed-tools: Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Delivery Loop

The lead (the main session) runs the loop; implementers and critics are its workers. The lead
dispatches, keeps the ledger, packages reviews and rules on conflicts. It does not write a
dispatched slice's code: a lead fix skips review and fills the context the loop runs on.
Inside a wave nothing waits on the user; the wave gate waits on nothing else.

## Commit modes (picked with the gear at Gate 0)
- **Solo** (take-homes, demos, spikes; the default with no shared repo): local `git init`, no
  remote. It overrides a project's git ban only when the ban states no reason.
- **Team** (a repo with a PR workflow): a branch per slice off the house base branch, one PR
  per slice, the house conventions for branch names, messages, PR titles and labels.
- Both: one commit per green slice (its tests and integration green; never red or broken),
  named for the slice and its behavior ("slice 3: reject expired JWT with 401"), never "wip".

## Build scratch and ledger
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/build-scratch <spec-folder>` prints the build's scratch
dir: git-ignored, at the main checkout's root, shared by every worktree. It holds `ledger.md`,
one `slice-<N>-report.md` per slice and the review packages; always use the absolute path.
Compaction erases what the conversation held, and a lead that lost its place re-dispatches
finished slices. The ledger is the memory: one line per event, written by the lead alongside
the action it records, never in a later turn.
```
S3 dispatched: s3-expired-jwt, <worktree>, BASE 1a2b3c4, opus, agent <id>
S3 DONE: 1a2b3c4..5d6e7f8 · S3 review 1: With fixes, open: <one-liners>
S3 PR: <url> · S3 minor: <one-liner> · S3 ruling: <decision> — <why> — <cost if wrong>
wave 1 merged: <PRs>
```
Once context is compacted, the ledger and `git log` outrank recollection: a slice with a DONE
line and its commits is never redone. Close-out deletes the dir.

## Per-wave loop
1. **Start.** Every slice of the wave starts off current main, one implementer each, all
   dispatched in one message so they run in parallel. Record BASE (`git rev-parse main`, or
   the house base branch) first; never `HEAD~1`, which loses all but the last commit. The
   lead's checkout sits on that commit and each dispatch sets `isolation: worktree`;
   `git worktree add` only where the repository profile names a location, and that location
   is git-ignored. On a 429, retry; never widen.
2. **Dispatch** content: one line on where the slice fits; the slice file path ("read this
   first; its values are exact"); interfaces from merged slices the file cannot know; the
   lead's ruling on any ambiguity; the report file path; `model` per the doctrine's task-type
   binding. Never pasted history or another slice's report. Small edits of one shape across
   files (the same field added to five DTOs) go in one standard-tier dispatch that names
   each file and the edit it gets.
3. **Worktree cost.** A fresh worktree has no installed dependencies; install only what the
   slice's stack needs. Before a repo's first wave, confirm tests run concurrently from
   separate worktrees (shared test database, fixed ports); if not, give each its own database
   or port, or verify those slices one at a time. Starting the app inside a wave needs
   per-worktree ports; otherwise the lead does it after merge.
4. **Wait** on completion notifications, never a poll. Meanwhile: ledger lines, packaging a
   finished slice's review, reading reports.
5. **Report.** DONE is a claim: `git -C <worktree> log --stat BASE..HEAD` must show the
   commits and files the report names before review. DONE_WITH_CONCERNS: read the concerns;
   correctness or scope doubts are settled before review. NEEDS_CONTEXT: supply it and resume.
   BLOCKED: more context, a more capable model, a smaller slice, or a ruling that corrects
   the plan; never the same dispatch again unchanged.
6. **Review**, tiered: own eyes on a trivial slice, the critic on the rest, in parallel as
   slices finish. `bash ${CLAUDE_PLUGIN_ROOT}/scripts/review-package -C <worktree> -s <spec-folder> BASE HEAD`
   writes the package and prints its path; the critic gets it with the slice file, the
   report file, the worktree and the branch. A dispatch that says "ignore X", "Minor at
   worst" or "the plan decided this" pre-judges the review to dodge a fix round. Every Set
   aside line is the lead's to rule on before the slice is done; a real gap joins the findings.
7. **Fix loop**, only while Critical or Important findings are open; at most 3 critic passes.
   Resume the same implementer (SendMessage) with the whole findings list, never one fixer per
   finding. It fixes, reruns the covering tests and appends a fix report to its file. Package
   the fix range (reviewed HEAD..new HEAD) and resume the same critic for the scoped
   re-review. A finding still open after a round goes to a fresh implementer (a more capable
   model if the first ran standard tier), given the findings and the report file: the first
   could not see its own problem. Minors go to the ledger, never into the loop.
8. **At the cap**, the lead rules on each open finding, a ledger line each: critic wrong →
   the code stands; real but nothing builds on it → deferred; real and load-bearing → the
   smallest unblocking change, carried into every dependent dispatch. Nothing is dropped
   silently, and ruling before the cap is pre-judging under another name.
9. **Push and PR** (team mode): the lead pushes once per slice after review and opens the
   PR. Review bots run after push and do not replace the critic; their threads and human
   comments are handled per `delivery-doctrine:review-feedback`, down to resolving each. A push the remote refuses
   means someone else pushed: fetch and look, never force. A PR's worktree stays while it is open.
10. **Wave gate.** When every PR of the wave is open and critic-clean, show them together
   with every ruling made inside the wave. On the go-ahead, merge each once mergeable under
   the house rules (required checks, approvals; the repository profile names them, or ask
   for the base branch) with every thread resolved. Enqueue at once the PRs the wave table
   does not order; an ordered one waits for what it follows or its release check. Rebase
   only a PR that conflicts (standard tier); regenerate generated files, never hand-merge.
11. **Cleanup**, after each merge: `git worktree remove <path>`, `git worktree prune`,
   `git branch -d <branch>`. A refused removal means files exist only there: list them
   (`git -C <path> status --porcelain`) and ask. `--force` and `branch -D` only when the
   user asked to discard the work.
12. **Next wave** starts when every PR of this one is merged, all its slices off the new main.
   A slice that cannot clear inside its wave moves to the next (its PR to draft) with what
   depends on it, and is rebased when that wave starts. Back to Gate 2 only when a
   dependency or the plan itself changed.

Solo mode runs the same loop locally: the gate is every branch critic-clean, and merging is
into local main on the go-ahead, with the slice's tests run on the merged tree before cleanup.

## Inline mode
Low gear and live sessions: the lead is the implementer, slices run one after another on a
branch in place (a worktree only when the profile asks; `EnterWorktree` then). Reread the
slice file before each slice: memory keeps a summary, the file keeps the values. A wrong
plan gets a ruling and a ledger line; wrong code gets `delivery-doctrine:systematic-debugging`.
The critic stays a subagent, once per meaningful slice, because the author's own read shares
the author's blind spots. Its Critical and Important findings are fixed test-first, a
reproducing test red then green, with no re-review; minors go to the ledger. In a live
session the wave table's status column can serve as the ledger.

## Models and narration
`model` is set on every dispatch. Turn count beats token price: a cheaper model that takes
three times the turns costs more. Outside presented sessions (`delivery-doctrine:narration-cue-map`)
the lead says one short line between steps; the ledger carries the record.
