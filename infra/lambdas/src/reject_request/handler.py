"""RejectRequest: mark a request REJECTED with a human-readable reason.

Business rejection (invalid schema/ownership/policy, or approval denied) — not a
system failure.
"""
import platform_common as pc


def _derive_reason(state):
    if not state.get("schema", {}).get("valid", True):
        return "schema_invalid", state["schema"].get("errors", [])
    if not state.get("ownership", {}).get("valid", True):
        return "ownership_invalid", state["ownership"].get("errors", [])
    if not state.get("policies", {}).get("valid", True):
        return "policy_rejected", state["policies"].get("violations", [])
    if not state.get("policy_check", {}).get("passed", True):
        return "plan_policy_rejected", state["policy_check"].get("violations", [])
    approval_result = state.get("approval_result")
    if approval_result is not None and not approval_result.get("approved", False):
        return "approval_denied", approval_result
    if "error" in state:
        return "approval_timeout_or_error", state.get("error")
    return "rejected", None


def handler(event, _context):
    request_id = event["request_id"]
    state = event.get("input", {})
    reason, detail = _derive_reason(state)

    pc.update_request_status(request_id, "REJECTED", {"rejection_reason": reason})
    pc.audit(request_id, "REQUEST_REJECTED", {"reason": reason, "detail": detail})
    return {"reason": reason}
