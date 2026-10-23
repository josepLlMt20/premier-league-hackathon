"""Verify the local Foundry connection using a bounded synthetic match tool."""
import asyncio
import json
import os
import time
from pathlib import Path

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict


class ProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cutoff: int
    shots: int
    goals: int
    evidence_ids: list[str]


CALLS: list[int] = []
EVENTS = (
    {"id": "e1", "sequence": 1, "kind": "pass"},
    {"id": "e2", "sequence": 2, "kind": "shot"},
    {"id": "e3", "sequence": 3, "kind": "goal"},
)


@tool(approval_mode="never_require")
def get_match_state(cutoff: int) -> str:
    """Return synthetic match facts at cutoff 2; other cutoffs are forbidden."""
    if cutoff != 2:
        raise ValueError("Cutoff outside authorized snapshot")
    CALLS.append(cutoff)
    visible = [event for event in EVENTS if event["sequence"] <= cutoff]
    return json.dumps({
        "cutoff": cutoff,
        "shots": sum(event["kind"] == "shot" for event in visible),
        "goals": sum(event["kind"] == "goal" for event in visible),
        "evidence_ids": [event["id"] for event in visible],
    })


async def main() -> None:
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env", override=False)
    cli_bin = root / "tmp" / "foundry-connection" / "azure-cli" / "bin"
    if (cli_bin / "az.cmd").is_file():
        os.environ["PATH"] = str(cli_bin) + os.pathsep + os.environ.get("PATH", "")
    credential = AzureCliCredential(process_timeout=20)
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["FOUNDRY_MODEL"],
        credential=credential,
        function_invocation_configuration={
            "max_iterations": 3,
            "max_function_calls": 2,
            "max_duration_seconds": 40,
        },
    )
    client.client = client.client.with_options(max_retries=0, timeout=20)
    agent = Agent(
        client=client,
        instructions=(
            "Use get_match_state exactly once with cutoff 2. "
            "Return its facts unchanged in the requested schema. "
            "Only tool-returned events may appear in evidence_ids."
        ),
        tools=[get_match_state],
    )
    started = time.perf_counter()
    try:
        response = await asyncio.wait_for(
            agent.run(
                "Inspect the synthetic match at authorized cutoff 2 using your tool.",
                options={
                    "response_format": ProbeResult,
                    "max_tokens": 1024,
                    "reasoning": {"effort": "minimal"},
                    "store": False,
                    "allow_multiple_tool_calls": False,
                },
            ),
            timeout=45,
        )
        value = response.value
        if not isinstance(value, ProbeResult):
            raise RuntimeError("No validated structured response received")
        expected = ProbeResult(cutoff=2, shots=1, goals=0, evidence_ids=["e1", "e2"])
        if value != expected or CALLS != [2]:
            raise RuntimeError("Tool invocation or bounded evidence did not match")
        report = {
            "status": "passed",
            "model_deployment": os.environ["FOUNDRY_MODEL"],
            "tool_calls": len(CALLS),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "result": value.model_dump(),
            "usage": dict(response.usage_details or {}),
            "scope": "Connection probe only; not the product spoiler evaluation",
        }
        report_path = root / "tmp" / "foundry-connection" / "smoke-result.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
    finally:
        await client.client.close()
        await client.project_client.close()
        credential.close()


if __name__ == "__main__":
    asyncio.run(main())
