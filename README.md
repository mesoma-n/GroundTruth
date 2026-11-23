# GroundTruth Lab

**Reproducible evaluation and release gates for structured LLM outputs.**

A small, runnable Python engineering project demonstrating how to compare model outputs **using the same test cases**, detect regressions in date extraction and structured fields, measure latency, and fail a release gate when quality falls below a threshold.

> **Portfolio demo, not a production medical system.** All patient names and cases are synthetic. The example model labels (`baseline`, `candidate`) represent simulated outputs, not live calls to commercial models. No real clinical efficacy, deployment, or performance claims are made.

## Architecture

```text
Synthetic JSON cases
        |
        v
  Field validators ----> date normalization / text / unordered lists
        |
        v
  Per-case results ----> exact match / safety term check / latency
        |
        v
  Model comparison ----> per-field accuracy / p95 latency
        |
        v
  Release gates -------> PASS / FAIL + machine-readable report.json
```

## Run in 30 seconds

Requires Python 3.10+; no runtime dependencies.

```bash
python -m unittest discover -s tests -v
python -m groundtruth
```

To fail CI when a model misses the default 90% field-accuracy threshold:

```bash
python -m groundtruth --strict
```

The included GitHub Actions workflow demonstrates a lower, explicitly demo-only accuracy threshold (70%) so both simulated models can pass CI. Set it to 90% for production-style enforcement.

## What is measured

| Metric | Meaning |
| --- | --- |
| Field accuracy | Correct expected fields / total expected fields |
| Exact-match rate | Fraction of cases with every field correct |
| Per-field accuracy | Accuracy for each structured field, including dates |
| Safety pass rate | Fraction of outputs without case-specific forbidden terms |
| p95 latency | Nearest-rank 95th percentile of supplied latencies |
| Release gate | Configurable accuracy, safety, and latency checks |

**Limitations:** Forbidden-term matching is a lightweight smoke test, **not** clinical safety evaluation. String matching does not verify medical correctness. The demo uses supplied latency values rather than measuring API requests. Real deployments require expert review, privacy controls, de-identification, calibration, and robust semantic evaluation.

## Input format

Each JSON case includes `id`, `model`, `expected`, `predicted`, and optional `generated_text`, `forbidden_terms`, and `latency_ms`. Use identical `id` and `expected` across models for comparable tests.

## Design choices

- **Standard-library only:** instant setup and easy code review.
- **Deterministic fixtures:** compare model candidates without sampling noise.
- **Per-field metrics:** catch failures hidden by aggregate accuracy.
- **Release gates:** translate evaluation results into a deploy/no-deploy decision.
- **CI:** run tests automatically on each push.

## Next steps

Add a Bedrock/OpenAI adapter, semantic grading, confidence intervals, dataset versioning, PII redaction, and human review queues.

## Author note

This is an independently created portfolio demonstration of evaluation engineering. It does not contain employer code or confidential datasets.
