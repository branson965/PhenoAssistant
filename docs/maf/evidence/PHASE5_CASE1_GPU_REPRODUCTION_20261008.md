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


## Scientific-conclusion parity

The regenerated and tracked 1,248-row phenotype tables were independently
reanalysed with the historical mixed repeated-measures ANOVA and Tukey-Kramer
implementation for projected leaf area.

Results:

- regenerated interaction: F = 22.666978865870615,
  p = 2.3816775373361665e-262;
- tracked-reference interaction: F = 22.6669360372141,
  p = 2.3834021910783026e-262;
- interaction significance decision matched at alpha = 0.01;
- all ten Tukey pairwise significance decisions matched at alpha = 0.05;
- ordered grouping matched exactly:
  - large: col0, ein2;
  - medium: adh1, pgm;
  - small: ctr;
- final scientific-conclusion parity status: passed.

This closes the Case 1 scientific reproduction gate: the regenerated vision
pipeline preserves both the numerical phenotype evidence and the inferential
scientific conclusion.

## Environment note

The ad-hoc installation of the historical statistical packages caused pip to
upgrade pandas from the Phase 5 pin (1.5.3) to 3.0.6 because the direct command
did not include the existing pandas constraint. The statistical parity result
passed, but the environment must be restored to the declared Phase 5 pins and
the CPU-only parity gate rerun before the environment is considered frozen.


## Frozen statistical-environment confirmation

The Phase 5 statistical environment was restored after the temporary resolver
drift. The confirmed versions are pandas 1.5.3, pandas-flavor 0.6.0,
seaborn 0.12.2, pingouin 0.5.5, scikit-learn 1.5.2,
statsmodels 0.14.4, and xarray 2024.3.0.

`python -m pip check` reported no broken requirements.

The scientific-conclusion parity gate was rerun under these restored pins and
passed again: the interaction decision, every Tukey pairwise significance
decision, the ordered grouping, and the final scientific conclusion all
matched the tracked reference.

Case 1 GPU scientific reproduction is therefore closed under the declared
environment rather than only under the temporary resolver state.
