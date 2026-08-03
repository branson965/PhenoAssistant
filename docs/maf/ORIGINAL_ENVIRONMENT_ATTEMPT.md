# Original PhenoAssistant Environment — Linux Recreation

## Status

Passed.

## Purpose

Determine whether the repository's original, unchanged `environment.yml` can be recreated on Linux before changing dependencies or migrating the AutoGen orchestration to Microsoft Agent Framework.

## Source

- Branch: `feature/maf-linux-migration`
- Source commit: `0de2dc429a2103615d60ccacce326a11bfb8f837`
- Environment file SHA-256: `d91e714151187ce697914dbd1ad9f8d8759940d1070f39d866f29a62153bbdc1`
- Environment specification modified for attempt: no

## Host

- GitHub Codespaces
- Ubuntu 24.04.4 LTS
- x86_64
- 2 logical CPUs
- approximately 7.8 GiB RAM
- no GPU exposed
- Conda 26.1.1

## Result

- Conda solver: passed
- Conda transaction: passed
- Pip installation: passed
- Exit code: `0`
- Duration: `458` seconds
- Environment size: approximately `12 GB`
- Python: `3.11.10`
- `pip check`: no broken requirements
- `pip check` exit code: `0`

Key installed packages include:

- `autogen-agentchat==0.2.39`
- `openai==1.62.0`
- `pandasai==2.4.2`
- `pytorch==2.4.1`
- `torchvision==0.19.1`
- `torchaudio==2.4.1`
- `transformers==4.45.2`
- `datasets==3.0.1`
- `accelerate==1.0.1`
- `pingouin==0.5.5`
- `numpy==1.26.4`
- `pandas==1.5.3`
- `scipy==1.14.1`

## Storage observation

The original environment occupies approximately 12 GB and includes CUDA, NVIDIA, PyTorch and vision-training dependencies even though the Codespace does not expose a GPU. Environment and cache data were stored under `/tmp`, protecting persistent repository storage.

## Findings

1. The original environment resolves and installs on Ubuntu Linux without modification.
2. Strict dependency pins and original channels remain available.
3. Environment recreation is not the current blocker.
4. The next compatibility boundary is the original AutoGen application's import and runtime behaviour.
5. A smaller CPU-only environment remains desirable, but it is now an optimisation rather than a prerequisite.

## Evidence

- `docs/maf/evidence/original-environment-attempt-20260803T162551Z.txt`
- `docs/maf/evidence/original-environment-explicit-20260803T162551Z.txt`
- `docs/maf/evidence/original-environment-pip-freeze-20260803T162551Z.txt`

## Limitations

This phase does not yet prove that `agents.py` imports, credentials are valid, Hugging Face login succeeds, Azure is reachable, CUDA is usable, model checkpoints exist, or the demo and case-study notebooks execute.

## Conclusion

The original PhenoAssistant environment has been recreated unchanged on Ubuntu Linux. The next phase is to establish the original AutoGen runtime baseline using this exact environment.
