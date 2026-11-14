#!/bin/bash
# PreToolUse guard for Bash: blocks destructive commands the doctrine enforces
# rather than instructs. Allows git push --force-with-lease (rebasing a PR onto new main).
export HOOK_INPUT="$(cat)"
python3 -I - <<'PY'
import json, os, re, sys

try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except json.JSONDecodeError:
    sys.exit(0)
cmd = data.get("tool_input", {}).get("command", "") or ""

rules = [
    (r'\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rR][a-zA-Z]*f|\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*f[a-zA-Z]*[rR]',
     "recursive force delete (rm -rf) is blocked; delete specific paths deliberately"),
    (r'\bsudo\b', "sudo is blocked; run without elevation"),
    (r'\bpkill\b|\bkillall\b',
     "blanket process kills are blocked; kill only the specific PID you own (see execution-hygiene)"),
    (r'\bgit\b(?:\s+-[cC]\s*\S+)*\s+push\b[^|;&\n]*\s--force(?!-with-lease|-if-includes)\b',
     "git push --force is blocked; use --force-with-lease"),
    (r'\bgit\b(?:\s+-[cC]\s*\S+)*\s+push\b[^|;&\n]*\s-[a-zA-Z]*f[a-zA-Z]*\b',
     "git push -f is blocked; use --force-with-lease"),
    (r'\bgit\b(?:\s+-[cC]\s*\S+)*\s+push\b[^|;&\n]*\s\+\S',
     "refspec force push (git push origin +branch) is blocked; use --force-with-lease"),
    (r'\bgit\b(?:\s+-[cC]\s*\S+)*\s+reset\b[^|;&\n]*\s--hard\b', "git reset --hard is blocked; use a safer recovery"),
    (r'\bchmod\s+(?:-\S+\s+)*0*777\b', "chmod 777 is blocked; use a precise mode"),
    (r'\bmkfs\b|\bdd\b[^|;&\n]*\bof=/dev/', "destructive disk operations are blocked"),
]

# Destructive rules match the raw command, failing closed: nothing is blanked, so a commit
# message that mentions one of these commands is refused too (write it to a file and use
# `git commit -F <file>`). Simple quoted words are unquoted first, so quoting a flag or a
# command name does not slip past. Execution-hygiene rules match only what the shell would
# run: heredoc bodies and quoted strings are blanked first, and test commands are recognised
# only at command position.

GO_VALUE_FLAGS = {"-run", "-skip", "-count", "-timeout", "-tags", "-p", "-parallel", "-cpu",
                  "-bench", "-benchtime", "-o", "-coverprofile", "-covermode", "-coverpkg",
                  "-exec", "-shuffle", "-outputdir", "-ldflags", "-gcflags"}
PYTEST_VALUE_FLAGS = {"-m", "-n", "-p", "-W", "-o", "-c", "-r", "--maxfail", "--tb",
                      "--durations", "--rootdir", "--confcutdir", "--basetemp", "--dist"}
LAUNCHERS = re.compile(r'^((\w+=\S*|env|time|nice|timeout\s+\S+|xargs(\s+-\S+)*|uv\s+run(\s+--with\s+\S+)*|poetry\s+run|pipenv\s+run|python3?\s+-m)\s+)*')
REDIRECT = re.compile(r'^(\d*|&)(>>?|<)(&?\S+)?$')


def runnable(command):
    command = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?([^\n]*)\n.*?\n\s*\1\b", r"\2", command, flags=re.S)
    command = re.sub(r"'[^']*'", "Q", command)
    command = re.sub(r'"(\\.|[^"\\])*"', "Q", command)
    return re.sub(r'(^|\s)#[^\n]*', r'\1', command)


def commands(text):
    for segment in re.split(r'&&|\|\||[;|\n]|\$\(|`', text):
        yield LAUNCHERS.sub("", segment.strip())


def operands(args, value_flags):
    found, skip = [], False
    for a in args:
        redirect = REDIRECT.match(a)
        if skip:
            skip = False
        elif redirect:
            skip = not redirect.group(3)
        elif a.startswith("-"):
            skip = a in value_flags
        else:
            found.append(a)
    return found


def wide_go_test(args):
    if "-c" in args:
        return None
    packages = operands(args, GO_VALUE_FLAGS)
    if any("..." in p for p in packages):
        return "go test over ./... compiles every package and is CI's job; run the touched package's tests by name (see execution-hygiene), or prefix DOCTRINE_WIDE_TESTS=1 if a wide run is truly needed"
    scoped = any(a.split("=")[0] in ("-run", "-skip") for a in args)
    if len(packages) > 1 and not scoped:
        return "go test over several whole packages is CI's job; scope with -run, or run one package at slice close (see execution-hygiene), or prefix DOCTRINE_WIDE_TESTS=1"
    return None


def wide_pytest(args):
    if any(a.split("=")[0] in ("-k", "--lf", "--last-failed", "--co", "--collect-only") for a in args):
        return None
    targets = operands(args, PYTEST_VALUE_FLAGS)
    if not targets:
        return "pytest without a target runs the whole suite (a -m marker run included), which is CI's job; name the test file, node id, or -k pattern (see execution-hygiene), or prefix DOCTRINE_WIDE_TESTS=1"
    if len([t for t in targets if "::" not in t and not t.endswith(".py")]) > 1:
        return "pytest over several directories is CI's job; name the touched test file or -k pattern (see execution-hygiene), or prefix DOCTRINE_WIDE_TESTS=1"
    return None


def hygiene(command):
    text = runnable(command)
    if re.search(r'\b(while|until|for)\b.*?\bdo\b((?!\bdone\b).)*\bsleep\b', text, flags=re.S):
        return "sleep-poll loops are blocked; run scoped checks in the foreground and wait, or launch a long run in the background and wait for the harness's completion notice (see execution-hygiene)"
    if "DOCTRINE_WIDE_TESTS=1" in command:
        return None
    for c in commands(text):
        words = c.split()
        if words[:2] == ["go", "test"]:
            reason = wide_go_test(words[2:])
            if not reason and "-c" not in words and re.search(r'\bgo\s+list\b[^|;&\n)]*\.\.\.', text):
                reason = "go test fed from a ./... listing (go list ./..., xargs) is a wide run and CI's job; name the touched package, or prefix DOCTRINE_WIDE_TESTS=1"
        elif words[:1] == ["pytest"]:
            reason = wide_pytest(words[1:])
        else:
            continue
        if reason:
            return reason
    return None


SIMPLE_QUOTED = re.compile(r"'([^'\s\\]*)'|\"([^\"\s\\$`]*)\"")
SEPARATOR = re.compile(r"[;&|\n()`]|\$\(")


def unquoted(command):
    return SIMPLE_QUOTED.sub(lambda m: m.group(1) if m.group(1) is not None else m.group(2), command)


def recursive_force_rm(command):
    for segment in SEPARATOR.split(command):
        words = segment.split()
        for i, word in enumerate(words):
            if word.lstrip("\\").rsplit("/", 1)[-1] != "rm":
                continue
            flags = [w for w in words[i + 1:] if w.startswith("-")]
            short = "".join(f[1:] for f in flags if not f.startswith("--"))
            recursive = "r" in short or "R" in short or "--recursive" in flags
            force = "f" in short or "--force" in flags
            if recursive and force:
                return True
    return False


joined = re.sub(r'\\\n', ' ', cmd)
reason = hygiene(joined)
if reason:
    rules.append((r'', reason))

checked = unquoted(joined)
if recursive_force_rm(checked):
    rules.insert(0, (r'', "recursive force delete (rm -rf) is blocked; delete specific paths deliberately"))
for pattern, reason in rules:
    if re.search(pattern, checked if pattern else cmd):
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
