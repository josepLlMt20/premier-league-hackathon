"""Inspect grounded context; Foundry calls require explicit --mode foundry."""

import argparse
import asyncio
import json

from match_context.agents.fallback import build_factual_result
from match_context.agents.orchestrator import orchestrate, prepare_tools
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest
from match_context.simulation.fixtures import scenario_manifest
from match_context.simulation.generator import generate_match


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("main", "neutral", "sterile", "correction"), default="main")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--from-second", type=int, default=0)
    parser.add_argument("--until-second", type=int, default=1500)
    parser.add_argument("--mode", choices=("factual", "foundry"), default="factual")
    parser.add_argument("--role", choices=("fan", "commentator"), default="fan")
    parser.add_argument("--depth", choices=("simple", "detailed"), default="simple")
    parser.add_argument("--language", choices=("es", "en"), default="es")
    parser.add_argument("--favorite-team", choices=("amber", "cobalt"))
    parser.add_argument("--include-facts", action="store_true")
    args = parser.parse_args(argv)
    if not 0 <= args.from_second <= args.until_second <= 5400:
        parser.error("Require 0 <= from-second <= until-second <= 5400")
    match = generate_match(args.scenario, args.seed if args.seed is not None else scenario_manifest(args.scenario).seed)
    cutoff = max((e.sequence for e in match.events if e.available_second <= args.until_second), default=0)
    start = max((e.sequence for e in match.events if e.available_second <= args.from_second), default=0)
    snapshot = build_snapshot(match.events, cutoff, match.metadata)
    request = ContextRequest(match_id=match.metadata.match_id, from_sequence=start, to_sequence=cutoff,
                             role=args.role, depth=args.depth, language=args.language,
                             favorite_team_id=args.favorite_team)
    if args.mode == "factual":
        tools = prepare_tools(snapshot, request)
        result = build_factual_result(snapshot, request, tools.facts, tools=tools)
    else:
        async def generate():
            from match_context.agents.foundry import local_foundry_runner
            async with local_foundry_runner() as runner:
                return await orchestrate(snapshot, request, runner)
        try:
            result = asyncio.run(generate())
        except Exception:
            # Startup errors are distinct from an in-request factual fallback.
            print(json.dumps({"status": "unavailable", "code": "foundry_startup_failed"}))
            return 1
    print(result.model_dump_json(indent=2, exclude=set() if args.include_facts else {"facts"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
