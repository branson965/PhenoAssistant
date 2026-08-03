# Original AutoGen Linux Runtime Baseline

## Status

Deterministic structural baseline passed.

## Scope

This baseline evaluates the original AutoGen-based PhenoAssistant on Ubuntu Linux using the repository's unchanged Conda environment plus the minimum runtime corrections needed to import the full application.

It does not claim that a live Azure/OpenAI conversation, GPU workflow, model checkpoint, notebook, or scientific case study has completed.

## Source

- Branch: `feature/maf-linux-migration`
- Source commit: `9438c97bc6ba3e56322362c9de5ba9fe3c46d2d0`
- Original environment: `/tmp/conda-envs/phenoassistant-original`
- Python: `3.11.10`
- AutoGen: `0.2.39`

## Runtime corrections

The original unchanged environment had already been preserved and documented in Phase 3B. Phase 4 required two additional runtime corrections:

1. Ubuntu host package `libgl1=1.7.0-1build1` to provide `libGL.so.1` for OpenCV.
2. `segment_anything==1.0`, installed from the official repository at commit `dca509fe793f601edb92606367a655c15ac00fdf`.

The repository already documents the Segment Anything Git install in `README.md`, while `environment.yml` contains a commented `segment-anything` entry.

## Import baseline

The initial controlled import matrix passed for the core AutoGen, scientific, pipeline, dataset, and search modules.

OpenCV-dependent modules initially failed because `libGL.so.1` was absent. After installing `libgl1`, these imports passed:

- `cv2`
- `functions.compute_phenotypes`
- `functions.image_classification`
- `functions.image_regression`

`functions.instance_segmentation` then exposed the undeclared `segment_anything` requirement. After installing the pinned official package, these imports passed:

- `segment_anything`
- `functions.leaf_only_sam`
- `functions.instance_segmentation`

`pip check` continued to report no broken requirements.

## Configuration boundary

The tracked `.env.yaml` matches `upstream/maf`.

The secret fields were classified without printing values:

- `HF_TOKEN`: empty
- `OPENAI_API_KEY`: empty
- `PANDASAI_API_KEY`: empty

The unmodified `agents.py` import failed at line 44 because it performs an unconditional Hugging Face login during module import. Hugging Face returned HTTP 401 for the empty token.

This is an application-bootstrap configuration boundary, not an environment, AutoGen, CUDA, or MAF failure.

## Structural bootstrap

For boundary discovery only, `huggingface_hub.login` was replaced in memory with a no-op. No repository source was edited.

With that isolated bypass:

- `agents.py` imported successfully;
- the original AutoGen object graph was constructed;
- the Manager exposed 25 LLM-facing tool schemas;
- the User Proxy exposed 25 executable functions;
- the schema and executable function name sets matched exactly;
- six inspected agent objects were constructed successfully;
- no deliberate Azure/OpenAI request was made.

## Deterministic registered-tool execution

The `calculator` tool was executed both directly and through the User Proxy function map.

Results:

- direct result: integer `12`
- registered result: string `"12"`
- normalized semantic result: integer `12`

This confirms AutoGen serializes the registered function result at the execution boundary while preserving its semantic value.

Final markers:

- `REGISTRATION_PARITY_PASS`
- `REGISTERED_TOOL_EXECUTION_PASS`
- `PHASE4B_DETERMINISTIC_BASELINE_PASS`

## Import-time side effects

Importing `agents.py` created `tmp/db/chroma.sqlite3`.

This confirms that the original application couples retrieval storage initialization to module import. The generated database was removed after each controlled test and was not committed.

The migration should separate configuration loading, credential validation, optional Hugging Face authentication, provider construction, agent construction, retrieval-storage initialization, and workflow execution.

## Evidence

- `docs/maf/evidence/phase4a-import-preflight-20260803T172346Z.log`
- `docs/maf/evidence/phase4a-libgl-retest-20260803T174425Z.log`
- `docs/maf/evidence/phase4a-segment-anything-20260803T175329Z.log`
- `docs/maf/evidence/phase4b-agents-import-20260803T175753Z.log`
- `docs/maf/evidence/phase4b-agents-import-hf-bypass-20260803T180524Z.log`
- `docs/maf/evidence/phase4b-object-graph-20260803T182010Z.log`
- `docs/maf/evidence/phase4b-registered-tool-execution-20260803T184806Z.log`

## Limitations

This phase does not prove successful live Azure/OpenAI inference, Manager tool selection, multi-agent ordering or argument construction, notebook execution, GPU execution, checkpoint availability, scientific equivalence, or Case 1/Case 3 completion.

## Conclusion

The original AutoGen PhenoAssistant is structurally loadable on Ubuntu Linux after two documented runtime corrections and an isolated bypass of unconditional import-time Hugging Face authentication.

Its complete 25-tool registration graph is internally consistent, and a registered deterministic tool executes with preserved semantics.

The next phase should map the original bootstrap, agents, tools, and side effects into explicit Microsoft Agent Framework components before rewriting `agents.py`.
