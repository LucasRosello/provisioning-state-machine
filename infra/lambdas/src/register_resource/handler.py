"""RegisterResource: persist the provisioned resource instance."""
import os
import uuid

import boto3

import platform_common as pc

RESOURCES_TABLE = os.environ["RESOURCES_TABLE"]
_ddb = boto3.resource("dynamodb")


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    template = event["template"]
    terraform = event["terraform"]
    outputs = event.get("resource_outputs", {}) or {}

    resource_id = f"res-{uuid.uuid4().hex[:12]}"
    item = {
        "resource_id": resource_id,
        "request_id": request_id,
        "template_id": template["id"],
        "template_version": template["version"],
        "template_commit_sha": template["commit_sha"],
        "team": request["team"],
        "service_name": request["service_name"],
        "environment": request["environment"],
        "resource_type": template["id"],
        "aws_region": os.environ.get("AWS_REGION", ""),
        "terraform_state_key": terraform["state_key"],
        "outputs": outputs,
        "status": "ACTIVE",
        "created_at": pc.now_iso(),
    }
    _ddb.Table(RESOURCES_TABLE).put_item(Item=item)

    pc.update_request_status(request_id, "SUCCEEDED", {"resource_id": resource_id})
    pc.audit(request_id, "RESOURCE_REGISTERED", {"resource_id": resource_id})
    return {"resource_id": resource_id}
