"""PolicyCheckPlan: evaluate policies over tfplan.json produced by CodeBuild.

Production shells out to conftest/OPA (or checkov/tfsec). Demo reads the plan
artifact from S3 and applies a couple of representative checks; if the artifact
is absent (pure orchestration demo without real terraform), it passes with a
note so the flow can be exercised end to end.
"""
import json
import os

import boto3

import platform_common as pc

_s3 = boto3.client("s3")
ARTIFACTS_BUCKET = os.environ["ARTIFACTS_BUCKET"]


def _load_plan(request_id):
    try:
        obj = _s3.get_object(Bucket=ARTIFACTS_BUCKET, Key=f"{request_id}/tfplan.json")
        return json.loads(obj["Body"].read())
    except _s3.exceptions.NoSuchKey:
        return None


def _evaluate(plan):
    """Very small representative rule set over planned resources."""
    violations = []
    for rc in plan.get("resource_changes", []):
        after = (rc.get("change", {}) or {}).get("after", {}) or {}
        rtype = rc.get("type", "")

        if rtype == "aws_db_instance":
            if not after.get("storage_encrypted", False):
                violations.append({"policy": "encryption-required", "message": f"{rc['address']} must enable storage_encrypted"})
            if int(after.get("backup_retention_period", 0) or 0) < 7:
                violations.append({"policy": "prod-rds-backup-required", "message": f"{rc['address']} requires backup retention >= 7 days"})

        if rtype == "aws_s3_bucket" and after.get("acl") == "public-read":
            violations.append({"policy": "no-public-access", "message": f"{rc['address']} must not be public"})

    return violations


def handler(event, _context):
    request_id = event["request_id"]
    pc.audit(request_id, "PLAN_POLICY_CHECK_STARTED")

    plan = _load_plan(request_id)
    if plan is None:
        pc.audit(request_id, "PLAN_POLICY_CHECK_SUCCEEDED", {"note": "no tfplan.json artifact (demo)"})
        return {"policy_check": {"passed": True, "violations": []}}

    violations = _evaluate(plan)
    passed = len(violations) == 0
    pc.audit(
        request_id,
        "PLAN_POLICY_CHECK_SUCCEEDED" if passed else "PLAN_POLICY_CHECK_FAILED",
        {"violations": violations} if violations else None,
    )
    return {"policy_check": {"passed": passed, "violations": violations}}
