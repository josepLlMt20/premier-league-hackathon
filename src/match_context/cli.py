import argparse
import json

from match_context.analysis.evidence import resolve_evidence
from match_context.analysis.metrics import compute_facts
from match_context.analysis.patterns import detect_stories
from match_context.analysis.snapshot import build_snapshot
from match_context.domain.contracts import ContextRequest
from match_context.simulation.fixtures import scenario_manifest
from match_context.simulation.generator import generate_match


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect synthetic match facts and evidence; no cloud calls.")
    parser.add_argument("--scenario", choices=("main", "neutral", "sterile", "correction"), default="main")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--from-second", type=int, default=0)
    parser.add_argument("--until-second", type=int, default=1500)
    parser.add_argument("--favorite-team", choices=("amber", "cobalt"))
    parser.add_argument("--include-evidence", action="store_true", help="Include raw known events supporting the output.")
    arguments = parser.parse_args(argv)
    if not 0 <= arguments.from_second <= arguments.until_second <= 5400:
        parser.error("Require 0 <= from-second <= until-second <= 5400")
    seed = arguments.seed if arguments.seed is not None else scenario_manifest(arguments.scenario).seed
    match = generate_match(arguments.scenario, seed)
    cutoff = max((e.sequence for e in match.events if e.available_second <= arguments.until_second), default=0)
    start = max((e.sequence for e in match.events if e.available_second <= arguments.from_second), default=0)
    snapshot = build_snapshot(match.events, cutoff, match.metadata)
    request = ContextRequest(match_id=match.metadata.match_id, from_sequence=start,
                             to_sequence=cutoff, favorite_team_id=arguments.favorite_team)
    facts = compute_facts(snapshot, start, cutoff)
    candidates = detect_stories(snapshot, request)
    fact_registry = {fact.fact_id: fact for fact in facts}
    comparison_windows = {
        (interval.start_second, interval.end_second)
        for story in candidates for interval in (story.current_interval, story.comparison_interval)
    }
    for lower, upper in sorted(comparison_windows):
        for fact in compute_facts(snapshot, 0, cutoff, start_second=lower, end_second=upper):
            fact_registry[fact.fact_id] = fact
    stories = []
    for story in candidates:
        item = story.model_dump(mode="json")
        item["facts"] = [fact_registry[identifier].model_dump(mode="json") for identifier in story.fact_ids]
        stories.append(item)
    report = {
        "synthetic": True,
        "status": "factual" if len(snapshot.known_events) >= 10 else "insufficient",
        "match_id": match.metadata.match_id,
        "teams": [{"team_id": team.team_id, "name": team.name} for team in match.metadata.teams],
        "snapshot_id": snapshot.snapshot_id,
        "cutoff_sequence": cutoff,
        "clock_second": snapshot.cutoff_second,
        "requested_seconds": {"from": arguments.from_second, "until": arguments.until_second},
        "score": {score.team_id: score.goals for score in snapshot.score},
        "facts": [fact.model_dump(mode="json") for fact in facts],
        "stories": stories,
        "limitations": ["Synthetic, event-based simulation; no continuous tracking or calibrated xG.",
                        "Patterns are descriptive; a detected change does not prove a tactical cause."],
    }
    if arguments.include_evidence:
        references = {identifier for fact in facts for identifier in fact.event_ids}
        references.update(identifier for story in candidates for identifier in story.event_ids)
        report["evidence"] = resolve_evidence(snapshot, tuple(references)).model_dump(mode="json")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0
