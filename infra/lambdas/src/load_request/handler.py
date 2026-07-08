"""LoadRequest: load the full request from the database using only request_id."""
import platform_common as pc


def handler(event, _context):
    request_id = event["request_id"]

    request = pc.get_request(request_id)

    pc.update_request_status(request_id, "VALIDATING")
    pc.audit(request_id, "REQUEST_LOADED", {"template_id": request.get("template_id")})
    pc.audit(request_id, "VALIDATION_STARTED")

    return {
        "request": {
            "template_id": request["template_id"],
            "template_version": request["template_version"],
            "service_name": request["service_name"],
            "team": request["team"],
            "environment": request["environment"],
            "config": request.get("config", {}),
        }
    }
