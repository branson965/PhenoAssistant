"""Compare GPU-regenerated Case 1 phenotypes with the tracked reference artefact.

The script performs a deterministic metadata merge on file_name, never mutates the
historical Case 1 files, and writes a JSON comparison report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PHENOTYPES = (
    "leaf_count",
    "average_leaf_area",
    "projected_leaf_area",
    "diameter",
    "perimeter",
    "compactness",
    "stockiness",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value: float | int) -> float | None:
    number = float(value)
    return number if math.isfinite(number) else None


def _rank_ecotypes(frame: pd.DataFrame, phenotype: str) -> list[str]:
    subject_means = (
        frame.groupby(["ecotype", "plant_id"], as_index=False)[phenotype]
        .mean()
    )
    summary = (
        subject_means.groupby("ecotype")[phenotype]
        .mean()
        .sort_values(ascending=False)
    )
    return [str(value) for value in summary.index]


def main() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--regenerated",
        default="results/maf_gpu_case1/phenotypes.csv",
    )
    parser.add_argument(
        "--metadata",
        default="data/aracrop_metadata.json",
    )
    parser.add_argument(
        "--reference",
        default="results/Case1/aracrop_phenotypes.csv",
    )
    parser.add_argument(
        "--merged-output",
        default="results/maf_gpu_case1/aracrop_phenotypes.csv",
    )
    parser.add_argument(
        "--report-output",
        default="results/maf_gpu_case1/comparison_to_tracked.json",
    )
    args = parser.parse_args()

    regenerated_path = Path(args.regenerated)
    metadata_path = Path(args.metadata)
    reference_path = Path(args.reference)
    merged_output = Path(args.merged_output)
    report_output = Path(args.report_output)

    for path in (regenerated_path, metadata_path, reference_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    regenerated = pd.read_csv(regenerated_path)
    reference = pd.read_csv(reference_path)
    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata = pd.DataFrame(metadata_payload)

    required_meta = {"file_name", "plant_id", "ecotype", "days_after_sowing"}
    missing_meta = sorted(required_meta.difference(metadata.columns))
    if missing_meta:
        raise ValueError(
            "metadata is missing required columns: " + ", ".join(missing_meta)
        )

    if "file_name" not in regenerated.columns:
        raise ValueError("regenerated phenotype CSV lacks file_name")
    if "file_name" not in reference.columns:
        raise ValueError("reference phenotype CSV lacks file_name")

    if regenerated["file_name"].duplicated().any():
        raise ValueError("regenerated phenotype CSV has duplicate file_name keys")
    if metadata["file_name"].duplicated().any():
        raise ValueError("metadata has duplicate file_name keys")
    if reference["file_name"].duplicated().any():
        raise ValueError("reference phenotype CSV has duplicate file_name keys")

    missing_phenotypes = sorted(
        set(PHENOTYPES).difference(regenerated.columns)
    )
    if missing_phenotypes:
        raise ValueError(
            "regenerated phenotype CSV is missing: "
            + ", ".join(missing_phenotypes)
        )

    merged = regenerated.merge(
        metadata[list(required_meta)],
        on="file_name",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    unmatched_metadata = int((merged["_merge"] != "both").sum())
    merged = merged.drop(columns=["_merge"])

    merged_output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(merged_output, index=False)

    aligned = merged.merge(
        reference,
        on="file_name",
        how="inner",
        suffixes=("_regen", "_ref"),
        validate="one_to_one",
    )

    regenerated_keys = set(merged["file_name"].astype(str))
    reference_keys = set(reference["file_name"].astype(str))

    per_phenotype: dict[str, object] = {}

    for phenotype in PHENOTYPES:
        regen_column = f"{phenotype}_regen"
        ref_column = f"{phenotype}_ref"

        if regen_column not in aligned.columns or ref_column not in aligned.columns:
            raise ValueError(
                f"aligned comparison is missing {phenotype} columns"
            )

        pair = aligned[[regen_column, ref_column]].dropna()
        regen_values = pair[regen_column].astype(float).to_numpy()
        ref_values = pair[ref_column].astype(float).to_numpy()

        abs_diff = np.abs(regen_values - ref_values)
        denominator = np.maximum(np.abs(ref_values), 1e-12)
        rel_diff = abs_diff / denominator

        if len(pair) >= 2 and np.std(regen_values) > 0 and np.std(ref_values) > 0:
            correlation = float(
                np.corrcoef(regen_values, ref_values)[0, 1]
            )
        else:
            correlation = None

        per_phenotype[phenotype] = {
            "paired_rows": int(len(pair)),
            "mean_absolute_difference": _finite(abs_diff.mean())
            if len(abs_diff)
            else None,
            "max_absolute_difference": _finite(abs_diff.max())
            if len(abs_diff)
            else None,
            "median_relative_difference": _finite(np.median(rel_diff))
            if len(rel_diff)
            else None,
            "pearson_correlation": _finite(correlation)
            if correlation is not None
            else None,
        }

    ranking_comparison: dict[str, object] = {}

    for phenotype in ("projected_leaf_area", "leaf_count"):
        regen_rank = _rank_ecotypes(merged.dropna(subset=["ecotype"]), phenotype)
        ref_rank = _rank_ecotypes(reference, phenotype)
        ranking_comparison[phenotype] = {
            "regenerated": regen_rank,
            "reference": ref_rank,
            "exact_match": regen_rank == ref_rank,
        }

    report = {
        "schema_version": "1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "regenerated": {
                "path": str(regenerated_path),
                "sha256": _sha256(regenerated_path),
                "rows": int(len(regenerated)),
            },
            "metadata": {
                "path": str(metadata_path),
                "sha256": _sha256(metadata_path),
                "rows": int(len(metadata)),
            },
            "reference": {
                "path": str(reference_path),
                "sha256": _sha256(reference_path),
                "rows": int(len(reference)),
            },
        },
        "merge": {
            "output_path": str(merged_output),
            "output_sha256": _sha256(merged_output),
            "rows": int(len(merged)),
            "unmatched_metadata_rows": unmatched_metadata,
        },
        "coverage": {
            "aligned_rows": int(len(aligned)),
            "reference_rows": int(len(reference)),
            "regenerated_rows": int(len(merged)),
            "reference_coverage": float(
                len(aligned) / len(reference)
            )
            if len(reference)
            else 0.0,
            "missing_from_regenerated": int(
                len(reference_keys - regenerated_keys)
            ),
            "extra_in_regenerated": int(
                len(regenerated_keys - reference_keys)
            ),
        },
        "per_phenotype": per_phenotype,
        "ranking_comparison": ranking_comparison,
    }

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(report_output)
    print(
        json.dumps(
            {
                "aligned_rows": report["coverage"]["aligned_rows"],
                "reference_coverage": report["coverage"][
                    "reference_coverage"
                ],
                "pla_ranking_exact": ranking_comparison[
                    "projected_leaf_area"
                ]["exact_match"],
                "leaf_count_ranking_exact": ranking_comparison[
                    "leaf_count"
                ]["exact_match"],
            },
            sort_keys=True,
        )
    )

    if unmatched_metadata:
        raise RuntimeError(
            "some regenerated rows could not be joined to Case 1 metadata"
        )

    return report_output


if __name__ == "__main__":
    main()
