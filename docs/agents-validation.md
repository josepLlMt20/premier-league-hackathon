# Grounded agents: implementation and validation

## Current deadline and professional samples

The user's subsequent request replaces the local 10-second generation ceiling with a shared 25-second ceiling across configuration, orchestration and SDK/HTTP/function loops; calls/tools/tokens/admission caps are unchanged. Latest real HTTP samples returned accepted Foundry cards in Spanish (8.31 seconds of agent time) and English (16.25 seconds, including repair), with rejected candidates withheld. Earlier semantic failures and manually excluded outputs are retained in the report. These are point samples, not an editorial-quality or latency guarantee. [Deadline change, tests, measured attempts and live preview](foundry-deadline-validation.md). Older sections below retain their historical limits and observations.

## Professional copy correction, 24 October

The writer/reviewer now distinguish headline, explanatory context, speakable commentary and compact overlay. Numerical synthetic-shot-index claims require an explicit synthetic/heuristic index label and points unit; territorial-share values require attacking-third passing context and a percent unit. Exact repeated main fields are rejected after normalized rendering and may be repaired within the existing budget. These are narrow mechanical guards, not a semantic-quality guarantee. Higher index sums must not be described as higher shot volume without supporting shot counts.

The bilingual scripted writer now supplies readable pattern-specific examples.65 frontend unit tests,269 backend tests and22 real browser journeys pass. Two separate real professional samples (ES/EN) returned factual fallback at the unchanged10-second deadline; English also encountered a free-number rejection. No new live editorial-quality success is claimed. See [professional validation and measured report](commentator-validation.md).

Scope: task 4 of the approved plan. The analyst, writer and reviewer use one closed snapshot and explicit typed handoffs. This delivery does not add the API, web application, browser state, hosted agents or deployment. The previous persistent-ingestion PR is merged into master.

## Workflow

1. Reconstruct canonical facts and supported patterns using the existing deterministic engine. Every supplied fact is checked against a fresh calculation for its own interval; forged values or references cannot become trusted facts by reusing an identifier.
2. The application prefetches `list_candidates` at the already-authorized cutoff and supplies its actual result to the analyst, avoiding a model turn whose only purpose was requesting these fixed arguments. The tool call is charged and traced as `candidates_prefetched`. The analyst still makes the selection and can request further facts or events. A simple fan receives one selected story; the model is instructed to select up to two for detailed fans or commentators, under the public cap of three.
3. The writer returns typed cards containing observed or tentative interpretation claims. Four claims cover the headline, explanation, suggested line and overlay. Each cites its own story's canonical facts/events.
4. Deterministic checks reject unknown references, unrelated support, literal Unicode numeric symbols (before and after normalization), raw known match names, invalid markers, duplicate claim IDs, unsupported interpretations, strong causal wording and overlays longer than 140 rendered characters. Claims citing high-recovery counts, or naming recoveries while supported by that metric, must retain the distinguishing `high recoveries` / `recuperaciones altas` qualifier. Unicode marker normalization uses the same representation for validation and rendering.
5. The reviewer judges metric labels, team/window correspondence, language, audience, qualifiers and interpretation. Rejected cards get one batch repair attempt; accepted cards survive while twice-rejected stories are discarded. The summary is assembled only from accepted lines. Invalid writer or reviewer JSON/schema output enters the same bounded batch-repair path; malformed review during a repair does not discard previously accepted stories. Deadline/provider/budget failures still return identified factual fallback.
6. Final validation checks the public summary, cards, limitations and overlays against their validated claims and canonical story intervals. Rendered fields cannot bypass validation by carrying different text. No rejected prose is inserted into a repair prompt or public rejection reason.

The default CLI is factual-only. It renders a localized count of shots from trusted facts and identifies limited observations when applicable. It does not fabricate a standout pattern or present template output as a successful agent run. Empty or unsupported-pattern contexts do not trigger unnecessary model calls.

## Tools and isolation

`list_candidates`, `read_facts` and `inspect_events` require exactly the authorized cutoff. Unknown facts, unknown events and future cutoffs are denied. Evidence inspection is limited to ten requested IDs at a time. Compact tool facts retain their canonical ID, value, interval, sample/denominator, method and limitations, with explicit `event_sample_ids` and `evidence_count`; full evidence remains resolvable in the closed snapshot.

Each request has a new tools registry, budget, trace ID and typed payloads. Each Foundry role creates a fresh Agent; there are no reused conversation/session IDs, previous-response IDs, persistent model memory, web search or hosted tools. A shared inference client may reuse its network connection, while the role history remains call-local. Static fictional rosters are allowed context, including names of substitutes; they do not reveal later match events.

Public traces contain role/decision labels, allowed tool names, attempted provider turns, requested-tool counts, aggregate provider-reported token usage captured before structured parsing and elapsed request time. They contain no prompts, private reasoning, token credentials or raw provider error messages. Provider startup/authentication is reported separately from an in-request fallback.

## Foundry and limits

The adapter uses Microsoft Agent Framework `Agent` and `FoundryChatClient`, a Pydantic `response_format`, the existing deployed model and Azure CLI identity. Each role requests only its own output schema. A provider-only codec uses integer fact indexes and reconstructs canonical references and unique claim IDs before the existing validation pipeline. Each claim still supplies explicit support. Unknown indexes, unsupported caveat codes, wrong-story support, malformed markers and free numbers remain rejected. Public `ContextResult` contracts retain canonical IDs; these internal indexes are never public claim references.

The writer chooses from `observed_association` and `sample_limited` caveat codes, localized by code; full source and pattern limitations are still added independently. This prevents generated negative-causation disclaimers from triggering the conservative causal-language filter, and avoids copying English source limitations into Spanish output. Cost: custom model-written limitation prose is unavailable through this provider adapter. Scripted runners and the public Claim contract retain their original expressiveness.

Provider-generated claims require fact support; their complete event evidence is restored through those facts. Direct event-only claims remain supported by the public contract and scripted runners, but are outside this compact provider format.

Connection setup warms the **same** refreshable [Azure Identity bearer-token provider](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.aio?view=azure-python) passed to inference. The earlier raw-credential warmup left the SDK's separate provider cold. The regression proves that inference reuses the valid token and that the provider reacquires it near expiry. Tokens remain in the SDK's memory, are not logged or written into the repository, and security policies are unchanged. No resources or model deployments are created. HTTP retries are disabled.

| Budget | Limit | Enforcement |
| --- | --- | --- |
| Model turns | Seven across all roles and repairs | Chat middleware reserves before each SDK provider turn, including the continuation after a tool result. |
| Tools | Eight across a request | The initial application prefetch is charged through the scoped tool. Middleware reserves any additional model-requested calls before execution, including unknown names or invalid arguments. Scoped wrappers do not charge the same call twice. Direct offline tools enforce the same budget. |
| Output | 1200 tokens per provider turn | Run options serialize into the actual SDK request body. |
| Request duration | 25 seconds (previously ten) | Request-local monotonic deadline and cancellable asynchronous role calls. Timeout returns identified factual output. |

These are operational bounds, not a monetary cap or an assurance of successful generation within the deadline. Cold startup/token acquisition is extra. The SDK middleware shape was checked against the [Microsoft middleware documentation](https://learn.microsoft.com/en-us/agent-framework/agents/middleware/chat-middleware); the provider uses the [Foundry application-owned agent pattern](https://learn.microsoft.com/en-us/agent-framework/agents/providers/microsoft-foundry).

## Tests and current live status

Tests exercise invented facts, unknown/future events, forged metrics, malformed JSON, two reviewer rejections, partial acceptance, one repair, timeout, provider-error sanitization, profile selection, bilingual factual output, request isolation, Unicode markers, public-text tampering and preservation of interpretation limitations. A real SDK plus fake HTTP transport verifies provider-turn counting, aggregate usage, no retained earlier sentinel, no previous response/conversation IDs, actual output/store options and a budget stopping the next network turn. The SDK transport tests never contact Azure.

The live test is opted in with `RUN_FOUNDRY_LIVE=1`. It requests Spanish context at second 1500 and English context at second 1490 through the same inference client with fresh role contexts; it requires verified Foundry output, all three roles, actual tools, usage and distinct cutoffs. Reports go to ignored `tmp/foundry-agents/`.

On 23 October, the first live attempt stopped during token acquisition with Azure error `AADSTS530035` (blocked by security defaults). No model request was made in that attempt. Azure CLI account metadata was accessible, which does not itself demonstrate that a fresh inference token can be obtained. The subsequent device-code attempt was cancelled after sign-in was denied; no security policies were changed.

On 24 October, interactive sign-in on the participant's PC succeeded and a fresh Foundry inference token was obtained. The opted-in live test then reached the real deployment: the analyst called `list_candidates`, completed its selection and handed off to the writer. The request reached its ten-second deadline during writing and correctly returned identified factual fallback: zero story cards, rejection `deadline`, three attempted model turns, one tool call, 6003 reported input tokens and 98 reported output tokens from completed responses, and 10.003 seconds of request time. Usage from a cancelled/incomplete response is not represented by those counters. The test failed its required verified-output assertion and therefore did not run the second English request. Reports remain in ignored `tmp/foundry-agents/`.

Authentication was resolved for this session. The initial latency profile measured 2.559 seconds for requesting the known candidate query and 2.304 seconds for selection; writing did not finish before the deadline. Compact wire schemas alone did not pass. Subsequent diagnostic runs also exposed reference arrays containing marker strings and generated disclaimers rejected by the existing causal filter. Integer support indexes and localized finite caveats address those format failures without weakening evidence or prose validation. These exploratory failures are not counted as successful smoke runs.

The initial optimization produced four accepted outputs, but the later whole-PR review found a concrete semantic error in one detailed English response: high recoveries were labelled simply as recoveries. Total recoveries were flat at five in both windows while high recoveries rose from one to four. Those original outputs are preserved unchanged in [the superseded report](evidence/2026-10-24-foundry-agents-smoke-before-review.json), marked as historical. Current validation rejects the captured ambiguous wording; it is not presented as valid current evidence.

After the review fixes, the unchanged opted-in bilingual test passed again: both requests produced verified Foundry output, all three real roles, scoped retrieval, positive usage and isolated trace/snapshot cutoffs. The first post-review attempt instead requested repair and reached the deadline, failing the verified-output assertion; its English case was not reached. The subsequent two detailed-profile checks also reached the deadline while repairing rejected prose and returned identified factual fallback. All five post-review requests, including these failures, are saved in [the current smoke evidence](evidence/2026-10-24-foundry-agents-smoke.json).

| Request | Status / cards | Model turns | Tool executions | Input / output tokens | Request seconds |
| --- | --- | --- | --- | --- | --- |
| Simple fan, Spanish, second 1500 | Verified / 1 | 3 | 1 | 7312 / 341 | 7.0315 |
| Simple fan, English, second 1490 | Verified / 1 | 3 | 1 | 6422 / 314 | 6.7935 |
| Detailed commentator, Spanish, second 1500, favorite amber | Factual / 0 | 3 | 1 | 6229 / 792 | 10.0095 |
| Detailed fan, English, second 1500, favorite amber | Factual / 0 | 4 | 1 | 9390 / 639 | 10.0103 |
| First post-review attempt, simple Spanish | Factual / 0 | 5 | 2 | 9173 / 373 | 10.0138 |

These five requests are not a success-rate or tail-latency benchmark. Startup/authentication is separate; the ten-second cancellation deadline has small scheduling/cleanup overhead. Detailed output and repair are not reliably completed within the deadline; these cases safely withheld rejected prose. Semantic review can miss paraphrases beyond the targeted recovery-label guard. The earlier 20 October connection probe and the four pre-review measurements remain historical evidence only. The ten-second limit was not raised.

## Decisions and limits

- Execute task 4 on a new branch in the user's chosen current folder, keeping subsequent API/UI work separate. Cost: branch isolation does not create a separate filesystem checkout.
- Use compact per-story model inputs while retaining complete canonical facts outside the prompt. Cost: deeper event inspection requires explicit tool calls.
- One repair batch retains only accepted stories, with a conservative factual fallback on provider/budget failures. Cost: more retries could recover useful stories, but would exceed the chosen bounded workflow.
- The model is instructed to choose up to two detailed/professional stories to fit the output budget; deterministic contracts still support three. Cost: less breadth than the maximum card count.
- Async token warmup is connection startup, separate from the ten-second per-request deadline. Cost: cold startup latency remains additional and unmeasured here.
- Strict warning verification exposed two unclosed SQLite connections in a prior test's context-manager use; the test now explicitly closes them. No storage product behavior changes.
- Numeric provenance is deterministic; semantic correctness of unrestricted prose is reviewed by a model and is not a mathematical guarantee. The causal-language filter is intentionally conservative and cannot recognize every paraphrase. Spelled-out numerical claims and mismatched concepts also require semantic review. Live language quality and actual usefulness still require evaluation.
- The module accepts trusted internally built snapshots. Future API code must reconstruct them from bounded storage, never trust a user-submitted snapshot. Browser/API races, model-independent playback, cache isolation, cloud readiness and user studies remain later tasks.

Offline verification before independent review: 188 tests passed, one explicitly opted-in live test skipped, with Python warnings treated as errors; dependency consistency check passed. This count does not include a successful Azure model run.

## Independent review and fix verification

The fresh read-only reviewer independently ran the initial suite (188 passed, one live test skipped) and reported three Important findings, no Critical findings and no separate Minors. All entered one fix pass:

1. The real SDK serialized generation constraints unsupported by Azure. The provider-specific output schemas remove those keywords and defaults while preserving compiled local validation. The HTTP-transport regression checks the actual sent schema, and a separate case verifies local array limits still reject oversized output. This follows [Azure structured-output schema limitations](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs); the later live smoke accepted these schemas.
2. SDK-wrapped Pydantic/JSON output errors bypassed the repair path and lost usage when parsing failed. The adapter now classifies these as invalid output and records only aggregate usage in a response hook before structured parsing. A request-local ContextVar keeps concurrent calls separate. Actual-SDK regressions feed malformed JSON and schema-invalid writer output, then a repaired card and reviewer approval: four HTTP turns are observed, all 76 input and 28 output tokens are retained. Successful responses are not double-counted; concurrent request counters remain independent.
3. Decimal-digit matching missed numerical glyphs such as Tamil numerals and Roman symbols. Claim text and limitations now check Unicode numeric characters in both the original and normalized representations, outside trusted markers. The Tamil/Roman cases failed before the fix and pass afterward; circled digits and fractions remain covered.

The regression run before fixes had seven failures and five passing controls. After fixes all twelve targeted cases passed. Additional local-cap and concurrent-usage checks also passed. Final isolated-environment verification: **200 passed, one opted-in live test skipped**, with warnings treated as errors. Dependency installation, installed CLI entry point and `pip check` passed. The author verified the fixes with tests; no second independent review was performed.

Review boundaries were explicitly retained: authentication, actual model quality and latency need a live run; unchanged persistence remains task 2; API/browser/cache/playback/export and deployment are later tasks; free-prose semantic truth, spelled-out quantities and name/causal paraphrases require semantic review; deliberately forged internal snapshots are outside the trusted internal contract; the two-story generation target is an explicit scope decision. No deferred minor findings remain.

## Latency optimization verification (24 October)

The regressions cover role-specific wire schemas and strict local caps, compact-to-canonical support roundtrips, unknown references, request-local indexes, localized interpretation caveats, charged application prefetch, optional model-requested integer `read_facts`, the three-turn SDK happy path, malformed-output repair with aggregate usage, and reuse/near-expiry refresh of the actual authentication provider. These changes were tested RED to GREEN; no validation rule, deadline, model or budget limit was relaxed.

Final isolated pinned-environment suite: **211 passed, one opted-in live test skipped**, with warnings treated as errors, in 21.18 seconds. `pip check` and `git diff --check` passed. The separate opted-in bilingual Azure test passed in 19.64 seconds including startup and cleanup; per-request measurements and additional detailed cases are above. This optimization receives a fresh review of its delta; the earlier whole-agent review and its fixes remain historical records.

The fresh read-only reviewer examined `5ed5932..345fe34`, found no Critical, Important or Minor issues, and independently passed 50 targeted SDK/wire/orchestration/claim tests with warnings treated as errors. The reviewer reconstructed all four evidence snapshots, checked fact/marker roundtrips and value/window preservation, and verified canonical support and exact card rendering. No further live requests or full-suite rerun were performed by the reviewer. No fixes or deferred minor findings resulted.

Review boundaries remain explicit: unchanged storage/ingestion has its own review; API/UI/playback/cache/export/deployment and production ownership are later tasks; four samples cannot establish reliability under jitter or concurrent load; free-prose semantic review can still miss loose labels or paraphrases; broader caveats and direct event-only output require extending the provider format; internally forged snapshots are unsupported; live identity revocation/policy and Azure availability were not tested in the read-only review. These limits do not weaken the closed-snapshot evidence checks, and none is presented as verified production behavior.

## Whole-PR review and fixes before integration

At the participant's request, a fresh read-only reviewer examined the complete PR from `5b3eea9` to `d2f7fdb`, independently passed all 211 then-existing offline tests, and found two Important issues and one documentation Minor:

- The recorded recovery-label error above escaped model review. A focused regression reconstructs the actual high-recovery one-to-four and total-recovery five-to-five facts. Captured ambiguous English summary/overlay wording and a Spanish equivalent failed the new expectation before the fix; the validator now rejects them with `missing_metric_qualifier`. Qualified English/Spanish controls remain valid. Cost: some otherwise reasonable recovery paraphrases require the explicit canonical qualifier. This targets the demonstrated error, not universal semantic truth.
- Malformed reviewer output escaped to global fallback rather than the existing repair loop, also losing previously accepted cards if repair review failed. First-pass malformed JSON/schema and partial-acceptance/repair-review regressions failed before the fix and now pass. Actual-SDK transport cases also recover from malformed reviewer JSON/schema in five accounted model turns with all completed-response usage retained; the existing deadline/budgets and one repair attempt remain unchanged.
- The README's stale reauthentication notice was corrected.

After the fix pass: **221 offline tests passed, one opted-in live test skipped**, warnings treated as errors, in 20.63 seconds; dependency consistency passed. The subsequent unchanged bilingual live test passed in 19.21 seconds including startup/cleanup, after the recorded failed attempt. Current professional/detail fallback observations are explicitly retained above. No second reviewer was dispatched; tests verify the fixes. No review findings are deferred. Integration readiness means the bounded, guarded implementation is ready to merge, not reliable professional narrative generation or complete application readiness.
