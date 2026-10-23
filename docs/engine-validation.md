# Generator and evidence engine: delivery record

Date: 23 October 2026. Branch: `feat/synthetic-match-engine`.

## Delivered and verified

The delivery implements plan tasks 1 and 3 and the minimal Python packaging they need. It includes four reproducible 90-minute event histories, immutable data contracts, prefix snapshots, correction-aware scores and metrics, inspectable evidence, deterministic pattern ranking and a local JSON command. It makes no Azure or model calls.

The full local suite passes **75 tests**. Editable installation, dependency compatibility, compilation and the installed command were also checked. CLI runs exercised the main, neutral and sterile scenarios and the correction at seconds 1500 and 1600. The latter preserves the earlier 1–0 score and later shows 0–0. The latest known clock at the second request is 1596, since no event arrives at exactly 1600.

Tests cover hand-calculated pass distances and percentages, opposite attack directions after half-time, heuristic shot quality, exact pattern thresholds, neutral and sparse samples, empty intervals, stable ranking and favorite-team changes, foreign and future evidence, duplicate conflicts, future-independent hashes, same-second sequences, late actors/recipients, nested immutability and late goal annulments.

## Independent review and fixes

A fresh reviewer inspected the branch read-only and independently ran the original 65-test suite. It found no Critical issue, three Important issues and two initially classified Minor issues. Both Minor issues were reclassified as Important by effect: accepting a goal before its shot violates the data contract, and reporting an empty selected interval as factual misstates the available observations.

All five findings were reproduced before their fixes. Seven regression cases failed against the original implementation; additional cases preserved valid lineup behavior and checked ranking ties. One fix pass addressed:

1. New sequences arriving in the same second are considered even when the exclusive start sequence has that timestamp.
2. Active players and recipients are validated at occurrence time within the known prefix, with sequence breaking occurrence-time ties.
3. Unsupported substitution annulments are rejected explicitly; they cannot leave effective history and lineup validation contradictory.
4. A goal cannot occur before its linked shot.
5. CLI sufficiency considers the selected observations and available comparison candidates, not just the full history length.

The full suite then passed 75/75. No review finding is left as a deferred minor. This is one independent review followed by regression verification of the fixes, not a claim that a second independent review was performed.

## Decisions and boundaries

| Decision | Reason and practical cost |
| --- | --- |
| Deliver tasks 1 and 3 with minimal Python setup. | This is the user's requested scope. Full configuration service, ingestion, API, agents and UI remain later work. |
| Keep the current directory on a new branch. | The user selected this preference; no extra worktree was created. |
| Permit optional occurred-time filters in `compute_facts`. | Availability controls knowledge and occurrence controls comparison windows. Callers must preserve both bounds. |
| Define territorial share as completed attacking-third pass share. | It has an explicit denominator; it is not continuous territory or possession time. |
| Support annul-only corrections; suppress a goal linked to an annulled shot. Reject substitution annulments. | Preserves raw history and a coherent supported subset; replacement or roster corrections need a later design. |
| Normalize plan headings from `Tarea` to `Task`. | The task-recording scripts require the latter label; this does not change the product behavior. |
| Provide a local JSON inspection command. | Makes the engine reviewable before the web interface exists; adds a small supported CLI surface. |
| Suppress overlapping same-pattern/team candidates sharing current signal events. | Avoids duplicate stories; partially overlapping episodes can be combined. |
| Keep full comparison windows on short requests. | Earlier context is permitted by the design; evidence can precede the selected interval and carries explicit dates. |

The review deliberately set aside API/UI response races, browser storage, persistence/restarts/pagination, model memory and language validation, provider failures and deployment. They belong to later tasks and are not claimed as verified here. Calibration against real football and continuous tracking are also unclaimed. `BoundedSnapshot` is an internal trusted result of `build_snapshot`; future APIs must accept requests and build it server-side rather than deserialize a caller-supplied snapshot.

## Run it

Follow the [README](../README.md#run-the-match-engine-locally), then:

```powershell
.\.venv\Scripts\python.exe -m match_context --scenario main --until-second 1500 --include-evidence
.\.venv\Scripts\python.exe -m pytest -q
```

Definitions and simulator limits are in the [data dictionary](data-dictionary.md). Synthetic tests establish behavior in these inputs; they do not establish real-world utility or the absence of errors outside the evaluated cases.
