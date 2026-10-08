# Phase 5 Case 1 GPU Reproduction Evidence — 2026-10-08

## Environment

- Host: Nottingham Plato, `amp16/tamar`
- GPU: NVIDIA RTX A4000
- Visible devices: 1
- Driver: 595.71.05
- Driver-reported CUDA capability: 13.2
- PyTorch: 2.4.1+cu121
- PyTorch CUDA runtime: 12.1
- Python: 3.11.17
- Case 1 checkpoint:
  `fengchen025/arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft`
- Pinned Hugging Face revision:
  `a75bc3d595148ebc62afad7c9800908279e7aea8`

## Data integrity

- Metadata rows/images: 1,248
- Local source images present: 1,248
- Missing images: 0
- Source archive checksum was verified before execution.

## GPU validation

### One-image smoke

- Executed images: 1
- Segmentation annotations: 5
- Status: passed

### Bounded 16-image sample

- Executed images: 16
- Segmentation annotations: 106
- Wall-clock inference time: 4.907891370356083 seconds
- Status: passed

### Full Case 1 execution

- Executed images: 1,248
- Segmentation image records: 1,248
- Segmentation annotations: 11,848
- Wall-clock inference time: 184.8577586542815 seconds
- Status: passed
- Segmentation SHA-256:
  `4d779ee715b9c54fe3e6e3bfc9a02275eedc9f5e9412edd34e644361005798d1`
- Regenerated phenotype CSV SHA-256:
  `d235f2ff0a37ecba811d191aba5ab507290e2cfc936f080ad05059520c39b3e2`

## Regenerated-vs-tracked comparison

Coverage was exact:

- aligned rows: 1,248
- reference rows: 1,248
- regenerated rows: 1,248
- missing from regenerated: 0
- extra in regenerated: 0
- reference coverage: 1.0
- unmatched metadata rows: 0

Ecotype ranking was identical for both leaf count and projected leaf area:

`ein2 > col0 > adh1 > pgm > ctr`

Per-phenotype agreement was effectively exact:

| Phenotype | Pearson correlation | Mean absolute difference |
|---|---:|---:|
| leaf_count | 1.0 | 0.0 |
| average_leaf_area | 0.999999999060287 | 2.487895745945101e-06 |
| projected_leaf_area | 0.9999999996377159 | 2.596153846154592e-05 |
| diameter | 1.0 | 3.3804867736983932e-18 |
| perimeter | 0.999999952800227 | 0.0007211538461538478 |
| compactness | 0.999999852047137 | 6.986886077902026e-06 |
| stockiness | 0.9999988434180236 | 1.217386069115879e-05 |

The comparison therefore establishes full row/key coverage and near-numerical identity between the newly regenerated GPU phenotype table and the tracked Case 1 reference artefact.

## Remaining Case 1 scientific gate

The remaining Gate 5G check is to rerun the historical mixed repeated-measures ANOVA and Tukey-Kramer analysis on both regenerated and tracked phenotype tables and verify that:

- the interaction significance decision is unchanged;
- pairwise Tukey significance decisions are unchanged;
- the inferred phenotype grouping is unchanged.

This is implemented by
`scripts/gpu/compare_case1_scientific_conclusions.py`.
