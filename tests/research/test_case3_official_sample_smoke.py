"""Static contract for the official-sample Case 3 GPU compatibility smoke."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "scripts"
    / "gpu"
    / "phase5_case3_official_sample_smoke.py"
)


def test_case3_official_sample_smoke_contract() -> None:
    assert SCRIPT.is_file()

    source = SCRIPT.read_text(
        encoding="utf-8",
    )

    assert (
        "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
        in source
    )
    assert (
        "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
        in source
    )
    assert (
        "202306200458172.png"
        in source
    )
    assert (
        "accuracy_claim_authorized"
        in source
    )
    assert (
        "CASE3_FULLFT_GPU_COMPATIBILITY_PASS=true"
        in source
    )
    assert "snapshot_download" in source
    assert "local_files_only=True" in source
    assert (
        "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
        in source
    )
