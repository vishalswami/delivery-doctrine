#!/bin/bash
# SessionStart: inject the doctrine, then the personal profile (~/.claude/delivery-doctrine.md,
# every repository), then the repository profile if the repo has one.
# .claude/delivery-doctrine.md is the team's (committed); .claude/delivery-doctrine.local.md
# is personal (gitignored). Both are optional; the local one is read last, so it wins.
# A worktree has no copy of the gitignored file, so it falls back to the main checkout's.
# Symlinked repository profiles are skipped (a cloned repo could point one at a private file);
# the personal one is the user's own and may be a symlink. Later profiles win. 64 KiB cap each.
export HOOK_INPUT="$(cat)"
cat "${CLAUDE_PLUGIN_ROOT}/doctrine/DOCTRINE.md"

show() {
    printf '\n## %s\n\n' "$2"
    head -c 65536 "$1"
    [ "$(wc -c < "$1")" -gt 65536 ] && printf '\n[profile truncated at 64 KiB]\n'
    return 0
}

[ -f "$HOME/.claude/delivery-doctrine.md" ] && show "$HOME/.claude/delivery-doctrine.md" "Personal profile (~/.claude/delivery-doctrine.md)"

cwd=$(python3 -c 'import json,os; print(json.loads(os.environ.get("HOOK_INPUT") or "{}").get("cwd") or "")' 2>/dev/null)
root=$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null) || exit 0
main=$(git -C "$root" worktree list --porcelain 2>/dev/null | awk 'NR==1 {sub(/^worktree /, ""); path=$0} NR==2 && $0=="bare" {path=""} END {print path}')

profile() { [ -f "$1" ] && [ ! -L "$1" ] && [ ! -L "$(dirname "$1")" ]; }

profile "$root/.claude/delivery-doctrine.md" && show "$root/.claude/delivery-doctrine.md" "Repository profile (.claude/delivery-doctrine.md)"
for dir in "$root" ${main:+"$main"}; do
    if profile "$dir/.claude/delivery-doctrine.local.md"; then
        show "$dir/.claude/delivery-doctrine.local.md" "Repository profile (.claude/delivery-doctrine.local.md)"
        break
    fi
done
exit 0
