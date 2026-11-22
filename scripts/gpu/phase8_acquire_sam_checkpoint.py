"""Verify or explicitly acquire the frozen potato Leaf-only SAM ViT-H weights.

Source is Meta's official Segment Anything release. A separate, independently
reported content SHA-256 from two public mirrors is pinned below. This helper
never imports torch, executes an untrusted pickle, or launches any GPU/LLM run.

For approved institutional network use, --download fetches to a temporary
file, verifies SHA-256, then atomically installs the final filename. By
default, the command ONLY checks the checkpoint already on disk.

WARNING: the file is approximately 2.56 GB. Check local quota, university
network policy, and permission before any download to a cluster login node.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "models" / "sam_vit_h_4b8939.pth"
OFFICIAL_URL = (
    "https://dl.fbaipublicfiles.com/segment_anything/"
    "sam_vit_h_4b8939.pth"
)
# Reported identically by independent public mirrors. Validate against the
# actual official downloaded bytes. Do not treat filename as an integrity test.
EXPECTED_SHA256 = (
    "a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e"
)
EXPECTED_MINIMUM_BYTES = 2_400_000_000
MAXIMUM_BYTES = 3_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("checkpoint is missing or is a symlink")
    size = path.stat().st_size
    if not EXPECTED_MINIMUM_BYTES <= size <= MAXIMUM_BYTES:
        raise ValueError(f"checkpoint size is not credible: {size} bytes")
    measured = sha256(path)
    if measured != EXPECTED_SHA256:
        raise ValueError(
            "SAM checkpoint SHA-256 mismatch: not approved for loading; "
            f"actual={measured}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download", action="store_true",
        help="Explicitly allow one official-source checkpoint download",
    )
    args = parser.parse_args()
    if DESTINATION.exists() or DESTINATION.is_symlink():
        verify(DESTINATION)
        print("PHASE8_SAM_CHECKPOINT_VERIFY_PASS=true")
        print("PHASE8_SAM_CHECKPOINT_SHA256=" + EXPECTED_SHA256)
        print("PHASE8_SAM_CHECKPOINT_DOWNLOAD_PERFORMED=false")
        return 0
    if not args.download:
        print("PHASE8_SAM_CHECKPOINT_PRESENT=false")
        print("PHASE8_SAM_CHECKPOINT_EXPECTED_SHA256=" + EXPECTED_SHA256)
        print("PHASE8_SAM_CHECKPOINT_DOWNLOAD_PERFORMED=false")
        return 2
    if shutil.which("curl") is None:
        raise RuntimeError("curl missing: cannot download safely")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.parent.is_symlink():
        raise ValueError("checkpoint directory is an untrusted symlink")
    partial = DESTINATION.with_name(DESTINATION.name + ".download")
    if partial.is_symlink():
        raise ValueError("temporary checkpoint is an untrusted symlink")
    available = shutil.disk_usage(DESTINATION.parent).free
    remaining = max(0, MAXIMUM_BYTES - (partial.stat().st_size if partial.exists() else 0))
    if available < remaining:
        raise RuntimeError(
            f"insufficient free disk space: {available} bytes; "
            f"need up to {remaining} bytes (also check quotas)"
        )
    print("PHASE8_SAM_OFFICIAL_SOURCE=" + OFFICIAL_URL, flush=True)
    subprocess.run(
        [
            "curl", "--fail", "--location", "--retry", "3",
            "--retry-delay", "5", "--connect-timeout", "30",
            "--continue-at", "-", "--output", str(partial),
            OFFICIAL_URL,
        ], check=True,
    )
    # Check before renaming. Never leave unverified bytes under .pth.
    verify(partial)
    if DESTINATION.exists() or DESTINATION.is_symlink():
        raise RuntimeError("destination appeared during download: refuse overwrite")
    os.replace(partial, DESTINATION)
    print("PHASE8_SAM_CHECKPOINT_VERIFY_PASS=true")
    print("PHASE8_SAM_CHECKPOINT_SHA256=" + EXPECTED_SHA256)
    print("PHASE8_SAM_CHECKPOINT_DOWNLOAD_PERFORMED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
