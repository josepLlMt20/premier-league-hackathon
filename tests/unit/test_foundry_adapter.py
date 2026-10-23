import asyncio
import json

import httpx2
from openai import AsyncOpenAI
import pytest

from agent_framework.foundry import FoundryChatClient
from match_context.agents.base import AgentLimits, BudgetExceeded, RunBudget
from match_context.agents.foundry import FoundryRunner
from match_context.agents.orchestrator import prepare_tools
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest


def test_real_sdk_counts_every_model_turn_and_keeps_requests_isolated(scenario_main):
    requests = []

    async def run():
        cutoff = max(e.sequence for e in scenario_main.events if e.available_second <= 1500)
        snapshot = build_snapshot(scenario_main.events, cutoff, scenario_main.metadata)
        request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=cutoff)
        tools = prepare_tools(snapshot, request)
        selected = tools.candidates[0].story_id

        async def respond(http_request):
            body = json.loads(http_request.content)
            requests.append(body)
            if len(requests) == 1:
                output = [{"type": "function_call", "id": "fc1", "call_id": "call1", "name": "list_candidates",
                           "arguments": json.dumps({"cutoff": cutoff}), "status": "completed"}]
            else:
                output = [{"type": "message", "id": "msg1", "role": "assistant", "status": "completed",
                           "content": [{"type": "output_text", "text": json.dumps({"selected_story_ids": [selected],
                                                                                     "cards": [], "decisions": []}),
                                        "annotations": []}]}]
            return httpx2.Response(200, json={"id": f"response{len(requests)}", "object": "response",
                                           "created_at": 1, "status": "completed", "model": "offline",
                                           "output": output,
                                           "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}})

        client = FoundryChatClient(project_endpoint="https://offline.services.ai.azure.com/api/projects/test",
                                    model="offline", credential=lambda: "offline")
        await client.client.close()
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", max_retries=0,
                                    http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
        runner = FoundryRunner(client)
        try:
            result = await runner.run("analyst", {"cutoff": cutoff, "sentinel": "first-request"}, tools)
            assert result.selected_story_ids == (selected,)
            assert tools.budget.model_calls == 2
            assert tools.budget.trace().tool_calls == 1
            assert tools.budget.input_tokens == 20
            assert tools.budget.output_tokens == 4
            fresh = prepare_tools(snapshot, request)
            await runner.run("analyst", {"cutoff": cutoff, "sentinel": "second-request"}, fresh)
            assert "first-request" not in json.dumps(requests[-1])
            assert fresh.budget.model_calls == 1
            assert all(body["max_output_tokens"] == 1200 and body["store"] is False for body in requests)
            assert all("previous_response_id" not in body and "conversation" not in body for body in requests)
        finally:
            await runner.close()

    asyncio.run(run())


def test_model_budget_stops_the_next_network_turn(scenario_main):
    sent = []

    async def run():
        snapshot = build_snapshot(scenario_main.events, 269, scenario_main.metadata)
        request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=269)
        tools = prepare_tools(snapshot, request, budget=RunBudget(limits=AgentLimits(model_calls=1)))

        async def respond(http_request):
            sent.append(http_request)
            return httpx2.Response(200, json={"id": "r1", "object": "response", "created_at": 1,
                                           "status": "completed", "model": "offline",
                                           "output": [{"type": "function_call", "id": "fc1", "call_id": "c1",
                                                       "name": "list_candidates", "arguments": '{"cutoff":269}',
                                                       "status": "completed"}],
                                           "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}})

        client = FoundryChatClient(project_endpoint="https://offline.services.ai.azure.com/api/projects/test",
                                    model="offline", credential=lambda: "offline")
        await client.client.close()
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", max_retries=0,
                                    http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
        try:
            with pytest.raises(BudgetExceeded):
                await FoundryRunner(client).run("analyst", {"cutoff": 269}, tools)
            assert len(sent) == 1
        finally:
            await client.client.close()
            await client.project_client.close()

    asyncio.run(run())
