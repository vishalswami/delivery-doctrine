"""Regression suite for hooks/guard-bash.sh.

Every case states the decision the guard must make. Cases expected to be harmless are also
run through real bash, with the destructive programs replaced by logging stubs, to prove
nothing destructive actually executes. Run: python3 -I tests/guard.py
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "guard-bash.sh")
STUBBED = ["rm", "sudo", "pkill", "killall", "git", "gh", "chmod", "mkfs", "dd", "ash", "make", "go", "ls", "kill"]
PASSTHROUGH = ["bash", "sh", "cat", "echo", "find", "xargs", "env"]
ABSOLUTE_BINARY = re.compile(r"(^|[\s;&|(`'\"<>=])/\S*bin/")

DANGEROUS = [
    'rm -rf /',
    "git commit -m 'x'; rm -rf /",
    "git commit -m 'x'\nrm -rf /",
    'git commit -m \'x\' -m "$(rm -rf /)"',
    'git commit -m "`rm -rf /`"',
    "git commit -F - <<'EOF' && rm -rf /\nmsg\nEOF",
    "git commit -F - <<'EOF'\nmsg\nEOF\nrm -rf /",
    "( git commit -m 'x' ); rm -rf /",
    "git commit -m 'x' | rm -rf /",
    "gh pr checkout -b 'x'; rm -rf /",
    "eval git commit -m 'x; rm -rf /'",
    'sh -c "git commit -m \'x\'; rm -rf /"',
    "find . -execdir git commit -m 'x' \\; -execdir rm -rf {} \\;",
    "git commit -m 'docs: source of truth; never git reset --hard'",
    "git commit -m 'exec: never git push --force'",
    'echo "git commit -m \'x" ; rm -rf / ; echo "y\'"',
    'echo \'git commit -m "x\' ; rm -rf / ; echo "y"',
    'echo "git commit -m \'x"\nrm -rf /\necho "y\'"',
    'git commit --author=\'a -m "\' ; rm -rf / ; echo \'"\'',
    "git commit -m $'x\\' -m ' ; rm -rf / ; echo ''",
    "git commit -m\n'rm' -rf /",
    'git commit -m\n"rm" -rf /',
    "cat <<EOF\ngit commit -F - <<'X'\nEOF\nrm -rf /\nX",
    'echo "git commit -F - <<\'X\'\n" ; rm -rf /\nX',
    "git commit -F - <<'E'OF\nEOF\nrm -rf /\nE",
    'git commit -F - <<\'EOF\'"X"\nEOFX\nrm -rf /\nEOF',
    "git commit -F - <<A <<'B'\n$(rm -rf /)\nA\nx\nB",
    'rm -r -f /',
    'rm -Rf /',
    'rm --recursive --force /',
    'rm / -rf',
    'git push -fu origin main',
    'git -C . push --force origin main',
    'git reset -q --hard HEAD~1',
    'chmod 0777 x',
    'dd if=/dev/zero of="/dev/disk9"',
    'git commit -m "$(cat <<\'EOF\'\nmsg\nEOF\n)" && rm -rf /',
    'git commit -m "$(cat <<EOF\n$(rm -rf /)\nEOF\n)"',
    'git commit -m "$(cat <<\'EOF\'\nmsg\nEOF\nrm -rf /)"',
    'bash -c "git commit -m \'x\'; rm -rf /"',
    'm=\'rm -rf /\'; git commit -m \'x\'; eval "$m"',
    "git commit -m 'x' $(rm -rf /)",
    "''rm -rf /",
    "git commit -m 'x' && echo -m 'rm -rf /'; rm -rf /",
    "gh pr create -t 'x' -b 'y'; sudo ls",
    "git commit -m 'x' ; ( rm -rf / )",
    "git commit -m 'a)b' ; rm -rf /",
    'git commit -m "a; b" ; rm -rf /',
    'git commit -m "it\'s" ; rm -rf /',
    'git commit -m \'say "hi"\' ; rm -rf /',
    "'rm' -rf /",
    "rm '-rf' /",
    '\\rm -rf /',
    "'sudo' ls",
    "git push '--force' origin main",
    "git 'push' --force origin main",
    "chmod '777' x",
    "git reset '--hard'",
    '"pkill" -f node',
    'FOO=1 sudo ls',
    'command rm -rf /',
    'rm -rf build',
    'sudo ls',
    "bash -c 'rm -rf /tmp/x'",
    'sh -c "sudo ls"',
    'git commit -m "$(rm -rf /tmp/x)"',
    'eval "rm -rf x"',
    'echo x | xargs rm -rf',
    'python3 -c \'import os; os.system("rm -rf x")\'',
    "bash <<'EOF'\nrm -rf x\nEOF",
    'git push --force origin main',
    'git reset --hard HEAD',
    'git commit -m "`rm -rf /tmp/x`"',
    "git commit -m 'ok' && rm -rf y",
    'awk \'BEGIN{system("rm -rf x")}\'',
    'cat <<EOF | bash\nrm -rf x\nEOF',
    'git commit -F - <<EOF\n$(rm -rf x)\nEOF',
    "git commit -F - <<'EOF'\nmsg\nEOFX\nEOF\nrm -rf x",
    "git commit -F - <<'EOF'\nmsg\nEOF\nrm -rf x",
    "eval git commit -m 'x; rm -rf y'",
    'git push \\\n--force origin main',
    'git push origin \\\nmain -f',
    'git push origin \\\n+main',
    'git reset \\\n--hard HEAD',
    'dd if=/dev/zero \\\nof=/dev/disk9',
    'rm -r \\\n-f build',
    'rm \\\n-rf build',
    'chmod \\\n777 x',
    'su\\\ndo ls',
    'pk\\\nill node',
    'git pu\\\nsh --for\\\nce origin main',
    'git reset --ha\\\nrd',
    'r\\\nm -r\\\nf build',
    'chmod 7\\\n77 x',
    'true # note\\\nsudo ls',
    'true # x\\\nrm -rf build',
    'true # x\\\ngit push --force',
    "git -c alias.x='!rm -rf /' x",
    'echo | xargs -I{} sh -c \'git commit -m "x"; rm -rf /\'',
    'echo \'git commit -m "x"; rm -rf /\' | ash',
    "git rebase --exec 'rm -rf x' main",
    'find . -name x -exec rm -rf {} +',
    "git commit -m 'x' && . ./s.sh 'sudo'",
    "git -c alias.z='!rm -rf y' z",
]

TEXT_ONLY = [
    "git commit -m 'drop rm -rf / from script'",
    "git commit --message='rm -rf /'",
    "git commit -am 'stop using rm -rf /'",
    "git commit -m'stop using rm -rf /'",
    "git commit -m $'stop using rm -rf /'",
    'git commit -m "stop \\"rm -rf /\\" usage"',
    'git commit -m "$(cat <<\'EOF\'\nGuard: deny sudo\nEOF\n)"',
    "git commit -F - <<'EOF'\nstop using rm -rf /\nEOF",
    'git commit -F - <<"EOF"\nstop using rm -rf /\nEOF',
    'git commit -F - <<\\EOF\nstop using rm -rf /\nEOF',
    "git commit --file=- <<'EOF'\nstop using rm -rf /\nEOF",
    "gh pr create -t x --body-file=- <<'EOF'\nstop using rm -rf /\nEOF",
    "gh pr create -t x -F - <<'EOF'\nstop using rm -rf /\nEOF",
    "git commit -F - <<'EOF'\r\nstop using rm -rf /\r\nEOF\r\n",
    "git commit -F - <<-'EOF'\n\tstop using rm -rf /\n\tEOF\n",
    "git commit -F - <<'EOF'\nstop using rm -rf /\n",
    "git commit -m 'x' <(cat <<'EOF'\nrm -rf /\nEOF\n)",
    "git commit -m 'docker image no longer needs sudo'",
    "git commit -m 'Fix guard. Block sudo'",
    "git commit -m 'remove rm -rf / from install script'",
    "git commit -m 'node tests no longer pkill the server'",
    "gh pr create -t 'perms' -b 'python setup stops doing chmod 777'",
    "git commit -m 'su is gone; also drop sudo'",
    "git commit -m 'gcc-c flags; drop sudo'",
    "cat <<A; git commit -F - <<'B'\nB\nA\nrm -rf /\nB",
    "git commit -m 'drop rm -rf / from the build'",
    "gh pr create -t 'no sudo' -b 'installer no longer needs sudo'",
    "git log --grep 'sudo' --oneline",
    "git tag -a v1 -m 'drops sudo'",
    'git commit -m "$(cat <<\'EOF\'\nsay "sudo" never\nEOF\n)"',
    'git commit -m "$(cat <<\'EOF\'\nGuard: deny sudo. Add tests\n\nCo-Authored-By: x\nEOF\n)"',
    'eval "git commit -m \'x; rm -rf /\'"',
    "git commit -F - -- <<'EOF'\nstop rm -rf /\nEOF",
    'cat <<EOF\nrm -rf /\nEOF',
    'git commit -m "guard blocks sudo and rm -rf"',
    "git log --grep='sudo'",
    'echo "sudo is blocked"',
    'gh pr create --body "removes rm -rf usage"',
    "git commit -m 'drop rm -rf usage' -m 'second paragraph'",
    'gh pr create --title "Guard" --body "removes rm -rf usage"',
    "git commit -q -F - <<'EOF'\nGuard: allow sudo in messages\n\nmore\nEOF",
    "gh pr create --title t --body-file - <<'EOF'\nNo more rm -rf\nEOF",
    "git commit -F - <<'EOF'\nmsg\n EOF\nrm -rf x\nEOF",
    "xargs git commit -m 'x; rm -rf y' < f",
    'sh -c "git commit -m \'x; rm -rf y\'"',
    'git push --force-with-\\\nlease origin main',
    "echo 'a\\\n'sudo ls",
]

SCOPE = [
    'go test ./...',
    'go te\\\nst ./...',
]

SAFE = [
    'git log -1 --format=%s | make -f -',
    'git push --force-with-lease --force-if-includes',
    "git commit -m 'a'rm -rf /",
    'git push --force-with-lease origin main',
    'go test ./pkg/order',
    'git push \\\n--force-with-lease origin main',
    'git status',
    'git sta\\\ntus',
    'ls -la',
    'git status\n',
    'git log --oneline -5\n',
    'git push origin feat\n',
    'git push -u origin feat\n',
    'git reset --soft HEAD~1\n',
    'rm notes.txt\n',
    'rm -r build\n',
    'rm -f a.log\n',
    'chmod 755 run.sh\n',
    'chmod -R 644 docs\n',
    'kill 4242\n',
    'dd if=a.img of=b.img\n',
    'git commit -F /tmp/msg.txt\n',
    'gh pr create -t x -F body.md\n',
    'pytest tests/test_order.py\n',
    'mvn -pl orders test -Dtest=OrderTest\n',
    './gradlew test --tests OrderTest\n',
    'npm test\n',
    'go vet ./pkg/order\n',
    'python3 -m pytest tests/test_x.py::test_a\n',
    'git rebase --onto main feat\n',
    'git clean -n\n',
    'git stash\n',
    'echo hello > out.txt\n',
    'git push --force-with-lease origin feat\n',
    'git fetch -f origin\n',
    'git checkout -f main\n',
    'git branch -f topic HEAD\n',
    'git push origin feat && git status -f\n',
]

SWITCHED = [
    ({"DOCTRINE_GUARD": "0"}, "rm -rf /", "allow"),
    ({"DOCTRINE_GUARD": "0"}, "go test ./...", "allow"),
    ({"DOCTRINE_GUARD": "1"}, "sudo ls", "deny"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "go test ./...", "allow"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "pytest", "allow"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "while true; do sleep 5; done", "allow"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "sudo ls", "deny"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "git push --force origin main", "deny"),
    ({"DOCTRINE_GUARD_HYGIENE": "0"}, "rm -rf build", "deny"),
]


def hook_decision(command, switches=None):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    env = {k: v for k, v in os.environ.items() if not k.startswith("DOCTRINE_")}
    env.update(switches or {})
    out = subprocess.run(["bash", HOOK], input=payload, capture_output=True, text=True, timeout=20, env=env).stdout
    return "deny" if '"deny"' in out else "allow"


def make_sandbox_path(root):
    stubs = os.path.join(root, "bin")
    os.makedirs(stubs)
    for name in STUBBED:
        path = os.path.join(stubs, name)
        with open(path, "w") as f:
            f.write('#!/bin/bash\nprintf \'%s\\n\' "${0##*/} $*" >> "$STUBLOG"\n')
        os.chmod(path, 0o755)
    for name in PASSTHROUGH:
        real = shutil.which(name)
        if real:
            os.symlink(real, os.path.join(stubs, name))
    return stubs


def destructive(logged):
    words = logged.split()
    command, args = words[0], words[1:]
    if command == "rm":
        short = "".join(a.lstrip("-") for a in args if a.startswith("-") and not a.startswith("--"))
        recursive = "r" in short.lower() or "--recursive" in args
        force = "f" in short or "--force" in args
        return recursive and force
    if command in ("sudo", "pkill", "killall", "mkfs"):
        return True
    if command == "chmod":
        return any(a.lstrip("0") == "777" for a in args)
    if command == "dd":
        return any(a.startswith("of=/dev/") for a in args)
    if command == "git" and "push" in args:
        rest = args[args.index("push") + 1:]
        return any(a == "--force" or a.startswith("+") or (a.startswith("-") and not a.startswith("--") and "f" in a)
                   for a in rest)
    if command == "git" and "reset" in args:
        return "--hard" in args
    return False


def bash_runs_destructive(command, path, scratch):
    log = os.path.join(scratch, "log")
    open(log, "w").close()
    env = {"PATH": path, "STUBLOG": log, "HOME": scratch, "LC_ALL": "C"}
    proc = subprocess.Popen(["bash", "-c", "enable -n kill\n" + command], cwd=scratch, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    return any(destructive(line) for line in open(log).read().splitlines() if line.strip())


def main():
    failures = []
    expectations = ([(c, "deny", "dangerous") for c in DANGEROUS]
                    + [(c, "deny", "text-only") for c in TEXT_ONLY]
                    + [(c, "deny", "scope") for c in SCOPE]
                    + [(c, "allow", "safe") for c in SAFE])
    for command, _, _ in expectations:
        if ABSOLUTE_BINARY.search(command):
            sys.exit(f"refusing a case that names a binary by absolute path: {command!r}")
    with tempfile.TemporaryDirectory() as root:
        path = make_sandbox_path(root)
        for command, want, kind in expectations:
            got = hook_decision(command)
            if got != want:
                failures.append(f"{kind}: hook said {got}, expected {want}: {command!r}")
            if kind in ("text-only", "safe"):
                with tempfile.TemporaryDirectory(dir=root) as scratch:
                    if bash_runs_destructive(command, path, scratch):
                        failures.append(f"{kind}: bash runs something destructive, so this case belongs in DANGEROUS: {command!r}")
    for switches, command, want in SWITCHED:
        got = hook_decision(command, switches)
        if got != want:
            failures.append(f"switch {switches}: hook said {got}, expected {want}: {command!r}")
    for failure in failures:
        print(failure)
    print(f"{len(expectations) + len(SWITCHED)} cases, {len(failures)} failures")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
