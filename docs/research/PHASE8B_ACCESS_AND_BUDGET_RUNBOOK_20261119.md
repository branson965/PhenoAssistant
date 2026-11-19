# Phase 8B: New OpenRouter Key, No-Charge Budget Gate and First Paid Preflight

**Date:** 2026-11-19  
**Status:** KEY_AUTH_AND_MODEL_CATALOGUE_VERIFIED; PAID_MAF_TOOL_PREFLIGHT_PENDING  
**Scope:** post-Phase-7-v0.2, strictly pre-outcome  
**User-reported starting credit:** $9 USD (not independently verified)

## What changed and what did not

The researcher now reports an OpenRouter API key with $9 credit. This clears
the *key-in-hand* obstacle, but by itself does **not** establish authentication,
provider billing authorisation, model/tool support, sufficient evaluation
budget or scientific performance.

The prior provider gate also requires confirmation that this is the **approved
credential ownership/provider/billing route**, and that the predeclared
Luna/Sol study models are approved. Do not silently waive that confirmation.

All 22 Phase 7 v0.2 frozen scientific-method/protocol files remain unchanged.
No scientific outcomes have been obtained and the hidden benchmark is sealed.
The latest evidence-weighted progress remains overall 51%, Phase 8 20%, 6/9
phases fully closed.

## OpenRouter listed model costs at drafting time

- `openai/gpt-5.6-luna`: **$0.20/M input, $1.20/M output** (authenticated model-catalogue check on 2026-11-19).
- `openai/gpt-5.6-sol`: **$4.00/M input, $20.00/M output** (authenticated model-catalogue check on 2026-11-19).

Prices can change. The public model catalogue is read at run time and its
observed exact model prices must replace these estimates before paid work.

## First gate: no billed inference

Script: `scripts/research/check_phase8_openrouter_budget.py`

The script:
- reads `OPENROUTER_API_KEY` from the current shell;
- calls only `GET /api/v1/key` and `GET /api/v1/models`;
- verifies key authentication and the exact pinned model IDs;
- captures catalogue pricing and optional per-key credit cap;
- uses the researcher-reported account balance as an **assumption**, not a
  verified account-balance fact (the credit-balance endpoint requires a
  management key);
- prints no key, request headers or raw API response;
- makes no billed generation or scientific call;
- fails closed on bad prices, missing models, unexpected errors, or a negative
  estimated budget headroom.

Planning envelope: Luna 12 qualification scenarios x 9 conditions x 3 seeds
x <=2 rounds; Sol 4 qualification scenarios x 3 conditions x 3 seeds
x <=2 rounds. Estimate assumes 4,000 input tokens and 2,048 output tokens
per model roundtrip, with a minimum $1 unallocated buffer. These numbers are
planning assumptions; retries, longer context, any other fees, and actual
token counts may raise costs. **Do not launch the full Sol run on a $9
budget from an estimate alone.**

## Plato operations

1. In the existing Plato SSH session, pull the current
   `experiments/ijcai2027` branch **as a standalone interactive command**
   (the Git SSH passphrase prompt may consume later pasted commands).

   ```bash
   cd ~/PhenoAssistant
   git branch --show-current
   git pull --ff-only origin experiments/ijcai2027
   ```

   Expected branch `experiments/ijcai2027`. Stop on a mismatch;
   do not switch branches while preserving uncommitted work.

2. Run the entirely offline regression suite:

   ```bash
   cd ~/PhenoAssistant
   ~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
     tests/research/test_phase8_budget_preflight.py \
     tests/research/test_phase8_preflight.py
   ```

3. Enter the API key **interactively without shell history or screen echo**:

   ```bash
   read -r -s -p "OpenRouter API key (hidden): " OPENROUTER_API_KEY
   printf '\n'
   export OPENROUTER_API_KEY
   ```

   Paste the secret only in response to the prompt. Do not enter it as
   `export OPENROUTER_API_KEY=...`, send it in chat, store it in a file, or
   commit it. The shell variable exists only for this session.

4. Run the zero-inference-cost gate:

   ```bash
   ~/.local/envs/phenoassistant-phase6-mcp/bin/python \
     scripts/research/check_phase8_openrouter_budget.py \
     --reported-balance-usd 9 \
     --luna-cases 12 \
     --sol-cases 4
   ```

   Required marker: `PHASE8_BUDGET_CHECK_PASS=true`.
   The marker is **permission to consider a single paid infrastructure
   preflight**, not to launch the estimated set of experiments.

5. After confirming supervisor-approved credential/billing/model route,
   execute exactly the existing **non-scientific** echo-tool preflight:

   ```bash
   ~/.local/envs/phenoassistant-phase6-mcp/bin/python \
     scripts/research/validate_ijcai_openrouter_preflight.py
   ```

   Required markers:
   `PHASE8A_LIVE_PREFLIGHT_OUTCOME_BEARING=false` and
   `PHASE8A_LIVE_OPENROUTER_MAF_PREFLIGHT_PASS=true`.
   Capture only the safe printed evidence. Stop on model/provider
   parameter mismatch, 402/429 or unexpected tool-call behaviour.
   Do **not** try alternate providers or alter protocol settings ad hoc.

6. After the session:

   ```bash
   unset OPENROUTER_API_KEY
   ```

## Strict post-preflight gates

After the paid echo succeeds, record:
- observed model identity/fingerprint, model parameter acceptance;
- actual OpenRouter activity cost or key usage delta (no credentials);
- actual balance/headroom and preflight evidence;
- whether supervisor/provider/billing route was approved.

Then create a **new final runtime-freeze record**, retaining the October
pre-outcome candidate unchanged. Only after that, build and qualify the
outcome-bearing C0-C8 harness. Do not use the 12-case qualification set
as proof of real distribution-shift generalisation. Schedule the stronger
Sol breadth subset only after actual measured per-round spend is known.

**Scientific execution remains forbidden** until the formal Phase 8A provider
conditions and non-scientific preflight have passed.


## Observed Plato results — 2026-11-19

The researcher ran the exact gate on Plato on branch
`experiments/ijcai2027`. The repository fast-forwarded from
`2c9717a` to `24ba5f1`; the targeted offline suite passed
**17/17** in 3.54 seconds.

Observed safe marker set, transcribed without credentials:

```text
PHASE8_KEY_AUTH_VALID=true
PHASE8_MODEL_LUNA_CATALOGUE_PRESENT=true
PHASE8_MODEL_SOL_CATALOGUE_PRESENT=true
PHASE8_KEY_LIMIT_REMAINING_USD=50
PHASE8_ACCOUNT_BALANCE_SOURCE=user-reported-not-api-verified
PHASE8_REPORTED_BALANCE_USD=9
PHASE8_LUNA_INPUT_PER_MILLION_USD=0.2000000
PHASE8_LUNA_OUTPUT_PER_MILLION_USD=1.2000000
PHASE8_SOL_INPUT_PER_MILLION_USD=4.000000
PHASE8_SOL_OUTPUT_PER_MILLION_USD=20.00000
PHASE8_ESTIMATED_LUNA_USD=2.1109248
PHASE8_ESTIMATED_SOL_USD=4.101120
PHASE8_ESTIMATED_TOTAL_USD=6.2120448
PHASE8_PILOT_COST_CEILING_USD=8.00
PHASE8_ESTIMATED_HEADROOM_USD=1.7879552
PHASE8_OUTCOME_BEARING=false
PHASE8_BUDGET_CHECK_PASS=true
```

**Interpretation:** Authentication and exact study-model catalogue
availability pass. The 50 USD number is a **per-key spending allowance**,
not a verified account credit balance; budget against the reported
9 USD until confirmed otherwise. The $6.21 forecast assumes up to two
roundtrips per trial and is neither measured spend nor clearance to execute
the entire pilot. No tool-call completion has been observed yet.

**Next:** once supervisor/provider/billing approval of this key and model
route is confirmed, execute exactly one non-scientific paid echo-tool
preflight using the existing script. Preserve the printed safe markers;
do not execute a scientific scenario yet. The paper progress score remains
51% overall, 20% Phase 8, 6/9 phases fully closed.


## Live preflight failure and controlled diagnostic — 2026-11-19

The first `scripts/research/validate_ijcai_openrouter_preflight.py` live
attempt on Plato returned **HTTP 404** from OpenRouter:

```text
No endpoints found that can handle the requested parameters
failed_routing_step=Filter by Parameters
initial_endpoints=8
after_regional_filter=5
after_tier_filter=3
```

This is **not** a successful MAF tool-call preflight. It also is not
evidence that the scientific PhenoGuard method failed, because no
scientific scenario was executed. OpenRouter's parameter enforcement
refused the request before the provider accepted it. The exact
offending request parameter has **not** been established.

The preflight includes a forced `tool_choice="required"`, seed 2026,
reasoning effort medium, token cap, a single tool, and
`provider.require_parameters=true`. Do not guess which one caused the
404, disable strict parameter matching, or silently change
provider/model/seed policy.

New non-inference diagnostic:

```bash
cd ~/PhenoAssistant
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_routing_diagnostic.py \
  tests/research/test_phase8_preflight.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/diagnose_phase8_openrouter_routing.py
```

It uses authenticated GET `/models` for exact model supported
parameters and attempts authenticated GET
`/models/openai/gpt-5.6-luna/endpoints` for per-endpoint
supported-parameter sets. It prints no key and executes no model.
The endpoints endpoint may require management-key access (403);
in that case retain the model-level signal but **do not** infer which
provider endpoint supports the full parameter combination.

After inspecting the diagnostic output, the next action is to
produce a bounded, explicit *pre-outcome* compatibility remedy, with
a new runtime-candidate version if any study model/runtime control
changes. Preserve the October candidate and the failure evidence.
Only rerun the paid echo after the concrete incompatibility has
been identified and the approved provider route is retained.

**Status:** LIVE_ECHO_FAILED_PARAMETER_ROUTING; diagnostic pending.
**Progress:** unchanged (overall 51%, Phase 8 20%, 6/9 fully closed).


## Endpoint capability inspection passed, wire shape remains to prove — 2026-11-19

Plato fast-forwarded from `24ba5f1` to `013e549`; the targeted
diagnostic suite passed **16/16**. The authenticated OpenRouter catalogue
reported Luna model-level support for `tools`, `tool_choice`, `seed`,
`reasoning`, `max_tokens`, and `max_completion_tokens`, but **did not
advertise** `parallel_tool_calls`. Five individual endpoints were returned,
including `openai`, `openai/flex` and `openai/fast`. All three listed
OpenAI endpoints support the former controls and none advertises
`parallel_tool_calls`. Azure lists `max_completion_tokens` rather than
`max_tokens`, which is another reason not to bypass the provider pin.

The first error's endpoint counts are dynamic filters and need not equal
the five endpoints exposed in the detail query.

**Leading hypothesis:** MAF's `allow_multiple_tool_calls=False` may be
translated into a transmitted `parallel_tool_calls=false`, triggering the
strict parameter filter. This is *not yet proven*. A fully qualified
pre-outcome change requires seeing the actual wire-level JSON control names,
not guessing from the MAF options or endpoint catalogue.

New no-network, no-charge capture script:
`scripts/research/capture_phase8_maf_request_shape.py`.
It runs the exact existing preflight with a dummy credential, intercepts
`httpx.AsyncClient.send` before transmission, blocks socket connect,
prints only safe allowed parameter control metadata and payload key names,
and does not reveal prompts, schemas, messages or headers. It never
uses or transmits the user's real key.

Plato next gate:

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
```

Then, after completing any interactive Git SSH passphrase prompt:

```bash
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_request_shape_capture.py \
  tests/research/test_phase8_preflight.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/capture_phase8_maf_request_shape.py
```

Inspect `PHASE8_WIRE_SHAPE` and required
`PHASE8_WIRE_SHAPE_CAPTURE_PASS=true`,
`PHASE8_WIRE_SHAPE_PAID_INFERENCE=false`.
If `parallel_tool_calls` appears and is false, prepare a documented
wire-compatibility change which omits the unsupported API parameter
**while retaining application-side single-tool execution limits**,
then recapture and reverify the outgoing request. Do not weaken
`provider.require_parameters` or allow other providers silently.
If not present, diagnose the remaining control fields with exact
request/endpoint comparison before making a change.

Do not retry the paid live preflight or execute any scientific task until
the dry capture evidence validates the remedy. No Phase 8 scientific
outcome is claimed and completion percentages are unchanged.


## SDK source cross-check: two candidate option translations

The published Microsoft Agent Framework
`agent_framework_openai/_chat_completion_client.py` contains an
`OPTION_TRANSLATIONS` mapping of:

```python
"allow_multiple_tool_calls": "parallel_tool_calls"
"max_tokens": "max_completion_tokens"
```

The installed package is pinned to `agent-framework-openai==1.11.0`.
The published main-branch mapping is a strong diagnostic lead but **is
not a substitute for capturing this exact installed runtime**.

This raises two simultaneous routing suspects:

1. `parallel_tool_calls=false`: absent from the advertised OpenAI
   endpoint parameter sets;
2. `max_completion_tokens=512`: absent from the advertised
   `openai`/ `openai/fast`/`openai/flex` endpoint parameter sets,
   which instead list `max_tokens`.

The payload capture must check **both** fields. Changing only the
parallel-tools option may leave the request unroutable due to
`max_completion_tokens`.

The eventual pre-outcome compatibility remedy should preserve:
- exact Luna model and provider `openai` pin, no fallbacks;
- strict required-parameter routing;
- original token ceiling;
- one tool execution as an application-side hard limit;
- full recorded request-shape and newly frozen final runtime controls.

Do not submit further paid calls until the installed runtime's actual
request confirms the set of unsupported parameters.


## Exact post-MAF request captured, compatibility adapter staged (2026-11-19)

Plato fast-forwarded to `6f09554`. The offline wire-capture regression
suite passed **16/16**. The actual `agent-framework-openai==1.11.0`
generated HTTP request contained **both** endpoint-incompatible fields:

```text
max_completion_tokens=512
parallel_tool_calls=false
```

The remaining control fields were preserved and correct:
`model=openai/gpt-5.6-luna`, `seed=2026`,
`reasoning.effort=medium`, `tool_choice=required`,
`provider.order=[openai]`, `allow_fallbacks=false`,
`require_parameters=true`, `stream=false`, exactly one advertised
tool. The capture used a fake key and blocked transmission; no
inference charge.

The OpenAI-tagged Luna endpoints advertise `max_tokens`, but not
`max_completion_tokens` or `parallel_tool_calls`.

The exact two-field *interface compatibility* remedy is committed:

- `scripts/research/openrouter_compat.py` implements a fail-closed
  `httpx.AsyncBaseTransport` that enforces the Luna model identity,
  strict OpenAI routing, medium reasoning effort, 2026/2027/2028
  seed schedule, no transmitted temperature, token ceiling, and
  the permitted non-streaming request shape.
- At the final HTTP transport boundary it converts
  `max_completion_tokens: N` to `max_tokens: N`; it omits
  `parallel_tool_calls` **only when false**. An enabled
  parallel-tool request fails locally.
- Prompts, messages, tools, seed, routing, model and token *value*
  remain unchanged. MAF's `max_function_calls=1` and
  `allow_concurrent_invocation=false` stay in force.
- `scripts/research/validate_ijcai_openrouter_preflight.py`
  now constructs an injected `AsyncOpenAI` client with that
  compatibility transport. SDK automatic preflight retries
  are disabled.
- `scripts/research/capture_phase8_maf_request_shape.py`
  now intercepts at `httpx.AsyncHTTPTransport.handle_async_request`
  to capture the **post-adapter** request, not the pre-rewrite
  MAF request.
- `tests/research/test_phase8_openrouter_compat.py`
  adds negative-path guardrails and an actual MAF no-network
  integration assertion.

Local isolated `httpx` adapter tests passed **14/14** in the authoring
environment; the full MAF runtime integration tests must still
be run on Plato.

### Exact Plato validation before any paid retry

First run `git pull --ff-only origin experiments/ijcai2027` as a
standalone Git command and complete the SSH passphrase prompt.

Then:

```bash
cd ~/PhenoAssistant
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_openrouter_compat.py \
  tests/research/test_phase8_request_shape_capture.py \
  tests/research/test_phase8_preflight.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/capture_phase8_maf_request_shape.py
```

Required offline output:
- all targeted tests pass;
- `PHASE8_WIRE_SHAPE_CAPTURE_PASS=true`;
- `PHASE8_WIRE_SHAPE_PAID_INFERENCE=false`;
- request body includes `max_tokens=512`;
- request body contains **neither**
  `max_completion_tokens` nor `parallel_tool_calls`;
- strict provider pin and all other controls unchanged.

Do **not** retry the paid OpenRouter echo until those outputs pass.
After offline verification and confirmation of the approved
billing/provider/model route, run one paid non-scientific echo
using the existing script. The new wire-compatibility transport
is an explicitly documented pre-outcome interface change, **not**
a new scientific method or revised experimental condition.
Before any scientific scenario, freeze a newly content-addressed
final runtime candidate that records this adapter.
