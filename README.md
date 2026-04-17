# claude-debate

**Pressure-test any decision with a 3-call adversarial debate.** Advocate argues FOR, Critic argues AGAINST (seeing the advocate's case), Judge synthesizes into a structured verdict with calibrated confidence.

Works for PR reviews, architecture choices, hiring calls, trading decisions — anything where both sides have valid points and a single-model "ask once" answer is too confident.

Ships as a Python package and a [Claude Code skill](#claude-code-skill).

## Why

A single Claude call tends toward confident-sounding verdicts. On real decisions with genuine tradeoffs that's worse than useless — you get the same answer with false certainty. Adversarial debate forces both sides onto the table, makes the critic rebut specific claims instead of floating independent objections, and hands a synthesizer the full surface area to weigh.

Pattern extracted from [orallexa-ai-trading-agent](https://github.com/alex-jb/orallexa-ai-trading-agent) (Bull/Bear/Judge trading decisions) and generalized.

## Install

```bash
pip install claude-debate
```

## Usage

```python
from anthropic import Anthropic
from claude_debate import run_debate, DebateConfig

verdict = run_debate(
    proposal="Merge PR #42: adds Redis cache to auth middleware",
    client=Anthropic(),
    context={
        "diff_size_loc": 340,
        "coverage_after": "85%",
        "author_tenure": "3 weeks",
        "prod_qps": 2400,
    },
    config=DebateConfig(
        decision_options=("APPROVE", "REQUEST_CHANGES", "DEFER"),
        criteria=["correctness", "rollback cost", "perf under load", "on-call burden"],
    ),
)

print(verdict.decision)                   # APPROVE
print(verdict.confidence)                 # 72.0
print(verdict.reasoning_summary)          # one-sentence why
print(verdict.reasoning_detail)           # 2-3 sentences + tipping condition
print(verdict.strongest_advocate_point)
print(verdict.strongest_critic_point)
print(verdict.advocate_case)              # full advocate argument
print(verdict.critic_case)                # full critic rebuttal
```

See [`examples/`](examples/) for PR review, architecture choice, and trading decision demos.

## How it works

```
                    ┌──────────────┐
  proposal +   ───► │  Advocate    │  (Haiku) ──► case FOR
  context           └──────────────┘
                                      │
                                      ▼
                    ┌──────────────┐
  same inputs +───► │   Critic     │  (Haiku) ──► case AGAINST
  advocate case     └──────────────┘               (rebuts specifically)
                                      │
                                      ▼
                    ┌──────────────┐
  both cases   ───► │    Judge     │  (Sonnet) ──► structured Verdict
                    └──────────────┘
```

- **Advocate and Critic** are structured argument generation — Haiku does this well and cheaply.
- **Judge** reasons over conflicting evidence — Sonnet's sweet spot.
- **Cost per debate:** ~$0.003 (2 Haiku + 1 Sonnet call). **Latency:** ~10–15s.

## Design choices worth knowing

- **Critic sees the advocate's case.** So critic points are specific rebuttals, not independent monologues. This is what makes it adversarial.
- **Judge is asked for the tipping condition** — "what evidence would flip this call?" — so the verdict is falsifiable instead of just assertive.
- **`decision_options` are bounded.** Judge can't invent a new option. Forces commit.
- **Confidence is calibrated in the prompt.** 80+ means "bet on it", 50 means "genuinely uncertain", not a vibe.
- **Graceful on garbage input.** If the judge returns malformed JSON or picks an out-of-options decision, `run_debate` raises `ValueError` — you get a clear signal instead of silent mush.

## When NOT to use

- Questions with one right answer — waste of a debate
- Pure factual extraction — use a cheap single Haiku call (see [claude-tier-router](https://github.com/alex-jb/claude-tier-router))
- Open-ended brainstorming — debate narrows, not expands
- Low-stakes decisions — $0.003 + 15s isn't free

## Custom configuration

```python
from claude_debate import DebateConfig

# Hiring decision — different options, different criteria
cfg = DebateConfig(
    decision_options=("HIRE", "PASS", "SECOND_LOOP"),
    criteria=["technical signal", "growth trajectory", "team fit", "bar risk"],
    judge_model="claude-opus-4-7",  # swap in Opus for the judge if stakes are high
)
```

## Claude Code skill

Drop `.claude/skills/adversarial-debate/` into your Claude Code project and the agent learns when to call `run_debate` instead of answering directly. See [`SKILL.md`](.claude/skills/adversarial-debate/SKILL.md).

## Dev

```bash
pip install -e '.[dev]'
pytest
```

## Related

- [claude-tier-router](https://github.com/alex-jb/claude-tier-router) — the Haiku/Sonnet routing pattern also used internally here

## License

MIT — see [LICENSE](LICENSE).
