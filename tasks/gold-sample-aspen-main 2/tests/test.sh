#!/usr/bin/env bash
# Aspen verifier entrypoint.
# Runs Harbor's RewardKit, which executes the agent-as-judge over the
# submitted unified-diff at /repo/answer.diff.
set -uo pipefail

mkdir -p /logs/artifacts /logs/verifier

# Capture the verifier stdout+stderr to a file so diagnostic_log can embed
# tail context if rewardkit fails before writing reward.json.
TEST_LOG=$(mktemp /tmp/aspen-verifier.XXXXXX.log)
export TEST_LOG

cleanup_and_reward() {
    local rc=$?
    # If rewardkit already wrote reward.json (or reward.txt), keep it.
    if [ -f /logs/verifier/reward.json ] || [ -f /logs/verifier/reward.txt ]; then
        exit "$rc"
    fi
    # Diagnostic fallback: tail of the verifier log embedded in reward.json so
    # the API surface always has a breadcrumb instead of a bare
    # RewardFileNotFoundError.
    python3 - "$rc" "$TEST_LOG" <<'PY' >/logs/verifier/reward.json 2>/dev/null || \
        echo '{"score":0.0,"error":"verifier early exit; fallback writer also failed"}' > /logs/verifier/reward.json
import json, sys
rc = int(sys.argv[1])
log_path = sys.argv[2] if len(sys.argv) > 2 else ""
tail = ""
try:
    with open(log_path, "r", errors="replace") as f:
        tail = f.read()[-4000:]
except Exception:
    tail = ""
json.dump({
    "score": 0.0,
    "error": f"verifier early-exit rc={rc} (no reward.json from rewardkit)",
    "diagnostic_log": tail,
}, sys.stdout)
PY
    exit "$rc"
}
trap cleanup_and_reward EXIT

# Copy the agent's submitted diff (and any working notes) into run artifacts
# so we keep evidence of what was scored, even if the judge fails.
cp -f "/repo/answer.diff" /logs/artifacts/answer.diff 2>/dev/null || true
cp -f "/repo/notes.md" /logs/artifacts/notes.md 2>/dev/null || true

# RewardKit reads /tests/review/agent_judge.toml + prompt.md and writes a
# reward.json under /logs/verifier with the per-criterion breakdown.
# `--python 3.13` is belt-and-suspenders alongside the Dockerfile UV_PYTHON
# env var: ensures uvx uses the provisioned interpreter even if env vars get
# stripped by some intermediate harbor/E2B wrapper.
uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit /tests --max-concurrent-agent 1 \
    > >(tee -a "$TEST_LOG") 2> >(tee -a "$TEST_LOG" >&2)
