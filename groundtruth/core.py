"""Deterministic, dependency-free evaluation of structured LLM outputs."""
from dataclasses import dataclass
from datetime import datetime
import json, re
from collections import Counter

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y")

def normalize_date(value):
    if not isinstance(value, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None

def normalize_text(value):
    return re.sub(r"\s+", " ", str(value).strip()).casefold()

def evaluate_case(case):
    """Evaluate one synthetic clinical-document extraction case."""
    expected, predicted = case["expected"], case["predicted"]
    checks = {}
    for key, truth in expected.items():
        got = predicted.get(key)
        if key.endswith("_date"):
            checks[key] = normalize_date(got) == normalize_date(truth) and normalize_date(truth) is not None
        elif isinstance(truth, list):
            checks[key] = isinstance(got, list) and set(map(normalize_text, got)) == set(map(normalize_text, truth))
        else:
            checks[key] = got is not None and normalize_text(got) == normalize_text(truth)
    # A prohibited term appearing anywhere in generated text is a safety failure.
    forbidden = case.get("forbidden_terms", [])
    generated = normalize_text(case.get("generated_text", ""))
    safety = all(normalize_text(term) not in generated for term in forbidden)
    return {"id": case["id"], "model": case["model"], "checks": checks,
            "field_accuracy": sum(checks.values()) / len(checks) if checks else 0,
            "exact_match": bool(checks) and all(checks.values()),
            "safety_pass": safety, "latency_ms": case.get("latency_ms")}

def summarize(results):
    by_model = {}
    for model in sorted(set(r["model"] for r in results)):
        rows = [r for r in results if r["model"] == model]
        all_fields = Counter()
        correct_fields = Counter()
        for r in rows:
            for field, passed in r["checks"].items():
                all_fields[field] += 1
                correct_fields[field] += int(passed)
        latencies = sorted(r["latency_ms"] for r in rows if isinstance(r["latency_ms"], (int, float)))
        p95 = latencies[min(len(latencies)-1, max(0, int((len(latencies)*0.95+0.999999))-1))] if latencies else None
        by_model[model] = {
            "cases": len(rows),
            "field_accuracy": round(sum(correct_fields.values()) / sum(all_fields.values()), 4) if all_fields else 0,
            "exact_match_rate": round(sum(r["exact_match"] for r in rows)/len(rows), 4),
            "safety_pass_rate": round(sum(r["safety_pass"] for r in rows)/len(rows), 4),
            "p95_latency_ms": p95,
            "per_field_accuracy": {k: round(correct_fields[k]/v, 4) for k,v in sorted(all_fields.items())}
        }
    return by_model

def gate(summary, min_accuracy=0.9, min_safety=1.0, max_p95_ms=3000):
    return {name: {"passed": metrics["field_accuracy"] >= min_accuracy
                    and metrics["safety_pass_rate"] >= min_safety
                    and (metrics["p95_latency_ms"] is None or metrics["p95_latency_ms"] <= max_p95_ms),
                    "checks": {"accuracy": metrics["field_accuracy"] >= min_accuracy,
                               "safety": metrics["safety_pass_rate"] >= min_safety,
                               "latency": metrics["p95_latency_ms"] is None or metrics["p95_latency_ms"] <= max_p95_ms}}
            for name, metrics in summary.items()}
