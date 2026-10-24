"""Compact provider-only schemas; public claims always retain canonical references."""

import re
from typing import Annotated, Literal

from pydantic import Field

from match_context.domain.contracts import Claim
from match_context.domain.events import FrozenModel
from .base import AgentOutput, CardDraft, ReviewDecision

FACT_MARKER = re.compile(r"\{\{fact:([A-Za-z0-9_-]+)\}\}")


class AzureOutput(FrozenModel):
    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        schema = super().model_json_schema(*args, **kwargs)
        unsupported = {"maxItems", "minItems", "maxLength", "minLength", "pattern", "format", "default",
                       "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "uniqueItems"}

        def clean(node):
            if isinstance(node, dict):
                for key in list(node):
                    if key in unsupported:
                        del node[key]
                    elif key in ("properties", "$defs"):
                        for child in node[key].values():
                            clean(child)
                    else:
                        clean(node[key])
            elif isinstance(node, list):
                for child in node:
                    clean(child)
        clean(schema)
        return schema


class SelectionOutput(AzureOutput):
    selected_story_ids: tuple[str, ...] = Field(max_length=3)


class WireClaim(FrozenModel):
    text: str = Field(min_length=1, max_length=600)
    facts: tuple[Annotated[int, Field(strict=True, ge=0)], ...] = Field(min_length=1, max_length=12)
    kind: Literal["observed", "interpretation"]
    limits: tuple[Literal["observed_association", "sample_limited"], ...] = Field(max_length=3)


class WireCard(FrozenModel):
    story_id: str
    headline: WireClaim
    explanation: WireClaim
    line: WireClaim
    overlay: WireClaim


class WritingOutput(AzureOutput):
    cards: tuple[WireCard, ...] = Field(max_length=3)


class ReviewOutput(AzureOutput):
    decisions: tuple[ReviewDecision, ...] = Field(max_length=3)


ROLE_OUTPUTS = {"analyst": SelectionOutput, "writer": WritingOutput, "reviewer": ReviewOutput}


class WireCodec:
    def __init__(self, tools, *, language="en"):
        # This map is rebuilt per invocation, exclusively from the closed snapshot.
        self._aliases = {fact.fact_id: index for index, fact in enumerate(tools.facts)}
        self._facts = {str(alias): identifier for identifier, alias in self._aliases.items()}
        self._caveats = {
            "es": {"observed_association": "Asociación observada en datos sintéticos.",
                   "sample_limited": "Conclusión limitada a la muestra de eventos disponible."},
            "en": {"observed_association": "Observed association in synthetic data.",
                   "sample_limited": "Conclusion limited to the available event sample."},
        }[language]

    def fact_id(self, alias):
        if str(alias) not in self._facts:
            raise ValueError("unknown_fact_alias")
        return self._facts[str(alias)]

    def encode(self, value):
        if isinstance(value, str):
            return self._aliases.get(value, FACT_MARKER.sub(
                lambda match: "{{fact:" + str(self._aliases.get(match[1], match[1])) + "}}", value))
        if isinstance(value, dict):
            return {key: self.encode(child) for key, child in value.items()}
        if isinstance(value, (tuple, list)):
            return [self.encode(child) for child in value]
        return value

    def _text(self, text):
        return FACT_MARKER.sub(lambda match: "{{fact:" + self.fact_id(match[1]) + "}}", text)

    def decode(self, output):
        if isinstance(output, SelectionOutput):
            return AgentOutput(selected_story_ids=output.selected_story_ids)
        if isinstance(output, ReviewOutput):
            return AgentOutput(decisions=output.decisions)
        if not isinstance(output, WritingOutput):
            raise ValueError("invalid_output")
        cards = []
        for card in output.cards:
            claims = {}
            for field, wire_field in (("headline", "headline"), ("explanation", "explanation"),
                                      ("suggested_line", "line"), ("overlay", "overlay")):
                claim = getattr(card, wire_field)
                claims[field] = Claim(claim_id=f"{card.story_id}-{field}", text=self._text(claim.text),
                    kind=claim.kind, fact_ids=tuple(self.fact_id(alias) for alias in claim.facts),
                    limitations=tuple(self._caveats[code] for code in claim.limits))
            cards.append(CardDraft(story_id=card.story_id, **claims))
        return AgentOutput(cards=tuple(cards))
