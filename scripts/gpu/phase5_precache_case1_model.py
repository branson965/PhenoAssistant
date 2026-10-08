"""Pre-cache the exact public Case 1 checkpoint before reserving a GPU.

This performs network/disk work only and is intended for the Plato login node.
It pins the checkpoint revision observed by the Phase 5 access probe so GPU
execution does not silently drift if the Hugging Face repository changes later.
"""

from __future__ import annotations

import json
from pathlib import Path

from huggingface_hub import model_info, snapshot_download


REPO_ID = (
    "fengchen025/"
    "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
)
EXPECTED_REVISION = "a75bc3d595148ebc62afad7c9800908279e7aea8"


def main() -> None:
    info = model_info(REPO_ID)
    observed = getattr(info, "sha", None)

    if observed != EXPECTED_REVISION:
        raise RuntimeError(
            "Case 1 checkpoint revision changed: expected {}, observed {}. "
            "Review provenance before continuing.".format(
                EXPECTED_REVISION, observed
            )
        )

    path = snapshot_download(
        repo_id=REPO_ID,
        revision=EXPECTED_REVISION,
    )

    path_obj = Path(path)
    files = sorted(
        str(item.relative_to(path_obj))
        for item in path_obj.rglob("*")
        if item.is_file()
    )

    required = {"label2id.json", "id2label.json"}
    missing_required = sorted(required.difference(files))
    if missing_required:
        raise RuntimeError(
            "Checkpoint cache is missing required files: {}".format(
                missing_required
            )
        )

    print(
        json.dumps(
            {
                "repo_id": REPO_ID,
                "revision": EXPECTED_REVISION,
                "cache_path": str(path_obj),
                "file_count": len(files),
                "required_metadata_present": True,
                "status": "ready",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
