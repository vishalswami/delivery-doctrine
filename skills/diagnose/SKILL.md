---
name: diagnose
description: Use when the user asks why the doctrine did not do something in a session, in words
  like "why didn't the skill load", "the doctrine was ignored", "it never named a gear", "it
  skipped test-first", "why did the guard block that", "the session went wrong", "what happened
  in that session", or wants to "file a bug report" or open an issue about delivery-doctrine.
  Runs doctrine-diagnose on the session's transcript, reads the report against the doctrine,
  explains the likely cause in plain words, and offers a scrubbed bundle for a public issue.
---

# Diagnose

The user saw the doctrine skip a step, or saw something go wrong, and wants to know why. The
transcript records what happened; `doctrine-diagnose` turns it into a short report. Your job is
to read that report against the doctrine and say, plainly, what most likely went wrong and what
would fix it. Evidence first: what the report shows, then what you infer from it.

## 1. Pick the session

- **The current session**: run `doctrine-diagnose` with no argument from the folder the session
  started in. It takes that folder's newest transcript.
- **An earlier session**: ask for its session id, or for the transcript path, and pass it.
  Claude Code keeps transcripts in `~/.claude/projects/<folder>/<session-id>.jsonl`, where
  `<folder>` is the start directory with every character other than a letter or digit turned
  into `-`. A session started in another folder (a worktree, a parent directory) lives under
  that folder's name; pass its id and the tool searches every project.

## 2. Run it

```
doctrine-diagnose [SESSION_ID | TRANSCRIPT]
```

Read the whole report; it is short. It has the session basics (Claude Code version, start and
end, user prompts, compactions), the gear named in a reply, the skills loaded and at which
prompt, the doctrine skills never loaded, subagents dispatched with their model, guard denials
with the reason, likely misses, and the same per subagent under "Subagent sessions".

## 3. Read it against the doctrine

The doctrine is injected at session start (`doctrine/DOCTRINE.md` in the plugin). Match each
finding to the rule it touches:

| The report shows | The rule | Usual causes |
|---|---|---|
| No gear named | Gate 0: the gear comes first | Request read as a question or a chat; doctrine not injected (no SessionStart hook in `/hooks`) |
| No doctrine skill loaded at all | Load the skill a step names | Plugin disabled or failed to load (`/plugin`); session started before the install |
| A step done, its skill never loaded | Skills discipline | The model worked from the doctrine's summary; the user's wording missed the skill's trigger words |
| Language file edited before its profile | Profiles load before code in their language | Profile skipped in the main session, or loaded there but not in the subagent that wrote the code |
| Test file edited before `test-first` | Test-first | Tests written after the code, or the step started without loading the skill |
| Failing run, then edits, no `systematic-debugging` | A bug or failing test goes to systematic-debugging first | Fix by trial and error |
| Subagent with `model not set` | The orchestrator sets `model` on every dispatch | Dispatch written from memory after a compaction |
| Guard denials | The guard blocks destructive commands and wide test runs | Working as designed; repeats mean the agent retried instead of changing course; a denied commit message wanted `git commit -F <file>` |
| Behaviour changes after a compaction | After compaction the ledger and `git log` are the truth | Rules dropped out of the summary; check whether the anchor hook was turned off |

A subagent loads its own skills. A skill loaded in the main session does not carry into a
subagent, so read each subagent's section on its own.

### The misses are heuristics

"Likely misses" are pattern matches over tool calls, not verdicts. Before you call one a
miss, check it:

- A failing test after a production edit can still be a planned red step.
- A file under a `test/` folder may be a fixture, not a test.
- A skill may have been loaded by a slash command, which the report does not count.

When a finding matters and is unclear, read only the few transcript entries around its
timestamp, or ask the user what they saw.

## 4. Explain it

Tell the user, most important first, one finding at a time:

1. **What happened**: the fact from the report, with its prompt number or time.
2. **Which rule it missed**: the doctrine's own words, briefly.
3. **The likely cause**: one, stated as likely, with what would confirm it.
4. **What would change it**: a different prompt wording, a setting in the personal or
   repository profile, a plugin update, or, when the doctrine itself is at fault, a bug report.

Keep it plain and short. Do not blame the user for their wording, and do not claim more than the
report and the transcript show. If nothing in the report explains what they saw, say so.

## 5. Offer the bundle for an issue

When the cause looks like a doctrine or plugin bug, or the user wants to report it, offer the
scrubbed bundle:

```
doctrine-diagnose [SESSION_ID] --bundle <absolute path in the scratchpad>
```

The bundle holds the report and an event timeline (tool names, skill names, hook decisions,
timestamps). It leaves out message text, file contents, command text, subagent descriptions
and MCP server names; paths are cut to their extension; emails, tokens and home paths are
redacted. Its header says what was removed and what was kept.

- Ask the user to read the bundle before posting it. Skill names, subagent types and hook
  reasons are kept and may still say more than they want.
- Never attach the raw transcript or the unscrubbed report; both carry the conversation.
- A good issue says what the user asked for, what they expected, what happened, the plugin
  version (`/plugin`) and the Claude Code version (in the report), with the bundle attached.
- Draft the issue text for the user. Open it only on their explicit yes.
