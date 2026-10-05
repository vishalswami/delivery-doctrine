#!/usr/bin/env python3
"""SubagentStop hook: log one subagent run's time distribution.

Async and zero-token. Reads the hook's JSON from stdin, finds the subagent's
own transcript, and appends one JSON line to runs.jsonl under
DOCTRINE_METRICS_DIR (default ~/.claude/doctrine-metrics). In hook mode it
prints nothing, exits 0 and swallows every error: a metrics problem must never
surface in a session.

Hand-run report over the log (never called by the hook):
    python3 subagent_timing.py summarise [runs.jsonl]
"""
import collections
import json
import os
import re
import sys
import warnings
from datetime import datetime, timezone

warnings.simplefilter("ignore")

MAX_TRANSCRIPT_BYTES = 64 * 1024 * 1024


def metrics_dir():
    return os.path.expanduser(os.environ.get("DOCTRINE_METRICS_DIR", "~/.claude/doctrine-metrics"))


# ---- tool categories: what kind of work a tool call is ----

BASH_RULES = [
    ("test",      r"\bgo test\b|\bpytest\b|\bmake test"),
    ("lint",      r"make lint|golangci|gofmt|goimports|\bgo vet\b|ruff|nilaway"),
    ("codegen",   r"make generate|go generate|atlas migrate|openapi-generator"),
    ("build",     r"\bgo build\b|make build"),
    ("git",       r"^\s*(cd [^&;]*&&\s*)?git |\bgh "),
    ("run-app",   r"go run .*cmd/server|make run-backend|setup-workspace|run-local-services|docker"),
    ("search",    r"\b(grep|rg|ugrep|find|ls|sed -n|cat|head|tail|awk|wc)\b"),
]


def category(name, inp):
    if name == "Read":
        return "read"
    if name in ("Grep", "Glob"):
        return "search"
    if name in ("Edit", "Write", "NotebookEdit"):
        return "edit"
    if name == "Bash":
        cmd = (inp or {}).get("command", "") or ""
        for cat, rx in BASH_RULES:
            if re.search(rx, cmd):
                return cat
        return "bash-other"
    if name == "Skill":
        return "skill"
    if name in ("Agent", "SendMessage"):
        return "delegate"
    return "other:" + str(name)


# ---- doctrine phases: where a tool call sits in red-green-refactor ----
# A test run is "TEST" until its result says whether it failed (red) or passed
# (verification); model time before a call is charged to that call's phase.

TEST_FAILED = re.compile(r"\bFAIL\b|panic:|build failed|undefined:")


def phase(name, inp):
    inp = inp or {}
    path = inp.get("file_path", "") or ""
    if name in ("Edit", "Write", "NotebookEdit"):
        if path.endswith("_test.go") or ("/test" in path and path.endswith(".py")):
            return "red-write-tests"
        if path.endswith(".md"):
            return "spec-docs"
        if re.search(r"\.(sql|yaml|yml|json|sum|ts)$", path) or "gen.go" in path:
            return "mechanical-edit"
        return "green-write-code"
    if name == "Read":
        return "spec-docs" if path.endswith(".md") else "read-code"
    if name in ("Grep", "Glob"):
        return "read-code"
    if name == "Bash":
        cmd = inp.get("command", "") or ""
        if re.search(r"until .*(ps -p|sleep)|while .*sleep|\bsleep \d", cmd):
            return "wait-background-test-lint"
        if re.search(r"\bgo test\b|pytest", cmd):
            return "TEST"
        if re.search(r"lint|golangci|gofmt|goimports|\bgo vet\b|nilaway", cmd):
            return "lint-vet"
        if re.search(r"generate|atlas migrate", cmd):
            return "codegen"
        if re.search(r"\bgo build\b", cmd):
            return "build"
        if re.search(r"\bgit |\bgh ", cmd):
            return "git"
        if re.search(r"go run|run-backend|setup-workspace|docker", cmd):
            return "run-app"
        return "read-code"
    return "other"


def resolve_test_phase(result_block):
    if result_block is None:
        return "test-run"
    if result_block.get("is_error") or TEST_FAILED.search(text_of(result_block)):
        return "red-run-failing"
    return "verify-run-passing"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def text_of(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return [r for r in rows if isinstance(r, dict) and r.get("type") in ("user", "assistant") and r.get("timestamp")]


def analyse(path):
    """One pass over a finished transcript: tool-category calls and seconds,
    doctrine-phase seconds, and the run's metadata."""
    rows = load_rows(path)
    if not rows:
        return None

    pending = {}  # tool_use_id -> (start, category, phase, think seconds charged to it)
    secs = collections.Counter()
    calls = collections.Counter()
    phase_secs = collections.Counter()
    model = 0.0
    last_result_at = ts(rows[0]["timestamp"])
    meta = {}

    for r in rows:
        t = ts(r["timestamp"])
        msg = r.get("message") if isinstance(r.get("message"), dict) else {}
        content = msg.get("content")
        blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
        if r.get("gitBranch") and "git_branch" not in meta:
            meta["git_branch"] = r["gitBranch"]
        if r.get("cwd") and "cwd" not in meta:
            meta["cwd"] = r["cwd"]
        if r["type"] == "assistant":
            if msg.get("model") and "model" not in meta:
                meta["model"] = msg["model"]
            if r.get("attributionAgent") and "agent" not in meta:
                meta["agent"] = r["attributionAgent"]
            uses = [b for b in blocks if b.get("type") == "tool_use" and b.get("id")]
            if not uses:
                continue
            think = 0.0
            if last_result_at is not None:
                think = max(0.0, (t - last_result_at).total_seconds())
                model += think
                last_result_at = None
            for i, b in enumerate(uses):
                pending[b["id"]] = (
                    t,
                    category(b.get("name"), b.get("input")),
                    phase(b.get("name"), b.get("input")),
                    think if i == 0 else 0.0,
                )
        else:
            results = [b for b in blocks if b.get("type") == "tool_result" and b.get("tool_use_id") in pending]
            if not results:
                continue
            share = 1.0 / len(results)
            for b in results:
                start, cat, ph, think = pending.pop(b["tool_use_id"])
                elapsed = max(0.0, (t - start).total_seconds()) * share
                secs[cat] += elapsed
                calls[cat] += 1
                if ph == "TEST":
                    ph = resolve_test_phase(b)
                phase_secs[ph] += elapsed + think
            last_result_at = t

    for _, _, ph, think in pending.values():
        if think:
            phase_secs[resolve_test_phase(None) if ph == "TEST" else ph] += think

    end = ts(rows[-1]["timestamp"])
    if last_result_at is not None:
        model += max(0.0, (end - last_result_at).total_seconds())
    secs["model"] = model

    return {
        "agent": meta.get("agent"),
        "model": meta.get("model"),
        "cwd": meta.get("cwd"),
        "git_branch": meta.get("git_branch"),
        "start": rows[0]["timestamp"],
        "wall_s": round((end - ts(rows[0]["timestamp"])).total_seconds()),
        "calls": dict(calls),
        "seconds": {k: round(v) for k, v in secs.items()},
        "phases": {k: round(v) for k, v in phase_secs.items()},
    }


# ---- hook mode: locate the subagent transcript, append one record ----

def find_transcript(data):
    """The hook's field names for this event are undocumented in places, so try
    the documented field, then the session transcript if it is itself a subagent
    transcript, then the path Claude Code derives from session and agent ids.
    No guessing by modification time: a sibling subagent still running is
    always the most recently written file."""
    p = data.get("agent_transcript_path")
    if isinstance(p, str) and os.path.isfile(p):
        return p

    p = data.get("transcript_path")
    if not isinstance(p, str) or not p:
        return None
    if "/subagents/" in p and os.path.isfile(p):
        return p

    session_id = data.get("session_id")
    agent_id = data.get("agent_id") or data.get("agentId")
    if session_id and agent_id:
        candidate = os.path.join(os.path.dirname(p), str(session_id), "subagents", f"agent-{agent_id}.jsonl")
        if os.path.isfile(candidate):
            return candidate
    return None


def already_logged(runs_path, basename):
    marker = json.dumps({"transcript": basename})[1:-1]
    try:
        with open(runs_path, encoding="utf-8", errors="replace") as f:
            return any(marker in line for line in f)
    except FileNotFoundError:
        return False


def append_line(path, line):
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def run_hook():
    raw = sys.stdin.read()
    mdir = metrics_dir()
    os.makedirs(mdir, exist_ok=True)

    try:
        with open(os.path.join(mdir, "last_subagent_stop.json"), "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception:
        pass

    data = json.loads(raw)
    if not isinstance(data, dict):
        return

    transcript = find_transcript(data)
    if not transcript or os.path.getsize(transcript) > MAX_TRANSCRIPT_BYTES:
        return

    basename = os.path.basename(transcript)
    runs_path = os.path.join(mdir, "runs.jsonl")
    if already_logged(runs_path, basename):
        return

    result = analyse(transcript)
    if result is None:
        return

    record = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "transcript": basename,
        "session_id": data.get("session_id"),
        "agent": result["agent"] or data.get("agent_type"),
        "model": result["model"],
        "cwd": data.get("cwd") or result["cwd"],
        "git_branch": result["git_branch"],
        "start": result["start"],
        "wall_s": result["wall_s"],
        "calls": result["calls"],
        "seconds": result["seconds"],
        "phases": result["phases"],
    }
    append_line(runs_path, json.dumps(record))


# ---- summarise mode: hand-run report over runs.jsonl ----

def summarise(runs_path=None):
    runs_path = runs_path or os.path.join(metrics_dir(), "runs.jsonl")
    rows = []
    try:
        with open(runs_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    rows = [r for r in rows if isinstance(r, dict)]
    if not rows:
        print(f"no runs logged at {runs_path}")
        return

    by_agent = collections.defaultdict(list)
    for r in rows:
        by_agent[r.get("agent") or "unknown"].append(r)

    total_wall = sum(r.get("wall_s", 0) for r in rows)
    print(f"runs: {len(rows)}   total wall: {total_wall / 60:.1f} min   ({runs_path})")
    for agent, runs in sorted(by_agent.items(), key=lambda kv: -sum(r.get("wall_s", 0) for r in kv[1])):
        wall = sum(r.get("wall_s", 0) for r in runs)
        models = collections.Counter(r.get("model") or "unknown" for r in runs)
        print()
        print(f"{agent}: runs={len(runs)}  wall={wall / 60:.1f}m  models={', '.join(f'{m} x{n}' for m, n in models.most_common())}")
        phases = collections.Counter()
        for r in runs:
            for ph, s in (r.get("phases") or {}).items():
                phases[ph] += s
        phase_wall = sum(phases.values()) or 1
        for ph, s in phases.most_common():
            print(f"  {ph:<26} {s / 60:6.1f}m  {100 * s / phase_wall:5.1f}%")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "summarise":
        summarise(sys.argv[2] if len(sys.argv) > 2 else None)
        return
    try:
        run_hook()
    except BaseException:
        pass


if __name__ == "__main__":
    main()
