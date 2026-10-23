# Synthetic match data and analysis rules

All teams, players, event histories and results are fictional. This event-level simulator is not continuous player tracking or a calibrated physical model. Scenario labels describe controlled evaluation inputs, not conclusions supplied to an AI model.

## Events

Events are immutable Pydantic models. Unknown fields, invalid coordinates, non-finite numbers, backwards availability, inconsistent periods and invalid identifiers are rejected. Complete histories also validate contiguous sequences, unique event IDs, player membership, active players, pass recipients, substitutions and references to earlier events of the same match and team. Lineups are reconstructed in occurrence order within the known prefix, using sequence as the tie-breaker: a pass that arrives after a substitution can still belong to a player who was active when it occurred. The first eleven roster entries are the starting lineup; remaining entries are bench players.

| Field | Meaning |
| --- | --- |
| `match_id`, `event_id` | Validated, globally namespaced fictional identifiers. |
| `sequence` | Positive, contiguous order of availability. This is the knowledge boundary. |
| `occurred_second` | Integer elapsed football time, 0–5400. |
| `available_second` | Integer arrival time, at least `occurred_second`; non-decreasing through a history. |
| `period` | 1 before second 2700, 2 from 2700 onward. No stoppage time or wall-clock half-time break in this version. |
| `team_id`, `player_id` | Fictional team and optional actor. Corrections need not have an actor. |
| `start`, `end` | Event locations in metres on a 105 × 68 field; origin is fixed throughout the match. |
| `attributes` | Immutable, event-specific fields described below. |

Metadata contains rosters and each team's attack direction for each period. Teams attack opposite ends and switch ends at half-time. Normalized attacking x is x for the positive direction, or 105 − x otherwise. It must be recomputed with the event's period, not the viewer's current period.

| Kind | Attributes and interpretation |
| --- | --- |
| `pass` | `recipient_id`, `completed`, `under_pressure`; actor and recipient are different active teammates. Start/end locations allow Euclidean pass distance. |
| `recovery` | No extra attributes. Team gains possession; high recovery means normalized start x ≥ 70 m. |
| `turnover` | `to_team_id`, the opposing team. |
| `pressure` | No extra attributes. Actor belongs to the team applying pressure. |
| `shot` | `on_target`, `under_pressure`; event location is the shot origin. |
| `goal` | `shot_event_id` identifies an earlier on-target shot by the same team; the goal cannot occur before that shot. One shot cannot score twice. A goal is not a second shot. |
| `substitution` | `replaced_player_id`, `replacement_player_id`; one active player leaves and a rostered bench player enters. |
| `correction` | `target_event_id`, `action=annul`; target must already exist. The original event remains in the log. Replacement corrections and substitution annulments are explicitly unsupported and rejected. |

## Reproducible scenarios

`generate_match(scenario, seed)` returns only metadata and events; the same arguments reproduce the same history. Each match spans 90 minutes with at least ten events in every five-minute evaluation window. Player names, team names and coordinates are synthetic. Event positions represent observed actions with gaps, not the position of every player between events.

| Scenario | Evaluation seed | Controlled behavior |
| --- | --- | --- |
| `main` | 7 | From seconds (900,1200] to (1200,1500], Ámbar's high recoveries increase from 1 to 4; better shooting opportunities follow. |
| `neutral` | 11 | Repeating balanced passages without an introduced change of pattern. Zero goals is a valid result. |
| `sterile` | 19 | More attacking-third passing for Ámbar in the focus window, without a corresponding increase in shots. |
| `correction` | 23 | Main-style change, followed by an annulment arriving after a goal. Earlier knowledge must retain the original score. |

`simulation/fixtures.py` holds separate evaluation manifests. They are not part of metadata, snapshots or public evidence. Tests use their expectations to assess the engine; the engine must derive facts from events.

## Measurement definitions

The next layer reconstructs effective events at a sequence cutoff. Corrections apply only after they are available; annulling a shot also suppresses its linked goal. Prior snapshots remain unchanged.

Sequence selection is `(start, end]`. Time comparisons use explicit occurred-time windows and still share the same availability cutoff. A correction may change what is known about an older interval; it does not give an earlier viewer future knowledge.

- **Shot quality:** `round(100 * max(0, 1 - distance_metres / 50) * pressure_factor, 2)`, distance to the opposing goal centre; pressure factor 0.7 under pressure, 1 otherwise. This is a simulator heuristic, not calibrated xG or a probability of scoring.
- **Pass accuracy:** completed passes / attempted passes × 100; no attempts means undefined, not zero accuracy.
- **Territorial share (field tilt):** a team's completed passes ending in its attacking third / both teams' completed passes ending in their attacking thirds × 100. No qualifying passes means undefined. It measures event-based activity, not possession time or continuous territory control.
- **High recoveries:** recoveries beginning in the attacking third, defined by normalized x ≥ 70 m.
- **Candidate rules:** high recoveries increase by at least 2; shot quality total increases by at least 30 with at least 2 current shots; territorial share increases by at least 20 percentage points with at least 10 completed passes in each comparison window.

Patterns compare complete 300-second windows. The engine examines five-minute boundaries within the requested interval and its latest known point. Ranking is deterministic; overlapping candidates of the same pattern and team that reuse the same current recovery, shot or pass events are suppressed, leaving at most three distinct episodes. A favorite team can affect ranking, never the measured facts.

Observations with insufficient history or samples retain their facts without manufacturing a trend. Each fact records its interval, denominator where relevant, method and evidence. Interpretations based on these heuristics must not assert demonstrated tactical causation.
