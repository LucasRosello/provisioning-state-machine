"""GenerateTerraformVariables: build tfvars + state key and stage them in S3.

Writes terraform.tfvars.json to s3://<artifacts>/<request_id>/ so the CodeBuild
plan/apply jobs consume exactly the variables the platform generated (not raw
user input).
"""
import json
import os

import boto3

import platform_common as pc

_s3 = boto3.client("s3")
ARTIFACTS_BUCKET = os.environ["ARTIFACTS_BUCKET"]


def _dynamodb_config(config):
    normalized = dict(config)
    partition_key = normalized.get("partition_key")
    sort_key = normalized.get("sort_key")

    if isinstance(partition_key, str):
        normalized["partition_key"] = {"name": partition_key, "type": "S"}

    if isinstance(sort_key, str):
        if sort_key:
            normalized["sort_key"] = {"name": sort_key, "type": "S"}
        else:
            normalized.pop("sort_key", None)

    return normalized


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    template = event["template"]
    config = request.get("config", {}) or {}
    if template["id"] == "dynamodb-table":
        config = _dynamodb_config(config)

    env = request["environment"]
    team = request["team"]
    service = request["service_name"]

    tags = {
        "ManagedBy": "platform-self-service",
        "Team": team,
        "Service": service,
        "Environment": env,
        "RequestId": request_id,
    }

    variables = {
        "service_name": service,
        "team": team,
        "environment": env,
        "tags": tags,
        **config,
    }

    # Deterministic, collision-free state key per logical resource.
    resource_name = config.get("table_name") or config.get("name") or service
    state_key = f"resources/{env}/{team}/{service}/{template['id']}/{resource_name}/terraform.tfstate"

    _s3.put_object(
        Bucket=ARTIFACTS_BUCKET,
        Key=f"{request_id}/terraform.tfvars.json",
        Body=json.dumps(variables, indent=2).encode(),
        ContentType="application/json",
    )

    terraform = {
        "module_path": template["module_path"],
        "state_key": state_key,
        "variables": variables,
    }

    pc.update_request_status(request_id, "PLANNING")
    pc.audit(request_id, "TERRAFORM_VARIABLES_GENERATED", {"state_key": state_key})
    return {"terraform": terraform}
