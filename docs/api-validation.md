# Temporal context API

Scope: task 5 of the approved plan, with typed server configuration and pinned API/type-generation dependencies as minimal task 0 prerequisites. The API consumes the merged generator, immutable event log, analysis engine and guarded agents. It does not add the fan/commentator UI, deployment, cloud provisioning, authentication accounts or production load guarantees.

## HTTP contracts

| Route | Result and temporal boundary |
| --- | --- |
| `GET /healthz` | Liveness only, independent of storage/model readiness. |
| `GET /api/matches` | Registered static metadata only. No source fixture, outcome, event stream or ingestion clock. |
| `GET /api/matches/{id}/head` | Committed sequence, ingestion availability clock and scheduler state; no score. |
| `GET /api/matches/{id}/cursor?available_second=S` | Greatest sequence available through S within one captured committed head. Reject S beyond the captured ingestion clock. Returns zero before the first event. |
| `GET /api/matches/{id}/view?to_sequence=N` | Reconstructed score, metrics, annulments and at most 100 recent events through N. No events after N are loaded into the snapshot. |
| `POST /api/context` | `ContextRequest` interval/preferences; returns the original request identity, snapshot, mode, status, cards, facts, evidence references and safe aggregate trace. |
| `POST /api/evidence` | Match, `to_sequence`, up to 100 event IDs. Known dependencies/corrections are resolved within that same snapshot; unknown, other-match and later references are unavailable. Dependency closure can exceed the number of requested IDs. |

Sequences are ordered by availability, not occurrence time. Snapshot reconstruction uses only `EventLog.read_through`, after validating N against the durable head; clients cannot supply snapshots, facts, fixtures or provider settings. A late correction affects only prefixes containing its arrival. Cursor reads can address positions older than the recent-event tail. During a partially committed same-second ingestion batch, the captured head defines the visible prefix; re-querying can return newly committed events from that same second.

All public response models are explicit. HTTP body validation does not echo raw inputs or exception contexts. Stable errors are `invalid_request` (422), `invalid_cutoff` (422), `future_cutoff` (422), `future_time` (422), `unknown_favorite` (422), `unknown_evidence` (422), `match_not_found` (404), `storage_timeout` / `storage_unavailable` (503), and `generation_busy` (429, `Retry-After: 1`). A disconnected context client produces an internal 499 `client_disconnected` response, normally with no recipient. Match paths and evidence IDs are validated before querying. HTTP responses use `Cache-Control: no-store` so shared browser/proxy caches do not substitute a later response.

The cutoff is an explicit request contract, not an authenticated playback session. The future web client must choose the correct cutoff, cancel stale work and compare its local request key before rendering. Reversed HTTP completion preserves each result's request/snapshot identity; this API alone does not implement browser stale-response handling or localStorage rules.

## Context coordination and caching

Each `ContextService` owns one in-memory LRU of at most 128 immutable results. Its hash key includes match, from/to sequence, role, language, depth, favorite team and the canonical prefix hash (which includes metadata). No earlier/later snapshot or preference can reuse a different key. A service restart starts with an empty cache and reconstructs snapshots from durable history. Exact repeated verified requests and intentional factual-mode requests can reuse a cached result, including its trace ID; browser request identity must remain a separate local counter.

Transient agent/provider fallback is not cached. Missing Foundry startup returns explicit `mode=factual` with `provider_unavailable`, and valid data reads still work. At most two uncached agent generations run concurrently per service/process; excess requests receive 429 without queuing. Cached results and data queries do not consume model slots. Identical simultaneous misses are not coalesced and can occupy both slots; cost is bounded by admission limits rather than deduplication.

Synchronous storage reads/reconstruction and ingestion work run in worker threads. No lazy SDK iterator escapes back to the event loop. Context storage time is subtracted from the remaining generation deadline; the existing seven-model/eight-tool/1200-output/ten-second maxima cannot be increased through settings. After body validation, the context route watches ASGI disconnects, cancels abandoned generation and awaits cleanup before ending its lifecycle. A normal completed request cancels its disconnect watcher. Cancellation and exceptions release generation slots without caching partial output. This stops local work; already incurred remote provider usage is not refunded or guaranteed to stop immediately. A cancelled/timeout storage call may finish in its worker; storage SDK/OS timeouts still matter operationally. This is not a hard real-time system.

## Runtime and ownership

`create_app(settings, log, runner)` does not generate fixtures, open storage or authenticate. Its caller owns injected resources. Both SQLite and Azure Tables implement static `list_matches`; the latter queries header metadata through the real paginated SDK. This extends the EventLog interface: other adapters must implement enumeration.

The local `match-serve` launcher owns one SQLite log, one private seeded source, one scheduler and optional existing Foundry client. Startup may ingest through `--initial-second`; subsequent advancement uses wall time and persisted position at configurable speed. There is no HTTP write/tick/rewind endpoint. Shutdown signals the scheduler, waits for its worker before closing storage and closes provider resources. Restart validates the source against immutable history and resumes. An ingestion failure marks its state failed at the last committed point; it is not silently resumed. Other registered matches can be listed/read but are marked `external` unless this launcher owns their scheduler.

Factual mode is the default and needs no Azure credentials. Foundry mode is explicit and reuses the existing local Azure CLI identity. Explicit Settings endpoint/model values are passed to the provider, rather than accidentally using different `.env` values. If provider startup fails, the local server serves factual context; repair authentication and restart to construct the missing runner. An already constructed runner can recover on later calls after a transient provider error. Scripted mode requires development/test plus an explicitly injected runner; the local CLI deliberately does not fabricate a model. Cloud storage/managed-identity construction and production deployment remain later work. Use one process/worker/replica for this ownership model.

## Reproduce

From the repository root, Python 3.13:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-api-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q -W error
$env:AGENT_MODE = 'factual'
.\.venv\Scripts\match-serve.exe --database tmp/api-demo.sqlite3 --initial-second 1200
```

Read `/api/matches` for the generated ID, resolve a cursor, then request its view/context. Stop the server before reusing that port; reuse the database for resume or a different filename for a fresh stream. The full Python lock includes the unchanged agent/storage pins. API versions verified together: FastAPI 0.149.0, Starlette 1.9.0, Uvicorn 0.54.0, Pydantic 2.14.1. Node tools are locked independently in `web/package-lock.json` with openapi-typescript 7.13.0.

Export public OpenAPI using `python scripts/export_openapi.py`; `--check` detects drift. From `web`, `npm.cmd ci --ignore-scripts`, `npm.cmd run api:types` and `npm.cmd run api:check` generate/check immutable TypeScript declarations. This scaffolds contracts only, not React or a visual application. Patterns follow [FastAPI async testing](https://fastapi.tiangolo.com/advanced/async-tests/), [lifespan ownership](https://fastapi.tiangolo.com/advanced/events/) and the [openapi-typescript CLI](https://openapi-ts.dev/cli).

## Verification before independent review

- Config/cache/catalog regressions first failed for missing modules/methods; HTTP tests first failed for the missing API. Runtime tests first failed for the missing launcher, then demonstrated a synchronous status read on the event loop before that call was moved to a worker. Explicit Foundry endpoint override failed before the optional provider arguments were added. Each now passes.
- In a newly created isolated environment installed only from the lock plus editable project: **253 passed, one explicitly opted-in live test skipped**, warnings treated as errors, in 86.36 seconds. Dependency consistency and installed `match-serve --help` passed.
- HTTP tests cover future rejection, early/empty context, unknown favorites, evidence bounds, old cursors outside the 100-event tail, simultaneous arrivals, late corrections, two viewers completing out of order, two-slot saturation with independent data reads, provider fallback/recovery, cancellation cleanup and error sanitization. Catalog tests use six matches through both adapters, exercising real-SDK offline pagination.
- OpenAPI export/check and TypeScript generation/check passed. These commands neither start ingestion nor authenticate to Azure.
- A real local Uvicorn process in factual mode returned successful health/catalog/view/context responses, bounded a cursor at second 900 while ingestion was at second 3067, reused the exact context cache result, and rejected later evidence and a future cursor with 422. Ctrl+C completed application shutdown; reopening SQLite retained position sequence 606 / second 3429. [Recorded smoke](evidence/2026-10-24-api-http-smoke.json). No model calls or Azure resource changes were made by this delivery's validation.

Prior Foundry smoke results remain evidence of the merged agent delivery, not a new real model run through this API. Semantic/narrative stability, professional-generation success within ten seconds, browser race protection, actual Azure storage/identity behavior, deployment and user studies remain separate checks.

## Independent review and fix pass

A fresh read-only review of `3053a13..0c16c13` independently passed all 253 then-existing tests with warnings as errors, dependency consistency and schema/type drift checks. It found no Critical or Minor issues and one Important lifecycle error: closing a real client TCP connection did not cancel generation under the pinned Uvicorn/Starlette stack. With a one-slot test configuration the abandoned runner remained active and a replacement request received 429. The original direct service-cancellation test did not cover that HTTP boundary.

An ASGI disconnect regression reproduced the missing cancellation (timeout waiting for the runner's cancellation). The context route now watches disconnects concurrently with generation, cancels pending tasks and awaits provider/slot cleanup. That regression passes, and an additional real localhost Uvicorn test closes a TCP connection, observes runner cancellation and empty partial-result cache, then completes a replacement request with HTTP 200. Slot-saturation, out-of-order completion, direct cancellation and deadline controls remain green. No second independent review is performed; regression tests verify this single fix pass.

Review boundaries retained: browser rendering/request-key/localStorage is task 6; actual Azure identity/storage and deployment are task 8; distributed admission and multiple workers are outside the one-process model; deliberate access to already-ingested later cutoffs is outside the public synthetic playback contract; general semantic reliability and detailed-profile latency remain agent limits; duplicate concurrent misses/cache trace reuse remain explicit design choices; hard cancellation of blocking storage threads remains an SDK/OS limitation. No review findings are deferred.

Final fix verification in the isolated pinned environment: **255 passed, one opted-in live test skipped**, warnings treated as errors, in 93.62 seconds. Dependency consistency, OpenAPI export/check and TypeScript generation/check passed after the fix. No new Azure model calls or resource changes were made.
