# Grounded agents: implementation and validation

Scope: task 4 of the approved plan. The analyst, writer and reviewer use one closed snapshot and explicit typed handoffs. This delivery does not add the API, web application, browser state, hosted agents or deployment. The previous persistent-ingestion PR is merged into master.

## Workflow

1. Reconstruct canonical facts and supported patterns using the existing deterministic engine. Every supplied fact is checked against a fresh calculation for its own interval; forged values or references cannot become trusted facts by reusing an identifier.
2. The analyst uses read-only snapshot tools to select candidate IDs. A simple fan receives one selected story; the model is instructed to select up to two for detailed fans or commentators, under the public cap of three.
3. The writer returns typed cards containing observed or tentative interpretation claims. Four claims cover the headline, explanation, suggested line and overlay. Each cites its own story's canonical facts/events.
4. Deterministic checks reject unknown references, unrelated support, literal Unicode numeric symbols (before and after normalization), raw known match names, invalid markers, duplicate claim IDs, unsupported interpretations, strong causal wording and overlays longer than 140 rendered characters. Unicode marker normalization uses the same representation for validation and rendering.
5. The reviewer judges metric labels, team/window correspondence, language, audience, qualifiers and interpretation. Rejected cards get one batch repair attempt; accepted cards survive while twice-rejected stories are discarded. The summary is assembled only from accepted lines. Invalid JSON also gets at most one writer repair.
6. Final validation checks the public summary, cards, limitations and overlays against their validated claims and canonical story intervals. Rendered fields cannot bypass validation by carrying different text. No rejected prose is inserted into a repair prompt or public rejection reason.

The default CLI is factual-only. It renders a localized count of shots from trusted facts and identifies limited observations when applicable. It does not fabricate a standout pattern or present template output as a successful agent run. Empty or unsupported-pattern contexts do not trigger unnecessary model calls.

## Tools and isolation

`list_candidates`, `read_facts` and `inspect_events` require exactly the authorized cutoff. Unknown facts, unknown events and future cutoffs are denied. Evidence inspection is limited to ten requested IDs at a time. Compact tool facts retain their canonical ID, value, interval, sample/denominator, method and limitations, with explicit `event_sample_ids` and `evidence_count`; full evidence remains resolvable in the closed snapshot.

Each request has a new tools registry, budget, trace ID and typed payloads. Each Foundry role creates a fresh Agent; there are no reused conversation/session IDs, previous-response IDs, persistent model memory, web search or hosted tools. A shared inference client may reuse its network connection, while the role history remains call-local. Static fictional rosters are allowed context, including names of substitutes; they do not reveal later match events.

Public traces contain role/decision labels, allowed tool names, attempted provider turns, requested-tool counts, aggregate provider-reported token usage captured before structured parsing and elapsed request time. They contain no prompts, private reasoning, token credentials or raw provider error messages. Provider startup/authentication is reported separately from an in-request fallback.

## Foundry and limits

The adapter uses Microsoft Agent Framework `Agent` and `FoundryChatClient`, a Pydantic `response_format`, the existing deployed model and Azure CLI identity. Connection setup uses an asynchronous credential and warms the token before per-request timing. No resources or model deployments are created. HTTP retries are disabled.

| Budget | Limit | Enforcement |
| --- | --- | --- |
| Model turns | Seven across all roles and repairs | Chat middleware reserves before each SDK provider turn, including the continuation after a tool result. |
| Tools | Eight across a request | Middleware reserves model-requested calls before execution, including unknown names or invalid arguments. Scoped wrappers do not charge the same call twice. Direct offline tools enforce the same budget. |
| Output | 1200 tokens per provider turn | Run options serialize into the actual SDK request body. |
| Request duration | Ten seconds | Request-local monotonic deadline and cancellable asynchronous role calls. Timeout returns identified factual output. |

These are operational bounds, not a monetary cap or an assurance of successful generation within ten seconds. Cold startup/token acquisition is extra. The SDK middleware shape was checked against the [Microsoft middleware documentation](https://learn.microsoft.com/en-us/agent-framework/agents/middleware/chat-middleware); the provider uses the [Foundry application-owned agent pattern](https://learn.microsoft.com/en-us/agent-framework/agents/providers/microsoft-foundry).

## Tests and current live status

Tests exercise invented facts, unknown/future events, forged metrics, malformed JSON, two reviewer rejections, partial acceptance, one repair, timeout, provider-error sanitization, profile selection, bilingual factual output, request isolation, Unicode markers, public-text tampering and preservation of interpretation limitations. A real SDK plus fake HTTP transport verifies provider-turn counting, aggregate usage, no retained earlier sentinel, no previous response/conversation IDs, actual output/store options and a budget stopping the next network turn. The SDK transport tests never contact Azure.

The live test is opted in with `RUN_FOUNDRY_LIVE=1`. It requests Spanish context at second 1500 and English context at second 1490 through the same inference client with fresh role contexts; it requires verified Foundry output, all three roles, actual tools, usage and distinct cutoffs. Reports go to ignored `tmp/foundry-agents/`.

On 23 October, the first live attempt stopped during token acquisition with Azure error `AADSTS530035` (blocked by security defaults). No model request was made in that attempt. Azure CLI account metadata was accessible, which does not itself demonstrate that a fresh inference token can be obtained. The subsequent device-code attempt was cancelled after sign-in was denied; no security policies were changed.

On 24 October, interactive sign-in on the participant's PC succeeded and a fresh Foundry inference token was obtained. The opted-in live test then reached the real deployment: the analyst called `list_candidates`, completed its selection and handed off to the writer. The request reached its ten-second deadline during writing and correctly returned identified factual fallback: zero story cards, rejection `deadline`, three attempted model turns, one tool call, 6003 reported input tokens and 98 reported output tokens from completed responses, and 10.003 seconds of request time. Usage from a cancelled/incomplete response is not represented by those counters. The test failed its required verified-output assertion and therefore did not run the second English request. Reports remain in ignored `tmp/foundry-agents/`.

Authentication is resolved for this session, but successful live three-role output, bilingual isolation and acceptable generation latency remain pending. The earlier 20 October single-agent connection probe remains historical evidence only. The ten-second limit was not raised to make the live test pass.

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

1. The real SDK serialized generation constraints unsupported by Azure. `FoundryOutput` now removes those keywords and defaults from its provider-specific Pydantic JSON Schema while preserving the original compiled local validation. The HTTP-transport regression checks the actual sent schema, and a separate case verifies local array limits still reject oversized output. This follows [Azure structured-output schema limitations](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs); live endpoint acceptance still needs the pending smoke.
2. SDK-wrapped Pydantic/JSON output errors bypassed the repair path and lost usage when parsing failed. The adapter now classifies these as invalid output and records only aggregate usage in a response hook before structured parsing. A request-local ContextVar keeps concurrent calls separate. Actual-SDK regressions feed malformed JSON and schema-invalid writer output, then a repaired card and reviewer approval: four HTTP turns are observed, all 76 input and 28 output tokens are retained. Successful responses are not double-counted; concurrent request counters remain independent.
3. Decimal-digit matching missed numerical glyphs such as Tamil numerals and Roman symbols. Claim text and limitations now check Unicode numeric characters in both the original and normalized representations, outside trusted markers. The Tamil/Roman cases failed before the fix and pass afterward; circled digits and fractions remain covered.

The regression run before fixes had seven failures and five passing controls. After fixes all twelve targeted cases passed. Additional local-cap and concurrent-usage checks also passed. Final isolated-environment verification: **200 passed, one opted-in live test skipped**, with warnings treated as errors. Dependency installation, installed CLI entry point and `pip check` passed. The author verified the fixes with tests; no second independent review was performed.

Review boundaries were explicitly retained: authentication, actual model quality and latency need a live run; unchanged persistence remains task 2; API/browser/cache/playback/export and deployment are later tasks; free-prose semantic truth, spelled-out quantities and name/causal paraphrases require semantic review; deliberately forged internal snapshots are outside the trusted internal contract; the two-story generation target is an explicit scope decision. No deferred minor findings remain.
