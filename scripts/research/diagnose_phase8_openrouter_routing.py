"""Read-only OpenRouter capability probe following Phase 8A parameter 404.

No completions, no paid inference, no local files, no secret output. Lists
model-level capabilities, and endpoint-level capabilities if the key is
authorized to view them. Does not alter the frozen model/runtime plan.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-5.6-luna"

# Every entry is a *hypothesis* about routing, not a statement that the
# Agent Framework actually transmitted this parameter.
PARAMETER_CANDIDATES = (
    "tools",
    "tool_choice",
    "seed",
    "reasoning",
    "max_tokens",
    "max_completion_tokens",
    "parallel_tool_calls",
)


def get_json(path: str, key: str) -> tuple[int, dict | None]:
    request = Request(
        API_ROOT + path,
        headers={"Authorization": "Bearer " + key, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=25) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        # Suppress the entire API error body so no token/header/user metadata
        # can accidentally appear in chat, terminal capture, or logs.
        return exc.code, None
    except (URLError, TimeoutError, ValueError, TypeError):
        return 0, None


def model_summary(payload: dict) -> dict | None:
    rows = payload.get("data")
    if not isinstance(rows, list):
        return None
    model = next(
        (row for row in rows if isinstance(row, dict) and row.get("id") == MODEL),
        None,
    )
    if model is None:
        return None
    supported = model.get("supported_parameters")
    if not isinstance(supported, list):
        supported = []
    return {
        "model": MODEL,
        "supported_parameters": sorted(
            item for item in supported if isinstance(item, str)
        ),
        "parameter_candidate_membership": {
            param: param in supported for param in PARAMETER_CANDIDATES
        },
        "top_level_reasoning": model.get("reasoning") if isinstance(model.get("reasoning"), dict) else None,
    }


def endpoint_summary(payload: dict) -> list[dict] | None:
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("endpoints"), list):
        return None
    summaries = []
    for endpoint in data["endpoints"]:
        if not isinstance(endpoint, dict):
            continue
        supported = endpoint.get("supported_parameters")
        if not isinstance(supported, list):
            supported = []
        supported_set = set(item for item in supported if isinstance(item, str))
        summaries.append({
            "provider_tag": str(endpoint.get("tag", "<unknown>"))[:120],
            "provider_name": str(endpoint.get("provider_name", "<unknown>"))[:120],
            "name": str(endpoint.get("name", "<unknown>"))[:120],
            "parameter_candidate_membership": {
                param: param in supported_set for param in PARAMETER_CANDIDATES
            },
            "supports_tool_choice": endpoint.get("supports_tool_choice"),
        })
    return summaries


def main() -> int:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        print("PHASE8_ROUTING_DIAGNOSTIC_PASS=false")
        print("PHASE8_ROUTING_REASON=key-not-set")
        return 2
    status, models = get_json("/models", key)
    if status != 200 or models is None:
        print("PHASE8_ROUTING_DIAGNOSTIC_PASS=false")
        print("PHASE8_ROUTING_MODELS_HTTP=" + str(status))
        return 3
    summary = model_summary(models)
    if summary is None:
        print("PHASE8_ROUTING_DIAGNOSTIC_PASS=false")
        print("PHASE8_ROUTING_REASON=model-not-in-catalogue")
        return 4
    print("PHASE8_ROUTING_MODEL_SUMMARY=" + json.dumps(summary, sort_keys=True))
    status, endpoints = get_json("/models/openai/gpt-5.6-luna/endpoints", key)
    print("PHASE8_ROUTING_ENDPOINTS_HTTP=" + str(status))
    if status == 200 and endpoints is not None:
        rows = endpoint_summary(endpoints)
        if rows is None:
            print("PHASE8_ROUTING_ENDPOINTS_FORMAT=unexpected")
        else:
            print("PHASE8_ROUTING_ENDPOINT_COUNT=" + str(len(rows)))
            for index, row in enumerate(rows):
                print(
                    "PHASE8_ROUTING_ENDPOINT_"
                    + str(index)
                    + "="
                    + json.dumps(row, sort_keys=True)
                )
    elif status == 403:
        print("PHASE8_ROUTING_ENDPOINTS_ACCESS=not-authorized-for-endpoint-details")
    else:
        print("PHASE8_ROUTING_ENDPOINTS_ACCESS=unavailable")
    print("PHASE8_ROUTING_REQUEST_SHAPE=not-yet-captured")
    print("PHASE8_ROUTING_OUTCOME_BEARING=false")
    print("PHASE8_ROUTING_PAID_INFERENCE=false")
    print("PHASE8_ROUTING_DIAGNOSTIC_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
