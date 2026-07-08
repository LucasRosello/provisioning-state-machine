"""ValidateOwnership: validate the team owns the requested service.

Demo implementation uses a local ownership map. Production integrates with
Backstage / CMDB / GitHub Teams / internal service catalog.
"""
import platform_common as pc

OWNERSHIP = {
    "platform": [
        "users-api",
        "billing-api",
        "catalog-service",
        "identity-service",
        "notifications-api",
        "audit-service",
    ],
    "growth": [
        "referrals-api",
        "campaigns-api",
        "experiments-api",
        "landing-pages-api",
    ],
    "payments": [
        "checkout-api",
        "ledger-api",
        "settlements-api",
        "invoices-api",
        "pricing-api",
    ],
    "data": [
        "analytics-api",
        "events-ingestion-api",
        "feature-store-api",
        "reports-api",
    ],
    "risk": [
        "fraud-detection-api",
        "kyc-api",
        "limits-api",
        "risk-scoring-api",
    ],
    "mobile": [
        "mobile-bff",
        "push-notifications-api",
        "device-registry-api",
    ],
    "support": [
        "helpdesk-api",
        "customer-profile-api",
        "case-management-api",
    ],
    "security": [
        "secrets-broker-api",
        "access-review-api",
        "policy-audit-api",
    ],
}


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    team = request.get("team")
    service = request.get("service_name")
    errors = []

    if team not in OWNERSHIP:
        errors.append({"field": "team", "message": f"unknown team '{team}'"})
    elif service not in OWNERSHIP[team]:
        errors.append({
            "field": "service_name",
            "message": f"service '{service}' is not owned by team '{team}'",
        })

    valid = len(errors) == 0
    pc.audit(
        request_id,
        "OWNERSHIP_VALIDATION_SUCCEEDED" if valid else "OWNERSHIP_VALIDATION_FAILED",
        {"errors": errors} if errors else None,
    )
    return {"ownership_valid": valid, "errors": errors}
