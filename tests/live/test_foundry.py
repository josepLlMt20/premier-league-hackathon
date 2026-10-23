"""Explicitly opted-in live requests; ordinary pytest never spends model quota."""
import asyncio
import json
import os
from pathlib import Path

import pytest

from match_context.agents.orchestrator import orchestrate
from match_context.agents.validation import validate_claims
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest
from match_context.simulation.generator import generate_match

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.environ.get("RUN_FOUNDRY_LIVE") != "1",
                                                 reason="Set RUN_FOUNDRY_LIVE=1 to spend Foundry quota")]


def test_three_foundry_roles_real_tools_and_isolated_requests():
    async def run():
        from match_context.agents.foundry import local_foundry_runner
        match = generate_match("main", 7)
        reports = []
        async with local_foundry_runner() as runner:
            for until, language in ((1500, "es"), (1490, "en")):
                cutoff = max(e.sequence for e in match.events if e.available_second <= until)
                snapshot = build_snapshot(match.events, cutoff, match.metadata)
                request = ContextRequest(match_id=match.metadata.match_id, from_sequence=0, to_sequence=cutoff,
                                         language=language)
                result = await orchestrate(snapshot, request, runner)
                reports.append(result)
                path = Path("tmp/foundry-agents")
                path.mkdir(parents=True, exist_ok=True)
                (path / f"live-{until}-{language}.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
                print(json.dumps({"until": until, "status": result.status, "mode": result.mode,
                                  "cards": len(result.cards), "rejections": result.rejection_codes,
                                  "trace": result.trace.model_dump(mode="json")}))
                assert result.status == "verified" and result.mode == "foundry"
                assert {step.role for step in result.trace.steps} >= {"analyst", "writer", "reviewer"}
                assert 3 <= result.trace.model_calls <= 7
                assert 1 <= result.trace.tool_calls <= 8
                assert result.trace.input_tokens > 0 and result.trace.output_tokens > 0
                assert not validate_claims(result, snapshot, result.facts).codes
                assert all(e.available_second <= until for e in snapshot.known_events)
            assert reports[0].trace_id != reports[1].trace_id
            assert reports[0].snapshot_id != reports[1].snapshot_id
            assert reports[1].request.to_sequence < reports[0].request.to_sequence
        return reports
    asyncio.run(run())
