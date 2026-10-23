# Persistent ingestion validation

Scope: task 2 of the approved implementation plan, 23 October 2026. This delivery adds durable history and a single shared ingestion writer. It does not add the HTTP service, browser playback controls, agents or cloud deployment.

## Storage contract

`EventLog` provides `register_match`, `metadata`, `position`, `head`, `append`, `read_through`, `advance_clock` and `close`. Metadata and events are immutable. Unknown matches raise `MatchNotFound` rather than masquerading as an empty match. A repeated identical event returns false; conflicting event identifiers or sequence slots raise `EventConflict`.

Each append revalidates the full historical prefix using the existing domain validator. It rejects gaps, invalid players/teams, duplicate identities, invalid goal references and non-monotonic availability before committing anything. Historical substitutions and late arrivals retain the domain's occurrence-time lineup rules. Corrections append new events and never delete the originals.

| Adapter | Durable records | Atomicity and reads |
| --- | --- | --- |
| SQLite | `matches` stores metadata, head and clock; `events` stores immutable JSON with unique match/sequence and match/event ID keys. | `BEGIN IMMEDIATE` commits event and head together; rollback preserves the previous state. Parameterized reads filter match and sequence and return sequence order. |
| Azure Tables | Existing `MatchEvents` table; `PartitionKey=match_id`, twelve-digit event `RowKey`; `!head` stores metadata, sequence and clock. | An entity-group transaction creates the event and conditionally replaces the header using its ETag. Reads use parameterized match/range filters and consume every SDK page. |

Reads beyond the current head return the currently committed prefix; API-level rejection of future requests remains task 5. No storage read returns a sequence above the requested cutoff. The Azure reader also checks that every committed sequence is present. Azure write failures read the event key and head to distinguish a lost success response from a failed transaction. Conflicting ETags without a committed matching event raise `ConcurrentWrite`; there is no blind write retry loop.

The table must already exist. The adapter accepts a caller-configured `TableClient`; credentials and resource provisioning belong to deployment. The SDK and resolved test dependencies are pinned in `requirements-core-dev.lock`; the library's optional `storage` extra installs `azure-data-tables==12.7.0`. Transaction and conditional-update behavior follows the [Microsoft TableClient API](https://learn.microsoft.com/en-us/python/api/azure-data-tables/azure.data.tables.tableclient?view=azure-python).

## Ingestion behavior and decisions

- `Ingestor.tick(match_id, available_second)` appends only the available event prefix and checkpoints the clock. It returns the count of new events. A tick can commit several events before a later append fails; committed events remain intact and the clock never claims the failed tick's target.
- `advance(match_id, elapsed_seconds)` uses a configurable rate, default 30x. The persisted integer clock also preserves empty gaps between events. Fractional progress is kept between steps in a running process; a restart may lose less than one match second of fractional scheduling time, never committed events.
- A failed writer exposes `failed`, the error class and its last confirmed durable position. It stays stopped until `resume` or a new writer instance validates the stored prefix against the replay source. It never exposes raw exception messages through its status. A restart at a partially committed availability second continues the remaining events at that second.
- The writer lock serializes calls within one instance. SQLite transactions and Azure ETags protect persistent history against competing calls, but this is not distributed leader election. The approved deployment remains one worker and one replica. No viewer action resets or rewinds this shared stream; viewer controls are a later task.
- Adding metadata registration and a durable clock to the original three storage methods is an implementation decision: it enables validation and restart during event-free intervals. Cost: a slightly larger internal storage interface.
- Work remains in the user's chosen folder on a new `codex/` branch. Only task 2 and its local inspection command are implemented. Cost: filesystem isolation is by convention; later app integration and live cloud validation remain necessary.

## Checks

Run `.\.venv\Scripts\python.exe -m pytest -q` after installing the development lockfile. Integration cases cover both adapters with the same contract, including duplicates, identity conflicts, gaps, invalid events, bounded reads, restart, independent writer instances, monotonic clocks and preservation of metadata. SQLite has a real transaction rollback test. Azure uses the actual SDK with a fake HTTP transport to exercise paginated queries, transaction serialization, ETags, service errors and a lost success response.

Ingestion tests cover the default rate, fractional time, restart in a gap, same-second partial failure, append/checkpoint/read failures, source conflicts, invalid clock inputs and completion at second 5400. A shot, goal and late annulment verify that two historical cutoffs retain distinct scores after ingestion advances. CLI tests reopen the same database between runs and inspect an earlier view.

The first storage test run failed because storage did not exist; the first ingestion/CLI runs failed for their missing modules. The read-position failure case reproduced a raw storage exception before the writer's failure handler; the handler now stops the stream and exposes its last confirmed position. A new score test initially expected a dictionary although the existing snapshot contract returns `TeamScore` tuples; its assertions were corrected without changing the domain contract.

Offline tests do not verify live Azure authentication, permissions, throttling, service latency or restart behavior of a deployed container. The fake transport is a narrow test double, not an Azure Storage emulator. Those checks remain a deployment prerequisite. Per-append full-prefix validation prioritizes correctness for the small synthetic matches; throughput for real feeds is unmeasured. End-to-end spoiler protection also requires the later API and browser tests.

Measured before independent review: 153 tests passed. A full main-scenario SQLite replay committed all 951 events through second 5400, reopened the database, matched the original event tuple and appended zero duplicates; the complete smoke took 32.321 seconds on this Windows workspace. This is an offline throughput observation, not a live-stream latency benchmark.

## Independent review and final recovery regressions

A fresh read-only reviewer independently ran the 153-test suite and found two Important recovery issues, with no Critical or Minor findings. Both were reproduced by five failing test cases before fixes:

1. A real SQLite reader lock could make COMMIT fail while leaving the writer's transaction open and exposing uncommitted progress. COMMIT now runs inside the rollback guard. The regression checks zero durable progress, no remaining transaction, and successful resume with the same adapter after the reader releases its lock.
2. A restart could claim completion or skip the realtime loop with only part of the target second committed. Completion now requires all source events, and realtime startup drains the current second before waiting for clock advancement. Both an ordinary second and second 5400 are covered; the final-second status test runs against both adapters.

All five regressions passed after the fixes. The final complete suite passes 158 tests from a newly installed development environment, including the installed CLI entry point and a successful dependency consistency check. The author verified the fixes with tests; no second independent review was performed.

Review boundaries were explicitly retained: live cloud conditions need deployment verification; HTTP/browser isolation and agent behavior belong to their later tasks; distributed ownership across replicas is not supplied; deliberate external database edits and physical-corruption repair have no recovery contract; larger/real-feed throughput is not established. These limits do not weaken validation of inputs through the delivered storage interface.
