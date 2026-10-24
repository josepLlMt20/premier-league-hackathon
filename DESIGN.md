# Match Context web

The approved [product specification](docs/superpowers/specs/2026-10-19-match-context-design.md) defines behavior. This first delivery implements the fan journey (task 6); professional tools follow separately.

The user selected [Heyclicky](https://better-design.com/design-systems/heyclicky): light dotted canvas, silver window chrome, rounded buttons, restrained blue actions. The gain is a friendly fan experience; the cost is more space than a dense professional desk. This is a consumer match viewer, with no sidebar or dashboard navigation.

## Source and components

- `web/src/styles/tokens.css`: installed Heyclicky React/Base UI tokens.
- `web/src/components/ui/`: actual installed Button, Card, Badge, Dialog and NativeSelect, plus shared helpers. The full kit was installed; unused catalog components and dependencies were removed.
- `web/src/styles/app.css`: application layout, data visualization tokens and accessibility adaptations. Keep the kit materials.
- `web/src/components/icons/`: exact MingCute **line** source supplied by Better Design/Iconify. The kit's mixed icon imports were replaced; the native select uses the browser arrow. Do not introduce runtime icon CDN requests.
- Playback time uses native range inputs for keyboard/screen-reader behavior. Pitch is SVG data visualization of one bounded event, not decorative player tracking.
- Dialog handles focus trapping, Escape and focus return. Evidence remains optional and does not change the playback cursor.

## Deliberate adaptations

Inter is self-hosted from the pinned Fontsource package, using the Latin variable font needed for the current Spanish/English UI. Preserve the `Inter` family token. Other language scripts need their font subsets before they are offered.

The original primary gradient was too light for white text. Its blue hue is retained with darker stops, and small blue story indices use `--primary-ink` after an actual axe contrast failure. Controls have 44px targets, a visible focus outline, explicit names and reduced-motion handling. Input borders are darker than decorative window borders.

Keep real states distinct: loading, no events, unavailable API, insufficient evidence, scripted tests, calculated factual fallback and reviewed AI narrative. A reviewed narrative is not a guarantee of semantic truth. Generation starts only on request, can be cancelled, and never advances ingestion.

## Review evidence

Run the commands in [web validation](docs/web-validation.md). Check the rendered app at 390, 1440 and 1728px, plus 320px reflow; open preferences and evidence, test focus and keyboard controls. Generated spacing captures live in `tmp/ui-validation/`. Fully clipped keyboard-only skip links are excluded from unfocused geometry; the focused link is tested separately.

The spacing tool's inferred card padding includes a full-width window border, while content padding lives in inner bodies. Its default scale also flags the installed kit's 6/20/28px values and fluid auto margins. Evaluate those measurements against the actual source and screenshot rather than turning the window chrome into a padded nested card. Record unresolved functional findings; never substitute tool scores for visual inspection or real user testing.

MingCute and Inter license notices are bundled under `web/public/licenses/`. No league/team logos, real match feed, copyrighted music or real player imagery are used.
