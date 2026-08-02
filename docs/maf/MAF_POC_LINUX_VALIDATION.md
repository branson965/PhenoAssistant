# MAF Proof-of-Concept Linux Validation

## Status

Passed.

## Date

2 August 2026.

## Purpose

Validate whether the preserved Microsoft Agent Framework proof of
concept reproduces unchanged in a Linux environment before beginning
the migration of the real PhenoAssistant application.

## Environment

- Platform: GitHub Codespaces
- Operating system: Ubuntu 24.04.4 LTS
- Architecture: x86_64
- Kernel: 6.8.0-1052-azure
- CPU allocation: 2 logical CPUs
- Memory allocation: approximately 7.8 GiB
- Python: 3.11.15
- Source branch: `backup/maf-stage2a-poc`
- Source commit: `48a7709fb3e8ed53c505f321d0ac910a70644cb2`

The Python environment, Conda packages and pip cache were placed under
`/tmp` to avoid using the persistent Codespaces workspace.

## Package versions

- `agent-framework-core==1.11.0`
- `agent-framework-openai==1.11.0`
- `openai==2.52.0`
- `pydantic==2.13.4`
- `pytest==8.4.2`
- `pytest-asyncio==0.26.0`

## Dependency validation

Command:

~~~bash
python -m pip check
~~~

Result:

~~~text
No broken requirements found.
~~~

## Test execution

Command:

~~~bash
PYTHONDONTWRITEBYTECODE=1 \
python -m pytest tests/maf_poc -q
~~~

Result:

~~~text
.......................................... [100%]
42 passed in 0.92s
~~~

Pytest exit code:

~~~text
0
~~~

## Repository integrity

The test execution produced no tracked or untracked changes in the
temporary proof-of-concept worktree.

## Findings

1. The preserved MAF provider and offline Agent-to-FunctionTool proof
   of concept is portable from macOS Intel to Ubuntu Linux x86_64.
2. Python 3.11 can be provisioned successfully through Conda in
   GitHub Codespaces.
3. MAF Core 1.11.0 and the MAF OpenAI provider 1.11.0 install and
   execute successfully on Ubuntu 24.04.
4. The Linux resolver selected `openai==2.52.0`, while the previous
   macOS environment recorded `openai==2.48.0`.
5. The test suite validates the isolated MAF framework path. It does
   not yet validate the complete PhenoAssistant application or its
   scientific workflows.

## Storage incident

An ignored repository-local virtual environment occupied approximately
7.8 GB and contained CUDA, PyTorch and Triton binaries. This exhausted
the persistent Codespaces filesystem.

The environment was safely removed after confirming that:

- no files under `venv/` were tracked by Git;
- `venv/` was explicitly excluded by `.gitignore`;
- no active process was using the environment;
- a package freeze was preserved temporarily under `/tmp`.

After removal:

- repository usage decreased from approximately 8.1 GB to 279 MB;
- approximately 7.8 GB became available under `/workspaces`;
- the stale `.git/index.lock` was removed;
- Git functionality was restored.

This confirms that CPU-side migration and GPU-side validation should
use separate environments.

## Limitations

This validation did not:

- run the original AutoGen PhenoAssistant application;
- install the complete repository `environment.yml`;
- execute a live OpenRouter model call;
- execute a real scientific analysis;
- run computer-vision models;
- validate CUDA or GPU functionality;
- run `demo.ipynb` or the case-study notebooks;
- integrate MCP.

## Conclusion

The isolated MAF proof of concept has been successfully reproduced on
Linux. The project can proceed to reproducing the original AutoGen
PhenoAssistant baseline on Linux before modifying the real agent
implementation.
