#!/bin/bash
# SessionStart: inject the doctrine, then the repository profile if the repo has one.
# .claude/delivery-doctrine.md is the team's (committed); .claude/delivery-doctrine.local.md
# is personal (gitignored). Both are optional; the local one is read last, so it wins.
# A worktree has no copy of the gitignored file, so it falls back to the main checkout's.
export HOOK_INPUT="$(cat)"
cat "${CLAUDE_PLUGIN_ROOT}/doctrine/DOCTRINE.md"

cwd=$(python3 -c 'import json,os; print(json.loads(os.environ.get("HOOK_INPUT") or "{}").get("cwd") or "")' 2>/dev/null)
root=$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null) || exit 0
main=$(git -C "$root" worktree list --porcelain 2>/dev/null | awk 'NR==1 {sub(/^worktree /, ""); path=$0} NR==2 && $0=="bare" {path=""} END {print path}')

show() {
    printf '\n## Repository profile (%s)\n\n' "$2"
    cat "$1"
}

[ -f "$root/.claude/delivery-doctrine.md" ] && show "$root/.claude/delivery-doctrine.md" .claude/delivery-doctrine.md
for dir in "$root" ${main:+"$main"}; do
    if [ -f "$dir/.claude/delivery-doctrine.local.md" ]; then
        show "$dir/.claude/delivery-doctrine.local.md" .claude/delivery-doctrine.local.md
        break
    fi
done
exit 0
