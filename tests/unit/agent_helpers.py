from match_context.agents.base import AgentOutput, CardDraft, ReviewDecision
from match_context.domain.contracts import Claim


def compact_card(draft, codec):
    card = {"story_id": draft.story_id}
    for field, claim in zip(("headline", "explanation", "line", "overlay"), draft.claims()):
        card[field] = codec.encode({"text": claim.text, "facts": list(claim.fact_ids),
                                    "kind": claim.kind,
                                    "limits": ["observed_association"] if claim.limitations else []})
    return card


def draft_for(story, language="es"):
    candidate = story["candidate"]
    team = "{{entity:" + candidate["team_id"] + "}}"

    def metric(name):
        facts = [f for f in story["facts"] if f["name"] == name]
        before, now = facts[:2]
        return ("{{fact:" + before["fact_id"] + "}}", "{{fact:" + now["fact_id"] + "}}",
                (before["fact_id"], now["fact_id"]))

    pattern = candidate["pattern"]
    before, now, refs = metric({"high_recoveries": "high_recoveries", "chance_quality": "shots",
                               "territorial_shift": "territorial_share"}[pattern])
    if pattern == "chance_quality":
        previous_quality, quality, quality_refs = metric("shot_quality_total")
        shot_counts = [f["value"] for f in story["facts"] if f["name"] == "shots"]
        volume_grew = shot_counts[1] > shot_counts[0]
        if language == "es":
            texts = (f"{team} aumenta su volumen de tiros." if volume_grew else f"{team} eleva su índice sintético de tiro.",
                     f"Registra {now} tiros frente a {before}; su índice sintético de tiro pasa de {previous_quality} a {quality} puntos.",
                     f"{team} ha pasado de {before} a {now} tiros en este tramo." if volume_grew else f"{team}: el índice sintético de tiro sube de {previous_quality} a {quality} puntos, con {now} tiros.",
                     f"{team}: {now} tiros; antes, {before}." if volume_grew else f"{team}: índice sintético de tiro {quality} puntos.")
        else:
            texts = (f"{team} increases its shot volume." if volume_grew else f"{team} raises its synthetic shot-quality index.",
                     f"Records {now} shots versus {before}; the synthetic shot-quality index rises from {previous_quality} to {quality} points.",
                     f"{team} has gone from {before} shots to {now} in this spell." if volume_grew else f"{team}'s synthetic shot-quality index rises from {previous_quality} to {quality} points, with {now} shots.",
                     f"{team}: {now} shots; previously {before}." if volume_grew else f"{team}: synthetic shot-quality index {quality} points.")
        supports = (refs if volume_grew else quality_refs, (*refs, *quality_refs),
                    refs if volume_grew else (*refs, *quality_refs), refs if volume_grew else quality_refs)
    elif pattern == "territorial_shift":
        if language == "es":
            texts = (f"{team} gana peso en los pases del último tercio.",
                     f"Su cuota de pases completados en el último tercio es {now}%, frente al {before}% anterior; el total incluye a ambos equipos en sus respectivos tercios ofensivos.",
                     f"{team} aumenta su cuota de pases completados en el último tercio: del {before}% al {now}%.",
                     f"{team}: {now}% de los pases completados en el último tercio.")
        else:
            texts = (f"{team} grows its share of attacking-third passes.",
                     f"Its completed attacking-third pass share is {now}%, previously {before}%; the total covers both teams in their respective attacking thirds.",
                     f"{team} increases its completed attacking-third pass share from {before}% to {now}%.",
                     f"{team}: {now}% of completed attacking-third passes.")
        supports = (refs,) * 4
    else:
        if language == "es":
            texts = (f"{team} aumenta sus recuperaciones altas.",
                     f"Registra {now} recuperaciones altas frente a {before}; se cuentan las recuperaciones en el tercio ofensivo.",
                     f"{team} suma más recuperaciones altas: {now}, frente a {before} en el tramo anterior.",
                     f"{team}: recuperaciones altas {before} → {now}.")
        else:
            texts = (f"{team} increases its high recoveries.",
                     f"Records {now} high recoveries versus {before}; these are recoveries in the attacking third.",
                     f"{team} registers more high recoveries: {now}, compared with {before} in the previous spell.",
                     f"{team}: high recoveries {before} → {now}.")
        supports = (refs,) * 4
    claims = [Claim(claim_id=f"claim-{candidate['story_id']}-{index}", kind="observed", text=text,
                    fact_ids=tuple(support), event_ids=())
              for index, (text, support) in enumerate(zip(texts, supports))]
    return CardDraft(story_id=candidate["story_id"], headline=claims[0], explanation=claims[1],
                     suggested_line=claims[2], overlay=claims[3])


class ScriptedRunner:
    mode = "scripted"

    def __init__(self):
        self.calls = []
        self.tools_seen = []

    async def run(self, role, payload, tools):
        self.calls.append((role, payload))
        self.tools_seen.append(tools)
        if role == "analyst":
            stories = tools.list_candidates(tools.snapshot.cutoff)["stories"]
            return AgentOutput(selected_story_ids=tuple(s["candidate"]["story_id"] for s in stories))
        if role == "writer":
            return AgentOutput(cards=tuple(draft_for(story) for story in payload["stories"]))
        return AgentOutput(decisions=tuple(ReviewDecision(story_id=c["story_id"], accepted=True)
                                           for c in payload["cards"]))
