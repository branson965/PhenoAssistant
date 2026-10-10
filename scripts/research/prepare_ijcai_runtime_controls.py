"""Prepare the pre-outcome IJCAI Phase 8 runtime-control candidate.

This script performs no LLM call and executes no scientific benchmark. It captures
and hashes the runtime identity required by the frozen Phase 7 protocol.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from research.phenoguard import ControlledVariables

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "ijcai2027" / "runtime"
PROMPT_CONTRACT = (
    ROOT
    / "experiments"
    / "ijcai2027"
    / "condition_prompt_contract.json"
)


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


def require_env(name: str) -> str:
    value = os.environ.get(
        name,
        "",
    ).strip()

    if not value:
        raise SystemExit(
            f"missing required environment variable: {name}"
        )

    return value


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


def torch_snapshot() -> dict[str, object]:
    try:
        import torch
    except Exception:
        return {
            "torch_imported": False,
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
    }


def main() -> None:
    phase7_manifest = (
        ROOT
        / "docs"
        / "research"
        / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json"
    )

    frozen = json.loads(
        phase7_manifest.read_text(
            encoding="utf-8",
        )
    )

    expected_aggregate = (
        "337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f"
    )

    if frozen["aggregate_sha256"] != expected_aggregate:
        raise SystemExit(
            "Phase 7 freeze aggregate is not the expected verified digest"
        )

    provider = require_env("IJCAI_PROVIDER")

    model_id = (
        os.environ.get(
            "IJCAI_MODEL_ID",
            "",
        ).strip()
        or os.environ.get(
            "OPENROUTER_MODEL",
            "",
        ).strip()
    )

    if not model_id:
        raise SystemExit(
            "missing IJCAI_MODEL_ID and OPENROUTER_MODEL"
        )

    model_revision = require_env(
        "IJCAI_MODEL_REVISION"
    )

    temperature = float(
        require_env(
            "IJCAI_TEMPERATURE"
        )
    )

    max_output_tokens = int(
        require_env(
            "IJCAI_MAX_OUTPUT_TOKENS"
        )
    )

    retry_policy = require_env(
        "IJCAI_RETRY_POLICY"
    )

    iteration_limit = int(
        require_env(
            "IJCAI_ITERATION_LIMIT"
        )
    )

    session_reset_policy = require_env(
        "IJCAI_SESSION_RESET_POLICY"
    )

    hardware_class = require_env(
        "IJCAI_HARDWARE_CLASS"
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

    controls = ControlledVariables(
        provider=provider,
        model_id=model_id,
        model_revision=model_revision,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        prompt_bundle_sha256=aggregate_sha256(
            prompt_inputs
        ),
        tool_catalogue_sha256=aggregate_sha256(
            tool_inputs
        ),
        task_manifest_sha256=aggregate_sha256(
            task_inputs
        ),
        retry_policy=retry_policy,
        iteration_limit=iteration_limit,
        session_reset_policy=session_reset_policy,
        package_lock_sha256=sha256_file(
            lock_path
        ),
        hardware_class=hardware_class,
    )

    payload = {
        "schema": (
            "phenoguard-ijcai2027-runtime-controls-candidate-v0.1"
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
            "package_lock": lock_path.relative_to(
                ROOT
            ).as_posix(),
        },
        "environment": {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
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

    print(
        "PHASE8A_RUNTIME_CONTROLS_CANDIDATE="
        + out_path.relative_to(ROOT).as_posix()
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
