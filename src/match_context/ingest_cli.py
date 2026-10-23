"""Local durable replay inspection; never calls a model or provisions Azure."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time

from match_context.analysis.snapshot import build_snapshot
from match_context.simulation.fixtures import scenario_manifest
from match_context.simulation.generator import generate_match
from match_context.simulation.ingest import IngestionFailed, Ingestor
from match_context.storage.sqlite import SQLiteEventLog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("tmp/matches.sqlite3"))
    parser.add_argument("--scenario", choices=("main", "neutral", "sterile", "correction"), default="main")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--until-second", type=int, default=1500)
    parser.add_argument("--view-second", type=int)
    parser.add_argument("--speed", type=float, default=30)
    parser.add_argument("--realtime", action="store_true", help="Advance using wall time at the selected speed.")
    args = parser.parse_args(argv)
    view_second = args.until_second if args.view_second is None else args.view_second
    if not 0 <= view_second <= args.until_second <= 5400:
        parser.error("Require 0 <= view-second <= until-second <= 5400")
    try:
        Ingestor._check_elapsed(args.speed, positive=True)
    except ValueError as error:
        parser.error(str(error))
    seed = args.seed if args.seed is not None else scenario_manifest(args.scenario).seed
    match = generate_match(args.scenario, seed)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    log = SQLiteEventLog(args.database)
    try:
        ingestor = Ingestor(log, (match,), speed=args.speed)
        match_id = match.metadata.match_id
        initial = log.position(match_id)
        if args.until_second < initial.available_second:
            parser.error("Cannot rewind shared ingestion; use --view-second to inspect an earlier position")
        if args.realtime:
            previous = time.monotonic()
            while log.position(match_id).available_second < args.until_second:
                time.sleep(0.05)
                now = time.monotonic()
                remaining = (args.until_second - log.position(match_id).available_second) / args.speed
                ingestor.advance(match_id, min(now - previous, remaining))
                previous = now
        else:
            ingestor.tick(match_id, args.until_second)
        position = log.position(match_id)
        events = log.read_through(match_id, position.sequence)
        cutoff = max((event.sequence for event in events if event.available_second <= view_second), default=0)
        snapshot = build_snapshot(log.read_through(match_id, cutoff), cutoff, log.metadata(match_id))
        print(json.dumps({
            "synthetic": True, "storage": "sqlite", "match_id": match_id,
            "ingestion": {**asdict(ingestor.status(match_id)), "new_events": position.sequence - initial.sequence},
            "view": {"requested_second": view_second, "cutoff_sequence": cutoff,
                     "last_event_second": snapshot.cutoff_second,
                     "score": {score.team_id: score.goals for score in snapshot.score}},
        }, indent=2))
    except IngestionFailed:
        print(json.dumps({"status": "failed", "ingestion": asdict(ingestor.status(match.metadata.match_id))}))
        return 1
    finally:
        log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
