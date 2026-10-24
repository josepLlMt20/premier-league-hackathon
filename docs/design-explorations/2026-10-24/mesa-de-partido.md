# Mesa de partido — revised visual proposal

Status: proposed for user review; not implemented. Generated with the built-in Image Gen tool from the current application screenshot. The PNG is a visual mockup, not evidence of application behavior.

The user clarified that the issue is a generic component-library appearance, not insufficient decoration. They want a serious, understandable, usable professional tool while preserving the existing structure. The previous three concepts are rejected as directions.

## Visual decisions

- Preserve the left match/replay workspace and right recap/evidence workflow.
- Use aligned surfaces and fine rules instead of floating cards and window chrome.
- Keep body text readable, times tabular, and score and summary prominent.
- Use compact rectangular controls with a consistent shape language; preserve accessible hit areas in implementation.
- Reserve deep petrol for actions and selection, and amber/cobalt for fictional club identity.
- Avoid decorative backgrounds, photography, gradients, glow and pill-shaped controls.

The existing implementation, design tokens, behavior and accessibility tests have not changed. This proposal supersedes the earlier style brief only if the user approves it. A generated image cannot establish contrast, keyboard behavior or responsive quality; those require implementation validation later.

## Source and output

- Structural reference: `tmp/remote-captures/01-escritorio.png`.
- Output: `04-mesa-de-partido.png`.
- Tool: built-in Image Gen; no separate API or Azure model calls.
- Date anchor: 2026-10-24; displayed match data is synthetic.

## Generation prompt

```text
Create ONE carefully art-directed, realistic, production-quality desktop WEB APPLICATION UI mockup for MatchContext, 1440 x 1264. Concept name: Mesa de partido. The attached image is a STRUCTURAL AND CONTENT REFERENCE ONLY. It is the existing application whose layout the user likes but whose template-like visual language they reject. This is a professional football match intelligence tool, useful for both fans and analysts, not a marketing page, a generic dashboard template or a themed sports poster. The user explicitly wants serious, understandable, usable visual craft WITHOUT Google Material UI styling or stereotypical AI UI.

HARD CONSTRAINTS
Preserve the two-column structure: larger left match replay/score/field/playback area (~695px), right catch-up controls and explanation (~480px), within a ~1200px aligned workspace. Preserve every core function and current facts. Do not add navigation, charts, metrics dashboards, AI chat, tabs, odds, video or functionality. Do not add a sidebar. Output a single screen, not a moodboard/comparison sheet, no browser/device bezel or annotations. Match the provided image aspect ratio naturally.

DESIGN DIRECTION — precision through proportion, typography and alignment
A bespoke analytical sports desk. Flat warm-cool neutral near-white canvas #F3F4F3, white working surfaces, ink #1E272B, restrained muted slate secondary text, a single deep petrol #165D66 action accent. Amber and cobalt reserved ONLY for identifying the two fictional clubs. No gradients, drop shadows, glow, decorative backgrounds, paper/grain textures, stadium photography, illustrations, shiny surfaces, dotted canvas, giant marketing headlines, pills, oversized round buttons, glass, glowing balls or repeated floating cards. No oversized AI/sparkle iconography. Professional does not mean cramming. Calm polished finish, crisp 1px separators, deliberate group spacing, all elements grounded on a stable baseline grid. Modest 3-4px corners on controls; square-ish action buttons. Shared component geometry throughout. No cards within cards; use page surface, alignment, fine rules and functional grouping.
Typography: IBM Plex Sans for clear human industrial character, its tabular numerals for match statistics, IBM Plex Mono only for small timestamps if needed; max two typefaces. Intentional 14-16px readable body, 12px minimum labels, headings 20-28px, medium-weight controls, 32-36px score, no enormous display typography. Professional custom sports tool identity in precise column alignments, clock numerals, field caption, temporal markers and considered microcopy. Not the default soft Google controls from the reference.

LAYOUT AND CONTENT
Top thin product header: small original monochrome geometric football mark and wordmark MatchContext left, understated "Inside the Game · Hackathon" right. Thin separator. Below a compact workspace heading "El partido, explicado." at 26px with small plain "Partido sintético" disclosure and "A tu ritmo" context. This header consumes substantially less height than a landing-page hero but keeps the same structural location.
Left area: compact, precisely aligned scoreboard with original typographic ÁM and CO square club identifiers, Ámbar FC and Cobalto United, centered score "1 – 0", "1ª parte". Small separate clock/status row "Estás viendo 25:00" and "En pausa". Prefer a clean light scoreboard with typographic contrast; do not turn it into an advertisement or giant black banner. Use fine ruled divisions rather than surrounding everything with cards.
Below "Última acción registrada" left and "25:00" right, a readable deep subdued GREEN football field with thin pale markings, clean rectangular proportions, almost-square corners, extremely subtle alternating grass strips. Exactly ONE small amber event-location point near the right penalty area. No 22 imagined player positions, no unearned heatmap, no motion effects baked in. Under field an understated line-icon and caption "Presión · Cobalto 01"; helper "Un evento, no seguimiento continuo."
A purpose-built playback rail: "Minuto del partido" and tabular "25:00", slim dark teal progress track, precise thumb, understated small reference ticks if useful. Below a 44px-height rectangular outlined rewind icon control, rectangular "Reproducir" with play icon and outlined compact "Velocidad 1×" select. Small plain footer "Datos recibidos hasta 62:16" and text action "Ir al último minuto recibido".
A slim recent-actions strip with three separated cells/rows, NOT three floating pills: "25:00 Presión", "24:55 Gol", "24:54 Disparo". Functional small line icons, active event indicated by a thin petrol edge or underline. Collapsed disclosure "Acciones recientes" and count100 underneath.

Right area aligned with match area top: separated by a single vertical rule or very subtle neutral boundary, no window title bar, no card chrome. Plain small sectionlabel "TU RESUMEN", heading "¿Qué me he perdido?" at24px, supporting sentence "Lo que cambió, hasta tu minuto." Below a precise clearly labeled range control "Resumir desde" with tabular "00:00" and "Hasta 25:00"; slim track, consistent 44px hit areas. Compact "Personalizar" row with line sliders icon, chevron, subtle rules.
Primary action rectangular solid deep petrol with white text "Ponerme al día" and modest arrow, height44px, no giant radius or glow. Distinct content below clear divider: small uppercase "RESUMEN FACTUAL", readable actual summary "Ámbar FC: 6 tiros en el tramo. Cobalto United: 0 tiros en el tramo." Keep useful breathing room and strong text legibility, no unnecessary summary-container card. Supporting caveat "Mostramos hechos calculados. No se ha completado una narrativa de IA revisada." Secondary rectangular outlined action "Ver evidencia" with document/list line icon. The explanation is the result; make it easy to read, not a decorative info tile.

Content must remain honest and finite: score1–0 at25:00, syntheticmatch, factualsummary; no claim of liveAI/reviewedAI. Dates if any anchored to2026-10-24, but no calendar date is necessary. All visible text Spanish, proper spacing and diacritics. Faithfully present a usable crafted screen with clear priorities. Visual richness must come entirely from excellent layout-detail and typographic execution, NOT extra color or ornamental effects.
```
