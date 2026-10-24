import re
import unicodedata

from match_context.domain.contracts import Claim, ContextCard, ContextResult
from .base import ValidationReport

MARKER = re.compile(r"\{\{(fact|entity):([A-Za-z0-9_-]+)\}\}")
CAUSAL = re.compile(r"\b(caused|causes|proves|therefore|because|causó|causa|causaron|demuestra|provocó|porque)\b|due to|gracias a", re.I)
HIGH_RECOVERY_LABEL = re.compile(r"\b(?:high[-\s]+recover(?:y|ies)|recuperaci(?:ón|ones)[-\s]+altas?)\b", re.I)
RECOVERY_WORD = re.compile(r"\b(?:recover\w*|recuper\w*)\b", re.I)
SHOT_INDEX_LABEL = re.compile(r"(?:calidad|índice|puntuación).*?(?:sintétic|heurístic)|(?:synthetic|heuristic).*?(?:shot|quality)", re.I)
POINT_UNIT = re.compile(r"\b(?:puntos|points)\b", re.I)
THIRD_PASS_LABEL = re.compile(r"(?:pases?|passes|passing).*?(?:último tercio|tercio ofensivo|attacking[-\s]+third)|attacking[-\s]+third.*?pass", re.I)
PERCENT_UNIT = re.compile(r"%|\b(?:por ciento|percent)\b", re.I)
FACT_AS_COORDINATE = re.compile(r"\b[xy]\s*(?:[<>]=?|[=≥≤≈:])\s*\{\{fact:", re.I)
FACT_AS_THRESHOLD = re.compile(r"(?:[<>]=?|[≥≤])\s*\{\{fact:")
METRE_UNIT = re.compile(r"\s*(?:m|metres?|meters?|metros?)\b", re.I)


def check_claim(claim: Claim, tools) -> tuple[str, ...]:
    codes = set()
    if not claim.fact_ids and not claim.event_ids:
        codes.add("missing_support")
    if any(identifier not in tools.fact_map for identifier in claim.fact_ids):
        codes.add("unknown_fact")
    known = {event.event_id for event in tools.snapshot.known_events}
    if not set(claim.event_ids) <= known:
        codes.add("unknown_event")
    if claim.kind == "interpretation" and not claim.limitations:
        codes.add("missing_limitation")
    for text in (claim.text, *claim.limitations):
        # Check the original as well: Roman numeric symbols can normalize to letters.
        if any(character.isnumeric() for character in MARKER.sub("", text)):
            codes.add("free_number")
        text = unicodedata.normalize("NFKC", text)
        markers = MARKER.findall(text)
        # The narrative fact registry contains aggregate match metrics, not
        # pitch coordinates or definition thresholds. A real count reference
        # must not be repurposed as a spatial threshold (e.g. a count of 1
        # rendered as x >= 1 instead of the canonical 70 m definition).
        if FACT_AS_COORDINATE.search(text) or FACT_AS_THRESHOLD.search(text):
            codes.add("unsupported_meaning")
        for marker in MARKER.finditer(text):
            kind, identifier = marker.groups()
            fact = tools.fact_map.get(identifier) if kind == "fact" else None
            if fact and fact.unit != "m" and METRE_UNIT.match(text[marker.end():]):
                codes.add("unsupported_meaning")
        for kind, identifier in markers:
            if kind == "fact" and (identifier not in tools.fact_map or identifier not in claim.fact_ids):
                codes.add("unknown_fact")
            if kind == "entity" and identifier not in tools.entities:
                codes.add("unknown_entity")
        free = MARKER.sub("", text)
        high_support = any(tools.fact_map[identifier].name == "high_recoveries"
                           for identifier in claim.fact_ids if identifier in tools.fact_map)
        high_number = any(kind == "fact" and identifier in tools.fact_map
                          and tools.fact_map[identifier].name == "high_recoveries" for kind, identifier in markers)
        if high_support and (high_number or RECOVERY_WORD.search(free)) and not HIGH_RECOVERY_LABEL.search(free):
            codes.add("missing_metric_qualifier")
        numeric_metrics = {tools.fact_map[identifier].name for kind, identifier in markers
                           if kind == "fact" and identifier in tools.fact_map}
        if "shot_quality_total" in numeric_metrics and not (SHOT_INDEX_LABEL.search(free) and POINT_UNIT.search(free)):
            codes.add("missing_metric_qualifier")
        if "territorial_share" in numeric_metrics and not (THIRD_PASS_LABEL.search(free) and PERCENT_UNIT.search(free)):
            codes.add("missing_metric_qualifier")
        if "{{" in free or "}}" in free:
            codes.add("invalid_marker")
        if any(character.isnumeric() for character in free):
            codes.add("free_number")
        if any(name.casefold() in free.casefold() for name in tools.entities.values()):
            codes.add("raw_entity")
        if CAUSAL.search(free):
            codes.add("causal_language")
    return tuple(sorted(codes))


def render_claim(claim: Claim, tools) -> str:
    if check_claim(claim, tools):
        raise ValueError("Cannot render an invalid claim")

    def replace(match):
        kind, identifier = match.groups()
        if kind == "entity":
            return tools.entities[identifier]
        value = tools.fact_map[identifier].value
        if value is None:
            return "—"
        return str(int(value)) if float(value).is_integer() else str(value)

    return MARKER.sub(replace, unicodedata.normalize("NFKC", claim.text))


def check_draft(draft, tools, candidate) -> tuple[str, ...]:
    codes = {code for claim in draft.claims() for code in check_claim(claim, tools)}
    allowed_facts, allowed_events = set(candidate.fact_ids), set(candidate.event_ids)
    if any(not set(claim.fact_ids) <= allowed_facts or not set(claim.event_ids) <= allowed_events
           for claim in draft.claims()):
        codes.add("unrelated_support")
    if len({claim.claim_id for claim in draft.claims()}) != 4:
        codes.add("duplicate_claim")
    if not codes:
        main_fields = [re.sub(r"\W+", " ", render_claim(claim, tools).casefold()).strip()
                       for claim in draft.claims()[:3]]
        if len(set(main_fields)) != 3:
            codes.add("repetitive_copy")
    if not codes and len(render_claim(draft.overlay, tools)) > 140:
        codes.add("overlay_length")
    return tuple(sorted(codes))


def localized_limits(language, pattern):
    if language == "es":
        values = ["Datos sintéticos; el cambio observado no demuestra una causa táctica."]
        if pattern == "chance_quality":
            values.append("La calidad de ocasión es una heurística del simulador, no xG calibrado.")
        if pattern == "territorial_shift":
            values.append("La cuota de pases en el último tercio no mide amenaza ni tiempo de posesión.")
    else:
        values = ["Synthetic data; an observed change does not establish tactical causation."]
        if pattern == "chance_quality":
            values.append("Shot quality is a simulator heuristic, not calibrated xG.")
        if pattern == "territorial_shift":
            values.append("Attacking-third passing share does not measure threat or possession time.")
    return tuple(values)


def render_card(draft, tools, candidate, language):
    if check_draft(draft, tools, candidate):
        raise ValueError("Invalid card")
    limits = (*localized_limits(language, candidate.pattern),
              *(render_claim(claim.model_copy(update={"text": limitation}), tools)
                for claim in draft.claims() for limitation in claim.limitations))
    return ContextCard(story_id=draft.story_id, headline=render_claim(draft.headline, tools),
                       explanation=render_claim(draft.explanation, tools),
                       suggested_line=render_claim(draft.suggested_line, tools),
                       overlay_text=render_claim(draft.overlay, tools), claims=draft.claims(),
                       current_interval=candidate.current_interval, comparison_interval=candidate.comparison_interval,
                       limitations=tuple(dict.fromkeys(limits)))


def validate_claims(result: ContextResult, snapshot, facts) -> ValidationReport:
    from .tools import make_scoped_tools
    from .base import CardDraft
    from .fallback import build_factual_result
    from match_context.analysis.patterns import detect_stories
    try:
        tools = make_scoped_tools(snapshot, facts)
    except ValueError:
        return ValidationReport(codes=("invalid_facts",))
    claims = (*result.summary_claims, *(claim for card in result.cards for claim in card.claims))
    rejected, accepted, codes = [], [], set()
    if (result.snapshot_id != snapshot.snapshot_id or result.request.to_sequence != snapshot.cutoff
            or result.request.match_id != snapshot.metadata.match_id):
        codes.add("wrong_snapshot")
        return ValidationReport(codes=tuple(codes))
    if result.facts != facts:
        codes.add("invalid_facts")
    if not set(result.evidence_ids) <= {event.event_id for event in snapshot.known_events}:
        codes.add("unknown_event")
    for claim in claims:
        errors = check_claim(claim, tools)
        (rejected if errors else accepted).append(claim.claim_id)
        codes.update(errors)
    if result.status == "verified":
        candidates = {story.story_id: story for story in detect_stories(snapshot, result.request)}
        card_ids = [card.story_id for card in result.cards]
        claim_ids = [claim.claim_id for card in result.cards for claim in card.claims]
        if len(set(card_ids)) != len(card_ids) or len(set(claim_ids)) != len(claim_ids):
            codes.add("duplicate_claim")
        if not result.cards or result.mode == "factual":
            codes.add("invalid_status")
        for card in result.cards:
            if card.story_id not in candidates or len(card.claims) != 4:
                codes.add("unknown_story")
                continue
            draft = CardDraft(story_id=card.story_id, headline=card.claims[0], explanation=card.claims[1],
                              suggested_line=card.claims[2], overlay=card.claims[3])
            errors = check_draft(draft, tools, candidates[card.story_id])
            codes.update(errors)
            if not errors and card != render_card(draft, tools, candidates[card.story_id], result.request.language):
                codes.add("render_mismatch")
        if (result.summary != " ".join(card.suggested_line for card in result.cards)
                or result.summary_claims != tuple(card.claims[2] for card in result.cards if len(card.claims) == 4)):
            codes.add("render_mismatch")
    else:
        expected = build_factual_result(snapshot, result.request, facts, tools=tools)
        if (result.mode != "factual" or result.cards or result.status != expected.status
                or result.summary != expected.summary or result.summary_claims != expected.summary_claims):
            codes.add("render_mismatch")
    return ValidationReport(accepted=tuple(accepted), rejected=tuple(rejected), codes=tuple(sorted(codes)))
