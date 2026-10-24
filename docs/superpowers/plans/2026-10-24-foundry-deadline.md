# Foundry deadline alignment plan

> Use superpowers:executing-plans inline; one integrated fix and one fresh review. User explicitly authorizes solving the10-second limit and trying real texts. Update current PR6 in the current checkout; do not merge.

**Goal:** Let real analyst/writer/reviewer briefings finish within a finite end-to-end budget and verify Spanish/English output on the existing deployment.
**Architecture:** One authoritative25-second generation cap shared by Settings, AgentLimits, Foundry HTTP/SDK and SDK function-loop duration. Keep the browser's30-second context timeout,10-second storage-read cap (15-second browser reads), manual cancellation, admission2, calls7/tools8/output1200 and one repair. No schema/dependency/resource changes.
**Spec:** Existing bounded professional workflow plus the user's explicit request to replace the local10-second ceiling. Previous measured evidence docs/evidence/commentator-2026-10-24/live-copy-probe.json shows both languages exhausted the orchestration deadline, not a Foundry-enforced service cap.

## Integrated fix

- [x] RED: configuration/defaults accept25 but reject26/infinite/NaN; service/CLI orchestration can finish a simulated12-second three-role run; SDK HTTP and function-loop do not retain10-second ceilings; storage reads retain10 seconds. Short-deadline cancellation, limits and fallback regressions remain.
- [x] GREEN: align bounded generation limits in base/config/Foundry; preserve shorter overrides and storage read guard. Browser timeout remains30, not shortened during model work.
- [x] Verify targeted/full suites. Run measured existing-deployment ES/EN professional samples with per-role timing and strict final validation; record public text, provenance, usage, latency and actual fallbacks. If25 seconds is insufficient, diagnose the exact remaining failure before another change; no unbounded retries or relaxed grounding.
- [ ] Open an isolated real Foundry preview, keep factual/scripted previews explicit, inspect evidence/exports and show actual generated text. Refresh docs and one independent review, regression-fix material findings once, push/update PR6, no merge.

Decision:25 seconds leaves response margin beneath the existing30-second web timeout. It allows a longer wait, not a larger model/tool/token budget. Storage read time is kept at10 to avoid extending it past the15-second web read limit. The main factual preview stays available; a separate explicit Foundry preview is used for user testing.
Observed extension: real probes exposed a count used as a spatial threshold. Targeted failing/passing grounding regressions and clearer writer/reviewer guidance were added before enabling user testing. No budgets were relaxed to admit these mistakes. Current live Spanish prose can still be awkward; automatic accepted status is not a human editorial endorsement.
