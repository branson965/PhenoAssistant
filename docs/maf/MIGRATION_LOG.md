# PhenoAssistant MAF Linux Migration Log

## 2026-07-29

### Phase
Phase 0 and Phase 1 — Preservation and clean migration branch

### Objective
Preserve the previous MAF proof of concept and establish a clean branch from the upstream `maf` branch for the real Linux-first migration.

### Completed
- Created a local Stage 2A backup archive.
- Recorded its SHA-256 checksum.
- Created and pushed `backup/maf-stage2a-poc`.
- Preserved the offline prototype in commit `48a7709`.
- Fetched `upstream/maf`.
- Created `feature/maf-linux-migration` from `upstream/maf@aff8551`.
- Pushed the migration branch to the fork.

### Evidence
- Backup archive: `PhenoAssistant-stage2a-backup-20260728-145741.tar.gz`
- Backup SHA-256: `b88f382a90de381bbeea2ed28d0bfbd4a5346744d8bef84a5376c2713c3c4c3c`
- Backup branch: `backup/maf-stage2a-poc`
- Backup commit: `48a7709`
- Migration branch: `feature/maf-linux-migration`
- Migration baseline: `aff8551`

### Blocked
- Nottingham GPU/cluster account not yet available.
- Canonical scientific fixture not yet approved.
- Final OpenRouter model not yet selected.
- Vincent's authoritative MCP interface not yet confirmed.

### Next
- Add local environments and generated Python files to `.gitignore`.
- Commit the master execution plan and this log.
- Create a dedicated Ubuntu VM in VirtualBox.
- Clone the migration branch inside Linux.
- Record Linux runtime evidence.

### Overall completion
30%

## 2026-08-02

### Phase

Phase 2 — Linux environment and MAF proof-of-concept validation

### Objective

Establish a viable Linux development environment and determine whether
the preserved MAF proof of concept reproduces successfully under
Python 3.11.

### Completed

- Established a GitHub Codespaces Linux environment.
- Verified Ubuntu 24.04.4 LTS on x86_64.
- Verified the migration branch at commit `76d8267`.
- Created an isolated worktree at backup commit `48a7709`.
- Created a Conda Python 3.11.15 environment under `/tmp`.
- Installed the pinned MAF proof-of-concept requirements.
- Verified that `pip check` reports no broken requirements.
- Ran the complete MAF proof-of-concept test suite.
- Confirmed that all 42 tests pass on Linux.
- Confirmed a pytest exit code of zero.
- Confirmed that testing produced no repository changes.
- Diagnosed and removed an ignored 7.8 GB CUDA virtual environment.
- Restored approximately 7.8 GB of persistent workspace capacity.
- Restored normal Git operation after removing a stale index lock.

### Evidence

- Platform: GitHub Codespaces
- Operating system: Ubuntu 24.04.4 LTS
- Source commit: `48a7709fb3e8ed53c505f321d0ac910a70644cb2`
- Python: 3.11.15
- MAF Core: 1.11.0
- MAF OpenAI provider: 1.11.0
- OpenAI SDK: 2.52.0
- Dependency result: no broken requirements
- Test result: 42 passed in 0.92 seconds
- Pytest exit code: 0
- Runtime document: `docs/maf/LINUX_RUNTIME_CODESPACES.md`
- Validation document: `docs/maf/MAF_POC_LINUX_VALIDATION.md`

### Findings

- The isolated MAF implementation is portable to Linux.
- Codespaces provides a viable CPU-side Linux development environment.
- CPU migration and GPU validation must use separate environments.
- The OpenAI SDK resolved to version 2.52.0 rather than the 2.48.0
  version previously recorded on macOS.
- The complete PhenoAssistant environment remains substantially larger
  and requires a deliberate CPU-first compatibility strategy.

### Blocked

- The original AutoGen PhenoAssistant baseline has not yet been run.
- The full repository environment has not yet been reproduced.
- Nottingham cluster and GPU access remain unavailable.
- Vincent's authoritative MCP interface remains unconfirmed.
- The approved scientific validation fixture remains pending.

### Next

- Commit and push the Linux runtime and validation evidence.
- Inspect the original application imports and configuration side
  effects.
- design a CPU-first AutoGen baseline environment;
- attempt to run the original application before modifying `agents.py`;
- document every dependency and provider blocker.

### Overall completion

35%

## 2026-08-03 — Original environment recreation

### Phase

Phase 3B — unchanged original Linux environment attempt

### Result

Passed.

### Evidence

- Source commit: `0de2dc429a2103615d60ccacce326a11bfb8f837`
- Environment SHA-256: `d91e714151187ce697914dbd1ad9f8d8759940d1070f39d866f29a62153bbdc1`
- Python: 3.11.10
- AutoGen: 0.2.39
- OpenAI SDK: 1.62.0
- Exit code: 0
- Duration: 458 seconds
- Environment size: approximately 12 GB
- Dependency result: no broken requirements

### Findings

- The unchanged Conda specification resolves and installs on Ubuntu.
- Environment compatibility is not the current blocker.
- The next boundary is the original AutoGen application's import and runtime behaviour.
- A CPU-only environment is now an optimisation rather than a prerequisite.

### Next

- Commit the Phase 3B evidence.
- Use the exact original environment for controlled module-import tests.
- Inspect configuration requirements without exposing values.
- Attempt `agents.py` in an isolated subprocess.
- Classify the first runtime, credential, provider or hardware boundary.

### Overall completion

40%

## 2026-08-03 — Original AutoGen Linux runtime baseline

### Phase

Phase 4 — original AutoGen import and deterministic execution baseline

### Result

Passed with documented runtime and configuration boundaries.

### Runtime corrections

- Installed Ubuntu `libgl1=1.7.0-1build1`.
- Installed `segment_anything==1.0` from official commit
  `dca509fe793f601edb92606367a655c15ac00fdf`.

### Findings

- All selected repository function modules import successfully.
- The unmodified `agents.py` import reaches unconditional Hugging Face
  authentication and fails with HTTP 401 because `HF_TOKEN` is empty.
- With Hugging Face login replaced in memory for boundary discovery,
  the complete AutoGen object graph constructs successfully.
- The Manager has 25 tool schemas.
- The User Proxy has 25 executable functions.
- Schema and function names match exactly.
- Registered calculator execution preserves the semantic result.
- AutoGen serializes the mapped integer result to a string.
- Importing `agents.py` creates `tmp/db/chroma.sqlite3`.
- No deliberate live Azure/OpenAI request was made.

### Architectural implications

The MAF implementation should separate configuration, authentication,
provider construction, agent construction, retrieval persistence, and
workflow execution. Optional Hugging Face functionality must not block
module import or unrelated CPU workflows.

### Next

- Commit the original AutoGen Linux baseline evidence.
- Produce the detailed AutoGen-to-MAF component migration map.
- Confirm provider scope with the research team before live execution.
- Implement the first MAF vertical slice without modifying scientific
  tool behavior.

### Overall completion

50%
