# Touchline match studio

The user approved the Estudio de partido mockup and interaction proposal on 24 October 2026. This supersedes the earlier Heyclicky appearance. They also requested an English-based identity; **Touchline** is the current provisional name. Backend identifiers, repository name and the preferences storage key remain stable.

## Visual system

- Selected truth: `docs/design-explorations/2026-10-24/05-estudio-de-partido.png`.
- Compact scoreboard across the workspace, larger dark replay stage, integrated transport and chronological recent actions; contextual reading surface on the right.
- Mineral background, white surfaces, graphite stage, petrol actions; amber/cobalt identify fictional clubs. No decorative gradients, dotted canvas, window chrome or pill buttons.
- Self-hosted IBM Plex Sans Latin variable font; tabular numerals for clocks/counts. Native form controls and consistent licensed MingCute line icons.
- `web/src/styles/tokens.css` holds semantic tokens; `app.css` owns composition, data visualization and responsive behavior. Base UI keeps focus, disabled states and modal semantics.
- The generated abstract sequence mark is local; no generic football brand icon. See `docs/design/touchline-brand.md`.
- Real SVG pitch coordinates remain 105 by 68 meters. Its proportions are taller than the schematic mockup; do not distort coordinate geometry to fit a decorative frame.
- Mobile stacks the workspaces and retains all controls. The tiny pitch annotation is hidden; the full readable event caption remains below it.

## Data and interaction

One event/trajectory is shown, never inferred continuous tracking. The anchored event label uses known coordinates; a leader line is an annotation, not an inferred movement. Recent shortcuts use availability time and focus the stable native time control before reloading.

The result-bound shot comparison renders only when exactly one valid fact per team matches the immutable context snapshot, cutoff and full requested sequence interval, without an additional time filter. Null, unsafe, negative, fractional, duplicate or mismatched counts produce no chart. Zero is an empty meter. Context text remains authoritative and provenance labels distinguish factual, insufficient, scripted and reviewed outputs.

Finite cue durations: event 450 ms, recap 220 ms, drawer 240 ms, press 150 ms. Exact score/count changes are immediate. Seeks clear stale content and evidence immediately; no outgoing snapshot is kept for animation. Reduced motion disables transitions/animations.

Evidence uses a right-side modal drawer on desktop and full-width dialog on mobile, with focus trapping, scroll region, Escape and return focus. It retains the context's immutable snapshot and API batching.

## Verification

See `design-qa.md`, `docs/web-validation.md` and `docs/evidence/studio-2026-10-24/`. Real captures use factual mode, synthetic data, cutoff269 at25:00 and zero model calls. No new Azure deployment or live-model quality evaluation is implied. Better Design's exhausted quota was not retried; visual QA uses the approved mockup and rendered browsers.
