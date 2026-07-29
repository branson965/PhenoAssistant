# PhenoAssistant AutoGen-to-Microsoft Agent Framework Linux Migration
## Master Execution Plan

**Owner:** Branson  
**Created:** 29 July 2026  
**Status:** Active  
**Current overall completion:** 30%  
**Current branch:** `feature/maf-linux-migration`  
**Target upstream branch:** `vios-s/PhenoAssistant:maf`  
**Baseline commit:** `aff8551`  
**Backup branch:** `backup/maf-stage2a-poc`  
**Backup commit:** `48a7709`

---

# 1. Purpose

This document is the single execution plan for migrating the real PhenoAssistant repository from AutoGen to Microsoft Agent Framework (MAF), running it on Linux, validating the repository demo and priority cases, integrating GPU-dependent capabilities later, aligning with Vincent's MCP work, and submitting a pull request to the upstream `maf` branch.

The plan is phase-gated. Do not work on several phases simultaneously.

For each phase:

1. Read only the current phase.
2. Complete the listed tasks.
3. Produce the required evidence.
4. Check the acceptance gate.
5. Commit and push only after the gate passes.
6. Update the migration log and completion percentage.
7. Move forward only after review.

---

# 2. Final mission

The final deliverable must:

1. Preserve `v2` as the original AutoGen baseline.
2. Run the original PhenoAssistant on Linux as far as credentials and compute allow.
3. Document package and platform compatibility decisions.
4. Migrate the real agent/orchestration layer from AutoGen to MAF.
5. Reuse existing scientific and computer-vision tools rather than rewriting them unnecessarily.
6. Run `demo.ipynb` through the MAF path.
7. Reproduce the important workflows in `case1.ipynb` and `case3.ipynb`.
8. Attempt `case2.ipynb` after the priority cases.
9. Use a Linux GPU environment for vision execution and training when access becomes available.
10. Integrate or align with Vincent's MCP implementation.
11. Produce a focused evaluation of tool selection, ordering, arguments, outputs, failures, latency, token use, and cost.
12. Provide reproducible documentation.
13. Submit a reviewable pull request to upstream `maf`.

---

# 3. Definition of 100% completion

## Repository and Git

- [ ] `v2` remains a clean AutoGen baseline.
- [ ] Migration work is based on `upstream/maf`.
- [ ] Previous POC work remains preserved.
- [ ] No secrets, virtual environments, weights, or caches are committed.
- [ ] Commit history is understandable.
- [ ] A pull request targets `vios-s/PhenoAssistant:maf`.

## Linux baseline

- [ ] Dedicated Linux environment documented.
- [ ] Original environment attempted unchanged.
- [ ] Compatibility problems recorded.
- [ ] Original AutoGen run attempted on Linux.
- [ ] Successful and blocked functionality documented.

## MAF migration

- [ ] Real Manager/orchestration path uses MAF.
- [ ] Existing tools are exposed through validated MAF contracts.
- [ ] Model-controlled inputs are restricted.
- [ ] Tool results return to the agent correctly.
- [ ] State/session behaviour is explicit.
- [ ] Import-time side effects are controlled.
- [ ] A supported provider path exists.

## Functional validation

- [ ] `demo.ipynb` works through MAF.
- [ ] Case 1 is validated.
- [ ] Case 3 training is executed on suitable hardware.
- [ ] Case 2 is attempted and documented.
- [ ] GPU blockers are resolved or accepted by supervisors.

## MCP and evaluation

- [ ] Vincent's authoritative MCP interface is identified.
- [ ] MAF invokes at least one relevant tool through MCP.
- [ ] Direct and MCP output parity is checked.
- [ ] Prompts, fixtures, models, and tools are controlled.
- [ ] Tool selection, order, arguments, outputs, failures, latency, tokens, and cost are recorded.
- [ ] Setup, limitations, and reproduction steps are documented.

---

# 4. Project history

Completed before the clean migration branch:

- Architecture audit of PhenoAssistant.
- MAF decision log.
- Python 3.11 MAF environment.
- `agent-framework-core==1.11.0`.
- `agent-framework-openai==1.11.0`.
- Import-safe OpenRouter configuration.
- Explicit MAF client factory.
- Nineteen Stage 1 tests.
- Offline native MAF Agent and FunctionTool prototype.
- Forty-two total local tests before recalibration.
- Independent Stage 2A review.
- Backup archive:
  `PhenoAssistant-stage2a-backup-20260728-145741.tar.gz`
- SHA-256:
  `b88f382a90de381bbeea2ed28d0bfbd4a5346744d8bef84a5376c2713c3c4c3c`
- Backup branch:
  `backup/maf-stage2a-poc`
- Backup commit:
  `48a7709`
- Active clean branch:
  `feature/maf-linux-migration`
- Active branch baseline:
  `upstream/maf@aff8551`

---

# 5. Branch strategy

```text
upstream/v2
    Original AutoGen baseline.

upstream/maf
    Feng's integration target.

feature/maf-openrouter-poc
    Completed provider/configuration research.

backup/maf-stage2a-poc
    Preserved offline prototype with known review issues.

feature/maf-linux-migration
    Active team deliverable targeting upstream/maf.
```

Rules:

1. Never commit directly to `v2` or `upstream/maf`.
2. Never force-push the migration branch.
3. Keep one logical change per commit.
4. Push at the end of every successful work session.
5. Do not merge the backup branch wholesale.
6. Reuse individual ideas or commits only where they support the real migration.

---

# 6. Non-negotiable principles

- AutoGen is the experimental baseline, not disposable legacy code.
- Linux is the canonical migration and evaluation environment.
- CPU-side orchestration comes before GPU setup.
- Run the original system before changing the framework.
- Change one major variable at a time.
- Wrap existing scientific code before considering rewrites.
- Imports must not silently read credentials, log in, download weights, construct live clients, mutate global state, or write files.
- Never commit API keys, Hugging Face tokens, Azure credentials, OpenRouter credentials, passwords, or private SSH keys.
- Evidence must match the claim being made.

---

# 7. Completion model

| Milestone | Completion |
|---|---:|
| Architecture, MAF investigation, and preserved POC | 20% |
| Backup and clean migration branch | 30% |
| Dedicated Linux VM and repository clone | 35% |
| Original Linux environment recreated/documented | 45% |
| AutoGen Linux baseline attempted/documented | 55% |
| MAF provider integrated into Linux migration environment | 60% |
| First real Manager-to-tool MAF path | 70% |
| Lightweight tools and `demo.ipynb` migrated | 80% |
| Priority cases validated on CPU | 85% |
| GPU vision and training validated | 92% |
| MCP integration and parity checks | 96% |
| Evaluation, documentation, and PR | 100% |

Current position: **30%**.

---

# 8. Time estimate

Assuming 3–5 focused hours per day:

- Best case: 4–5 weeks.
- Realistic: 6–8 weeks.
- Significant dependency, credential, or GPU delays: 9–12 weeks.

---

# 9. Daily operating procedure

## Start

```bash
git status
git branch --show-current
git pull --ff-only
```

Record the current phase, today's single objective, expected evidence, and known blocker.

## During work

- Make one narrow change.
- Run the smallest relevant check.
- Inspect the diff.
- Stop if the change expands beyond the current phase.
- Record errors exactly.
- Do not randomly change package versions.

## End

```bash
git status --short
git diff --check
git diff --stat
```

Where tests exist:

```bash
python -m pytest -q
python -m pip check
```

Commit exact files only, then push.

---

# 10. Phase 0 — Preserve previous POC

**Status:** Complete  
**Completion after phase:** 25%

- [x] Backup archive created.
- [x] SHA-256 recorded.
- [x] Backup branch created.
- [x] Five Stage 2A files committed.
- [x] Backup branch pushed.
- [x] Working tree cleaned.

---

# 11. Phase 1 — Create clean migration branch

**Status:** Complete  
**Completion after phase:** 30%

- [x] Fetched `upstream/maf`.
- [x] Created `feature/maf-linux-migration`.
- [x] Pushed branch to fork.
- [x] Confirmed tracking.

Current housekeeping issue: `.venv-maf/` is untracked on the clean branch.

---

# 12. Phase 1.5 — Branch hygiene and plan commit

**Status:** Current  
**Estimated time:** 30–60 minutes  
**Completion remains:** 30%

## Tasks

1. Confirm branch and status.

```bash
cd ~/research/phenoassistant
git branch --show-current
git status --short --untracked-files=all
```

2. Add these entries to `.gitignore` without removing existing rules:

```gitignore
# Local environments
.venv-maf/
.venv/
venv/

# Python generated files
__pycache__/
*.py[cod]
.pytest_cache/

# macOS
.DS_Store

# Local credentials
.env
.env.*
!.env.example
.env.yaml
```

3. Save this plan as:

```text
docs/maf/MAF_LINUX_MIGRATION_MASTER_PLAN.md
```

4. Create:

```text
docs/maf/MIGRATION_LOG.md
```

5. Commit only the plan, log, and ignore rules.

```bash
git add .gitignore docs/maf/MAF_LINUX_MIGRATION_MASTER_PLAN.md docs/maf/MIGRATION_LOG.md
git diff --cached --check
git diff --cached --stat
git commit -m "docs: add MAF Linux migration execution plan"
git push
```

## Gate

- [ ] `.venv-maf/` no longer appears in status.
- [ ] Plan is committed.
- [ ] Migration log is committed.
- [ ] Working tree is clean.
- [ ] Branch is pushed.

# 13. Phase 2 — Create a dedicated Linux VM

**Status:** Not started  
**Estimated time:** 2–4 hours  
**Completion after phase:** 35%

## Decision on the existing VirtualBox VMs

VirtualBox is installed and working. The screenshot shows existing course/lab VMs, including `Coursework1` and `Cybersecurity LabVM Workstation 20230210`.

Do not use the cybersecurity course appliance for this migration unless there is no alternative. It may contain old packages, unknown credentials, course-specific hardening, or previous modifications.

Create a dedicated VM:

```text
PhenoAssistant-Ubuntu
```

## Recommended specification

| Resource | Value |
|---|---:|
| Guest OS | Ubuntu 22.04 LTS 64-bit |
| CPUs | 4 |
| RAM | 8 GB; 6 GB where host memory is constrained |
| Disk | 60 GB dynamically allocated |
| Video memory | 128 MB |
| Network | NAT |
| Shared clipboard | Bidirectional |
| GPU expectation | None |

The VM is for Linux compatibility, dependency resolution, MAF migration, lightweight tools, and notebooks. GPU/CUDA work will occur later on a real Linux GPU machine or university cluster.

## VM tasks

1. Download an official Ubuntu 22.04 LTS desktop ISO.
2. Create the VM in VirtualBox.
3. Install Ubuntu with hostname `phenoassistant-linux`.
4. Update the OS.
5. Install base packages.
6. Enable SSH.
7. Clone the migration branch.
8. Record the runtime.
9. Take snapshot `00-clean-ubuntu`.

## Base packages

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y \
  git curl wget ca-certificates build-essential \
  unzip zip jq tree tmux htop openssh-server
sudo systemctl enable --now ssh
```

## Optional SSH from Mac

VirtualBox NAT forwarding:

- Protocol: TCP
- Host IP: `127.0.0.1`
- Host port: `2222`
- Guest port: `22`

Mac command:

```bash
ssh -p 2222 <linux-user>@127.0.0.1
```

## Git setup and clone

```bash
git config --global user.name "Branson"
git config --global user.email "<git-email>"
mkdir -p ~/research
cd ~/research
git clone https://github.com/branson965/PhenoAssistant.git
cd PhenoAssistant
git remote add upstream https://github.com/vios-s/PhenoAssistant.git
git fetch --all --prune
git switch feature/maf-linux-migration
```

Verify:

```bash
git remote -v
git branch -vv
git status
git rev-parse --short HEAD
```

## Runtime record

Create `docs/maf/LINUX_RUNTIME.md` and record the outputs of:

```bash
date
uname -a
cat /etc/os-release
uname -m
nproc
free -h
df -h
git branch --show-current
git rev-parse HEAD
```

## Gate

- [ ] Dedicated VM boots.
- [ ] Base packages install.
- [ ] Repository is cloned inside Linux.
- [ ] Correct branch is checked out.
- [ ] Runtime is recorded.
- [ ] Snapshot `00-clean-ubuntu` exists.
- [ ] No GPU claim has been made.

Suggested commit:

```bash
git add docs/maf/LINUX_RUNTIME.md docs/maf/MIGRATION_LOG.md
git commit -m "docs: record initial Linux migration runtime"
git push
```

---

# 14. Phase 3 — Recreate the original environment on Linux

**Estimated time:** 2–5 working days  
**Completion after phase:** 45%

## Objective

Attempt the repository's original environment before adding MAF.

## Environment strategy

Maintain two environments:

```text
phenoassistant-autogen
    Original Linux baseline.

phenoassistant-maf
    Migration environment created only after the baseline is understood.
```

## Tasks

1. Install Miniforge or another approved Conda distribution.
2. Inspect `environment.yml`.
3. Attempt it unchanged.
4. Log every error.
5. Build a compatibility matrix.
6. Create a documented CPU variant only when required.

Inspect:

```bash
sed -n '1,260p' environment.yml
grep -nEi 'python|autogen|openai|torch|cuda|transformers|pandas|pingouin|jupyter|huggingface' environment.yml
```

Attempt unchanged:

```bash
conda env create -f environment.yml \
  2>&1 | tee docs/maf/linux-environment-create.log
```

Do not randomly edit versions after the first failure.

## Compatibility document

Create `docs/maf/LINUX_COMPATIBILITY.md` with:

| Package/component | Original requirement | Linux result | CPU phase? | GPU phase? | Decision | Evidence |
|---|---|---|---|---|---|---|

Classify failures as:

- unavailable version;
- OS incompatibility;
- Python incompatibility;
- dependency conflict;
- CUDA-only requirement;
- network failure;
- authentication failure;
- missing system library;
- repository bug;
- unclear.

## CPU baseline variant

Where GPU packages block setup, create `environment-linux-cpu.yml`.

Rules:

1. Copy the original.
2. Change only proven blockers.
3. Document every change.
4. Keep AutoGen.
5. Do not add MAF yet.

Export evidence:

```bash
conda env export --no-builds > docs/maf/AUTOGEN_LINUX_ENVIRONMENT.yml
python -m pip freeze > docs/maf/AUTOGEN_LINUX_PIP_FREEZE.txt
python -m pip check
```

## Gate

- [ ] Original environment attempt logged.
- [ ] Compatibility matrix exists.
- [ ] Every change is justified.
- [ ] CPU-capable AutoGen environment exists, or exact blocker is documented.
- [ ] MAF has not been added to the baseline environment.
- [ ] No secrets are committed.

---

# 15. Phase 4 — Run the original AutoGen system on Linux

**Estimated time:** 2–4 working days  
**Completion after phase:** 55%

## Objective

Observe the original application on Linux before migration.

## Tasks

1. Inventory required credentials privately.
2. Test imports from smallest to largest.
3. Attempt agent construction.
4. Run a minimal prompt.
5. Run a lightweight tool.
6. Attempt notebooks in priority order.
7. Record exact stopping points.

Notebook order:

1. `demo.ipynb`
2. `case1.ipynb`
3. `case3.ipynb`
4. `case2.ipynb`

Use Jupyter interactively first:

```bash
jupyter lab
```

## Baseline report

Create `docs/maf/AUTOGEN_LINUX_BASELINE.md`.

| Item | Result | Tool(s) | Output | Blocker | GPU? | Credential? |
|---|---|---|---|---|---|---|

A partial baseline is valid when the stopping point is evidenced. Examples:

- provider credentials unavailable;
- GPU weights unavailable;
- environment succeeds but import fails;
- lightweight tools work but vision does not.

## Gate

- [ ] Original system attempted.
- [ ] Exact stopping point documented.
- [ ] Lightweight and GPU failures distinguished.
- [ ] Baseline commit/environment recorded.
- [ ] Notebook results captured.
- [ ] No MAF change contaminated the baseline.

---

# 16. Phase 5 — Create the Linux MAF environment

**Estimated time:** 1–3 working days  
**Completion after phase:** 60%

## Objective

Create a separate migration environment that retains working dependencies and adds MAF.

Clone the environment:

```bash
conda create --name phenoassistant-maf --clone phenoassistant-autogen
conda activate phenoassistant-maf
```

Install verified MAF versions:

```bash
python -m pip install \
  agent-framework-core==1.11.0 \
  agent-framework-openai==1.11.0
python -m pip check
```

## Reuse Stage 1 carefully

Inspect commits before reuse:

```bash
git show --stat e337394
git show --stat 372ee3e
```

Where appropriate:

```bash
git cherry-pick e337394
git cherry-pick 372ee3e
```

Do not accept conflicts blindly.

Run Stage 1 tests on Linux:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/maf_poc -q
python -m pip check
```

Export environment state:

```bash
conda env export --no-builds > docs/maf/MAF_LINUX_ENVIRONMENT.yml
python -m pip freeze > docs/maf/MAF_LINUX_PIP_FREEZE.txt
```

## Gate

- [ ] Separate baseline and MAF environments exist.
- [ ] MAF installs cleanly.
- [ ] Provider tests pass on Linux.
- [ ] Package versions are recorded.
- [ ] Baseline environment remains unchanged.
- [ ] No live model call is required.

---

# 17. Phase 6 — Build the migration map

**Estimated time:** 1 working day  
**Completion remains:** 60%

Create `docs/maf/AUTOGEN_TO_MAF_MIGRATION_MAP.md`.

For every component record:

- file and symbol;
- responsibility;
- prompt;
- tools;
- provider;
- state/history;
- nested agents;
- human input;
- streaming;
- side effects;
- external services;
- proposed MAF replacement;
- difficulty and priority.

Migration order:

1. Provider.
2. Manager.
3. One lightweight tool.
4. Statistics.
5. Tables and plotting.
6. Retrieval.
7. Vision.
8. Training.
9. Nested/specialist agents.
10. MCP.

## Gate

- [ ] Every real agent is mapped.
- [ ] Every tool is inventoried.
- [ ] Side effects are identified.
- [ ] First real migration slice is selected.
- [ ] No broad rewrite has begun.

---

# 18. Phase 7 — First real Manager-to-tool MAF slice

**Estimated time:** 2–4 working days  
**Completion after phase:** 70%

## Objective

Make one real PhenoAssistant prompt execute one existing repository tool through MAF on Linux.

Initial structure may be side by side:

```text
agents_maf.py
```

or:

```text
maf_runtime/
    provider.py
    manager.py
    tools.py
```

Do not delete the AutoGen path.

Choose a tool that is deterministic, CPU-safe, low-side-effect, already present, and easy to verify.

Required path:

```text
User prompt
    -> MAF Manager
    -> one existing tool
    -> real repository output
    -> Manager summary
```

Checks:

- exact tool name;
- exact schema;
- exact arguments;
- one invocation;
- output preserved;
- exceptions visible;
- no arbitrary path access;
- state/session explicit.

## Gate

- [ ] One real prompt runs through MAF.
- [ ] One real tool executes.
- [ ] Output is verifiable.
- [ ] AutoGen path still exists.
- [ ] Linux tests pass.
- [ ] Code is committed and pushed.

# 19. Phase 8 — Migrate lightweight tools and `demo.ipynb`

**Estimated time:** 5–10 working days  
**Completion after phase:** 80%

## Objective

Move enough real functionality to MAF for `demo.ipynb` to run.

## Tool order

1. Pure deterministic utilities.
2. Statistics.
3. Table operations.
4. Plotting.
5. Retrieval.
6. Safe file operations.
7. Vision wrappers.
8. Training wrappers.

For every tool document:

- MAF-visible name;
- description;
- input schema;
- trusted inputs;
- model-controlled inputs;
- return type;
- files read/written;
- network use;
- GPU requirement;
- error behaviour;
- fixture.

Preserve Manager behaviour:

- planning intent;
- tool selection;
- parameter generation;
- tool ordering;
- evidence-based summary.

Define sessions explicitly:

- stateless versus stateful;
- when a session starts;
- what history is retained;
- how tests isolate runs;
- how notebooks reset state.

Adapt `demo.ipynb` only where required:

- imports;
- construction;
- run calls;
- response extraction;
- output display.

## Gate

- [ ] `demo.ipynb` runs through MAF.
- [ ] Tool selection is appropriate.
- [ ] Arguments are inspectable.
- [ ] Outputs are verifiable.
- [ ] Failures are explicit.
- [ ] CPU-safe tools work on Linux.

---

# 20. Phase 9 — Validate priority cases on CPU

**Estimated time:** 3–6 working days  
**Completion after phase:** 85%

## Priority

1. Case 1.
2. Case 3.
3. Case 2.

## Case 1

Separate and record:

- segmentation;
- table analysis;
- plotting;
- interpretation;
- ANOVA;
- Tukey;
- summary.

Run CPU-safe parts first.

## Case 3

Validate:

- interpretation of training request;
- selected data/training tools;
- arguments;
- path handling;
- execution up to GPU boundary.

Do not claim training completion without real training.

## Case 2

Attempt after priority cases and document whether it is mainly a data/species variation.

Create `docs/maf/CASE_VALIDATION.md`:

| Case/task | Expected tools | Actual tools | Arguments correct? | Output correct? | Blocker | Next |
|---|---|---|---|---|---|---|

## Gate

- [ ] Case 1 CPU path documented.
- [ ] Case 3 reaches expected compute boundary.
- [ ] Case 2 attempted or explicitly deferred.
- [ ] GPU blockers are separated from MAF blockers.
- [ ] No unsupported scientific claim is made.

---

# 21. Phase 10 — GPU and vision validation

**Estimated time:** 5–10 working days after access  
**Completion after phase:** 92%

## Objective

Run GPU-dependent vision and training workflows on suitable Linux hardware.

Preferred environment:

- Nottingham GPU cluster;
- approved project server;
- suitable remote Linux GPU host.

The VirtualBox VM remains the CPU development environment.

## Required access

- Nottingham account;
- SSH credentials;
- allocation;
- storage path;
- CUDA-compatible node;
- Hugging Face token;
- model-weight access.

Record GPU runtime:

```bash
nvidia-smi
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
PY
```

Validate:

- model import;
- weight access;
- device placement;
- inference;
- output files;
- deterministic settings where possible;
- memory use;
- runtime;
- training data preparation;
- checkpointing;
- evaluation;
- recovery from failure.

## Gate

- [ ] GPU runtime documented.
- [ ] Vision model executes.
- [ ] Case 1 GPU step runs.
- [ ] Case 3 training runs.
- [ ] Outputs are verified.
- [ ] Hardware/package versions recorded.
- [ ] Credentials and weights are not committed.

---

# 22. Phase 11 — MCP integration

**Estimated time:** 3–7 working days  
**Completion after phase:** 96%

## Objective

Integrate Vincent's authoritative MCP interface and verify parity with direct execution.

Confirm before coding:

- branch;
- server entry point;
- tool names;
- schemas;
- transport;
- authentication;
- error format;
- supported cases.

Integration order:

1. Lightweight deterministic tool.
2. Statistical tool.
3. Vision tool.
4. Training tool where appropriate.

For identical inputs compare:

- direct callable;
- direct MAF tool;
- MCP result.

Record:

- output parity;
- schema differences;
- transport failures;
- latency overhead;
- error visibility.

## Gate

- [ ] MAF invokes at least one real MCP tool.
- [ ] Direct/MCP parity checked.
- [ ] Failures visible.
- [ ] Scientific values are not silently changed.
- [ ] Cases use the agreed MCP path where intended.

---

# 23. Phase 12 — Controlled evaluation

**Estimated time:** 3–5 working days  
**Completion after phase:** 98%

## Conditions

Where feasible compare:

1. AutoGen baseline.
2. MAF direct tools.
3. AutoGen + MCP.
4. MAF + MCP.

Control:

- prompt;
- dataset;
- model;
- temperature;
- tool catalogue;
- tool descriptions;
- hardware;
- retry policy;
- iteration limits;
- session state.

Metrics:

- overall tool chain;
- tool existence;
- tool appropriateness;
- argument correctness;
- tool order;
- output correctness;
- grounding in tool evidence;
- failure rate;
- latency;
- tokens;
- cost.

Create:

```text
docs/maf/EVALUATION.md
results/maf-evaluation/
```

Do not commit sensitive raw logs.

## Gate

- [ ] Conditions are comparable.
- [ ] Metrics are defined.
- [ ] Results are reproducible.
- [ ] Negative findings retained.
- [ ] Limitations explicit.
- [ ] No unsupported claim that MAF is superior.

---

# 24. Phase 13 — Documentation and PR

**Estimated time:** 2–3 working days  
**Completion after phase:** 100%

## Documentation

- [ ] Linux setup.
- [ ] Compatibility matrix.
- [ ] AutoGen baseline.
- [ ] Migration map.
- [ ] MAF architecture.
- [ ] Provider configuration.
- [ ] Tool schemas.
- [ ] Notebook instructions.
- [ ] Case validation.
- [ ] GPU runtime.
- [ ] MCP integration.
- [ ] Evaluation.
- [ ] Known limitations.
- [ ] Secret handling.

## Final checks

```bash
git status
git diff --check
git fetch upstream
git diff upstream/maf...HEAD --stat
git diff upstream/maf...HEAD
python -m pytest -q
python -m pip check
```

Search for accidental secrets:

```bash
git grep -n "sk-"
git grep -n "api_key"
git grep -n "token"
git grep -n "password"
```

Variable names may be legitimate; secret values are not.

Suggested PR title:

```text
MAF: migrate PhenoAssistant workflows on Linux
```

Suggested draft PR command:

```bash
gh pr create \
  --repo vios-s/PhenoAssistant \
  --head branson965:feature/maf-linux-migration \
  --base maf \
  --title "MAF: migrate PhenoAssistant workflows on Linux" \
  --draft
```

## Final gate

- [ ] Branch clean.
- [ ] Tests pass.
- [ ] Documentation complete.
- [ ] No secrets.
- [ ] PR targets `maf`.
- [ ] Linux setup reproducible.
- [ ] Limitations honest.
- [ ] Supervisors approve.

---

# 25. Risk register

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Original environment fails on Linux | High | High | Preserve logs; create minimal documented CPU variant |
| Azure credentials unavailable | High | Medium | Document baseline blocker; use approved provider for migration |
| MAF conflicts with original versions | Medium | High | Separate baseline and MAF environments |
| VM lacks GPU | Certain | Medium | VM for CPU; cluster for GPU |
| Nottingham account delayed | Medium | High | Complete CPU migration first |
| Vision weights unavailable | Medium | High | Record model IDs and request access early |
| `agents.py` import side effects | High | Medium | Isolate configuration and construction |
| Multi-agent mapping is complex | Medium | High | Manager and one tool first |
| MCP interface changes | Medium | Medium | Confirm authoritative branch before integration |
| Model outputs are nondeterministic | High | Medium | Controlled runs and repeated trials |
| Scientific values are coerced | Medium | High | Strict serialization and parity checks |
| Scope becomes overwhelming | High | High | Work only on current phase |
| Coding-agent quota unavailable | High | Low | Small diffs, tests, manual review, ChatGPT support |
| Laptop/VM failure | Medium | High | Push daily and take snapshots |

---

# 26. Issue template

```markdown
## Issue: <short name>

### Phase
Phase X

### Environment
- OS:
- Python:
- Branch:
- Commit:
- Environment:
- Hardware:

### Command
```bash
...
```

### Expected
...

### Actual
...

### Full error
```text
...
```

### Classification
- [ ] Dependency
- [ ] Python version
- [ ] Operating system
- [ ] Credential
- [ ] Network
- [ ] GPU/CUDA
- [ ] Repository bug
- [ ] MAF API
- [ ] MCP
- [ ] Unknown

### Attempts
1. ...
2. ...

### Evidence
...

### Proposed next action
...
```

---

# 27. Migration log template

```markdown
## YYYY-MM-DD

### Phase
Phase X — Name

### Objective
...

### Completed
- ...

### Evidence
- ...

### Blocked
- ...

### Next
- ...

### Overall completion
XX%
```

---

# 28. Meeting update template

```text
Since the last meeting, I completed Phase X of the Linux-first MAF migration.

The concrete deliverable is [deliverable].

The evidence is [test/notebook/log/commit].

The main technical finding was [finding].

The current blocker is [blocker], which affects [scope].

The next phase is [phase], where I will [single objective].

The AutoGen baseline remains preserved, and the migration branch still targets upstream maf.

Overall completion is now XX%.
```

---

# 29. Immediate next action

Do not start Phase 3 yet.

The current sequence is:

1. Complete Phase 1.5.
2. Commit this plan and the migration log.
3. Create a dedicated Ubuntu VM.
4. Clone the migration branch inside it.
5. Record the Linux runtime.
6. Take the clean snapshot.
7. Stop at the Phase 2 gate.
8. Review the evidence before beginning environment installation.

---

# 30. Current completion log

## Completed

- Architecture investigation.
- MAF provider research.
- Stage 1 provider foundation.
- Stage 2A offline POC.
- Independent review.
- Backup archive.
- Backup branch and commit.
- Clean migration branch from upstream `maf`.
- Migration branch pushed.

## In progress

- Branch hygiene.
- Master plan and migration log.
- Dedicated Linux VM.

## Blocked

- Nottingham cluster/GPU account.
- Canonical scientific fixture.
- Final OpenRouter model.
- Vincent's authoritative MCP interface.

## Overall completion

**30%**
