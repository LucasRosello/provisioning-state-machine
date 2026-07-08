"""ValidatePolicies: platform rules evaluated BEFORE terraform plan.

Cheap, static checks that can reject a request early (e.g. a prod relational
database without backups) without spending a CodeBuild run.
"""
import platform_common as pc

ALLOWED_ENVIRONMENTS = {"dev", "staging", "prod"}
ACTIVE_TEMPLATES = {"dynamodb-table", "rds-postgres", "cache-valkey"}


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    env = request.get("environment")
    template_id = request.get("template_id")
    config = request.get("config", {}) or {}
    violations = []

    if env not in ALLOWED_ENVIRONMENTS:
        violations.append({"policy": "allowed-environment", "message": f"environment '{env}' not allowed"})

    if template_id not in ACTIVE_TEMPLATES:
        violations.append({"policy": "active-template", "message": f"template '{template_id}' is not active"})

    # Naming convention: service_name kebab-case.
    service = request.get("service_name", "")
    if service and not service.replace("-", "").isalnum():
        violations.append({"policy": "naming-convention", "message": "service_name must be kebab-case alphanumeric"})

    # Prod relational DB must declare backups before we even plan.
    if env == "prod" and template_id == "rds-postgres":
        retention = int(config.get("backup_retention_days", 0) or 0)
        if retention < 7:
            violations.append({
                "policy": "prod-rds-backup-required",
                "message": "Production RDS requires backup_retention_days >= 7",
            })

    valid = len(violations) == 0
    pc.audit(
        request_id,
        "POLICY_VALIDATION_SUCCEEDED" if valid else "POLICY_VALIDATION_FAILED",
        {"violations": violations} if violations else None,
    )
    return {"policies_valid": valid, "violations": violations}
