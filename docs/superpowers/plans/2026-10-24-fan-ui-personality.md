# Fan UI personality refinement

> **For agentic workers:** use superpowers:executing-plans inline, with one final delta review. This refines the already approved task6/Heyclicky delivery and updates its existing PR5.

**Goal:** Give the football viewer recognizable character and meaningful movement while retaining its temporal guarantees.
**Architecture:** Compose the existing Heyclicky components, local MingCute SVGs and CSS animations. Keep the neutral pitch/metadata mounted while bounded data loads; remove old events/score immediately. No backend changes, paid assets, animation runtime or Azure calls.
**Spec:** [Design and motion brief](../../../DESIGN.md#personality-pass-24-october), plus the original approved match-context specification.

## Task 1: Fan UI personality delivery

1. Capture the existing desktop/mobile UI before editing; inspect official icon and animation sources. Done before this plan.
2. Add failing tests for recent-event seeking by availability time, empty/correction presentation, and neutral-pitch loading without old event content.
3. Implement `EventIcon`, the bounded recent-action rail and the neutral loading shell in Pitch/Viewer. Keep abort/request-key behavior.
4. Refine the scoreboard, spacing, icon use and finite event/recap/press motion. Honor reduced motion and do not animate numeric values or exits.
5. Verify unit tests/build/types/format, real desktop/mobile HTTP journeys, no stale event during motion, reduced-motion computed styles, focus/contrast and screenshots at390/1440/1728. Review the rendered change against the stored rules because the MCP quota is exhausted.
6. Run one independent review of this delta, fix significant findings with regressions, then update PR5 with evidence and limitations. Preserve its pending merge status.

Review focus: late-event availability versus occurrence; a seek during an active animation must remove the previous event immediately; loading must not show the old score/player; no animation replays for an unchanged event on clock ticks; disabled/reduced motion leaves the complete trajectory visible; no fabricated live status or team assets.
