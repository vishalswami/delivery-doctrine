#!/bin/bash
# UserPromptSubmit: asks for a written YES/NO on the doctrine skills that could apply before
# acting, then loading every YES. A written decision per skill makes skill loading reliable
# where a plain reminder does not. Candidates follow the repository's language.
# DOCTRINE_SKILL_CHECK=0 turns it off.
export HOOK_INPUT="$(cat)"
[ "${DOCTRINE_SKILL_CHECK:-1}" = "0" ] && exit 0
python3 -I - <<'PY' 2>/dev/null
import json, os

ALWAYS = [
    ("grill-fast / grill-brownfield", "a new feature or plan to agree first (greenfield / existing code)"),
    ("fast-path", "a small change, bugfix, spike or throwaway"),
    ("test-first", "writing any test or production code"),
    ("systematic-debugging", "a bug, failing test, hang or surprise"),
    ("review-feedback", "acting on review comments"),
    ("execution-hygiene", "running tests, lint or a slow command"),
    ("delivery-loop", "commits and PRs, or running the slice loop"),
]
BY_LANGUAGE = [
    (("go.mod",), [("go-style", "writing Go"), ("go-testing", "writing Go tests")]),
    (("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"),
     [("python-style", "writing Python"), ("pytest-testing", "writing pytest tests")]),
    (("pom.xml", "build.gradle", "build.gradle.kts"),
     [("readable-java-style", "writing Java"), ("java-domain", "a Java domain and its wiring"),
      ("gwt-testing", "writing JUnit tests"), ("spring-boot", "a Spring Boot service")]),
]


def candidates(cwd):
    found = list(ALWAYS)
    for markers, skills in BY_LANGUAGE:
        if any(os.path.exists(os.path.join(cwd, m)) for m in markers):
            found += skills
    return found


try:
    data = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    prompt = (data.get("prompt") or "").strip()
    if prompt and not prompt.startswith("/"):
        lines = "\n".join(f"- {name}: {when}" for name, when in candidates(data.get("cwd") or os.getcwd()))
        text = ("Skill check (delivery-doctrine). Before any other tool call, write one line\n"
                "`Skills: <name> YES|NO, ...` deciding each candidate below for this message, then load\n"
                "every YES with the Skill tool (delivery-doctrine:<name>). A question or chat that needs\n"
                "no work: write `Skills: none` and answer.\n" + lines)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))
except Exception:
    pass
PY
exit 0
