"""Contract for the collaborator-approved Case 3 full-FT smoke wrapper."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "gpu" / "phase5_case3_fullft_smoke.py"


def test_case3_fullft_smoke_wrapper_points_to_public_model() -> None:
    assert SCRIPT.is_file()
    source = SCRIPT.read_text(encoding="utf-8")
    assert "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020" in source
    assert "legacy_smoke.CHECKPOINT = FULLFT_CHECKPOINT" in source
