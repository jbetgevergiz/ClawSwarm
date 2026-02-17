"""
ClawSwarm: Swarms-based agent with ClawSwarm prompt and Claude as a tool.
Responds on Telegram, Discord, and WhatsApp via the Messaging Gateway.
"""

__all__ = [
    "claim_fees",
    "create_agent",
    "launch_token",
    "run_claude_agent",
    "run_claude_agent_async",
    "stream_claude_agent",
]


def __getattr__(name: str):
    """Lazy imports so CLI can run --help/settings without heavy deps."""
    if name == "create_agent":
        from claw_swarm.agent import create_agent

        return create_agent
    if name in ("launch_token", "claim_fees"):
        from claw_swarm.swarms_world_tools import (
            claim_fees,
            launch_token,
        )

        return {
            "launch_token": launch_token,
            "claim_fees": claim_fees,
        }[name]
    if name in (
        "run_claude_agent",
        "run_claude_agent_async",
        "stream_claude_agent",
    ):
        from claw_swarm.tools import (
            run_claude_agent,
            run_claude_agent_async,
            stream_claude_agent,
        )

        return {
            "run_claude_agent": run_claude_agent,
            "run_claude_agent_async": run_claude_agent_async,
            "stream_claude_agent": stream_claude_agent,
        }[name]
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
