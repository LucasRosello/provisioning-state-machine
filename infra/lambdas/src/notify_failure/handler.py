"""NotifyFailure: announce a rejected or failed request."""
import platform_common as pc


def handler(event, _context):
    request_id = event["request_id"]
    mode = event.get("mode", "failed")  # "rejected" | "failed"
    state = event.get("input", {})

    if mode == "rejected":
        final_status = "REJECTED"
        error_type = state.get("rejection", {}).get("reason", "rejected")
    else:
        final_status = state.get("failure", {}).get("classification", "FAILED")
        error_type = "workflow_failure"

    message = {
        "status": final_status,
        "request_id": request_id,
        "error_type": error_type,
        "detail_link": f"/requests/{request_id}",
        "recommended_action": "Review the request detail and audit events.",
    }
    pc.notify(f"[platform] request {request_id} {mode}", message)
    return {"notified": True}
