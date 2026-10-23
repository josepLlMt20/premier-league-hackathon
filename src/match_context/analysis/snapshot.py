import hashlib
import json

from match_context.domain.contracts import BoundedSnapshot, TeamScore
from match_context.domain.events import MatchEvent, MatchMetadata, validate_stream


def build_snapshot(events: tuple[MatchEvent, ...], cutoff: int, metadata: MatchMetadata) -> BoundedSnapshot:
    """Validate and reconstruct only the known prefix, ignoring all future payloads."""
    if type(cutoff) is not int or cutoff < 0:
        raise ValueError("Cutoff must be a non-negative integer")
    by_sequence: dict[int, MatchEvent] = {}
    for event in events:
        if event.sequence > cutoff:
            continue
        existing = by_sequence.get(event.sequence)
        if existing is not None and existing != event:
            raise ValueError("Event conflict at the same sequence")
        by_sequence[event.sequence] = event
    known = tuple(by_sequence[key] for key in sorted(by_sequence))
    if len(known) != cutoff:
        raise ValueError("Cutoff is beyond the available contiguous prefix")
    validate_stream(known, metadata)
    annulled = {e.attributes.target_event_id for e in known if e.kind == "correction"}
    annulled.update(e.event_id for e in known if e.kind == "goal" and e.attributes.shot_event_id in annulled)
    effective = tuple(e for e in known if e.event_id not in annulled and e.kind != "correction")
    digest_payload = {"metadata": metadata.model_dump(mode="json"),
                      "events": [event.model_dump(mode="json") for event in known]}
    digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return BoundedSnapshot(
        metadata=metadata, cutoff=cutoff, cutoff_second=known[-1].available_second if known else 0,
        known_events=known, effective_events=effective,
        annulled_event_ids=tuple(e.event_id for e in known if e.event_id in annulled),
        score=tuple(TeamScore(team_id=team.team_id, goals=sum(e.kind == "goal" and e.team_id == team.team_id for e in effective))
                    for team in metadata.teams), prefix_hash=digest,
    )
