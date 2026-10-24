import asyncio
import json

import httpx2
from openai import AsyncOpenAI
import pytest

from agent_framework.foundry import FoundryChatClient
from match_context.agents.base import AgentLimits, BudgetExceeded, RunBudget
from match_context.agents.foundry import FoundryRunner
from match_context.agents.wire import WireCodec
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
        fact = tools.facts[0]
        fact_index = WireCodec(tools).encode(fact.fact_id)

        async def respond(http_request):
            body = json.loads(http_request.content)
            requests.append(body)
            if len(requests) == 1:
                assert 'candidate_context' in json.dumps(body['input'])
                assert selected in json.dumps(body['input'])
            if len(requests) == 1:
                output = [{"type": "function_call", "id": "fc1", "call_id": "call1", "name": "read_facts",
                           "arguments": json.dumps({"fact_ids": [fact_index], "cutoff": cutoff}), "status": "completed"}]
            else:
                output = [{"type": "message", "id": "msg1", "role": "assistant", "status": "completed",
                           "content": [{"type": "output_text", "text": json.dumps({"selected_story_ids": [selected]}),
                                        "annotations": []}]}]
            return httpx2.Response(200, json={"id": f"response{len(requests)}", "object": "response",
                                           "created_at": 1, "status": "completed", "model": "offline",
                                           "output": output,
                                           "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}})

        client = FoundryChatClient(project_endpoint="https://offline.services.ai.azure.com/api/projects/test",
                                    model="offline", credential=lambda: "offline")
        await client.client.close()
        http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", max_retries=0,
                                    http_client=http_client)
        runner = FoundryRunner(client, http_client=http_client)
        try:
            result = await runner.run("analyst", {"cutoff": cutoff, "sentinel": "first-request"}, tools)
            assert result.selected_story_ids == (selected,)
            assert tools.budget.model_calls == 2
            assert tools.budget.trace().tool_calls == 2
            assert tools.budget.trace().tool_names == ("list_candidates", "read_facts")
            returned_fact = json.loads(next(item["output"] for item in requests[1]["input"]
                                           if item.get("type") == "function_call_output"))[0]
            assert returned_fact["fact_id"] == fact_index
            assert returned_fact["value"] == fact.value
            assert tools.budget.input_tokens == 20
            assert tools.budget.output_tokens == 4
            fresh = prepare_tools(snapshot, request)
            await runner.run("analyst", {"cutoff": cutoff, "sentinel": "second-request"}, fresh)
            assert "first-request" not in json.dumps(requests[-1])
            assert fresh.budget.model_calls == 1
            assert all(body["max_output_tokens"] == 1200 and body["store"] is False for body in requests)
            assert all("previous_response_id" not in body and "conversation" not in body for body in requests)
            unsupported = {"maxItems", "minItems", "maxLength", "minLength", "pattern", "default",
                           "minimum", "maximum", "format", "multipleOf"}

            def check_schema(node):
                if isinstance(node, dict):
                    assert not (set(node) & unsupported)
                    for child in node.values():
                        check_schema(child)
                elif isinstance(node, list):
                    for child in node:
                        check_schema(child)
            for body in requests:
                check_schema(body["text"]["format"]["schema"])
        finally:
            await runner.close()

    asyncio.run(run())


@pytest.mark.parametrize("bad_text", [None, "{bad json", '{"selected_story_ids":[],"cards":"invalid","decisions":[]}'])
def test_sdk_three_role_output_and_parse_repair_keep_all_reported_usage(scenario_main, bad_text):
    from match_context.agents.orchestrator import orchestrate
    from .agent_helpers import compact_card, draft_for
    from match_context.agents.wire import WireCodec
    sent = []

    async def run():
        snapshot = build_snapshot(scenario_main.events, 269, scenario_main.metadata)
        request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=269)
        tools = prepare_tools(snapshot, request)
        candidate = tools.candidates[0]
        draft = draft_for(tools.story_payload(candidate))
        outputs = [json.dumps({"selected_story_ids": [candidate.story_id]})] + ([bad_text] if bad_text else []) + [
                   json.dumps({"cards": [compact_card(draft, WireCodec(tools))]}),
                   json.dumps({"decisions": [{"story_id": candidate.story_id, "accepted": True, "codes": []}]})]

        async def respond(http_request):
            text = outputs[len(sent)]
            sent.append(http_request)
            return httpx2.Response(200, json={"id": f"r{len(sent)}", "object": "response", "created_at": 1,
                                           "status": "completed", "model": "offline",
                                           "output": [{"type": "message", "id": f"msg{len(sent)}", "role": "assistant",
                                                       "status": "completed", "content": [{"type": "output_text",
                                                       "text": text, "annotations": []}]}],
                                           "usage": {"input_tokens": 19, "output_tokens": 7, "total_tokens": 26}})

        client = FoundryChatClient(project_endpoint="https://offline.services.ai.azure.com/api/projects/test",
                                    model="offline", credential=lambda: "offline")
        await client.client.close()
        http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", max_retries=0,
                                    http_client=http_client)
        runner = FoundryRunner(client, http_client=http_client)
        try:
            result = await orchestrate(snapshot, request, runner)
            expected_turns = 4 if bad_text else 3
            assert len(sent) == expected_turns
            assert result.status == "verified"
            assert result.trace.model_calls == expected_turns
            assert result.trace.tool_names == ("list_candidates",)
            assert result.trace.input_tokens == expected_turns * 19
            assert result.trace.output_tokens == expected_turns * 7
            assert any(step.decision == "repair_requested" for step in result.trace.steps) == bool(bad_text)
            if bad_text:
                assert bad_text not in result.model_dump_json()
            required_outputs = ["selected_story_ids"] + (["cards"] if bad_text else []) + ["cards", "decisions"]
            assert [set(json.loads(req.content)["text"]["format"]["schema"]["properties"])
                    for req in sent] == [{field} for field in required_outputs]
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
        http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", max_retries=0,
                                    http_client=http_client)
        runner = FoundryRunner(client, http_client=http_client)
        try:
            with pytest.raises(BudgetExceeded):
                await runner.run("analyst", {"cutoff": 269}, tools)
            assert len(sent) == 1
        finally:
            await runner.close()

    asyncio.run(run())


def test_provider_wire_schema_retains_strict_local_output_limits():
    from match_context.agents.wire import SelectionOutput
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SelectionOutput.model_validate({"selected_story_ids": ["a", "b", "c", "d"]})


def test_concurrent_sdk_calls_keep_usage_and_inputs_request_local(scenario_main):
    async def run():
        snapshot = build_snapshot(scenario_main.events, 269, scenario_main.metadata)
        request = ContextRequest(match_id=snapshot.metadata.match_id, from_sequence=0, to_sequence=269)
        first, second = prepare_tools(snapshot, request), prepare_tools(snapshot, request)
        bodies = []

        async def respond(http_request):
            raw = http_request.content.decode()
            bodies.append(raw)
            assert not ("viewer_one" in raw and "viewer_two" in raw)
            one = "viewer_one" in raw
            await asyncio.sleep(0.01)
            return httpx2.Response(200, json={"id": "r-one" if one else "r-two", "object": "response",
                "created_at": 1, "status": "completed", "model": "offline",
                "output": [{"type": "message", "id": "msg-one" if one else "msg-two", "role": "assistant",
                            "status": "completed", "content": [{"type": "output_text", "annotations": [],
                            "text": json.dumps({"selected_story_ids": [first.candidates[0].story_id]})}]}],
                "usage": {"input_tokens": 19 if one else 31, "output_tokens": 7 if one else 11,
                          "total_tokens": 26 if one else 42}})

        client = FoundryChatClient(project_endpoint="https://offline.services.ai.azure.com/api/projects/test",
                                    model="offline", credential=lambda: "offline")
        await client.client.close()
        http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(respond))
        client.client = AsyncOpenAI(api_key="offline", base_url="https://offline.invalid/v1/", http_client=http_client)
        runner = FoundryRunner(client, http_client=http_client)
        try:
            await asyncio.gather(runner.run("analyst", {"sentinel": "viewer_one"}, first),
                                 runner.run("analyst", {"sentinel": "viewer_two"}, second))
            assert (first.budget.model_calls, first.budget.input_tokens, first.budget.output_tokens) == (1, 19, 7)
            assert (second.budget.model_calls, second.budget.input_tokens, second.budget.output_tokens) == (1, 31, 11)
            assert len(bodies) == 2
        finally:
            await runner.close()
    asyncio.run(run())


def test_startup_warms_the_same_refreshable_provider_used_for_inference(monkeypatch):
    import time
    from azure.core.credentials import AccessToken
    import azure.identity.aio
    from match_context.agents.foundry import local_foundry_runner

    class Credential:
        calls = 0
        closed = False

        async def get_token(self, *scopes, **kwargs):
            assert scopes == ("https://ai.azure.com/.default",)
            self.calls += 1
            return AccessToken("offline-token", int(time.time()) + 3600)

        async def close(self):
            self.closed = True

    credential = Credential()
    monkeypatch.setattr(azure.identity.aio, "AzureCliCredential", lambda **kwargs: credential)
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://offline.services.ai.azure.com/api/projects/test")
    monkeypatch.setenv("FOUNDRY_MODEL", "offline")

    async def run():
        async with local_foundry_runner() as runner:
            assert credential.calls == 1
            # Exercise the exact SDK authentication callback, without network I/O.
            assert await runner.client.client._api_key_provider() == "offline-token"
            assert await runner.client.client._api_key_provider() == "offline-token"
            assert credential.calls == 1
            now = time.time()
            monkeypatch.setattr(time, "time", lambda: now + 3590)
            assert await runner.client.client._api_key_provider() == "offline-token"
            assert credential.calls == 2
        assert credential.closed
    asyncio.run(run())
