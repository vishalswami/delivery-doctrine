#!/bin/bash
# PreToolUse guard for Bash: blocks destructive commands the doctrine enforces
# rather than instructs. Allows git push --force-with-lease (stacked-PR restacks).
export HOOK_INPUT="$(cat)"
python3 - <<'PY'
import json, os, re, sys

try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except json.JSONDecodeError:
    sys.exit(0)
cmd = data.get("tool_input", {}).get("command", "") or ""

rules = [
    (r'\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*f[a-zA-Z]*r',
     "recursive force delete (rm -rf) is blocked; delete specific paths deliberately"),
    (r'\bsudo\b', "sudo is blocked; run without elevation"),
    (r'\bpkill\b|\bkillall\b',
     "blanket process kills are blocked; kill only the specific PID you own (see execution-hygiene)"),
    (r'\bgit\s+push\b[^|;&]*\s--force(?!-with-lease)\b',
     "git push --force is blocked; use --force-with-lease"),
    (r'\bgit\s+push\b[^|;&]*\s-f\b',
     "git push -f is blocked; use --force-with-lease"),
    (r'\bgit\s+push\b[^|;&]*\s\+\S',
     "refspec force push (git push origin +branch) is blocked; use --force-with-lease"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard is blocked; use a safer recovery"),
    (r'\bchmod\s+777\b', "chmod 777 is blocked; use a precise mode"),
    (r'\bmkfs\b|\bdd\s+[^|;&]*\bof=/dev/', "destructive disk operations are blocked"),
]

for pattern, reason in rules:
    if re.search(pattern, cmd):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
        sys.exit(0)

sys.exit(0)
PY
