# Match Context Assistant

Work in progress for the Microsoft and Premier League **Inside the Game: Developer Hackathon**.

The planned application helps fans catch up on a missed part of a synthetic football match without revealing events beyond their playback position. A commentator mode will turn the same evidence into editorial briefings and short overlays. All teams, players and match events are fictional.

## Current status

- Product design and implementation plan documented.
- Local Microsoft Foundry connection verified with Microsoft Agent Framework, Azure sign-in, a local function tool and a Pydantic structured response.
- Four seeded 90-minute scenarios, immutable events, bounded snapshots, metrics, pattern detection and inspectable evidence are implemented with automated tests.
- Persistent SQLite event history and resumable ingestion are implemented. An Azure Tables adapter shares the same contract and is tested offline through the real SDK.
- The analyst/writer/reviewer workflow, scoped tools, claim validation and explicit factual fallback are implemented and tested offline, including the real Foundry SDK with a simulated transport. The new live agent smoke currently needs Azure reauthentication.
- The web application and Azure application deployment are **not implemented yet**. Live Azure storage verification is still pending.

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

## Run the match engine locally

Requires Python 3.13. No Azure account, credentials or model calls are needed for generation and analysis.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-agents-dev.lock
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

Add `--realtime --speed 30` to advance with wall time at 30 match seconds per real second; the default command advances immediately to the chosen point. The durable ingestion clock and the viewer's requested point are separate. Viewer playback controls will be implemented in the web application.

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

Requests are limited to seven model turns, eight requested tools, 1200 output tokens per model turn and a ten-second request deadline. Ordinary tests never call a model. The live test is a separate opt-in that consumes existing Azure quota:

```powershell
$env:RUN_FOUNDRY_LIVE = '1'
.\.venv\Scripts\python.exe -m pytest tests/live/test_foundry.py -m live -q -s
Remove-Item Env:RUN_FOUNDRY_LIVE
```

The full development environment is pinned in `requirements-agents-dev.lock`. `requirements-core-dev.lock` retains the smaller engine/storage environment; the full test suite now also needs the agent SDK dependencies. The historic connection-probe lockfile remains separate.

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
