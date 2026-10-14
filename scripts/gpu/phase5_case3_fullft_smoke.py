"""Run the collaborator-approved Case 3 fully fine-tuned checkpoint.

This wrapper preserves the original bounded GPU smoke runner while replacing only
its checkpoint constant. It performs inference only and does not mutate model_zoo.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gpu import phase5_case3_smoke as legacy_smoke


FULLFT_CHECKPOINT = (
    "fengchen025/"
    "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
)


def main() -> Path:
    legacy_smoke.CHECKPOINT = FULLFT_CHECKPOINT
    return legacy_smoke.main()


if __name__ == "__main__":
    main()
