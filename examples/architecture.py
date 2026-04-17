"""
Architecture choice as adversarial debate — Postgres vs DynamoDB for a new service.

Requires: pip install anthropic claude-debate
Requires: ANTHROPIC_API_KEY env var
"""
from anthropic import Anthropic
from claude_debate import run_debate, DebateConfig


def main():
    client = Anthropic()

    verdict = run_debate(
        proposal="Use Postgres (not DynamoDB) for the new order-history service",
        client=client,
        context={
            "read_qps_peak": 8000,
            "write_qps_peak": 400,
            "query_patterns": "user_id + date range, occasional joins to products",
            "team_experience": "strong on Postgres, minimal on Dynamo",
            "target_p99_ms": 80,
            "existing_infra": "RDS Postgres fleet, no DynamoDB",
            "data_size_5yr_projection_tb": 3.2,
        },
        config=DebateConfig(
            decision_options=("POSTGRES", "DYNAMODB", "BOTH_HYBRID"),
            criteria=["read/write scale", "operational burden", "team velocity", "cost at scale", "lock-in"],
        ),
    )

    print(f"DECISION: {verdict.decision}   (confidence {verdict.confidence:.0f}%)\n")
    print(verdict.reasoning_summary)
    print()
    print(f"  Advocate's strongest: {verdict.strongest_advocate_point}")
    print(f"  Critic's strongest:   {verdict.strongest_critic_point}")


if __name__ == "__main__":
    main()
