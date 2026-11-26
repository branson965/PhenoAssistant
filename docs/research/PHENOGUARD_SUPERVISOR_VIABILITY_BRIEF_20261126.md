# PhenoGuard: scientific viability decision

**26 November 2026 | Supervisor discussion | Exploratory evidence, not an IJCAI-ready method result**

## Decision requested

Approve a bounded investigation into consequential errors in scientific tool-using agents, and nominate an independent reviewer for the 108-trial registered qualification. Do not yet endorse the existing resolver or validator as a novel method. Agree a prospective go/no-go based on whether an intervention adds value over information-matched and deterministic alternatives.

## 1. Direct evidence: technically valid outputs can be scientifically poor

Eight distinct potato plants, one filename-selected representative per tray, two varieties (Desiree and Voyager), 51 original manually labelled leaf polygons. Same original image bytes for both capabilities. All 8 image and annotation files matched Zenodo record 7938231 checksums; legacy licence identifier cc-by, exact version not asserted. Original physical leaf-area and dry-weight values reconciled 16/16 against the harvest-image records. Six EXIF orientation-6 files scored in the annotation coordinate frame using lossless mask transpose. The original annotations may overlap with Leaf-only SAM development/evaluation; no claim of independently held-out generalisation. Annotator completeness and instance semantics not independently adjudicated.

Slurm job 64597, NVIDIA RTX A4000, 8/8 tasks completed, 16/16 direct model executions succeeded and passed structural validation. No provider calls and no registered agent trials.

| Metric | Potato Leaf-only SAM | Arabidopsis Mask2Former |
| --- | ---: | ---: |
| Execution / structural acceptance | 8/8 | 8/8 |
| Macro foreground IoU | 0.800755 | 0.119231 |
| Macro Dice | 0.841202 | 0.155077 |
| Macro instance F1 at IoU 0.5 | 0.705132 | 0.085227 |
| Mean absolute annotated count error | 2.25 | 5.00 |
| Median relative union-area error | 6.71% | 100% |
| Mean relative union-area error | 386.43% | 86.69% |
| Empty predictions | 0/8 | 5/8 |

Paired mean foreground IoU difference +0.681523; all 8 differences positive. No inferential population claim. This is a comparison of entire capabilities (architecture, preprocessing, training and thresholds differ), not an isolated causal estimate of species shift.

| Tray | SAM IoU | Mask2Former IoU |
| --- | ---: | ---: |
| 1 | .970450 | .112907 |
| 2 | .959210 | .104774 |
| 3 | .947742 | .000000 |
| 4 | .886652 | .000000 |
| 5 | .912620 | .736170 |
| 6 | .851487 | .000000 |
| 7 | .846092 | .000000 |
| 8 | .031784 | .000000 |

## 2. Applicability is not enough

Tray 8: nominally applicable SAM produced 1,510,196 union-area pixels versus 48,000 annotated foreground pixels (31.46x, 3,046.24% relative error). One true positive and one false positive at instance IoU 0.5; instance F1 .667 despite foreground IoU .0318. Both models' artifacts passed structural checks. Do not remove this outlier or change thresholds retrospectively.

Historical projected-area extraction uses XOR rather than foreground OR. Holding predicted masks constant, XOR removes 84.30%, 54.77% and 87.20% of the union area in trays 5, 6 and 7. Tray 5: reference 341,429 px, union 369,096 px (8.10% relative error), XOR 57,952 px (83.03% error). This is a measurement-semantics discrepancy; discuss intended semantics with original authors before any change or assertion about published conclusions. Correct OR for projected union is standard image processing, not an AI novelty claim.

## 3. Scientific utility is not equivalent to mask accuracy

All eight successful pairs retained. Pearson r / Spearman rho:

| Area measure | Manual leaf area | Dry weight |
| --- | --- | --- |
| Physical manual leaf area | — | .9970 / .9286 |
| SAM union area | .5652 / .5000 | .5805 / .4286 |
| SAM historical XOR area | .5665 / .3810 | .5823 / .2143 |
| Mask2Former union area | .5564 / .7910 | .5296 / .7910 |
| Mask2Former historical XOR area | .5562 / .7910 | .5294 / .7910 |

SAM has slightly better Pearson correlations, while Mask2Former has better Spearman correlations despite 5 empty predictions and very low IoU. The latter has tied zeros; correlation is not an accuracy metric. Projected image area and harvested physical total area differ in meaning; no absolute physical calibration or generalisation claim. Both correlations are substantially weaker than the observed manual area/weight Pearson relationship. The eight-case outlier is retained. The original physical association report's stale limitation about reconciliation is superseded by the independently recorded source-table audit (not a rewritten result).

## 4. Prior evidence and counterevidence

- 12 mechanical dev/val cases: frozen resolver and lexical name/task baseline both 12/12; naive passthrough 6/12. No evidence of added value over lexical matching.
- 1,248 historical Arabidopsis images, 11,848 masks, 12,480 retrospective faults/probes: basic structure 10%, frozen validator 70%, ordinary source-bound mask reference 90%. All methods accept all originals. All four miss all 1,248 relabelled wrong-source probes. These are constructed probes, not natural operational prevalence or a demonstrated vulnerability of the full runner.
- 24 historical Arabidopsis plants, five ecotypes: constructed same-day cross-ecotype exchange changes 7/10 Tukey decisions and reverses extreme area ranks; image-ID rotation changes neither. Severe constructed sensitivity test, not independent biological truth.

## 5. Hypothesis worth testing, and why

Technical execution, evidence-backed applicability, output credibility and measurement semantics are distinct. A correct species choice is necessary in some cases but insufficient for reliable scientific reporting; our direct model comparison supplies empirical examples of all three post-routing concerns. A scientifically grounded agent might identify consequential errors without over-refusing valid work, but there is currently NO evidence that PhenoGuard beats strong alternatives or that agents naturally produce these errors at meaningful rates.

The next experiment must compare actual agents and strong information-matched conventional baselines, including ordinary deterministic routing/validation and trusted input/output binding. An intervention should measure selective risk/coverage and scientific utility using sealed reference cases, with no access to gold masks at decision time. Do not tune credibility thresholds on these eight outcomes and call the same cases independent validation. A new method version needs prospective review and a fresh evaluation set; retain the current 22-file freeze.

## 6. Bounded investment and stop criteria

1. Supervisor reviews 12 qualification fixtures and runtime/billing controls; nominate domain reviewer. Current 0/12 independent approvals, 0/108 registered live trials, final provider approval absent. Existing release packet source predates later diagnostic commits; prospective execution identity must be reviewed/rebound.
2. Complete 108 registered C3/C4/C8 development/validation trials only after approval. They qualify the harness; not final independent paper evidence.
3. Agree separately on an independent study with broader scientific tasks or held-out images, including real agent errors, matched information, ordinary deterministic checks, and biological outcome metrics. Prior direct-model pilot is evidence of problem importance, not evidence of an agent solution.
4. Continue the method-paper route only if real agent errors occur on independently justified cases and the intervention improves consequential error/coverage trade-offs over competitive references. If simple rules solve the problem, narrow to a scientifically valuable diagnostic/benchmark contribution or stop. Do not commit to the existing IJCAI claim solely because the direct-model pilot has a large effect.

## Evidence identity (reported by researcher from Plato)

Branch feature/phase8-wednesday-gpu-smokes, pilot runner 1da8dd9, annotation evaluator 872c63b. Private staging data/_staging/potato_cross_capability_pilot_v0.1.
- manifest.json: 1efb97145e19bb51eaab0da0d12cecb479e675c5aaa21b4396cf181cb36ce691
- annotation_eval_v0.1/audit.json: 1e473486b8b9c89a004daf7c63c2b98630988262f335c41d45cfd52bbfe629ed
- annotation_eval_v0.1/report.json: 9d33a16210869128d6b2d1bf86d626ed89b694c369238a1648474c03f6e03361
- report.json: 449320ca3067d6d615d03f9f265654ee4858e6803ee7555feec8dfa87adef7e3
- Prior viability report: b3a5cd4d9be75d575c74db30958e6a797a4ff333d3f623018e894c0b36ee13eb
- Prior scientific consequence report: 5f9de32d6722be43fca2d40410471dc0a8b395ff6cb873c656bb63bc18203821

Reported hashes, not independent rehashing of remote files. See PHENOGUARD_VIABILITY_DECISION_20261125.md for full earlier history. No changes to frozen scientific method or experiment outcomes.
