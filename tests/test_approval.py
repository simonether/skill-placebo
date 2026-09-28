import json
import subprocess

from skill_placebo.harbor_agents import CHECK_JS, claude_followup, codex_followup

CLAUDE_CMD = ('export PATH="$HOME/.local/bin:$PATH"; x="$X"; unset X; printf "%s" "$x" | '
              'claude --verbose --output-format=stream-json --permission-mode=bypassPermissions --effort medium '
              '--disallowedTools WebSearch,WebFetch --print 2>&1 | tee /logs/agent/claude-code.txt')
CODEX_CMD = ('if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; codex exec --dangerously-bypass-approvals-and-sandbox '
             '--skip-git-repo-check --model gpt-6-sol --json --enable unified_exec -c model_reasoning_effort=medium '
             "-- 'Fix the bug?' 2>&1 </dev/null | tee /logs/agent/codex.txt")


def test_claude_followup_resumes_same_flags():
    f = claude_followup(CLAUDE_CMD)
    assert '--continue --print 2>&1 | tee -a /logs/agent/claude-code.txt' in f
    assert "--effort medium --disallowedTools WebSearch,WebFetch --continue" in f
    assert "$SP_APPROVAL" in f and "_sp_n -lt 2" in f
    assert claude_followup("mkdir -p x") is None


def test_codex_followup_resumes_last_session():
    f = codex_followup(CODEX_CMD)
    assert "codex exec resume --last --dangerously-bypass-approvals-and-sandbox" in f
    assert '-- "$SP_APPROVAL" 2>&1 </dev/null | tee -a /logs/agent/codex.txt' in f
    assert "Fix the bug" not in f  # the task instruction is not repeated


def _check(kind, events, tmp_path):
    p = tmp_path / "log.txt"
    p.write_text("\n".join(json.dumps(e) for e in events))
    return subprocess.run(["node", "-e", CHECK_JS, kind, str(p)]).returncode == 0


def test_question_detection(tmp_path):
    assert _check("claude", [{"type": "result", "result": "I see two options. Which one should I use?"}], tmp_path)
    assert not _check("claude", [{"type": "result", "result": "Done. All tests pass."}], tmp_path)
    assert not _check("claude", [{"type": "result", "result": "Should I? error", "is_error": True}], tmp_path)
    assert _check("codex", [{"type": "turn.started"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Proceed?"}}], tmp_path)
    assert not _check("codex", [{"type": "turn.started"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Proceed?"}}, {"type": "turn.failed"}], tmp_path)
    assert not _check("codex", [], tmp_path)
