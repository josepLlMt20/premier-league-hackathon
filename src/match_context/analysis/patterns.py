import hashlib

from match_context.analysis.metrics import compute_facts
from match_context.domain.contracts import BoundedSnapshot, ContextRequest, StoryCandidate


def detect_stories(snapshot: BoundedSnapshot, request: ContextRequest) -> tuple[StoryCandidate, ...]:
    """Find up to three supported changes, comparing complete five-minute windows."""
    if request.match_id != snapshot.metadata.match_id or request.to_sequence != snapshot.cutoff:
        raise ValueError("Request and snapshot must have the same match and knowledge cutoff")
    teams = {team.team_id for team in snapshot.metadata.teams}
    if request.favorite_team_id is not None and request.favorite_team_id not in teams:
        raise ValueError("Unknown favorite team")
    if request.from_sequence == request.to_sequence or snapshot.cutoff_second < 600:
        return ()
    since = snapshot.known_events[request.from_sequence - 1].available_second if request.from_sequence else 0
    anchors = set(range(600, snapshot.cutoff_second + 1, 300)) | {snapshot.cutoff_second}
    stories = []
    for finish in sorted(anchors):
        if finish <= since:
            continue
        current = compute_facts(snapshot, 0, snapshot.cutoff, start_second=finish - 300, end_second=finish)
        previous = compute_facts(snapshot, 0, snapshot.cutoff, start_second=finish - 600, end_second=finish - 300)
        if any(sum(lower < e.occurred_second <= upper for e in snapshot.effective_events) < 10
               for lower, upper in ((finish - 600, finish - 300), (finish - 300, finish))):
            continue
        now = {(f.team_id, f.name): f for f in current}
        before = {(f.team_id, f.name): f for f in previous}
        for team_id in sorted(teams):
            for pattern, metric, threshold, base in (
                ("high_recoveries", "high_recoveries", 2, 100),
                ("chance_quality", "shot_quality_total", 30, 80),
                ("territorial_shift", "territorial_share", 20, 60),
            ):
                latest, prior = now[team_id, metric], before[team_id, metric]
                if latest.value is None or prior.value is None:
                    continue
                delta = round(latest.value - prior.value, 2)
                if delta < threshold:
                    continue
                support = [prior, latest]
                if pattern == "chance_quality":
                    if now[team_id, "shots"].value < 2:
                        continue
                    support += [before[team_id, "shots"], now[team_id, "shots"]]
                if pattern == "territorial_shift":
                    if min(sum(f.value for f in facts if f.name == "completed_passes") for facts in (current, previous)) < 10:
                        continue
                    support += [f for facts in (previous, current) for f in facts if f.name == "completed_passes"]
                identifiers = {identifier for fact in support for identifier in fact.event_ids}
                identity = f"{snapshot.prefix_hash}:{team_id}:{pattern}:{finish}"
                limits = ["Observed event-based change, not proof of a tactical cause."]
                if pattern == "chance_quality":
                    limits.append("Shot quality is a synthetic heuristic, not calibrated xG.")
                elif pattern == "territorial_shift":
                    limits.append("Attacking-third passing share does not establish attacking threat or possession time.")
                stories.append(StoryCandidate(
                    story_id="s-" + hashlib.sha256(identity.encode()).hexdigest()[:24],
                    pattern=pattern, team_id=team_id, delta=delta,
                    priority=base + delta / (1 if pattern == "high_recoveries" else 100) + (10 if request.favorite_team_id == team_id else 0),
                    current_interval=latest.interval, comparison_interval=prior.interval,
                    fact_ids=tuple(f.fact_id for f in support),
                    event_ids=tuple(e.event_id for e in snapshot.known_events if e.event_id in identifiers),
                    limitations=tuple(limits),
                ))
    ranked = sorted(stories, key=lambda story: (
        -story.priority, -story.current_interval.end_second, story.pattern, story.team_id, story.story_id,
    ))
    selected = []
    occupied: dict[tuple[str, str], set[str]] = {}
    for story in ranked:
        signal_kind = {"high_recoveries": "recovery", "chance_quality": "shot", "territorial_shift": "pass"}[story.pattern]
        signal = {e.event_id for e in snapshot.effective_events
                  if e.team_id == story.team_id and e.kind == signal_kind
                  and story.current_interval.start_second < e.occurred_second <= story.current_interval.end_second}
        key = story.pattern, story.team_id
        if signal & occupied.get(key, set()):
            continue
        selected.append(story)
        occupied.setdefault(key, set()).update(signal)
        if len(selected) == 3:
            break
    return tuple(selected)
