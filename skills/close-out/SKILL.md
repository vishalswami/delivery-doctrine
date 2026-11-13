---
name: close-out
description: Use when the user says a full-gear feature is live. Consolidates the slice
  files into plan.md, design.md and deferred.md (only what those docs lack), deletes the
  slice files, fact-checks, deduplicates and tightens the three docs, updates the context
  file of each bounded context touched, and keeps all of them within size. One docs PR.
---

# Close-out

Slice files are build notes. Once the feature is live they are deleted, and the three
lasting docs are left accurate, without repetition, and short. Trigger: the user says
the feature is live; never run it unprompted.

## The three docs
- **plan.md**: what shipped. Each slice by its stable number with its PR link, and a
  Status line saying what is live and what is not. Where the build departed from the
  plan, say so in one line (planned X, built Y, because Z).
- **design.md**: how it works now: decisions, constraints, verified facts, how to run
  and operate it.
- **deferred.md**: what was not built, each with where it would slot in and any open
  question.

## Steps
1. **Consolidate.** Read slices.md and slices/*.md against the three docs. Most of it is
   already there. Move only what the docs lack and still matters after launch: a
   decision, a constraint, a verified fact, a deferral, an operational step. Copy
   nothing by default. Drop one-off build steps (a slice's manual test plan, its "done
   when"), branch names and the wave table's merge order. Slice numbers stay as they
   were; other documents cite them.
2. **Unshipped work.** A slice that never merged, or went to another project, goes into
   deferred.md, or into the receiving spec with a pointer left behind.
3. **Delete.** `git rm -r` slices/ and slices.md. Search the repository for links to them
   and point each at the doc that now holds the fact. Other files in the folder (grill
   logs, research) stay. Remove the build's git-ignored scratch dir too (ledger, reports,
   review packages): `rm -r` the path that
   `bash ${CLAUDE_PLUGIN_ROOT}/scripts/build-scratch <spec-folder>` prints.
4. **Fact-check, deduplicate, tighten.** Check every claim in the three docs against the
   merged code and the PRs, and correct it to what was built. Say each fact once, in the
   doc it belongs to; replace repeats with a pointer or delete them. Cut anything that no
   longer helps a reader of the live system.
5. **Update the context files.** For each bounded context the feature touched, update its
   context file (shape and file choice: grill-brownfield's CONTEXT-FILE.md; create it if
   missing): the feature's line under Features (live, spec path in backticks), the domain
   terms design.md recorded during the grill, and any invariant or boundary the feature
   added; remove those terms from design.md once they are there. Only what an agent
   changing that package must not miss; depth stays in the spec docs. Change nothing else
   in the file without the user's yes.
6. **Size.** Instruction files lose adherence past about 200 lines (Claude Code's own
   guidance), so a feature adds at most three lines plus its new terms and invariants. The
   spec docs are read on demand: plan.md under about 150 lines, design.md under 300,
   deferred.md under 100. Over budget, cut, and move depth down (context file →
   design.md), never up. If the context file as a whole is past 200 lines, propose a trim
   in the PR and apply it only on the user's yes. Budgets in the repository profile win.
7. **Verify.** A fresh reviewer checks the three docs against the code and the deleted
   slice files (from git history): nothing that mattered lost, nothing stale, nothing
   said twice; the context files true and within budget. Fix its findings; at most two
   review rounds.
8. **Ship.** One docs PR, merged on the same rule as a wave: the user's go-ahead,
   mergeable under the house rules, every review thread resolved.

## Models
Consolidate and fact-check are analysis → standard tier. The verify review → deep tier.
