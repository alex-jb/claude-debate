# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-04-17

### Added
- `run_debate(proposal, client, context=..., config=...)` → `Verdict` — three-stage Advocate/Critic/Judge debate over any decision
- `Verdict` dataclass: `decision`, `confidence`, `reasoning_summary`, `reasoning_detail`, `advocate_case`, `critic_case`, `strongest_advocate_point`, `strongest_critic_point`, `cost_usd`, `raw_judge_json`
- `DebateConfig` — override `decision_options`, `criteria`, `fast_model`, `deep_model`, `max_tokens_arg`, `max_tokens_judge`, `temperature`
- Three examples: PR merge review, Postgres-vs-DynamoDB architecture choice, trading BUY/SELL/WAIT decision
- Claude Code skill at `.claude/skills/adversarial-debate/SKILL.md`
- GitHub Actions CI on Python 3.9 through 3.13
- 14 unit tests covering three-call order, argument chaining, JSON parsing, edge cases, cost tracking

### Design choices
- **Critic sees the advocate's case** — rebuttals are specific, not parallel monologues
- **Judge is asked for the tipping condition** — verdicts are falsifiable
- **`decision_options` are bounded** — the judge can't invent a new option
- **Confidence is calibrated in the prompt** — 80+ = would bet on it, 50 = genuinely uncertain
- **Uses [`claude-tier-router`](https://github.com/alex-jb/claude-tier-router) internally** — advocate/critic through the fast tier, judge through deep; `verdict.cost_usd` shows real $ spent

### Notes
- Pattern extracted from the Bull/Bear/Judge trading-decision pipeline in [orallexa-ai-trading-agent](https://github.com/alex-jb/orallexa-ai-trading-agent) and generalized.
- Not yet on PyPI — install via `pip install git+https://github.com/alex-jb/claude-debate.git@v0.1.0`.

[Unreleased]: https://github.com/alex-jb/claude-debate/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alex-jb/claude-debate/releases/tag/v0.1.0
