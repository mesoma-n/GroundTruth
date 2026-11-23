import unittest
from groundtruth.core import normalize_date, evaluate_case, summarize, gate

class EvaluationTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(normalize_date("March 5, 2026"), "2026-03-05")
        self.assertEqual(normalize_date("03/05/2026"), "2026-03-05")
        self.assertIsNone(normalize_date("March 40, 2026"))
    def test_case(self):
        row = {"id":"a","model":"x","expected":{"visit_date":"2026-03-05","diagnosis":"Flu"},
               "predicted":{"visit_date":"03/05/2026","diagnosis":"flu"},
               "generated_text":"draft", "forbidden_terms":["confidential"]}
        result = evaluate_case(row)
        self.assertTrue(result["exact_match"])
        self.assertTrue(result["safety_pass"])
    def test_safety(self):
        row = {"id":"b","model":"x","expected":{"diagnosis":"flu"},
               "predicted":{"diagnosis":"flu"},"generated_text":"DO NOT SHARE",
               "forbidden_terms":["do not share"]}
        self.assertFalse(evaluate_case(row)["safety_pass"])
    def test_gates(self):
        r = [evaluate_case({"id":"a","model":"x","expected":{"x":"a"},
                            "predicted":{"x":"a"},"latency_ms":120})]
        self.assertTrue(gate(summarize(r))["x"]["passed"])
    def test_missing_field(self):
        r = evaluate_case({"id":"a","model":"x","expected":{"x":"a"},"predicted":{}})
        self.assertFalse(r["exact_match"])

if __name__ == "__main__":
    unittest.main()
