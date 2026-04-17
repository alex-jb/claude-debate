# Contributing

Small PRs and bug reports are welcome. Larger refactors — open an issue first so we can agree on scope before you spend time.

## Setup

```bash
git clone https://github.com/alex-jb/claude-debate.git
cd claude-debate
pip install -e '.[dev]'   # pulls claude-tier-router from git too
pytest
```

All 14 tests should pass in under a second. They use mocks — no Anthropic API key needed for development.

## What a good PR looks like

- One focused change, one commit (or a clean series)
- Tests for new behavior, not just the happy path — especially for prompt changes, which should have a test verifying the expected keywords appear in the rendered prompt
- `pytest -v` green on Python 3.9+ before pushing (CI will catch this too)
- `pyflakes src tests` clean
- README or CHANGELOG updated when behavior or API changes

## What we'll probably merge quickly

- **Prompt improvements** with before/after examples showing the judge gives more calibrated verdicts
- **New example scripts** in `examples/` — hiring, vendor selection, pricing decisions, etc.
- **Bug fixes** with a failing test that reproduces the bug
- **Better JSON parsing** — the current `_parse_json` is conservative, edge cases welcome

## What we'll push back on

- **Turning the three-stage pattern into N-stage** — that's a different tool. This is Advocate + Critic + Judge, not a generic graph.
- **Streaming the debate** — each stage must complete before the next has input; streaming doesn't fit.
- **Replacing Anthropic with other providers** — this is Claude-specific by design. If you want multi-provider, fork.
- **Large config frameworks** — keep `DebateConfig` a plain dataclass.

## Design principles (to save argument)

- **Critic sees the advocate's case.** Don't change this without a very strong argument — this is what makes the debate adversarial instead of two independent monologues.
- **Judge is bounded to `decision_options`.** No "MAYBE" / "IT DEPENDS" escape hatches. The point is to force a commit.
- **Confidence is calibrated in the prompt.** Don't soften the calibration ("80+ = bet on it") — that's the anchor that keeps scores honest.

## Reporting bugs

Open an issue with:
- What you ran (minimal repro)
- What you expected
- What you got (full judge JSON if possible)
- Python version + `anthropic` SDK version

Security issues — email instead of opening a public issue.

## License

By contributing you agree your contributions are MIT licensed.
