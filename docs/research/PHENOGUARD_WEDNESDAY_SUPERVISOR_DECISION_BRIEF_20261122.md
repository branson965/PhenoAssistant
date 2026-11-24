# PhenoGuard IJCAI 2027: Wednesday 25 November decision brief

**Prepared:** 22 November 2026. **Purpose:** present an accurate, actionable
research status to supervisor. **Scope:** repository Phase 7/8 freeze and
researcher-provided Plato commands; not independently checked institutional
permissions, scientific labels or provider billing.

## One-paragraph supervisor summary

PhenoGuard asks whether a scientific tool that is *callable* is also
scientifically *applicable*, especially under species shift and missing
metadata. The three vision-tool pathways are now demonstrably executable:
Arabidopsis Mask2Former has a historical 1,248-image, hash-verified full
run with reproduced scientific conclusions; potato SAM ViT-H completed a
one-image Plato inference with 13 predicted mask instances and a real C8
COCO structural validation pass; winter-wheat DINOv2 has an audited
full-fine-tuned checkpoint and one-image compatibility evidence. **None of
these results demonstrates an improvement in unsafe scientific execution
versus the baselines.** The decisive C3/C4/C8 comparison has **0/108
outcome-bearing qualification trials** observed in this research record.

## Preliminary measured component results (24 November 2026)

Source: researcher-supplied Plato terminal output from runner commit
`e6eb78d`, completed successfully, with the 22-file Phase 7 freeze
verified at aggregate SHA-256
`25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`.
Local report: `data/_staging/meeting_component_results_lGyfu3.txt`.
No provider calls, GPU calls, hidden gold access or registered agent trials
were made by this component evaluation.

### A. Deterministic scientific applicability

| Metric | Naive requested-tool passthrough | Frozen PhenoGuard resolver |
| --- | ---: | ---: |
| Exact action and capability correctness | 6/12 (50%) | 12/12 (100%) |
| Correct model on executable cases | 5/7 | 7/7 |
| Wrong model on executable cases | 2 | 0 |
| Execution proposed on non-execution cases | 3 | 0 |
| Total execution proposals | 10/12 | 7/12 |
| Inappropriate execution proposals (wrong capability or non-execution case) | 5/10 | 0/7 |
| Unnecessary abstentions | 0 | 0 |

The six corrected scenarios comprise two species-triggered reselections,
two missing-species clarifications, one unsupported-maize abstention and
one training-readiness recommendation. The frozen resolver was run on
all 12 development/validation cases; the comparison reference executes the
requested tool whenever one is supplied, otherwise asks for clarification.
It is **not** the live C3 Manager or C4 generic Critic. The mechanical
labels are deliberately aligned with the contract under test; this is a
component-level correctness demonstration, not independent generalisation
or a measured agent-safety effect. "Execution proposed" is not actual tool
dispatch. No significance or population-level safety claim is justified.

### B. Scientific output fault detection

The preserved genuine potato GPU artifact (13 predicted instances) and
its input were hash-verified before and after this test. The original
passed both JSON parsing and PhenoGuard COCO structural validation.
Nine one-at-a-time, JSON-valid injected faults were rejected by the
validator, whereas none were rejected by ordinary JSON parsing.

| Test set | JSON parser | PhenoGuard COCO validator |
| --- | ---: | ---: |
| Unmodified artifact accepted | 1/1 | 1/1 |
| Targeted invariant faults rejected | 0/9 | 9/9 |
| All injected variants including RLE limitation probe rejected | 0/10 | 9/10 |

Targeted faults: incorrect filename, negative area, area exceeding image
size, confidence outside range, wrong image reference, unknown category,
duplicate annotation ID, inconsistent RLE dimensions and empty RLE counts.
**Negative result:** the additional nonempty RLE string probe was accepted
by the validator. The implementation checks shape and nonemptiness, not
mask decoding. Do not conceal this probe or report universal 100% fault
detection. These are targeted synthetic faults of one real artifact, not
mask accuracy or an independent corruption benchmark.

### Meeting conclusion and remaining experiment

The two component demonstrations support the plausibility of pre-execution
applicability checks and post-execution output checks. They do not establish
that PhenoGuard improves on a real LLM Manager or Critic. The frozen 108-trial
live qualification remains **0/108**; independent fixture review remains
**0/12**. The private 9-image and 12-scenario review worksheets were
successfully generated on Plato on 24 November with owner-only permissions,
and the candidate's technical audit passed. The next scientific decision is
to authorise the reviewed runtime and fixtures, then execute the real
comparative protocol without changing the frozen method.

## Evidence available now

| Tool | Actual evidence | What it does not establish |
| --- | --- | --- |
| Case 1, Arabidopsis Mask2Former | 1,248/1,248 local images and output hashes; regenerated/reference phenotypes align; reported conclusion decision match | Segmentation gold accuracy; agent decision safety |
| Case 2, potato Leaf-only SAM | Plato job 63134, RTX A4000, 13m19s, exit 0; 13 predicted instances; output SHA-256 `5f4aaa3c68e0c0f1035e15bbd79c70a80b84cd998339e6ae448609f62f846180`; `validate_coco(...).safe_to_report=true, issues=[]` | Expert leaf count, mask accuracy, shift robustness, or comparative C8 effect |
| Case 3, winter-wheat DINOv2 | Audited pinned full-FT checkpoint; one official montage inference with matching image/output digests | Individual labelled classification accuracy or tested generalisation |

Detailed references: `docs/research/PHENOGUARD_PLATO_GPU_EVIDENCE_AUDIT_20261122.md`.

## Experiment we actually need to run

Frozen Phase 8 C3/C4/C8 qualification:
- **12 cases (8 development, 4 validation) x 3 conditions x 3 seeds = 108 trials**.
- **C3:** Manager + tool schemas.
- **C4:** Manager + separate generic Critic.
- **C8:** Manager + scientific operating envelope, verifier,
  appropriate clarification/reselection/abstention and output-aware
  post-validation.
- Mechanically adjudicable cases include valid Arabidopsis, potato
  species shift, missing species, valid potato, unsupported maize
  segmentation, maize classification training-readiness requests.
- The same frozen, model-visible scientific facts and matched-case identities
  must be preserved across conditions; application-side images and
  private fixture metadata must never enter Manager/Critic prompts.
- Record decision accuracy, unsafe execution, correct/unnecessary abstention,
  clarification/reselection, actual tool dispatch, and measured model usage.
- **This is harness qualification on development/validation, not a final
  independent hidden benchmark.** Even a perfect 108-trial result would not,
  by itself, demonstrate distribution-shift generalisation.

## Private fixture candidate preparation, 22 November

The researcher confirmed **12/12 blank private entries**, with all eight
source/reviewer fields missing and no maize directory under `data`.
To remove avoidable manual transcription without inventing approval,
`scripts/research/phase8_prefill_local_fixture_candidate.py` now
selects source-referenced real images from the existing AraCrop JSON and
potato CSV metadata. The two missing-species cases reuse the exact
same image as their corresponding valid pair. No hidden labels are read.

The optional `--maize-root` parameter supports an **original, Git
revision-identified PlantDoc checkout** staged privately under `data/_staging`.
It proposes two maize images for three maize scenarios, reusing one
across the training-ready/missing-data contrast to isolate metadata
variation. **This does not verify maize species or imaging comparability.**
PlantDoc contains cropped disease-classification imagery, whereas the
potato segmentation examples use a different acquisition setup. A
species-shift result would be confounded by those visual differences
unless the reviewer approves the specific pairing. Prefer view- and
acquisition-matched maize phenotyping imagery for final analysis.

The helper writes a **new**, ignored candidate file, never overwrites
the private source template or frozen method. It leaves all
`reviewed_species`, `license_or_access_evidence`, and
`reviewer_evidence_id` fields blank and reports the real prefill count.

The original PlantDoc repository advertises CC BY 4.0, but its authors
also report internet-scraped source material. Reviewer verification
of asset-specific access/rights is necessary; no automatic license
or reviewer attestation is recorded.

No candidate file, including a structurally complete one, can activate
an execution gate until independent review and the final reviewed SHA
are recorded in the approved runtime process.

## Updated Plato asset status for Wednesday (researcher terminal evidence)

The researcher has now produced the private candidate file
`data/_staging/phase8_image_fixture_candidate_v0.1.json`, SHA-256
`152c8c929c3da07b3a43743b4afe438ab2ccc0eaea65073600d501787c08755c`.

- **12/12** source records populated with path, image digest, asset ID,
  metadata source and source image ID; **0/12** independently reviewed.
- **36 human review fields still missing**: `reviewed_species`,
  `license_or_access_evidence`, `reviewer_evidence_id` on each case.
- Local PlantDoc repository source commit:
  `5467f6012d78d1c446145d5f582da6096f852ae8`, 244 images observed
  in the two sparse-checkout maize-class directories. This is **source
  revision provenance**, not an independent biological taxonomy review.
- The `phase8_private_fixture_readiness.py` output reports
  `PHASE8_FIXTURE_STRUCTURAL_AUDIT=NOT_RUN_INCOMPLETE`, correctly,
  because missing review attestations cannot be filled by software.
- Clean `git status` confirms the private assets stayed ignored.
- This user terminal evidence has been recorded in GitHub documentation,
  not independently inspected from the Plato filesystem.

### Offline data integrity check

Run the read-only script on Plato:

```bash
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"
env -u OPENROUTER_API_KEY "$PY" \
  scripts/research/phase8_audit_private_fixture_candidate.py
```

It checks source memberships, decoded images, actual digests, PlantDoc
revision and three metadata-only same-image pairs. It does not print
private paths or touch gold labels. If all checks pass, the data are
*technically consistent*, not independently reviewed.

### Human review protocol for the existing candidate

An independent reviewer must inspect actual image bytes and original
metadata for each of the 12 cases and record:

1. **Taxonomic identification:** specific `reviewed_species` for the
   *actual image*. For missing-species prompt cases, this is still the
   image's biological species, not the literal string "UNSPECIFIED".
2. **Access/provenance:** credible evidence identifying original dataset,
   relevant permission/licence and image provenance; do not equate a
   GitHub repository licence with verified third-party source rights.
3. **Review evidence ID:** reference to the actual recorded reviewer
   decision and date, not a generated dummy ID.

For the three maize scenarios, visually assess whether cropped leaf
disease images introduce view/background/disease confounds relative to
whole-plant potato examples. If they do, explicitly reject them for a
claim of *species-isolated visual shift* and choose appropriate
matched-acquisition images. This is a real design decision rather than
a request to fill the JSON mechanically.

After an independent reviewer signs off, preserve the reviewed private
registry and its SHA-256 in a prospective final runtime record.
**Do not edit the historical v0.3 candidate or frozen Phase 7 method
to bypass that signoff**. Actual paid qualification remains blocked
until provider/billing/harness approval is independently evidenced.

## Technical fixture audit passed on Plato (24 November 2026)

Researcher-provided Plato output now confirms
`PHASE8_CANDIDATE_TECHNICAL_AUDIT_PASS=true` with:

- 12/12 image bindings checked; **9 unique image contents**.
- Source type counts, by scenario: `ara=4`, `potato=5`, `maize=3`.
- All 12 content SHA-256s rechecked, AraCrop/potato metadata
  membership checked, original PlantDoc commit validated, and 3/3
  deliberately identical-image metadata pairs verified.
- Private candidate SHA-256 remained
  `152c8c929c3da07b3a43743b4afe438ab2ccc0eaea65073600d501787c08755c`.
- No provider or GPU calls, and the Git worktree was clean.
- **No biological species review, source-rights review or reviewer ID
  has been recorded.** Technically valid file bindings do not make the
  actual image scientifically appropriate or authorised for trials.
- **0/108** C3/C4/C8 qualification trials executed.

The remaining urgent work before experiment execution is **human review
of the 9 distinct image files and their 12 case contexts**, plus a
prospectively reviewed final runtime/provider/billing approval. Do not
reiterate the same GPU and fixture integrity commands as if they were
scientific results.

## Reviewer packet preparation, 24 November

A separate no-network utility creates **two owner-only local CSVs** (the
files are ignored by Git) after re-running the technical candidate audit:

```bash
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"
env -u OPENROUTER_API_KEY "$PY" \
  scripts/research/phase8_prepare_private_review_worksheet.py
```

- `data/_staging/phase8_private_image_review_9unique_v0.1.csv`:
  9 distinct source images, hash, local path, original metadata,
  dimensions and scenario usage, with blank observed-species,
  imaging/shift-confound, source-rights and reviewer fields.
- `data/_staging/phase8_private_scenario_review_12cases_v0.1.csv`:
  12 case contexts, model-visible request species and pair IDs, source
  image hash, blank independent case-specific review fields.

These are **human-review worksheets only**, not a final registry and not
a substitute for inspecting original images and access rights. The script
does not write into the frozen candidate, invent attestations, or switch
on the scientific execution gate. Outputs are private and must not be
committed to GitHub. The researcher should bring these to the 25 Nov
supervisor meeting with unresolved PlantDoc image comparability flagged.

## Immediate go/no-go gates

| Prerequisite | Current evidence | Needed to proceed |
| --- | --- | --- |
| GPU scientific inference compatibility | Supported by Case 1/2/3 real inference checks | **Close** this engineering workstream; avoid re-running |
| Frozen test conditions and study design | Phase 7 method SHA `25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`; 108 planned records | Preserve freeze; no post-outcome tuning |
| Reviewed image fixture registry | `TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256=None` | Complete 12 private source/provenance mappings, genuine independent review and reviewed SHA pin |
| Final runtime + model/provider/billing authority | v0.3 candidate has `scientific_execution_permitted=false`, researcher attestation false | Supervisor-supported, evidenced approved final runtime; do not alter history or fabricate approval |
| Actual C3/C4/C8 integrated live harness | Real MAF/MCP bridge exists, but documented as integration-only; independent final runtime trust pin unset | Review equality of condition exposure, real tool dispatch, C8 validator, C4 Critic, failure preservation and spend controls |
| Cost control | $8 pilot software ceiling and unmeasured forecast `$0.7036416` for Manager/model roundtrips, excluding Critic, retries, actual bill | Approved upstream key cap and measured provider-billed cost/attempt; forecast is not approval |
| Final scientific claim | No confirmed PhenoGuard comparative effects | Independently reviewed, sealed expert benchmark and statistical comparisons after qualification |

**Do not** forge reviewer identities, fill unreviewed species labels as fact,
mark v0.3 approved, switch off guards or run unmetered paid scientific calls.

## Next 48 hours, in parallel

1. **Researcher:** populate the private image fixture template from actual
   approved images, with reviewer/source evidence. It must remain under
   `data/_staging`, never be committed or leaked into model prompts. In
   particular, maize-labelled scenarios require real reviewed maize-image
   provenance if the fixture contract requires image species to match the
   declared request. Do not invent a maize fixture using a potato image.
2. **Supervisor:** decide and record the **provider/model/billing approval**
   and whether the development/validation qualification can be authorised
   before Wednesday. Treat an unreviewed private-image registry as a blocker,
   not as an authorisation placeholder.
3. **Harness reviewer:** verify that the existing MAF proposal bridge has
   the same scientific MCP tool and compatible transport across C3/C4/C8,
   with C4's Critic separately invoked and C8 pre/post checks applied.
   Confirm measured cost reconciliation and stable single-attempt ledger
   before any outcomes.
4. **Researcher + domain expert:** define how the *subsequent hidden benchmark*
   will be independently adjudicated and sealed, including hard shifts and
   matched positive/negative cases. Do not evaluate with hidden labels
   before the runtime and scoring procedure is frozen.
5. **Researcher:** once all final gates are approved, launch the predeclared,
   bounded 108-trial qualification and report **all** outcomes, failures,
   time/cost and paired comparisons. Do not substitute offline fake-agent
   tests for this step.

## Direct private-fixture assessment (read-only)

The older `phase8_image_fixture_registry.py` preflight emits a fixed
`PHASE8_FIXTURE_REAL_IMAGES_BOUND=0` line: it does not inspect existing
private registry bindings. To establish real completeness, run:

```bash
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"
env -u OPENROUTER_API_KEY "$PY" \
  scripts/research/phase8_private_fixture_readiness.py
```

The helper shows all 12 frozen case IDs, declared species, missing private
source/reviewer fields and whether the *existing* structural audit can run.
It prints no private image paths and reads no hidden benchmark gold. A
fully populated local file is still **not independently approved** until
the reviewer checks the truth of the dataset/source/species evidence and
pins the frozen registry SHA.

## No-cost commands that can run on Plato now

From `~/PhenoAssistant`:

```bash
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"
env -u OPENROUTER_API_KEY "$PY" scripts/research/phase8_attempt_ledger.py
env -u OPENROUTER_API_KEY "$PY" scripts/research/phase8_image_fixture_registry.py
env -u OPENROUTER_API_KEY "$PY" scripts/research/phase8_proposal_mcp_bridge_v1.py
```

Optionally create the **blank private** fixture template (only if absent):

```bash
test -e data/_staging/phase8_image_fixture_binding_template_v0.1.json || \
  env -u OPENROUTER_API_KEY "$PY" \
    scripts/research/phase8_image_fixture_registry.py --write-template
```

These commands inspect contract readiness. They **do not** approve scientific
execution, make provider calls or run the 108 trials. Passing their
preflight does not mean the real comparison has begun.

## Wednesday decision requested

1. Authorise or explicitly decline the proposed provider route and hard
   external spend ceiling.
2. Nominate independent reviewer(s) for the 12 private image bindings,
   scientific checkpoint/provenance and the final runtime SHA.
3. Agree the time and responsible person for the first genuinely
   outcome-bearing qualification matrix, *after* the above controls pass.
4. Set the go/no-go criteria for scaling beyond the 108 mechanical
   development/validation trials into the sealed expert benchmark.

**Bottom line:** GPU hardware is **not the present binding constraint**.
The binding constraint is trustworthy and approved experimental execution.
Our paper needs a real comparative effect, not another green engineering test.
