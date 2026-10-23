from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")]
Second = Annotated[int, Field(ge=0, le=5400, strict=True)]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class Point(FrozenModel):
    x: float = Field(ge=0, le=105)
    y: float = Field(ge=0, le=68)


class Player(FrozenModel):
    player_id: Identifier
    name: str = Field(min_length=1, max_length=80)


class Team(FrozenModel):
    team_id: Identifier
    name: str = Field(min_length=1, max_length=80)
    players: tuple[Player, ...] = Field(min_length=2)


class AttackDirection(FrozenModel):
    team_id: Identifier
    period: Literal[1, 2]
    direction: Literal[-1, 1]


class MatchMetadata(FrozenModel):
    match_id: Identifier
    duration_seconds: Literal[5400] = 5400
    teams: tuple[Team, Team]
    attack_directions: tuple[AttackDirection, ...]

    @model_validator(mode="after")
    def validate_rosters(self):
        teams = {team.team_id for team in self.teams}
        players = [p.player_id for team in self.teams for p in team.players]
        if len(teams) != 2 or len(players) != len(set(players)):
            raise ValueError("Team and player identifiers must be unique")
        keys = [(a.team_id, a.period) for a in self.attack_directions]
        if len(keys) != 4 or set(keys) != {(t, p) for t in teams for p in (1, 2)}:
            raise ValueError("Attack directions must cover both teams and periods")
        for period in (1, 2):
            if sum(a.direction for a in self.attack_directions if a.period == period) != 0:
                raise ValueError("Teams must attack opposite goals")
        for team in teams:
            if sum(a.direction for a in self.attack_directions if a.team_id == team) != 0:
                raise ValueError("Teams must switch ends at half-time")
        return self

    def direction(self, team_id: str, period: int) -> int:
        for direction in self.attack_directions:
            if (direction.team_id, direction.period) == (team_id, period):
                return direction.direction
        raise ValueError("Unknown team or period")


class EmptyAttributes(FrozenModel):
    pass


class PassAttributes(FrozenModel):
    recipient_id: Identifier
    completed: bool = Field(strict=True)
    under_pressure: bool = Field(default=False, strict=True)


class TurnoverAttributes(FrozenModel):
    to_team_id: Identifier


class ShotAttributes(FrozenModel):
    on_target: bool = Field(strict=True)
    under_pressure: bool = Field(default=False, strict=True)


class GoalAttributes(FrozenModel):
    shot_event_id: Identifier


class CorrectionAttributes(FrozenModel):
    target_event_id: Identifier
    action: Literal["annul"]


class SubstitutionAttributes(FrozenModel):
    replaced_player_id: Identifier
    replacement_player_id: Identifier


_ATTRIBUTE_TYPES = {
    "pass": PassAttributes, "recovery": EmptyAttributes,
    "turnover": TurnoverAttributes, "pressure": EmptyAttributes,
    "shot": ShotAttributes, "goal": GoalAttributes,
    "correction": CorrectionAttributes, "substitution": SubstitutionAttributes,
}


class MatchEvent(FrozenModel):
    match_id: Identifier
    event_id: Identifier
    sequence: int = Field(ge=1, strict=True)
    occurred_second: Second
    available_second: Second
    period: Literal[1, 2]
    kind: Literal["pass", "recovery", "turnover", "pressure", "shot", "goal", "substitution", "correction"]
    team_id: Identifier
    player_id: Identifier | None = None
    start: Point | None = None
    end: Point | None = None
    attributes: PassAttributes | TurnoverAttributes | ShotAttributes | GoalAttributes | CorrectionAttributes | SubstitutionAttributes | EmptyAttributes

    @model_validator(mode="before")
    @classmethod
    def parse_attributes(cls, data):
        if isinstance(data, dict) and data.get("kind") in _ATTRIBUTE_TYPES:
            data = dict(data)
            data["attributes"] = _ATTRIBUTE_TYPES[data["kind"]].model_validate(data.get("attributes", {}))
        return data

    @model_validator(mode="after")
    def validate_shape(self):
        if self.available_second < self.occurred_second:
            raise ValueError("An event cannot arrive before it occurs")
        if self.period != (1 if self.occurred_second < 2700 else 2):
            raise ValueError("Period does not match elapsed match time")
        if not isinstance(self.attributes, _ATTRIBUTE_TYPES[self.kind]):
            raise ValueError("Attributes do not match event kind")
        if self.kind in ("pass", "shot", "recovery", "pressure", "turnover"):
            if self.player_id is None or self.start is None:
                raise ValueError("On-ball and pressure events require a player and location")
        if self.kind == "pass" and self.end is None:
            raise ValueError("A pass requires its end location")
        return self


def validate_event(event: MatchEvent) -> None:
    MatchEvent.model_validate(event.model_dump())


def validate_stream(events: tuple[MatchEvent, ...], metadata: MatchMetadata) -> None:
    known: dict[str, MatchEvent] = {}
    rosters = {team.team_id: {p.player_id for p in team.players} for team in metadata.teams}
    active = {team.team_id: {p.player_id for p in team.players[:11]} for team in metadata.teams}
    previous_available = -1
    scored_shots: set[str] = set()
    for expected_sequence, event in enumerate(events, 1):
        validate_event(event)
        if event.match_id != metadata.match_id or event.sequence != expected_sequence:
            raise ValueError("Events must form a contiguous prefix of the same match")
        if event.event_id in known or event.available_second < previous_available:
            raise ValueError("Duplicate event or non-monotonic availability")
        if event.team_id not in rosters or event.player_id is not None and event.player_id not in rosters[event.team_id]:
            raise ValueError("Unknown team or player")
        if event.player_id is not None and event.kind != "correction" and event.player_id not in active[event.team_id]:
            raise ValueError("Player is not active")
        attributes = event.attributes
        if event.kind == "pass" and (attributes.recipient_id not in active[event.team_id] or attributes.recipient_id == event.player_id):
            raise ValueError("Pass recipient must be a different active teammate")
        if event.kind == "turnover" and (attributes.to_team_id not in rosters or attributes.to_team_id == event.team_id):
            raise ValueError("Turnover must transfer possession to the other team")
        if event.kind == "goal":
            shot = known.get(attributes.shot_event_id)
            if shot is None or shot.kind != "shot" or shot.team_id != event.team_id or not shot.attributes.on_target:
                raise ValueError("Goal must reference an earlier on-target shot of the same team")
            if attributes.shot_event_id in scored_shots:
                raise ValueError("A shot cannot score twice")
            scored_shots.add(attributes.shot_event_id)
        if event.kind == "correction":
            target = known.get(attributes.target_event_id)
            if target is None or target.kind == "correction" or target.team_id != event.team_id:
                raise ValueError("Correction must reference an earlier event of the same team and match")
        if event.kind == "substitution":
            if attributes.replaced_player_id not in active[event.team_id] or attributes.replacement_player_id not in rosters[event.team_id] - active[event.team_id]:
                raise ValueError("Substitution requires an active player and a bench replacement")
            active[event.team_id].remove(attributes.replaced_player_id)
            active[event.team_id].add(attributes.replacement_player_id)
        known[event.event_id] = event
        previous_available = event.available_second


class GeneratedMatch(FrozenModel):
    metadata: MatchMetadata
    events: tuple[MatchEvent, ...]

    @model_validator(mode="after")
    def validate_history(self):
        validate_stream(self.events, self.metadata)
        return self
