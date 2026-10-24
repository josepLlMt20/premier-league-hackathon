# Match studio design QA

## Latest user-directed correction

The user rejected floating field labels and reported page-like flicker every second. The labels are now removed on all widths; the full event caption remains below the pitch. Automatic playback retains the committed frame until its next bounded read completes, then updates clock and data together. Explicit seeks still clear immediately. Fresh actual captures are in `docs/evidence/playback-2026-10-24/`, including `06-campo.png`. The field capture was opened and inspected: no text overlays or layout changes remain on the pitch. The previous label design and corrections below are historical.

Latest checks:44 unit and14 real HTTP/browser tests pass, with stable score/pitch/sequence DOM during1200ms reads, cancellation-safe recap generation, normal/reduced motion, desktop/mobile accessibility and320px reflow. Build/types/format pass; factual captures have zero model calls and no console/page errors. The selected visual direction and all other modules remain unchanged. **final result: passed** for this correction.

**Source visual truth:** `docs/design-explorations/2026-10-24/05-estudio-de-partido.png` (1435×1096 pixels).
**Implementation:** `docs/evidence/studio-2026-10-24/01-escritorio.png` (1440×1335 full page); CSS viewport1440×1100, device density1. Reference normalized by width1440/1435 for comparison; its vertical composition is a schematic target, not a mandate to distort metric pitch geometry.
**State:** synthetic match paused at25:00; score1–0; factual context00:00–25:00; shots6–0; cutoff269; zero model calls. Received head is90:00 in the actual completed local ingestion, rather than the older mock's62:16. No future event/score beyond the selected cutoff is displayed.

## Comparison evidence

The source and full desktop capture were opened together for comparison. Focused review also inspected the scoreboard/header, field annotation, native transport, result/shot meters and `02-evidencia.png` (620×1100), plus `04-movil.png` (390×1712) and `05-evidencia-movil.png` (390×844). `03-personalizacion.png` covers the expanded preferences.

### Required fidelity surfaces

- **Typography:** IBM Plex Sans is loaded locally (45.71kB font asset), with readable text and tabular numeric clocks. The real UI is quieter/denser than some generated typography; context title and shot heading retain the intended hierarchy.
- **Layout rhythm:** compact match strip, two aligned workspaces, matte replay and integrated native transport are implemented. Actual 105×68 pitch geometry intentionally makes the page taller than the mock; no field-coordinate distortion is introduced. Recent actions form the one chronological event strip rather than duplicating a second, inaccurate miniature event axis. At320/390px workspaces stack without horizontal overflow; fields/buttons preserve44px hit areas.
- **Colors/tokens:** neutral, slate and petrol semantic tokens replace the previous gradients/chrome. Team colors appear on original typographic club identifiers and factual comparison. Page and dialog axe checks found no selected WCAG A/AA violations.
- **Assets:** user-requested identity replacement is intentional: local generated abstract sequence mark and provisional English name Touchline replace the reference's generic football/MatchContext identity. Existing licensed MingCute icons remain. Pitch and annotation are factual SVG data visualization, not approximated decorative assets.
- **Copy/content:** original Spanish/English controls and honest factual/scripted/reviewed disclosures remain. The zero-shot team has an empty meter; no causation or invented narrative is added. The read-only end of the recap interval follows the cursor.

## Findings and comparison history

- [P2, fixed] Initial pitch label had an oversized border because HTML inside an SVG foreignObject rounded fractional CSS borders before scaling. Replaced it with native SVG data annotation and a thin leader line; final desktop capture shows the corrected label.
- [P2, fixed] The same small annotation became unreadable on a390px pitch. Hide that redundant annotation on narrow screens; preserve the readable full caption and event icon below the plot. Final mobile capture confirms this.
- Expected adaptations: preserve actual field aspect; avoid duplicated recent-event controls; use real received-head metadata; replace branding as requested. These are intentional product constraints, not silent fidelity claims.
- No remaining actionable P0/P1/P2 visual findings after the above corrections.

## Interaction and runtime verification

- Integrated replay: play/pause, rewind, native keyboard slider, speed, latest received minute and chronology-safe shortcuts.
- Context: language/detail/team settings, interval bounds, explicit generation/cancellation, result and evidence.
- Drawer: finite240ms transform/opacity, scrollable sources, focus trapping, Escape/return; full-width on mobile.
- Event450ms and recap220ms cues remain finite; reduced motion is static. Rewinds disconnect old event data immediately.
- Unit40 tests pass; real HTTP/SQLite browser suite12 tests covers desktop/mobile. The final suite is rerun after the annotation correction; see validation record/ledger.
- Factual capture automation found no page/console errors. Browser inspection in Codex's in-app browser also confirmed the actual local screen and generated factual result.
- Remaining coverage limits: no Safari/Firefox, NVDA/VoiceOver, user usefulness study or real Foundry quality evaluation in this visual delivery.

## Implementation checklist

- [x] Selected mock and actual desktop/mobile captures inspected.
- [x] Five fidelity surfaces checked and intended adaptations recorded.
- [x] Corrected annotation and readable mobile caption captured.
- [x] Real controls and original bounded data flow retained.
- [x] No actionable P0/P1/P2 design findings remain.

**final result: passed**
