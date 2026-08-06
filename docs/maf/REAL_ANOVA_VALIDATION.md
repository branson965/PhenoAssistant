# Real ANOVA runtime validation

This phase validates the original `functions.stat_test.perform_anova`
implementation on a deterministic repeated-measures plant dataset.

It covers direct CPU execution and the production MAF path:

`Manager -> perform_anova tool -> typed adapter -> original implementation`

## Reproduce

```bash
python -m pip install -r requirements-maf-science.txt
python scripts/maf/validate_real_anova.py
python -m pytest tests/science/test_real_anova_runtime.py -q
```

A pass proves real CPU ANOVA execution and production-graph delegation. It does
not yet prove live model selection of ANOVA, Tukey correctness, GPU execution,
retrieval, MCP integration, multimodal interpretation, or migration of all
25 original tools.


## Direct-execution import-path recovery

The first validation attempt installed the scientific runtime and generated all
planned artifacts, but direct execution of
`scripts/maf/validate_real_anova.py` failed before ANOVA execution with
`ModuleNotFoundError: No module named 'functions'`.

This was a script-entry-point defect rather than a scientific-runtime defect.
When Python executes a file by path, the script directory is placed on
`sys.path`; the repository root is not guaranteed to be present. The validator
now resolves and inserts the repository root before importing the preserved
implementation from `functions.stat_test`.

The original statistical implementation was not modified. The failed attempt
remains preserved outside the repository at:

`/workspaces/.phenoassistant-runtime/logs/phase6e-real-anova-20260805T165936Z.log`


## Explicit tool dependency isolation

The first graph execution resolved every default production tool even though
the request exercised only ANOVA. That imported the legacy calculator module,
which has unrelated HTTP dependencies, and stopped execution before the ANOVA
tool call.

The validation graph now binds the preserved `perform_anova` implementation
explicitly and injects fail-fast calculator and Tukey callables. This proves the
real ANOVA adapter and production Manager path without treating unrelated tool
dependencies as prerequisites. Selecting calculator or Tukey during this
validation fails visibly.
