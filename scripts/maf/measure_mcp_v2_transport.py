#!/usr/bin/env python3
"""Measure bounded direct-versus-MCP v2 transport overhead.

This is an interface microbenchmark, not an end-to-end scientific workload benchmark.
It isolates the MCP boundary with the deterministic calculator tool and reports direct,
one-shot ("cold-session"), and persistent-session ("warm-session") timings.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import statistics
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.client_v2 import (
    MCP_PROTOCOL_VERSION,
    McpV2Session,
    call_structured_tool,
)
from phenoassistant_mcp.server_v2 import build_phase6_mcp_server


def calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    operations = {
        "+": a + b,
        "-": a - b,
        "*": a * b,
        "/": int(a / b),
    }
    return operations[operator]


def anova(*args, **kwargs):
    del args, kwargs
    return [{"Source": "Interaction"}]


def tukey(*args, **kwargs):
    del args, kwargs
    return [{"A": "control", "B": "treated"}]


def summarise(samples_ns: list[int]) -> dict[str, float]:
    values_ms = [
        value / 1_000_000
        for value in samples_ns
    ]
    ordered = sorted(values_ms)
    p95_index = max(
        0,
        min(
            len(ordered) - 1,
            int(0.95 * len(ordered)) - 1,
        ),
    )

    return {
        "mean_ms": statistics.fmean(values_ms),
        "median_ms": statistics.median(values_ms),
        "p95_ms": ordered[p95_index],
        "min_ms": min(values_ms),
        "max_ms": max(values_ms),
    }


def measure_direct(
    *,
    warmup: int,
    trials: int,
) -> list[int]:
    for _ in range(warmup):
        assert calculator(7, 5, "+") == 12

    samples: list[int] = []

    for _ in range(trials):
        start = time.perf_counter_ns()
        result = calculator(7, 5, "+")
        elapsed = time.perf_counter_ns() - start

        assert result == 12
        samples.append(elapsed)

    return samples


async def measure_one_shot(
    server,
    *,
    warmup: int,
    trials: int,
) -> list[int]:
    arguments = {
        "a": 7,
        "b": 5,
        "operator": "+",
    }

    for _ in range(warmup):
        result = await call_structured_tool(
            server,
            "calculator",
            arguments,
        )
        assert result == {"result": 12}

    samples: list[int] = []

    for _ in range(trials):
        start = time.perf_counter_ns()
        result = await call_structured_tool(
            server,
            "calculator",
            arguments,
        )
        elapsed = time.perf_counter_ns() - start

        assert result == {"result": 12}
        samples.append(elapsed)

    return samples


async def measure_persistent(
    server,
    *,
    warmup: int,
    trials: int,
) -> list[int]:
    arguments = {
        "a": 7,
        "b": 5,
        "operator": "+",
    }

    async with McpV2Session(server) as session:
        for _ in range(warmup):
            result = await session.call_structured_tool(
                "calculator",
                arguments,
            )
            assert result == {"result": 12}

        samples: list[int] = []

        for _ in range(trials):
            start = time.perf_counter_ns()
            result = await session.call_structured_tool(
                "calculator",
                arguments,
            )
            elapsed = time.perf_counter_ns() - start

            assert result == {"result": 12}
            samples.append(elapsed)

    return samples


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    if args.warmup < 0:
        raise ValueError("--warmup must be non-negative")

    if args.trials <= 0:
        raise ValueError("--trials must be positive")

    server = build_phase6_mcp_server(
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    direct = measure_direct(
        warmup=args.warmup,
        trials=args.trials,
    )
    one_shot = await measure_one_shot(
        server,
        warmup=args.warmup,
        trials=args.trials,
    )
    persistent = await measure_persistent(
        server,
        warmup=args.warmup,
        trials=args.trials,
    )

    direct_summary = summarise(direct)
    one_shot_summary = summarise(one_shot)
    persistent_summary = summarise(persistent)

    report: dict[str, Any] = {
        "schema": "phenoassistant-phase6e-mcp-transport-overhead-v1",
        "scope": (
            "transport-only calculator microbenchmark; "
            "not end-to-end scientific latency"
        ),
        "protocol": MCP_PROTOCOL_VERSION,
        "python": platform.python_version(),
        "packages": {
            "mcp": version("mcp"),
            "agent-framework-core": version("agent-framework-core"),
            "agent-framework-openai": version("agent-framework-openai"),
        },
        "warmup": args.warmup,
        "trials": args.trials,
        "direct": direct_summary,
        "mcp_one_shot_session": one_shot_summary,
        "mcp_persistent_session": persistent_summary,
        "median_overhead_ms": {
            "one_shot_minus_direct": (
                one_shot_summary["median_ms"]
                - direct_summary["median_ms"]
            ),
            "persistent_minus_direct": (
                persistent_summary["median_ms"]
                - direct_summary["median_ms"]
            ),
        },
        "parity": {
            "expected_result": 12,
            "all_paths_match": True,
        },
    }

    payload = json.dumps(
        report,
        indent=2,
        sort_keys=True,
    )

    if args.output is not None:
        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        args.output.write_text(
            payload + "\n",
            encoding="utf-8",
        )

    print(payload)
    print("PHASE6E_MCP_TRANSPORT_BENCHMARK_PASS=true")


if __name__ == "__main__":
    asyncio.run(main())
