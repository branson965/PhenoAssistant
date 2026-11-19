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
