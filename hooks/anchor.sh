#!/bin/bash
# UserPromptSubmit: once the session's context passes a threshold, re-state the doctrine's
# core rules next to the user's message, where a long context still attends to them.
# Context size comes from the last main-session reply's token usage in the transcript.
# DOCTRINE_ANCHOR=0 turns it off; DOCTRINE_ANCHOR_TOKENS sets the threshold (default 150000).
export HOOK_INPUT="$(cat)"
[ "${DOCTRINE_ANCHOR:-1}" = "0" ] && exit 0
python3 -I - <<'PY' 2>/dev/null
import json, os

ANCHOR = """Delivery doctrine, restated because this session is long:
- Gear named first (full or low). Stop at every gate; only an explicit yes moves past it.
- Load the skill a step names before acting on it; a bug or failing test → systematic-debugging first.
- Full gear: building goes to implementer subagents with `model` set; the lead orchestrates and never patches a dispatched slice itself.
- Local checks scoped to what changed; full suites are CI's. No claim of done without fresh output.
- After a long run, the ledger, the spec files and `git log` are the truth, not memory."""

try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    threshold = int(os.environ.get("DOCTRINE_ANCHOR_TOKENS", "150000"))
    path = data.get("transcript_path") or ""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, size - 4 * 1024 * 1024))
        tail = f.read().decode("utf-8", "replace").split("\n")
    context = 0
    for line in reversed(tail):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("type") == "system" and entry.get("subtype") == "compact_boundary":
            break
        message = entry.get("message")
        if entry.get("type") != "assistant" or entry.get("isSidechain") or not isinstance(message, dict):
            continue
        usage = message.get("usage") or {}
        context = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        if context:
            break
    if context >= threshold:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ANCHOR}}))
except Exception:
    pass
PY
exit 0
