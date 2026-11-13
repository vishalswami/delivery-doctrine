---
name: close-out
description: Use when the user says a full-gear feature is live. Consolidates the slice
  files into plan.md, design.md and deferred.md (only what those docs lack), deletes the
  slice files, then fact-checks the three docs against the merged code, deduplicates
  them and tightens them. One docs PR.
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
   logs, research) stay.
4. **Fact-check, deduplicate, tighten.** Check every claim in the three docs against the
   merged code and the PRs, and correct it to what was built. Say each fact once, in the
   doc it belongs to; replace repeats with a pointer or delete them. Cut anything that no
   longer helps a reader of the live system.
5. **Verify.** A fresh reviewer checks the three docs against the code and the deleted
   slice files (from git history): nothing that mattered lost, nothing stale, nothing
   said twice. Fix its findings; at most two review rounds.
6. **Ship.** One docs PR, merged on the same rule as a wave: the user's go-ahead,
   mergeable under the house rules, every review thread resolved.

## Models
Consolidate and fact-check are analysis → sonnet. The verify review → opus.
