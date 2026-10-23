import hashlib
from math import hypot

from match_context.analysis.evidence import resolve_evidence
from match_context.domain.contracts import BoundedSnapshot, FactInterval, MetricFact


def compute_facts(
    snapshot: BoundedSnapshot, start: int, end: int, *,
    start_second: int | None = None, end_second: int | None = None,
) -> tuple[MetricFact, ...]:
    """Aggregate (start,end] as known at the snapshot cutoff, optionally by occurred time."""
    if type(start) is not int or type(end) is not int or not 0 <= start <= end <= snapshot.cutoff:
        raise ValueError("Metric interval is outside the knowledge boundary")
    interval = FactInterval(start_sequence=start, end_sequence=end,
                            start_second=start_second, end_second=end_second)
    if end_second is not None and end_second > snapshot.cutoff_second:
        raise ValueError("Time interval extends beyond the known clock")

    def selected(event):
        return start < event.sequence <= end and (start_second is None or start_second < event.occurred_second <= end_second)

    originals = tuple(e for e in snapshot.known_events if selected(e))
    events = tuple(e for e in snapshot.effective_events if selected(e))
    evidence = resolve_evidence(snapshot, tuple(e.event_id for e in originals))
    evidence_ids = tuple(e.event_id for e in evidence.events)

    def normalized_x(event, point):
        return point.x if snapshot.metadata.direction(event.team_id, event.period) == 1 else 105 - point.x

    completed = [e for e in events if e.kind == "pass" and e.attributes.completed]
    third_passes = [e for e in completed if normalized_x(e, e.end) >= 70]
    facts = []
    for team in snapshot.metadata.teams:
        own = [e for e in events if e.team_id == team.team_id]
        passes = [e for e in own if e.kind == "pass"]
        shots = [e for e in own if e.kind == "shot"]
        recoveries = [e for e in own if e.kind == "recovery"]
        complete_count = sum(e.attributes.completed for e in passes)
        third_count = sum(e.team_id == team.team_id for e in third_passes)
        quality = 0.0
        for shot in shots:
            goal_x = 105 if snapshot.metadata.direction(team.team_id, shot.period) == 1 else 0
            distance = hypot(goal_x - shot.start.x, 34 - shot.start.y)
            quality += round(100 * max(0, 1 - distance / 50) * (0.7 if shot.attributes.under_pressure else 1), 2)
        counts = {
            "pass_attempts": (len(passes), "passes", None, len(passes), "All attempted passes."),
            "completed_passes": (complete_count, "passes", len(passes), len(passes), "Passes tagged completed."),
            "pass_accuracy": (round(100 * complete_count / len(passes), 2) if passes else None, "%", len(passes), len(passes), "Completed / attempted passes × 100."),
            "pass_distance_total": (round(sum(hypot(e.end.x - e.start.x, e.end.y - e.start.y) for e in passes), 2), "m", None, len(passes), "Euclidean distance of every attempted pass."),
            "shots": (len(shots), "shots", None, len(shots), "Shot events; linked goals are not additional shots."),
            "shots_on_target": (sum(e.attributes.on_target for e in shots), "shots", len(shots), len(shots), "Shots tagged on target."),
            "goals": (sum(e.kind == "goal" for e in own), "goals", None, sum(e.kind == "goal" for e in own), "Effective goal events at the knowledge cutoff."),
            "recoveries": (len(recoveries), "recoveries", None, len(recoveries), "Recovery events."),
            "high_recoveries": (sum(normalized_x(e, e.start) >= 70 for e in recoveries), "recoveries", len(recoveries), len(recoveries), "Recoveries with attacking-normalized start x ≥ 70 m."),
            "pressure_events": (sum(e.kind == "pressure" for e in own), "events", None, sum(e.kind == "pressure" for e in own), "Pressure events applied by this team."),
            "shot_quality_total": (round(quality, 2), "heuristic points", None, len(shots), "Sum of distance-and-pressure shot-quality heuristic; not calibrated xG."),
            "territorial_share": (round(100 * third_count / len(third_passes), 2) if third_passes else None, "%", len(third_passes), len(completed), "Team's completed attacking-third passes / both teams' such passes × 100."),
        }
        for name, (value, unit, denominator, sample_count, method) in counts.items():
            key = f"{snapshot.prefix_hash}:{interval.model_dump_json()}:{team.team_id}:{name}"
            limitations = ("Synthetic events; descriptive evidence does not establish tactical causation.",)
            if value is None:
                limitations += ("Undefined because the denominator is zero.",)
            if name == "shot_quality_total":
                limitations += ("Simulator heuristic, not a goal probability.",)
            facts.append(MetricFact(
                fact_id="f-" + hashlib.sha256(key.encode()).hexdigest()[:24],
                snapshot_id=snapshot.snapshot_id, cutoff_sequence=snapshot.cutoff,
                team_id=team.team_id, name=name, value=value, unit=unit,
                interval=interval, denominator=denominator, sample_count=sample_count,
                event_ids=evidence_ids, method=method, limitations=limitations,
            ))
    return tuple(facts)
