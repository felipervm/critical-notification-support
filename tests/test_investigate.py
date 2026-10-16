import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from investigate import investigate, analyze_recipient

CASE = json.loads((ROOT / "data/case.json").read_text(encoding="utf-8"))

class InvestigationTests(unittest.TestCase):
    def test_expected_five_cases(self):
        self.assertEqual([x["classification"] for x in investigate(CASE)["findings"]],
                         ["expected_behavior", "configuration_review", "configuration_review",
                          "evidence_gap", "customer_verification"])

    def test_does_not_mutate_fixture(self):
        obj = copy.deepcopy(CASE)
        investigate(obj)
        self.assertEqual(obj, CASE)

    def test_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            analyze_recipient({"events": [{"at": "2026-10-15T14:00:00Z", "type": "unknown"}]}, CASE)

    def test_empty_log_is_unknown(self):
        self.assertEqual(analyze_recipient({"events": []}, CASE)[0], "needs_review")

    def test_suppression_without_confirmation(self):
        e = [{"at": "2026-10-15T14:00:00Z", "type": "followup_suppressed"}]
        self.assertEqual(analyze_recipient({"events": e}, CASE)[0], "needs_review")

    def test_suppression_before_confirmation(self):
        e = [{"at": "2026-10-15T14:00:00Z", "type": "followup_suppressed"},
             {"at": "2026-10-15T14:01:00Z", "type": "confirmed"}]
        self.assertEqual(analyze_recipient({"events": e}, CASE)[0], "needs_review")

    def test_out_of_order_timestamps(self):
        e = [{"at": "2026-10-15T14:04:00Z", "type": "accepted"},
             {"at": "2026-10-15T14:00:00Z", "type": "confirmed"}]
        self.assertEqual(analyze_recipient({"events": e}, CASE)[0], "needs_review")

    def test_retry_on_window_end_not_expired(self):
        e = [{"at": CASE["window_end"], "type": "retry_planned"}]
        self.assertEqual(analyze_recipient({"events": e}, CASE)[0], "needs_review")

    def test_duplicate_ids_rejected(self):
        obj = copy.deepcopy(CASE)
        obj["recipients"].append(copy.deepcopy(obj["recipients"][0]))
        with self.assertRaises(ValueError):
            investigate(obj)

    def test_provider_delivered_not_human_ack(self):
        classification, detail, _ = analyze_recipient(CASE["recipients"][4], CASE)
        self.assertEqual(classification, "customer_verification")
        self.assertIn("acknowledgement", detail)

    def test_no_vendor_outage_claim(self):
        self.assertFalse(any("outage" in f["explanation"].lower() for f in investigate(CASE)["findings"]))

    def test_published_report_consistent(self):
        saved = json.loads((ROOT / "data/findings.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, investigate(CASE))

    def test_site_loads_generated_json(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("data/findings.json", html)
        self.assertNotIn("const rows=[", html)

if __name__ == "__main__":
    unittest.main()
