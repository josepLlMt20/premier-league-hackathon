# Estudio de partido — modern professional proposal

Status: proposed revision, awaiting user feedback. No application implementation changes.

The user accepts a serious professional tone but wants more modernity through composition, modules, controls and interaction. This revises Mesa de partido and allows deliberate distribution changes while retaining the match replay and context workflows.

## Visual proposal

- Replace the large generic heading with a compact match scoreboard and clock.
- Give the replay a larger, matte dark working surface and anchor the event label to its known location.
- Integrate a purpose-built playback ruler, precise current playhead and recent-event strip.
- Keep the latest three close events in a clearly local sequence strip; do not falsely distribute them across the whole match ruler.
- Make the catch-up interval compact, keep the end fixed at the playback cursor, and use one explicit generation action.
- Restate the existing shot counts as a restrained comparison, with zero represented by an empty neutral track.
- Keep the result and its evidence connected in the context panel.
- Retain neutral surfaces, petrol actions, limited team colors, readable type, consistent line icons and small corner radii.

## Proposed interaction, not demonstrated by the static image

- On a valid newly accepted event, show a single 350–450 ms location cue and update the anchored event label. Never imply continuous player tracking.
- Selected-event feedback takes 120–150 ms. Seeking immediately clears old contextual data; do not animate an outgoing stale snapshot.
- Reveal a completed recap with a restrained 180–220 ms opacity transition. Update exact score and statistics immediately, without count-up animation.
- Evidence opens as an accessible side panel on desktop, using a 200–250 ms small transform/opacity transition; use a full-width dialog on narrow screens. Preserve focus, Escape and return behavior.
- Personalization opens inline without hiding the selected match moment.
- Respect reduced-motion preferences and keyboard access. Preserve visible focus and 44 px targets.

These are design intentions; responsive behavior, data bounds, timing and accessibility need implementation verification after approval.

## Scope and provenance

- Final visual: `05-estudio-de-partido.png`.
- Reference: `04-mesa-de-partido.png`.
- Built-in Image Gen generated the concept and a targeted correction to transport icon, fixed interval end and removal of an unsupported fullscreen action.
- Static image only; all displayed match data is synthetic. No separate API/Azure model calls or application code changes.
- Generated UI text and geometry are a visual target; semantic controls and exact event-availability rules remain governed by the existing product specification.

## Generation prompt

```text
Create ONE realistic high-fidelity professional desktop WEB APPLICATION design, 1440x1100. Revise the attached MatchContext mockup in response to precise user feedback: its serious professional tone is right, but it remains too plain and conventional. Introduce noticeable MODERN PRODUCT DESIGN through composition, module relationships, a custom replay transport and connected evidence. This is a proposed next iteration, not an implemented screenshot. Concept name "Estudio de partido". No moodboard, no multiple designs, no external captions, no browser or device bezel.

REFERENCE ROLE: attached image is the previous concept and factual-content reference. Keep its neutral/petrol identity and factual integrity but you MAY substantially refine page distribution. User now explicitly allows new layout, modules, buttons and purposeful motion. Do not reproduce its oversized headline, symmetrical columns or default thin range controls. Aim for an independently art-directed professional analysis product, more contemporary and distinctive without loud colors, marketing decorations, dashboard filler or template-library appearance.

COMPOSITION
Use a tailored 1320px working area with 60px side margins. Compact 64px high header: original understated geometric match mark and "MatchContext" wordmark left, discreet "PARTIDO SINTÉTICO" text and small "Inside the Game · Hackathon" right. Below a clean match-specific scoreboard strip, not a large marketing hero: Ámbar FC with small amber ÁM square, score "1 – 0", Cobalto United with small cobalt CO square, "1ª parte", and tabular clock "25:00 · En pausa". Deliberate baselines and asymmetric grouping. No generic left navigation or fake tabs.

Below, asymmetrical working composition: ~820px left visual replay stage, ~440px right contextual reading workspace separated by 28px. On the left a beautifully proportioned matte graphite (#18252B) REPLAY SURFACE, corners8px max, with its own small top header "Última acción" and timestamp25:00, subdued functional action icon. Main football pitch is a precise schematic top-down visualization in muted deep sage-green tonal values with thin high-contrast field markings, almost square corners, no grass photography, texture, glowing effects or gradients. ONE small amber event-location dot near the right penalty area, with discreet short leader label "Presión · Cobalto 01" anchored close to that point. Do not draw fabricated players, passing routes, pressure heatmaps, balltracking or animations not supported by a single point. Small neutral helper at bottom of surface "Localización del evento · Sin seguimiento continuo". Professional chart-like craft: functional line weight, quiet boundary labels, little angular bracket detail if useful, never decorative futuristicHUD clutter.

A TAILORED REPLAY TRANSPORT below the field: one continuous pale neutral horizontal module, integrated with the replay stage instead of lots of buttons. Clear square play/pause44px control and secondary rewind icon at left, custom well-spaced time ruler across the center, current cursor a crisp narrow petrol vertical playhead with small time tag25:00, restrained ticks showing actual elapsed match range00:00–25:00. Three precisely spaced event markers clustered truthfully at the current end:24:54Disparo,24:55Gol,25:00Presión. Do NOT spread them over earlier minutes or fabricate events to fill empty space. Can group last moments into a dedicated zoomed local strip beneath the broad time ruler, with clearly labeled timestamps. A small compact rectangular1× speed control on the right. 44px touch targets, visible selected state; no giant round Material controls. Below, quiet metadata "Datos recibidos hasta62:16" and text action "Ir al último minuto recibido"; received clock is metadata only, do not expose future scores/events beyond25:00.

A slim connected 'Secuencia reciente' section at lower left makes the three known actions read as a chronological sequence with small line icons and exact times24:54Disparo →24:55Gol →25:00Presión, most recent selected via a petrol vertical edge/underline. Each is a compact readable row/cell in one grouped module rather than individual cards. Disclosure "Todas las acciones" remains accessible. This relationship gives the interface product-specific identity.

RIGHT CONTEXT WORKSPACE: Treat the explanation as a well-designed reading and reasoning document, not a tall form or promotional card. Small kicker "CONTEXTO DEL TRAMO", heading "¿Qué me he perdido?" at24px; one compact inset control band "Desde00:00" with labeled input/slider and "Hasta25:00", plus an understated rectangular "Personalizar" control. Strong primary rectangular petrol button44pxheight "Ponerme al día" and arrow, no glow/gradients/shadow. After an intentional divider show smalllabel "RESUMEN FACTUAL" and meaningful focal data typography: "6 tiros frente a0" with a restrained two-row horizontal comparison made ONLY from those known shot counts, labels ÁmbarFC6 / CobaltoUnited0, amber/cobalt small identifiers. This is a restatement of actual existing data, not added analytics. Zero should have no invented bar length.
Readable compact explanation "Ámbar FC:6tiros en el tramo. Cobalto United:0tiros en el tramo." Small caveat "Hechos calculados; narrativa de IA pendiente." Place a neatly aligned source/evidence footnote row with document line icon and supporting action "Ver evidencia" that feels anchored to this result. Do NOT invent causes such as control or dominance from the shot count. Use deliberate editorial spacing, gentle neutral section tint only if needed, no cards nested in cards.

VISUAL LANGUAGE
Quiet pale mineral-gray canvas, clean offwhite surfaces, nearblack text and matte slate replay stage, one restrained deep petrol accent. Club amber/cobalt only for team identification. Balanced negative space; professional but warm, readable and contemporary. Typography IBM Plex Sans or equivalent precise modern humanist sans, with tabular numeric clocks, 14–16px body, 12pxminimum labels, 24px headings, score32px. Max2fonts. Weight, proportion and information relationships carry identity. Small consistent custom-feeling line icons, compact rectangular buttons with4–6px corners, crisply inset input fields, precise alignment, subtle surface layering without visible dropshadows. No pills, defaultGoogleMaterial appearance, gradients, sparkleicons, glows, stadiumbackgrounds, giantheadline, excessive rounding, charts unrelated to the currentfacts or multiple decorative panels. Modernity comes from a bespoke instrument-like transport, point-linked event label, strong light/dark contrast in the working surface, and connected context/evidence.

All UI text Spanish with proper spacing and diacritics. Match synthetic at25:00,1–0; current dateanchor2026-10-24, no calendar datesneeded. Keep all controls and metadata plausible, legible and unclipped. This is a serious implementable tool with a clear primary workflow: select moment → inspect location → understand context → inspect evidence. Output ONLY the single complete screen.
```

## Targeted edit

```text
Make a surgical correction to this existing UI mockup; preserve the whole image, exact composition, typography, colors, all data, all text, field and modules. Exactly three small changes: (1) The match is paused ('En pausa'), so the solid petrol replay transport button near bottom left must show a WHITE RIGHT-POINTING PLAY TRIANGLE, not two pause bars. (2) Remove the small fullscreen action icon in the upper-right corner of the dark replay surface, leaving that small area plain dark; fullscreen is not part of the agreed workflow. (3) The right-hand range control has a fixed 'Hasta 25:00' bound: preserve both time boxes and the connecting rail but use only ONE adjustable circular thumb at the left endpoint (Desde00:00); the right endpoint should be a short fixed thin vertical tick, not a second draggable circular thumb. No other changes. Output the one complete corrected screen, same dimensions as the input.
```

