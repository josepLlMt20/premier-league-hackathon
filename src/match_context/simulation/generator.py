import hashlib
import random

from match_context.domain.events import GeneratedMatch, MatchEvent, MatchMetadata


def generate_match(scenario: str, seed: int) -> GeneratedMatch:
    """Generate a complete seeded event log; event coordinates are not continuous tracking."""
    if scenario not in ("main", "neutral", "sterile", "correction"):
        raise ValueError("Unknown synthetic scenario")
    rng = random.Random(seed)
    match_id = "m-" + hashlib.sha256(f"{scenario}:{seed}".encode()).hexdigest()[:16]
    metadata = MatchMetadata.model_validate({
        "match_id": match_id,
        "teams": [{"team_id": team, "name": name, "players": [
            {"player_id": f"{team}-{i:02}", "name": f"{name.split()[0]} {i:02}"}
            for i in range(1, 15)
        ]} for team, name in (("amber", "Ámbar FC"), ("cobalt", "Cobalto United"))],
        "attack_directions": [{"team_id": team, "period": period, "direction": direction}
            for team, period, direction in (("amber", 1, 1), ("amber", 2, -1), ("cobalt", 1, -1), ("cobalt", 2, 1))],
    })
    events: list[MatchEvent] = []
    active = {t.team_id: [p.player_id for p in t.players[:11]] for t in metadata.teams}
    owner = None
    goal_id = None
    kickoff = None

    def other(team):
        return "cobalt" if team == "amber" else "amber"

    def point(team, second, x, y=None):
        direction = metadata.direction(team, 1 if second < 2700 else 2)
        return {"x": round(x if direction == 1 else 105 - x, 3),
                "y": round(y if y is not None else rng.uniform(12, 56), 3)}

    def emit(kind, second, team, player, start=None, end=None, attributes=None):
        event = MatchEvent.model_validate({
            "match_id": match_id, "event_id": f"{match_id}-e{len(events)+1:05}",
            "sequence": len(events) + 1, "occurred_second": second,
            "available_second": second, "period": 1 if second < 2700 else 2,
            "kind": kind, "team_id": team, "player_id": player,
            "start": start, "end": end, "attributes": attributes or {},
        })
        events.append(event)
        return event.event_id

    for minute in range(90):
        second = minute * 60
        team = ("amber", "cobalt", "amber", "cobalt", "amber")[minute % 5]
        focused = 20 <= minute < 25
        pressure_phase = scenario in ("main", "correction") and 15 <= minute < 25
        if pressure_phase:
            team = "amber"
        if scenario == "sterile" and focused:
            team = "cobalt" if minute == 24 else "amber"
        if kickoff is not None:
            team, kickoff = kickoff, None
        high = pressure_phase and (minute == 18 or minute in (20, 21, 23, 24))
        if owner == team:
            emit("turnover", second, team, active[team][0], point(team, second, 45),
                 attributes={"to_team_id": other(team)})
        emit("recovery", second + 1, team, active[team][0], point(team, second + 1, 82 if high else 16))
        owner = team
        if minute == 60:
            replaced = active["amber"][0]
            emit("substitution", second + 3, "amber", replaced,
                 attributes={"replaced_player_id": replaced, "replacement_player_id": "amber-12"})
            active["amber"][0] = "amber-12"
        if scenario == "correction" and minute == 26:
            emit("correction", second + 5, "amber", None,
                 attributes={"target_event_id": goal_id, "action": "annul"})
        shot_minute = minute % 5 == 4
        if pressure_phase:
            shot_minute = minute in (17, 21, 24)
        if scenario == "sterile" and focused:
            shot_minute = False
        current = point(team, second + 1, 82 if high else 16)
        for slot, normal_x in enumerate((30, 40, 49, 58, 65, 72, 76, 81, 84), 1):
            clock = second + slot * 6
            actor = active[team][(slot - 1) % len(active[team])]
            if slot == 9 and shot_minute:
                quality_x = 92 if pressure_phase and focused else 48
                current = point(team, clock, quality_x, 34)
                shot_id = emit("shot", clock, team, actor, current,
                    attributes={"on_target": focused or minute % 3 == 0, "under_pressure": not focused})
                if pressure_phase and minute == 24:
                    goal_id = emit("goal", clock + 1, team, actor, current,
                                   attributes={"shot_event_id": shot_id})
                    kickoff = other(team)
                continue
            if high or scenario == "sterile" and focused and team == "amber":
                normal_x = 81 + slot
            elif scenario == "sterile" and focused and team == "cobalt":
                normal_x = 30 + slot
            target = point(team, clock, normal_x + rng.uniform(-1, 1))
            completed = not (slot == 9 and minute % 11 == 0)
            emit("pass", clock, team, actor, current, target,
                 {"recipient_id": active[team][slot % len(active[team])],
                  "completed": completed, "under_pressure": high})
            current = target
            if not completed:
                owner = other(team)
        if (minute + 1) % 5 == 0:
            defending = other(owner)
            emit("pressure", second + 60, defending, active[defending][0], current)
    return GeneratedMatch(metadata=metadata, events=tuple(events))
