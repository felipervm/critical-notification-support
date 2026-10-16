"""Evidence-based interpretation of fictional notification traces; no vendor integration."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"accepted", "confirmed", "followup_suppressed", "invalid_contact", "attempted",
           "retry_planned", "provider_handoff", "receipt_checked", "provider_delivered", "ack_checked"}

def parse_time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("UTC offset required")
    return dt.astimezone(timezone.utc)

def analyze_recipient(recipient, case):
    events = recipient["events"]
    if not events:
        return ("needs_review", "No event evidence available", "Request trace identifiers and check authorized logs")
    times = [parse_time(e["at"]) for e in events]
    if times != sorted(times):
        return ("needs_review", "Event timestamps out of order", "Validate source clock and event ordering before concluding")
    types = [e["type"] for e in events]
    if any(t not in ALLOWED for t in types):
        raise ValueError("Unknown event type")
    if "confirmed" in types and "provider_delivered" in types:
        # This is not necessarily contradictory; confirmation may follow delivery.
        pass
    if "followup_suppressed" in types:
        if "confirmed" not in types or types.index("confirmed") > types.index("followup_suppressed"):
            return ("needs_review", "Follow-up suppressed without preceding confirmation", "Verify delivery policy and event sequence")
        return ("expected_behavior", "Confirmation preceded a suppressed follow-up", "Verify configured confirmation rule, then explain the contact-cycle behavior")
    if "invalid_contact" in types:
        return ("configuration_review", "Contact path is invalid in the sample trace", "Ask an authorized administrator to validate the affected contact record")
    if "retry_planned" in types and any(parse_time(e["at"]) > parse_time(case["window_end"]) for e in events if e["type"] == "retry_planned"):
        return ("configuration_review", "Planned retry is beyond the fictional notification window", "Review permitted retry intervals and window duration with the administrator")
    if "provider_delivered" in types:
        if "ack_checked" in types and not any(e["type"] == "confirmed" for e in events):
            return ("customer_verification", "Provider marked delivered; human acknowledgement is not shown", "Clarify whether customer means transport status, device observation or explicit acknowledgement")
        return ("customer_verification", "Provider delivery status is present", "Confirm customer-reported symptoms before closing")
    if "provider_handoff" in types:
        return ("evidence_gap", "Handoff recorded; final delivery outcome is unavailable in this trace", "Check provider receipt, scope, elapsed time and incident policy; escalate if impact warrants")
    return ("needs_review", "Evidence insufficient for a specific cause", "Collect additional authorized event details")

def investigate(case):
    if case["request"]["http_status"] != 202:
        raise ValueError("Fixture expects an illustrative HTTP 202")
    ids = [r["id"] for r in case["recipients"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate recipient IDs")
    findings = []
    for r in case["recipients"]:
        kind, explanation, next_action = analyze_recipient(r, case)
        findings.append({"recipient_id": r["id"], "classification": kind, "explanation": explanation,
                         "next_action": next_action, "events": r["events"]})
    return {"case_id": case["case_id"], "total_recipients": len(findings),
            "findings": findings, "requires_followup": sum(f["classification"] in ("evidence_gap", "needs_review") for f in findings),
            "disclaimer": "All findings are fictional. These are investigative prompts, not vendor diagnostics."}

def main():
    case = json.loads((ROOT / "data" / "case.json").read_text(encoding="utf-8"))
    findings = investigate(case)
    (ROOT / "data" / "findings.json").write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    print(f"Analyzed {findings['total_recipients']} fictional recipient paths")

if __name__ == "__main__":
    main()
