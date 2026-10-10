"""Verify the frozen Phase 7 IJCAI method snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    ROOT
    / "docs"
    / "research"
    / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json"
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


def verify_manifest() -> tuple[int, str]:
    payload = json.loads(
        MANIFEST.read_text(
            encoding="utf-8",
        )
    )

    frozen_files = payload["frozen_files"]

    if len(frozen_files) != payload["frozen_file_count"]:
        raise AssertionError(
            "frozen_file_count does not match manifest contents"
        )

    observed: dict[str, str] = {}

    for relative_path, expected in frozen_files.items():
        path = ROOT / relative_path

        if not path.is_file():
            raise AssertionError(
                f"frozen file is missing: {relative_path}"
            )

        actual = sha256_file(path)

        if actual != expected:
            raise AssertionError(
                f"hash mismatch for {relative_path}: "
                f"expected {expected}, observed {actual}"
            )

        observed[relative_path] = actual

    canonical = "".join(
        f"{path}\t{observed[path]}\n"
        for path in sorted(observed)
    ).encode(
        "utf-8",
    )

    aggregate = hashlib.sha256(
        canonical
    ).hexdigest()

    if aggregate != payload["aggregate_sha256"]:
        raise AssertionError(
            "aggregate freeze digest does not match manifest"
        )

    return len(observed), aggregate


if __name__ == "__main__":
    count, aggregate = verify_manifest()

    print(
        "PHASE7I_FROZEN_FILE_COUNT="
        + str(count)
    )

    print(
        "PHASE7I_AGGREGATE_SHA256="
        + aggregate
    )

    print(
        "PHASE7I_METHOD_FREEZE_MANIFEST_PASS=true"
    )
