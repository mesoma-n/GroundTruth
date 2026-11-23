import argparse, json, sys
from pathlib import Path
from .core import evaluate_case, summarize, gate

def main():
    parser = argparse.ArgumentParser(description="Reproducible LLM output evaluation")
    parser.add_argument("--input", default="examples/synthetic_cases.json")
    parser.add_argument("--output", default="report.json")
    parser.add_argument("--min-accuracy", type=float, default=0.9)
    parser.add_argument("--max-p95-ms", type=float, default=3000)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any model fails its gate")
    args = parser.parse_args()
    cases = json.loads(Path(args.input).read_text())
    if not isinstance(cases, list) or not cases:
        parser.error("input must contain a nonempty JSON array")
    results = [evaluate_case(c) for c in cases]
    summary = summarize(results)
    gates = gate(summary, min_accuracy=args.min_accuracy, max_p95_ms=args.max_p95_ms)
    report = {"dataset": args.input, "summary": summary, "release_gates": gates, "cases": results}
    Path(args.output).write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"summary": summary, "release_gates": gates}, indent=2))
    print(f"\nReport written to {args.output}")
    if args.strict and not all(v["passed"] for v in gates.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
