from types import MappingProxyType

from match_context.analysis.evidence import resolve_evidence
from match_context.analysis.metrics import compute_facts
from match_context.domain.contracts import BoundedSnapshot, MetricFact, StoryCandidate
from .base import RunBudget


class ToolDenied(ValueError):
    pass


def compact_fact(fact):
    value = fact.model_dump(mode="json", exclude={"event_ids"})
    value["event_sample_ids"] = list(fact.event_ids[-3:])
    value["evidence_count"] = len(fact.event_ids)
    return value


class ScopedTools:
    def __init__(self, snapshot, facts, candidates, budget):
        self.snapshot = snapshot
        self.facts = facts
        self.fact_map = MappingProxyType({fact.fact_id: fact for fact in facts})
        self.candidates = candidates
        self.budget = budget
        self.entities = MappingProxyType({
            **{team.team_id: team.name for team in snapshot.metadata.teams},
            **{player.player_id: player.name for team in snapshot.metadata.teams for player in team.players},
        })

    def _authorize(self, name, cutoff, charged=False):
        if not charged:
            self.budget.reserve_tool(name)
        self.budget.remaining()
        if type(cutoff) is not int or cutoff != self.snapshot.cutoff:
            raise ToolDenied("outside_snapshot")

    def story_payload(self, candidate):
        return {"candidate": candidate.model_dump(mode="json", exclude={"event_ids"}),
                "facts": [compact_fact(self.fact_map[identifier]) for identifier in candidate.fact_ids]}

    def list_candidates(self, cutoff: int, *, _charged=False) -> dict:
        self._authorize("list_candidates", cutoff, _charged)
        return {"snapshot_id": self.snapshot.snapshot_id, "cutoff": self.snapshot.cutoff,
                "stories": [self.story_payload(candidate) for candidate in self.candidates]}

    def read_facts(self, fact_ids: list[str], cutoff: int, *, _charged=False) -> list[dict]:
        self._authorize("read_facts", cutoff, _charged)
        if len(fact_ids) > 24 or any(identifier not in self.fact_map for identifier in fact_ids):
            raise ToolDenied("unknown_fact")
        return [compact_fact(self.fact_map[identifier]) for identifier in fact_ids]

    def inspect_events(self, event_ids: list[str], cutoff: int, *, _charged=False) -> dict:
        self._authorize("inspect_events", cutoff, _charged)
        if len(event_ids) > 10:
            raise ToolDenied("evidence_limit")
        try:
            return resolve_evidence(self.snapshot, tuple(event_ids)).model_dump(mode="json")
        except ValueError as error:
            raise ToolDenied("unknown_event") from error


def make_scoped_tools(snapshot: BoundedSnapshot, facts: tuple[MetricFact, ...], *,
                      candidates: tuple[StoryCandidate, ...] = (), budget: RunBudget | None = None) -> ScopedTools:
    canonical = {}
    for fact in facts:
        interval = fact.interval
        key = interval.model_dump_json()
        if key not in canonical:
            canonical[key] = {item.fact_id: item for item in compute_facts(
                snapshot, interval.start_sequence, interval.end_sequence,
                start_second=interval.start_second, end_second=interval.end_second)}
        if canonical[key].get(fact.fact_id) != fact:
            raise ValueError("Fact does not match canonical snapshot calculations")
    if len({fact.fact_id for fact in facts}) != len(facts):
        raise ValueError("Duplicate fact identifiers")
    identifiers = {fact.fact_id for fact in facts}
    if any(not set(candidate.fact_ids) <= identifiers for candidate in candidates):
        raise ValueError("Candidate has unknown facts")
    return ScopedTools(snapshot, facts, candidates, budget or RunBudget())
