"""Static contract tests for Phase 5 GPU validation assets.

These tests intentionally avoid importing Torch, Transformers, PEFT, or the legacy
vision modules so they remain runnable in the lean MAF CPU environment.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ENV_PROBE = ROOT / "scripts" / "gpu" / "phase5_environment_probe.py"
PREFLIGHT = ROOT / "scripts" / "gpu" / "phase5_preflight.py"
HF_PROBE = ROOT / "scripts" / "gpu" / "phase5_hf_access_probe.py"
CASE1 = ROOT / "scripts" / "gpu" / "phase5_case1_gpu.py"
CASE3 = ROOT / "scripts" / "gpu" / "phase5_case3_smoke.py"
COMPARATOR = ROOT / "scripts" / "gpu" / "compare_case1_gpu_to_tracked.py"
SCIENTIFIC_COMPARATOR = ROOT / "scripts" / "gpu" / "compare_case1_scientific_conclusions.py"
PROTOCOL = ROOT / "docs" / "gpu" / "PHASE5_GPU_VALIDATION_PROTOCOL.md"


def _source(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_phase5_assets_exist() -> None:
    for path in (
        ENV_PROBE,
        PREFLIGHT,
        HF_PROBE,
        CASE1,
        CASE3,
        COMPARATOR,
        SCIENTIFIC_COMPARATOR,
        PROTOCOL,
    ):
        assert path.is_file(), path


def test_environment_probe_is_secret_safe_by_contract() -> None:
    source = _source(ENV_PROBE)

    assert '"HF_TOKEN": bool(os.environ.get("HF_TOKEN"))' in source
    assert '"OPENROUTER_API_KEY": bool(' in source
    assert "os.environ.get("HF_TOKEN")," not in source
    assert "os.environ.get("OPENROUTER_API_KEY")," not in source
    assert '["status", "--short", "--untracked-files=all"]' in source


def test_preflight_does_not_import_heavy_ml_modules() -> None:
    source = _source(PREFLIGHT)

    for forbidden in (
        "import torch",
        "import transformers",
        "import peft",
        "from functions.instance_segmentation",
        "from functions.image_classification",
    ):
        assert forbidden not in source

    assert '"ready_for_gpu_smoke"' in source
    assert '"ready_for_inference_smoke"' in source


def test_hf_access_probe_never_prints_token_value() -> None:
    source = _source(HF_PROBE)

    assert '"hf_token_present": bool(os.environ.get("HF_TOKEN"))' in source
    assert 'print(os.environ.get("HF_TOKEN"))' not in source
    assert "model_info" in source
    assert "dataset_info" in source


def test_case1_gpu_runner_preserves_historical_results() -> None:
    source = _source(CASE1)

    assert "EXPECTED_IMAGES = 1248" in source
    assert "results/maf_gpu_case1_smoke" in source
    assert "results/maf_gpu_case1_sample" in source
    assert "results/maf_gpu_case1" in source
    assert "--sample-size" in source
    assert '"results/Case1"' not in source
    assert "pixel_to_cm=0.03" in source
    assert (
        "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
        in source
    )


def test_case3_smoke_is_inference_only() -> None:
    source = _source(CASE3)

    assert "infer_image_classification" in source
    assert "finetune_image_classification" not in source
    assert "prepare_dataset" not in source
    assert "update_model_zoo" not in source
    assert (
        "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
        in source
    )
    assert "results/maf_gpu_case3_smoke" in source


def test_case1_comparator_uses_deterministic_filename_join() -> None:
    source = _source(COMPARATOR)

    assert 'on="file_name"' in source
    assert 'validate="one_to_one"' in source
    assert "results/Case1/aracrop_phenotypes.csv" in source
    assert "reference_coverage" in source
    assert "ranking_comparison" in source


def test_case1_scientific_comparator_checks_inference_conclusions() -> None:
    source = _source(SCIENTIFIC_COMPARATOR)

    assert 'DESCRIPTOR = "projected_leaf_area"' in source
    assert "INTERACTION_ALPHA = 0.01" in source
    assert "POSTHOC_ALPHA = 0.05" in source
    assert '"scientific_conclusion_match"' in source
    assert "perform_anova" in source
    assert "perform_tukey_test" in source


def test_gpu_scripts_never_use_exit_or_systemexit() -> None:
    combined = "\n".join(
        _source(path)
        for path in (ENV_PROBE, PREFLIGHT, CASE1, CASE3, COMPARATOR, SCIENTIFIC_COMPARATOR)
    )

    assert "sys.exit" not in combined
    assert "SystemExit" not in combined
    assert "exit(" not in combined


def test_protocol_keeps_training_lower_priority_than_inference() -> None:
    source = _source(PROTOCOL)

    assert "Do **not** retrain simply because GPU access now exists." in source
    assert (
        "inference validation has higher priority than retraining"
        in source
    )
