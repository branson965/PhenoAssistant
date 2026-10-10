"""Prepare the pre-outcome IJCAI Phase 8 runtime-control candidate.

This script performs no LLM call and executes no scientific benchmark. It captures
the prospectively frozen model/runtime plan plus the local software/hardware identity.
It never reads or prints the OpenRouter API key.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from research.phenoguard import ControlledVariables

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "ijcai2027" / "runtime"
EXPERIMENT_DIR = ROOT / "experiments" / "ijcai2027"
PROMPT_CONTRACT = EXPERIMENT_DIR / "condition_prompt_contract.json"
MODEL_PLAN = EXPERIMENT_DIR / "model_plan.json"
RUNTIME_PLAN = EXPERIMENT_DIR / "runtime_plan.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def aggregate_sha256(paths: tuple[Path, ...]) -> str:
    rows: list[str] = []

    for path in sorted(
        paths,
        key=lambda item: item.relative_to(ROOT).as_posix(),
    ):
        relative = path.relative_to(ROOT).as_posix()
        rows.append(
            f"{relative}\t{sha256_file(path)}\n"
        )

    return hashlib.sha256(
        "".join(rows).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def pip_freeze() -> tuple[str, ...]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "freeze",
            "--all",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return tuple(
        sorted(
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        )
    )


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise SystemExit(
            f"required package is not installed: {name}"
        ) from exc


def package_snapshot(
    expected: dict[str, str],
) -> dict[str, str]:
    observed: dict[str, str] = {}

    for name, expected_version in expected.items():
        actual = package_version(name)
        observed[name] = actual

        if actual != expected_version:
            raise SystemExit(
                f"package version mismatch for {name}: "
                f"expected {expected_version}, observed {actual}"
            )

    try:
        observed["openai"] = importlib.metadata.version(
            "openai"
        )
    except importlib.metadata.PackageNotFoundError:
        observed["openai"] = "<not-installed>"

    return observed


def torch_snapshot() -> dict[str, object]:
    try:
        import torch
    except Exception:
        return {
            "torch_imported": False,
            "gpu_required_for_phase8a": False,
        }

    return {
        "torch_imported": True,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": (
            torch.cuda.device_count()
            if torch.cuda.is_available()
            else 0
        ),
        "cuda_device_names": (
            [
                torch.cuda.get_device_name(index)
                for index in range(
                    torch.cuda.device_count()
                )
            ]
            if torch.cuda.is_available()
            else []
        ),
        "gpu_required_for_phase8a": False,
    }


def main() -> None:
    phase7_manifest_path = (
        ROOT
        / "docs"
        / "research"
        / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json"
    )

    frozen = read_json(
        phase7_manifest_path
    )

    expected_aggregate = (
        "337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f"
    )

    if frozen["aggregate_sha256"] != expected_aggregate:
        raise SystemExit(
            "Phase 7 freeze aggregate is not the expected verified digest"
        )

    model_plan = read_json(
        MODEL_PLAN
    )
    runtime_plan = read_json(
        RUNTIME_PLAN
    )

    if model_plan["status"] != "PRE_OUTCOME_FROZEN":
        raise SystemExit(
            "model plan is not frozen"
        )

    if runtime_plan["status"] != "PRE_OUTCOME_FROZEN":
        raise SystemExit(
            "runtime plan is not frozen"
        )

    primary_model = model_plan["primary"]

    if (
        runtime_plan["primary_model"]["model_id"]
        != primary_model["model_id"]
    ):
        raise SystemExit(
            "model plan and runtime plan disagree on primary model"
        )

    if (
        runtime_plan["primary_model"]["revision_label"]
        != primary_model["model_revision_label"]
    ):
        raise SystemExit(
            "model plan and runtime plan disagree on revision label"
        )

    provider = (
        runtime_plan["provider"]["gateway"]
        + "->"
        + runtime_plan["provider"]["upstream_provider"]
    )

    sampling = runtime_plan["sampling"]
    retry = runtime_plan["retry_policy"]
    tool_loop = runtime_plan["tool_loop"]

    if sampling["temperature_parameter_sent"] is not False:
        raise SystemExit(
            "Phase 8A expects temperature to remain unsent for GPT-5.6"
        )

    prompt_inputs = (
        ROOT / "phenoassistant_maf" / "manager.py",
        PROMPT_CONTRACT,
    )

    tool_inputs = (
        ROOT / "model_zoo.json",
        ROOT / "phenoassistant_maf" / "registry.py",
        ROOT / "phenoassistant_mcp" / "maf_bridge_v2.py",
    )

    task_inputs = (
        ROOT / "research" / "phenoguard" / "pilot_manifest.py",
        ROOT
        / "docs"
        / "research"
        / "IJCAI_2027_PROTOCOL_FREEZE.json",
    )

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    lock_lines = pip_freeze()

    lock_path = (
        OUT_DIR
        / "requirements_phase8_pilot.lock"
    )

    lock_path.write_text(
        "\n".join(lock_lines) + "\n",
        encoding="utf-8",
    )

    packages = package_snapshot(
        runtime_plan["package_expectations"]
    )

    controls = ControlledVariables(
        provider=provider,
        model_id=primary_model["model_id"],
        model_revision=primary_model[
            "model_revision_label"
        ],
        temperature=float(
            sampling["temperature_schema_value"]
        ),
        max_output_tokens=int(
            sampling["max_output_tokens"]
        ),
        prompt_bundle_sha256=aggregate_sha256(
            prompt_inputs
        ),
        tool_catalogue_sha256=aggregate_sha256(
            tool_inputs
        ),
        task_manifest_sha256=aggregate_sha256(
            task_inputs
        ),
        retry_policy=retry["label"],
        iteration_limit=int(
            tool_loop["max_iterations"]
        ),
        session_reset_policy=runtime_plan[
            "session_reset_policy"
        ],
        package_lock_sha256=sha256_file(
            lock_path
        ),
        hardware_class=runtime_plan[
            "hardware_class"
        ],
    )

    payload = {
        "schema": (
            "phenoguard-ijcai2027-runtime-controls-candidate-v0.2"
        ),
        "status": "CANDIDATE_PRE_OUTCOME",
        "captured_utc": datetime.now(
            UTC
        ).isoformat(),
        "phase7_freeze_aggregate_sha256": (
            frozen["aggregate_sha256"]
        ),
        "phase7_closure_branch": (
            "baseline/phenoguard-method-freeze-20261010"
        ),
        "controls": controls.model_dump(
            mode="json",
        ),
        "extensions": {
            "temperature_parameter_sent": sampling[
                "temperature_parameter_sent"
            ],
            "temperature_note": sampling[
                "temperature_note"
            ],
            "reasoning": sampling["reasoning"],
            "seed_schedule": sampling[
                "seed_schedule"
            ],
            "tool_loop": tool_loop,
            "provider_routing": model_plan[
                "routing"
            ][
                "openrouter_provider_object"
            ],
            "response_identity_policy": runtime_plan[
                "response_identity_policy"
            ],
            "breadth_model": model_plan[
                "breadth"
            ],
        },
        "hash_inputs": {
            "prompt_bundle": [
                path.relative_to(ROOT).as_posix()
                for path in prompt_inputs
            ],
            "tool_catalogue": [
                path.relative_to(ROOT).as_posix()
                for path in tool_inputs
            ],
            "task_manifest": [
                path.relative_to(ROOT).as_posix()
                for path in task_inputs
            ],
            "model_plan": {
                "path": MODEL_PLAN.relative_to(
                    ROOT
                ).as_posix(),
                "sha256": sha256_file(
                    MODEL_PLAN
                ),
            },
            "runtime_plan": {
                "path": RUNTIME_PLAN.relative_to(
                    ROOT
                ).as_posix(),
                "sha256": sha256_file(
                    RUNTIME_PLAN
                ),
            },
            "package_lock": lock_path.relative_to(
                ROOT
            ).as_posix(),
        },
        "environment": {
            "hostname": socket.gethostname(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "packages": packages,
            **torch_snapshot(),
        },
        "outcome_bearing_work_performed": False,
        "api_key_read": False,
    }

    out_path = (
        OUT_DIR
        / "runtime_controls_candidate.json"
    )

    out_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    candidate_sha256 = sha256_file(
        out_path
    )

    print(
        "PHASE8A_RUNTIME_CONTROLS_CANDIDATE="
        + out_path.relative_to(ROOT).as_posix()
    )

    print(
        "PHASE8A_RUNTIME_CONTROLS_CANDIDATE_SHA256="
        + candidate_sha256
    )

    print(
        "PHASE8A_HOSTNAME="
        + payload["environment"]["hostname"]
    )

    for package_name in sorted(
        payload["environment"]["packages"]
    ):
        print(
            "PHASE8A_PACKAGE_"
            + package_name.upper().replace("-", "_")
            + "="
            + payload["environment"]["packages"][package_name]
        )

    print(
        "PHASE8A_PROVIDER="
        + controls.provider
    )

    print(
        "PHASE8A_MODEL_ID="
        + controls.model_id
    )

    print(
        "PHASE8A_MODEL_REVISION="
        + controls.model_revision
    )

    print(
        "PHASE8A_TEMPERATURE_PARAMETER_SENT="
        + str(
            sampling[
                "temperature_parameter_sent"
            ]
        ).lower()
    )

    print(
        "PHASE8A_SEED_SCHEDULE="
        + ",".join(
            str(seed)
            for seed in sampling[
                "seed_schedule"
            ]
        )
    )

    print(
        "PHASE8A_PROMPT_BUNDLE_SHA256="
        + controls.prompt_bundle_sha256
    )

    print(
        "PHASE8A_TOOL_CATALOGUE_SHA256="
        + controls.tool_catalogue_sha256
    )

    print(
        "PHASE8A_TASK_MANIFEST_SHA256="
        + controls.task_manifest_sha256
    )

    print(
        "PHASE8A_PACKAGE_LOCK_SHA256="
        + controls.package_lock_sha256
    )

    print(
        "PHASE8A_OUTCOME_BEARING_WORK_PERFORMED=false"
    )

    print(
        "PHASE8A_RUNTIME_CAPTURE_PASS=true"
    )


if __name__ == "__main__":
    main()
