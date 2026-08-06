# Real Tukey and live statistical-tool selection

## Status

Validated by the Phase 6F gate.

## Scope

This phase validates two distinct claims:

1. The preserved `functions.stat_test.perform_tukey_test` implementation runs on a deterministic plant dataset and returns the expected three pairwise treatment comparisons.
2. A natural-language request sent through the production Microsoft Agent Framework Manager selects `perform_tukey_test`, supplies the correct model-controlled arguments, executes the real scientific implementation exactly once, and returns a grounded summary.

## Scientific fixture

The phase reuses `tests/fixtures/maf/mixed_anova_plants.csv`:

- 90 observations;
- 30 plants;
- three repeated time points;
- three treatments: `control`, `low`, and `high`;
- ten plants per treatment.

The preserved Tukey implementation first averages repeated observations by `plant_id` and `treatment`, then delegates to `pingouin.pairwise_tukey`. This documents existing repository behaviour; it is not a new statistical method or a correction to the scientific implementation.

## Deterministic gate

`scripts/maf/validate_real_tukey.py` verifies:

- the unsaved return branch is a list of records;
- exactly three pairwise treatment comparisons are returned;
- every expected treatment pair is present;
- every p-value lies in `[0, 1]`;
- all three pairs are significant at alpha 0.05 for the deterministic fixture.

`tests/science/test_real_tukey_runtime.py` makes this validation repeatable without a provider call.

## Live Manager gate

`tests/live/test_openrouter_tukey_selection.py` is skipped by default. With `RUN_LIVE_OPENROUTER=1`, it:

- constructs the production OpenRouter-backed MAF application;
- gives the Manager a natural-language Tukey request;
- makes calculator and ANOVA fail-fast so incorrect selection is visible;
- records the real Tukey invocation;
- requires exactly one Tukey call;
- verifies the trusted dataset path remains application-bound;
- verifies `height`, `treatment`, and `plant_id` are passed correctly;
- compares the live tool result with direct execution;
- checks that the final response mentions all treatment groups and is framed as a Tukey/significance conclusion.

Provider variability is handled by a bounded five-attempt integration-test policy. Every failed attempt remains visible in terminal evidence. This is integration evidence, not a controlled comparative evaluation and not a claim that MAF is superior to AutoGen.

## Reproduction

Offline:

```bash
python scripts/maf/validate_real_tukey.py
python -m pytest tests/science/test_real_tukey_runtime.py -q
```

Live:

```bash
RUN_LIVE_OPENROUTER=1 \
OPENROUTER_API_KEY='set-outside-the-repository' \
OPENROUTER_MODEL='openrouter/free' \
python -m pytest tests/live/test_openrouter_tukey_selection.py -q -s
```

No API key is written to repository files or evidence logs.
