"""
PR review as adversarial debate — should we merge this PR?

Requires: pip install anthropic claude-debate
Requires: ANTHROPIC_API_KEY env var
"""
from anthropic import Anthropic
from claude_debate import run_debate, DebateConfig


def main():
    client = Anthropic()

    verdict = run_debate(
        proposal="Merge PR #142: adds a Redis cache layer in front of the user-lookup endpoint",
        client=client,
        context={
            "diff_size_loc": 340,
            "files_touched": 7,
            "test_coverage_after": "84%",
            "author_tenure": "3 weeks",
            "prod_traffic_qps": 2400,
            "existing_latency_p99_ms": 180,
            "tests_added": "unit + integration; no load test",
        },
        config=DebateConfig(
            decision_options=("APPROVE", "REQUEST_CHANGES", "DEFER"),
            criteria=["correctness", "rollback cost", "performance under load", "on-call burden"],
        ),
    )

    print(f"DECISION: {verdict.decision}   (confidence {verdict.confidence:.0f}%)\n")
    print(f"Summary: {verdict.reasoning_summary}")
    print(f"Detail:  {verdict.reasoning_detail}\n")
    print(f"Strongest advocate point: {verdict.strongest_advocate_point}")
    print(f"Strongest critic point:   {verdict.strongest_critic_point}")
    print(f"\nDebate cost: ${verdict.cost_usd:.4f}")


if __name__ == "__main__":
    main()
