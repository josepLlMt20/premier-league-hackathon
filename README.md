# Match Context Assistant

Work in progress for the Microsoft and Premier League **Inside the Game: Developer Hackathon**.

The application helps fans catch up on a missed part of a synthetic football match without revealing events beyond their playback position. A commentator mode turns the same evidence into editorial briefings and short overlays. All teams, players and match events are fictional.

## Current status

- Product design and implementation plan documented.
- Local Microsoft Foundry connection verified with Microsoft Agent Framework, Azure sign-in, a local function tool and a Pydantic structured response.
- Four seeded 90-minute scenarios, immutable events, bounded snapshots, metrics, pattern detection and inspectable evidence are implemented with automated tests.
- Persistent SQLite event history and resumable ingestion are implemented. An Azure Tables adapter shares the same contract and is tested offline through the real SDK.
- The analyst/writer/reviewer workflow, scoped tools, claim validation and explicit factual fallback are implemented and tested offline, including the real Foundry SDK with a simulated transport. The live bilingual Foundry smoke has also passed; measured results and limitations are in [agent validation](docs/agents-validation.md).
- The temporal HTTP API, bounded views/evidence, isolated context cache and two-generation admission limit are implemented. A local single-process server runs an independent resumable ingestion scheduler.
- The first fan web experience is implemented: bounded playback, Spanish/English catch-up, favorite team/detail preferences and inspectable evidence. The approved Touchline studio includes stable automatic playback, a result-bound shot comparison and a responsive evidence drawer. Touchline is the provisional English identity. [Web usage and validation](docs/web-validation.md).
- Professional briefings, commentary copy with caveats, local overlay previews and receipt-bound JSON exports are implemented. Changing audience preserves the selected minute. [Professional workflow and validation](docs/commentator-validation.md).
- Azure application deployment, live Azure storage verification and user studies remain pending. The professional UI has been verified with explicitly programmed agents; its live Foundry editorial quality still requires evaluation.

The connection probe is a small infrastructure check, not a demonstration of the complete product or proof of its spoiler protection.

## Project documents

- [Product design](docs/superpowers/specs/2026-10-19-match-context-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-19-match-context-implementation.md)
- [Foundry setup and measured results](docs/readiness.md)
- [Original connection probe result, 20 October 2026](docs/evidence/2026-10-20-foundry-smoke.json)
- [Synthetic data and measurement definitions](docs/data-dictionary.md)
- [Engine tests, independent review and implementation decisions](docs/engine-validation.md)
- [Persistent ingestion: usage, tests and limits](docs/ingestion-validation.md)
- [Agent workflow, validation and Foundry smoke status](docs/agents-validation.md)
- [API usage, contracts, verification and limits](docs/api-validation.md)
- [Fan web experience, running instructions and verification](docs/web-validation.md)
- [Professional briefing/overlay workflow and verification](docs/commentator-validation.md)

## Open the fan experience locally

After the Python installation below, start the API in one terminal. Factual mode makes no model calls:

```powershell
$env:AGENT_MODE = 'factual'
.\.venv\Scripts\python.exe -m match_context.server --database tmp/viewer.sqlite3 --initial-second 1500 --speed 1
```

In a second terminal (Node 22.23.1 or compatible):

```powershell
cd web
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Playback starts paused at zero. Choose a minute, or **Ir al último minuto recibido**, then **Ponerme al día**. Only preferences survive a reload. To use the existing Foundry deployment, explicitly set `AGENT_MODE=foundry` before starting the backend; existing Azure identity/configuration is required and generation consumes model quota. Factual fallback remains visibly labeled.

Select **Profesional**, then **Preparar briefing** for the editorial workflow. Factual mode retains facts and evidence but disables editorial exports. With verified cards, you can inspect their evidence, copy commentary with its limitations, preview a short overlay and download its JSON or the complete briefing. The preview has no connection to a broadcast system.

## Run the match engine locally

Requires Python 3.13. No Azure account, credentials or model calls are needed for generation and analysis.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-api-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m match_context --scenario main --until-second 1500
```

The command prints JSON with the score as known at the selected point, numeric facts, comparison windows, up to three distinct pattern candidates and event references. Add `--include-evidence` to expand the referenced raw events. Use `--from-second`, `--seed` or `--favorite-team amber|cobalt` to change the request.

Try the neutral and sterile scenarios, then compare a correction before and after it becomes available:

```powershell
.\.venv\Scripts\python.exe -m match_context --scenario neutral --until-second 1500
.\.venv\Scripts\python.exe -m match_context --scenario sterile --until-second 1500
.\.venv\Scripts\python.exe -m match_context --scenario correction --until-second 1500
.\.venv\Scripts\python.exe -m match_context --scenario correction --until-second 1600
```

The correction example retains the 1–0 score at second 1500 and reports 0–0 after the annulment becomes available at second 1565. The displayed clock is the last received event's availability time, which can be earlier than the requested second. Empty samples do not invent trends or turn undefined percentages into zero. Shot quality is a simulator heuristic, not calibrated xG.

## Replay a match into persistent storage

After the local installation above, these commands use the same SQLite file across separate processes:

```powershell
.\.venv\Scripts\python.exe -m match_context.ingest_cli --database tmp/demo.sqlite3 --scenario correction --until-second 1500
.\.venv\Scripts\python.exe -m match_context.ingest_cli --database tmp/demo.sqlite3 --scenario correction --until-second 1600
.\.venv\Scripts\python.exe -m match_context.ingest_cli --database tmp/demo.sqlite3 --scenario correction --until-second 1600 --view-second 1500
```

The first score is 1–0, the second is 0–0 after the correction, and the third view still reports the earlier 1–0. Repeating a command adds no duplicate events. Ingestion cannot rewind; use `--view-second` to inspect earlier history, or choose a new database for a fresh shared stream.

Add `--realtime --speed 30` to advance with wall time at 30 match seconds per real second; the default command advances immediately to the chosen point. The durable ingestion clock and the viewer's requested point are separate. Web playback controls only change the viewer's position.

The development lockfile includes the Azure SDK for offline adapter tests. SQLite itself uses Python's standard library. To install just the library with the Azure adapter, use `pip install -e '.[storage]'`; an existing `MatchEvents` table and a configured `TableClient` are required for live use. These commands create no Azure resources and make no model calls.

## Inspect agent context

The default command produces an explicitly identified, bilingual factual summary without model calls:

```powershell
.\.venv\Scripts\python.exe -m match_context.agent_cli --until-second 1500 --language es
```

After Azure sign-in and configuring the existing `.env` endpoint and deployment, use `--mode foundry` to make real model requests:

```powershell
.\.venv\Scripts\python.exe -m match_context.agent_cli --mode foundry --until-second 1500 --language es --depth simple
.\.venv\Scripts\python.exe -m match_context.agent_cli --mode foundry --until-second 1500 --role commentator --language en
```

The output distinguishes `mode=foundry` from `mode=factual`, and `status=verified` from fallback or insufficient observations. It includes the request cutoff, accepted cards, resolved text, rejection codes and a concise usage trace. `--include-facts` includes the complete canonical fact registry. A failed local connection returns `foundry_startup_failed`; an in-request provider failure returns identified factual output.

Requests are limited to seven model turns, eight tool executions (including candidate prefetch), 1200 output tokens per model turn and a 25-second request deadline. `CONTEXT_TIMEOUT_SECONDS` may lower that deadline; values above 25 are rejected. The web context timeout remains 30 seconds, and storage reads retain their 10-second cap. The application retrieves candidates before the analyst's model call; the analyst, writer and reviewer still run separately. Compact internal references are restored to canonical evidence before validation. [Deadline fix and real professional measurements](docs/foundry-deadline-validation.md). Ordinary tests never call a model. The live test is a separate opt-in that consumes existing Azure quota:

```powershell
$env:RUN_FOUNDRY_LIVE = '1'
.\.venv\Scripts\python.exe -m pytest tests/live/test_foundry.py -m live -q -s
Remove-Item Env:RUN_FOUNDRY_LIVE
```

The full backend development environment is pinned in `requirements-api-dev.lock`, including the unchanged agent/storage pins from `requirements-agents-dev.lock`. `requirements-core-dev.lock` retains the smaller engine/storage environment. The historic connection-probe lockfile remains separate.

## Run the local API

After installing the full backend environment above:

```powershell
$env:AGENT_MODE = 'factual'
.\.venv\Scripts\python.exe -m match_context.server --database tmp/api-demo.sqlite3 --initial-second 1200
```

Open [the API documentation](http://127.0.0.1:8000/docs). The initial-second option ingests through that point before accepting requests; afterward one scheduler advances at 30 match seconds per wall second. Browsing, seeking and requesting context do not control ingestion. Ctrl+C shuts down the scheduler and preserves committed history. Restarting the same database resumes its monotonic clock; use a different file for a fresh stream.

The default factual mode makes no model requests. To use the existing Foundry deployment, explicitly set `AGENT_MODE=foundry`, configure the `.env` project endpoint/model and sign in to Azure CLI. Provider startup failure leaves match reads and identified factual context available; retry startup after repairing authentication. `/healthz` is liveness only. The local launcher supports SQLite; `create_app` also accepts an existing Azure Tables adapter and an explicitly owned runner. No resources are provisioned.

Public routes: `/api/matches`, per-match `/head`, `/cursor?available_second=…`, `/view?to_sequence=…`, and `POST /api/context` / `POST /api/evidence`. Error responses carry stable `error.code` values; generation saturation returns HTTP 429 with `Retry-After: 1`. All responses use `Cache-Control: no-store`; the bounded server-side context cache remains independent.

Export and check the API schema without starting a server or contacting Azure:

```powershell
.\.venv\Scripts\python.exe scripts/export_openapi.py
.\.venv\Scripts\python.exe scripts/export_openapi.py --check
cd web
npm.cmd ci --ignore-scripts
npm.cmd run api:types
npm.cmd run api:check
```

The generated `web/openapi.json` and `web/src/api/schema.d.ts` prepare the future web client. There is no frontend application yet.

## Run the connection probe

Requirements: Python 3.13, [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows), a Foundry project, a deployed model and access to call it. The dependencies below reproduce the Windows Python environment used for the original probe.

From the repository root, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-foundry-probe.txt
Copy-Item .env.example .env
```

Set your project endpoint and model deployment name in `.env`. If `.env` already exists, keep it and edit the required values instead of copying over it.

Sign in with the account that has access to your Foundry resource, then run the probe:

```powershell
az login
.\.venv\Scripts\python.exe scripts/check_foundry_connection.py
```

The probe makes real model requests and consumes Azure credit or paid quota. It disables HTTP retries, limits tool calls and output tokens, and has a 45-second overall timeout. No web search or hosted tools are enabled. These limits are not a monetary spending cap.

Success prints `status: passed`, one local tool invocation, the measured duration and SDK-reported token usage. It validates one shot, zero goals and evidence `e1`, `e2` at cutoff 2; a synthetic goal at sequence 3 is excluded from the tool output. The latest local report is written to `tmp/foundry-connection/smoke-result.json`.

The original setup also has a portable Azure CLI in `tmp/foundry-connection/azure-cli/bin`; the script uses it if present. A fresh clone can use a normal Azure CLI installation on PATH. SDK dependencies are pinned in `requirements-foundry-probe.txt`; these are probe dependencies, not the future application's dependency lockfiles.

## Repository contents

Source, documentation, dependency versions and the original non-sensitive result are tracked in Git. Local `.env` files, Azure authentication caches, virtual environments, downloaded tools and temporary output are excluded. Recreate those from these instructions when moving to another computer; authenticate again rather than copying credentials.
