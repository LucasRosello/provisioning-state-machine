"""EvaluateApproval: decide whether the request needs human approval."""
import platform_common as pc

SENSITIVE_TEMPLATES = {"rds-postgres"}


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    env = request.get("environment")
    template_id = request.get("template_id")

    reasons = []
    if env == "prod":
        reasons.append("production environment")
    if template_id in SENSITIVE_TEMPLATES and env == "prod":
        reasons.append("production relational database")

    required = len(reasons) > 0
    approval = {
        "required": required,
        "approvers": ["platform-engineering"] if required else [],
        "reason": "; ".join(reasons) if required else "no approval required",
    }

    if required:
        pc.audit(request_id, "APPROVAL_REQUIRED", approval)
    return {"approval": approval}
