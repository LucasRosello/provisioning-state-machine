"""ValidateSchema: validate required fields and template config."""
import platform_common as pc

REQUIRED_TOP = ["template_id", "template_version", "service_name", "team", "environment", "config"]

# Minimal per-template required config keys. In production this is derived from
# the template.schema.json shipped with each template.
TEMPLATE_REQUIRED_CONFIG = {
    "dynamodb-table": ["table_name", "partition_key", "billing_mode"],
    "rds-postgres": ["engine_version", "instance_class", "allocated_storage"],
    "cache-valkey": ["node_type", "num_nodes"],
}


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    errors = []

    for field in REQUIRED_TOP:
        if request.get(field) in (None, "", {}):
            errors.append({"field": field, "message": f"{field} is required"})

    config = request.get("config", {}) or {}
    for key in TEMPLATE_REQUIRED_CONFIG.get(request.get("template_id"), []):
        if config.get(key) in (None, ""):
            errors.append({"field": f"config.{key}", "message": f"{key} is required"})

    valid = len(errors) == 0
    if valid:
        pc.audit(request_id, "SCHEMA_VALIDATION_SUCCEEDED")
    else:
        pc.audit(request_id, "SCHEMA_VALIDATION_FAILED", {"errors": errors})

    return {"schema_valid": valid, "errors": errors}
