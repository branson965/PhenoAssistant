# IJCAI 2027 Scientific-Paper Completion Scorecard

**As of:** 2026-11-18  
**Scope:** PhenoGuard / scientific applicability under distribution shift  
**Branch:** `experiments/ijcai2027`  
**Status:** evidence-weighted progress accounting; not an empirical result and not an acceptance probability

## Purpose

This scorecard supersedes the legacy engineering-heavy "87% overall / 43% Phase 8 / 7 of 9 phases" accounting. The old score overstated paper readiness by giving implemented and tested infrastructure too much credit relative to still-unrun scientific comparisons and the submission manuscript.

**100% now means a completed, appropriately evaluated, defensible, submission-ready paper and reproducible artifact, with acknowledged limitations.** It does not mean acceptance by a venue.

## Frozen scoring weights for tracking (administrative, not scientific-method freeze)

| Phase | Workstream | Overall weight | Current completion | Weighted points | Status |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | Original AutoGen baseline preservation | 3% | 100% | 3.00 | closed |
| 2 | Production-shaped MAF CPU architecture | 3% | 100% | 3.00 | closed |
| 3 | CPU case-study behavioural migration | 3% | 100% | 3.00 | closed |
| 4 | Vincent MCP audit and integration contract | 3% | 100% | 3.00 | closed |
| 5 | GPU scientific workflows and provenance | 8% | 85% | 6.80 | qualified, open limitation |
| 6 | MCP v2, MAF integration, parity | 8% | 100% | 8.00 | closed |
| 7 | Scientific-applicability method and experiment protocol | 14% | 100% | 14.00 | closed, v0.2 frozen |
| 8 | Outcome-bearing experiments, benchmark and analysis | 35% | 20% | 7.00 | active; pre-outcome |
| 9 | Manuscript, artifact, review, submission | 23% | 15% | 3.45 | pending outcome data |
| **TOTAL** | | **100%** | | **51.25 / 100** | **51% rounded** |

**Current score:** overall 51%; current Phase 8 20%; fully closed phases 6/9 (1, 2, 3, 4, 6, 7). Phase 5 is not counted as fully closed under this strict policy; it is scientifically usable with an outstanding exact-history training-reproduction limitation.

## How the assessment is grounded

- Phase 5: Case 1 full 1,248-image GPU inference and phenotype/statistical-conclusion parity are verified; Case 3 functioning full-FT checkpoint has immutable revision, weight integrity and PEFT-isolated GPU compatibility proof. Exact historical Case 3 prepared training-data reproduction is still absent. Completion can reach 100% through validated reproduction **or** an evidence-backed, explicitly documented scope decision showing that exact historical training reproduction is not a required claim, with any required training-ability checks closed separately. Do not imply exact reproduction.
- Phase 7: scientific method v0.2 is content-addressed and re-verified on Plato, including 104/104 research tests. Method verification is not evidence of effectiveness against LLM baselines.
- Phase 8: 20% recognises the pre-registered C0–C9 comparison design, task/metric/hidden-label contracts, preserved offline runtime candidate and qualification harness work. It **does not** count the mechanically scored 12-case fixture as an outcome-bearing LLM experiment. The approved provider path, live non-scientific preflight, controlled pilot, real/provenance-grounded shifted benchmark, model breadth/transport comparison, sealed hidden test and statistical/failure analysis remain to be executed.
- Phase 9: 15% recognises a coherent title, problem statement, claim plan, review threats and manuscript outline/planning. A complete substantive manuscript and empirically grounded tables/figures do not yet exist in the project evidence.

## Scoring discipline going forward

1. Do not grant credit in Phase 8 for unit tests, deterministic fixtures, or engineering validation as though they were scientific performance evidence.
2. Do not raise Phase 8 merely for provider credentials. Progress requires successful authenticated preflight, immutable final controls, and subsequent outcome-bearing benchmark results.
3. Do not raise Phase 9 for conceptual outlines as though they were author-written completed sections or camera-ready figures.
4. Keep **overall completion**, **current Phase 8 completion**, and **phases fully closed** separate. Overall progress is the weighted sum, not an arithmetic average and not an acceptance probability.
5. Update scores only after verifiable new evidence is preserved. Progress scoring is managerial and must not modify the frozen scientific-method protocol.
6. Preserve negative outcomes. If evaluation disproves the principal claim, do not manufacture a rising "paper readiness" score without a scientifically honest change in submission strategy.
7. The operational priority is the supervisor-approved provider/API gate, then non-scientific preflight, then an outcome-bearing C3/C4/C8 pilot. The 2026-11-30 IJCAI go/no-go remains conditional on pilot evidence, not completion percentage.

**Reference state:** Phase 7 v0.2 aggregate `25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`; offline runtime candidate preserved at `baseline/phase8a-runtime-candidate-20261014`; Phase 8 provider gate documented at `docs/research/PHASE8A_PROVIDER_GATE.md`.
