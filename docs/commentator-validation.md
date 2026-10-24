# Professional commentator workflow — 24 October 2026

Touchline now has fan and professional audiences on one match workspace. Choose a received minute, select **Profesional**, choose the interval/preferences and request **Preparar briefing**. Changing audience preserves the committed minute and scoreboard, pauses playback and invalidates incompatible context. The latest received minute is an explicit action; reloading starts in fan mode and only persists preferences.

A verified result supplies up to three cards: headline, what changed, suggested commentary, observation/interpretation labels, cited figures, comparison intervals and limitations. **Ver evidencia** reuses the bounded snapshot drawer. **Copiar frase** includes every card limitation. Clipboard failures keep the text selectable and give a recovery message.

The selected overlay uses the engine's exact short text, limited to 140 Unicode code points, alongside full caveats and a synthetic-data marker. This is a local graphical preview with no broadcast connection. Briefing and overlay JSON include version, match, snapshot, cutoff, displayed second, captured score, language, provenance, intervals and references. Briefings include rendered claims and canonical cited facts. Raw claim templates are never presented as commentary. No current global scoreboard enters an old receipt's export.

Exports reject factual/insufficient results, fan receipts, missing/unknown stories, mismatched snapshots/cutoffs, invalid intervals/references and oversized overlays. Some discarded candidates do not prevent accepted cards from being exported. Factual fallback retains useful facts and evidence, explains the absence of editorial cards and disables editorial export. No browser text-generation fallback invents commentary.

## Verification

- 65 Vitest tests passed, including immutable export receipts, 140/141 Unicode code points, role cancellation/late responses, clipboard failure, missing-trace handling and removal of the duplicated locution aggregate above accepted cards.
- 22 real HTTP/SQLite Playwright journeys passed across desktop 1440px and mobile 390px, including the existing fan journeys, actual downloaded JSON, fallback, language invalidation, clipboard/download failure, evidence focus return, 320px reflow and axe WCAG checks with no reported violations.
- TypeScript/production build and generated API contract check passed. Prettier check passed after normalizing local Windows line endings; unchanged files add no semantic diff.
- 269 backend tests passed; one opt-in live test was skipped. The copy correction updates Foundry instructions and narrow publication checks, with14 editorial regressions covering distinct fields, labeled units, repair/fallback and not inferring shot volume from the quality index.

The browser suite uses `tests.e2e_server`, real ingestion/snapshots and explicitly programmed analyst/writer/reviewer responses. Captures visibly say **Prueba guiada · texto programado** and the trace reports zero model calls. The revised bilingual templates give distinct roles to headline, explanation, commentary and overlay. Shot stories lead with actual counts when they increase; the synthetic quality index is labeled in points as supporting detail. Territorial copy defines completed attacking-third passing share across both teams. These scripted checks do not establish live Foundry language quality.

Two separate professional samples were attempted against the existing Foundry deployment at25:00, in Spanish and English. Both returned factual fallback at the unchanged10-second deadline; the English attempt also recorded `free_number` during repair. No real editorial card was published. Seven model turns were attempted across the two samples; no additional retry or budget increase followed. [Measured report](evidence/commentator-2026-10-24/live-copy-probe.json). Live editorial quality and latency remain unresolved; the revised demo must not be presented as live-model output.

The main preview remains factual, with no Azure calls. An isolated guided preview can be run in separate terminals without changing it:

```powershell
.\.venv\Scripts\python.exe -m tests.e2e_server --port 8767
```

```powershell
cd web
$env:MATCH_CONTEXT_API = 'http://127.0.0.1:8767'
npm.cmd run dev -- --port 5175 --strictPort
```

Open `http://127.0.0.1:5175`, select 25:00 and request a professional briefing. This test-only launcher uses temporary SQLite state and cannot be deployed as the production backend. The normal launcher and explicit `AGENT_MODE=foundry` behavior remain as documented in README.

## Captures and limits

Real rendered captures: [desktop overview](evidence/commentator-2026-10-24/desktop-overview.png), [complete studio](evidence/commentator-2026-10-24/desktop-studio.png), [overlay](evidence/commentator-2026-10-24/desktop-overlay.png), [evidence](evidence/commentator-2026-10-24/desktop-evidence.png), [mobile](evidence/commentator-2026-10-24/mobile-studio.png) and [320px](evidence/commentator-2026-10-24/mobile-320.png).

The UI was inspected in the in-app browser with its explicit scripted provenance. Better Design's exhausted quota was not retried; the approved Touchline system, local tokens/font/icons and actual browser evidence were used. This change adds no runtime dependency, new Azure resource or paid upgrade. The two bounded live probes above consumed existing model quota; the main preview remains factual. Public deployment, real storage smoke and professional user research remain separate work.
## Independent branch review

One fresh reviewer examined `049c99d..6e7cdc1`, including cancellation, role isolation, receipt exports, references, Unicode limits, failures, provenance, accessibility markup and supplied desktop/320px captures. No actionable findings or deferred minors. The reviewer independently ran64/64 unit tests and `git diff --check`; browser/build evidence above was produced by the implementer. No second review or fix loop was needed.

Decisions and costs: changing audience preserves the historical minute (latest-head needs an explicit click); export helpers require a view/time receipt instead of an ID alone (callers need the extra captured context); audience selection stays in the shared Viewer (audience state remains coupled to playback); existing approved tokens/browser inspection replace the exhausted Better Design service (no fresh MCP audit). Review boundaries remain explicit: live Foundry prose, professional usefulness and cloud deployment need their own evaluation before claims of production readiness. Arbitrary malicious responses from a compromised backend are outside this trusted API review; that threat would require separate hardening.
