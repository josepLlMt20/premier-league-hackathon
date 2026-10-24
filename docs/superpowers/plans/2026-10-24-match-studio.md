# Match studio implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user approved implementation of the selected Estudio de partido visual and motion; do not restart ideation or request another approval.

**Goal:** Implement the approved professional match studio and show real desktop/mobile captures.

**Architecture:** Keep the existing reducer, bounded HTTP reads and immutable evidence flow. Recompose the existing React components and design tokens, introduce a result-bound shot comparison, and adapt the existing Base UI dialog into a responsive evidence drawer.

**Tech Stack:** React, TypeScript, Vite, Base UI, native CSS/SVG data visualization, Vitest and existing Playwright HTTP/SQLite journeys.

**Spec:** `docs/design-explorations/2026-10-24/estudio-de-partido.md`; visual truth `05-estudio-de-partido.png` in the same folder, approved by the user on 24 October. The user additionally rejects the old name/logo; new visible branding is provisional pending preference feedback.

## Global constraints

- Stay in the current feature branch/folder and update PR #5; no worktree or merge.
- No backend, schema, storage, ingestion, model budgets or Azure provisioning changes.
- Preserve abort/request-key invalidation, availability-time navigation, keyboard focus, factual/scripted/reviewed disclosures and preferences-only storage.
- Clear stale data immediately on seeks; no animated outgoing snapshots or count-up scores.
- Keep generated media local and existing licensed MingCute icons. Field geometry remains real SVG data visualization.
- Finite event cue 450 ms; recap 220 ms; drawer 240 ms; press/selection 150 ms; reduced motion disables all transitions.

## Review focus

- A comparison must use the context's exact interval, snapshot and cutoff, never full-view or earlier-window facts.
- Missing, null, negative, non-finite, duplicate or mismatched shot facts must not produce a misleading chart.
- A control seek or preference change must immediately clear old context, chart, pitch event and drawer even during transitions.
- Timeline shortcuts use availability time, preserve chronology and return focus to the stable native time control.
- The drawer retains scrollability, focus trapping, Escape/return, narrow-screen reflow and reduced-motion behavior.

## Task 1: Match studio and provisional identity

**Files:** `web/src/App.tsx`, `web/src/features/viewer/{Viewer,PlaybackControls,CatchUpPanel,EvidencePanel}.tsx`, `web/src/components/{Scoreboard,Pitch,Timeline}.tsx`, new `ShotComparison.tsx` and tests, `web/src/styles/{tokens,app}.css`, shared UI primitives, `web/index.html`, local brand/font assets, browser regression tests, design/validation docs and captures.

**Interfaces:** Existing props and API types remain compatible. `ShotComparison` consumes only `ContextResult`, `MatchMetadata`, language; it validates exactly one shots fact per team sharing the context snapshot/cutoff and matching intervals before rendering.

- [x] Write/run failing focused tests for result-bound shot comparison, missing/zero/mismatched facts, and chronological shortcut selection.
- [x] Implement the compact scoreboard, replay stage/anchored label, integrated transport, chronological actions and compact contextual panel. Keep a single native time slider and existing labels.
- [x] Implement the validated comparison and evidence drawer; add a provisional custom brand without the generic football logo.
- [x] Run unit suite/build/types/format; inspect the actual browser against the mock at the same minute and viewport, plus narrow screens.
- [x] Extend/run browser checks for drawer enter/reduced-motion behavior and immediate stale-data removal. Preserve existing real HTTP/SQLite checks.
- [x] Fix observed issues, capture real factual desktop/mobile/evidence/preferences states, and save `design-qa.md` with comparison findings.
- [x] Obtain one independent review of this delivery; address material findings in one regression-tested fix pass.
- [ ] Commit/push the verified update to PR #5; return accessible image links. Do not merge.

**Expected checks:** unit tests pass, build/types/format pass, real HTTP browser suite passes, no actionable P0/P1/P2 visual findings. Existing unchanged Python suite remains prior evidence; no new cloud/model quality claims.
