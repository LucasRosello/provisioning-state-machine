"""Shared helpers for the provisioning orchestration Lambdas.

Packaged as a Lambda layer so every handler reuses the same DynamoDB access,
audit-event emission, request-status transitions and notification logic.
"""
import datetime
import json
import os
import uuid

import boto3

_ddb = boto3.resource("dynamodb")
_sns = boto3.client("sns")
_sfn = boto3.client("stepfunctions")

REQUESTS_TABLE = os.environ.get("REQUESTS_TABLE", "")
RESOURCES_TABLE = os.environ.get("RESOURCES_TABLE", "")
AUDIT_TABLE = os.environ.get("AUDIT_TABLE", "")
NOTIFICATIONS_TOPIC = os.environ.get("NOTIFICATIONS_TOPIC", "")


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Requests ---------------------------------------------------------------

def get_request(request_id):
    """Load a request row. The DB is the source of truth for the workflow."""
    resp = _ddb.Table(REQUESTS_TABLE).get_item(Key={"request_id": request_id})
    item = resp.get("Item")
    if not item:
        raise KeyError(f"request {request_id} not found")
    return item


def update_request_status(request_id, status, extra=None):
    """Move the request to a new lifecycle status (VALIDATING, PLANNING, ...)."""
    names = {"#s": "status", "#u": "updated_at"}
    values = {":s": status, ":u": now_iso()}
    sets = ["#s = :s", "#u = :u"]
    for i, (k, v) in enumerate((extra or {}).items()):
        names[f"#k{i}"] = k
        values[f":v{i}"] = v
        sets.append(f"#k{i} = :v{i}")
    _ddb.Table(REQUESTS_TABLE).update_item(
        Key={"request_id": request_id},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


# --- Audit ------------------------------------------------------------------

def audit(request_id, event_type, detail=None):
    """Append an immutable audit event. event_id sorts chronologically."""
    event_id = f"{now_iso()}#{uuid.uuid4().hex[:8]}"
    _ddb.Table(AUDIT_TABLE).put_item(
        Item={
            "request_id": request_id,
            "event_id": event_id,
            "event_type": event_type,
            "detail": detail or {},
            "created_at": now_iso(),
        }
    )
    return event_id


# --- Notifications ----------------------------------------------------------

def notify(subject, message):
    if not NOTIFICATIONS_TOPIC:
        return
    _sns.publish(
        TopicArn=NOTIFICATIONS_TOPIC,
        Subject=subject[:100],
        Message=json.dumps(message) if isinstance(message, dict) else str(message),
    )


# --- Step Functions callbacks ----------------------------------------------

def send_task_success(task_token, output):
    _sfn.send_task_success(taskToken=task_token, output=json.dumps(output))


def send_task_failure(task_token, error, cause):
    _sfn.send_task_failure(taskToken=task_token, error=error, cause=cause)
