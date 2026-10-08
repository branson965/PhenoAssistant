# Working Paper Plan — Scientific Applicability Under Distribution Shift

**Status:** research direction frozen for engineering design, not yet experimentally validated  
**Date:** 2026-10-08

## Working title

**Beyond Callability: Scientific Applicability Verification for Tool-Using Agents Under Distribution Shift**

`PhenoGuard` remains a possible system/method name, not the scientific claim.

## Central problem

A scientific tool can be:

- installed;
- schema-valid;
- callable;
- executable;

while still being scientifically inappropriate for the current data.

Examples include a model applied to the wrong species, acquisition view, sensor, environment, or operating condition.

The paper therefore separates **technical callability** from **scientific applicability**.

## Core research question

> When distribution shift makes an available scientific tool inappropriate, can a tool-using agent recognise the mismatch before execution, and can explicit applicability grounding reduce unsafe scientific actions without collapsing useful coverage?

## Proposed primitive

### Scientific Operating Envelope

Each scientific capability declares machine-readable applicability metadata such as:

- scientific task;
- species/domain;
- modality;
- acquisition geometry;
- environment;
- training-data provenance;
- required metadata;
- supported ranges;
- output semantics;
- assumptions;
- known failure conditions;
- version/checkpoint.

The current request/data conditions are checked against that envelope before execution.

## Allowed system decisions

- `EXECUTE`
- `RESELECT`
- `CLARIFY`
- `ABSTAIN`
- `RECOMMEND_TRAINING`

The system should optimise both safety and useful coverage; always-abstain is not a successful policy.

## Proposed claims

### Claim 1 — callability is insufficient

Schema-valid/callable scientific tools can still be selected outside their valid operating conditions, especially under distribution shift.

### Claim 2 — explicit scientific applicability grounding helps

Scientific Operating Envelopes plus pre-execution verification reduce scientifically inappropriate executions relative to ordinary tool descriptions/schemas and generic critique.

### Claim 3 — reliability should survive transport choice

The applicability intervention should behave consistently across direct Python and MCP-backed execution when Manager, prompt, model, data, and canonical scientific implementation are held constant.

### Optional Claim 4 — shift changes agent failure signatures

Distribution shift changes not only task accuracy but routing, verification, clarification, and termination failures.

## Minimum experimental questions

### E1 — applicability

Can the agent distinguish technically callable from scientifically valid capabilities?

### E2 — distribution shift

How does that distinction degrade under species, acquisition/view, environment, sensor/modality, or metadata shift?

### E3 — intervention

Do Scientific Operating Envelopes plus verification/clarification/abstention reduce unsafe execution while retaining coverage?

### E4 — portability

Do the results persist under both direct and MCP-backed execution?

### E5 — architecture ablation, if feasible

Compare:

- model-only;
- single tool-using agent;
- Manager/coordinated-agent architecture.

## Baselines

At minimum:

1. model without tools;
2. Manager + tool names;
3. Manager + tool descriptions;
4. Manager + tool schemas / MCP metadata;
5. Manager + generic Critic;
6. deterministic structural/schema validation;
7. Scientific Operating Envelope only;
8. envelope + verifier;
9. full verify/reselect/clarify/abstain/post-validation method;
10. expert oracle.

## Paired-case design

Construct minimally different valid/invalid cases so refusal is not sufficient.

Example:

```text
Arabidopsis + top-view + controlled environment
→ EXECUTE
```

paired with:

```text
Arabidopsis + side-view + field environment
→ RESELECT / CLARIFY / ABSTAIN
```

Other paired perturbations may target:

- species;
- sensor;
- view;
- season;
- region;
- image quality/resolution;
- missing metadata;
- conflicting metadata;
- checkpoint provenance;
- output semantics.

Real dataset/domain shifts should be used where possible; prompt-only metadata perturbations are secondary stress tests, not substitutes for genuine shift.

## Evaluation

Required metrics should include:

- valid-execution accuracy;
- unsafe-execution rate;
- correct abstention rate;
- unnecessary-abstention rate;
- clarification accuracy;
- re-selection accuracy;
- coverage;
- risk-coverage curves;
- repeated-run reliability;
- final-answer grounding to tool evidence;
- latency/cost;
- failure-category distribution.

Where possible, scoring should be deterministic. Human/domain-expert adjudication is reserved for scientific applicability labels that cannot be mechanically established.

## Reviewer attacks to design against

- "This is just hand-written rules."
- "Generic agent abstention already exists."
- "Capability contracts already exist."
- "MCP benchmarking already exists."
- "This is just PhenoAssistant engineering."
- "The shifts are synthetic prompt edits."
- "The benchmark was built to favour the method."
- "A generic Critic would do the same thing."
- "The method is safe only because it refuses everything."
- "This is not actually multi-agent."
- "Results depend on one framework/model."
- "The LLM judge is grading another LLM."

The final experiment design must answer these before submission.

## Relationship to the PhD

The paper occupies the system-level reliability strand of:

**Multi-Agentic AI for Robust Multimodal Agricultural Reasoning under Distribution Shift**

It complements model/VLM-level distribution-shift papers by asking whether the **agentic decision layer** remains reliable when the data move outside a capability's operating envelope.

## Venue strategy

### Stretch target — IJCAI 2027

Internal go/no-go date: **2026-11-30**.

Proceed only if by that gate:

- GPU baseline is complete;
- MCP v2 + MAF integration is complete;
- method implemented;
- benchmark protocol frozen;
- strong pilot result exists;
- major baselines exist;
- updated novelty audit remains favourable.

### Primary fallback — ECAI 2027

Use the additional development/evaluation window rather than rushing a weak IJCAI submission.

AAMAS 2028 remains a high-fit later option if the work requires a longer experimental programme.

## Scope discipline

MAF migration, MCP migration, and PhenoAssistant integration are **infrastructure**.

They are not the main novelty claim.

The research contribution is scientific-applicability verification and safe decision-making under distribution shift.
