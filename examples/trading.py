"""
Trading decision debate — the original use case from orallexa-ai-trading-agent.
Bull argues FOR the trade, Bear argues AGAINST, Judge synthesizes.

Requires: pip install anthropic claude-debate
Requires: ANTHROPIC_API_KEY env var
"""
from anthropic import Anthropic
from claude_debate import run_debate, DebateConfig


def main():
    client = Anthropic()

    verdict = run_debate(
        proposal="Open a long position in NVDA based on the current signal",
        client=client,
        context={
            "ticker": "NVDA",
            "close": 142.30,
            "ma20": 138.10,
            "ma50": 131.50,
            "rsi": 64,
            "macd_hist": 1.2,
            "volume_ratio_vs_20d_avg": 1.8,
            "initial_signal": "BUY (confidence 68%)",
            "broader_market": "SPY +0.4% on the day, tech leadership",
        },
        config=DebateConfig(
            decision_options=("BUY", "SELL", "WAIT"),
            criteria=["trend quality", "entry timing", "risk/reward", "macro context"],
        ),
    )

    print(f"DECISION: {verdict.decision}   (confidence {verdict.confidence:.0f}%)\n")
    print(verdict.reasoning_summary)
    print(f"\nBull's key point: {verdict.strongest_advocate_point}")
    print(f"Bear's key point: {verdict.strongest_critic_point}")


if __name__ == "__main__":
    main()
