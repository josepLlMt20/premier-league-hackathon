# Fan viewer: task 6

The React/Vite/TypeScript fan experience consumes the existing temporal API. It shows the score known at the selected minute, one recorded event on an SVG pitch, recent events, a missed-segment recap and optional supporting evidence. Spanish/English, simple/detailed output and favorite-team preferences feed the same backend context request.

The local product is runnable; deployment, professional briefings and evaluation with real users remain separate work. The current frontend tests use factual or explicitly scripted output. They do not establish new Foundry narrative quality, latency or cloud readiness.

## Reproduce

Install Python API development dependencies as described in the README. In `web/`:

```powershell
npm.cmd ci
npm.cmd test -- --run
npm.cmd run api:check
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e -- fan.spec.ts
```

Playwright starts a real loopback Uvicorn API with temporary SQLite, seeded synthetic events, independent ingestion and explicitly injected scripted agents. It owns ports 8765 and 5173 and refuses to reuse existing services. No Azure keys, sign-in or model calls are required. Set `E2E_PYTHON` to a Python executable if the repository `.venv` is elsewhere. Browser reports/screenshots/traces stay in ignored `tmp/ui-validation/`.

For manual use, start `match_context.server` in factual or explicitly configured Foundry mode on port 8000, then `npm.cmd run dev` in `web/`. `MATCH_CONTEXT_API` can select another development proxy target. The eventual static production server/container is task 8.

## Temporal behavior and decisions

- Start paused at zero; only static match metadata is preloaded. The shared head exposes received time without the current score. Every selected second resolves a cursor before fetching a bounded view. There is no fixture download, ingestion write route or full-match browser store.
- Seeking clears the old score, pitch, events, context and open evidence immediately. Both abort and local increasing request keys reject late cursor/view/context completions. Cached server trace IDs are never client request keys.
- Generating pauses local playback so the request refers to a stable missed segment. Seeking or changing language/detail/team/start invalidates it; changing a preference preserves the selected minute. Pause/speed do not mutate or stop shared ingestion.
- Evidence uses the immutable context snapshot and cutoff, loads on demand in batches of at most 100 requested IDs, validates snapshot identity and cancels/ignores late responses when closed. Source dependencies may legitimately include more events. Units, intervals, sample sizes and caveats remain visible. Escape/back returns focus and retains playback time.
- Only validated preferences go to localStorage. Storage failure/private mode is tolerated; neither match data, generated narrative nor playback cursor is persisted there. Reload starts at zero.
- API reads time out after 15 seconds and context requests after 30 seconds; these browser limits do not alter backend model budgets. A pending recap has cancellation and a slower-than-usual message after ten seconds. The backend's factual fallback is kept distinct from reviewed model narrative and guided scripted tests. No streamed partial text is produced by this API.

## Design and accessibility

[Design provenance and adaptations](../DESIGN.md). Actual Heyclicky Button/Card/Badge/Dialog/NativeSelect components are used; field geometry is data visualization. Inter is local, and all application icons are MingCute line. The primary gradient and small blue indices were darkened after contrast checks. A real scrollability failure in evidence was fixed with a named, focusable scroll region.

Checks include desktop and 390px mobile Chromium, 320px reflow, page/dialog axe scans, native keyboard time control, Escape and focus return, reduced motion, font loading, network request boundaries and preferences-only localStorage. Rendered spacing is captured at 390/1440/1728px. Text-comprehension checks cover the actual playback, catch-up and evidence navigation panels; they are heuristics, not user research.

No NVDA/VoiceOver session, Safari/Firefox run, load/latency study or real-user usefulness session has been performed. Those claims are intentionally absent.

## Verification record

- Full pinned Python suite: **255 passed, one opted-in live test skipped**, warnings as errors, 98.55 seconds. No Python production behavior changes in this branch.
- Vitest: **20 passed**. Includes delayed/out-of-order transport completions even after abort, cached trace reuse, rewind clearing, language/cursor preservation, focus return, cancellation, slow runs, head-poll serialization, timeout recovery and metric units.
- Real HTTP/SQLite Playwright suite: **six passed**, 40.3 seconds, covering desktop and 390px mobile. Page and open-dialog axe scans report zero violations under the selected WCAG A/AA tags. Spanish/English, evidence bounds, independent ingestion, native keyboard playback, 320px reflow and preference-only storage are checked.
- Build, dependency consistency, formatting, exported OpenAPI and generated immutable TypeScript drift checks pass. The original Windows CRLF-only schema check failure was reproduced, normalized bytes were identical, and generated-file LF checkout rules make regeneration/check reproducible.
- Better Design measured 390/1440/1728px: zero Critical/Serious geometry findings. Seven moderate heuristics concern intentional fluid auto margins, a 24px column gutter and full-width window borders with separate content padding; interpretation is recorded in `DESIGN.md`. This is not a claim of a perfect tool score or user-validated layout.
- Independent whole-branch review follows these checks; any findings/fixes are recorded below.

Rendered examples use the clearly labeled scripted test backend:

![Desktop fan view](evidence/fan-desktop.png)

[Mobile fan view](evidence/fan-mobile.png)

## Licenses

Heyclicky components and tokens were obtained through the user-selected [Better Design kit](https://better-design.com/design-systems/heyclicky). [MingCute source and Apache 2.0 license](https://github.com/mingcute-design/mingcute-icons/blob/main/LICENSE) and Inter's SIL Open Font License are copied to `web/public/licenses/` for distribution. npm package licenses remain with their dependencies. No real football assets are included.
