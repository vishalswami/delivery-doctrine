#!/bin/bash
# SessionStart: keep the Mac awake for as long as this Claude Code session lives.
# caffeinate -w exits with the claude process, so no Stop/SessionEnd cleanup is needed.
# It prevents idle sleep only; closing the lid still sleeps unless sleep is disabled
# system-wide (Lidless does that via pmset), so remind once a day when it is not.
cat > /dev/null
[ "$(uname)" = "Darwin" ] || exit 0

pid=$PPID
while [ "${pid:-0}" -gt 1 ] && ! ps -o comm= -p "$pid" | grep -q 'claude'; do
    pid=$(ps -o ppid= -p "$pid" | tr -d ' ')
done
[ "${pid:-0}" -gt 1 ] || exit 0

pgrep -qf "caffeinate -ims -w $pid\$" || { nohup caffeinate -ims -w "$pid" > /dev/null 2>&1 & }

if [ -d /Applications/Lidless.app ] && pmset -g | grep -q 'SleepDisabled[[:space:]]*0'; then
    stamp="${DOCTRINE_METRICS_DIR:-$HOME/.claude/doctrine-metrics}/lid-reminder"
    if [ "$(cat "$stamp" 2>/dev/null)" != "$(date +%F)" ]; then
        mkdir -p "$(dirname "$stamp")" && date +%F > "$stamp"
        echo '{"systemMessage": "Kept awake while the lid is open. Lidless is off: switch it on before closing the lid on a long run."}'
    fi
fi
exit 0
