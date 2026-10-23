from match_context.agents.base import AgentOutput, CardDraft, ReviewDecision
from match_context.domain.contracts import Claim


def draft_for(story):
    candidate = story["candidate"]
    facts = [f for f in story["facts"] if f["name"] == {
        "high_recoveries": "high_recoveries", "chance_quality": "shot_quality_total",
        "territorial_shift": "territorial_share",
    }[candidate["pattern"]]]
    before, now = facts[:2]
    text = ("{{entity:" + candidate["team_id"] + "}}: "
            "{{fact:" + now["fact_id"] + "}}, antes {{fact:" + before["fact_id"] + "}}.")
    claims = [Claim(claim_id=f"claim-{candidate['story_id']}-{index}", kind="observed", text=text,
                    fact_ids=(now["fact_id"], before["fact_id"]), event_ids=()) for index in range(4)]
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
