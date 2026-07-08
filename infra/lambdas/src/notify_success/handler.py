"""NotifySuccess: announce a successfully provisioned resource."""
import platform_common as pc


def handler(event, _context):
    request_id = event["request_id"]
    resource = event.get("resource", {})
    outputs = event.get("resource_outputs", {})

    message = {
        "status": "SUCCEEDED",
        "request_id": request_id,
        "resource_id": resource.get("resource_id"),
        "outputs": outputs,
    }
    pc.audit(request_id, "PROVISIONING_SUCCEEDED", {"resource_id": resource.get("resource_id")})
    pc.notify(f"[platform] request {request_id} provisioned", message)
    return {"notified": True}
