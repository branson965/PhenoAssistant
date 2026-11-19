"""No-inference-cost OpenRouter key/model/pricing check for Phase 8.

Runs GET /api/v1/key and GET /api/v1/models only. This script never invokes
a completion endpoint, stores credentials, or prints a secret. Its cost model
is prospective, not a substitute for measured token usage or hard key limits.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_ROOT = "https://openrouter.ai/api/v1"
LUNA = "openai/gpt-5.6-luna"
SOL = "openai/gpt-5.6-sol"


def get_json(path: str, *, api_key: str | None = None) -> dict:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    request = Request(API_ROOT + path, headers=headers)
    try:
        with urlopen(request, timeout=25) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(
            "OpenRouter request to " + path + " failed with HTTP "
            + str(exc.code) + " (response body suppressed)"
        ) from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            "OpenRouter request to " + path + " failed due to transport/network error"
        ) from None
    except (ValueError, TypeError):
        raise RuntimeError(
            "OpenRouter returned invalid JSON for " + path
        ) from None


def extract_prices(payload: dict) -> dict[str, tuple[Decimal, Decimal]]:
    """Return USD/token prompt and completion prices for exact study slugs."""
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("models response does not contain a data list")
    found: dict[str, tuple[Decimal, Decimal]] = {}
    for item in rows:
        if not isinstance(item, dict) or item.get("id") not in (LUNA, SOL):
            continue
        pricing = item.get("pricing")
        if not isinstance(pricing, dict):
            raise ValueError("missing pricing for " + str(item.get("id")))
        try:
            prompt = Decimal(str(pricing["prompt"]))
            completion = Decimal(str(pricing["completion"]))
        except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid pricing for " + str(item.get("id"))) from exc
        if not prompt.is_finite() or not completion.is_finite() or prompt < 0 or completion < 0:
            raise ValueError("unusable prices for " + str(item.get("id")))
        found[item["id"]] = (prompt, completion)
    if set(found) != {LUNA, SOL}:
        raise ValueError("one or both predeclared models absent from public catalog")
    return found


def estimate_cost(
    price: tuple[Decimal, Decimal],
    *,
    cases: int,
    conditions: int,
    seeds: int,
    rounds: int,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    calls = cases * conditions * seeds * rounds
    return Decimal(calls) * (
        Decimal(input_tokens) * price[0]
        + Decimal(output_tokens) * price[1]
    )


def budget_plan(
    prices: dict[str, tuple[Decimal, Decimal]],
    *,
    available_usd: Decimal,
    luna_cases: int = 12,
    sol_cases: int = 4,
    input_tokens: int = 4000,
    output_tokens: int = 2048,
) -> dict[str, Decimal]:
    """Estimate 9 Luna conditions and 3 Sol conditions, 3 seeds, <=2 rounds."""
    if available_usd <= 0 or any(
        n < 1 for n in (luna_cases, sol_cases, input_tokens, output_tokens)
    ):
        raise ValueError("budget and dimensions must be positive")
    if output_tokens > 2048:
        raise ValueError("output token estimate exceeds frozen runtime limit")
    luna = estimate_cost(
        prices[LUNA], cases=luna_cases, conditions=9, seeds=3, rounds=2,
        input_tokens=input_tokens, output_tokens=output_tokens,
    )
    sol = estimate_cost(
        prices[SOL], cases=sol_cases, conditions=3, seeds=3, rounds=2,
        input_tokens=input_tokens, output_tokens=output_tokens,
    )
    # Retain >=$1 of user-reported balance for unforeseen variance and preflight.
    ceiling = available_usd - Decimal("1.00")
    return {
        "luna_usd": luna,
        "sol_usd": sol,
        "total_usd": luna + sol,
        "ceiling_usd": ceiling,
        "headroom_usd": ceiling - (luna + sol),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reported-balance-usd", type=Decimal, required=True)
    parser.add_argument("--luna-cases", type=int, default=12)
    parser.add_argument("--sol-cases", type=int, default=4)
    parser.add_argument("--estimated-input-tokens", type=int, default=4000)
    parser.add_argument("--estimated-output-tokens", type=int, default=2048)
    args = parser.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        print("PHASE8_BUDGET_CHECK_PASS=false")
        print("PHASE8_BUDGET_ERROR=OPENROUTER_API_KEY not set")
        return 2
    try:
        key_data = get_json("/key", api_key=key).get("data")
        if not isinstance(key_data, dict):
            raise ValueError("key endpoint returned no key information")
        prices = extract_prices(get_json("/models"))
        plan = budget_plan(
            prices,
            available_usd=args.reported_balance_usd,
            luna_cases=args.luna_cases,
            sol_cases=args.sol_cases,
            input_tokens=args.estimated_input_tokens,
            output_tokens=args.estimated_output_tokens,
        )
        raw_remaining = key_data.get("limit_remaining")
        key_remaining = (
            "not-set-or-unlimited"
            if raw_remaining is None
            else str(Decimal(str(raw_remaining)))
        )
        # A key's remaining credit cap is NOT the account balance. Do not
        # pretend /api/v1/key can reveal total account credits.
        print("PHASE8_KEY_AUTH_VALID=true")
        print("PHASE8_MODEL_LUNA_CATALOGUE_PRESENT=true")
        print("PHASE8_MODEL_SOL_CATALOGUE_PRESENT=true")
        print("PHASE8_KEY_LIMIT_REMAINING_USD=" + key_remaining)
        print("PHASE8_ACCOUNT_BALANCE_SOURCE=user-reported-not-api-verified")
        print("PHASE8_REPORTED_BALANCE_USD=" + str(args.reported_balance_usd))
        print("PHASE8_LUNA_INPUT_PER_MILLION_USD=" + str(prices[LUNA][0] * 1000000))
        print("PHASE8_LUNA_OUTPUT_PER_MILLION_USD=" + str(prices[LUNA][1] * 1000000))
        print("PHASE8_SOL_INPUT_PER_MILLION_USD=" + str(prices[SOL][0] * 1000000))
        print("PHASE8_SOL_OUTPUT_PER_MILLION_USD=" + str(prices[SOL][1] * 1000000))
        print("PHASE8_ASSUMED_INPUT_TOKENS_PER_ROUND=" + str(args.estimated_input_tokens))
        print("PHASE8_ASSUMED_OUTPUT_TOKENS_PER_ROUND=" + str(args.estimated_output_tokens))
        print("PHASE8_ESTIMATED_LUNA_USD=" + str(plan["luna_usd"]))
        print("PHASE8_ESTIMATED_SOL_USD=" + str(plan["sol_usd"]))
        print("PHASE8_ESTIMATED_TOTAL_USD=" + str(plan["total_usd"]))
        print("PHASE8_PILOT_COST_CEILING_USD=" + str(plan["ceiling_usd"]))
        print("PHASE8_ESTIMATED_HEADROOM_USD=" + str(plan["headroom_usd"]))
        print("PHASE8_COST_ESTIMATE_EXCLUDES=transport_retries,non_token_fees,variable_context")
        print("PHASE8_OUTCOME_BEARING=false")
        passes = (
            plan["headroom_usd"] >= 0
            and (
                raw_remaining is None
                or Decimal(str(raw_remaining)) >= plan["total_usd"]
            )
        )
        print("PHASE8_BUDGET_CHECK_PASS=" + str(passes).lower())
        return 0 if passes else 3
    except (RuntimeError, ValueError, ArithmeticError) as exc:
        # Keep messages limited to fixed endpoint paths / model slugs.
        print("PHASE8_BUDGET_CHECK_PASS=false")
        print("PHASE8_BUDGET_ERROR=" + str(exc))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
