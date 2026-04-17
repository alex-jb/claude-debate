"""
run_debate() — three-stage adversarial debate (Advocate/Critic/Judge) over any
proposal. Returns a structured Verdict.

Pattern:
  1. Advocate argues FOR              (Haiku — cheap)
  2. Critic argues AGAINST, rebuts    (Haiku — cheap)
  3. Judge synthesizes                 (Sonnet — reasoning)

Cost ~$0.003 per debate with default config. Extracted from the Bull/Bear/Judge
trading-decision pipeline in orallexa-ai-trading-agent and generalized: the
same pattern works for PR reviews, architecture choices, hiring calls, any
binary or ternary decision with real tradeoffs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from claude_debate.prompts import ADVOCATE_TEMPLATE, CRITIC_TEMPLATE, JUDGE_TEMPLATE

FAST_MODEL = "claude-haiku-4-5-20251001"
DEEP_MODEL = "claude-sonnet-4-6"


@dataclass
class DebateConfig:
    """Config for a debate run. All fields have sensible defaults."""
    decision_options: tuple[str, ...] = ("APPROVE", "REJECT", "DEFER")
    criteria: list[str] = field(default_factory=lambda: ["correctness", "tradeoffs", "reversibility"])
    advocate_model: str = FAST_MODEL
    critic_model: str = FAST_MODEL
    judge_model: str = DEEP_MODEL
    max_tokens_arg: int = 800
    max_tokens_judge: int = 600
    temperature: float = 0.0


@dataclass
class Verdict:
    """Structured result of a debate."""
    decision: str
    confidence: float
    reasoning_summary: str
    reasoning_detail: str
    advocate_case: str
    critic_case: str
    strongest_advocate_point: str
    strongest_critic_point: str
    raw_judge_json: dict


def _extract_text(response: Any) -> str:
    out = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            out.append(block.text)
    return "".join(out).strip()


def _format_context(context: Optional[dict]) -> str:
    if not context:
        return "(no additional context provided)"
    return "\n".join(f"- {k}: {v}" for k, v in context.items())


def _format_criteria(criteria: list[str]) -> str:
    return "\n".join(f"- {c}" for c in criteria)


def _parse_json(text: str) -> dict:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _call(client: Any, *, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_text(response)


def run_debate(
    proposal: str,
    *,
    client: Any,
    context: Optional[dict] = None,
    config: Optional[DebateConfig] = None,
) -> Verdict:
    """Run Advocate → Critic → Judge over `proposal` using `client`.

    Args:
        proposal: one-sentence description of what's being decided.
        client: an anthropic.Anthropic instance (or anything with the same
            .messages.create signature).
        context: dict of facts/evidence to hand every speaker. Optional.
        config: override models, criteria, decision options. Optional.

    Returns:
        Verdict — structured decision with the full advocate/critic arguments
        and the judge's reasoning.

    Raises:
        ValueError: if the judge output doesn't parse as the expected JSON
            shape or picks a decision outside config.decision_options.
    """
    cfg = config or DebateConfig()
    ctx_block = _format_context(context)
    criteria_block = _format_criteria(cfg.criteria)

    advocate_prompt = ADVOCATE_TEMPLATE.format(
        proposal=proposal, context=ctx_block, criteria=criteria_block
    )
    advocate_case = _call(
        client,
        model=cfg.advocate_model,
        prompt=advocate_prompt,
        max_tokens=cfg.max_tokens_arg,
        temperature=cfg.temperature,
    )

    critic_prompt = CRITIC_TEMPLATE.format(
        proposal=proposal,
        context=ctx_block,
        criteria=criteria_block,
        advocate_case=advocate_case,
    )
    critic_case = _call(
        client,
        model=cfg.critic_model,
        prompt=critic_prompt,
        max_tokens=cfg.max_tokens_arg,
        temperature=cfg.temperature,
    )

    judge_prompt = JUDGE_TEMPLATE.format(
        proposal=proposal,
        context=ctx_block,
        criteria=criteria_block,
        advocate_case=advocate_case,
        critic_case=critic_case,
        decision_options=" | ".join(cfg.decision_options),
    )
    judge_text = _call(
        client,
        model=cfg.judge_model,
        prompt=judge_prompt,
        max_tokens=cfg.max_tokens_judge,
        temperature=cfg.temperature,
    )

    try:
        data = _parse_json(judge_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Judge returned malformed JSON: {e}\n---\n{judge_text[:500]}") from e

    decision = str(data.get("decision", "")).upper().strip()
    valid = tuple(d.upper() for d in cfg.decision_options)
    if decision not in valid:
        raise ValueError(
            f"Judge chose '{decision}' which is not in allowed options {valid}"
        )

    try:
        confidence = float(data.get("confidence", 50.0))
    except (TypeError, ValueError):
        confidence = 50.0

    return Verdict(
        decision=decision,
        confidence=max(0.0, min(100.0, confidence)),
        reasoning_summary=str(data.get("reasoning_summary", "")),
        reasoning_detail=str(data.get("reasoning_detail", "")),
        advocate_case=advocate_case,
        critic_case=critic_case,
        strongest_advocate_point=str(data.get("strongest_advocate_point", "")),
        strongest_critic_point=str(data.get("strongest_critic_point", "")),
        raw_judge_json=data,
    )
