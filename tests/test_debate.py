"""Tests for run_debate — uses mock clients, no real API calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from claude_debate import run_debate, Verdict, DebateConfig
from claude_debate.debate import FAST_MODEL, DEEP_MODEL


def _mock_response(text: str):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    return resp


def _mock_client(advocate: str, critic: str, judge: dict):
    """Returns a client whose .messages.create returns different text per call."""
    client = MagicMock()
    client.messages.create.side_effect = [
        _mock_response(advocate),
        _mock_response(critic),
        _mock_response(json.dumps(judge)),
    ]
    return client


def _valid_judge(decision="APPROVE", confidence=72.0):
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning_summary": "Tradeoffs favor shipping given strong test coverage.",
        "reasoning_detail": "Upside is real, critic's perf concern is testable post-merge. Would flip if prod p99 jumps >20%.",
        "strongest_advocate_point": "85% coverage and isolated blast radius.",
        "strongest_critic_point": "Performance impact not measured in production-like load.",
    }


def test_basic_debate_returns_verdict():
    client = _mock_client("Advocate case...", "Critic case...", _valid_judge())
    verdict = run_debate("Merge PR #42", client=client)

    assert isinstance(verdict, Verdict)
    assert verdict.decision == "APPROVE"
    assert 70 <= verdict.confidence <= 75
    assert verdict.advocate_case == "Advocate case..."
    assert verdict.critic_case == "Critic case..."
    assert verdict.strongest_advocate_point.startswith("85%")


def test_three_calls_made_in_order():
    client = _mock_client("A", "C", _valid_judge())
    run_debate("Proposal", client=client)

    calls = client.messages.create.call_args_list
    assert len(calls) == 3
    # Advocate + critic use fast, judge uses deep
    assert calls[0].kwargs["model"] == FAST_MODEL
    assert calls[1].kwargs["model"] == FAST_MODEL
    assert calls[2].kwargs["model"] == DEEP_MODEL


def test_critic_prompt_sees_advocate_case():
    client = _mock_client("ADVOCATE_UNIQUE_123", "C", _valid_judge())
    run_debate("Proposal", client=client)

    critic_prompt = client.messages.create.call_args_list[1].kwargs["messages"][0]["content"]
    assert "ADVOCATE_UNIQUE_123" in critic_prompt


def test_judge_prompt_sees_both_cases():
    client = _mock_client("ADVOCATE_UNIQUE", "CRITIC_UNIQUE", _valid_judge())
    run_debate("Proposal", client=client)

    judge_prompt = client.messages.create.call_args_list[2].kwargs["messages"][0]["content"]
    assert "ADVOCATE_UNIQUE" in judge_prompt
    assert "CRITIC_UNIQUE" in judge_prompt


def test_context_passed_to_all_speakers():
    client = _mock_client("A", "C", _valid_judge())
    run_debate("Proposal", client=client, context={"diff_size": 340, "coverage": "85%"})

    for call in client.messages.create.call_args_list:
        prompt = call.kwargs["messages"][0]["content"]
        assert "diff_size" in prompt
        assert "340" in prompt


def test_custom_decision_options():
    cfg = DebateConfig(decision_options=("HIRE", "PASS", "SECOND_LOOP"))
    judge = _valid_judge(decision="HIRE")
    client = _mock_client("A", "C", judge)
    verdict = run_debate("Hire this candidate?", client=client, config=cfg)
    assert verdict.decision == "HIRE"


def test_judge_picks_invalid_option_raises():
    judge = _valid_judge(decision="MAYBE")  # not in default options
    client = _mock_client("A", "C", judge)
    with pytest.raises(ValueError, match="not in allowed options"):
        run_debate("Proposal", client=client)


def test_judge_malformed_json_raises():
    client = MagicMock()
    client.messages.create.side_effect = [
        _mock_response("A"),
        _mock_response("C"),
        _mock_response("this is not json"),
    ]
    with pytest.raises(ValueError, match="malformed JSON"):
        run_debate("Proposal", client=client)


def test_confidence_clamped_to_0_100():
    judge = _valid_judge(confidence=150.0)
    client = _mock_client("A", "C", judge)
    verdict = run_debate("Proposal", client=client)
    assert verdict.confidence == 100.0


def test_json_extracted_from_markdown_fences():
    judge_dict = _valid_judge()
    wrapped = f"Here is my verdict:\n```json\n{json.dumps(judge_dict)}\n```\nDone."
    client = MagicMock()
    client.messages.create.side_effect = [
        _mock_response("A"),
        _mock_response("C"),
        _mock_response(wrapped),
    ]
    verdict = run_debate("Proposal", client=client)
    assert verdict.decision == "APPROVE"


def test_custom_criteria_appear_in_prompts():
    cfg = DebateConfig(criteria=["latency", "cost", "UX"])
    client = _mock_client("A", "C", _valid_judge())
    run_debate("Proposal", client=client, config=cfg)
    advocate_prompt = client.messages.create.call_args_list[0].kwargs["messages"][0]["content"]
    assert "latency" in advocate_prompt
    assert "cost" in advocate_prompt


def test_no_context_uses_placeholder():
    client = _mock_client("A", "C", _valid_judge())
    run_debate("Proposal", client=client)
    advocate_prompt = client.messages.create.call_args_list[0].kwargs["messages"][0]["content"]
    assert "no additional context" in advocate_prompt
