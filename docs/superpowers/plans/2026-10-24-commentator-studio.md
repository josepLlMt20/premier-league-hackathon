# Commentator studio implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user approved proceeding with professional briefings and overlays after PR #5. Keep the approved Touchline visual system.

**Goal:** Deliver the professional audience workflow on the same bounded match/evidence engine, with validated briefing and overlay exports.

**Architecture:** The existing Viewer remains the shared match workspace and owns a role in its reducer, so switching audience preserves the match and committed second while invalidating incompatible context. Shared context controls feed separate fan and commentator results. Pure export helpers consume a result plus its immutable view/clock receipt; no current global score or text-generation logic enters exports.

**Tech Stack:** Existing React/TypeScript/Vite, Base UI, MingCute icons, native CSS, Vitest and real HTTP/SQLite Playwright. No new runtime dependency or backend API change.

**Spec:** `docs/superpowers/specs/2026-10-19-match-context-design.md`, section3 and accepted Task7 in `docs/superpowers/plans/2026-10-19-match-context-implementation.md`.

## Global constraints

- Current folder, branch `codex/commentator-studio`, new tested GitHub PR; do not merge without further user instruction.
- Preserve bounded reads, request-key/abort protection, atomic automatic playback, explicit-generation receipt retirement, evidence focus/scroll and truthful factual/scripted/Foundry provenance.
- Keep a selected historical minute when changing audience. Latest received time remains an explicit action to avoid surprising fan spoilers. This refines the professional default while preserving the spec's latest-head capability.
- Export only accepted verified cards (scripted tests remain explicitly labeled), at most3, with overlay text at most140 Unicode code points. Never truncate validated meaning or drop limitations.
- Factual/insufficient results retain their facts/evidence but cannot become editorial exports. Rejected/unknown stories cannot be selected for export.
- Export snapshot, cutoff, selected time, score, intervals, claim classes, references and limitations from one receipt. No prompts or private chain of thought.
- Preserve current serious design tokens/font/identity, keyboard controls,44px targets,390px/mobile and320px reflow, reduced motion.
- Better Design's previously exhausted quota is not retried. Reuse approved Touchline and stored guidance; verify through rendered browser evidence.

## Review focus

- A role change or seek during generation must not restore an old role's context or export controls.
- A stale/mismatched frame, missing reference, unknown story or malformed overlay must be blocked from export.
- JSON/clipboard exports must retain interpretation limits and exact old snapshot score, with Unicode-safe140-character checks.
- Clipboard/download failure must leave a usable, truthful interface; zero-card and factual modes must be understandable.
- Agent trace uses only supplied roles/decisions/counts; scripted/factual operation cannot imply real provider calls.

## Task 1: Professional receipt and export contracts

**Files:** new `web/src/features/commentator/export.ts`, `export.test.ts`, test fixture; modify `web/src/domain/playback.ts`, its tests and Viewer role routing.

**Interfaces:** `Audience = 'fan' | 'commentator'`; role action preserves selected second/view and cancels pending steps while clearing old context/evidence and incrementing requestKey. `ContextFrame = {result: ContextResult; view: MatchView; second: number}`. `exportBriefing(frame): Blob`; `overlayFor(frame, storyId): OverlayPayload`; `canExportBriefing(frame): boolean`. These stronger helper inputs replace the sketch signatures that lacked a way to validate cutoff or include the captured score/time.

- [ ] Write failing tests for role/cached-response isolation, old snapshot exports, unknown/rejected stories, factual status, Unicode limits and context/frame mismatch. Run focused tests; expected failure before implementation.
- [ ] Implement pure receipt-bound validation/serialization and audience transitions. Preserve known reference intervals; use only rendered card strings, not raw claim templates.
- [ ] Run focused tests and build; expected green. Commit tested contracts.

## Task 2: Professional workspace and shared controls

**Files:** shared `ContextControls.tsx`/presentation formatter; new `Commentator.tsx`, `BriefingCard.tsx`, `OverlayPreview.tsx`, `TracePanel.tsx`, bilingual copy/tests; Viewer, CatchUpPanel, EvidencePanel, styling.

**Interfaces:** Existing context callbacks and evidence panel reused. Shared controls accept optional audience action labels. Commentator consumes current `PlaybackState`, metadata and the same generation/evidence callbacks. The audience selector lives inside the shared Viewer rather than replacing it in App, preserving one reducer and match identity.

- [ ] Write/run failing UI tests: audience switch preserves cursor and dispatches commentator role; old fan generation ignored; professional cards, intervals, claim kinds, evidence and export state; factual/empty results; clipboard failures.
- [ ] Implement up to3 briefing cards, selected overlay preview, copy locution with limitations, JSON briefing/overlay download, safe structured trace and shared preferences/interval/generation controls.
- [ ] Apply existing Touchline tokens and finite motion; preserve the fan UI, playback and accessible evidence behavior. Run unit/build/types/format; expected green.

## Task 3: Browser verification and delivery

**Files:** `web/e2e/commentator.spec.ts`, professional validation docs and real captures; update README/design records.

- [ ] Test actual HTTP/SQLite flow in explicit scripted mode: both roles share selected match/time and evidence, serialized exports retain cutoffs/score, switching role invalidates old output, rejected/factual exports unavailable, trace truthful, desktop/mobile axe/reflow/keyboard.
- [ ] Inspect actual in-app browser and capture desktop/mobile/professional overlay/evidence. Use clearly labeled scripted preview for accepted cards; retain the factual preview without silently enabling Azure calls.
- [ ] Run full frontend suite plus existing fan journeys; record results. Backend production unchanged; retain its freshly verified255-test baseline unless new backend changes justify rerun.
- [ ] Obtain one independent whole-branch review; fix material findings in one regression-tested pass. Commit/push and create/attach the PR; show real captures, keep preview available, do not merge.
