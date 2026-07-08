"""HandleFailure: global error handler.

Classifies the error, decides FAILED vs INCONSISTENT (a partial apply may have
created real resources), records metadata and an audit event.
"""
import platform_common as pc


def _classify(state):
    error = state.get("error", {}) or {}
    cause = str(error.get("Cause", "")) + str(error.get("Error", ""))

    # If terraform apply started, the resource may exist despite the failure.
    if state.get("apply_build") is not None:
        return "INCONSISTENT", "apply_failed_after_start"
    if "States.Timeout" in cause:
        return "FAILED", "timeout"
    if state.get("plan_build") is not None:
        return "FAILED", "plan_or_policy_failed"
    return "FAILED", "validation_or_setup_failed"


def handler(event, _context):
    request_id = event["request_id"]
    state = event.get("input", {})
    status, classification = _classify(state)

    pc.update_request_status(
        request_id,
        status,
        {"error_classification": classification, "error_detail": state.get("error", {})},
    )
    pc.audit(request_id, "PROVISIONING_FAILED", {"status": status, "classification": classification})
    return {"classification": classification}
