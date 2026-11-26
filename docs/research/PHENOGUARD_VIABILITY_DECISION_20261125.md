# PhenoGuard: research viability decision, 25 November 2026

**Purpose:** justify or decline a bounded research investment, not claim a
submission-ready result. Working title: *Beyond Callability: Scientific
Applicability Verification for Tool-Using Agents Under Distribution Shift*.

## What is measured

- Deterministic resolver: 12/12 exact decisions vs 6/12 for naive requested-tool
  passthrough; 0/7 vs 5/10 inappropriate execution proposals. Mechanical
  development/validation labels, not independent evidence or live LLM comparison.
- Real historical Arabidopsis outputs: 1,248 images, 11,848 predicted masks;
  9,984 synthetic artifact faults/probes. Frozen output validator rejected
  7,488 (75%) vs 1,248 (12.5%) for a custom basic structural reference;
  both accepted all historical originals. Not accuracy, prevalence or
  independent-sample inference. Both missed two complete probe families.
- Scientific engineering: historical Arabidopsis full run with regenerated
  phenotype conclusion agreement; real potato inference and wheat checkpoint
  compatibility; combined MAF/MCP/CUDA runtime tested on RTX A4000; 159
  targeted tests passed at a9d2e88, three later routing regressions passed.
- Revised qualification fixtures: 12 bindings, 9 distinct images, 3
  exact-image metadata controls. Maize images now original PHENOARCH
  whole-plant frames (same plant, two acquisitions); source DOI
  10.5281/zenodo.1002675, original member checksums and bytes verified on
  Plato; full archive checksum not verified. User-reported fixture SHA
  bbaf5e16c739da1412e1f31ac79de1304acf082b13e8311545895ab45e851fb2.
- Reviewed fixtures 0/12, registered real-agent trials 0/108. Final
  runtime/credential approval not granted. No claim of empirical agent superiority.

## Updated novelty risk

Relevant primary sources (initial targeted search, not exhaustive):
- SciToolAgent, Nature Computational Science 2025:
  https://doi.org/10.1038/s43588-025-00849-y (scientific knowledge graph
  and safety checks; not defensible to claim novelty for knowledge-guided
  scientific tool use or safety checks generally).
- SciToolAgent-Evo, July 2026 preprint: https://arxiv.org/abs/2607.28692
  (ontology-aware tool acquisition and 900-task OpenSciToolBench).
- ToolBeHonest, EMNLP 2024:
  https://aclanthology.org/2024.emnlp-main.637/ (tool hallucination and
  inadequate-tool scenarios).
- AgentAbstain, July 2026 preprint: https://arxiv.org/abs/2607.10059
  (paired tasks and tool-agent abstention).
- Model Cards for Model Reporting: https://arxiv.org/abs/1810.03993
  (intended use and limitations).
- Verification and validation for trustworthy scientific machine learning:
  https://doi.org/10.1088/2632-2153/ae59ec.

Candidate distinction: a callable scientific checkpoint may be inappropriate
for a specific evidence-backed operating context despite successful execution
and plausible output. Evaluate grounding, policy enforcement and scientific
output binding separately. Formal applicability contracts, abstention and
paired benchmarks are not novel on their own. Compare against strong
information-matched baselines. No broad first-of-kind claim.

## Immediate falsification diagnostic (no new inference)

At commit 1b0e78c, `scripts/research/phase8_viability_challenge.py` adds:
1. Lexical name/task/species baseline on the known 12 mechanical cases.
   This uses the shared model inventory and a generic training-readiness
   rule, not SOE constraints. It may tie the frozen resolver. It is designed
   after exposure to development cases and not a generalisation result.
2. A stronger ordinary mask/range/reference consistency check, using bounded
   independent compressed-RLE arithmetic and pycocotools area, on historical
   masks and all eight old fault families. Report every original rejection
   and missed fault. This is a local reference, not a formal COCO conformance
   suite or a competing published method.
3. Two real-output source swap probes per historical image: intact wrong
   image's prediction and the same artifact with only filename relabelled.
   A source swap is a known provenance error; it does not prove biological
   mask inaccuracy. The relabelled case can expose limits of both methods.

This diagnostic is **implemented, not run yet**. Results must not be
anticipated. No changes to the frozen method, no hidden labels and no
registered paid trials. Do not add more synthetic diagnostics after this
unless a specific issue warrants one.

## Proposed decision sequence

**Gate A: qualification investment.** Review the physical fixtures and
runtime/provider/billing controls. Use the predeclared 108-trial C3/C4/C8
matrix. It is a feasibility check, not the paper's final benchmark.
Use same ordinary model names/tasks/schema; C8 additionally gets SOEs.
Report all registered trials, failed dispatches, missing traces, coverage,
wrong capability, unsafe proposals and actual dispatch separately. If all
conditions tie or abstain, record that result, not a stronger claim.

**Gate B: independent paper experiment.** Design and seal cases with a
domain expert independent of method authoring. Aim initially for a planning
target of 60 independent matched case groups (120 contexts), not a power
calculation or fixed sample-size commitment. Final size depends on case
availability, expert review and a prospective paired precision/power
calculation. Repeated seeds are nested within cases, not independent
specimens. Balance valid and invalid requests, keep same-image metadata
controls separate from physical cross-dataset shifts, and label ambiguity
explicitly. Current envelopes constrain species and wheat RGB modality
only; do not fabricate view/environment restrictions. New independently
sourced envelopes would require a separately reviewed pre-outcome version
and fresh sealed cases, not a silent modification to Phase 7.

Include C0-C9 as frozen and a strong information-matched prose/model-card
baseline containing the same applicability facts as C8. A deterministic
reference with identical facts tests whether explicit enforcement adds
anything beyond ordinary rule checking. C6/C7/C8 isolate envelope
exposure, pre-verification and post-validation. C3/C8 direct vs MCP
paired semantic checks and a stronger-model subset are planned, not done.
Use expert applicability and permitted use labels, not method-generated
gold. Primary unsafe action and correct execution rates use all registered
trials, with missing-evidence sensitivity bounds. Case-clustered paired
confidence intervals and actual cost/latency; no seed-as-independent
significance. Biological validity requires independent ground truth or
domain-specific outcome evidence, not merely plausible COCO.

**Gate C: submission decision.** The existing internal IJCAI go/no-go is
30 November. Go only if the real qualification demonstrates a credible
failure mechanism, competitive evaluation is feasible, and the novelty
audit supports a distinct contribution. Strong reliability claim requires
C8 to reduce unsafe execution vs C3/C4 without valid-execution accuracy
below both (see frozen protocol). If strong references tie, narrow the
research question or stop this paper route. If safety improves at coverage
cost, report trade-off. If independent evaluation cannot be delivered,
defer to ECAI or later venue rather than inflate a qualification result.

## Request to Valerio

Approve a bounded qualification effort and nominate a domain reviewer;
review the native no-call restriction, provider/model and institutional
data-handling, dedicated key cap and actual runtime freeze. Request feedback
on whether the proposed independent benchmark and information-matched
comparison justify a paper. This is a request to test a plausible idea,
not endorse the conclusion in advance.


## Measured stronger-reference results (26 November 2026)

Researcher supplied successful Plato execution at 59dd0c3. Private report
`data/_staging/phase8_viability_challenge_v0.1.json`, reported SHA-256
`b3a5cd4d9be75d575c74db30958e6a797a4ff333d3f623018e894c0b36ee13eb`.

- Lexical name/task/species reference and frozen resolver both 12/12 exact,
  7/7 correct executable cases, 0 inappropriate proposals. Naive passthrough
  6/12, 5/7 correct executable cases, 5 inappropriate proposals. The
  reference was designed after exposure to the 12 mechanical cases.
- All four artifact references accept 1,248/1,248 historical originals;
  all 11,848 masks have valid run extents and stored areas matching runs.
- All 12,480 constructed variants/probes: basic reference 1,248/12,480
  (10%); frozen validator 8,736/12,480 (70%); mask consistency reference
  8,736/12,480 (70%); source-bound mask reference 11,232/12,480 (90%).
  The two 70% methods detect different faults. Source-bound reference
  outperforms the frozen validator by 20 pp.
- Intact wrong-image predictions: frozen and source-bound validators
  reject 1,248/1,248; basic and mask-only references reject 0.
  After relabelling only the filename, all four accept 1,248/1,248.
  This is an explicit provenance counterexample, not a demonstrated
  natural pipeline error or a biological accuracy failure.
- 22 frozen files unchanged. Zero provider calls, GPU calls, hidden gold
  access or live qualification trials.

**Decision:** no evidence of distinctive superiority over stronger
deterministic references. Do not pitch the existing resolver or artifact
checks as competitive methodological novelty on these results. A narrower
hypothesis concerns scientific consequences of context/provenance errors
and whether verified execution binding plus applicability enforcement
can prevent them when ordinary validation and information-matched agents
cannot. Existing runner checks application-bound identity and hashes;
the artifact-only probe does not establish a vulnerability of that full
runner. No method change without prospective review.

At b62f4d2, a separate retrospective consequence replay is implemented
(not run): reproduce the prior image-ID rotation of complete historical
phenotype vectors and a predeclared, metadata-only, disjoint cross-ecotype
whole-trajectory exchange matching observation schedules. Report changes
in leaf count, projected leaf area, ecotype rankings, mixed ANOVA and
Tukey significance decisions relative to the original prediction-derived
analysis. This measures sensitivity to constructed misassociation, not
biological truth, observed failure rates or agent-level prevention.
The historical source files and method are preserved.

Recommendation to Valerio: conditional investment in a small real-agent
qualification and independent biological consequence study, not a go
decision for the present IJCAI method claim. If the information-matched
baseline ties and no scientific consequence advantage can be shown,
narrow further or stop. Independent fixture approval 0/12; live
qualification 0/108. No additional synthetic fault-volume expansion.
