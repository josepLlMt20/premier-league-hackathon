# Match Context Assistant

Work in progress for the Microsoft and Premier League **Inside the Game: Developer Hackathon**.

The planned application helps fans catch up on a missed part of a synthetic football match without revealing events beyond their playback position. A commentator mode will turn the same evidence into editorial briefings and short overlays. All teams, players and match events are fictional.

## Current status

- Product design and implementation plan documented.
- Local Microsoft Foundry connection verified with Microsoft Agent Framework, Azure sign-in, a local function tool and a Pydantic structured response.
- The match generator, application, three-agent workflow and Azure application deployment are **not implemented yet**.

The connection probe is a small infrastructure check, not a demonstration of the complete product or proof of its spoiler protection.

## Project documents

- [Product design](docs/superpowers/specs/2026-10-19-match-context-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-19-match-context-implementation.md)
- [Foundry setup and measured results](docs/readiness.md)
- [Original connection probe result, 20 October 2026](docs/evidence/2026-10-20-foundry-smoke.json)

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
