# Task-conditioned scientific validity: prospective decision proposal

Status: PROPOSAL FOR SUPERVISOR AND DOMAIN REVIEW; not an approved protocol,
not a change to the Phase 7 method freeze, not authorization for inference.

## Motivation

The 27 November credibility report shows species lookup equals the observed
two-model oracle on 221/221 observations. Correctly routed accepted outputs
still have task-dependent errors (36/221 projected-area relative error >10%;
21/221 absolute count error >2; two IoU <.5). These are exploratory thresholds,
not domain-validated safety labels. Confidence ranking is inconsistent and
the same masks can lead to different measurements through XOR versus union.

## Research question and falsifiable contribution

Can a tool-using agent determine when a requested scientific conclusion is
supported by available evidence, and choose report, qualify, clarify, abstain,
or a bounded verification action, better than an information-matched
conventional policy? Scientific validity is relative to the requested
quantity, reference conditions, provenance and acceptable error. A report
can be accurate about visible projected area but not total harvested leaf
area, count, dry mass, or biological significance. Do not equate those tasks.

## Two distinct stages

A. Complete previously registered 108 C3/C4/C8 development/validation trials
only after independent 12-case review, actual runtime and budget approval.
Retain negative outcomes and no-call decisions. These trials qualify the
existing system; not an independent test of a new method.

B. Separate prospective study. Use development outputs for hypothesis
generation only; independently select new eligible biological plants
and tasks before seeing outcomes. Candidate source: unused PhenoLeaf-TS
plant sequences (255 nominal remaining, subject to identity/training
overlap audit and custom licence). Do not treat frames as independent.
Seek an independent potato source or explicitly restrict conclusions to
Arabidopsis if none is available. No reuse of original 63 plants as test.
No raw restricted data or mask files sent to external providers without
specific permission. Use local model execution and permitted derived
summaries, with reviewer-approved data handling.

## Proposed task families for domain review

1. Visible instance count vs projected foreground union area from same
   image and model output. Reference labels and units are task-specific.
2. Longitudinal projected-area or count change for the same plant:
   verify identity, timestamps, acquisition and comparability; evaluate
   error of change against independently annotated endpoints.
3. Physical/biological interpretation: distinguish projected pixel area
   from calibrated area, total harvested area and dry mass. A request for
   unidentifiable quantity must be qualified or clarified, not converted
   by unsupported inference. Use available measured references only.
4. Provenance and measurement semantics: naturally occurring problems
   separated from deliberately constructed mismatches. Synthetic stress
   tests are secondary and not estimates of natural prevalence.

Reviewers independently specify task gold, required information, allowed
actions, units, biologically justified tolerances, uncertainty and
adjudication rules before model outcomes are exposed. Retain disagreements.
Include valid-report controls, not only adversarial cases.

## Competitive comparisons (same information, same action/cost budgets)

- Correct species lookup + source-bound structural/mask validation.
- Above + ordinary model-specific score/empty-output checks + explicit
  unit, measurement, metadata and provenance rules.
- Development-calibrated conventional risk/coverage policy using observable
  features (confidence, overlap, count, area fraction and temporal checks
  only when lawful and available); no test labels or threshold fitting.
- Agent with information-equivalent prose/model cards and scientific rules,
  without proposed structured intervention.
- Proposed agent with task-conditioned evidence/decision mechanism, if
  independently approved. Do not privilege it with extra observations
  or tools. If extra verification actions are allowed, give every capable
  policy the same menu and budget; report costs separately.
- Oracle is a descriptive upper bound, not a deployable baseline.

Primary endpoint candidate: task-specific unacceptable reported result rate
among reports at matched coverage, with report/qualify/abstain semantics and
false abstention explicitly defined. Also report all-attempt scientific
utility, coverage, appropriate clarification, verification costs, and
case-level paired outcomes. Predefine one primary contrast and operating
point with reviewer, choose sample size from development-only variability
and practically meaningful effect, and cluster analysis by biological plant
(or source cluster for other tasks). No post-hoc threshold selection.
Distinguish natural errors from constructed perturbations, and actual agent
behavior from replay.

## Continue/stop gate

Continue method-paper route only if consequential errors remain under
strong conventional policy and proposed intervention offers meaningful
improvement at matched coverage/cost on independently reviewed cases.
If deterministic rules suffice or no real agent errors occur, report
negative results and consider benchmark/diagnostic or pipeline correction
rather than claim novel agent efficacy. No additional bulk development
inference required before this decision. No new paid trials without approvals.
