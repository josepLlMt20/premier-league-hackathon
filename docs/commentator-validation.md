# Professional commentator workflow — 24 October 2026

Touchline now has fan and professional audiences on one match workspace. Choose a received minute, select **Profesional**, choose the interval/preferences and request **Preparar briefing**. Changing audience preserves the committed minute and scoreboard, pauses playback and invalidates incompatible context. The latest received minute is an explicit action; reloading starts in fan mode and only persists preferences.

A verified result supplies up to three cards: headline, what changed, suggested commentary, observation/interpretation labels, cited figures, comparison intervals and limitations. **Ver evidencia** reuses the bounded snapshot drawer. **Copiar frase** includes every card limitation. Clipboard failures keep the text selectable and give a recovery message.

The selected overlay uses the engine's exact short text, limited to 140 Unicode code points, alongside full caveats and a synthetic-data marker. This is a local graphical preview with no broadcast connection. Briefing and overlay JSON include version, match, snapshot, cutoff, displayed second, captured score, language, provenance, intervals and references. Briefings include rendered claims and canonical cited facts. Raw claim templates are never presented as commentary. No current global scoreboard enters an old receipt's export.

Exports reject factual/insufficient results, fan receipts, missing/unknown stories, mismatched snapshots/cutoffs, invalid intervals/references and oversized overlays. Some discarded candidates do not prevent accepted cards from being exported. Factual fallback retains useful facts and evidence, explains the absence of editorial cards and disables editorial export. No browser text-generation fallback invents commentary.

## Verification

- 64 Vitest tests passed, including immutable export receipts, 140/141 Unicode code points, role cancellation/late responses, clipboard failure and missing-trace handling.
- 22 real HTTP/SQLite Playwright journeys passed across desktop 1440px and mobile 390px, including the existing fan journeys, actual downloaded JSON, fallback, language invalidation, clipboard/download failure, evidence focus return, 320px reflow and axe WCAG checks with no reported violations.
- TypeScript/production build and generated API contract check passed. Prettier check passed after normalizing local Windows line endings; unchanged files add no semantic diff.
- Backend production code is unchanged. Its pre-branch 255-passed/one opt-in live test skipped result is retained, not represented as a fresh backend run.

The browser suite uses `tests.e2e_server`, real ingestion/snapshots and explicitly programmed analyst/writer/reviewer responses. Captures visibly say **Prueba guiada · texto programado** and the trace reports zero model calls. These checks establish integration and receipt safety, not real Foundry language quality. Programmed descriptions intentionally repeat simple source facts; they are not a demonstration of polished AI commentary.

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

The UI was inspected in the in-app browser with its explicit scripted provenance. Better Design's exhausted quota was not retried; the approved Touchline system, local tokens/font/icons and actual browser evidence were used. This change adds no runtime dependency, new Azure resource, paid upgrade or new live provider request. Public deployment, real storage smoke and professional user research remain separate work.