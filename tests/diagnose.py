"""Tests for bin/doctrine-diagnose, driven against the synthetic transcripts in tests/fixtures.

Run: python3 -I tests/diagnose.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "bin", "doctrine-diagnose")
FIXTURES = os.path.join(HERE, "fixtures")
MISSED = os.path.join(FIXTURES, "missed-skills.jsonl")
FOLLOWED = os.path.join(FIXTURES, "followed.jsonl")
SIDECHAIN_HEADING = "Subagent sessions (sidechain)"


def diagnose(*args, cwd=HERE, env=None):
    run_env = dict(os.environ, **(env or {}))
    proc = subprocess.run(["bash", SCRIPT, *args], capture_output=True, text=True, cwd=cwd, env=run_env, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def main_and_sidechain(report):
    main, _, sidechain = report.partition(SIDECHAIN_HEADING)
    return main, sidechain


def section(report, heading):
    match = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^\S|\Z)", report, re.S | re.M)
    return match.group(1) if match else ""


def lines_with(text, needle):
    return [line for line in text.splitlines() if needle in line]


def check_session_basics(report):
    main, _ = main_and_sidechain(report)
    return [f"basics: missing {want!r}" for want in
            ("Claude Code: 2.1.400", "User prompts: 3", "Compactions: 1",
             "Started: 2026-01-05 10:00:00", "Ended: 2026-01-05 10:09:00")
            if want not in main]


def check_gear(report):
    gear = section(report, "Gear")
    return [] if "full gear" in gear and "prompt 1" in gear else [f"gear: full gear at prompt 1 not reported: {gear!r}"]


def check_skills_listed(report):
    main, _ = main_and_sidechain(report)
    loaded = section(main, "Skills loaded")
    failures = []
    if not any("prompt 1" in line for line in lines_with(loaded, "grill-fast")):
        failures.append(f"skills: grill-fast at prompt 1 not listed: {loaded!r}")
    never = " ".join(lines_with(main, "Doctrine skills never loaded"))
    if "systematic-debugging" not in never or "go-style" not in never:
        failures.append(f"skills: never-loaded list incomplete: {never!r}")
    if "grill-fast" in never:
        failures.append(f"skills: grill-fast listed as never loaded: {never!r}")
    return failures


def check_subagent_dispatch(report):
    dispatched = section(report, "Subagents dispatched")
    wanted = ("delivery-doctrine:implementer", "opus", "SENTINEL-DESC slice one", "prompt 2")
    return [f"dispatch: missing {want!r} in {dispatched!r}" for want in wanted if want not in dispatched]


def check_guard_denial(report):
    main, sidechain = main_and_sidechain(report)
    failures = []
    if "git push --force is blocked" not in section(main, "Guard denials"):
        failures.append("denial: main-session force-push denial not reported")
    if "sudo is blocked" in main:
        failures.append("denial: the subagent's denial leaked into the main session")
    if "sudo is blocked" not in sidechain:
        failures.append("denial: the subagent's denial is missing from the sidechain section")
    return failures


def check_language_misses(report):
    main, sidechain = main_and_sidechain(report)
    misses = section(main, "Likely misses (heuristics, not proof)")
    failures = []
    if not lines_with(misses, "go-style"):
        failures.append(f"misses: Go edit without go-style not flagged: {misses!r}")
    if not lines_with(misses, "go-testing"):
        failures.append(f"misses: Go test edit without go-testing not flagged: {misses!r}")
    if not lines_with(misses, "test-first"):
        failures.append(f"misses: test edit before test-first not flagged: {misses!r}")
    if not lines_with(misses, "systematic-debugging"):
        failures.append(f"misses: edits after a failing run not flagged: {misses!r}")
    sidechain_misses = sidechain.partition("Likely misses")[2]
    if not lines_with(sidechain_misses, "python-style"):
        failures.append(f"misses: the subagent's Python edit without python-style not flagged: {sidechain_misses!r}")
    if lines_with(sidechain_misses, "go-style"):
        failures.append(f"misses: go-style flagged in the subagent that loaded it: {sidechain_misses!r}")
    return failures


def check_followed_session_is_clean(report):
    misses = section(report, "Likely misses (heuristics, not proof)")
    failures = [] if "none found" in misses else [f"clean: misses reported for a session that followed the doctrine: {misses!r}"]
    if "low gear" not in section(report, "Gear"):
        failures.append("clean: low gear not reported")
    return failures


def check_bundle(bundle):
    forbidden = ["SENTINEL", "example.com", "/Users/", "jane", "order.go", "order_test", "shop", "sk-ant", "gen.py"]
    failures = [f"bundle: contains {word!r}" for word in forbidden if word in bundle]
    for want in ("Removed:", "skill grill-fast", "hook PreToolUse:Bash deny", "edit Write .go", "agent delivery-doctrine:implementer",
                 "refusing to write <path .yaml> or <path .md> for <email>"):
        if want not in bundle:
            failures.append(f"bundle: missing {want!r}")
    return failures


def check_bundle_written(tmp):
    out = os.path.join(tmp, "bundle.txt")
    code, _, err = diagnose(MISSED, "--bundle", out)
    if code != 0 or not os.path.exists(out):
        return [f"bundle: exit {code}, no file: {err}"]
    with open(out) as f:
        return check_bundle(f.read())


def check_latest_transcript_of_cwd(tmp):
    project = os.path.realpath(os.path.join(tmp, "my.project"))
    os.makedirs(project)
    store = os.path.join(tmp, "config", "projects", re.sub(r"[^A-Za-z0-9]", "-", project))
    os.makedirs(store)
    shutil.copy(FOLLOWED, os.path.join(store, "11111111-older.jsonl"))
    shutil.copy(MISSED, os.path.join(store, "22222222-newer.jsonl"))
    os.utime(os.path.join(store, "11111111-older.jsonl"), (1, 1))
    env = {"CLAUDE_CONFIG_DIR": os.path.join(tmp, "config")}
    failures = []
    code, out, err = diagnose(cwd=project, env=env)
    if code != 0 or "22222222-newer" not in out:
        failures.append(f"resolve: newest transcript of the cwd not picked: exit {code} {err}")
    code, out, err = diagnose("11111111-older", cwd=project, env=env)
    if code != 0 or "low gear" not in out:
        failures.append(f"resolve: session id not found: exit {code} {err}")
    code, _, err = diagnose("no-such-session", cwd=project, env=env)
    if code != 2 or "no-such-session" not in err:
        failures.append(f"resolve: unknown session gave exit {code}: {err}")
    return failures


def main():
    code, missed, err = diagnose(MISSED)
    if code != 0:
        sys.exit(f"doctrine-diagnose failed on {MISSED}: exit {code}\n{err}")
    code, followed, err = diagnose(FOLLOWED)
    if code != 0:
        sys.exit(f"doctrine-diagnose failed on {FOLLOWED}: exit {code}\n{err}")
    checks = [check_session_basics(missed), check_gear(missed), check_skills_listed(missed),
              check_subagent_dispatch(missed), check_guard_denial(missed), check_language_misses(missed),
              check_followed_session_is_clean(followed)]
    with tempfile.TemporaryDirectory() as tmp:
        checks += [check_bundle_written(tmp), check_latest_transcript_of_cwd(tmp)]
    failures = [failure for found in checks for failure in found]
    for failure in failures:
        print(failure)
    print(f"{len(checks)} checks, {len(failures)} failures")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
