---
name: review-feedback
description: Use when acting on review findings — from the critic, a human reviewer or a review
  bot — before changing any code. Check each finding against the codebase, clarify unclear
  items before touching any, push back with evidence when one is wrong, fix in order with a
  test each, then reply and resolve in the PR thread. No performative agreement.
---

# Review Feedback

A finding is a claim about the code, made by someone who holds less context than you, or
different context. It earns a change once it is checked, not because of who raised it or
how sure it sounds. The fix shows that you agree; saying so adds nothing.

## Before changing anything
1. **Read the whole list first.** Findings often share a cause, and the third can change
   how you read the first.
2. **Restate each one as a technical requirement**: "`reserve` accepts a negative seat
   count; it must reject it with 400." One you cannot restate is unclear.
3. **Clarify every unclear item before fixing any.** Fixing the clear half first builds on
   a guess about the rest. Ask in one message: which items you understood, which you did not.
4. **Check each against the code.** Is the problem there (read it, run the case)? Would
   the change break a caller or a test? Is there a reason it is this way (blame, an ADR,
   the slice file)? Does it hold on every platform, version and configuration supported?

## Where it comes from
- **The critic** (fix rounds): it read the diff and the slice file. Check and fix; a
  finding you believe is wrong is answered in your fix report with the evidence, and the
  lead rules on it (`delivery-doctrine:delivery-loop`). A plan-mandated finding is the
  user's call.
- **The user**: trusted on intent; still ask when the scope is unclear.
- **Humans on the PR and review bots** usually lack the slice file, the plan and the wave.
  Check harder. A suggestion that contradicts a decision the user already made (the plan,
  an ADR, a gate) goes to the user before any change.
- **"Do it properly"** (make it configurable, add metrics, generalize it): search for
  callers first. If nothing uses it, propose removing it instead of building it out.

## Pushing back
Push back when a finding is wrong for this codebase, breaks working behavior, ignores a
constraint the reviewer could not see, or asks for what nothing uses. Bring evidence: the
test that shows the behavior, the caller that needs it, the line of the spec or ADR. When
unsure, ask a specific question. No defensiveness and no hedging. When checking shows you
were wrong, one line says so ("Checked: `X` does `Y`; fixing.") and the fix follows.

## Fixing
- Order: what blocks the merge (wrong behavior, security, lost data), then the quick ones,
  then the ones that need restructuring.
- One at a time, each with a test that fails before and passes after
  (`delivery-doctrine:test-first`) and its scoped checks (`delivery-doctrine:execution-hygiene`),
  so every result points at one change.
- A finding that turns out to be the symptom of something deeper goes through
  `delivery-doctrine:systematic-debugging` first.

## Replying
State what changed and where, or why the code stands and the evidence:
"Fixed in 3f2a1c9: `reserve` rejects negative counts
(`given_negative_count_when_reserve_then_400`)." No thanks, no praise for the catch, no
announcing agreement: the reply is a fact a reader can check.

On a PR, reply inside the comment's thread, never as a new top-level comment, then resolve
the thread; the wave gate needs every thread resolved.
```
gh api repos/{owner}/{repo}/pulls/<pr>/comments/<comment-id>/replies -f body='Fixed in 3f2a1c9: ...'
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{id isResolved path comments(first:1){nodes{databaseId body}}}}}}}' -F o='{owner}' -F r='{repo}' -F n=<pr>
gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=<thread-id>
```
The first query maps each thread id to its first comment's `databaseId`, the id the reply
call takes. A fixed thread is resolved at once. A thread you pushed back on is resolved when
the reviewer accepts the reasoning, or by the user's ruling at the wave gate.

## Who acts
In the per-wave loop the lead triages a PR's comments and resumes the slice's implementer
with the ones to fix, as one list; the implementer fixes them in its worktree and records
each comment and its handling in its report. The lead replies and resolves. Inline, the lead
does all of it.
