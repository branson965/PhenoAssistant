"""Static contract for the Case 3 checkpoint-integrity audit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "scripts"
    / "gpu"
    / "phase5_case3_checkpoint_audit.py"
)


def test_case3_checkpoint_audit_contract() -> None:
    assert SCRIPT.is_file()

    source = SCRIPT.read_text(
        encoding="utf-8",
    )

    assert "model.safetensors" in source
    assert "classifier.weight" in source
    assert "classifier.bias" in source
    assert "adapter_model.safetensors" in source
    assert "classifier_matches_label_count" in source
    assert (
        "CASE3_FULLFT_CHECKPOINT_INTEGRITY_PASS=true"
        in source
    )
