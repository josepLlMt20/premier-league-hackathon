# Foundry generation deadline — 24 October 2026

The ten-second ceiling belonged to this application, not to an Azure service restriction. It was enforced independently in Settings, AgentLimits, the inference HTTP/SDK client and the SDK function-invocation loop. Prior real Spanish/English requests exhausted it before the pipeline could reliably complete.

## Change

The generation cap/default is now 25 seconds, shared through `MAX_CONTEXT_SECONDS`. Environment setting `CONTEXT_TIMEOUT_SECONDS` can lower the total; values above 25, NaN and infinity are rejected. The API subtracts snapshot-read time from the remaining generation budget. SDK transport and function-loop caps no longer retain a hidden ten-second cutoff, while request-local cancellation still bounds all roles together. The CLI uses the same default.

The web still allows 30 seconds for context. Data reads remain capped at 10 seconds on the backend (or a shorter configured context limit), below the web's 15-second read timeout. Calls remain capped at 7, tools 8, output 1200 tokens per turn, one repair, two concurrent generations and no automatic HTTP retries. A longer allowed wait is not an increased model/tool/token budget, an exact real-time guarantee or unlimited waiting. Authentication/cold startup remains separate.

Real trials also exposed a semantic hole: an aggregate recovery count was being substituted into a spatial definition. Tests reproduced this with valid canonical references. Publication now rejects numeric fact markers used as coordinate values/inequality thresholds, and counts mislabeled as metre distances. Genuine canonical distance facts in metres remain allowed. Writer instructions describe high recoveries in plain attacking-third language, prohibit numeric definition thresholds, keep Spanish units/prose Spanish, and remind the reviewer that observed claims receive source caveats from code. This is targeted hardening, not a complete natural-language proof system.

## Verification

- 279 Python tests passed; one opt-in live test skipped. Deadline regressions first failed at the old ceiling; a simulated 12-second three-role run now completes without sleeping 12 seconds. SDK transport/function-loop cap checks, storage-read bounds, short-budget fallback, cancellation/slot cleanup, unchanged cost caps and the seven targeted grounding regressions pass.
- 66 web unit tests passed, including a fake-timer HTTP response arriving at 25 seconds within the existing 30-second deadline.
- 22 real HTTP/SQLite browser journeys passed, including the existing fan/professional playback, cancellation, exports, evidence, mobile/320px and accessibility journeys. These automated browser tests remain explicitly scripted and do not spend model quota.
- Production build, API contract check, formatting and diff checks pass. No new dependency or resource was created.

## Actual Foundry samples

[Machine-readable measured attempts](evidence/foundry-deadline-2026-10-24/live-results.json) retains all seven controlled probes, including failures and outputs excluded by manual inspection. Additional user-driven preview requests are not included in that diagnostic count. Provider usage is charged to the existing deployment; reported tokens may omit incomplete provider responses.

At 25:00, the latest real API samples after safeguards produced:

| Language | Agent time | Calls | Result |
| --- | ---: | ---: | --- |
| Spanish |8.31s |3 | One accepted card, no rejection codes. Explanation wording remains awkward; automatic acceptance is not human editorial approval. |
| English |16.25s |5 | One accepted card after repair; rejected candidate output is withheld. |

Observed HTTP totals were 8.39s and 16.35s respectively. The English result exceeds the previous ten-second ceiling and completes under the new budget. Earlier Spanish runs finished around 18–19 seconds but failed semantic review rather than timing out. A diagnostic Spanish run profiled the analyst/writer/reviewer stages; manually excluded spatial-definition mistakes informed the new guards. No negative observation is presented as an editorial success. These samples do not establish a success rate, tail-latency guarantee or professional usability.

## Try real text

The current isolated preview is `http://127.0.0.1:5176`, proxied to the real Foundry API on 8001. Select **Profesional**, choose a received minute and click **Preparar briefing**. Spanish/English are under **Personalizar**. **Cómo se preparó** displays actual model calls. A valid cached result can reuse the same trace without another model request; failed provider results are not cached. Explicit generation can consume quota when the request is not already cached.

The main preview 5173/API8000 stays factual, and 5175/API8767 stays explicitly scripted. They do not silently change provider. Real preview startup can be reproduced with the existing Azure login and `.env` deployment:

```powershell
$env:AGENT_MODE = 'foundry'
$env:CONTEXT_TIMEOUT_SECONDS = '25'
.\.venv\Scripts\python.exe -m match_context.server --database tmp/foundry-real-preview.sqlite3 --initial-second 1800 --speed 1 --port 8001
```

```powershell
cd web
$env:MATCH_CONTEXT_API = 'http://127.0.0.1:8001'
npm.cmd run dev -- --port 5176 --strictPort
```

The in-app browser was inspected without altering the user's ongoing test. Its real generated Spanish result at 26:07 showed the **Narrativa IA · revisada** label, a distinct explanation/locution and enabled exports. [Actual preview capture](evidence/foundry-deadline-2026-10-24/real-preview-es.jpg). Screenshot content and timing samples are separate observed requests; no scripted text is represented as Foundry output.