"""Capture a secret-safe Phase 5 Nottingham GPU environment record.

Run from the repository root. The script never prints or stores credential values.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "docs" / "maf" / "evidence"


def _command(args: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    torch_evidence: dict[str, object]

    try:
        import torch

        devices = []
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            devices.append(
                {
                    "index": index,
                    "name": properties.name,
                    "total_memory_bytes": properties.total_memory,
                    "major": properties.major,
                    "minor": properties.minor,
                }
            )

        torch_evidence = {
            "version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "cudnn_version": torch.backends.cudnn.version(),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "devices": devices,
        }
    except Exception as exc:
        torch_evidence = {
            "import_ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "cuda_available": False,
            "device_count": 0,
            "devices": [],
        }

    paths = {
        "model_zoo": ROOT / "model_zoo.json",
        "case1_metadata": ROOT / "data" / "aracrop_metadata.json",
        "case1_images": ROOT / "data" / "AraCropData",
        "case3_dataset": (
            ROOT
            / "data"
            / "winter-wheat_nutri-defi-identify_dndww20"
        ),
    }

    record = {
        "schema_version": "1",
        "captured_at_utc": timestamp,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "git": {
            "head": _command(["git", "rev-parse", "HEAD"]),
            "branch": _command(["git", "branch", "--show-current"]),
            "status": _command(
                ["git", "status", "--short", "--untracked-files=all"]
            ),
        },
        "nvidia_smi": _command(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,compute_cap",
                "--format=csv,noheader",
            ]
        ),
        "torch": torch_evidence,
        "packages": {
            name: _version(name)
            for name in (
                "agent-framework",
                "mcp",
                "torch",
                "torchvision",
                "transformers",
                "peft",
                "datasets",
                "accelerate",
                "huggingface-hub",
                "pydantic",
            )
        },
        "credential_presence": {
            "HF_USER": bool(os.environ.get("HF_USER")),
            "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
            "OPENROUTER_API_KEY": bool(
                os.environ.get("OPENROUTER_API_KEY")
            ),
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        },
        "trusted_path_presence": {
            label: {
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
            }
            for label, path in paths.items()
        },
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    target = EVIDENCE_DIR / f"phase5-gpu-environment-{timestamp}.json"
    target.write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(target.relative_to(ROOT))
    print(
        json.dumps(
            {
                "cuda_available": torch_evidence.get(
                    "cuda_available", False
                ),
                "device_count": torch_evidence.get("device_count", 0),
                "evidence": str(target.relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )

    if not torch_evidence.get("cuda_available", False):
        raise RuntimeError(
            "CUDA is not available in the active Python environment; "
            "evidence was written before this failure."
        )

    return target


if __name__ == "__main__":
    main()
